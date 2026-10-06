"""Edit existing Word paragraphs without rebuilding the document body.

Original archive members, paragraph/run properties, tables and drawings survive.
The XML tree outside edited paragraphs is preserved, including TOC occurrences.
"""
from __future__ import annotations

import copy
import hashlib
import posixpath
import re
import unicodedata
import zipfile
from difflib import SequenceMatcher
from pathlib import Path
from xml.etree import ElementTree as ET  # nosec B405

from revisor.docx.reader import NS, WORD_NS, parse_xml

W = '{' + WORD_NS + '}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'
MAX_ARCHIVE = 256 * 1024 * 1024
REL_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT_NS = 'http://schemas.openxmlformats.org/package/2006/content-types'


def normalized(text: str) -> str:
    value = unicodedata.normalize('NFD', text.casefold())
    return re.sub(r'[^a-z0-9 ]', '', ''.join(c for c in value if not unicodedata.combining(c))).strip()


def _members(path: Path) -> dict[str, bytes]:
    if path.suffix.casefold() != '.docx':
        raise ValueError('Selecione um arquivo Word .docx.')
    try:
        with zipfile.ZipFile(path) as archive:
            if sum(i.file_size for i in archive.infolist()) > MAX_ARCHIVE:
                raise ValueError('O Word descompactado excede 256 MB.')
            members = {i.filename: archive.read(i.filename) for i in archive.infolist()}
    except zipfile.BadZipFile as error:
        raise ValueError('O arquivo não é um Word .docx válido.') from error
    if 'word/document.xml' not in members:
        raise ValueError('O arquivo não contém o documento Word.')
    return members


def _serialize(root: ET.Element, original: bytes) -> bytes:
    # Retain namespace declarations referenced only by mc:Ignorable or QName values.
    declarations = dict(re.findall(rb'xmlns:([\w]+)=["\']([^"\']+)', original))
    default_namespace = re.search(rb'xmlns=["\']([^"\']+)', original)
    if default_namespace is not None:
        ET.register_namespace('',default_namespace.group(1).decode())
    for prefix, uri in declarations.items():
        name = prefix.decode()
        if not re.fullmatch(r'ns\d+', name):
            ET.register_namespace(name, uri.decode())
    rendered = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    for prefix, uri in declarations.items():
        attr = b'xmlns:' + prefix + b'='
        if attr not in rendered:
            at = rendered.index(b'>', rendered.index(b'?>') + 2)
            rendered = rendered[:at] + b' ' + attr + b'"' + uri + b'"' + rendered[at:]
    return rendered


def _write(members: dict[str, bytes], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.tmp.docx')
    with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, value in members.items():
            archive.writestr(name, value)
    temporary.replace(output)


def _paragraph_text(paragraph: ET.Element) -> str:
    def walk(node):
        for child in node:
            if child.tag == W + 'p':  # Text boxes have their own paragraph IDs.
                continue
            if child.tag == W + 't':
                yield child.text or ''
            elif child.tag == W + 'tab':
                yield '\t'
            elif child.tag in {W + 'br', W + 'cr'} and child.get(W + 'type', 'textWrapping') == 'textWrapping':
                yield '\n'
            else:
                yield from walk(child)
    return ''.join(walk(paragraph))


def inspect_document(path: Path) -> dict:
    members = _members(path)
    root = parse_xml(members['word/document.xml'])
    body = root.find('w:body', NS)
    if body is None:
        raise ValueError('O Word não contém corpo de texto.')
    paragraphs = []
    headings = []
    for index, paragraph in enumerate(body.iter(W + 'p'), 1):
        text = _paragraph_text(paragraph)
        style_node = paragraph.find('w:pPr/w:pStyle', NS)
        style = style_node.get(W + 'val', '') if style_node is not None else ''
        item = {'id': index, 'text': text, 'style': style, 'part': 'word/document.xml'}
        paragraphs.append(item)
        title = normalized(text)
        is_toc = bool(re.search(r'toc|sumario|sumário', style, re.I))
        special = title in {'epilogo', 'posfacio'}
        chapter = bool(re.fullmatch(r'(capitulo|chapter)\s+[0-9ivxlcdm]+(?: .{0,100})?', title))
        heading_style = bool(re.fullmatch(r'(heading|titulo|título)\s*1', style, re.I))
        if text.strip() and len(text) < 160 and not is_toc and (special or chapter or heading_style):
            headings.append({'title': text.strip(), 'key': title if special else f'section-{index}',
                             'start': index, 'normalized': title})
    # Drop capitals and decorative headings can split a chapter title across paragraphs.
    # Reconstruct the navigation label only; the original Word paragraphs remain intact.
    nonempty = [p for p in paragraphs if p['text'].strip()]
    for i, item in enumerate(nonempty[:-1]):
        first = item['text'].strip()
        following = nonempty[i + 1]
        if re.search(r'toc|sumario|sumário', item['style'], re.I):
            continue
        if normalized(first) == 'c' and re.match(r'^ap[ií]tulo\b', following['text'].strip(), re.I):
            title = first + following['text'].strip()
        elif normalized(first) in {'capitulo', 'chapter'} and re.fullmatch(r'[0-9IVXLCDM]+', following['text'].strip(), re.I):
            title = first + ' ' + following['text'].strip()
        else:
            continue
        if re.fullmatch(r'(capitulo|chapter)\s+[0-9ivxlcdm]+(?: .{0,100})?', normalized(title)):
            consumed = {item['id'], following['id']}
            headings = [h for h in headings if h['start'] not in consumed]
            headings.append({'title': title, 'key': f'section-{item["id"]}', 'start': item['id'], 'normalized': normalized(title)})
    headings.sort(key=lambda h: h['start'])
    # Unstyled literal TOCs can contain the same title; the body occurrence follows them.
    last_occurrence = {h['normalized']: h['start'] for h in headings}
    headings = [h for h in headings if last_occurrence[h['normalized']] == h['start']]
    if not headings or headings[0]['start'] > 1:
        headings.insert(0, {'title': 'Abertura', 'key': 'frontmatter', 'start': 1})
    sections = []
    for i, heading in enumerate(headings):
        end = headings[i + 1]['start'] - 1 if i + 1 < len(headings) else len(paragraphs)
        ids = [p['id'] for p in paragraphs if heading['start'] <= p['id'] <= end and p['text'].strip()]
        if ids:
            sections.append({k:v for k,v in heading.items() if k != 'normalized'} | {'end': end, 'paragraph_ids': ids})
    # Published footnotes/endnotes and running headers/footers also belong to whole-book coverage.
    extra_parts = [n for n in members if re.fullmatch(r'word/(footnotes|endnotes|header\d+|footer\d+)\.xml', n)]
    for part in extra_parts:
        extra = parse_xml(members[part])
        for i, paragraph in enumerate(extra.iter(W + 'p'), 1):
            text = _paragraph_text(paragraph)
            if text.strip():
                paragraphs.append({'id': f'{part}#{i}', 'text': text, 'style': '', 'part': part})
    return {'paragraphs': paragraphs, 'sections': sections, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'paragraph_count': sum(bool(p['text'].strip()) for p in paragraphs)}


def _replace_nodes(nodes: list, replacement: str) -> None:
    old = ''.join(n.text or '' for n in nodes)
    spans = []; offset = 0
    for node in nodes:
        end = offset + len(node.text or '')
        spans.append((offset, end)); offset = end
    outputs = [''] * len(nodes)
    for opcode, a, b, c, d in SequenceMatcher(a=old, b=replacement, autojunk=False).get_opcodes():
        if opcode == 'equal':
            for i, (start, end) in enumerate(spans):
                lo, hi = max(a, start), min(b, end)
                if hi > lo: outputs[i] += old[lo:hi]
        elif opcode in {'insert', 'replace'}:
            index = next((i for i, (_, end) in enumerate(spans) if a < end), len(nodes) - 1)
            outputs[index] += replacement[c:d]
    for node, text in zip(nodes, outputs):
        node.text = text; node.set(XML_SPACE, 'preserve')


def _replace_text(paragraph: ET.Element, replacement: str) -> None:
    groups = [[]]; separators = []
    def walk(node):
        for child in node:
            if child.tag == W + 'p': continue
            if child.tag == W + 't': groups[-1].append(child)
            elif child.tag == W + 'tab':
                separators.append(('\t', child, node)); groups.append([])
            elif child.tag in {W + 'br', W + 'cr'} and child.get(W + 'type','textWrapping') == 'textWrapping':
                separators.append(('\n', child, node)); groups.append([])
            else: walk(child)
    walk(paragraph)
    pieces = re.split(r'([\n\t])', replacement)
    if pieces[1::2] != [s[0] for s in separators]:
        raise ValueError('Mantenha as quebras internas e tabulações do parágrafo para preservar a estrutura do Word.')
    for i, (nodes, text) in enumerate(zip(groups, pieces[::2])):
        if not nodes and text:
            if i:
                _, anchor, parent = separators[i-1]
                node = ET.Element(W+'t'); parent.insert(list(parent).index(anchor)+1,node)
            elif separators:
                _, anchor, parent = separators[0]
                node = ET.Element(W+'t'); parent.insert(list(parent).index(anchor),node)
            else:
                run = ET.SubElement(paragraph,W+'r'); node = ET.SubElement(run,W+'t')
            nodes.append(node)
        if nodes: _replace_nodes(nodes,text)


def _set_language(paragraph, language):
    for run in paragraph.iter(W+'r'):
        props=run.find('w:rPr',NS)
        if props is None: props=ET.Element(W+'rPr'); run.insert(0,props)
        lang=props.find('w:lang',NS)
        if lang is None: lang=ET.SubElement(props,W+'lang')
        lang.set(W+'val',language)


def edit_document(source: Path, output: Path, replacements: dict, *, only_ids: set | None = None, language: str | None = None) -> None:
    if source.resolve() == output.resolve():
        raise ValueError('A exportação não pode sobrescrever o original.')
    members = _members(source)
    parts = {'word/document.xml'} | {str(i).split('#')[0] for i in replacements if '#' in str(i)}
    for part in parts:
        original = members[part]; root = parse_xml(original)
        parent = root.find('w:body', NS) if part == 'word/document.xml' else root
        changed = False
        for index, paragraph in enumerate(parent.iter(W + 'p'), 1):
            pid = index if part == 'word/document.xml' else f'{part}#{index}'
            if pid in replacements and _paragraph_text(paragraph) != replacements[pid]:
                _replace_text(paragraph, replacements[pid])
                changed = True
            if language and pid in replacements:
                _set_language(paragraph,language); changed=True
        if only_ids is not None and part == 'word/document.xml':
            # Section-only standalone export retains page settings, not unrelated chapters.
            ids={id(p):i for i,p in enumerate(parent.iter(W+'p'),1)}
            for block in list(parent):
                paras=list(block.iter(W+'p'))
                if paras and not any(ids[id(p)] in only_ids for p in paras):
                    parent.remove(block); changed = True
        if changed: members[part] = _serialize(root, original)
    _write(members, output)


class _PackageMerger:
    def __init__(self, source, target):
        self.source, self.target = source,target
        self.prefix = 'word/imported-' + hashlib.sha256(source['word/document.xml']).hexdigest()[:12] + '/'
        self.copied = set(); self.relations = {}
        self.source_rels = parse_xml(source.get('word/_rels/document.xml.rels',f'<Relationships xmlns="{REL_NS}"/>'.encode()))
        self.target_rels = parse_xml(target.get('word/_rels/document.xml.rels',f'<Relationships xmlns="{REL_NS}"/>'.encode()))
        self.types = parse_xml(target.get('[Content_Types].xml',f'<Types xmlns="{CT_NS}"/>'.encode()))
        source_types = parse_xml(source.get('[Content_Types].xml',f'<Types xmlns="{CT_NS}"/>'.encode()))
        self.defaults = {n.get('Extension'):n.get('ContentType') for n in source_types if n.tag.endswith('Default')}
        self.overrides = {n.get('PartName').lstrip('/'):n.get('ContentType') for n in source_types if n.tag.endswith('Override')}
        self.known_types = {n.get('PartName') for n in self.types if n.tag.endswith('Override')}

    def copy_part(self, name):
        if name not in self.source: raise ValueError('O Word contém uma referência a arquivo interno inexistente.')
        new = self.prefix + name
        if name in self.copied: return new
        self.copied.add(name); self.target[new] = self.source[name]
        content_type = self.overrides.get(name,self.defaults.get(name.rsplit('.',1)[-1]))
        if content_type and '/'+new not in self.known_types:
            ET.SubElement(self.types,'{'+CT_NS+'}Override',PartName='/'+new,ContentType=content_type)
            self.known_types.add('/'+new)
        directory, basename = posixpath.split(name)
        rel_path = posixpath.join(directory,'_rels',basename+'.rels')
        if rel_path in self.source:
            rels = parse_xml(self.source[rel_path])
            for rel in rels:
                if rel.get('TargetMode')=='External': continue
                target = rel.get('Target','')
                old_part = posixpath.normpath(posixpath.join(directory,target)) if not target.startswith('/') else target.lstrip('/')
                new_part = self.copy_part(old_part)
                rel.set('Target',posixpath.relpath(new_part,posixpath.dirname(new)))
            self.target[self.prefix+rel_path] = _serialize(rels,self.source[rel_path])
        return new

    def relation(self, rid):
        if rid in self.relations: return self.relations[rid]
        source = next((r for r in self.source_rels if r.get('Id')==rid),None)
        if source is None: raise ValueError('O Word contém um vínculo sem relacionamento correspondente.')
        new = copy.deepcopy(source)
        used = {r.get('Id') for r in self.target_rels}; new_id = f'rIdImported{len(used)+1}'
        while new_id in used: new_id+='x'
        new.set('Id',new_id)
        if source.get('TargetMode')!='External':
            name = source.get('Target','')
            name = posixpath.normpath(posixpath.join('word',name)) if not name.startswith('/') else name.lstrip('/')
            new.set('Target',posixpath.relpath(self.copy_part(name),'word'))
        self.target_rels.append(new); self.relations[rid]=new_id
        return new_id

    def finish(self):
        if self.relations:
            self.target['word/_rels/document.xml.rels'] = _serialize(self.target_rels,self.target.get('word/_rels/document.xml.rels',b''))
            self.target['[Content_Types].xml'] = _serialize(self.types,self.target.get('[Content_Types].xml',b''))


def splice_sections(source: Path, destination: Path, output: Path, sections: list[dict], replacements: dict) -> None:
    if output.resolve() in {source.resolve(), destination.resolve()}:
        raise ValueError('Gere uma cópia; não sobrescreva os originais.')
    src_members, dest_members = _members(source), _members(destination)
    src = parse_xml(src_members['word/document.xml']); dest = parse_xml(dest_members['word/document.xml'])
    src_body, dest_body = src.find('w:body', NS), dest.find('w:body', NS)
    src_paras, dest_paras = list(src_body.iter(W + 'p')), list(dest_body.iter(W + 'p'))
    target_sections = {s['key']: s for s in inspect_document(destination)['sections']}
    for section in sections:
        if section['key'] not in target_sections:
            raise ValueError(f'O destino não contém a seção {section["title"]}. Selecione o Word correto.')
    merger = _PackageMerger(src_members,dest_members)
    drawing_tag = '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr'
    drawing_id = max((int(n.get('id','0')) for n in dest.iter(drawing_tag)),default=0)
    bookmark_id = max((int(n.get(W+'id','0')) for n in dest.iter(W+'bookmarkStart')),default=0)
    bookmark_map = {}
    bookmark_names = {n.get(W+'name') for n in dest.iter(W+'bookmarkStart')}
    # Style ID collisions must not change existing destination paragraphs.
    style_map = {}
    source_default_style = None
    styles_path = 'word/styles.xml'
    if styles_path in src_members and styles_path in dest_members:
        source_styles, target_styles = parse_xml(src_members[styles_path]), parse_xml(dest_members[styles_path])
        known = {s.get(W + 'styleId'):s for s in target_styles}
        for style in source_styles:
            sid = style.get(W+'styleId')
            if not sid: continue
            if style.get(W+'default')=='1' and style.get(W+'type')=='paragraph': source_default_style=sid
            style_map[sid] = sid if sid not in known or ET.tostring(style)==ET.tostring(known[sid]) else 'Imported'+hashlib.sha256(src_members['word/document.xml']).hexdigest()[:8]+'_'+sid
        for style in source_styles:
            sid = style.get(W+'styleId')
            if sid and style_map[sid] not in known:
                new = copy.deepcopy(style); new.set(W+'styleId',style_map[sid])
                new.attrib.pop(W+'default',None)
                name = new.find('w:name',NS)
                if name is not None and style_map[sid]!=sid:
                    name.set(W+'val',name.get(W+'val',sid)+' (importado)')
                for node in new.iter():
                    if node.tag in {W+'basedOn',W+'next',W+'link'} and node.get(W+'val') in style_map:
                        node.set(W+'val',style_map[node.get(W+'val')])
                target_styles.append(new)
        if len(target_styles) > len(parse_xml(dest_members[styles_path])):
            dest_members[styles_path] = _serialize(target_styles, dest_members[styles_path])
    for section in sorted(sections, key=lambda s: target_sections[s['key']]['start'], reverse=True):
        target = target_sections[section['key']]
        para_ids = {id(p):i for i,p in enumerate(src_paras,1)}
        selected = [block for block in src_body if any(section['start'] <= para_ids[id(p)] <= section['end'] for p in block.iter(W+'p'))]
        if any(n.tag in {W+'footnoteReference', W+'endnoteReference'} for block in selected for n in block.iter()):
            raise ValueError('Esta seção contém notas vinculadas. Exporte as seções separadamente para preservar as notas.')
        old_paras = dest_paras[target['start']-1:target['end']]
        old_ids = {id(p) for p in old_paras}
        old_blocks = [block for block in dest_body if any(id(p) in old_ids for p in block.iter(W+'p'))]
        position = list(dest_body).index(old_blocks[0])
        bookmarks = [copy.deepcopy(n) for n in old_paras[0] if n.tag in {W+'bookmarkStart',W+'bookmarkEnd'}]
        terminal_section = old_paras[-1].find('w:pPr/w:sectPr',NS)
        for block in old_blocks: dest_body.remove(block)
        for i, block in enumerate(selected):
            new = copy.deepcopy(block)
            for original_p, copied_p in zip(block.iter(W+'p'),new.iter(W+'p')):
                pid = para_ids[id(original_p)]
                if pid in replacements: _replace_text(copied_p,replacements[pid])
                if pid in replacements: _set_language(copied_p,'es-MX')
                if source_default_style and copied_p.find('w:pPr/w:pStyle',NS) is None:
                    props=copied_p.find('w:pPr',NS)
                    if props is None: props=ET.Element(W+'pPr'); copied_p.insert(0,props)
                    ET.SubElement(props,W+'pStyle',{W+'val':source_default_style})
            for node in new.iter():
                if node.tag == drawing_tag:
                    drawing_id += 1; node.set('id',str(drawing_id))
                if node.tag in {W+'bookmarkStart',W+'bookmarkEnd'}:
                    old_id=node.get(W+'id')
                    if old_id not in bookmark_map:
                        bookmark_id += 1; bookmark_map[old_id]=str(bookmark_id)
                    node.set(W+'id',bookmark_map[old_id])
                    if node.tag == W+'bookmarkStart' and node.get(W+'name') in bookmark_names:
                        node.set(W+'name','Imported_'+str(bookmark_id)+'_'+node.get(W+'name',''))
                if node.tag in {W+'pStyle',W+'rStyle'} and node.get(W+'val') in style_map:
                    node.set(W+'val',style_map[node.get(W+'val')])
                for attr,rid in list(node.attrib.items()):
                    if attr.startswith(R): node.set(attr,merger.relation(rid))
            if i==0 and bookmarks and new.tag==W+'p':
                for node in list(new):
                    if node.tag in {W+'bookmarkStart',W+'bookmarkEnd'}: new.remove(node)
                for bookmark in bookmarks: new.append(bookmark)
            # Section breaks in the source must not change the destination's global setup.
            for paragraph in new.iter(W+'p'):
                for prop in paragraph.findall('w:pPr/w:sectPr',NS): paragraph.find('w:pPr',NS).remove(prop)
            if i==len(selected)-1 and terminal_section is not None:
                last = list(new.iter(W+'p'))[-1]
                props = last.find('w:pPr',NS)
                if props is None: props=ET.Element(W+'pPr'); last.insert(0,props)
                props.append(copy.deepcopy(terminal_section))
            dest_body.insert(position+i, new)
    merger.finish()
    dest_members['word/document.xml'] = _serialize(dest, dest_members['word/document.xml'])
    _write(dest_members, output)
