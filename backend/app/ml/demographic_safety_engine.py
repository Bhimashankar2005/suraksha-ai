import re
from typing import Dict, Any, List, Tuple
from urllib.parse import quote

class DemographicSafetyEngine:
    """
    Specialized Safety Engine for Women Cyber Protection & Senior Citizen Digital Safety.
    Combines rule-based forensic heuristics, threat severity classification,
    and localized plain-language / voice explanations in English, Kannada, and Hindi.
    """

    WOMEN_HELPLINES = [
        {
            "name": "Women Police Helpline",
            "number": "1091",
            "portal": "https://cybercrime.gov.in",
            "description": "Toll-free 24/7 dedicated distress line for women facing harassment or threats."
        },
        {
            "name": "National Commission for Women (NCW) Cyber Cell",
            "number": "7827170170",
            "portal": "https://ncw.nic.in",
            "description": "NCW 24/7 national cyber cell for blackmail, non-consensual images & online stalking."
        },
        {
            "name": "All-India Emergency Helpline",
            "number": "112",
            "portal": "https://112.gov.in",
            "description": "Immediate police emergency response across all Indian States and Union Territories."
        },
        {
            "name": "National Cyber Crime Helpline",
            "number": "1930",
            "portal": "https://cybercrime.gov.in",
            "description": "Official portal for filing anonymous women/child cyber crime complaints."
        }
    ]

    # Women Harassment & Blackmail Threat Indicators
    EXTORTION_IMAGE_PATTERNS = [
        r"\b(leak|viral|expose|post|upload|share|send)\b.*\b(photo|photos|picture|pictures|video|videos|pic|pics|nude|nudes|private|clip|morphed)\b",
        r"\b(morphed|private|nude|secret)\b.*\b(photo|photos|picture|pictures|video|videos|clip|image|images)\b",
        r"\b(pay|transfer|send\s*money|crypto|bitcoin|upi)\b.*\b(or\s*else|or\s*i\s*will|to\s*your\s*family|to\s*your\s*friends|to\s*your\s*college)\b",
        r"\b(webcam|recorded\s*you|camera\s*hacked|recorded\s*video|screen\s*recorded)\b",
        r"(ವೈರಲ್|ಫೋಟೋ\s*ಲೀಕ್|ವೀಡಿಯೋ\s*ಹಂಚಿಕೆ|ಹಣ\s*ನೀಡದಿದ್ದರೆ|ಬ್ಲಾಕ್‌ಮೇಲ್)",
        r"(वायरल|फोटो\s*लीक|वीडियो\s*पोस्ट|ब्लैकमेल|पैसे\s*दो\s*वरना)"
    ]

    STALKING_VIOLENCE_PATTERNS = [
        r"\b(know\s*where\s*you\s*live|following\s*you|watching\s*you|at\s*your\s*college|outside\s*your\s*house|gps)\b",
        r"\b(kill\s*you|hurt\s*you|destroy\s*you|ruin\s*your\s*life|die|acid)\b",
        r"\b(answer\s*my\s*call|pick\s*up|talk\s*to\s*me\s*or\s*else)\b",
        r"(ಹಿಂಬಾಲಿಸುತ್ತಿದ್ದೇನೆ|ಕೊಲ್ಲುತ್ತೇನೆ|ನಿನ್ನ\s*ಮನೆ\s*ಗೊತ್ತು|ಜೀವನ\s*ಹಾಳು)",
        r"(पीछा\s*कर\s*रहा|घर\s*का\s*पता|जान\s*से\s*मार|बर्बाद\s*कर\s*दूंगा)"
    ]

    IMPERSONATION_DEFAMATION_PATTERNS = [
        r"\b(fake\s*account|fake\s*profile|posing\s*as\s*you|created\s*profile|using\s*your\s*pictures)\b",
        r"\b(defame|slut|character|prostitute|reputation|rumors)\b",
        r"(ನಕಲಿ\s*ಖಾತೆ|ನಿನ್ನ\s*ಹೆಸರಲ್ಲಿ\s*ಪ್ರೊಫೈಲ್|ಮಾನಹಾನಿ)",
        r"(फेक\s*अकाउंट|फर्जी\s*प्रोफाइल|बदनाम|चरित्र)"
    ]

    def analyze_harassment(self, content: str, context: str = None) -> Dict[str, Any]:
        """
        Analyzes messages for cyber harassment, stalking, image extortion, and defamation.
        Returns severity, detected categories, safety steps, and official reporting hotlines.
        """
        text = content.lower()
        detected_patterns = []
        score = 0

        # 1. Extortion / Image Leak Threat Check
        is_extortion = any(re.search(p, text, re.IGNORECASE) for p in self.EXTORTION_IMAGE_PATTERNS)
        if is_extortion:
            detected_patterns.append("Blackmail & Non-Consensual Media Distribution Threat")
            score += 55

        # 2. Stalking & Violence Threat Check
        is_violence = any(re.search(p, text, re.IGNORECASE) for p in self.STALKING_VIOLENCE_PATTERNS)
        if is_violence:
            detected_patterns.append("Cyberstalking & Physical Threat / Intimidation")
            score += 50

        # 3. Impersonation & Defamation Check
        is_impersonation = any(re.search(p, text, re.IGNORECASE) for p in self.IMPERSONATION_DEFAMATION_PATTERNS)
        if is_impersonation:
            detected_patterns.append("Impersonation, Fake Profile or Online Defamation")
            score += 35

        # General abusive keywords
        if re.search(r"\b(bitch|whore|slut|rape|harass|abuse)\b", text, re.IGNORECASE):
            detected_patterns.append("Sexually Abusive & Vulgar Language")
            score += 25

        score = min(score, 100)

        if is_extortion or (is_violence and score >= 70):
            severity = "CRITICAL_EMERGENCY"
        elif is_violence or score >= 50:
            severity = "HIGH"
        elif score >= 25:
            severity = "MEDIUM"
        else:
            severity = "LOW"
            if not detected_patterns:
                detected_patterns.append("No explicit blackmail or violent threat keywords detected")

        # Concrete safety protocol
        immediate_actions = [
            "DO NOT PAY EXTORTION MONEY: Paying never stops the blackmailer and results in higher financial demands.",
            "DO NOT DELETE CHAT MESSAGES: Keep full unedited screenshots showing timestamps, usernames, phone numbers, and profile URLs. They are vital legal proof.",
            "FILE AN ANONYMOUS COMPLAINT: Indian law permits women to report cyber harassment without making their name public at cybercrime.gov.in.",
            "BLOCK THE PERPETRATOR: Once screenshots and URLs are captured, report the account inside the app and block them."
        ]

        evidence_checklist = [
            "Clear screenshots of chat messages showing phone number or handle",
            "Profile URL / link of the perpetrator's account",
            "Exact dates and timestamps of received messages",
            "Call logs showing repeated unprompted calls",
            "Bank transaction details or UPI handles if money was demanded"
        ]

        return {
            "threat_severity": severity,
            "detected_patterns": detected_patterns,
            "risk_score": score,
            "immediate_actions": immediate_actions,
            "emergency_helplines": self.WOMEN_HELPLINES,
            "evidence_checklist": evidence_checklist,
            "official_filing_link": "https://cybercrime.gov.in"
        }

    def explain_senior_scam(self, message: str, language: str = "en") -> Dict[str, Any]:
        """
        Plain-Language, High-Accessibility Scam Explainer for Senior Citizens.
        Provides zero-jargon explanation and TTS voice script in English, Kannada, or Hindi.
        """
        text = message.lower()
        lang = language if language in ["en", "kn", "hi"] else "en"

        # Topic detection for common senior scams
        if re.search(r"\b(pension|jeevan\s*pramaan|epfo|life\s*certificate|treasury)\b", text) or \
           re.search(r"(ಪಿಂಚಣಿ|ಜೀವನ್\s*ಪ್ರಮಾಣ|ಪಿಎಫ್|ಪೆನ್ಷನ್)", text) or \
           re.search(r"(पेंशन|जीवन\s*प्रमाण|ईपीएफओ)", text):
            category = "PENSION_KYC_SCAM"
            verdict = "DANGEROUS SCAM"
            
            explanations = {
                "en": (
                    "This is a FAKE PENSION SCAM. Real government pension offices and banks will NEVER call you "
                    "or send SMS asking you to click a link or download an app to update your Jeevan Pramaan certificate. "
                    "Fraudsters want you to install a screen-sharing app like AnyDesk to steal your pension savings."
                ),
                "kn": (
                    "ಇದು ನಕಲಿ ಪಿಂಚಣಿ (ಪೆನ್ಷನ್) ವಂಚನೆ. ಯಾವುದೇ ಸರ್ಕಾರಿ ಕಚೇರಿ ಅಥವಾ ಬ್ಯಾಂಕ್ ನಿಮ್ಮ ಜೀವನ ಪ್ರಮಾಣ ಪತ್ರ ನವೀಕರಿಸಲು "
                    "ಲಿಂಕ್ ಕ್ಲಿಕ್ ಮಾಡಲು ಅಥವಾ ಆ್ಯಪ್ ಡೌನ್‌ಲೋಡ್ ಮಾಡಲು ಹೇಳುವುದಿಲ್ಲ. ವಂಚಕರು ನಿಮ್ಮ ಖಾತೆಯಿಂದ ಹಣ ದೋಚಲು ಪ್ರಯತ್ನಿಸುತ್ತಿದ್ದಾರೆ."
                ),
                "hi": (
                    "यह एक फर्जी पेंशन घोटाला है। सरकार या बैंक कभी भी जीवन प्रमाण पत्र अपडेट करने के लिए फोन पर लिंक या ऐप डाउनलोड "
                    "करने को नहीं कहते। ठग आपका पेंशन का पैसा चुराने की कोशिश कर रहे हैं।"
                )
            }
            voice_scripts = {
                "en": "Warning! This is a fake pension message. Do not click any link. Do not download any app. Your pension is safe.",
                "kn": "ಎಚ್ಚರಿಕೆ! ಇದು ನಕಲಿ ಪಿಂಚಣಿ ಸಂದೇಶ. ಯಾವುದೇ ಲಿಂಕ್ ಮುಟ್ಟಬೇಡಿ. ನಿಮ್ಮ ಪಿಂಚಣಿ ಹಣ ಸುರಕ್ಷಿತವಾಗಿದೆ.",
                "hi": "सावधान! यह फर्जी पेंशन संदेश है। किसी भी लिंक पर क्लिक न करें। आपकी पेंशन सुरक्षित है।"
            }
            actions = [
                "Do NOT click any link in the message.",
                "Never install apps like AnyDesk, TeamViewer, or QuickSupport.",
                "For Life Certificate (Jeevan Pramaan), visit your nearest Bank Branch or Post Office in person."
            ]

        elif re.search(r"\b(electricity|power\s*cut|bill\s*unpaid|disconnected\s*tonight|bescom|mseb|bses)\b", text) or \
             re.search(r"(ವಿದ್ಯುತ್|ಕರೆಂಟ್\s*ಕಟ್|ಲೈಟ್\s*ಬಿಲ್|ಬೆಸ್ಕಾಂ)", text) or \
             re.search(r"(बिजली\s*बिल|बिजली\s*कट|पावर\s*कट)", text):
            category = "ELECTRICITY_BILL_SCAM"
            verdict = "DANGEROUS SCAM"
            
            explanations = {
                "en": (
                    "This is the common ELECTRICITY DISCONNECTION SCAM. Power boards never send personal 10-digit mobile "
                    "numbers threatening to cut off power tonight at 9:30 PM. They want you to make a small payment on a fake website to steal your bank details."
                ),
                "kn": (
                    "ಇದು ನಕಲಿ ವಿದ್ಯುತ್ ಬಿಲ್ ವಂಚನೆ. ಬೆಸ್ಕಾಂ ಅಥವಾ ವಿದ್ಯುತ್ ಇಲಾಖೆಯು ಇಂತಹ ಎಸ್‌ಎಂಎಸ್ ಕಳುಹಿಸಿ ವೈಯಕ್ತಿಕ ನಂಬರ್‌ಗೆ ಕರೆ ಮಾಡಲು ಹೇಳುವುದಿಲ್ಲ. "
                    "ಯಾವುದೇ ಕಾರಣಕ್ಕೂ ಕರೆ ಮಾಡಬೇಡಿ."
                ),
                "hi": (
                    "यह बिजली बिल का फर्जी मैसेज है। बिजली विभाग कभी भी किसी व्यक्तिगत मोबाइल नंबर पर फोन करने या आज रात बिजली काटने की धमकी नहीं देता।"
                )
            }
            voice_scripts = {
                "en": "Do not panic. Your electricity will not be disconnected. The number in the message belongs to a scammer.",
                "kn": "ಹೆದರಬೇಡಿ. ನಿಮ್ಮ ವಿದ್ಯುತ್ ಕಡಿತಗೊಳ್ಳುವುದಿಲ್ಲ. ಆ ಸಂದೇಶದಲ್ಲಿರುವ ಸಂಖ್ಯೆ ವಂಚಕನದ್ದು.",
                "hi": "घबराएं नहीं। आपकी बिजली नहीं कटेगी। मैसेज में दिया गया नंबर धोखेबाज का है।"
            }
            actions = [
                "Do NOT call the phone number given in the SMS.",
                "Verify your bill status directly inside the official electricity board app or at the local office.",
                "Do NOT share OTP or banking passwords with anyone."
            ]

        elif re.search(r"\b(lottery|won\s*lakhs|kbc|lucky\s*draw|winner|prize)\b", text) or \
             re.search(r"(ಲಾಟರಿ|ಬಹುಮಾನ|ಕೆಬಿಸಿ|ಗೆದ್ದಿದ್ದೀರಿ)", text) or \
             re.search(r"(लॉटरी|इनाम|केबीसी|जीते\s*हैं)", text):
            category = "LOTTERY_PRIZE_SCAM"
            verdict = "DANGEROUS SCAM"
            
            explanations = {
                "en": (
                    "This is a 100% FAKE LOTTERY SCAM. You cannot win a lottery or prize you never bought a ticket for. "
                    "They will ask you to pay 'GST', 'tax', or 'registration fees' upfront, and then disappear with your money."
                ),
                "kn": (
                    "ಇದು ಸಂಪೂರ್ಣ ನಕಲಿ ಲಾಟರಿ ವಂಚನೆ. ನೀವು ಟಿಕೆಟ್ ಖರೀದಿಸದೆ ಲಾಟರಿ ಗೆಲ್ಲಲು ಸಾಧ್ಯವಿಲ್ಲ. "
                    "ಬಹುಮಾನದ ಆಮಿಷವೊಡ್ಡಿ ಪ್ರೊಸೆಸಿಂಗ್ ಶುಲ್ಕದ ಹೆಸರಿನಲ್ಲಿ ನಿಮ್ಮಿಂದ ಹಣ ದೋಚುತ್ತಾರೆ."
                ),
                "hi": (
                    "यह पूरी तरह से फर्जी लॉटरी है। जिस लॉटरी का आपने टिकट ही नहीं खरीदा, उसमें आप कभी नहीं जीत सकते। टैक्स के नाम पर पैसे न दें।"
                )
            }
            voice_scripts = {
                "en": "This is a lottery fraud. Do not pay any processing fee. Delete this message immediately.",
                "kn": "ಇದು ನಕಲಿ ಲಾಟರಿ. ಯಾವುದೇ ಹಣ ಪಾವತಿಸಬೇಡಿ. ಈ ಸಂದೇಶವನ್ನು ಅಳಿಸಿಹಾಕಿ.",
                "hi": "यह लॉटरी फ्रॉड है। कोई टैक्स या फीस न दें। इस मैसेज को डिलीट कर दें।"
            }
            actions = [
                "Never send money to claim any prize or lottery.",
                "Block and report the sender number.",
                "Delete the message."
            ]

        elif re.search(r"\b(otp|enter\s*pin|upi\s*pin|share\s*code|bank\s*officer)\b", text) or \
             re.search(r"(ಓಟಿಪಿ|ಪಿನ್|ಕೋಡ್|ಬ್ಯಾಂಕ್\s*ಅಧಿಕಾರಿ)", text) or \
             re.search(r"(ओटीपी|पिन|कोड|बैंक\s*अधिकारी)", text):
            category = "CREDENTIAL_THEFT"
            verdict = "DANGEROUS SCAM"
            
            explanations = {
                "en": (
                    "CRITICAL WARNING: Someone is trying to steal your OTP or UPI PIN! "
                    "Remember the golden rule: You NEVER need to enter a PIN to receive money. PIN is strictly for paying out. "
                    "No real bank employee will ever ask for your OTP."
                ),
                "kn": (
                    "ಅಪಾಯಕಾರಿ ಎಚ್ಚರಿಕೆ: ಯಾರೋ ನಿಮ್ಮ ಓಟಿಪಿ ಅಥವಾ ಯುಪಿಐ ಪಿನ್ ಕದಿಯಲು ಯತ್ನಿಸುತ್ತಿದ್ದಾರೆ! "
                    "ನೆನಪಿಡಿ: ಹಣ ಸ್ವೀಕರಿಸಲು ಎಂದಿಗೂ ಪಿನ್ ಹಾಕಬಾರದು. ಬ್ಯಾಂಕ್ ನೌಕರರು ಎಂದಿಗೂ ಓಟಿಪಿ ಕೇಳುವುದಿಲ್ಲ."
                ),
                "hi": (
                    "खतरनाक चेतावनी: कोई आपका ओटीपी या यूपीआई पिन चुराने की कोशिश कर रहा है! "
                    "पैसे प्राप्त करने के लिए कभी पिन नहीं डाला जाता। किसी को भी ओटीपी न बताएं।"
                )
            }
            voice_scripts = {
                "en": "Alert! Never share your OTP or enter your PIN. Real banks never ask for passwords.",
                "kn": "ಎಚ್ಚರ! ಯಾರೊಂದಿಗೂ ಓಟಿಪಿ ಹಂಚಿಕೊಳ್ಳಬೇಡಿ. ಪಿನ್ ನಮೂದಿಸಬೇಡಿ.",
                "hi": "सावधान! किसी को भी ओटीपी न दें और न ही पिन डालें।"
            }
            actions = [
                "Do NOT share any 4 or 6-digit number received on SMS.",
                "Do NOT enter your UPI PIN on your phone.",
                "If already shared, immediately call your bank to block your account."
            ]

        else:
            category = "GENERAL_SUSPICIOUS"
            verdict = "SUSPICIOUS"
            explanations = {
                "en": (
                    "This message appears suspicious or unsolicited. Do not click links or call numbers sent by unknown people. "
                    "When in doubt, ask a trusted family member or call the Cyber Helpline at 1930."
                ),
                "kn": (
                    "ಈ ಸಂದೇಶವು ಅನುಮಾನಾಸ್ಪದವಾಗಿದೆ. ಅಪರಿಚಿತ ಲಿಂಕ್ ಮುಟ್ಟಬೇಡಿ ಅಥವಾ ಕರೆ ಮಾಡಬೇಡಿ. ಸಂದೇಹವಿದ್ದರೆ ಕುಟುಂಬದವರನ್ನು ಕೇಳಿ ಅಥವಾ 1930 ಗೆ ಕರೆ ಮಾಡಿ."
                ),
                "hi": (
                    "यह संदेश संदिग्ध प्रतीत होता है। किसी अनजान लिंक पर क्लिक न करें। संदेह होने पर 1930 हेल्पलाइन पर संपर्क करें।"
                )
            }
            voice_scripts = {
                "en": "Be cautious. Do not click unknown links. Ask family or call 1930.",
                "kn": "ಎಚ್ಚರಿಕೆಯಿಂದಿರಿ. ಅಪರಿಚಿತ ಲಿಂಕ್ ಮುಟ್ಟಬೇಡಿ. 1930 ಗೆ ಕರೆ ಮಾಡಿ.",
                "hi": "सतर्क रहें। अनजान लिंक न खोलें। 1930 पर कॉल करें।"
            }
            actions = [
                "Verify with a family member before taking action.",
                "Do not click links or send money.",
                "Call 1930 if you suspect fraud."
            ]

        return {
            "verdict": verdict,
            "plain_explanation": explanations[lang],
            "voice_script": voice_scripts[lang],
            "scam_category": category,
            "what_to_do_now": actions,
            "emergency_helpline": "1930",
            "language": lang
        }

    def generate_trusted_contact_alert(
        self,
        contact_name: str,
        phone_number: str,
        user_name: str,
        incident_type: str,
        incident_details: str = None
    ) -> Dict[str, str]:
        """
        Drafts a pre-formatted safe emergency text message for the citizen's trusted contact.
        User reviews and clicks to send via WhatsApp or SMS.
        """
        details = f" Details: {incident_details}" if incident_details else ""
        draft_text = (
            f"SURAKSHA AI SECURITY ALERT: Dear {contact_name}, your family member {user_name} "
            f"has encountered a suspected {incident_type} cyber threat and has requested your assistance.{details} "
            f"Please check in with them immediately. Emergency helpline: 1930."
        )

        # Generate WhatsApp click-to-chat URL
        clean_phone = re.sub(r"\D", "", phone_number)
        if len(clean_phone) == 10:
            clean_phone = "91" + clean_phone
        encoded_text = quote(draft_text)
        whatsapp_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_text}"

        return {
            "contact_name": contact_name,
            "phone_number": phone_number,
            "draft_sms_text": draft_text,
            "whatsapp_share_url": whatsapp_url
        }

demographic_safety_engine = DemographicSafetyEngine()
