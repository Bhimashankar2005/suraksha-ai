import re
import math
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field

@dataclass
class IndicatorMatch:
    rule_id: str
    category: str
    description: str
    weight: int
    matched_terms: List[str]

@dataclass
class ScamAnalysisResult:
    risk_score: int  # 0 to 100
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    scam_category: str
    ml_probability: float
    heuristic_score: int
    matched_indicators: List[Dict[str, Any]]
    highlighted_tokens: List[str]
    explanation: str
    recommendations: List[str]

# -------------------------------------------------------------------------
# Transparent Heuristic Rule Definitions
# -------------------------------------------------------------------------

HEURISTIC_RULES = [
    {
        "id": "BANK_KYC_SUSPENSION",
        "category": "BANK_KYC",
        "weight": 40,
        "description": "Threat of bank account, PAN card, or SIM deactivation paired with an update demand.",
        "patterns": [
            r"\b(account|ac|a/c)\s+(will\s+be\s+)?(blocked|suspended|deactivated|closed|frozen)\b",
            r"\b(update|link|complete)\s+(your\s+)?(kyc|pan|aadhaar|aadhar)\b",
            r"\b(sbi|hdfc|icici|pnb|axis|bob|canara|kotak)\s+(account|alert|netbanking)\b",
            r"\b(debit\s+card|sim\s+card)\s+(blocked|expired|update)\b"
        ]
    },
    {
        "id": "ELECTRICITY_POWER_CUT",
        "category": "ELECTRICITY_BILL",
        "weight": 45,
        "description": "Urgent threat of electricity disconnection tonight due to unpaid bill.",
        "patterns": [
            r"\b(electricity|power|light)\b.*?\b(disconnected|cut|suspended)\b",
            r"\b(disconnected|cut)\b.*?\b(electricity|power)\b",
            r"\b(electricity\s+officer|power\s+office|electricity\s+bill)\b",
            r"\bprevious\s+month\s+bill\s+not\s+updated\b"
        ]
    },
    {
        "id": "UPI_RECEIVE_FRAUD",
        "category": "UPI_FRAUD",
        "weight": 50,
        "description": "Demanding a UPI PIN or QR code scan to 'receive' money or cashback (UPI PIN is ONLY for paying).",
        "patterns": [
            r"\b(enter|send|provide)\s+(your\s+)?(upi\s+)?pin\b.*?\b(receive|credit|claim|get)\b",
            r"\b(receive|credit|claim|cashback)\b.*?\b(enter|send|provide)\b.*?\b(upi\s+)?pin\b",
            r"\b(scan\s+qr\s+code\s+to\s+receive|scan\s+to\s+credit|scan\s+qr\b.*?\breceive)\b",
            r"\bcashback\s+of\s+rs\.?\s*\d+\b"
        ]
    },
    {
        "id": "OTP_CREDENTIAL_DEMAND",
        "category": "OTP_THEFT",
        "weight": 45,
        "description": "Unsolicited request to share an OTP, password, or verification code.",
        "patterns": [
            r"\b(share|send|tell|provide|forward)\s+(the\s+)?(otp|one\s+time\s+password|code|verification\s+code)\b",
            r"\botp\s+is\s+required\s+to\s+(unblock|verify|cancel)\b",
            r"\bdo\s+not\s+share\s+this\s+otp\s+with\s+anyone\b"  # Often quoted legitimately, weighted lower if standalone
        ]
    },
    {
        "id": "PART_TIME_JOB_SCAM",
        "category": "JOB_SCAM",
        "weight": 35,
        "description": "Unrealistic high-pay part-time job offers like liking YouTube videos or Telegram tasks.",
        "patterns": [
            r"\b(part\s+time\s+job|work\s+from\s+home)\s+(daily\s+income|earn\s+rs|earn\s+\d+)\b",
            r"\b(like|subscribe)\s+(youtube\s+videos|reviews)\s+earn\b",
            r"\bearn\s+\d{3,5}\s*(rs|inr|-)?\s*(per\s+day|daily)\b",
            r"\btelegram\s+task|contact\s+on\s+telegram\b"
        ]
    },
    {
        "id": "LOTTERY_PRIZE_FRAUD",
        "category": "LOTTERY",
        "weight": 40,
        "description": "Fake lottery, lucky draw, or KBC prize notification requiring a processing fee or contact.",
        "patterns": [
            r"\b(congratulations|lucky\s+winner)\s+you\s+(have\s+)?won\b",
            r"\b(won|claim)\s+(rs\.?\s*)?(\d+\s*lakh|\d+\s*crore|25\s*lakh)\b",
            r"\b(kbc|kaun\s+banega\s+crorepati|whatsapp)\s+lottery\b"
        ]
    },
    {
        "id": "DIGITAL_ARREST_POLICE_IMPERSONATION",
        "category": "DIGITAL_ARREST",
        "weight": 50,
        "description": "Impersonation of police, CBI, TRAI, or FedEx claiming illegal parcels or money laundering.",
        "patterns": [
            r"\b(cbi|customs|crime\s+branch|mumbai\s+police|delhi\s+police|trai)\s+(department|investigation|notice)\b",
            r"\b(illegal\s+parcel|narcotics|drugs|money\s+laundering)\s+(found|linked\s+to\s+your\s+aadhaar)\b",
            r"\bdigital\s+arrest|stay\s+on\s+skype|video\s+call\s+verification\b"
        ]
    },
    {
        "id": "URGENCY_PRESSURE",
        "category": "URGENCY",
        "weight": 25,
        "description": "High artificial urgency forcing victim to act immediately without verifying.",
        "patterns": [
            r"\b(tonight|within\s+\d+\s*(hours?|mins?|days?)|immediately|today\s+itself|within\s+24\s*hrs?)\b",
            r"\burgent\s+(action\s+required|notice|alert)\b",
            r"\bavoid\s+(permanent\s+blocking|legal\s+action|disconnection)\b"
        ]
    },
    {
        "id": "UNOFFICIAL_LINK_OR_HANDLE",
        "category": "SUSPICIOUS_LINK",
        "weight": 30,
        "description": "Suspicious URL shorteners, direct APK download links, or personal messaging redirection.",
        "patterns": [
            r"https?://(bit\.ly|tinyurl\.com|cutt\.ly|is\.gd|t\.me|wa\.me)/[a-zA-Z0-9_-]+",
            r"https?://[^\s]+\.(apk|xyz|top|live|online|cam|work|rest)\b",
            r"\bdownload\s+(and\s+install\s+)?(the\s+)?apk\b",
            r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        ]
    },
    {
        "id": "INVESTMENT_PROFIT_SCHEME",
        "category": "INVESTMENT",
        "weight": 35,
        "description": "Unrealistic guaranteed return investment schemes or crypto doubling promises.",
        "patterns": [
            r"\b(guaranteed\s+profit|guaranteed\s+return|risk\s+free\s+return)\b",
            r"\b(double\s+your\s+money|100%\s+profit|300%\s+return)\b",
            r"\binvest\s+(rs\.?\s*)?\d+\s+and\s+get\s+\d+\b"
        ]
    }
]

# -------------------------------------------------------------------------
# Transparent TF-IDF + Multinomial Naive Bayes Model
# -------------------------------------------------------------------------

class ExplainableScamClassifier:
    """
    Zero-cost, explainable TF-IDF + Naive Bayes scam message classifier.
    Designed for 100% local, student-friendly deployment with zero API costs.
    """
    def __init__(self):
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.scam_word_log_probs: Dict[str, float] = {}
        self.ham_word_log_probs: Dict[str, float] = {}
        self.log_prior_scam: float = -0.693
        self.log_prior_ham: float = -0.693
        self.is_trained: bool = False
        self._train_foundation_model()

    def _tokenize(self, text: str) -> List[str]:
        """Normalize text and extract unigram and bigram tokens."""
        text = text.lower()
        # Replace URLs and numbers with normalized placeholders for general patterns
        tokens = re.findall(r"\b[a-z0-9/_-]{2,}\b", text)
        
        # Add bigrams for contextual phrases
        bigrams = []
        for i in range(len(tokens) - 1):
            bigrams.append(f"{tokens[i]}_{tokens[i+1]}")
            
        return tokens + bigrams

    def _train_foundation_model(self):
        """Train the explainable classifier on representative Indian cyber fraud and legitimate datasets."""
        training_corpus: List[Tuple[str, int]] = [
            # SCAM SAMPLES (Class 1)
            ("dear customer your sbi bank account will be blocked today update your pan card immediately click link http://bit.ly/sbi-pan", 1),
            ("your hdfc netbanking access suspended due to incomplete kyc update kyc now to avoid permanent block", 1),
            ("dear consumer tonight 9:30 pm electricity power will be disconnected from power office contact officer at 9876543210", 1),
            ("congratulations you have won 25 lakh lottery in kaun banega crorepati whatsapp lucky draw call rana pratap singh", 1),
            ("part time work from home like youtube videos earn rs 3000 to 5000 daily no experience contact on telegram @taskagent", 1),
            ("to receive cashback of rs 2500 enter your upi pin on phonpe app now", 1),
            ("scan qr code to credit money of rs 12000 into your account immediately", 1),
            ("your jio sim card verification pending sim will be deactivated within 24 hours call 9811223344", 1),
            ("trai notice your phone number involved in criminal activity arrest warrant issued connect on skype", 1),
            ("invest rs 5000 and get rs 20000 within 48 hours 100% guaranteed profit cryptocurrency scheme", 1),
            ("share your 6 digit otp to unblock debit card transfer now", 1),
            ("income tax refund of rs 15400 approved click here to verify bank account details http://tinyurl.com/incometax-ref", 1),
            ("dear customer axis bank debit card reward points worth rs 8900 expiring today redeem now http://axis-points.xyz", 1),
            ("urgent electricity bill unpaid connection will be cut at 10 pm contact electricity board officer", 1),
            ("exclusive amazon gift card won in lucky draw claim 50000 rupees voucher submit registration fee", 1),
            ("cbi crime branch notice aadhaar card used in money laundering case immediate video verification required", 1),
            ("work 1 hour daily earn 2000 inr subscribe telegram channel deposit 500 security deposit", 1),
            ("dear pnb user your account has been disabled visit http://192.168.1.1/pnb-auth to submit kyc", 1),
            ("send otp sent to your mobile number to verify upi refund payment", 1),
            ("double your money guaranteed risk free stock tips join vip telegram group", 1),

            # LEGITIMATE / HAM SAMPLES (Class 0)
            ("dear customer your sbi debit card ending with 4321 used for inr 500 at supermarket on 01-nov-2026. avl bal inr 12000.", 0),
            ("your swiggy order #49281 has been picked up by delivery partner and will arrive in 20 minutes.", 0),
            ("your one time password otp for login to irctc is 849201. do not share this otp with anyone.", 0),
            ("team meeting rescheduled to tomorrow 3:30 pm in conference room b. please update your calendar.", 0),
            ("thank you for paying your bescom electricity bill of rs 1420 via upi. transaction id 294819204.", 0),
            ("dear parent school annual sports day will be held this saturday from 8 am onwards. attendance is compulsory.", 0),
            ("your monthly salary of inr 65000 credited to your hdfc bank account. balance inr 145000.", 0),
            ("your amazon delivery package will be delivered today by courier partner. track at amazon app.", 0),
            ("dear customer your monthly e-statement for axis bank savings account for october is ready to view.", 0),
            ("hi ramesh, please review the attached engineering design document when you get a chance.", 0),
            ("otp for authenticating aadhaar authentication on digilocker is 394012 valid for 10 minutes.", 0),
            ("your gas cylinder booking confirmed. delivery scheduled within 2 working days. indane gas.", 0),
            ("reminder your dentist appointment is scheduled for tuesday at 5 pm with dr sharma.", 0),
            ("payment of rs 250 to grocery store successful through google pay. upi ref 40928190.", 0),
            ("hello, are you available for a quick phone call regarding the college project submission?", 0)
        ]

        total_docs = len(training_corpus)
        scam_docs = [text for text, label in training_corpus if label == 1]
        ham_docs = [text for text, label in training_corpus if label == 0]

        self.log_prior_scam = math.log(len(scam_docs) / total_docs)
        self.log_prior_ham = math.log(len(ham_docs) / total_docs)

        # Build vocabulary & document frequency
        doc_freq: Dict[str, int] = {}
        scam_word_counts: Dict[str, int] = {}
        ham_word_counts: Dict[str, int] = {}

        for text, label in training_corpus:
            tokens = set(self._tokenize(text))
            for token in tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1
                if label == 1:
                    scam_word_counts[token] = scam_word_counts.get(token, 0) + 1
                else:
                    ham_word_counts[token] = ham_word_counts.get(token, 0) + 1

        # Calculate IDF with Laplace smoothing
        for token, df in doc_freq.items():
            self.idf[token] = math.log((total_docs + 1) / (df + 1)) + 1.0

        # Calculate word likelihoods with additive smoothing
        vocab_size = len(doc_freq)
        total_scam_words = sum(scam_word_counts.values()) + vocab_size
        total_ham_words = sum(ham_word_counts.values()) + vocab_size

        for token in doc_freq:
            self.scam_word_log_probs[token] = math.log((scam_word_counts.get(token, 0) + 1.0) / total_scam_words)
            self.ham_word_log_probs[token] = math.log((ham_word_counts.get(token, 0) + 1.0) / total_ham_words)

        self.is_trained = True

    def predict_ml_probability(self, text: str) -> Tuple[float, List[str]]:
        """Predict probability of message being a scam and extract highest contributing tokens."""
        tokens = self._tokenize(text)
        log_prob_scam = self.log_prior_scam
        log_prob_ham = self.log_prior_ham

        contributing_tokens: List[Tuple[str, float]] = []

        default_log_scam = math.log(1.0 / (len(self.scam_word_log_probs) + 100))
        default_log_ham = math.log(1.0 / (len(self.ham_word_log_probs) + 100))

        for token in tokens:
            p_scam = self.scam_word_log_probs.get(token, default_log_scam)
            p_ham = self.ham_word_log_probs.get(token, default_log_ham)
            log_prob_scam += p_scam
            log_prob_ham += p_ham

            diff = p_scam - p_ham
            if diff > 0.5:
                contributing_tokens.append((token, diff))

        # Softmax / log-odds to probability
        max_log = max(log_prob_scam, log_prob_ham)
        exp_scam = math.exp(log_prob_scam - max_log)
        exp_ham = math.exp(log_prob_ham - max_log)
        prob_scam = exp_scam / (exp_scam + exp_ham)

        # Sort top contributing scam tokens
        contributing_tokens.sort(key=lambda x: x[1], reverse=True)
        top_tokens = [t[0].replace("_", " ") for t in contributing_tokens[:8]]

        return prob_scam, top_tokens

    def evaluate_test_dataset(self) -> Dict[str, float]:
        """
        Evaluate the classifier against a test dataset and return
        precision, recall, f1-score, and accuracy.
        """
        test_samples = [
            ("Dear HDFC user account blocked today click link http://bit.ly/hdfc-pan", 1),
            ("Electricity cut tonight 9 pm call officer 9845012345", 1),
            ("Earn 5000 daily part time work like youtube videos telegram", 1),
            ("Share 6 digit otp to unblock debit card", 1),
            ("You have won 25 lakh lottery in KBC lucky draw", 1),
            ("Your Zomato order has been delivered enjoy your meal", 0),
            ("Dear customer OTP for login is 392019 valid for 5 mins", 0),
            ("Monthly statement for SBI account ending 9102 generated", 0),
            ("Class lecture tomorrow morning at 10 am in room 302", 0),
            ("Payment of Rs 150 to metro card recharge successful", 0)
        ]

        tp = fp = tn = fn = 0
        for text, actual_label in test_samples:
            prob, _ = self.predict_ml_probability(text)
            pred_label = 1 if prob >= 0.5 else 0

            if pred_label == 1 and actual_label == 1:
                tp += 1
            elif pred_label == 1 and actual_label == 0:
                fp += 1
            elif pred_label == 0 and actual_label == 0:
                tn += 1
            elif pred_label == 0 and actual_label == 1:
                fn += 1

        accuracy = (tp + tn) / len(test_samples) if test_samples else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "test_sample_count": len(test_samples)
        }

    def analyze_message(self, text: str) -> ScamAnalysisResult:
        """
        Execute full hybrid analysis combining transparent heuristic rules
        and explainable TF-IDF Naive Bayes classification.
        """
        clean_text = text.strip()
        matched_indicators: List[IndicatorMatch] = []
        highlighted_terms: set = set()
        heuristic_score = 0
        detected_categories = []

        # 1. Match Heuristic Rules
        for rule in HEURISTIC_RULES:
            matched_in_rule = []
            for pattern in rule["patterns"]:
                found = re.findall(pattern, clean_text, re.IGNORECASE)
                if found:
                    for f in found:
                        if isinstance(f, tuple):
                            term = " ".join([x for x in f if x])
                        else:
                            term = str(f)
                        matched_in_rule.append(term)
                        highlighted_terms.add(term)

            if matched_in_rule:
                heuristic_score += rule["weight"]
                detected_categories.append(rule["category"])
                matched_indicators.append(IndicatorMatch(
                    rule_id=rule["id"],
                    category=rule["category"],
                    description=rule["description"],
                    weight=rule["weight"],
                    matched_terms=list(set(matched_in_rule))
                ))

        # 2. Run ML Naive Bayes Classifier
        ml_prob, ml_top_tokens = self.predict_ml_probability(clean_text)
        for t in ml_top_tokens:
            highlighted_terms.add(t)

        # 3. Hybrid Scoring Computation (0 to 100)
        # 60% Weight to Heuristic Rules, 40% to ML Probability
        raw_score = (min(heuristic_score, 100) * 0.6) + ((ml_prob * 100) * 0.4)
        risk_score = int(min(max(raw_score, 0), 100))

        # 4. Determine Severity Classification
        if risk_score >= 75:
            risk_level = "CRITICAL"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # 5. Determine Primary Scam Category
        if detected_categories:
            primary_category = detected_categories[0]
        elif ml_prob > 0.6:
            primary_category = "GENERAL_SUSPICIOUS"
        else:
            primary_category = "LEGITIMATE"

        # 6. Formulate Clear Explanation
        explanation = self._build_explanation(risk_level, primary_category, matched_indicators, ml_prob)

        # 7. Provide Practical Safety Recommendations
        recommendations = self._build_recommendations(primary_category, matched_indicators)

        return ScamAnalysisResult(
            risk_score=risk_score,
            risk_level=risk_level,
            scam_category=primary_category,
            ml_probability=round(ml_prob, 4),
            heuristic_score=heuristic_score,
            matched_indicators=[
                {
                    "rule_id": m.rule_id,
                    "category": m.category,
                    "description": m.description,
                    "weight": m.weight,
                    "matched_terms": m.matched_terms
                }
                for m in matched_indicators
            ],
            highlighted_tokens=list(highlighted_terms),
            explanation=explanation,
            recommendations=recommendations
        )

    def _build_explanation(
        self,
        risk_level: str,
        category: str,
        indicators: List[IndicatorMatch],
        ml_prob: float
    ) -> str:
        if risk_level == "CRITICAL":
            details = "; ".join([ind.description for ind in indicators])
            return (
                f"CRITICAL FRAUD ALERT ({round(ml_prob * 100)}% scam language confidence). "
                f"This message exhibits known cybercrime patterns: {details}. "
                "Legitimate banks, government departments, and utility providers never send urgent threats with unofficial contact numbers."
            )
        elif risk_level == "HIGH":
            return (
                f"HIGH RISK DETECTED: This message contains strong phishing and urgency markers ({category}). "
                "It attempts to pressure you into immediate action. Do not click links, call the phone numbers provided, or share credentials."
            )
        elif risk_level == "MEDIUM":
            return (
                "MODERATE CAUTION: The message contains promotional or ambiguous wording. "
                "While not definitively confirmed as fraud, it shares patterns with mass-marketing or emerging unsolicited spam."
            )
        else:
            return (
                "LOW RISK: The message language appears normal and does not exhibit known financial coercion, "
                "credential theft, or phishing indicators. Note: Always verify the sender independently before clicking any link."
            )

    def _build_recommendations(self, category: str, indicators: List[IndicatorMatch]) -> List[str]:
        recommendations = [
            "Never share OTPs, UPI PINs, or banking passwords with anyone under any circumstances."
        ]

        if category == "BANK_KYC":
            recommendations.append("Never update KYC through SMS links. Only visit your bank branch or use the official mobile banking app.")
            recommendations.append("Call your bank's customer care using the verified phone number printed on the back of your debit card.")
        elif category == "ELECTRICITY_BILL":
            recommendations.append("Electricity boards never disconnect power overnight through random WhatsApp or SMS alerts.")
            recommendations.append("Pay and verify power bills only on the official state electricity portal (e.g. BESCOM, Mahavitaran, UPPCL).")
        elif category == "UPI_FRAUD":
            recommendations.append("IMPORTANT: You NEVER enter a UPI PIN or scan a QR code to receive money. A PIN is strictly for paying.")
        elif category == "JOB_SCAM":
            recommendations.append("Legitimate companies never hire via random WhatsApp/Telegram tasks or ask you to pay a security deposit.")
        elif category == "LOTTERY":
            recommendations.append("You cannot win a lottery you never entered. Genuine lotteries do not ask for processing fees upfront.")
        elif category == "DIGITAL_ARREST":
            recommendations.append("There is NO legal concept of 'Digital Arrest' in Indian law. Police or CBI never conduct trials over Skype or WhatsApp video.")
            recommendations.append("If intimidated, disconnect immediately and dial 1930 or 112.")

        recommendations.append("If money has been stolen, report within the golden hour to helpline 1930 or cybercrime.gov.in.")
        return recommendations

# Global singleton instance
scam_classifier = ExplainableScamClassifier()
