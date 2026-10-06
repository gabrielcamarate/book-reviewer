"""Automatic editorial results with exact paragraph coverage and computed diffs."""
from difflib import SequenceMatcher
import re
from revisor.provider import InvalidModelResponse


class EditorialIssues(ValueError):
    """A valid model result has unresolved editorial questions; keep other work moving."""


def apply_paragraphs(source, response):
    paragraphs=response.get('paragraphs')
    if not isinstance(paragraphs,list) or any(not isinstance(p,dict) for p in paragraphs):
        raise InvalidModelResponse('A resposta deve trazer uma versão completa de cada parágrafo.')
    if [p.get('paragraph_id') for p in paragraphs]!=list(source):
        raise InvalidModelResponse('A revisão precisa cobrir todos os parágrafos, uma vez cada, na ordem recebida.')
    revised={}; changes=[]
    for paragraph in paragraphs:
        pid=paragraph['paragraph_id']; original=source[pid]; text=paragraph.get('text')
        if not isinstance(text,str) or not text.strip():
            raise InvalidModelResponse(f'A correção não pode apagar um parágrafo inteiro (parágrafo {pid}).')
        if re.findall(r'[\n\t]',text)!=re.findall(r'[\n\t]',original):
            raise InvalidModelResponse(f'Preserve as quebras internas e tabulações do parágrafo {pid}.')
        reason=paragraph.get('reason'); category=paragraph.get('category')
        if not isinstance(reason,str) or not isinstance(category,str) or (text!=original and (not reason.strip() or not category.strip())):
            raise InvalidModelResponse(f'A correção do parágrafo {pid} precisa de justificativa e categoria.')
        revised[pid]=text
        # The model cannot propose intersecting ranges. Positions are derived from the
        # unchanged input, including insertions, so the recorded changes reconstruct it.
        for tag,start,end,new_start,new_end in SequenceMatcher(None,original,text,autojunk=False).get_opcodes():
            if tag!='equal':
                changes.append({'paragraph_id':pid,'original':original[start:end],'replacement':text[new_start:new_end],
                                'start':start,'end':end,'reason':reason,'category':category})
    return revised,changes
