# -*- coding: utf-8 -*-
import json
import hashlib
from text_clean import canonical_subject, sender_domain

def content_hash(meta: dict) -> str:
    """Compute a stable hash over key fields to detect exact duplicates when the Message-ID is missing."""
    s = json.dumps({
        "From": meta.get("From"),
        "To": meta.get("To"),
        "Cc": meta.get("Cc"),
        "Subject": meta.get("Subject"),
        "Body": meta.get("Body"),
        "Received": meta.get("Received")
    }, sort_keys=True, ensure_ascii=False).encode("utf-8", errors="ignore")
    return hashlib.sha256(s).hexdigest()

def message_key(meta: dict) -> str:
    """Return MID:<Message-ID> if available, otherwise HASH:<sha256(all fields)>."""
    mid = (meta.get("MessageID") or "").strip()
    if mid:
        return f"MID:{mid}"
    return f"HASH:{content_hash(meta)}"

def thread_key(meta: dict) -> str:
    """
    Return the parent conversation key.
    The preferred strategy would use Thread-Index / References headers, but for portability,
    we fall back to a canonicalized subject (lowercased, with Re:/Fwd: noise removed).
    """
    return canonical_subject(meta.get("Subject", ""))

def update_group_key(meta: dict, clean_body_head: str) -> str:
    """
    Group near-duplicate 'versions' of a message together by hashing:
      sender_domain + '|' + canonical_subject + '|' + first N characters of the cleaned body.
    """
    dom = sender_domain(meta.get("From", ""))
    subj = canonical_subject(meta.get("Subject", ""))
    raw = (dom + "|" + subj + "|" + (clean_body_head or "")).encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()
