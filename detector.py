"""Steps 3-5 - run the matcher, compute similarity, build the result."""
from typing import List, Tuple

from matchers import get_matcher
from preprocess import Token, sentence_token_ranges, tokenize

DEFAULT_THRESHOLD = 20.0  # similarity % at or above which we report plagiarism


def _char_spans(runs: List[Tuple[int, int]], tokens: List[Token], text: str) -> List[Tuple[int, int]]:
    """Convert word-index runs into character spans of the raw text.
    A sentence-ending . ! ? right after the last word is included."""
    spans = []
    for a, b in runs:
        end = tokens[b - 1].end
        while end < len(text) and text[end] in ".!?":
            end += 1
        spans.append((tokens[a].start, end))
    return spans


def _merge_runs(runs: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Merge overlapping or touching word-index runs."""
    merged: List[List[int]] = []
    for a, b in sorted(runs):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [(a, b) for a, b in merged]


def _segments(text: str, spans: List[Tuple[int, int]]) -> List[dict]:
    """Cut `text` into [{text, match}] pieces so the UI can highlight matches."""
    out, pos = [], 0
    for s, e in spans:
        if s > pos:
            out.append({"text": text[pos:s], "match": False})
        out.append({"text": text[s:e], "match": True})
        pos = e
    if pos < len(text):
        out.append({"text": text[pos:], "match": False})
    return out


def _level(similarity: float, threshold: float) -> str:
    if similarity >= 70:
        return "High"
    if similarity >= 40:
        return "Moderate"
    if similarity >= threshold:
        return "Low"
    return "None"


def detect(original: str, submitted: str, algorithm: str = "ngram",
           min_words: int = 4, threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Compare `submitted` against `original` and return a result dictionary.
    Raises ValueError for unusable input."""
    ref_tokens = tokenize(original)
    sub_tokens = tokenize(submitted)
    if not ref_tokens:
        raise ValueError("The original text contains no readable words.")
    if not sub_tokens:
        raise ValueError("The submitted text contains no readable words.")

    ref_words = [t.text for t in ref_tokens]
    sub_words = [t.text for t in sub_tokens]
    sub_sentences = sentence_token_ranges(submitted, sub_tokens)

    matcher = get_matcher(algorithm, min_words)
    matches = matcher.find_matches(ref_words, sub_words, sub_sentences)

    sub_runs = _merge_runs([(m.sub_start, m.sub_end) for m in matches])
    ref_runs = _merge_runs([(m.ref_start, m.ref_end) for m in matches])
    matched_words = sum(b - a for a, b in sub_runs)

    similarity = round(matched_words / len(sub_words) * 100, 2)
    detected = similarity >= threshold and bool(matches)

    sections = []
    for m in sorted(matches, key=lambda x: x.sub_start):
        s, e = _char_spans([(m.sub_start, m.sub_end)], sub_tokens, submitted)[0]
        rs, re_ = _char_spans([(m.ref_start, m.ref_end)], ref_tokens, original)[0]
        sections.append({"text": submitted[s:e], "original_text": original[rs:re_],
                         "word_count": m.length})

    return {
        "plagiarism_detected": detected,
        "similarity": similarity,
        "level": _level(similarity, threshold),
        "message": "Potential Plagiarism Detected" if detected else "No Significant Plagiarism Detected",
        "algorithm": matcher.name,
        "min_words": matcher.min_words,
        "stats": {
            "original_words": len(ref_words),
            "submitted_words": len(sub_words),
            "matched_words": matched_words,
            "matched_sections": len(sections),
        },
        "matches": sections,
        "submitted_segments": _segments(submitted, _char_spans(sub_runs, sub_tokens, submitted)),
        "original_segments": _segments(original, _char_spans(ref_runs, ref_tokens, original)),
    }
