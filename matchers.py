"""Step 2 - String matching algorithms.

Every matcher returns a list of Match objects: a run of words that appears in
BOTH documents. To add a new algorithm (e.g. Rabin-Karp):
    1. subclass BaseMatcher and implement find_matches()
    2. register it in MATCHERS at the bottom of this file.
Nothing else in the project needs to change.
"""
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple, Type

from kmp import kmp_search


@dataclass(frozen=True)
class Match:
    sub_start: int  # word index in the submitted text (inclusive)
    sub_end: int    # word index in the submitted text (exclusive)
    ref_start: int  # word index in the original text (inclusive)
    ref_end: int    # word index in the original text (exclusive)

    @property
    def length(self) -> int:
        return self.sub_end - self.sub_start


class BaseMatcher(ABC):
    name = "base"
    label = "Base matcher"

    def __init__(self, min_words: int = 4):
        self.min_words = max(1, int(min_words))

    @abstractmethod
    def find_matches(self, ref: Sequence[str], sub: Sequence[str],
                     sub_sentences: List[Tuple[int, int]]) -> List[Match]:
        """ref / sub are lists of normalised words; sub_sentences are
        (start, end) word ranges of each submitted sentence."""


class NGramMatcher(BaseMatcher):
    """Word n-gram matching (default).

    1. Index every run of `n` consecutive original words in a dictionary.
    2. Slide a window of `n` words over the submitted text.
    3. When a window is found in the index, extend it word by word to get the
       longest common run, then continue after it.
    Finds copied phrases even when they are only part of a sentence.
    """
    name = "ngram"
    label = "Word n-gram (phrase matching)"

    def find_matches(self, ref, sub, sub_sentences=None):
        n = min(self.min_words, len(ref), len(sub))
        if n == 0:
            return []

        index: Dict[tuple, List[int]] = defaultdict(list)
        for j in range(len(ref) - n + 1):
            index[tuple(ref[j:j + n])].append(j)

        matches: List[Match] = []
        i = 0
        while i <= len(sub) - n:
            positions = index.get(tuple(sub[i:i + n]))
            if not positions:
                i += 1
                continue
            best_len, best_j = 0, -1
            for j in positions:                      # extend to longest run
                k = n
                while i + k < len(sub) and j + k < len(ref) and sub[i + k] == ref[j + k]:
                    k += 1
                if k > best_len:
                    best_len, best_j = k, j
            matches.append(Match(i, i + best_len, best_j, best_j + best_len))
            i += best_len
        return matches


class KMPSentenceMatcher(BaseMatcher):
    """Exact sentence matching using the KMP algorithm.

    Each submitted sentence (as a list of words) is searched inside the whole
    original text with KMP. Only sentences copied completely are reported.
    """
    name = "kmp"
    label = "KMP (exact sentence matching)"

    def find_matches(self, ref, sub, sub_sentences):
        needed = min(self.min_words, len(sub))
        matches: List[Match] = []
        for start, end in sub_sentences:
            words = list(sub[start:end])
            if len(words) < needed:
                continue
            pos = kmp_search(ref, words)
            if pos != -1:
                matches.append(Match(start, end, pos, pos + len(words)))
        return matches


# Registry: algorithm name -> class.  Add new algorithms here.
MATCHERS: Dict[str, Type[BaseMatcher]] = {
    NGramMatcher.name: NGramMatcher,
    KMPSentenceMatcher.name: KMPSentenceMatcher,
}


def get_matcher(name: str, min_words: int = 4) -> BaseMatcher:
    if name not in MATCHERS:
        raise ValueError(f"Unknown algorithm '{name}'. Choose one of: {', '.join(MATCHERS)}.")
    return MATCHERS[name](min_words)


def available_algorithms() -> List[dict]:
    return [{"name": c.name, "label": c.label} for c in MATCHERS.values()]
