# src/email_sorter/processor.py
import logging
import hashlib
from typing import List, Dict

from .mail_parser import parse_email_file
from .excel_writer import write_to_excel

logger = logging.getLogger(__name__)

def _compute_content_hash(text: str) -> str:
    text = (text or "").strip()
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest() if text else ""

def _cluster_topics_texts(texts: List[str]) -> List[str]:
    if not texts:
        return []
    if len(texts) < 3:
        return ["General"] * len(texts)

    from sklearn.feature_extraction.text import HashingVectorizer
    from sklearn.cluster import MiniBatchKMeans
    import math

    vect = HashingVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        n_features=2**18,
        alternate_sign=False,
        norm="l2",
    )
    X = vect.transform(texts)
    k = max(2, min(15, int(math.sqrt(len(texts)))))
