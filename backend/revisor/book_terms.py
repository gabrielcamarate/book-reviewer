"""Literal terminology guards: word boundaries, phrase priority and number flexion."""
import re


def canonical_glossary(learned, explicit):
    # First learned choice is stable; an author-supplied choice overrides it.
    choices={}
    for source,target in learned.items(): choices.setdefault(source.casefold(),(source,target))
    for source,target in explicit.items(): choices[source.casefold()]=(source,target)
    return dict(choices.values())


def source_terms(text, glossary):
    matches=[]
    for source,target in glossary.items():
        parts=[]
        for piece in re.findall(r'\w+|[^\w]+',source):
            if piece.isalpha() and re.search(r'[aeiouáéíóúãõ]s?$',piece,re.I) and len(piece)>3:
                piece=piece[:-1] if piece.endswith('s') else piece
                parts.append(re.escape(piece)+'s?')
            else: parts.append(re.escape(piece))
        for match in re.finditer(r'(?<!\w)'+''.join(parts)+r'(?!\w)',text,re.I):
            matches.append((match.start(),match.end(),source,target,match.group().casefold()==source.casefold()))
    chosen=[]; occupied=[]
    for start,end,source,target,_ in sorted(matches,key=lambda m:(-(m[1]-m[0]),not m[4],m[0])):
        if not any(start<right and end>left for left,right in occupied):
            chosen.append((start,source,target)); occupied.append((start,end))
    return [(source,target) for _,source,target in sorted(chosen)]


def contains_target(text, target):
    def number_form(word):
        word=word.casefold()
        return word[:-1] if len(word)>3 and re.search(r'[aeiouáéíóú]s$',word) else word
    def words(value):
        result=[]
        for word in re.findall(r'\w+',value):
            if word.casefold()=='del': result.extend(['de','el'])
            elif word.casefold()=='al': result.extend(['a','el'])
            else: result.append(number_form(word))
        return result
    expected=words(target)
    actual=words(text)
    return bool(expected) and any(actual[i:i+len(expected)]==expected for i in range(len(actual)-len(expected)+1))
