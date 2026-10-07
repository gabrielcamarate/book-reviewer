"""Highlighted letters of author spellings (the red X of eXilados).

The highlight is learned from how the original Word marks the unusual capitals of each protected
word, and then applied to every occurrence in the exported Word, including the Spanish form of the
word ("eXiliados" shares the "eX"). Only those letters change; the rest of the run keeps its format.
"""
from __future__ import annotations

import copy
import re
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET  # nosec B405

from revisor.docx.editable import W, XML_SPACE, _members, _serialize, _write
from revisor.docx.reader import parse_xml

PARTS = re.compile(r'word/(document|footnotes|endnotes|header\d+|footer\d+)\.xml')
VISUAL = {'color', 'highlight', 'shd', 'b', 'bCs', 'i', 'iCs', 'u', 'strike', 'sz', 'szCs', 'vertAlign', 'caps', 'smallCaps'}


def capitals(word):
    """Positions of the capitals that make the spelling unusual (not the first letter)."""
    return [i for i, ch in enumerate(word) if i and ch.isupper()]


def _paragraphs(root):
    return [p for p in root.iter(W + 'p')]


def _characters(paragraph):
    """(run, text node, offset) per character of the paragraph's own runs, skipping text boxes."""
    chars = []
    def walk(node):
        for child in node:
            if child.tag == W + 'p':
                continue
            if child.tag == W + 'r':
                for t in child.iter(W + 't'):
                    chars.extend((child, t, i) for i in range(len(t.text or '')))
            else:
                walk(child)
    walk(paragraph)
    return chars


def _text(chars):
    return ''.join((t.text or '')[i] for _, t, i in chars)


def _signature(element):
    # Compare meaning, not bytes: serialized prefixes change once a namespace is registered.
    return (element.tag, tuple(sorted(element.attrib.items())))


def _visual(run, signatures=False):
    props = run.find(W + 'rPr')
    if props is None: return {}
    return {child.tag[len(W):]: (_signature(child) if signatures else ET.tostring(child)) for child in props if child.tag[len(W):] in VISUAL}


def _occurrences(text, word):
    return [m.start() for m in re.finditer(r'(?<!\w)' + re.escape(word) + r'(?!\w)', text)]


def learn(path: Path, words: list[str]) -> dict:
    """{word: {position: [property XML]}} for words whose capitals the original highlights most of the time."""
    members = _members(path)
    roots = [parse_xml(data) for name, data in members.items() if PARTS.fullmatch(name)]
    rules = {}
    for word in words:
        positions = capitals(word)
        reference = next((i for i, ch in enumerate(word) if ch.islower()), None)
        if not positions or reference is None:
            continue
        seen = Counter(); total = 0
        for root in roots:
            for paragraph in _paragraphs(root):
                chars = _characters(paragraph)
                for start in _occurrences(_text(chars), word):
                    total += 1
                    plain = _visual(chars[start + reference][0], True)
                    delta = tuple((p, tuple(sorted(ET.tostring(element) for element in (chars[start + p][0].find(W + 'rPr') or [])
                                                   if element.tag[len(W):] in VISUAL and plain.get(element.tag[len(W):]) != _signature(element))))
                                  for p in positions)
                    if any(items for _, items in delta):
                        seen[delta] += 1
        if seen:
            delta, count = seen.most_common(1)[0]
            if count * 2 > total:  # Highlighted in most occurrences: the author's choice, not an accident.
                rules[word] = {p: list(items) for p, items in delta if items}
    return rules


def describe(rules: dict) -> dict:
    """What the interface shows for each learned highlight."""
    shown = {}
    for word, positions in rules.items():
        letters = []
        for p, items in sorted(positions.items()):
            props = [ET.fromstring(xml) for xml in items]
            color = next((el.get(W + 'val') for el in props if el.tag == W + 'color'), None)
            letters.append({'letter': word[p], 'color': color,
                            'bold': any(el.tag == W + 'b' and el.get(W + 'val', 'true') not in {'0', 'false'} for el in props),
                            'italic': any(el.tag == W + 'i' and el.get(W + 'val', 'true') not in {'0', 'false'} for el in props)})
        shown[word] = letters
    return shown


def _isolate(paragraph, run, t, offset, items):
    """Give one character its own run carrying the highlight; the text and the rest of the run stay the same."""
    parents = {child: parent for parent in paragraph.iter() for child in parent}
    parent = parents[run]
    props = run.find(W + 'rPr')
    content = [child for child in run if child.tag != W + 'rPr']
    index = content.index(t)
    text = t.text or ''
    def make(children, extra=None):
        new = ET.Element(run.tag, run.attrib)
        base = copy.deepcopy(props) if props is not None else ET.Element(W + 'rPr')
        for xml in extra or []:
            element = ET.fromstring(xml)
            for old in base.findall(element.tag): base.remove(old)
            base.append(element)
        if len(base) or base.attrib: new.append(base)
        new.extend(children)
        return new
    def node(value):
        element = ET.Element(W + 't'); element.text = value; element.set(XML_SPACE, 'preserve'); return element
    pieces = []
    before = content[:index] + ([node(text[:offset])] if offset else [])
    after = ([node(text[offset + 1:])] if offset + 1 < len(text) else []) + content[index + 1:]
    if before: pieces.append(make([copy.deepcopy(c) if c is not t else c for c in before]))
    pieces.append(make([node(text[offset])], items))
    if after: pieces.append(make(after))
    position = list(parent).index(run)
    parent.remove(run)
    for i, piece in enumerate(pieces):
        parent.insert(position + i, piece)


def apply(path: Path, rules: dict) -> int:
    """Highlight every occurrence in the exported Word; returns how many letters changed."""
    if not rules:
        return 0
    members = _members(path); changed = 0
    patterns = []
    for word, positions in rules.items():
        stem = word[:max(positions) + 1]  # "eX" also matches the Spanish "eXiliados".
        patterns.append((re.compile(r'(?<!\w)' + re.escape(stem) + r'\w*'), positions))
    for name in [n for n in members if PARTS.fullmatch(n)]:
        original = members[name]; root = parse_xml(original); touched = False
        for paragraph in _paragraphs(root):
            targets = []
            text = _text(_characters(paragraph))
            for pattern, positions in patterns:
                for m in pattern.finditer(text):
                    targets += [(m.start() + p, items) for p, items in positions.items() if m.start() + p < m.end()]
            for index, items in sorted(targets, reverse=True):
                run, t, offset = _characters(paragraph)[index]
                wanted = {element.tag[len(W):]: _signature(element) for element in map(ET.fromstring, items)}
                current = _visual(run, True)
                if all(current.get(tag) == signature for tag, signature in wanted.items()):
                    continue
                _isolate(paragraph, run, t, offset, items)
                changed += 1; touched = True
        if touched:
            members[name] = _serialize(root, original)
    if changed:
        _write(members, path)
    return changed
