import re
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple
from backend.app.core.config import settings

class AssistantEngine:
    """
    Multilingual Cyber Defense Assistant Engine.
    Combines local Ollama LLM integration (llama3.2 / phi3) with a zero-cost,
    deterministic trilingual safety dialogue tree (English, Kannada, Hindi).
    
    Strict Guardrails:
    - Never asks for OTP, PIN, password, or financial credentials.
    - Warns immediately if user inadvertently provides sensitive tokens.
    - Official helplines (1930 / cybercrime.gov.in) always integrated.
    """

    OFFICIAL_HELPLINES = [
        {
            "name": "National Cyber Crime Helpline",
            "number": "1930",
            "portal": "https://cybercrime.gov.in",
            "description": "Toll-free immediate citizen assistance for online financial fraud & cyber crimes.",
            "operating_hours": "24x7 (Act within 2-3 Golden Hours for fund freeze)"
        },
        {
            "name": "National Emergency Helpline",
            "number": "112",
            "portal": "https://112.gov.in",
            "description": "All-in-one emergency response for police, fire, and health.",
            "operating_hours": "24x7"
        },
        {
            "name": "Women Helpline / NCW",
            "number": "1091 / 7827170170",
            "portal": "https://ncw.nic.in",
            "description": "Dedicated cyber safety, stalking, harassment & blackmail support for women.",
            "operating_hours": "24x7"
        },
        {
            "name": "RBI Financial Fraud Portal (Sachet)",
            "number": "14440",
            "portal": "https://sachet.rbi.org.in",
            "description": "Reserve Bank of India awareness on unauthorized digital lending apps & deposits.",
            "operating_hours": "Working Days 9:30 AM - 5:30 PM"
        },
        {
            "name": "DoT Sanchar Saathi (TAFCOP)",
            "number": "1947",
            "portal": "https://sancharsaathi.gov.in",
            "description": "Check and disconnect fraudulent SIM cards registered on your Aadhaar.",
            "operating_hours": "Online Portal 24x7"
        }
    ]

    # Sensitive Information Detection Patterns
    SENSITIVE_PATTERNS = [
        re.compile(r"\b(otp|pin|cvv|password|passcode)\s*(is|:|=|-)?\s*([0-9]{4,8}|[a-zA-Z0-9@#$%^&*]{6,20})\b", re.IGNORECASE),
        re.compile(r"\b(upi\s*pin|atm\s*pin)\s*(is|:|=|-)?\s*[0-9]{4,6}\b", re.IGNORECASE),
        re.compile(r"\b\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\b"),  # 16-digit card number
    ]

    # Topic Matching Patterns
    TOPIC_PATTERNS = {
        "upi_fraud": [
            r"\b(upi|gpay|phonepe|paytm|bhim|qr\s*code|sent\s*money|debited|lost\s*money|transferred|stolen\s*money|money\s*deducted)\b",
            r"(ಯುಪಿಐ|ಹಣ\s*ಕಳೆದು|ಹಣ\s*ಕಡಿತ|ಜಿಪೇ|ಫೋನ್‌ಪೇ|ಪೇಟಿಎಂ|ಕ್ಯೂಆರ್\s*ಕೋಡ್|ವಂಚನೆ|ದುಡ್ಡು)",
            r"(यूपीआई|पैसे\s*कट\s*गए|धोखाधड़ी|गूगल\s*पे|फोनपे|पेटीएम|पैसे\s*वापस|क्यूआर\s*कोड)"
        ],
        "bank_kyc_freeze": [
            r"\b(kyc|account\s*block|account\s*freeze|account\s*suspend|pan\s*card\s*update|bank\s*sms|sbi|hdfc|icici)\b",
            r"(ಖಾತೆ\s*ಸ್ಥಗಿತ|ಕೆವೈಸಿ|ಪಾನ್\s*ಕಾರ್ಡ್|ಬ್ಯಾಂಕ್\s*ಖಾತೆ|ಬ್ಲಾಕ್\s*ಆಗಿದೆ|ಲಿಂಕ್\s*ಕ್ಲಿಕ್)",
            r"(केवाईसी|खाता\s*बंद|खाता\s*ब्लॉक|पैन\s*कार्ड\s*अपडेट|बैंक\s*संदेश|बैंक\s*खाता)"
        ],
        "otp_pin_safety": [
            r"\b(otp|pin|one\s*time\s*password|share\s*otp|enter\s*pin|receive\s*money\s*pin)\b",
            r"(ಓಟಿಪಿ|ಪಿನ್|ಪಾಸ್‌ವರ್ಡ್|ಹಣ\s*ಸ್ವೀಕರಿಸಲು\s*ಪಿನ್)",
            r"(ओटीपी|पिन|पासवर्ड|ओटीपी\s*मांग\s*रहा|पैसे\s*पाने\s*के\s*लिए\s*पिन)"
        ],
        "digital_arrest": [
            r"\b(digital\s*arrest|cbi|police\s*call|mumbai\s*police|customs|fedex\s*parcel|drugs|skype\s*call|warrant)\b",
            r"(ಡಿಜಿಟಲ್\s*ಅರೆಸ್ಟ್|ಪೊಲೀಸ್\s*ಕರೆ|ಸಿಬಿಐ|ಕೊರಿಯರ್|ಸ್ಕೈಪ್\s*ವಿಡಿಯೋ|ವಾರಂಟ್)",
            r"(डिजिटल\s*अरेस्ट|सीबीआई|पुलिस\s*कॉल|कस्टम\s*विभाग|पार्सल|ड्रग्स|स्काइप|वारंट)"
        ],
        "electricity_bill": [
            r"\b(electricity|power\s*cut|bill\s*unpaid|officer\s*number|light\s*bill|disconnected\s*tonight)\b",
            r"(ವಿದ್ಯುತ್\s*ಬಿಲ್|ಕರೆಂಟ್\s*ಕಟ್|ಬೆಸ್ಕಾಂ|ಲೈಟ್\s*ಬಿಲ್|ಸಂಪರ್ಕ\s*ಕಡಿತ)",
            r"(बिजली\s*बिल|बिजली\s*कट|पावर\s*कट|बिल\s*जमा|अधिकारी\s*का\s*नंबर)"
        ],
        "job_lottery_scam": [
            r"\b(part\s*time\s*job|work\s*from\s*home|telegram\s*task|youtube\s*like|lottery|kbc|prize|won\s*crores|gift\s*card)\b",
            r"(ಅರೆಕಾಲಿಕ\s*ಕೆಲಸ|ಟೆಲಿಗ್ರಾಂ|ಯೂಟ್ಯೂಬ್\s*ಲೈಕ್|ಲಾಟರಿ|ಬಹುಮಾನ|ಕೆಬಿಸಿ|ಲಕ್ಕಿ\s*ಡ್ರಾ)",
            r"(पार्ट\s*टाइम\s*जॉब|वर्क\s*फ्रॉम\s*होम|टेलीग्राम\s*टास्क|यूट्यूब\s*लाइक|लॉटरी|इनाम|केबीसी)"
        ],
        "cyber_harassment_women": [
            r"\b(harassment|stalking|blackmail|threat|morphing|private\s*photos|leaked|abuse|instagram\s*threat|fake\s*profile)\b",
            r"(ಕಿರುಕುಳ|ಬ್ಲಾಕ್‌ಮೇಲ್|ಬೆದರಿಕೆ|ಖಾಸಗಿ\s*ಫೋಟೋ|ನಕಲಿ\s*ಖಾತೆ|ಮಹಿಳಾ\s*ಸುರಕ್ಷತೆ|ಹಿಂಬಾಲಿಸುವುದು)",
            r"(उत्पीड़न|ब्लैकमेल|धमकी|निजी\s*फोटो|मॉर्फिंग|फेक\s*प्रोफाइल|छेड़छाड़|महिला\s*सुरक्षा)"
        ],
        "identity_theft_aadhaar": [
            r"\b(aadhaar|pan\s*misuse|fake\s*sim|sanchar\s*saathi|identity\s*theft|biometric\s*lock|loan\s*fraud)\b",
            r"(ಆಧಾರ್\s*ದುರುಪಯೋಗ|ನಕಲಿ\s*ಸಿಮ್|ಬಯೋಮೆಟ್ರಿಕ್\s*ಲಾಕ್|ಸಂಚಾರ\s*ಸಾಥಿ|ಗುರುತು\s*ಕಳ್ಳತನ)",
            r"(आधार\s*दुरुपयोग|फर्जी\s*सिम|बायोमेट्रिक\s*लॉक|संचार\s*साथी|पहचान\s*की\s*चोरी)"
        ],
        "phishing_links": [
            r"\b(link|url|website|click|suspicious\s*link|apk\s*file|download\s*app|fake\s*website)\b",
            r"(ಲಿಂಕ್|ವೆಬ್‌ಸೈಟ್|ಅನುಮಾನಾಸ್ಪದ\s*ಲಿಂಕ್|ಎಪಿಕೆ\s*ಫೈಲ್|ಆ್ಯಪ್\s*ಡೌನ್‌ಲೋಡ್)",
            r"(लिंक|वेबसाइट|फर्जी\s*लिंक|संदिग्ध\s*लिंक|एपीके\s*फाइल|ऐप\s*डाउनलोड)"
        ]
    }

    # Knowledge Base Dictionary: English, Kannada, Hindi
    KNOWLEDGE_BASE = {
        "upi_fraud": {
            "en": {
                "reply": (
                    "### 🚨 Immediate Action Protocol: UPI Fraud Recovery\n\n"
                    "If you have lost money via UPI (Google Pay, PhonePe, Paytm, BHIM):\n\n"
                    "1. **The Golden Hour Rule (Next 2 Hours Are Critical)**:\n"
                    "   - Call the **National Cyber Crime Helpline: 1930** immediately.\n"
                    "   - Provide the **Transaction ID / UTR number**, your bank account number, and the scammer's UPI ID / phone number.\n"
                    "   - The helpline works directly with banks to freeze the stolen funds before the fraudster withdraws them.\n\n"
                    "2. **Official Portal Registration**:\n"
                    "   - Visit **https://cybercrime.gov.in** and file a formal financial fraud complaint. Note down the Acknowledgement Number.\n\n"
                    "3. **Contact Your Bank**:\n"
                    "   - Call your bank's official toll-free fraud helpline. Request an immediate hotlist/freeze of your compromised UPI handle and debit cards.\n\n"
                    "4. **Raise a Dispute in Your UPI App**:\n"
                    "   - Open the payment app (GPay/PhonePe/Paytm) -> Go to Transaction History -> Select the fraudulent payment -> Click 'Have an issue with this transaction?' and report unauthorized debit.\n\n"
                    "> **Important Note**: SURAKSHA AI cannot recover money directly. Only legal reporting via 1930 within the Golden Hour enables bank freezes."
                ),
                "quick_actions": [
                    "Call 1930 Immediately",
                    "File Complaint at cybercrime.gov.in",
                    "Block Compromised Bank Cards",
                    "Raise Dispute in UPI App"
                ]
            },
            "kn": {
                "reply": (
                    "### 🚨 ತುರ್ತು ಸುರಕ್ಷತಾ ಕ್ರಮ: ಯುಪಿಐ ವಂಚನೆಗೆ ತಕ್ಷಣ ಏನು ಮಾಡಬೇಕು?\n\n"
                    "ನೀವು ಯುಪಿಐ (Google Pay, PhonePe, Paytm, BHIM) ಮೂಲಕ ಹಣ ಕಳೆದುಕೊಂಡಿದ್ದರೆ:\n\n"
                    "1. **ಗೋಲ್ಡನ್ ಅವರ್ ನಿಯಮ (ಮೊದಲ ೨ ಗಂಟೆಗಳು ಅತ್ಯಂತ ಮುಖ್ಯ)**:\n"
                    "   - ತಕ್ಷಣವೇ **ರಾಷ್ಟ್ರೀಯ ಸೈಬರ್ ಕ್ರೈಮ್ ಸಹಾಯವಾಣಿ: 1930** ಗೆ ಕರೆ ಮಾಡಿ.\n"
                    "   - ವಹಿವಾಟಿನ ಯುಟಿಆರ್ (UTR) ಸಂಖ್ಯೆ, ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆ ವಿವರ ಮತ್ತು ವಂಚಕನ ಯುಪಿಐ ಐಡಿ ನೀಡಿ.\n"
                    "   - ವಂಚಕನು ಹಣ ವಿತ್‌ಡ್ರಾ ಮಾಡುವ ಮುನ್ನ ಬ್ಯಾಂಕ್‌ಗಳ ಮೂಲಕ ಆ ಹಣವನ್ನು ತಡೆಹಿಡಿಯಲು (Freeze) 1930 ಸಹಾಯ ಮಾಡುತ್ತದೆ.\n\n"
                    "2. **ಅಧಿಕೃತ ಸೈಬರ್ ಕ್ರೈಮ್ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ದೂರು ದಾಖಲಿಸಿ**:\n"
                    "   - **https://cybercrime.gov.in** ಗೆ ಭೇಟಿ ನೀಡಿ ಹಣಕಾಸು ವಂಚನೆ (Financial Fraud) ದೂರು ದಾಖಲಿಸಿ.\n\n"
                    "3. **ನಿಮ್ಮ ಬ್ಯಾಂಕ್‌ಗೆ ಮಾಹಿತಿ ನೀಡಿ**:\n"
                    "   - ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಗ್ರಾಹಕ ಸೇವಾ ಸಂಖ್ಯೆಗೆ ಕರೆ ಮಾಡಿ, ಯುಪಿಐ ವಹಿವಾಟನ್ನು ಸ್ಥಗಿತಗೊಳಿಸಲು (Block) ವಿನಂತಿಸಿ.\n\n"
                    "4. **ಯುಪಿಐ ಆ್ಯಪ್‌ನಲ್ಲಿ ದೂರು ನೀಡಿ**:\n"
                    "   - ಆ್ಯಪ್‌ನಲ್ಲಿ ವಹಿವಾಟು ಇತಿಹಾಸಕ್ಕೆ ಹೋಗಿ 'Report Issue' ಆಯ್ಕೆಮಾಡಿ ಅನಧಿಕೃತ ಡೆಬಿಟ್ ಎಂದು ದೂರು ನೀಡಿ.\n\n"
                    "> **ನೆನಪಿಡಿ**: ಯುಪಿಐ ಪಿನ್ (PIN) ಅನ್ನು ಹಣ ಕಳುಹಿಸಲು ಮಾತ್ರ ಬಳಸಲಾಗುತ್ತದೆ; ಹಣ ಸ್ವೀಕರಿಸಲು ಯಾವುದೇ ಪಿನ್ ಅಗತ್ಯವಿಲ್ಲ!"
                ),
                "quick_actions": [
                    "ತಕ್ಷಣ 1930 ಗೆ ಕರೆ ಮಾಡಿ",
                    "cybercrime.gov.in ನಲ್ಲಿ ದೂರು ದಾಖಲಿಸಿ",
                    "ಬ್ಯಾಂಕ್ ಕಾರ್ಡ್ ಬ್ಲಾಕ್ ಮಾಡಿ",
                    "ಯುಪಿಐ ಆ್ಯಪ್‌ನಲ್ಲಿ ದೂರು ನೀಡಿ"
                ]
            },
            "hi": {
                "reply": (
                    "### 🚨 तत्काल सुरक्षा प्रोटोकॉल: यूपीआई फ्रॉड से पैसे कैसे बचाएं?\n\n"
                    "यदि आपके साथ यूपीआई (Google Pay, PhonePe, Paytm, BHIM) के माध्यम से धोखाधड़ी हुई है:\n\n"
                    "1. **गोल्डन ऑवर नियम (पहले 2 घंटे सबसे महत्वपूर्ण हैं)**:\n"
                    "   - तुरंत **राष्ट्रीय साइबर अपराध हेल्पलाइन: 1930** पर कॉल करें।\n"
                    "   - ट्रांजेक्शन आईडी (UTR नंबर), अपना बैंक खाता और धोखेबाज का यूपीआई आईडी / नंबर दर्ज कराएं।\n"
                    "   - 1930 हेल्पलाइन बैंकों के साथ समन्वय करके धोखेबाज के खाते से पैसे निकलने से पहले उसे फ्रीज करवाती है।\n\n"
                    "2. **आधिकारिक पोर्टल पर रिपोर्ट करें**:\n"
                    "   - **https://cybercrime.gov.in** पर जाएं और वित्तीय धोखाधड़ी की शिकायत दर्ज करें। रसीद नंबर सुरक्षित रखें।\n\n"
                    "3. **अपने बैंक से तुरंत संपर्क करें**:\n"
                    "   - अपने बैंक की आधिकारिक हेल्पलाइन पर कॉल करके प्रभावित खाते और डेबिट कार्ड को तुरंत ब्लॉक करवाएं।\n\n"
                    "4. **यूपीआई ऐप में शिकायत दर्ज करें**:\n"
                    "   - ऐप (GPay/PhonePe) के ट्रांजेक्शन हिस्ट्री में जाएं, संबंधित भुगतान चुनें और 'Report Fraud / Unauthorized Debit' दर्ज करें।\n\n"
                    "> **सावधानी**: यूपीआई पिन (PIN) केवल पैसे भेजने के लिए होता है, पैसे प्राप्त करने के लिए कभी पिन दर्ज न करें!"
                ),
                "quick_actions": [
                    "तुरंत 1930 पर कॉल करें",
                    "cybercrime.gov.in पर रिपोर्ट दर्ज करें",
                    "बैंक खाता/कार्ड ब्लॉक करें",
                    "यूपीआई ऐप में शिकायत दर्ज करें"
                ]
            }
        },

        "bank_kyc_freeze": {
            "en": {
                "reply": (
                    "### 🛡️ Fake Bank KYC & Account Block Warning\n\n"
                    "Scammers send fake SMS claiming: *'Your SBI/HDFC/ICICI account is blocked due to incomplete KYC. Click link to update.'*\n\n"
                    "1. **Do NOT Click the Link**: Real banks never send update links via ordinary SMS or WhatsApp. The link leads to a phishing page designed to steal your credentials.\n"
                    "2. **Never Install Any App / APK**: Scammers will ask you to install apps like AnyDesk, QuickSupport, or an APK file. These apps grant remote access to your device and empty your account.\n"
                    "3. **How to Verify Legitimate Account Status**:\n"
                    "   - Open your official banking mobile app (e.g., YONO, iMobile, HDFC Mobile) directly.\n"
                    "   - Or visit your local bank branch in person.\n"
                    "4. **Report the Fraudulent SMS**:\n"
                    "   - Forward the suspicious SMS to **1909** (Telecom Spam reporting) or report it on SURAKSHA AI Community Reports."
                ),
                "quick_actions": [
                    "Never Click SMS Links",
                    "Never Install Remote Apps (AnyDesk)",
                    "Verify Directly at Bank Branch",
                    "Report SMS to 1909"
                ]
            },
            "kn": {
                "reply": (
                    "### 🛡️ ನಕಲಿ ಬ್ಯಾಂಕ್ ಕೆವೈಸಿ (KYC) ಹಾಗೂ ಖಾತೆ ಸ್ಥಗಿತ ವಂಚನೆ ಎಚ್ಚರಿಕೆ\n\n"
                    "ವಂಚಕರು: *'ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆ ಸ್ಥಗಿತಗೊಂಡಿದೆ, ಕೆವೈಸಿ ಅಪ್‌ಡೇಟ್ ಮಾಡಲು ಈ ಲಿಂಕ್ ಕ್ಲಿಕ್ ಮಾಡಿ'* ಎಂದು ಸಂದೇಶ ಕಳುಹಿಸುತ್ತಾರೆ.\n\n"
                    "1. **ಲಿಂಕ್ ಕ್ಲಿಕ್ ಮಾಡಬೇಡಿ**: ಅಧಿಕೃತ ಬ್ಯಾಂಕ್‌ಗಳು ಎಂದಿಗೂ ಎಸ್‌ಎಂಎಸ್ ಮೂಲಕ ಕೆವೈಸಿ ಅಪ್‌ಡೇಟ್ ಲಿಂಕ್ ಕಳುಹಿಸುವುದಿಲ್ಲ.\n"
                    "2. **ಯಾವುದೇ ಆ್ಯಪ್ ಅಥವಾ ಎಪಿಕೆ (APK) ಡೌನ್‌ಲೋಡ್ ಮಾಡಬೇಡಿ**: AnyDesk, QuickSupport ನಂತಹ ಸ್ಕ್ರೀನ್ ಶೇರಿಂಗ್ ಆ್ಯಪ್‌ಗಳನ್ನು ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಲು ಹೇಳಿ ಹಣ ಲೂಟಿ ಮಾಡುತ್ತಾರೆ.\n"
                    "3. **ಖಾತೆಯ ಸ್ಥಿತಿ ತಿಳಿಯುವುದು ಹೇಗೆ?**:\n"
                    "   - ನಿಮ್ಮ ಬ್ಯಾಂಕಿನ ಅಧಿಕೃತ ಮೊಬೈಲ್ ಆ್ಯಪ್ (YONO, HDFC App) ಮೂಲಕ ನೇರವಾಗಿ ಪರಿಶೀಲಿಸಿ.\n"
                    "   - ಅಥವಾ ನೇರವಾಗಿ ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಶಾಖೆಗೆ ಭೇಟಿ ನೀಡಿ.\n"
                    "4. **ಸಂದೇಶವನ್ನು ವರದಿ ಮಾಡಿ**: ವಂಚನೆಯ ಎಸ್‌ಎಂಎಸ್ ಅನ್ನು **1909** ಗೆ ಫಾರ್ವರ್ಡ್ ಮಾಡಿ ದೂರಸಂಪರ್ಕ ಇಲಾಖೆಗೆ ದೂರು ನೀಡಿ."
                ),
                "quick_actions": [
                    "ಯಾವುದೇ ಲಿಂಕ್ ಕ್ಲಿಕ್ ಮಾಡಬೇಡಿ",
                    "AnyDesk ಆ್ಯಪ್ ಡೌನ್‌ಲೋಡ್ ಮಾಡಬೇಡಿ",
                    "ಬ್ಯಾಂಕ್ ಶಾಖೆಗೆ ಭೇಟಿ ನೀಡಿ",
                    "1909 ಗೆ ದೂರು ಕಳುಹಿಸಿ"
                ]
            },
            "hi": {
                "reply": (
                    "### 🛡️ फर्जी बैंक केवाईसी (KYC) और खाता ब्लॉक धोखाधड़ी से बचाव\n\n"
                    "धोखेबाज फर्जी मैसेज भेजते हैं: *'आपका बैंक खाता केवाईसी अधूरा होने के कारण बंद कर दिया गया है। तुरंत लिंक पर क्लिक करें।'* \n\n"
                    "1. **लिंक पर कभी क्लिक न करें**: असली बैंक कभी भी एसएमएस या व्हाट्सएप पर केवाईसी अपडेट लिंक नहीं भेजते। यह फिशिंग लिंक होता है।\n"
                    "2. **कोई भी ऐप या एपीके (APK) इंस्टॉल न करें**: धोखेबाज अक्सर AnyDesk, TeamViewer या QuickSupport ऐप डाउनलोड करवाते हैं, जिससे वे आपका फोन नियंत्रित कर पैसे निकाल लेते हैं।\n"
                    "3. **खाते की सही स्थिति कैसे जांचें?**:\n"
                    "   - अपने बैंक के आधिकारिक ऐप (जैसे YONO SBI) से खुद लॉग इन करें।\n"
                    "   - या अपनी नजदीकी बैंक शाखा में जाकर सीधे संपर्क करें।\n"
                    "4. **फर्जी मैसेज की शिकायत करें**: इस मैसेज को **1909** पर फॉरवर्ड करके टेलीकॉम ऑपरेटर को रिपोर्ट करें।"
                ),
                "quick_actions": [
                    "एसएमएस लिंक पर कभी क्लिक न करें",
                    "कोई स्क्रीन शेयरिंग ऐप न डालें",
                    "नजदीकी बैंक शाखा से पुष्टि करें",
                    "1909 पर संदेश रिपोर्ट करें"
                ]
            }
        },

        "otp_pin_safety": {
            "en": {
                "reply": (
                    "### 🔒 Golden Rule of Digital Safety: OTP & UPI PIN Protection\n\n"
                    "1. **UPI PIN is Exclusively for DEBITING (Sending) Money**:\n"
                    "   - You **NEVER** need to enter your UPI PIN to receive money, accept cashback, or claim a prize.\n"
                    "   - If someone asks you to enter your PIN to receive money, **it is a 100% confirmed scam**.\n"
                    "2. **No Bank Official Ever Asks for OTP**:\n"
                    "   - Bank staff, police officers, or customer care will never demand your OTP, password, or CVV.\n"
                    "   - Never read out or forward OTP messages to anyone over the phone.\n"
                    "3. **What to Do if You Accurately Shared an OTP**:\n"
                    "   - Immediately open your banking app and block your debit card and UPI access.\n"
                    "   - Call your bank's emergency fraud line instantly."
                ),
                "quick_actions": [
                    "Never Enter PIN to Receive Money",
                    "Never Share OTP with Anyone",
                    "Block Card Immediately if Leaked",
                    "Call Bank Emergency Helpline"
                ]
            },
            "kn": {
                "reply": (
                    "### 🔒 ಡಿಜಿಟಲ್ ಸುರಕ್ಷತೆಯ ಸುವರ್ಣ ನಿಯಮ: ಓಟಿಪಿ (OTP) ಮತ್ತು ಯುಪಿಐ ಪಿನ್ ಭದ್ರತೆ\n\n"
                    "1. **ಯುಪಿಐ ಪಿನ್ (UPI PIN) ಕೇವಲ ಹಣ ಕಳುಹಿಸಲು ಮಾತ್ರ**:\n"
                    "   - ಯಾವುದೇ ಕಾರಣಕ್ಕೂ ಹಣ, ಬಹುಮಾನ ಅಥವಾ ಕ್ಯಾಶ್‌ಬ್ಯಾಕ್ ಸ್ವೀಕರಿಸಲು ಯುಪಿಐ ಪಿನ್ ನಮೂದಿಸಬೇಕಾಗಿಲ್ಲ.\n"
                    "   - ಯಾರಾದರೂ ಹಣ ನೀಡಲು ಪಿನ್ ನಮೂದಿಸಿ ಎಂದರೆ ಅದು ೧೦೦% ಖಚಿತ ವಂಚನೆ!\n"
                    "2. **ಯಾರೂ ಓಟಿಪಿ (OTP) ಕೇಳುವಂತಿಲ್ಲ**:\n"
                    "   - ಬ್ಯಾಂಕ್ ಅಧಿಕಾರಿಗಳು, ಪೊಲೀಸರು ಅಥವಾ ಕಸ್ಟಮರ್ ಕೇರ್ ಸಿಬ್ಬಂದಿ ಎಂದಿಗೂ ನಿಮ್ಮ ಓಟಿಪಿ ಅಥವಾ ಸಿವಿವಿ (CVV) ಕೇಳುವುದಿಲ್ಲ.\n"
                    "3. **ತಪ್ಪಿ ಓಟಿಪಿ ಹಂಚಿಕೊಂಡಿದ್ದರೆ ತಕ್ಷಣ ಏನು ಮಾಡಬೇಕು?**:\n"
                    "   - ತಕ್ಷಣ ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಆ್ಯಪ್ ಮೂಲಕ ಎಟಿಎಂ ಕಾರ್ಡ್ ಮತ್ತು ಯುಪಿಐ ಅನ್ನು ಬ್ಲಾಕ್ ಮಾಡಿ.\n"
                    "   - ಬ್ಯಾಂಕ್ ಗ್ರಾಹಕ ಸೇವೆಗೆ ಕರೆ ಮಾಡಿ ವರದಿ ಮಾಡಿ."
                ),
                "quick_actions": [
                    "ಹಣ ಸ್ವೀಕರಿಸಲು ಪಿನ್ ಹಾಕಬೇಡಿ",
                    "ಯಾರೊಂದಿಗೂ ಓಟಿಪಿ ಹಂಚಿಕೊಳ್ಳಬೇಡಿ",
                    "ಕಾರ್ಡ್ ತಕ್ಷಣ ಬ್ಲಾಕ್ ಮಾಡಿ",
                    "ಬ್ಯಾಂಕ್ ಸಹಾಯವಾಣಿಗೆ ಕರೆ ಮಾಡಿ"
                ]
            },
            "hi": {
                "reply": (
                    "### 🔒 डिजिटल सुरक्षा का स्वर्णिम नियम: ओटीपी (OTP) और यूपीआई पिन की सुरक्षा\n\n"
                    "1. **यूपीआई पिन केवल पैसे भेजने (कटने) के लिए होता है**:\n"
                    "   - पैसे प्राप्त करने, कैशबैक पाने या लॉटरी का इनाम लेने के लिए **कभी भी यूपीआई पिन दर्ज नहीं करना पड़ता**।\n"
                    "   - अगर कोई कहे कि 'पिन डालो, पैसे आपके खाते में आ जाएंगे', तो वह 100% फ्रॉड है!\n"
                    "2. **कोई भी बैंक कर्मचारी कभी ओटीपी नहीं मांगता**:\n"
                    "   - बैंक, पुलिस या कस्टमर केयर अधिकारी कभी भी आपका ओटीपी, पासवर्ड या सीवीवी नहीं मांगते।\n"
                    "3. **अगर गलती से ओटीपी बता दिया हो तो क्या करें?**:\n"
                    "   - तुरंत अपनी बैंक ऐप में जाकर अपना डेबिट कार्ड और यूपीआई ट्रांजैक्शन ब्लॉक करें।\n"
                    "   - बैंक के इमरजेंसी फ्रॉड नंबर पर तुरंत कॉल करें।"
                ),
                "quick_actions": [
                    "पैसे पाने के लिए पिन न डालें",
                    "किसी को भी ओटीपी न बताएं",
                    "गलती होने पर तुरंत कार्ड ब्लॉक करें",
                    "बैंक हेल्पलाइन पर सूचित करें"
                ]
            }
        },

        "digital_arrest": {
            "en": {
                "reply": (
                    "### ⚖️ Digital Arrest Scam Alert: The Truth About Police / CBI Impersonation\n\n"
                    "**FACT: In Indian Law, there is NO such concept as 'Digital Arrest'.**\n\n"
                    "1. **How the Scam Operates**:\n"
                    "   - Scammers pose as Mumbai Police, CBI, ED, Customs, or TRAI.\n"
                    "   - They call claiming your Aadhaar or phone was used for illegal drugs/parcels, money laundering, or terrorist financing.\n"
                    "   - They show fake police uniforms, forged Supreme Court/CBI letters, and force you to stay on a 24-hour Skype/WhatsApp video call.\n"
                    "   - They demand you transfer your entire savings into a 'Reserve Bank verification account' to prove innocence.\n"
                    "2. **Official Protocol**:\n"
                    "   - Police or courts **NEVER** conduct arrests, hearings, or identity interrogations via video calls.\n"
                    "   - Police **NEVER** ask citizens to transfer money to personal or so-called government verification accounts.\n"
                    "3. **Action Steps**:\n"
                    "   - **Disconnect the video call immediately.**\n"
                    "   - Do not transfer any money.\n"
                    "   - Call the **Cyber Crime Helpline at 1930** and National Emergency **112**.\n"
                    "   - File a complaint at **https://cybercrime.gov.in**."
                ),
                "quick_actions": [
                    "Disconnect Video Call Immediately",
                    "Never Transfer Money for 'Verification'",
                    "Dial 1930 and 112",
                    "Report at cybercrime.gov.in"
                ]
            },
            "kn": {
                "reply": (
                    "### ⚖️ ಡಿಜಿಟಲ್ ಅರೆಸ್ಟ್ (Digital Arrest) ವಂಚನೆ ಎಚ್ಚರಿಕೆ: ನೈಜ ಕಾನೂನು ಸತ್ಯಾಂಶಗಳು\n\n"
                    "**ಸತ್ಯ: ಭಾರತೀಯ ಕಾನೂನಿನಲ್ಲಿ 'ಡಿಜಿಟಲ್ ಅರೆಸ್ಟ್' ಎಂಬ ಯಾವುದೇ ಪರಿಕಲ್ಪನೆಯೇ ಇಲ್ಲ!**\n\n"
                    "1. **ವಂಚಕರು ಹೇಗೆ ಮೋಸ ಮಾಡುತ್ತಾರೆ?**:\n"
                    "   - ಮುಂಬೈ ಪೊಲೀಸ್, ಸಿಬಿಐ, ಇಡಿ, ಕಸ್ಟಮ್ಸ್ ಅಥವಾ ಟ್ರಾಯ್ (TRAI) ಅಧಿಕಾರಿಗಳೆಂದು ನಟಿಸುತ್ತಾರೆ.\n"
                    "   - ನಿಮ್ಮ ಹೆಸರಿನ ಪಾರ್ಸೆಲ್‌ನಲ್ಲಿ ಮಾದಕ ದ್ರವ್ಯಗಳಿವೆ ಎಂದು ಸುಳ್ಳು ಹೇಳಿ ಬೆದರಿಸುತ್ತಾರೆ.\n"
                    "   - ನಕಲಿ ಪೊಲೀಸ್ ಸಮವಸ್ತ್ರ ಧರಿಸಿ ಸ್ಕೈಪ್ ಅಥವಾ ವಾಟ್ಸಾಪ್ ವಿಡಿಯೋ ಕಾಲ್‌ನಲ್ಲಿ ಕಟ್ಟಿಹಾಕುತ್ತಾರೆ.\n"
                    "   - ಪರಿಶೀಲನೆಗಾಗಿ ಹಣವನ್ನು ಆರ್‌ಬಿಐ ಖಾತೆಗೆ ವರ್ಗಾಯಿಸಿ ಎಂದು ಕೋಟ್ಯಂತರ ಹಣ ಲೂಟಿ ಮಾಡುತ್ತಾರೆ.\n"
                    "2. **ನಿಜವಾದ ನಿಯಮಗಳು**:\n"
                    "   - ಯಾವುದೇ ಪೊಲೀಸರು ವಿಡಿಯೋ ಕಾಲ್ ಮೂಲಕ ಬಂಧಿಸುವುದಿಲ್ಲ ಅಥವಾ ವಿಚಾರಣೆ ನಡೆಸುವುದಿಲ್ಲ.\n"
                    "   - ಪೊಲೀಸರು ಎಂದಿಗೂ ನಾಗರಿಕರಿಂದ ಹಣ ವರ್ಗಾವಣೆ ಕೇಳುವುದಿಲ್ಲ.\n"
                    "3. **ನೀವು ಮಾಡಬೇಕಾದದ್ದು**:\n"
                    "   - **ತಕ್ಷಣ ವಿಡಿಯೋ ಕಾಲ್ ಕಟ್ ಮಾಡಿ.**\n"
                    "   - ಯಾವುದೇ ಕಾರಣಕ್ಕೂ ಹಣ ಕಳುಹಿಸಬೇಡಿ.\n"
                    "   - ಸೈಬರ್ ಹೆಲ್ಪ್‌ಲೈನ್ **1930** ಹಾಗೂ ತುರ್ತು ಸಹಾಯವಾಣಿ **112** ಗೆ ಕರೆ ಮಾಡಿ."
                ),
                "quick_actions": [
                    "ತಕ್ಷಣ ವಿಡಿಯೋ ಕಾಲ್ ಕಟ್ ಮಾಡಿ",
                    "ಯಾವುದೇ ಹಣ ವರ್ಗಾಯಿಸಬೇಡಿ",
                    "1930 ಹಾಗೂ 112 ಗೆ ಕರೆ ಮಾಡಿ",
                    "cybercrime.gov.in ನಲ್ಲಿ ದೂರು ದಾಖಲಿಸಿ"
                ]
            },
            "hi": {
                "reply": (
                    "### ⚖️ डिजिटल अरेस्ट फ्रॉड से सावधान: पुलिस / सीबीआई के नाम पर ब्लैकमेल\n\n"
                    "**सत्य: भारतीय कानून में 'डिजिटल अरेस्ट' नाम की कोई भी कानूनी प्रक्रिया नहीं है!**\n\n"
                    "1. **ठग कैसे फंसाते हैं?**:\n"
                    "   - खुद को मुंबई पुलिस, सीबीआई, नारकोटिक्स, कस्टम्स या ट्राई का अधिकारी बताते हैं।\n"
                    "   - कहते हैं कि आपके आधार या नंबर से गैरकानूनी पार्सल भेजा गया है जिसमें ड्रग्स या फर्जी पासपोर्ट हैं।\n"
                    "   - फर्जी पुलिस स्टेशन का सेटअप और वर्दी दिखाकर स्काइप/व्हाट्सएप वीडियो कॉल पर बंधक बना लेते हैं।\n"
                    "   - 'सरकारी जांच' के नाम पर आपके सारे पैसे एक बैंक खाते में ट्रांसफर करवा लेते हैं।\n"
                    "2. **कानूनी वास्तविकता**:\n"
                    "   - कोई भी पुलिस विभाग या अदालत वीडियो कॉल पर किसी को गिरफ्तार नहीं करती।\n"
                    "   - कानून में कोई भी अधिकारी किसी नागरिक से बैंक ट्रांसफर की मांग नहीं करता।\n"
                    "3. **आपको तुरंत क्या करना चाहिए?**:\n"
                    "   - **तुरंत वीडियो कॉल काट दें।**\n"
                    "   - किसी भी खाते में एक रुपया भी न भेजें।\n"
                    "   - तुरंत **1930** और **112** पर कॉल करें और पुलिस को सूचित करें।"
                ),
                "quick_actions": [
                    "तुरंत वीडियो कॉल काटें",
                    "जांच के नाम पर कोई पैसा न भेजें",
                    "1930 और 112 पर कॉल करें",
                    "cybercrime.gov.in पर रिपोर्ट दर्ज करें"
                ]
            }
        },

        "electricity_bill": {
            "en": {
                "reply": (
                    "### 💡 Electricity Bill Disconnection Scam Warning\n\n"
                    "SMS text: *'Dear Consumer, Your electricity power will be disconnected tonight at 9:30 PM because previous month bill was not updated. Immediately call officer at 98xxxxxx.'*\n\n"
                    "1. **Confirmed Scam**: Power discoms (like BESCOM, MSEB, BSES, Tata Power) never send personal 10-digit mobile numbers for bill payments.\n"
                    "2. **Never Call the Given Mobile Number**: The scammer will instruct you to pay Rs. 10 through a malicious link or install a remote app, draining your account.\n"
                    "3. **How to Verify**:\n"
                    "   - Check your actual electricity bill status on the official DISCOM website or mobile app.\n"
                    "   - Or verify through trusted payment apps like Bharat BillPay (BBPS)."
                ),
                "quick_actions": [
                    "Do Not Call Personal Numbers",
                    "Never Pay via Unofficial Links",
                    "Verify via Official Discom App / BBPS",
                    "Report SMS to 1909"
                ]
            },
            "kn": {
                "reply": (
                    "### 💡 ವಿದ್ಯುತ್ ಬಿಲ್ ಸಂಪರ್ಕ ಕಡಿತ ವಂಚನೆ ಎಚ್ಚರಿಕೆ\n\n"
                    "ಎಸ್‌ಎಂಎಸ್: *'ನಿಮ್ಮ ಹಿಂದಿನ ತಿಂಗಳ ಕರೆಂಟ್ ಬಿಲ್ ಪಾವತಿಯಾಗಿಲ್ಲ, ಇಂದು ರಾತ್ರಿ ೯:೩೦ಕ್ಕೆ ವಿದ್ಯುತ್ ಕಡಿತಗೊಳಿಸಲಾಗುವುದು. ತಕ್ಷಣ ಅಧಿಕಾರಿಯ ಸಂಖ್ಯೆಗೆ ಕರೆ ಮಾಡಿ.'*\n\n"
                    "1. **ಖಚಿತ ವಂಚನೆ**: ಬೆಸ್ಕಾಂ (BESCOM) ಅಥವಾ ಯಾವುದೇ ವಿದ್ಯುತ್ ಮಂಡಳಿಯು ವೈಯಕ್ತಿಕ ಮೊಬೈಲ್ ಸಂಖ್ಯೆಯನ್ನು ನೀಡುವುದಿಲ್ಲ.\n"
                    "2. **ಆ ಸಂಖ್ಯೆಗೆ ಕರೆ ಮಾಡಬೇಡಿ**: ಅವರು ಕೇವಲ ೧೦ ರೂಪಾಯಿ ಪಾವತಿಸಲು ನಕಲಿ ಲಿಂಕ್ ನೀಡಿ ಇಡೀ ಖಾತೆಯ ಹಣವನ್ನು ದೋಚುತ್ತಾರೆ.\n"
                    "3. **ಪರಿಶೀಲಿಸುವುದು ಹೇಗೆ?**:\n"
                    "   - ನಿಮ್ಮ ವಿದ್ಯುತ್ ನಿಗಮದ ಅಧಿಕೃತ ಆ್ಯಪ್ ಅಥವಾ ಬಿಲ್‌ಪೇ (BBPS) ಮೂಲಕ ಮಾತ್ರ ಬಿಲ್ ಪರಿಶೀಲಿಸಿ."
                ),
                "quick_actions": [
                    "ವೈಯಕ್ತಿಕ ನಂಬರ್‌ಗೆ ಕರೆ ಮಾಡಬೇಡಿ",
                    "ನಕಲಿ ಲಿಂಕ್ ಮೂಲಕ ಹಣ ಪಾವತಿಸಬೇಡಿ",
                    "ಅಧಿಕೃತ ಬೆಸ್ಕಾಂ/ಬಿಬಿಪಿಎಸ್ ನಲ್ಲಿ ಪರಿಶೀಲಿಸಿ",
                    "1909 ಗೆ ದೂರು ನೀಡಿ"
                ]
            },
            "hi": {
                "reply": (
                    "### 💡 बिजली बिल और पावर कट फ्रॉड से सावधान\n\n"
                    "फर्जी एसएमएस: *'प्रिय उपभोक्ता, आपके पिछले महीने का बिजली बिल अपडेट नहीं हुआ है, आज रात 9:30 बजे बिजली काट दी जाएगी। तुरंत अधिकारी से संपर्क करें।'* \n\n"
                    "1. **पूरी तरह फर्जी संदेश**: बिजली विभाग कभी भी किसी व्यक्तिगत 10 अंकों के मोबाइल नंबर पर कॉल करने या पैसे ट्रांसफर करने के लिए नहीं कहता।\n"
                    "2. **दिए गए नंबर पर कॉल न करें**: धोखेबाज 10 रुपये जमा करने के नाम पर ऐप डलवाकर पूरा खाता खाली कर देते हैं।\n"
                    "3. **सही स्थिति कैसे जानें?**:\n"
                    "   - अपने बिजली विभाग के आधिकारिक पोर्टल या ऐप से बिल चेक करें।\n"
                    "   - या भारत बिलपे (BBPS) के जरिए सत्यापित करें।"
                ),
                "quick_actions": [
                    "संदेश में दिए नंबर पर कॉल न करें",
                    "अनजान लिंक से भुगतान न करें",
                    "बिजली विभाग के ऐप / BBPS से जांचें",
                    "1909 पर संदेश रिपोर्ट करें"
                ]
            }
        },

        "job_lottery_scam": {
            "en": {
                "reply": (
                    "### 💼 Part-Time Job, Telegram & Fake Lottery Scams\n\n"
                    "Common Scams: *'Earn ₹3,000 to ₹5,000/day by liking YouTube videos or rating hotels on Telegram'*, or *'You won ₹25 Lakhs in KBC Lottery.'*\n\n"
                    "1. **The Trap**:\n"
                    "   - Scammers pay Rs. 150-500 initially to build trust.\n"
                    "   - Then, they introduce 'Prepaid Crypto Tasks' or 'Processing Fees' demanding Rs. 10,000 to Rs. 5,00,000, promising huge returns.\n"
                    "   - Once you transfer money, they block you immediately.\n"
                    "2. **Golden Rule**:\n"
                    "   - **No legitimate employer will EVER ask you to pay money to get a job.**\n"
                    "   - No genuine lottery requires paying 'GST' or 'processing charge' upfront.\n"
                    "3. **What to Do**:\n"
                    "   - Never deposit money for jobs or prize winnings.\n"
                    "   - Leave the Telegram / WhatsApp group immediately and report it."
                ),
                "quick_actions": [
                    "Never Pay to Get a Job",
                    "Do Not Trust Telegram Crypto Tasks",
                    "Leave Suspicious Groups",
                    "Report to 1930 / cybercrime.gov.in"
                ]
            },
            "kn": {
                "reply": (
                    "### 💼 ಅರೆಕಾಲಿಕ ಕೆಲಸ, ಟೆಲಿಗ್ರಾಂ ಮತ್ತು ನಕಲಿ ಲಾಟರಿ ವಂಚನೆ\n\n"
                    "ಸಾಮಾನ್ಯ ವಂಚನೆಗಳು: *'ಯೂಟ್ಯೂಬ್ ಲೈಕ್ ಮಾಡಿ ದಿನಕ್ಕೆ ₹೩೦೦೦ ಗಳಿಸಿ'*, ಅಥವಾ *'ಕೆಬಿಸಿ ಲಾಟರಿಯಲ್ಲಿ ₹೨೫ ಲಕ್ಷ ಗೆದ್ದಿದ್ದೀರಿ.'*\n\n"
                    "1. **ವಂಚನೆಯ ವಿಧಾನ**:\n"
                    "   - ನಂಬಿಕೆ ಹುಟ್ಟಿಸಲು ಮೊದಲು ₹೨೦೦ - ₹೫೦೦ ಜಮೆ ಮಾಡುತ್ತಾರೆ.\n"
                    "   - ನಂತರ ಹೆಚ್ಚಿನ ಲಾಭದ ಆಮಿಷವೊಡ್ಡಿ ಹೂಡಿಕೆ ಅಥವಾ ಪ್ರೀಪೇಯ್ಡ್ ಟಾಸ್ಕ್ ಹೆಸರಿನಲ್ಲಿ ಲಕ್ಷಾಂತರ ರೂಪಾಯಿ ಕಸಿದುಕೊಳ್ಳುತ್ತಾರೆ.\n"
                    "2. **ಸುವರ್ಣ ನಿಯಮ**:\n"
                    "   - **ಯಾವುದೇ ಅಧಿಕೃತ ಕಂಪನಿಯು ಉದ್ಯೋಗ ನೀಡಲು ನಿಮ್ಮಿಂದ ಹಣ ಕೇಳುವುದಿಲ್ಲ!**\n"
                    "   - ಲಾಟರಿ ಹಣ ಪಡೆಯಲು ಜಿಎಸ್‌ಟಿ ಅಥವಾ ಪ್ರೊಸೆಸಿಂಗ್ ಶುಲ್ಕ ಪಾವತಿಸುವ ನಿಯಮವಿಲ್ಲ.\n"
                    "3. **ಕ್ರಮಗಳು**: ಆ ವಾಟ್ಸಾಪ್/ಟೆಲಿಗ್ರಾಂ ಗ್ರೂಪ್‌ನಿಂದ ತಕ್ಷಣ ಹೊರಬನ್ನಿ ಮತ್ತು ವರದಿ ಮಾಡಿ."
                ),
                "quick_actions": [
                    "ಉದ್ಯೋಗಕ್ಕಾಗಿ ಹಣ ನೀಡಬೇಡಿ",
                    "ಟೆಲಿಗ್ರಾಂ ಟಾಸ್ಕ್ ನಂಬಬೇಡಿ",
                    "ಗ್ರೂಪ್‌ನಿಂದ ಹೊರಬನ್ನಿ",
                    "1930 ಗೆ ದೂರು ನೀಡಿ"
                ]
            },
            "hi": {
                "reply": (
                    "### 💼 पार्ट-टाइम जॉब, टेलीग्राम टास्क और फर्जी लॉटरी से सावधान\n\n"
                    "धोखाधड़ी के तरीके: *'यूट्यूब वीडियो लाइक करके रोज ₹3,000 से ₹5,000 कमाएं'* या *'केबीसी लॉटरी में 25 लाख रुपये जीते हैं।'*\n\n"
                    "1. **जाल कैसे बिछाया जाता है?**:\n"
                    "   - विश्वास जीतने के लिए पहले 200-500 रुपये का भुगतान करते हैं।\n"
                    "   - फिर बड़े मुनाफे का झांसा देकर 'प्रीपेड टास्क' या 'सिक्योरिटी डिपॉजिट' के नाम पर लाखों रुपये ऐंठ लेते हैं।\n"
                    "2. **याद रखने योग्य नियम**:\n"
                    "   - **कोई भी असली कंपनी नौकरी देने के बदले पैसे नहीं मांगती।**\n"
                    "   - कोई भी वास्तविक लॉटरी पैसे जारी करने के लिए 'टैक्स' या 'फीस' अग्रिम नहीं मांगती।\n"
                    "3. **क्या करें**:\n"
                    "   - नौकरी के नाम पर किसी को भी पैसे न भेजें।\n"
                    "   - संदिग्ध टेलीग्राम/व्हाट्सएप ग्रुप को तुरंत छोड़ें और रिपोर्ट करें।"
                ),
                "quick_actions": [
                    "नौकरी के लिए कभी पैसे न दें",
                    "टेलीग्राम क्रिप्टो टास्क से बचें",
                    "संदिग्ध ग्रुप से तुरंत हटें",
                    "1930 पर शिकायत दर्ज करें"
                ]
            }
        },

        "cyber_harassment_women": {
            "en": {
                "reply": (
                    "### 🛡️ Women Digital Safety & Cyber Harassment Support\n\n"
                    "If you are facing blackmail, morphed photos, stalking, or abusive threats:\n\n"
                    "1. **Do NOT Delete Evidence**:\n"
                    "   - Take clear screenshots of chat messages, profiles, phone numbers, and URL links.\n"
                    "   - Note down timestamps. This is vital evidence for police action.\n"
                    "2. **Never Pay Extortion Money**:\n"
                    "   - Blackmailers never stop after one payment; giving money only increases extortion.\n"
                    "3. **Anonymous Official Reporting**:\n"
                    "   - Go to **https://cybercrime.gov.in** and click **'Report Crime Related to Women / Child'**.\n"
                    "   - You can choose to **Report Anonymously** without disclosing your identity publicly.\n"
                    "4. **Emergency Helplines**:\n"
                    "   - **Women Helpline: 1091**\n"
                    "   - **National Commission for Women (NCW) Cyber Cell: 7827170170**\n"
                    "   - **National Emergency: 112**\n"
                    "5. **Block and Report the Perpetrator** on the respective social media platform immediately."
                ),
                "quick_actions": [
                    "Save Screenshots and Evidence",
                    "Never Pay Blackmailers",
                    "Report Anonymously at cybercrime.gov.in",
                    "Call NCW (7827170170) or 1091"
                ]
            },
            "kn": {
                "reply": (
                    "### 🛡️ ಮಹಿಳಾ ಸೈಬರ್ ಸುರಕ್ಷತೆ ಹಾಗೂ ಕಿರುಕುಳ ರಕ್ಷಣಾ ಮಾರ್ಗದರ್ಶಿ\n\n"
                    "ಯಾರಾದರೂ ಬ್ಲಾಕ್‌ಮೇಲ್, ಫೋಟೋ ಮಾರ್ಫಿಂಗ್, ಸಾಮಾಜಿಕ ಜಾಲತಾಣದಲ್ಲಿ ಕಿರುಕುಳ ಅಥವಾ ಬೆದರಿಕೆ ಹಾಕುತ್ತಿದ್ದರೆ:\n\n"
                    "1. **ಸಾಕ್ಷ್ಯಗಳನ್ನು ಅಳಿಸಬೇಡಿ (Delete ಮಾಡಬೇಡಿ)**:\n"
                    "   - ಸಂದೇಶಗಳು, ಪ್ರೊಫೈಲ್ ಐಡಿ, ಫೋನ್ ನಂಬರ್ ಮತ್ತು ಲಿಂಕ್‌ಗಳ ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ತೆಗೆದಿಟ್ಟುಕೊಳ್ಳಿ.\n"
                    "2. **ಯಾವುದೇ ಕಾರಣಕ್ಕೂ ಹಣ ನೀಡಬೇಡಿ**:\n"
                    "   - ಬ್ಲಾಕ್‌ಮೇಲರ್‌ಗೆ ಹಣ ನೀಡಿದರೆ ಇನ್ನಷ್ಟು ಕಿರುಕುಳ ನೀಡುತ್ತಾರೆ; ಹಣ ನೀಡುವುದನ್ನು ಸಂಪೂರ್ಣ ನಿಲ್ಲಿಸಿ.\n"
                    "3. **ಗೌಪ್ಯವಾಗಿ ದೂರು ದಾಖಲಿಸಿ**:\n"
                    "   - **https://cybercrime.gov.in** ನಲ್ಲಿ **'ಮಹಿಳೆ ಮತ್ತು ಮಕ್ಕಳ ಅಪರಾಧ ವರದಿ'** ವಿಭಾಗದಲ್ಲಿ ನಿಮ್ಮ ಗುರುತನ್ನು ಗೌಪ್ಯವಾಗಿಟ್ಟು (Anonymously) ದೂರು ನೀಡಬಹುದು.\n"
                    "4. **ತುರ್ತು ಸಹಾಯವಾಣಿಗಳು**:\n"
                    "   - **ಮಹಿಳಾ ಸಹಾಯವಾಣಿ: 1091**\n"
                    "   - **ರಾಷ್ಟ್ರೀಯ ಮಹಿಳಾ ಆಯೋಗ (NCW): 7827170170**\n"
                    "   - **ರಾಷ್ಟ್ರೀಯ ತುರ್ತು ಸಂಖ್ಯೆ: 112**"
                ),
                "quick_actions": [
                    "ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ಸಾಕ್ಷ್ಯಗಳನ್ನು ಉಳಿಸಿ",
                    "ಬ್ಲಾಕ್‌ಮೇಲರ್‌ಗೆ ಹಣ ನೀಡಬೇಡಿ",
                    "cybercrime.gov.in ನಲ್ಲಿ ಗೌಪ್ಯ ದೂರು ನೀಡಿ",
                    "ಮಹಿಳಾ ಸಹಾಯವಾಣಿ 1091 ಗೆ ಕರೆ ಮಾಡಿ"
                ]
            },
            "hi": {
                "reply": (
                    "### 🛡️ महिला साइबर सुरक्षा और उत्पीड़न से बचाव निर्देश\n\n"
                    "यदि कोई आपको ब्लैकमेल कर रहा है, मॉर्फ्ड तस्वीरें वायरल करने की धमकी दे रहा है या ऑनलाइन परेशान कर रहा है:\n\n"
                    "1. **सबूत कभी डिलीट न करें**:\n"
                    "   - चैट, प्रोफाइल, नंबर और यूआरएल के पूरे स्क्रीनशॉट सुरक्षित रखें। यह कानूनी कार्रवाई के लिए आवश्यक है।\n"
                    "2. **ब्लैकमेलर को कभी पैसे न दें**:\n"
                    "   - पैसे देने से ब्लैकमेलिंग कभी खत्म नहीं होती, बल्कि उनकी मांग और बढ़ जाती है।\n"
                    "3. **पहचान छुपाकर (Anonymous) शिकायत दर्ज करें**:\n"
                    "   - **https://cybercrime.gov.in** पर जाएं और **'Report Crime Related to Women / Child'** चुनें।\n"
                    "   - यहां आप अपनी पहचान गुप्त रखकर भी आधिकारिक शिकायत दर्ज करा सकती हैं।\n"
                    "4. **आपातकालीन हेल्पलाइन**:\n"
                    "   - **महिला हेल्पलाइन: 1091**\n"
                    "   - **राष्ट्रीय महिला आयोग (NCW) साइबर सेल: 7827170170**\n"
                    "   - **राष्ट्रीय आपात नंबर: 112**"
                ),
                "quick_actions": [
                    "स्क्रीनशॉट और सबूत सुरक्षित रखें",
                    "ब्लैकमेलर को कभी पैसे न दें",
                    "cybercrime.gov.in पर गुप्त रिपोर्ट करें",
                    "महिला हेल्पलाइन 1091 या NCW 7827170170 पर कॉल करें"
                ]
            }
        },

        "identity_theft_aadhaar": {
            "en": {
                "reply": (
                    "### 🆔 Aadhaar, PAN & Identity Theft Protection\n\n"
                    "To safeguard your digital identity against unauthorized loans and fake SIM cards:\n\n"
                    "1. **Lock Your Aadhaar Biometrics**:\n"
                    "   - Download the official **mAadhaar app** or visit **https://myaadhaar.uidai.gov.in**.\n"
                    "   - Navigate to 'Lock/Unlock Biometrics' and enable biometric locking. This prevents unauthorized fingerprint/iris authentication.\n"
                    "2. **Check Unauthorized SIMs (DoT Sanchar Saathi)**:\n"
                    "   - Visit the government portal: **https://sancharsaathi.gov.in** (TAFCOP module).\n"
                    "   - Enter your mobile number to view all mobile connections issued using your Aadhaar.\n"
                    "   - Immediately disown and block any unknown numbers registered in your name.\n"
                    "3. **Monitor Your Credit Report**:\n"
                    "   - Check your CIBIL/Experian score periodically to detect fraudulent loans taken using your PAN card."
                ),
                "quick_actions": [
                    "Lock Aadhaar Biometrics on mAadhaar",
                    "Check SIMs on sancharsaathi.gov.in",
                    "Monitor Credit Score for Ghost Loans",
                    "Report Misuse at UIDAI 1947"
                ]
            },
            "kn": {
                "reply": (
                    "### 🆔 ಆಧಾರ್, ಪಾನ್ ಮತ್ತು ಗುರುತು ಕಳ್ಳತನ ರಕ್ಷಣೆ\n\n"
                    "ನಿಮ್ಮ ದಾಖಲೆಗಳನ್ನು ಬಳಸಿ ನಕಲಿ ಸಾಲ ಅಥವಾ ನಕಲಿ ಸಿಮ್ ಪಡೆಯುವುದನ್ನು ತಡೆಯಲು:\n\n"
                    "1. **ಆಧಾರ್ ಬಯೋಮೆಟ್ರಿಕ್ ಲಾಕ್ ಮಾಡಿ**:\n"
                    "   - ಅಧಿಕೃತ **mAadhaar ಆ್ಯಪ್** ಅಥವಾ **https://myaadhaar.uidai.gov.in** ಗೆ ಭೇಟಿ ನೀಡಿ.\n"
                    "   - 'Lock Biometrics' ಆಯ್ಕೆಮಾಡಿ ಲಾಕ್ ಮಾಡಿ. ಇದರಿಂದ ನಿಮ್ಮ ಬೆರಳಚ್ಚು ದುರುಪಯೋಗವಾಗುವುದಿಲ್ಲ.\n"
                    "2. **ನಿಮ್ಮ ಹೆಸರಿನಲ್ಲಿರುವ ಸಿಮ್ ಕಾರ್ಡ್‌ಗಳನ್ನು ಪರಿಶೀಲಿಸಿ (ಸಂಚಾರ ಸಾಥಿ)**:\n"
                    "   - ಭಾರತ ಸರ್ಕಾರದ **https://sancharsaathi.gov.in** (TAFCOP) ಪೋರ್ಟಲ್‌ಗೆ ಭೇಟಿ ನೀಡಿ.\n"
                    "   - ನಿಮ್ಮ ಆಧಾರ್ ಬಳಸಿ ಯಾರಾದರೂ ನಕಲಿ ಸಿಮ್ ಪಡೆದಿದ್ದರೆ ತಕ್ಷಣ ಬ್ಲಾಕ್ ಮಾಡಲು ವಿನಂತಿಸಿ.\n"
                    "3. **ಸಿಬಿಲ್ ಸ್ಕೋರ್ ಪರಿಶೀಲಿಸಿ**: ನಿಮ್ಮ ಪಾನ್ ಬಳಸಿ ಯಾರಾದರೂ ಸಾಲ ಪಡೆದಿದ್ದಾರೆಯೇ ಎಂದು ನಿಯಮಿತವಾಗಿ ಪರಿಶೀಲಿಸಿ."
                ),
                "quick_actions": [
                    "mAadhaar ನಲ್ಲಿ ಬಯೋಮೆಟ್ರಿಕ್ ಲಾಕ್ ಮಾಡಿ",
                    "sancharsaathi.gov.in ನಲ್ಲಿ ಸಿಮ್ ಪರಿಶೀಲಿಸಿ",
                    "ಸಿಬಿಲ್ ಸ್ಕೋರ್ ಪರಿಶೀಲಿಸಿ",
                    "ಆಧಾರ್ ಸಹಾಯವಾಣಿ 1947 ಗೆ ಕರೆ ಮಾಡಿ"
                ]
            },
            "hi": {
                "reply": (
                    "### 🆔 आधार, पैन और पहचान की चोरी से सुरक्षा उपाय\n\n"
                    "फर्जी लोन और आपके नाम पर अवैध सिम जारी होने से बचने के लिए:\n\n"
                    "1. **आधार बायोमेट्रिक तुरंत लॉक करें**:\n"
                    "   - आधिकारिक **mAadhaar ऐप** या **https://myaadhaar.uidai.gov.in** पर जाएं।\n"
                    "   - 'Lock/Unlock Biometrics' पर क्लिक करके बायोमेट्रिक लॉक चालू करें। इससे आपके फिंगरप्रिंट का कोई दुरुपयोग नहीं कर सकेगा।\n"
                    "2. **आपके नाम पर कितने सिम हैं? (संचार साथी पोर्टल)**:\n"
                    "   - भारत सरकार के पोर्टल **https://sancharsaathi.gov.in** (TAFCOP) पर जाएं।\n"
                    "   - अपना मोबाइल नंबर डालकर देखें कि आपके आधार से कौन-कौन से नंबर चल रहे हैं। जो नंबर आपका नहीं है, उसे तुरंत बंद करवाएं।\n"
                    "3. **सिबिल (CIBIL) रिपोर्ट जांचें**: समय-समय पर क्रेडिट स्कोर चेक करें ताकि आपके पैन पर कोई फर्जी लोन न चल रहा हो।"
                ),
                "quick_actions": [
                    "mAadhaar ऐप से बायोमेट्रिक लॉक करें",
                    "sancharsaathi.gov.in पर सिम चेक करें",
                    "फर्जी लोन के लिए सिबिल रिपोर्ट जांचें",
                    "आधार शिकायत के लिए 1947 डायल करें"
                ]
            }
        },

        "phishing_links": {
            "en": {
                "reply": (
                    "### 🔗 Phishing Link & Malicious Website Guide\n\n"
                    "1. **Look Closely at the Domain Name**:\n"
                    "   - Phishers use lookalike domains (e.g., `sbi-kyc-update.xyz`, `paytm-refund.top`).\n"
                    "   - Genuine Indian bank websites always end with `.com`, `.co.in`, or `.in` directly attached to their official brand.\n"
                    "2. **Dangerous Extensions**:\n"
                    "   - Never download or open files ending in `.apk`, `.exe`, or `.scr` received from SMS or WhatsApp.\n"
                    "3. **HTTPS Does NOT Mean Safe**:\n"
                    "   - Fraudulent websites also obtain free SSL certificates. HTTPS only encrypts the connection, it does not certify legitimacy.\n"
                    "4. **Use SURAKSHA AI Phishing URL Scanner**:\n"
                    "   - Paste the suspicious URL into our URL Scanner module before clicking!"
                ),
                "quick_actions": [
                    "Verify Domain Spelling Carefully",
                    "Never Install APKs from Chat",
                    "Scan Link with SURAKSHA URL Scanner",
                    "Report Malicious Link"
                ]
            },
            "kn": {
                "reply": (
                    "### 🔗 ಫಿಶಿಂಗ್ ಲಿಂಕ್ ಮತ್ತು ನಕಲಿ ವೆಬ್‌ಸೈಟ್‌ಗಳಿಂದ ಎಚ್ಚರ\n\n"
                    "1. **ವೆಬ್‌ಸೈಟ್ ಹೆಸರನ್ನು ಎಚ್ಚರಿಕೆಯಿಂದ ಗಮನಿಸಿ**:\n"
                    "   - ವಂಚಕರು ಅಸಲಿ ಬ್ಯಾಂಕ್‌ನಂತೆ ಕಾಣುವ ನಕಲಿ ಹೆಸರುಗಳನ್ನು (`sbi-update.xyz`, `phonepe-cashback.top`) ಬಳಸುತ್ತಾರೆ.\n"
                    "2. **ಎಪಿಕೆ (.apk) ಫೈಲ್‌ಗಳನ್ನು ಡೌನ್‌ಲೋಡ್ ಮಾಡಬೇಡಿ**:\n"
                    "   - ವಾಟ್ಸಾಪ್ ಅಥವಾ ಎಸ್‌ಎಂಎಸ್ ಮೂಲಕ ಬರುವ ಯಾವುದೇ ಆ್ಯಪ್ ಫೈಲ್ ಡೌನ್‌ಲೋಡ್ ಮಾಡಬೇಡಿ.\n"
                    "3. **ಸುರಕ್ಷಾ ಎಐ ಯುಆರ್‌ಎಲ್ ಸ್ಕ್ಯಾನರ್ ಬಳಸಿ**:\n"
                    "   - ಯಾವುದೇ ಲಿಂಕ್ ಕ್ಲಿಕ್ ಮಾಡುವ ಮುನ್ನ ನಮ್ಮ ಸುರಕ್ಷಾ URL Scanner ನಲ್ಲಿ ಪರಿಶೀಲಿಸಿ."
                ),
                "quick_actions": [
                    "ವೆಬ್‌ಸೈಟ್ ಕಾಗುಣಿತ ಎಚ್ಚರಿಕೆಯಿಂದ ನೋಡಿ",
                    "ಎಪಿಕೆ ಫೈಲ್ ಡೌನ್‌ಲೋಡ್ ಮಾಡಬೇಡಿ",
                    "ಸುರಕ್ಷಾ URL ಸ್ಕ್ಯಾನರ್ ಬಳಸಿ",
                    "ಸಂದೇಹಾಸ್ಪದ ಲಿಂಕ್ ವರದಿ ಮಾಡಿ"
                ]
            },
            "hi": {
                "reply": (
                    "### 🔗 फिशिंग लिंक और फर्जी वेबसाइटों की पहचान\n\n"
                    "1. **वेबसाइट के नाम (डोमेन) को ध्यान से देखें**:\n"
                    "   - धोखेबाज असली बैंक जैसा दिखने वाला फर्जी नाम बनाते हैं (जैसे `sbi-kyc.top`, `paytm-rewards.live`)।\n"
                    "2. **संदिग्ध एपीके (.apk) फाइल डाउनलोड न करें**:\n"
                    "   - मैसेज में आए किसी भी लिंक से ऐप डाउनलोड न करें। केवल गूगल प्ले स्टोर या एप्पल ऐप स्टोर का उपयोग करें।\n"
                    "3. **सुरक्षा एआई (SURAKSHA AI) यूआरएल स्कैनर का उपयोग करें**:\n"
                    "   - किसी भी लिंक पर क्लिक करने से पहले हमारे URL Scanner में पेस्ट करके उसकी सुरक्षा जांच लें।"
                ),
                "quick_actions": [
                    "वेबसाइट की स्पेलिंग ध्यान से देखें",
                    "अनजान लिंक से एपीके डाउनलोड न करें",
                    "सुरक्षा एआई URL स्कैनर से जांचें",
                    "संदिग्ध लिंक की शिकायत करें"
                ]
            }
        },

        "general_guidance": {
            "en": {
                "reply": (
                    "### 🛡️ SURAKSHA AI: Your Digital Safety Assistant\n\n"
                    "I am here to guide you against digital scams, UPI frauds, cyber harassment, and privacy threats.\n\n"
                    "**Essential Golden Rules for Digital Safety**:\n"
                    "1. **Never Share OTP or UPI PIN**: UPI PIN is only for paying, never for receiving money.\n"
                    "2. **Never Click Unknown Links or Install APKs**: Always use official apps and portals.\n"
                    "3. **No Agency Arrests People on Video Calls**: CBI, Police, and Courts do not conduct 'Digital Arrests'.\n"
                    "4. **Financial Fraud Helpline**: If money is deducted fraudulently, call **1930** immediately.\n\n"
                    "You can ask me specific questions in **English**, **ಕನ್ನಡ (Kannada)**, or **हिन्दी (Hindi)**."
                ),
                "quick_actions": [
                    "Ask About UPI Fraud Recovery",
                    "Ask About Fake KYC SMS",
                    "Ask About Digital Arrest Scam",
                    "Call Cyber Helpline 1930"
                ]
            },
            "kn": {
                "reply": (
                    "### 🛡️ ಸುರಕ್ಷಾ ಎಐ (SURAKSHA AI): ನಿಮ್ಮ ಡಿಜಿಟಲ್ ರಕ್ಷಣಾ ಸಹಾಯಕ\n\n"
                    "ಆನ್‌ಲೈನ್ ವಂಚನೆ, ಯುಪಿಐ ಫ್ರಾಡ್, ಸೈಬರ್ ಕಿರುಕುಳ ಹಾಗೂ ಡಿಜಿಟಲ್ ಬೆದರಿಕೆಗಳಿಂದ ರಕ್ಷಣೆ ಪಡೆಯಲು ನಾನು ಸದಾ ಸಿದ್ಧ.\n\n"
                    "**ಡಿಜಿಟಲ್ ಸುರಕ್ಷತೆಯ ಪ್ರಮುಖ ನಿಯಮಗಳು**:\n"
                    "1. **ಓಟಿಪಿ ಮತ್ತು ಯುಪಿಐ ಪಿನ್ ಎಂದಿಗೂ ಹಂಚಿಕೊಳ್ಳಬೇಡಿ**: ಪಿನ್ ಹಣ ಕಳುಹಿಸಲು ಮಾತ್ರ, ಪಡೆಯಲು ಅಲ್ಲ.\n"
                    "2. **ಅಪರಿಚಿತ ಲಿಂಕ್ ಅಥವಾ ಎಪಿಕೆ ಡೌನ್‌ಲೋಡ್ ಮಾಡಬೇಡಿ**: ಬ್ಯಾಂಕಿಂಗ್‌ಗಾಗಿ ಅಧಿಕೃತ ಆ್ಯಪ್ ಮಾತ್ರ ಬಳಸಿ.\n"
                    "3. **ವಿಡಿಯೋ ಕಾಲ್‌ನಲ್ಲಿ ಯಾರೂ ಬಂಧಿಸುವುದಿಲ್ಲ**: 'ಡಿಜಿಟಲ್ ಅರೆಸ್ಟ್' ಎಂಬುದು ಕೇವಲ ಸುಳ್ಳು ಬೆದರಿಕೆ.\n"
                    "4. **ಹಣಕಾಸು ವಂಚನೆಯಾದರೆ ತಕ್ಷಣ 1930 ಗೆ ಕರೆ ಮಾಡಿ**.\n\n"
                    "ನೀವು ನನಗೆ **ಕನ್ನಡ**, **English** ಅಥವಾ **हिन्दी** ನಲ್ಲಿ ಪ್ರಶ್ನೆ ಕೇಳಬಹುದು."
                ),
                "quick_actions": [
                    "ಯುಪಿಐ ವಂಚನೆ ಬಗ್ಗೆ ಕೇಳಿ",
                    "ಬ್ಯಾಂಕ್ ಕೆವೈಸಿ ಬಗ್ಗೆ ಕೇಳಿ",
                    "ಡಿಜಿಟಲ್ ಅರೆಸ್ಟ್ ಬಗ್ಗೆ ಕೇಳಿ",
                    "ಸಹಾಯವಾಣಿ 1930 ಗೆ ಕರೆ ಮಾಡಿ"
                ]
            },
            "hi": {
                "reply": (
                    "### 🛡️ सुरक्षा एआई (SURAKSHA AI): आपका डिजिटल सुरक्षा सहायक\n\n"
                    "मैं ऑनलाइन धोखाधड़ी, यूपीआई फ्रॉड, साइबर उत्पीड़न और डिजिटल खतरों से आपकी सुरक्षा के लिए उपस्थित हूं।\n\n"
                    "**डिजिटल सुरक्षा के बुनियादी नियम**:\n"
                    "1. **ओटीपी और यूपीआई पिन किसी को न बताएं**: पिन केवल पैसे भेजने के लिए होता है, पाने के लिए नहीं।\n"
                    "2. **अज्ञात लिंक या एपीके ऐप डाउनलोड न करें**: केवल आधिकारिक पोर्टल या प्ले स्टोर का उपयोग करें।\n"
                    "3. **वीडियो कॉल पर कोई गिरफ्तारी नहीं होती**: 'डिजिटल अरेस्ट' पूरी तरह से एक फर्जी धमकी है।\n"
                    "4. **पैसे कटने पर तुरंत 1930 पर कॉल करें**।\n\n"
                    "आप मुझसे **हिन्दी**, **English** या **ಕನ್ನಡ** में कोई भी प्रश्न पूछ सकते हैं।"
                ),
                "quick_actions": [
                    "यूपीआई फ्रॉड से बचाव के बारे में पूछें",
                    "बैंक केवाईसी फर्जीवाड़े के बारे में पूछें",
                    "डिजिटल अरेस्ट के बारे में पूछें",
                    "हेल्पलाइन 1930 पर कॉल करें"
                ]
            }
        }
    }

    def detect_sensitive_data(self, text: str) -> Optional[str]:
        """Checks if the user inadvertently pasted an OTP, PIN, password, or card number."""
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern.search(text):
                return (
                    "🚨 CRITICAL PRIVACY ALERT: Your message contains what looks like a sensitive OTP, PIN, or password! "
                    "SURAKSHA AI will NEVER ask you for credentials. Never share OTPs or PINs with anyone over chat, phone, or email!"
                )
        return None

    def detect_topic(self, text: str) -> str:
        """Determines the most appropriate cyber safety topic from user text."""
        lower_text = text.lower()
        for topic, patterns in self.TOPIC_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, lower_text, re.IGNORECASE):
                    return topic
        return "general_guidance"

    def check_ollama_availability(self) -> Tuple[bool, str]:
        """
        Non-blocking health probe for local Ollama endpoint.
        Returns (is_available, model_name).
        """
        try:
            req = urllib.request.Request(
                f"{settings.OLLAMA_BASE_URL}/api/tags",
                headers={"User-Agent": "SURAKSHA-AI-Client"}
            )
            with urllib.request.urlopen(req, timeout=1.2) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    models = data.get("models", [])
                    if models:
                        return True, models[0].get("name", "llama3.2")
                    return True, "llama3.2"
        except Exception:
            pass
        return False, "offline"

    def query_ollama(self, prompt: str, system_prompt: str, model: str = "llama3.2") -> Optional[str]:
        """Queries local Ollama instance with a system prompt and timeout."""
        try:
            payload = json.dumps({
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.9
                }
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "SURAKSHA-AI-Client"}
            )
            with urllib.request.urlopen(req, timeout=4.0) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    reply = data.get("response", "").strip()
                    if reply:
                        return reply
        except Exception:
            pass
        return None

    def get_assistant_reply(
        self,
        message: str,
        language: str = "en",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for generating a response.
        Applies privacy guardrail, detects topic, tries Ollama if available,
        and provides comprehensive deterministic trilingual fallback.
        """
        lang = language if language in ["en", "kn", "hi"] else "en"
        sensitive_warning = self.detect_sensitive_data(message)
        detected_topic = self.detect_topic(message)

        # Check if Ollama is available locally
        ollama_available, configured_model = self.check_ollama_availability()
        reply_text = None
        provider = "deterministic_fallback"

        if ollama_available:
            system_guardrail = (
                "You are SURAKSHA AI, a certified Indian public digital safety assistant. "
                "Help the user protect themselves from cyber fraud, scams, harassment, and digital threats. "
                "Provide accurate, actionable advice in " + (
                    "Kannada (ಕನ್ನಡ)" if lang == "kn" else ("Hindi (हिन्दी)" if lang == "hi" else "English")
                ) + ". Always mention the National Cyber Crime Helpline 1930 and cybercrime.gov.in. "
                "NEVER ask for passwords, OTPs, PINs, or bank details."
            )
            ollama_reply = self.query_ollama(message, system_guardrail, model=configured_model)
            if ollama_reply:
                reply_text = ollama_reply
                provider = "ollama"

        # If Ollama didn't respond or is offline, use the verified trilingual knowledge base
        if not reply_text:
            topic_dict = self.KNOWLEDGE_BASE.get(detected_topic, self.KNOWLEDGE_BASE["general_guidance"])
            lang_entry = topic_dict.get(lang, topic_dict.get("en", {}))
            reply_text = lang_entry.get("reply", "Stay vigilant and call 1930 if you suspect fraud.")
            quick_actions = lang_entry.get("quick_actions", [])
        else:
            quick_actions = [
                "Call Helpline 1930",
                "Report at cybercrime.gov.in",
                "Scan with URL Scanner",
                "Scan Screenshot"
            ]

        return {
            "reply": reply_text,
            "language": lang,
            "provider": provider,
            "detected_topic": detected_topic,
            "safety_warning": sensitive_warning,
            "quick_actions": quick_actions,
            "emergency_contacts": self.OFFICIAL_HELPLINES
        }

assistant_engine = AssistantEngine()

