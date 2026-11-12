import re
from typing import Dict, Any, List, Tuple, Optional

# --- Verhoeff Algorithm Tables for Aadhaar Checksum Validation ---
VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
]

VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
]

def validate_verhoeff(num_str: str) -> bool:
    """Validates Aadhaar number using official Verhoeff checksum algorithm."""
    digits = [int(c) for c in num_str if c.isdigit()]
    if len(digits) != 12:
        return False
    c = 0
    for i, digit in enumerate(reversed(digits)):
        c = VERHOEFF_D[c][VERHOEFF_P[i % 8][digit]]
    return c == 0

def validate_luhn(card_str: str) -> bool:
    """Validates 16-digit credit or debit card using Luhn checksum."""
    digits = [int(c) for c in card_str if c.isdigit()]
    if len(digits) != 16:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = d * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += d
    return checksum % 10 == 0

class PrivacyScanner:
    """
    Zero-Cloud, Pure In-Memory Personal Data & Privacy Protection Engine.
    Detects Indian Sensitive Identifiers: Aadhaar, PAN, Phone, Email, Cards, UPI VPA.
    Provides verified masking, redaction preview, risk score, and safety advice.
    """

    KNOWN_UPI_HANDLES = {
        "okhdfcbank", "okaxis", "oksbi", "okicici", "ybl", "ibl", "axl", "apl",
        "paytm", "upi", "barodampay", "fbl", "postbank", "federal", "indus"
    }

    def scan_and_redact(self, text: str) -> Dict[str, Any]:
        """
        Analyzes raw text for sensitive identifiers.
        Returns detected entities, risk score, severity band, sanitized text, and recommendations.
        """
        if not text:
            return {
                "detected_entities": [],
                "detected_counts": {},
                "risk_score": 0,
                "risk_level": "LOW",
                "sanitized_text": "",
                "recommendations": []
            }

        entities: List[Dict[str, Any]] = []
        replaced_spans: List[Tuple[int, int, str]] = []

        # 1. Detect Aadhaar Numbers (12 digits, cannot start with 0 or 1)
        aadhaar_regex = re.compile(r"\b([2-9]\d{3}[ -]?\d{4}[ -]?\d{4})\b")
        for match in aadhaar_regex.finditer(text):
            raw = match.group(1)
            digits_only = re.sub(r"\D", "", raw)
            if len(digits_only) == 12:
                is_verhoeff = validate_verhoeff(digits_only)
                # Mask first 8 digits: XXXX-XXXX-1234
                last4 = digits_only[-4:]
                separator = "-" if "-" in raw else (" " if " " in raw else "")
                redacted = f"XXXX{separator}XXXX{separator}{last4}"

                entities.append({
                    "type": "AADHAAR",
                    "raw_preview": f"•••• •••• {last4}",
                    "start": match.start(1),
                    "end": match.end(1),
                    "is_checksum_valid": is_verhoeff,
                    "confidence": 0.98 if is_verhoeff else 0.85
                })
                replaced_spans.append((match.start(1), match.end(1), redacted))

        # 2. Detect PAN Numbers ([A-Z]{5}[0-9]{4}[A-Z])
        pan_regex = re.compile(r"\b([A-Z]{5}[0-9]{4}[A-Z])\b")
        for match in pan_regex.finditer(text):
            raw = match.group(1)
            # Mask as XXXXX1234X
            redacted = f"XXXXX{raw[5:9]}{raw[9]}"
            entities.append({
                "type": "PAN",
                "raw_preview": redacted,
                "start": match.start(1),
                "end": match.end(1),
                "is_checksum_valid": True,
                "confidence": 0.99
            })
            replaced_spans.append((match.start(1), match.end(1), redacted))

        # 3. Detect 16-Digit Credit / Debit Cards
        card_regex = re.compile(r"\b(\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4})\b")
        for match in card_regex.finditer(text):
            # Check if this span was already matched by Aadhaar
            if any(s <= match.start(1) < e for s, e, _ in replaced_spans):
                continue
            raw = match.group(1)
            digits_only = re.sub(r"\D", "", raw)
            if len(digits_only) == 16:
                is_luhn = validate_luhn(digits_only)
                last4 = digits_only[-4:]
                redacted = f"XXXX-XXXX-XXXX-{last4}"
                entities.append({
                    "type": "PAYMENT_CARD",
                    "raw_preview": redacted,
                    "start": match.start(1),
                    "end": match.end(1),
                    "is_checksum_valid": is_luhn,
                    "confidence": 0.95 if is_luhn else 0.75
                })
                replaced_spans.append((match.start(1), match.end(1), redacted))

        # 4. Detect Indian Phone Numbers
        phone_regex = re.compile(r"(?:\+91[\-\s]?)?([6-9]\d{4}[\-\s]?\d{5})\b")
        for match in phone_regex.finditer(text):
            if any(s <= match.start() < e for s, e, _ in replaced_spans):
                continue
            raw = match.group(0)
            digits_only = re.sub(r"\D", "", raw)
            if len(digits_only) >= 10:
                core10 = digits_only[-10:]
                redacted = f"+91 XXXXX {core10[-5:]}"
                entities.append({
                    "type": "PHONE_NUMBER",
                    "raw_preview": redacted,
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.95
                })
                replaced_spans.append((match.start(), match.end(), redacted))

        # 5. Detect Email Addresses
        email_regex = re.compile(r"\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b")
        for match in email_regex.finditer(text):
            if any(s <= match.start() < e for s, e, _ in replaced_spans):
                continue
            user_part = match.group(1)
            domain_part = match.group(2)
            if len(user_part) <= 2:
                masked_user = user_part[0] + "*"
            else:
                masked_user = user_part[0] + "***" + user_part[-1]
            redacted = f"{masked_user}@{domain_part}"
            entities.append({
                "type": "EMAIL",
                "raw_preview": redacted,
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.99
            })
            replaced_spans.append((match.start(), match.end(), redacted))

        # 6. Detect UPI IDs (VPA)
        upi_regex = re.compile(r"\b([a-zA-Z0-9.\-_]{2,64})@([a-zA-Z]{2,32})\b")
        for match in upi_regex.finditer(text):
            if any(s <= match.start() < e for s, e, _ in replaced_spans):
                continue
            handle = match.group(2).lower()
            if handle in self.KNOWN_UPI_HANDLES:
                user_part = match.group(1)
                masked_user = user_part[0] + "***" + (user_part[-1] if len(user_part) > 1 else "")
                redacted = f"{masked_user}@{handle}"
                entities.append({
                    "type": "UPI_ID",
                    "raw_preview": redacted,
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.95
                })
                replaced_spans.append((match.start(), match.end(), redacted))

        # Generate Sanitized String by replacing spans in reverse order
        sanitized_chars = list(text)
        sorted_spans = sorted(replaced_spans, key=lambda x: x[0], reverse=True)
        for start, end, repl in sorted_spans:
            sanitized_chars[start:end] = list(repl)
        sanitized_text = "".join(sanitized_chars)

        # Count by entity type
        counts: Dict[str, int] = {}
        for ent in entities:
            t = ent["type"]
            counts[t] = counts.get(t, 0) + 1

        # Calculate Privacy Risk Score
        raw_score = (
            counts.get("PAYMENT_CARD", 0) * 40 +
            counts.get("AADHAAR", 0) * 35 +
            counts.get("PAN", 0) * 30 +
            counts.get("UPI_ID", 0) * 15 +
            counts.get("PHONE_NUMBER", 0) * 15 +
            counts.get("EMAIL", 0) * 10
        )
        risk_score = min(raw_score, 100)

        if risk_score >= 85:
            risk_level = "CRITICAL"
        elif risk_score >= 60:
            risk_level = "HIGH"
        elif risk_score >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Generate Actionable Privacy Recommendations
        recommendations = []
        if counts.get("AADHAAR", 0) > 0:
            recommendations.append(
                "Aadhaar exposed: Immediately open mAadhaar app or visit myaadhaar.uidai.gov.in and activate 'Biometric Lock' to prevent fingerprint misuse."
            )
        if counts.get("PAN", 0) > 0:
            recommendations.append(
                "PAN exposed: Check your CIBIL credit report periodically to ensure no ghost loans or credit cards are opened under your identity."
            )
        if counts.get("PAYMENT_CARD", 0) > 0:
            recommendations.append(
                "Debit/Credit Card exposed: Contact your issuing bank immediately to block the card and issue a replacement with a new CVV."
            )
        if counts.get("PHONE_NUMBER", 0) > 0:
            recommendations.append(
                "Phone exposed: Check DoT Sanchar Saathi (sancharsaathi.gov.in / TAFCOP) to verify all SIM cards registered under your identity."
            )
        if not recommendations:
            recommendations.append("No sensitive Indian financial or identity credentials detected in this text.")

        return {
            "detected_entities": entities,
            "detected_counts": counts,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "sanitized_text": sanitized_text,
            "recommendations": recommendations
        }

privacy_scanner = PrivacyScanner()

