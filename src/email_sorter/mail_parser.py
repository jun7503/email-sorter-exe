import os
import email
from email import policy
from email.parser import BytesParser
import extract_msg
from datetime import datetime

def _safe(x):
    return x or ""

def parse_eml(path: str):
    """Parse a .eml file and extract metadata and body content."""
    with open(path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)

    message_id = _safe(msg.get("Message-ID")).strip()
    subject    = _safe(msg.get("Subject"))
    sender     = _safe(msg.get("From"))
    to         = _safe(msg.get("To"))
    cc         = _safe(msg.get("Cc"))
    date_raw   = msg.get("Date")

    try:
        dt = email.utils.parsedate_to_datetime(date_raw) if date_raw else None
        received = dt.isoformat(sep=" ") if dt else _safe(date_raw)
    except Exception:
        received = _safe(date_raw)

    body = extract_text_body(msg)

    return {
        "MessageID": message_id,
        "Subject": subject,
        "From": sender,
        "To": to,
        "Cc": cc,
        "Sender": sender,
        "Received": received,
        "Body": body
    }

def extract_text_body(msg):
    """Extract the plain text body, falling back to HTML content if needed."""
    if msg.is_multipart():
        # Prefer plain text
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and (part.get_content_disposition() or "") != "attachment":
                try:
                    return part.get_content()
                except Exception:
                    pass

        # Fallback to HTML
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                try:
                    return html_to_text(part.get_content())
                except Exception:
                    pass

        return ""
    else:
        ctype = msg.get_content_type()
        if ctype == "text/plain":
            return msg.get_content()
        if ctype == "text/html":
            return html_to_text(msg.get_content())

        try:
            return msg.get_content()
        except Exception:
            return ""

def html_to_text(html):
    """Basic HTML-to-text converter."""
    import re
    t = re.sub(r"<(script|style)[\s\S]*?</\1>", "", html, flags=re.I)
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"</p>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    return t.replace("&nbsp;", " ")

def parse_msg(path: str):
    """Parse an Outlook .msg file and extract metadata and body content."""
    msg = extract_msg.Message(path)

    subject     = _safe(msg.subject)
    sender      = _safe(msg.sender)
    to          = _safe(msg.to)
    cc          = _safe(msg.cc)
    message_id  = _safe(msg.headerDict.get("Message-ID", "")).strip()
    received    = _safe(str(msg.date))

    try:
        body = msg.body or ""
    except Exception:
        body = ""

    return {
        "MessageID": message_id,
        "Subject": subject,
        "From": sender,
        "To": to,
        "Cc": cc,
        "Sender": sender,
        "Received": received,
        "Body": body
    }

def parse_email_file(path: str):
    """Dispatch to the appropriate parser based on file extension."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".eml":
        return parse_eml(path)
    if ext == ".msg":
        return parse_msg(path)
    raise ValueError(f"Unsupported file type: {ext}")
``
