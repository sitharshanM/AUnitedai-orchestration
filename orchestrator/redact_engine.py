import re
import math
from typing import List, Dict, Any, Optional

def shannon_entropy(s: str) -> float:
    """Calculates Shannon entropy in bits per character."""
    if not s:
        return 0.0
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    h = 0.0
    for ch, count in freq.items():
        p = count / len(s)
        h -= p * math.log2(p)
    return h

def luhn_valid(span: str) -> bool:
    """Validates credit card numbers using Luhn checksum."""
    digits = re.sub(r'[\s\-]', '', span)
    if not re.match(r'^\d{13,19}$', digits):
        return False
    total = 0
    alt = False
    for i in range(len(digits) - 1, -1, -1):
        d = ord(digits[i]) - 48
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0

def is_placeholder_span(span: str) -> bool:
    """Checks if a span matches standard placeholder patterns."""
    structural = [
        r'^your[_-]',
        r'^<[^>]*>$',
        r'^\*+$',
        r'^x{6,}$'
    ]
    for pattern in structural:
        if re.search(pattern, span, re.IGNORECASE):
            return True
    
    is_compound = "://" in span or "@" in span
    if not is_compound:
        substrings = [
            r'example',
            r'^changeme$',
            r'^redacted',
            r'^placeholder',
            r'^dummy',
            r'^fake',
            r'test[_-]?(key|token|secret)'
        ]
        for sub in substrings:
            if re.search(sub, span, re.IGNORECASE):
                return True
    return False

# Master regex list for secrets & sensitive data
REDACTION_PATTERNS = [
    # Genuinely Secret Credentials
    {"id": "aws.access_key", "regex": r'\b(AKIA[0-9A-Z]{16})\b', "token": "<REDACTED-AWS-KEY>"},
    {"id": "github.pat", "regex": r'\b(ghp_[A-Za-z0-9]{36})\b', "token": "<REDACTED-GITHUB-PAT>"},
    {"id": "github.oauth", "regex": r'\b(gho_[A-Za-z0-9]{36})\b', "token": "<REDACTED-GITHUB-OAUTH>"},
    {"id": "github.fine_grained", "regex": r'\b(github_pat_[A-Za-z0-9_]{82})\b', "token": "<REDACTED-GITHUB-PAT>"},
    {"id": "gitlab.token", "regex": r'\b(gl(?:pat|ptt|dt)-[A-Za-z0-9_-]{20,})\b', "token": "<REDACTED-GITLAB-TOKEN>"},
    {"id": "anthropic.key", "regex": r'\b(sk-ant-[A-Za-z0-9_\-]{20,})\b', "token": "<REDACTED-ANTHROPIC-KEY>"},
    {"id": "openai.key", "regex": r'\b(sk-(?:proj|svcacct|admin)-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{32,})\b', "token": "<REDACTED-OPENAI-KEY>"},
    {"id": "sendgrid.key", "regex": r'\b(SG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43})\b', "token": "<REDACTED-SENDGRID-KEY>"},
    {"id": "stripe.secret", "regex": r'\b(sk_live_[A-Za-z0-9]{24,})\b', "token": "<REDACTED-STRIPE-SECRET>"},
    {"id": "slack.token", "regex": r'\b(xox[baprs]-[A-Za-z0-9-]{10,})\b', "token": "<REDACTED-SLACK-TOKEN>"},
    {"id": "slack.webhook", "regex": r'(https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]{24})', "token": "<REDACTED-SLACK-WEBHOOK>"},
    {"id": "pem.private_key", "regex": r'(-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY-----)', "token": "<REDACTED-PRIVATE-KEY>"},
    {"id": "db.url_with_password", "regex": r'\b((?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^:\s/@]+:([^@\s/]+)@[^\s/]+)', "token": "<REDACTED-DB-URL>"},
    
    # Context-variable credentials
    {"id": "google.api_key", "regex": r'\b(AIza[0-9A-Za-z\-_]{35})\b', "token": "<REDACTED-GOOGLE-KEY>"},
    {"id": "jwt", "regex": r'\b(eyJ[A-Za-z0-9_\-]{8,}\.eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,})\b', "token": "<REDACTED-JWT>"},
    {"id": "env.kv", "regex": r'^[ \t]*(?:export[ \t]+)?[A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIALS?|DSN|AUTH|COOKIE|SESSION|PRIVATE)[ \t]*=[ \t]*[\'"]?([^\s\'"]{8,})[\'"]?', "token": "<REDACTED-ENV-SECRET>"},

    # PII Data
    {"id": "pii.email", "regex": r'\b([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})\b', "token": "<REDACTED-EMAIL>"},
    {"id": "pii.ssn", "regex": r'\b(\d{3}-\d{2}-\d{4})\b', "token": "<REDACTED-SSN>"},
    {"id": "pii.cc", "regex": r'\b((?:\d[ \-]?){13,19})\b', "token": "<REDACTED-CC>"}
]

class RedactEngine:
    """Engine for detecting and masking sensitive credentials, secrets, and PII."""
    
    def __init__(self):
        self.patterns = REDACTION_PATTERNS

    def redact(self, text: str) -> Dict[str, Any]:
        if not text or not isinstance(text, str):
            return {"sanitized_text": text, "findings": []}
            
        sanitized = text
        findings = []

        for p in self.patterns:
            matches = list(re.finditer(p["regex"], sanitized, re.MULTILINE))
            for match in matches:
                span = match.group(1) if match.lastindex else match.group(0)
                if is_placeholder_span(span):
                    continue
                    
                # Extra validation for env keys or Luhn credit cards
                if p["id"] == "env.kv" and shannon_entropy(span) < 2.5:
                    continue
                if p["id"] == "pii.cc" and not luhn_valid(span):
                    continue
                    
                findings.append({
                    "id": p["id"],
                    "token": p["token"],
                    "span": span[:4] + "..." if len(span) > 8 else "***"
                })
                sanitized = sanitized.replace(span, p["token"])

        return {
            "sanitized_text": sanitized,
            "findings_count": len(findings),
            "findings": findings
        }

# Global singleton engine
default_redactor = RedactEngine()

def redact_text(text: str) -> str:
    return default_redactor.redact(text)["sanitized_text"]
