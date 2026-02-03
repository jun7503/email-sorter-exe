import re

def strip_quoted(text: str) -> str:
    """Remove quoted replies."""
    lines = text.splitlines()
    out = []
    for ln in lines:
        if re.match(r'^\\s*>', ln):
            continue
        if re.search(r'^\\s*On .+ wrote:\\s*$', ln):
            break
        if re.search(r'^\\s*(De|Von)\\s*:.*$', ln):
            break
        out.append(ln)
    return "\\n".join(out)

def strip_signature(text: str) -> str:
    """Remove common signatures."""
    patterns = [
        r'^\\s*--\\s*$',
        r'^\\s*Best regards.*$',
        r'^\\s*Regards,.*$',
        r'^\\s*Mit freundlichen Grüßen.*$',
        r'^\\s*Cordialement.*$',
        r'^\\s*Thank you.*$'
    ]
    lines = text.splitlines()
    out = []
    for ln in lines:
        if any(re.match(p, ln, flags=re.I) for p in patterns):
            break
        out.append(ln)
    return "\\n".join(out)

def strip_disclaimers(text: str) -> str:
    return re.sub(r'(?is)(This message.*?confidential.*?$)', '', text)

def normalize_ws(text: str) -> str:
    text = re.sub(r'\\r\\n', '\\n', text)
    text = re.sub(r'[ \\t]+', ' ', text)
    text = re.sub(r'\\n{3,}', '\\n\\n', text)
    return text.strip()

def clean_body_for_semantics(body: str) -> str:
    t = strip_quoted(body or "")
    t = strip_signature(t)
    t = strip_disclaimers(t)
    return normalize_ws(t)

def canonical_subject(subject: str) -> str:
    s = subject or ""
    s = re.sub(r'^\\s*(RE|FWD|FW)\\s*[:\\-]\\s*', '', s, flags=re.I)
    s = re.sub(r'\\[[^\\]]+\\]\\s*', '', s)
    s = re.sub(r'\\s+', ' ', s)
    return s.strip().lower()

def sender_domain(sender_field: str) -> str:
    """Extract domain from sender email."""
    m = re.search(r'@([A-Za-z0-9\\.\\-]+)', sender_field or "")
    return (m.group(1).lower() if m else "unknown.local")
``
