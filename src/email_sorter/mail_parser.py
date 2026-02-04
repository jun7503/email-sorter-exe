import os
import hashlib
import logging
import email
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from datetime import datetime
from pathlib import Path
from html import unescape as html_unescape

logger = logging.getLogger(__name__)

def _safe(x):
    return x or ""

def parse_email_file(path: str):
    """Dispatch to the appropriate parser based on file extension."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".eml":
        return parse_eml(path)
    if ext == ".msg":
        return parse_msg(path)
    raise ValueError(f"Unsupported file type: {ext}")

# -------------------------
# EML
# -------------------------
def parse_eml(path: str):
    """Parse a .eml file and extract metadata and body content."""
    with open(path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)

    message_id = _safe(msg.get("Message-ID")).strip()
    subject    = _safe(msg.get("Subject")).strip()
    sender     = _safe(msg.get("From")).strip()
    to         = _safe(msg.get("To")).strip()
    cc         = _safe(msg.get("Cc")).strip()
    date_raw   = msg.get("Date")

    # Date normalization
    received = _normalize_date_str(date_raw)

    # Prefer text/plain; fallback to text/html -> text; final fallback to any content
    body = extract_text_body(msg)

    # Build combined Text for clustering/dedup
    text_for_topic = f"{subject}\n{body}".strip()
    if not text_for_topic:
        logger.warning("Empty content (EML) in %s", path)
        return None

    # Fallback MessageID if missing
    if not message_id:
        ident_source = (subject + sender + text_for_topic[:1000])
        message_id = f"<sha256:{hashlib.sha256(ident_source.encode('utf-8','ignore')).hexdigest()}>"

    return {
        "MessageID": message_id,
        "Subject": subject,
        "From": sender,
        "To": to,
        "Cc": cc,
        "Sender": sender,
        "Received": received,  # string ISO or original header when parse fails
        "Body": body,
        "Text": text_for_topic,  # <-- IMPORTANT for downstream steps
        "Path": str(Path(path)),
    }

def extract_text_body(msg):
    """Extract plain text; fallback to HTML→text; final fallback to get_content()."""
    if msg.is_multipart():
        # Prefer plain text
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and (part.get_content_disposition() or "") != "attachment":
                try:
                    return _coerce_text(part.get_content())
                except Exception:
                    pass

        # Fallback to HTML
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                try:
                    return html_to_text(_coerce_text(part.get_content()))
                except Exception:
                    pass

        # Fallback: try any string content
        for part in msg.walk():
            try:
                c = part.get_content()
                if isinstance(c, str) and c.strip():
                    return _coerce_text(c)
            except Exception:
                pass
        return ""
    else:
        ctype = msg.get_content_type()
        try:
            if ctype == "text/plain":
                return _coerce_text(msg.get_content())
            if ctype == "text/html":
                return html_to_text(_coerce_text(msg.get_content()))
            # final fallback
            return _coerce_text(msg.get_content())
        except Exception:
            return ""

def html_to_text(html):
    """
    Basic HTML-to-text converter.
    Works with real HTML tags by first unescaping entities.
    """
    import re
    if not html:
        return ""
    # Convert HTML entities to real characters first (&lt; -> <)
    s = html_unescape(html)

    # Remove script/style blocks
    s = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", s)
    # Replace <br> and <p> with newlines
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</p\s*>", "\n", s)
    # Strip all tags
    s = re.sub(r"(?s)<[^>]+>", "", s)
    # Normalize whitespace
    s = re.sub(r"\r\n|\r", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def _coerce_text(x):
    # Ensure we always return a string
    if x is None:
        return ""
    if isinstance(x, bytes):
        try:
            return x.decode("utf-8", "ignore")
        except Exception:
            return x.decode(errors="ignore")
    return str(x)

def _normalize_date_str(date_raw):
    """Try to parse RFC822 Date header → ISO; else return original string."""
    try:
        dt = parsedate_to_datetime(date_raw) if date_raw else None
        if dt and dt.tzinfo is not None:
            return dt.isoformat(sep=" ")
        if dt:
            # Assume naive local time
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    return _safe(date_raw)

# -------------------------
# MSG
# -------------------------
def parse_msg(path: str):
    """Parse an Outlook .msg file and extract metadata and body content."""
    try:
        import extract_msg  # keep local so PyInstaller can include via hidden-import
    except Exception as e:
        logger.exception("extract_msg not available in this build: %s", e)
        return None

    m = extract_msg.Message(path)

    subject     = _safe(getattr(m, "subject", None)).strip()
    sender      = _safe(getattr(m, "sender", None) or getattr(m, "sender_email", None)).strip()
    to          = _safe(getattr(m, "to", None)).strip()
    cc          = _safe(getattr(m, "cc", None)).strip()

    # Message-ID can be under different cases
    header_dict = getattr(m, "headerDict", {}) or {}
    message_id  = _safe(header_dict.get("Message-ID") or header_dict.get("Message-Id") or header_dict.get("MessageId") or "").strip()

    # Date: extract_msg.date may be datetime or str
    date_val = getattr(m, "date", None)
    received = _coerce_msg_date(date_val)

    # Body: MSG can be RTF-only; extract_msg usually converts; add fallback
    try:
        body = _coerce_text(getattr(m, "body", None) or "")
    except Exception:
        body = ""

    if not body:
        # best-effort fallback
        try:
            body = _coerce_text(str(m))
        except Exception:
            body = ""

    text_for_topic = f"{subject}\n{body}".strip()
    if not text_for_topic:
        logger.warning("Empty content (MSG) in %s", path)
        return None

    if not message_id:
        ident_source = (subject + sender + text_for_topic[:1000])
        message_id = f"<sha256:{hashlib.sha256(ident_source.encode('utf-8','ignore')).hexdigest()}>"

    return {
        "MessageID": message_id,
        "Subject": subject,
        "From": sender,
        "To": to,
        "Cc": cc,
        "Sender": sender,
        "Received": received,
        "Body": body,
        "Text": text_for_topic,  # <-- IMPORTANT
        "Path": str(Path(path)),
    }

def _coerce_msg_date(d):
    """Normalize extract_msg date to a string."""
    if d is None:
        return ""
    if isinstance(d, datetime):
        try:
            # keep timezone if present
            return d.isoformat(sep=" ")
        except Exception:
            return d.strftime("%Y-%m-%d %H:%M:%S")
    # Sometimes it's like '2026-02-03 09:12:00+00:00' already
    return _coerce_text(d)
