# -*- coding: utf-8 -*-
import re

ISSUE_PATTERNS = [
    r"\bINC-\d+\b",
    r"\bPRB-\d+\b",
    r"\bSR\d+\b",
    r"\b[A-Z]{2,10}-\d+\b",       # JIRA-like ABC-123
    r"#\d{3,10}\b"
]

MILESTONE_PATTERNS = [
    r"\bM(?:ilestone)?\s?\d+\b",
    r"\bRelease\s?R\d+\b",
    r"\bR\d+\b",
    r"\bSprint\s?\d+\b",
    r"\bGo-?Live\b",
    r"\bBeta\b",
    r"\bRC\b"
]

def extract_issue(subject: str, body: str) -> str:
    text = f"{subject}\n{body}"
    for pat in ISSUE_PATTERNS:
        m = re.search(pat, text, flags=re.I)
        if m:
            return m.group(0)
    return ""

def extract_milestone(subject: str, body: str) -> str:
    text = f"{subject}\n{body}"
    for pat in MILESTONE_PATTERNS:
        m = re.search(pat, text, flags=re.I)
        if m:
            return m.group(0)
    return ""

def extract_issue_milestone(subject: str, body: str):
    return extract_issue(subject, body), extract_milestone(subject, body)
