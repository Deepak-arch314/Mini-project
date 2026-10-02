"""Knuth-Morris-Pratt (KMP) string matching.

Works on any sequence (a string or a list of words). Runs in O(n + m) time:
the text is scanned once and the pattern is never re-compared from scratch.
"""
from typing import List, Sequence


def build_lps(pattern: Sequence) -> List[int]:
    """lps[i] = length of the longest proper prefix of pattern[:i+1]
    that is also a suffix of it. Tells KMP how far to fall back on a mismatch."""
    lps = [0] * len(pattern)
    length = 0
    i = 1
    while i < len(pattern):
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length:
            length = lps[length - 1]
        else:
            lps[i] = 0
            i += 1
    return lps


def kmp_search(text: Sequence, pattern: Sequence) -> int:
    """Return the first index where `pattern` occurs in `text`, or -1."""
    if not pattern or len(pattern) > len(text):
        return -1
    lps = build_lps(pattern)
    i = j = 0
    while i < len(text):
        if text[i] == pattern[j]:
            i += 1
            j += 1
            if j == len(pattern):
                return i - j
        elif j:
            j = lps[j - 1]
        else:
            i += 1
    return -1
