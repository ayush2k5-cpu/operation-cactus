from collections import Counter
from math import log2


def shannon_entropy(text: str) -> float:
    """Shannon entropy of `text` in bits per character. Empty text is 0.0."""
    total = len(text)
    return sum(-n / total * log2(n / total) for n in Counter(text).values())
