"""Select relevant, non-secret BrandWise product guidance for chat answers."""
from pathlib import Path
import re

GUIDE = Path(__file__).with_name('project-guide.md')
STOP_WORDS = {'a', 'an', 'and', 'are', 'can', 'do', 'for', 'how', 'i', 'in', 'is', 'it', 'me', 'my', 'of', 'on', 'our', 'the', 'to', 'where', 'with'}


def relevant_sections(question, limit=5):
    text = GUIDE.read_text(encoding='utf-8')
    sections = re.split(r'(?=^##? )', text, flags=re.MULTILINE)
    terms = set(re.findall(r'[a-z0-9]+', question.casefold())) - STOP_WORDS
    scored = []
    for section in sections:
        if not section.strip():
            continue
        heading = section.splitlines()[0].casefold()
        body = section.casefold()
        score = sum(4 for term in terms if term in heading) + sum(1 for term in terms if term in body)
        scored.append((score, section.strip()))
    ranked = sorted(scored[1:], key=lambda item: item[0], reverse=True)
    return '\n\n'.join([scored[0][1]] + [section for _, section in ranked[:limit - 1]])
