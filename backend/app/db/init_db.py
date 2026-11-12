import logging
from sqlalchemy.orm import Session
from backend.app.core.database import engine, Base
from backend.app.models import (
    Role, User, Profile, Course, Lesson, Quiz, ModelRegistry
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    # 1. Create all registered tables
    logger.info("Creating database tables if not present...")
    Base.metadata.create_all(bind=engine)

    # 2. Seed Default Roles
    default_roles = [
        {"name": "USER", "description": "Standard citizen user with scan, report, and educational access"},
        {"name": "ADMIN", "description": "Administrator with moderation, verification, and audit access"},
        {"name": "COMMUNITY_MODERATOR", "description": "Community triage and verification officer"}
    ]

    for role_data in default_roles:
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing_role:
            role = Role(name=role_data["name"], description=role_data["description"])
            db.add(role)
            logger.info(f"Seeded role: {role_data['name']}")

    # 3. Seed Default Model Registry entries
    default_models = [
        {
            "model_name": "SURAKSHA_HEURISTIC_ENGINE",
            "version": "1.0.0",
            "model_type": "HEURISTIC_RULESET",
            "parameters": {"urgency_weight": 25, "kyc_weight": 35, "upi_weight": 30, "otp_weight": 40}
        },
        {
            "model_name": "SURAKSHA_SCAM_TFIDF_CLASSIFIER",
            "version": "1.0.0",
            "model_type": "SCIKIT_LEARN_TFIDF",
            "parameters": {"max_features": 5000, "ngram_range": [1, 2], "classifier": "MultinomialNB"}
        },
        {
            "model_name": "SURAKSHA_LOCAL_OLLAMA_AGENT",
            "version": "1.0.0",
            "model_type": "OLLAMA_LLM",
            "parameters": {"model": "llama3.2:latest", "fallback": "deterministic_multilingual"}
        }
    ]

    for model_data in default_models:
        existing_model = db.query(ModelRegistry).filter(ModelRegistry.model_name == model_data["model_name"]).first()
        if not existing_model:
            model_entry = ModelRegistry(
                model_name=model_data["model_name"],
                version=model_data["version"],
                model_type=model_data["model_type"],
                parameters=model_data["parameters"]
            )
            db.add(model_entry)
            logger.info(f"Seeded model registry: {model_data['model_name']}")

    # 4. Seed Foundational Cyber Safety Courses, Lessons, and Quizzes
    courses_manifest = [
        {
            "slug": "upi-digital-payment-safety",
            "title": "UPI & Digital Payment Protection",
            "description": "Learn how UPI scams operate, understand PIN safety rules, detect fake QR codes, and follow immediate recovery steps.",
            "target_audience": "GENERAL",
            "language": "en",
            "lessons": [
                {
                    "order_index": 1,
                    "title": "The Golden Rule of UPI: PIN is Only to Pay, Never to Receive",
                    "content": "### The Fundamental Law of UPI\n\nIn India's Unified Payments Interface (UPI) system, you **NEVER enter your UPI PIN to receive money**.\n\n#### How Scammers Trick You:\n1. **OLX / Marketplace Scams**: The buyer promises to send an advance payment.\n2. **The Request Trap**: Instead of sending money, they send a 'Collect Request' on Google Pay, PhonePe, or Paytm.\n3. **The Lie**: They claim: *'Scan this QR code and type your PIN to accept Rs 5,000 into your account.'*\n4. **The Reality**: The moment you enter your PIN, money is deducted from your bank account instantly.\n\n> **Key Takeaway**: Receiving money is 100% automatic. If an app asks for your 4-digit or 6-digit MPIN/UPI PIN, you are SENDING money!"
                },
                {
                    "order_index": 2,
                    "title": "Fake QR Codes and Payment Screenshot Deceptions",
                    "content": "### Beware of Fake Payment Proofs\n\nScammers use mobile applications like 'FakePay' or 'Paytm Spoof' to generate visual receipts that look genuine.\n\n#### Why Never to Trust Screenshots:\n- Scammers will display a green checkmark screen with a fake UTR number.\n- Always check your actual bank SMS or refresh your banking app balance before handing over goods or transferring funds.\n\n#### Golden Hour Action Plan:\nIf you accidentally sent money to a fraudster:\n1. Call **1930** (National Cyber Fraud Helpline) immediately.\n2. The Indian Cyber Crime Coordination Centre (I4C) will freeze the fraudster's account in the banking pipeline if alerted within 2-3 hours."
                }
            ],
            "quiz": {
                "title": "UPI Security Master Quiz",
                "passing_score": 70,
                "questions": [
                    {
                        "id": 1,
                        "question": "When do you need to enter your UPI PIN?",
                        "options": [
                            "Only when money is being deducted/sent from your account",
                            "Whenever you want to receive money from a buyer",
                            "To verify your bank account on WhatsApp",
                            "To claim a cashback reward"
                        ],
                        "correct_index": 0,
                        "explanation": "Entering a UPI PIN authorizes a withdrawal. You never need a PIN to receive incoming credits."
                    },
                    {
                        "id": 2,
                        "question": "A buyer on OLX sends a screenshot showing Rs 10,000 transferred with a UTR number, but your bank balance has not updated. What should you do?",
                        "options": [
                            "Ship the product immediately because the UTR is visible",
                            "Send back half the money as goodwill",
                            "Do not ship anything until the funds reflect directly in your official bank account",
                            "Enter your UPI PIN to claim the funds"
                        ],
                        "correct_index": 2,
                        "explanation": "Screenshots can be effortlessly faked with spoofing apps. Only verify incoming funds through your bank balance."
                    },
                    {
                        "id": 3,
                        "question": "What is the official Indian National Cyber Fraud Helpline to freeze stolen UPI funds during the golden hour?",
                        "options": [
                            "100",
                            "1930",
                            "139",
                            "1098"
                        ],
                        "correct_index": 1,
                        "explanation": "1930 is the national cyber financial fraud helpline operated by the Ministry of Home Affairs."
                    }
                ]
            }
        },
        {
            "slug": "phishing-kyc-fraud-prevention",
            "title": "Spotting Phishing, Fake KYC & Bank Suspension Scams",
            "description": "Identify fraudulent SMS/WhatsApp messages claiming bank accounts, PAN cards, or SIM cards are blocked.",
            "target_audience": "SENIORS",
            "language": "en",
            "lessons": [
                {
                    "order_index": 1,
                    "title": "Deconstructing Fake Bank KYC & Account Freeze Messages",
                    "content": "### The Anatomy of a Panic Message\n\nFraudulent messages create artificial panic to make you bypass rational thinking:\n\n*\"Dear Customer, your SBI account will be blocked today at 9:30 PM due to unupdated PAN. Click here: sbi-kyc-update.xyz to update.\"*\n\n#### Red Flags:\n1. **Sense of Immediate Urgency**: Demands action within 24 hours or tonight.\n2. **Lookalike Domains**: Uses unofficial domains (`.xyz`, `.top`, `.online`) instead of `onlinesbi.sbi`.\n3. **Personal Phone Numbers**: Sent from standard 10-digit mobile numbers rather than registered corporate sender headers (e.g., `VK-SBIINB`)."
                },
                {
                    "order_index": 2,
                    "title": "Dangerous APK Sideloads & Remote Access Trojans",
                    "content": "### What Happens When You Download an APK\n\nScammers often send an `.apk` file (such as `SBI_Rewards.apk` or `ElectricityBill.apk`) over WhatsApp.\n\n#### The Danger:\n- These APKs contain Remote Access Trojans (RATs) or SMS forwarders.\n- Once installed, the attacker can view your screen, read your incoming two-factor OTPs, and access your bank account without your knowledge.\n\n> **Safety Rule**: Never install Android APKs sent over WhatsApp or SMS. Only install applications from Google Play Store or Apple App Store."
                }
            ],
            "quiz": {
                "title": "Phishing & KYC Defense Quiz",
                "passing_score": 70,
                "questions": [
                    {
                        "id": 1,
                        "question": "Which of the following sender IDs indicates a suspicious, unofficial message?",
                        "options": [
                            "+91 98234 56789 (a regular 10-digit mobile number)",
                            "AX-HDFCBK",
                            "BZ-SBIINB",
                            "VM-ICICIB"
                        ],
                        "correct_index": 0,
                        "explanation": "Banks in India are legally mandated by TRAI to send official transactional messages via registered 6-character alpha headers, never from personal 10-digit numbers."
                    },
                    {
                        "id": 2,
                        "question": "A WhatsApp contact asks you to download 'ElectricityBill_Update.apk' to pay an overdue Rs 10 bill. What should you do?",
                        "options": [
                            "Install the APK immediately to avoid power cutoff",
                            "Forward it to your friends to verify",
                            "Never download or install the APK, block the sender, and pay via official electricity board portal",
                            "Install it and delete it after payment"
                        ],
                        "correct_index": 2,
                        "explanation": "APKs sent over messaging apps often contain malware and screen-mirroring trojans. Always use verified portals."
                    },
                    {
                        "id": 3,
                        "question": "What is the legitimate website for verifying and updating Indian Aadhaar details?",
                        "options": [
                            "aadhaar-kyc-update.xyz",
                            "myaadhaar.uidai.gov.in",
                            "uidai-verification.com",
                            "gov-aadhaar.in"
                        ],
                        "correct_index": 1,
                        "explanation": "myaadhaar.uidai.gov.in is the only official UIDAI government portal ending in .gov.in."
                    }
                ]
            }
        },
        {
            "slug": "women-cyber-safety-harassment",
            "title": "Women Cyber Safety & Anti-Harassment Defense",
            "description": "Protective protocols against cyberstalking, non-consensual image sharing, and blackmail.",
            "target_audience": "WOMEN",
            "language": "en",
            "lessons": [
                {
                    "order_index": 1,
                    "title": "Defending Against Morphing Blackmail & Sextortion",
                    "content": "### How Sextortion Schemes Work\n\nExtortionists use AI face-swapping or cropped video recordings to threaten victims with sharing morphed images with friends, family, or employers.\n\n#### Crucial Rules:\n1. **NEVER Pay Money**: Paying extortion money guarantees repeated demands. Blackmailers will never delete the files after payment.\n2. **Cut Off Communication**: Do not plead, argue, or negotiate with the extortionist.\n3. **Preserve Evidence**: Take clear screenshots showing the user handle, phone number, messages, and timestamps."
                },
                {
                    "order_index": 2,
                    "title": "Legal Protections & Anonymous Incident Reporting",
                    "content": "### Your Legal Rights in India\n\nUnder Section 66E and 67A of the Information Technology Act and the Bharatiya Nyaya Sanhita (BNS):\n- Morphing, non-consensual image creation, and cyberstalking are non-bailable criminal offenses.\n\n#### Official Emergency Helplines:\n- **1091**: 24x7 Women Police Helpline\n- **112**: All-India Police Emergency\n- **7827170170**: National Commission for Women (NCW)\n- **cybercrime.gov.in**: Dedicated confidential section for 'Report Cyber Crime Against Women and Children' without public disclosure."
                }
            ],
            "quiz": {
                "title": "Women Cyber Defense & Legal Rights Quiz",
                "passing_score": 70,
                "questions": [
                    {
                        "id": 1,
                        "question": "If an online contact threatens to release morphed photos unless you pay Rs 20,000, what is the best first step?",
                        "options": [
                            "Pay the money quickly so they delete the files",
                            "Do NOT pay, preserve screenshots with handles/timestamps, and contact police helpline 1091",
                            "Delete your entire phone to destroy traces",
                            "Send them another photo to prove innocence"
                        ],
                        "correct_index": 1,
                        "explanation": "Paying money never solves extortion; it encourages escalated demands. Document evidence and seek legal support."
                    },
                    {
                        "id": 2,
                        "question": "What is the dedicated 24x7 Women Helpline number across India?",
                        "options": [
                            "1091",
                            "100",
                            "1098",
                            "1947"
                        ],
                        "correct_index": 0,
                        "explanation": "1091 is the dedicated 24x7 emergency helpline for women in distress."
                    },
                    {
                        "id": 3,
                        "question": "Does the Indian National Cyber Crime Reporting Portal allow confidential reporting of crimes against women?",
                        "options": [
                            "No, all complaints are published publicly",
                            "Yes, it has a dedicated section for confidential reporting of crimes against women and children",
                            "Only if filed through a lawyer",
                            "Only for financial crimes"
                        ],
                        "correct_index": 1,
                        "explanation": "cybercrime.gov.in provides specialized confidential reporting for crimes against women and children."
                    }
                ]
            }
        },
        {
            "slug": "senior-fraud-pension-safety",
            "title": "Senior Citizen Fraud Protection & Pension Security",
            "description": "Essential safety guidance on pension life certificate renewal, utility bill scams, and digital arrest threats.",
            "target_audience": "SENIORS",
            "language": "en",
            "lessons": [
                {
                    "order_index": 1,
                    "title": "Protecting Your Pension & Digital Life Certificate (Jeevan Pramaan)",
                    "content": "### The Jeevan Pramaan Scam\n\nScammers call senior pensioners claiming their monthly pension will stop immediately unless they download a biometric APK or share OTP.\n\n#### The Truth:\n- Banks and the Pension Disbursing Authority **never call** to ask for your ATM card number, PIN, or OTP.\n- Official Digital Life Certificates can be renewed securely at any local Post Office, CSC center, or bank branch using the official Jeevan Pramaan app from `jeevanpramaan.gov.in`."
                },
                {
                    "order_index": 2,
                    "title": "Exposing the 'Digital Arrest' Video Call Scam",
                    "content": "### What is 'Digital Arrest'?\n\nFraudsters dress in police uniforms over WhatsApp or Skype video calls and claim your Aadhaar was found in a money laundering or narcotics courier in Mumbai or Delhi.\n\n#### Reality Check:\n- There is **NO SUCH THING as 'Digital Arrest'** in Indian law.\n- Real police and CBI officers **NEVER** conduct interrogations or demand money over Skype, WhatsApp, or Telegram video calls.\n- Immediately hang up, dial **1930** or visit your local police station."
                }
            ],
            "quiz": {
                "title": "Senior Citizen Cyber Safety Quiz",
                "passing_score": 70,
                "questions": [
                    {
                        "id": 1,
                        "question": "A person calling on WhatsApp claims to be a Police Officer and says you are placed under 'Digital Arrest' until you transfer funds for clearance. What should you do?",
                        "options": [
                            "Transfer the funds to prove you are innocent",
                            "Indian law has no 'Digital Arrest'. Hang up immediately and dial 1930 or 112",
                            "Stay on the video call all night",
                            "Send them your pension book"
                        ],
                        "correct_index": 1,
                        "explanation": "'Digital Arrest' is a complete psychological scam. Police never arrest or interrogate citizens over WhatsApp video calls."
                    },
                    {
                        "id": 2,
                        "question": "Can your bank or pension authority ever ask for your ATM PIN or NetBanking password over phone?",
                        "options": [
                            "Yes, during annual verification",
                            "Never. Bank officials will NEVER ask for your PIN, OTP, or passwords",
                            "Only if calling from the main branch",
                            "Yes, if the pension is pending"
                        ],
                        "correct_index": 1,
                        "explanation": "Under Reserve Bank of India (RBI) regulations, bank officials are strictly forbidden from requesting PINs or passwords."
                    },
                    {
                        "id": 3,
                        "question": "Where can a senior citizen safely submit their Digital Life Certificate (Jeevan Pramaan)?",
                        "options": [
                            "Via any random APK link received in an SMS",
                            "At their nearest India Post Payments Bank postman, designated bank branch, or official CSC center",
                            "By sharing Aadhaar photo with unknown WhatsApp numbers",
                            "Over a phone call"
                        ],
                        "correct_index": 1,
                        "explanation": "Post offices and official bank branches provide authorized, biometric-assisted Jeevan Pramaan verification."
                    }
                ]
            }
        },
        {
            "slug": "passwords-2fa-account-security",
            "title": "Passwords, 2FA & Account Takeover Defense",
            "description": "Master passphrase creation, hardware keys, authenticator apps, and SIM swap protection.",
            "target_audience": "GENERAL",
            "language": "en",
            "lessons": [
                {
                    "order_index": 1,
                    "title": "Passphrases vs Passwords: Why Complexity Rules Fail",
                    "content": "### Stop Using P@ssw0rd123!\n\nShort complex passwords like `Tr0ub4dor&3` are hard for humans to remember but easy for computers to crack via dictionary attacks.\n\n#### The Passphrase Method:\n- Use 4 to 5 random, unrelated words: `correct-horse-battery-staple` or `coffee-monsoon-karnataka-train`.\n- Passphrases are over 25 characters long, providing massive entropy while remaining easy to remember."
                },
                {
                    "order_index": 2,
                    "title": "Why Authenticator Apps Beat SMS OTPs",
                    "content": "### The Flaw in SMS Two-Factor Authentication\n\nSMS OTPs are vulnerable to **SIM Swap Fraud** and telecom interception.\n\n#### Upgrade Your Security:\n1. Switch to an Authenticator App (Google Authenticator, Aegis, or Microsoft Authenticator).\n2. Authenticator app codes are generated locally on your device without transmitting over cellular networks."
                }
            ],
            "quiz": {
                "title": "Authentication & Password Security Quiz",
                "passing_score": 70,
                "questions": [
                    {
                        "id": 1,
                        "question": "Which of the following is the most secure password according to modern NIST guidelines?",
                        "options": [
                            "Password123!",
                            "mango-tiger-monsoon-bicycle",
                            "abcABC123$",
                            "Admin@2024"
                        ],
                        "correct_index": 1,
                        "explanation": "Long passphrases composed of multiple random words provide exponential entropy and resist brute-force attacks."
                    },
                    {
                        "id": 2,
                        "question": "Why is an Authenticator app safer than an SMS OTP for two-factor authentication?",
                        "options": [
                            "It uses less battery",
                            "It cannot be intercepted by SIM swap fraud or telecom snooping",
                            "It only works with Google accounts",
                            "It requires a credit card"
                        ],
                        "correct_index": 1,
                        "explanation": "Time-based One-Time Passwords (TOTP) generated inside authenticator apps do not travel over unencrypted cellular channels."
                    },
                    {
                        "id": 3,
                        "question": "What is the primary indicator of a SIM Swap attack?",
                        "options": [
                            "Your phone battery drains faster",
                            "Your phone suddenly loses cellular network service completely while people around you have full signal",
                            "Your phone screen brightness dims",
                            "You receive too many emails"
                        ],
                        "correct_index": 1,
                        "explanation": "When an attacker clones your SIM, your physical SIM is deactivated and immediately loses all network connectivity."
                    }
                ]
            }
        },
        {
            "slug": "deepfakes-synthetic-media-awareness",
            "title": "Deepfakes, Synthetic Media & Identity Theft",
            "description": "Understand how AI clones audio and video, recognize synthetic artifacts, and protect your digital persona.",
            "target_audience": "STUDENTS",
            "language": "en",
            "lessons": [
                {
                    "order_index": 1,
                    "title": "How Generative AI Generates Synthetic Faces & Clones Voices",
                    "content": "### The Rise of Generative Deepfakes\n\nModern diffusion models and neural voice cloners require as little as 3 seconds of reference audio to mimic someone's voice.\n\n#### Common Vectors in India:\n1. **CEO / Boss Fraud**: Audio messages demanding emergency bank transfers.\n2. **Relative Emergency Scams**: Cloning a grandchild or son's voice claiming they are stranded or arrested."
                },
                {
                    "order_index": 2,
                    "title": "Forensic Indicators & How to Verify a Suspicious Call",
                    "content": "### How to Spot Synthetic Video & Audio\n\n1. **Visual Cues**: Blurring around the hairline, unnatural blinking (too frequent or never), irregular earlobe symmetry, and teeth merging together.\n2. **Audio Cues**: Lack of natural breathing pauses, robotic flat intonation, and absence of ambient room noise.\n\n#### The Family Safe-Word Protocol:\nEstablish a private code-word with your immediate family members. If you ever receive a frantic call asking for money, ask for the code-word before transferring a single rupee."
                }
            ],
            "quiz": {
                "title": "Deepfake Detection & Media Literacy Quiz",
                "passing_score": 70,
                "questions": [
                    {
                        "id": 1,
                        "question": "What is an effective non-technical defense against voice-cloned emergency family scams?",
                        "options": [
                            "Immediately wire the requested money",
                            "Ask the caller for a pre-agreed family secret code-word or hang up and call their known number directly",
                            "Argue with the caller",
                            "Send them a photo of your ID"
                        ],
                        "correct_index": 1,
                        "explanation": "A private family safe-word or calling the relative back on their known regular phone number instantly defeats voice-cloning tricks."
                    },
                    {
                        "id": 2,
                        "question": "Which of the following is a common visual artifact in first-generation face-swapped deepfake videos?",
                        "options": [
                            "Unnatural edge blurring around the chin and hairline during head turns",
                            "Crystal clear 8K video resolution",
                            "Black and white colors",
                            "Extremely high audio volume"
                        ],
                        "correct_index": 0,
                        "explanation": "Diffusion and GAN warping artifacts commonly manifest as boundary blending anomalies around the chin, neck, and hairline."
                    },
                    {
                        "id": 3,
                        "question": "What does Error Level Analysis (ELA) measure in a digital photograph?",
                        "options": [
                            "The number of faces in the picture",
                            "Compression differences and error variance across image regions to identify spliced elements",
                            "The camera manufacturer price",
                            "The download speed of the file"
                        ],
                        "correct_index": 1,
                        "explanation": "ELA highlights non-uniform JPEG recompression levels, exposing spliced or pasted image regions."
                    }
                ]
            }
        }
    ]

    for item in courses_manifest:
        course = db.query(Course).filter(Course.slug == item["slug"]).first()
        if not course:
            course = Course(
                slug=item["slug"],
                title=item["title"],
                description=item["description"],
                target_audience=item["target_audience"],
                language=item["language"]
            )
            db.add(course)
            db.flush()
            logger.info(f"Seeded course: {item['slug']}")

        # Seed Lessons if not present
        existing_lessons = db.query(Lesson).filter(Lesson.course_id == course.id).all()
        if not existing_lessons and "lessons" in item:
            for l_data in item["lessons"]:
                lesson = Lesson(
                    course_id=course.id,
                    order_index=l_data["order_index"],
                    title=l_data["title"],
                    content=l_data["content"]
                )
                db.add(lesson)
            logger.info(f"Seeded {len(item['lessons'])} lessons for {item['slug']}")

        # Seed Quiz if not present
        existing_quiz = db.query(Quiz).filter(Quiz.course_id == course.id).first()
        if not existing_quiz and "quiz" in item:
            q_data = item["quiz"]
            quiz = Quiz(
                course_id=course.id,
                title=q_data["title"],
                passing_score=q_data["passing_score"],
                questions_data=q_data["questions"]
            )
            db.add(quiz)
            logger.info(f"Seeded quiz for {item['slug']}")

    db.commit()
    logger.info("Database initialization completed successfully.")

if __name__ == "__main__":
    from backend.app.core.database import SessionLocal
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()

