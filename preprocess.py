"""Step 1 - Text preprocessing.

Turns raw text into a list of lower-case word tokens. Every token remembers its
character position in the original text, so that matches can be highlighted later.
"""
import re
from dataclasses import dataclass
from typing import List, Tuple

# A word = letters/digits, optionally with an inner apostrophe (don't, student's)
WORD_RE = re.compile(r"[^\W_]+(?:'[^\W_]+)?")
# A sentence = text up to . ! ? or a new line
SENTENCE_RE = re.compile(r"[^.!?\n]+[.!?]*")


@dataclass(frozen=True)
class Token:
    text: str   # normalised (lower-case) word
    start: int  # character offset where the word starts in the raw text
    end: int    # character offset where the word ends (exclusive)


def tokenize(text: str) -> List[Token]:
    """Split text into normalised word tokens (case and punctuation ignored)."""
    text = text.replace("\u2019", "'")  # curly apostrophe -> straight (same length)
    return [Token(m.group().lower(), m.start(), m.end()) for m in WORD_RE.finditer(text)]


def sentence_token_ranges(text: str, tokens: List[Token]) -> List[Tuple[int, int]]:
    """Return (first_token_index, last_token_index + 1) for every sentence."""
    ranges = []
    t = 0
    for m in SENTENCE_RE.finditer(text):
        first = t
        while t < len(tokens) and tokens[t].start < m.end():
            t += 1
        if t > first:
            ranges.append((first, t))
    return ranges
