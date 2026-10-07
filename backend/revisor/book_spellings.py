"""Author spellings with unusual capitals (eXilados, CamaraTTe): found in the original and kept by code."""
from collections import Counter
from difflib import SequenceMatcher
import re

WORD = re.compile(r'[^\W\d_]+')


def unusual(word):
    """Mixed case that is neither all lower, all upper nor a capitalized word."""
    return len(word) > 1 and not word.islower() and not word.isupper() and not (word[0].isupper() and word[1:].islower())


def detect(texts):
    counts = Counter()
    for text in texts:
        counts.update(word for word in WORD.findall(text) if unusual(word))
    return dict(counts)


def occurrences(text, terms):
    spans = []
    for term in terms:
        spans += [(m.start(), m.end()) for m in re.finditer(r'(?<!\w)' + re.escape(term) + r'(?!\w)', text)]
    return spans


def protect(original, revised, terms):
    """Undo every change that touches a protected word of the original; keep all other changes."""
    spans = occurrences(original, terms)
    if not spans or original == revised:
        return revised
    def touches(i1, i2, inserted):
        if i1 == i2:
            # Letters glued to either end also change the word ("eXilados" -> "eXiladoss").
            return any(start < i1 < end or (i1 == end and inserted[:1].isalnum()) or (i1 == start and inserted[-1:].isalnum()) for start, end in spans)
        return any(i1 < end and i2 > start for start, end in spans)
    parts = []
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, original, revised, autojunk=False).get_opcodes():
        parts.append(original[i1:i2] if tag != 'equal' and touches(i1, i2, revised[j1:j2]) else revised[j1:j2])
    return ''.join(parts)
