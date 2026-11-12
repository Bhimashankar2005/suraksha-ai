import re
import ipaddress
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from backend.app.core.ssrf_guard import validate_url_and_check_ssrf

@dataclass
class UrlAnalysisResult:
    url: str
    domain: str
    risk_score: int  # 0 to 100
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    is_ip_host: bool
    has_ssl: bool
    is_shortened: bool
    lookalike_target: Optional[str]
    matched_indicators: List[Dict[str, Any]]
    analysis_details: Dict[str, Any]
    explanation: str
    recommendations: List[str]

# -------------------------------------------------------------------------
# Verified Authentic Indian Portals (Target Reference List)
# -------------------------------------------------------------------------

TRUSTED_BRAND_DOMAINS = {
    "onlinesbi.sbi": "State Bank of India",
    "sbi.co.in": "State Bank of India",
    "hdfcbank.com": "HDFC Bank",
    "icicibank.com": "ICICI Bank",
    "axisbank.com": "Axis Bank",
    "pnbindia.in": "Punjab National Bank",
    "kotak.com": "Kotak Mahindra Bank",
    "bankofbaroda.in": "Bank of Baroda",
    "canarabank.com": "Canara Bank",
    "paytm.com": "Paytm",
    "phonepe.com": "PhonePe",
    "google.com": "Google Pay",
    "bhimupi.org.in": "BHIM UPI",
    "npci.org.in": "NPCI",
    "incometax.gov.in": "Income Tax Department",
    "uidai.gov.in": "UIDAI (Aadhaar)",
    "cybercrime.gov.in": "National Cyber Crime Reporting Portal",
    "digilocker.gov.in": "DigiLocker",
    "epfindia.gov.in": "EPFO",
    "amazon.in": "Amazon India",
    "flipkart.com": "Flipkart",
    "jio.com": "Reliance Jio",
    "airtel.in": "Bharti Airtel"
}

DANGEROUS_TLDS = {
    "xyz", "top", "live", "cam", "work", "rest", "buzz", "fit",
    "apk", "cfd", "sbs", "icu", "click", "link", "gq", "ml", "cf"
}

KNOWN_SHORTENERS = {
    "bit.ly", "tinyurl.com", "is.gd", "cutt.ly", "t.co", "rb.gy",
    "shorturl.at", "ow.ly", "buff.ly", "rebrand.ly"
}

SUSPICIOUS_PATH_KEYWORDS = [
    "kyc", "pan", "verify", "verification", "update", "unblock",
    "suspended", "login", "auth", "secure", "otp", "cashback",
    "lottery", "claim", "reward", "bonus", "free", "gift"
]

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

class IntelligentUrlScanner:
    """
    Intelligent Phishing URL Scanner with strict SSRF defense,
    lookalike homoglyph comparison, and pattern heuristics.
    """

    def analyze_url(self, raw_url: str) -> UrlAnalysisResult:
        clean_url = raw_url.strip()
        if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
            clean_url = "https://" + clean_url

        # 1. Strictly enforce SSRF Protection
        is_safe_ssrf, domain, ssrf_error = validate_url_and_check_ssrf(clean_url)
        if not is_safe_ssrf:
            return UrlAnalysisResult(
                url=clean_url,
                domain=domain or "unknown",
                risk_score=100,
                risk_level="CRITICAL",
                is_ip_host=True,
                has_ssl=False,
                is_shortened=False,
                lookalike_target=None,
                matched_indicators=[{
                    "rule": "SSRF_PROHIBITED_DESTINATION",
                    "description": ssrf_error,
                    "weight": 100
                }],
                analysis_details={"ssrf_blocked": True, "reason": ssrf_error},
                explanation=f"CRITICAL SECURITY BLOCK: {ssrf_error} The platform strictly refuses connection to loopback, private, and internal addresses.",
                recommendations=["Never submit internal network addresses or metadata endpoints to public scanners."]
            )

        parsed = urlparse(clean_url)
        domain = parsed.hostname or domain
        path = parsed.path.lower()
        has_ssl = parsed.scheme == "https"

        # 2. Check for Direct IP Host
        is_ip_host = False
        try:
            ipaddress.ip_address(domain)
            is_ip_host = True
        except ValueError:
            is_ip_host = False

        # 3. Check for Shortened URLs
        is_shortened = domain in KNOWN_SHORTENERS

        # 4. Check for Domain Lookalike / Impersonation
        lookalike_target, lookalike_score, matched_brand = self._check_lookalike(domain)

        # 5. Extract Domain TLD & Structure
        domain_parts = domain.split(".")
        tld = domain_parts[-1] if domain_parts else ""
        is_suspicious_tld = tld in DANGEROUS_TLDS
        excess_subdomains = len(domain_parts) > 3

        # 6. Check for Phishing Keywords in Path / Subdomain
        found_keywords = []
        for kw in SUSPICIOUS_PATH_KEYWORDS:
            if re.search(r"\b" + kw + r"\b", path) or re.search(r"\b" + kw + r"\b", domain):
                found_keywords.append(kw)

        # 7. Aggregate Risk Score & Indicators
        risk_score = 0
        indicators = []

        if is_ip_host:
            risk_score += 60
            indicators.append({
                "rule": "RAW_IP_HOST",
                "description": "URL specifies a numeric IP address instead of an official registered domain name.",
                "weight": 60
            })

        if lookalike_target:
            risk_score += 65
            indicators.append({
                "rule": "HOMOGLYPH_LOOKALIKE_DOMAIN",
                "description": f"Domain name impersonates authentic entity '{lookalike_target}'.",
                "weight": 65
            })

        if is_suspicious_tld:
            risk_score += 30
            indicators.append({
                "rule": "HIGH_RISK_TLD",
                "description": f"Top-level domain '.{tld}' is frequently utilized in disposable phishing campaigns.",
                "weight": 30
            })

        if not has_ssl:
            risk_score += 25
            indicators.append({
                "rule": "UNENCRYPTED_HTTP",
                "description": "Connection lacks HTTPS encryption. Credential theft or eavesdropping is trivial.",
                "weight": 25
            })

        if is_shortened:
            risk_score += 25
            indicators.append({
                "rule": "SHORTENED_URL_MASK",
                "description": "URL uses a shortener service hiding the genuine target destination.",
                "weight": 25
            })

        if excess_subdomains:
            risk_score += 20
            indicators.append({
                "rule": "EXCESS_SUBDOMAINS",
                "description": "Unusually deep subdomain structure often engineered to deceive victims.",
                "weight": 20
            })

        if found_keywords:
            risk_score += 20
            indicators.append({
                "rule": "PHISHING_KEYWORDS_FOUND",
                "description": f"Suspicious security keywords detected: {', '.join(found_keywords)}",
                "weight": 20
            })

        # Whitelist exemption for genuine official domains with valid HTTPS
        if domain in TRUSTED_BRAND_DOMAINS and has_ssl and not is_ip_host:
            risk_score = 0
            indicators = [{
                "rule": "AUTHENTIC_VERIFIED_PORTAL",
                "description": f"Verified official digital portal for {TRUSTED_BRAND_DOMAINS[domain]}.",
                "weight": 0
            }]

        risk_score = min(max(risk_score, 0), 100)

        # 8. Determine Risk Level
        if risk_score >= 70:
            risk_level = "CRITICAL"
        elif risk_score >= 45:
            risk_level = "HIGH"
        elif risk_score >= 20:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # 9. Formulate Explanation & Recommendations
        explanation = self._build_explanation(risk_level, domain, lookalike_target, indicators, has_ssl)
        recommendations = self._build_recommendations(risk_level, lookalike_target, is_shortened, has_ssl)

        analysis_details = {
            "protocol": parsed.scheme.upper(),
            "has_ssl": has_ssl,
            "tld": tld,
            "subdomains_count": len(domain_parts) - 2 if len(domain_parts) >= 2 else 0,
            "is_ip_host": is_ip_host,
            "is_shortened": is_shortened,
            "detected_keywords": found_keywords,
            "matched_brand": matched_brand
        }

        return UrlAnalysisResult(
            url=clean_url,
            domain=domain,
            risk_score=risk_score,
            risk_level=risk_level,
            is_ip_host=is_ip_host,
            has_ssl=has_ssl,
            is_shortened=is_shortened,
            lookalike_target=lookalike_target,
            matched_indicators=indicators,
            analysis_details=analysis_details,
            explanation=explanation,
            recommendations=recommendations
        )

    def _check_lookalike(self, domain: str) -> Tuple[Optional[str], int, Optional[str]]:
        """
        Check if the domain impersonates any trusted Indian banking,
        UPI, or government entities using token matching & edit distance.
        """
        domain_clean = domain.lower()

        # If it's literally the authentic domain, it is NOT an impersonator
        if domain_clean in TRUSTED_BRAND_DOMAINS:
            return None, 0, None

        for legitimate_domain, brand_name in TRUSTED_BRAND_DOMAINS.items():
            base_legit = legitimate_domain.split(".")[0]

            # 1. Look for brand name embedded with hyphens or extra subdomains (e.g. onlinesbi-update.xyz)
            if base_legit in domain_clean:
                return f"{brand_name} ({legitimate_domain})", 85, brand_name

            # 2. Levenshtein edit distance check on the core SLD
            submitted_sld = domain_clean.split(".")[0]
            dist = levenshtein_distance(submitted_sld, base_legit)
            if 0 < dist <= 2 and len(base_legit) >= 4:
                return f"{brand_name} ({legitimate_domain})", 90, brand_name

        return None, 0, None

    def _build_explanation(
        self,
        risk_level: str,
        domain: str,
        lookalike_target: Optional[str],
        indicators: List[Dict[str, Any]],
        has_ssl: bool
    ) -> str:
        if risk_level == "CRITICAL":
            reasons = "; ".join([ind["description"] for ind in indicators])
            return (
                f"CRITICAL PHISHING THREAT DETECTED. Domain '{domain}' exhibits severe deception indicators: {reasons}. "
                "Visiting this destination may lead to credential harvesting, unauthorized UPI transfers, or malware downloads."
            )
        elif risk_level == "HIGH":
            return (
                f"HIGH RISK DETECTED: The domain '{domain}' matches known phishing patterns or uses an unverified/dangerous top-level domain. "
                "Exercise extreme caution. Do not enter personal, banking, or login credentials."
            )
        elif risk_level == "MEDIUM":
            return (
                f"MODERATE CAUTION: Destination '{domain}' contains masking characteristics (such as a shortened URL or unencrypted HTTP). "
                "Always verify the final landing destination before taking any action."
            )
        else:
            return (
                f"LOW RISK: Domain '{domain}' does not exhibit active homoglyph deception or known malicious patterns. "
                "Note: A clean scan does not guarantee absolute safety. Always look for the browser lock icon and verified organization names."
            )

    def _build_recommendations(
        self,
        risk_level: str,
        lookalike_target: Optional[str],
        is_shortened: bool,
        has_ssl: bool
    ) -> List[str]:
        recs = [
            "Never enter your NetBanking password, debit card details, or UPI PIN on unverified websites."
        ]

        if lookalike_target:
            recs.append(f"This URL falsely imitates {lookalike_target}. Only access the official portal by typing the genuine URL into your browser directly.")
        if is_shortened:
            recs.append("Shortened links mask the true destination. Do not click shortened links received from unknown senders.")
        if not has_ssl:
            recs.append("This site lacks HTTPS. Any data transmitted can be intercepted by third parties on public networks.")

        recs.append("Report suspected cyber fraud domains immediately to helpline 1930 or cybercrime.gov.in.")
        return recs

# Singleton instance
url_scanner = IntelligentUrlScanner()

