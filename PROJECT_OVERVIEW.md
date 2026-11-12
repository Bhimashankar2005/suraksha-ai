# SURAKSHA AI – Project Overview

## 1. Mission Statement
**SURAKSHA AI** is conceived as a public-good, AI-enabled community cyber defense ecosystem. With the hyper-growth of digital payments (UPI), mobile internet, and rapid AI-generated content, ordinary citizens face unprecedented vulnerabilities from cybercriminals. SURAKSHA AI empowers people with instantaneous threat verification, explainable risk assessments, multilingual guidance, and tamper-evident evidence collection.

---

## 2. Core Pillars

### 2.1 Explainable Detection vs. Black-Box Claims
Unlike black-box systems that merely output an unverified confidence score, SURAKSHA AI uses hybrid intelligence:
1. **Rule-Based Heuristic Extraction**: Pinpoints specific triggers (e.g., suspicious bank domain lookalikes, urgent payment keywords, fake APK downloads, lottery references).
2. **Scikit-Learn Machine Learning**: Analyzes linguistic, n-gram, and token patterns trained on public scam datasets.
3. **Transparent Reporting**: Explains clearly *why* a message or URL is flagged (e.g., "Contains urgent threat of account suspension paired with an unofficial bit.ly link and an unverified phone number").

### 2.2 Community Threat Intelligence & Verification Lifecycle
Scam techniques evolve daily. SURAKSHA AI empowers the community to submit emerging scams, which go through a structured, audited human-in-the-loop review workflow:
- User submission generates a unique tracking code (`SUR-REP-XXXXXX`).
- Admin review panel allows moderators to verify, reject, flag as duplicate, or escalate threats.
- Public threat alerts are broadcast only after verification, protecting user privacy and preventing unverified slander.

### 2.3 Evidence Preservation for Cyber Crime Reporting
Many victims fail to receive justice because crucial evidence (screenshots, transaction IDs, chat logs) is lost or modified. SURAKSHA AI provides an Evidence Vault:
- Calculates SHA-256 cryptographic hashes upon upload to guarantee integrity.
- Exports structured incident reports formatted for submission to the National Cyber Crime Reporting Portal ([cybercrime.gov.in](https://cybercrime.gov.in)) and helpline **1930**.
- Features explicit disclaimers that the application aids documentation but does not replace official police reporting.

### 2.4 Inclusive & Vulnerable Demographic Support
- **Senior Citizen Mode**: High-contrast, large-font interface, clear voice guidance, plain-English/Kannada/Hindi explanations without confusing technical jargon.
- **Women's Safety Module**: Targeted recognition of cyber harassment, stalking patterns, impersonation, and non-consensual image sharing threats, connected to official support resources (National Commission for Women, 112, 1091).
- **Trilingual Accessibility**: Fully localized for English, Kannada (ಕನ್ನಡ), and Hindi (हिन्दी).

---

## 3. Strict Credit-Friendly Development Plan

| Constraint | Strategy | Benefit |
|---|---|---|
| Zero Cloud Subscriptions | Local developer environment (Windows local execution) | $0.00 Cost |
| Zero Paid LLM APIs | Local Scikit-learn pipelines + Local Ollama LLM integration + Offline rule trees | $0.00 Cost |
| Zero Paid DB Hosting | Local SQLite for instant start + local PostgreSQL configuration | $0.00 Cost |
| Zero Cloud File Storage | Local filesystem evidence vault with hash indexing | $0.00 Cost |
| Zero Voice API Bills | Client-side HTML5 Web Speech API | $0.00 Cost |
