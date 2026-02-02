# -*- coding: utf-8 -*-
from typing import Optional

class SimilarityDecider:
    """
    Decide whether a new email is a 'version update' vs a 'new conversation'
    using a lightweight token Jaccard similarity on the cleaned body.

    If similarity >= threshold (default 0.90), treat as a near-duplicate 'version'.
    """
    def __init__(self, cfg: dict):
        self.threshold = float(cfg.get("similarity_threshold", 0.90))

    @staticmethod
    def _token_set(text: str):
        return set(t for t in (text or "").lower().split() if len(t) > 2)

    def similarity(self, a: str, b: str) -> float:
        A = self._token_set(a)
        B = self._token_set(b)
        if not A or not B:
            return 0.0
        return len(A & B) / float(len(A | B) + 1e-9)

    def is_version(self, new_text: str, prev_text: Optional[str]) -> bool:
        if not prev_text:
            return False
        return self.similarity(new_text, prev_text) >= self.threshold
