import io
import hashlib
import re
import shutil
from typing import Tuple, Optional, Dict, Any, List
from PIL import Image
from dataclasses import dataclass
from backend.app.ml.scam_classifier import scam_classifier, ScamAnalysisResult

@dataclass
class ImageAnalysisResult:
    file_hash: str
    file_name: str
    file_size_bytes: int
    dimensions: Tuple[int, int]
    mime_type: str
    extracted_text: str
    risk_score: int
    risk_level: str
    scam_category: str
    detected_entities: Dict[str, Any]
    matched_indicators: List[Dict[str, Any]]
    highlighted_tokens: List[str]
    explanation: str
    recommendations: List[str]
    ocr_engine: str

# Magic bytes signature validation
MAGIC_SIGNATURES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"]  # and "WEBP" at offset 8
}

PAYMENT_SCREENSHOT_PATTERNS = [
    {
        "id": "PAYMENT_CONFIRMATION_PATTERN",
        "description": "Payment confirmation / success receipt pattern detected.",
        "weight": 35,
        "patterns": [
            r"\b(payment\s+successful|paid\s+successfully|transaction\s+successful)\b",
            r"\b(transfer\s+successful|sent\s+successfully|debited\s+from)\b",
            r"\b(utr|upi\s+ref(\s+no)?|txn\s+id)\s*[:#]?\s*[a-zA-Z0-9]+\b"
        ]
    },
    {
        "id": "UPI_RECEIVE_DECEPTION_IMAGE",
        "description": "QR code or receipt stating money will be received or credited.",
        "weight": 50,
        "patterns": [
            r"\b(scan\s+qr\s+to\s+receive|enter\s+pin\s+to\s+credit)\b",
            r"\breceive\s+cashback\s+of\s+rs\b",
            r"\bcashback\s+received\b"
        ]
    },
    {
        "id": "BANK_APP_IMPERSONATION",
        "description": "Branded payment application UI markers.",
        "weight": 20,
        "patterns": [
            r"\b(phonepe|paytm|google\s+pay|gpay|bhim|cred)\b",
            r"\b(state\s+bank\s+of\s+india|hdfc\s+bank|icici\s+bank)\b"
        ]
    }
]

def validate_and_hash_image(file_bytes: bytes, original_filename: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate image file magic bytes, format, dimensions, and compute SHA-256 hash.
    Returns: (is_valid: bool, error_message: Optional[str], metadata: Optional[dict])
    """
    if not file_bytes or len(file_bytes) == 0:
        return False, "Uploaded file is empty.", None

    if len(file_bytes) > 15 * 1024 * 1024:
        return False, "File exceeds maximum size limit of 15MB.", None

    # Compute cryptographic SHA-256 hash
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()

    # Verify Magic Bytes
    detected_mime = None
    if file_bytes.startswith(b"\xff\xd8\xff"):
        detected_mime = "image/jpeg"
    elif file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        detected_mime = "image/png"
    elif file_bytes.startswith(b"RIFF") and len(file_bytes) >= 12 and file_bytes[8:12] == b"WEBP":
        detected_mime = "image/webp"

    if not detected_mime:
        return False, "Unsupported file format. Please upload JPG, JPEG, PNG, or WEBP.", None

    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            width, height = img.size
            img_format = img.format
            # Verify image can actually be decoded
            img.verify()
    except Exception as e:
        return False, f"Image decoding failed or file is corrupted: {str(e)}", None

    metadata = {
        "file_hash": sha256_hash,
        "file_name": original_filename,
        "file_size_bytes": len(file_bytes),
        "mime_type": detected_mime,
        "dimensions": (width, height),
        "format": img_format
    }
    return True, None, metadata

def perform_ocr_extraction(file_bytes: bytes, provided_text: Optional[str] = None) -> Tuple[str, str]:
    """
    Extract text using Tesseract OCR if available, otherwise resilient Python parser.
    Returns: (extracted_text: str, engine_used: str)
    """
    if provided_text and provided_text.strip():
        return provided_text.strip(), "DIRECT_OR_TEST_INPUT"

    # Check if tesseract binary exists in system path
    has_tesseract = shutil.which("tesseract") is not None
    if has_tesseract:
        try:
            import pytesseract
            with Image.open(io.BytesIO(file_bytes)) as img:
                extracted = pytesseract.image_to_string(img)
                if extracted.strip():
                    return extracted.strip(), "TESSERACT_OCR"
        except Exception:
            pass

    # Resilient fallback: Return clean message when pure image lacks binary OCR
    return (
        "Image uploaded and validated. Forensic metadata inspected. "
        "No machine-readable OCR text detected or OCR binary uninstalled.",
        "PILLOW_METADATA_FALLBACK"
    )

def analyze_screenshot_content(
    file_bytes: bytes,
    file_name: str,
    ocr_text_override: Optional[str] = None
) -> ImageAnalysisResult:
    """
    Analyze image screenshot for scam indicators, payment spoofing, and fraud text.
    """
    is_valid, err, meta = validate_and_hash_image(file_bytes, file_name)
    if not is_valid or not meta:
        raise ValueError(err or "Invalid image file")

    extracted_text, ocr_engine = perform_ocr_extraction(file_bytes, ocr_text_override)

    # 1. Run Scam Classifier on Extracted Text
    scam_res: ScamAnalysisResult = scam_classifier.analyze_message(extracted_text)

    # 2. Check for Specific Payment Screenshot Patterns
    detected_entities = {
        "is_payment_screenshot": False,
        "detected_apps": [],
        "utr_references": [],
        "amounts_mentioned": []
    }

    matched_indicators = list(scam_res.matched_indicators)
    payment_heuristic_score = 0

    for rule in PAYMENT_SCREENSHOT_PATTERNS:
        matched_in_rule = []
        for pattern in rule["patterns"]:
            matches = re.findall(pattern, extracted_text, re.IGNORECASE)
            if matches:
                for m in matches:
                    term = " ".join([x for x in m if x]) if isinstance(m, tuple) else str(m)
                    matched_in_rule.append(term)

        if matched_in_rule:
            payment_heuristic_score += rule["weight"]
            matched_indicators.append({
                "rule_id": rule["id"],
                "category": "PAYMENT_SCREENSHOT",
                "description": rule["description"],
                "weight": rule["weight"],
                "matched_terms": list(set(matched_in_rule))
            })
            if rule["id"] == "PAYMENT_CONFIRMATION_PATTERN":
                detected_entities["is_payment_screenshot"] = True
            elif rule["id"] == "BANK_APP_IMPERSONATION":
                detected_entities["detected_apps"].extend(matched_in_rule)

    # Extract currency amounts
    amounts = re.findall(r"(?:rs\.?|inr|₹)\s*(\d+(?:,\d+)*(?:\.\d+)?)\b", extracted_text, re.IGNORECASE)
    if amounts:
        detected_entities["amounts_mentioned"] = amounts

    # Extract UTR / Transaction ID references
    utrs = re.findall(r"\b(?:utr|txn|ref)\s*[:#]?\s*([a-zA-Z0-9]{8,22})\b", extracted_text, re.IGNORECASE)
    if utrs:
        detected_entities["utr_references"] = utrs

    # 3. Calculate Final Risk Score
    combined_score = max(scam_res.risk_score, min(payment_heuristic_score + (scam_res.risk_score // 2), 100))

    if combined_score >= 75:
        risk_level = "CRITICAL"
    elif combined_score >= 50:
        risk_level = "HIGH"
    elif combined_score >= 25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    category = scam_res.scam_category
    if detected_entities["is_payment_screenshot"] and category == "LEGITIMATE":
        category = "PAYMENT_RECEIPT_VERIFICATION"

    # Mandatory Safety Warning
    mandatory_disclaimer = (
        "IMPORTANT SAFETY RULE: A payment screenshot NEVER proves money was received. "
        "Fraudsters frequently use spoofing apps to fake 'Payment Successful' screens. "
        "Always independently verify credited funds inside your official banking app or official bank SMS."
    )

    explanation = scam_res.explanation
    if detected_entities["is_payment_screenshot"]:
        explanation += f" [Payment Proof Notice: {mandatory_disclaimer}]"

    recommendations = list(scam_res.recommendations)
    recommendations.insert(0, mandatory_disclaimer)

    return ImageAnalysisResult(
        file_hash=meta["file_hash"],
        file_name=file_name,
        file_size_bytes=meta["file_size_bytes"],
        dimensions=meta["dimensions"],
        mime_type=meta["mime_type"],
        extracted_text=extracted_text,
        risk_score=combined_score,
        risk_level=risk_level,
        scam_category=category,
        detected_entities=detected_entities,
        matched_indicators=matched_indicators,
        highlighted_tokens=scam_res.highlighted_tokens,
        explanation=explanation,
        recommendations=recommendations,
        ocr_engine=ocr_engine
    )

