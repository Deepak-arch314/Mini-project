"""Plagiarism detection package (string-matching based)."""
from .detector import detect
from .matchers import available_algorithms

__all__ = ["detect", "available_algorithms"]
