from fastapi import APIRouter
from backend.app.api.endpoints import (
    health, auth, dashboard, scam, url_scanner, image_scanner, chat,
    community_reports, evidence, privacy, demographics, deepfake, education,
    notifications, admin_management
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(scam.router, prefix="/scam", tags=["Scam Message Detection"])
api_router.include_router(url_scanner.router, prefix="/url", tags=["Phishing URL Scanner"])
api_router.include_router(image_scanner.router, prefix="/image", tags=["Screenshot & Image Scanner"])
api_router.include_router(chat.router, prefix="/chat", tags=["AI Cyber Assistant"])
api_router.include_router(community_reports.router, prefix="/reports", tags=["Community Threat Intelligence"])
api_router.include_router(evidence.router, prefix="/evidence", tags=["Cybercrime Evidence Management"])
api_router.include_router(privacy.router, prefix="/privacy", tags=["Personal Data & Privacy Protection"])
api_router.include_router(demographics.router, prefix="/demographics", tags=["Demographic Safety: Women & Seniors"])
api_router.include_router(deepfake.router, prefix="/deepfake", tags=["Deepfake & Media Authenticity"])
api_router.include_router(education.router, prefix="/education", tags=["Cyber Awareness & Education"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["In-App Notifications"])
api_router.include_router(admin_management.router, prefix="/admin", tags=["Admin Security & Monitoring"])
