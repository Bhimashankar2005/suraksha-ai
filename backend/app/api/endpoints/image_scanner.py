from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.image_scan import (
    ImageScanResponse, ImageHistoryItem, ConvertImageToReportRequest
)
from backend.app.schemas.scam import ConvertToReportResponse
from backend.app.services.image_service import (
    process_image_upload_and_scan, get_user_image_history, convert_image_scan_to_report
)
from backend.app.api.deps import get_current_user, get_current_user_optional

router = APIRouter()

@router.post("/scan", response_model=ImageScanResponse, status_code=status.HTTP_200_OK)
async def scan_screenshot_image(
    file: UploadFile = File(...),
    ocr_text_override: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Upload and analyze a suspicious screenshot (JPG, PNG, WEBP).
    Performs cryptographic SHA-256 hashing, OCR extraction, fake payment receipt detection,
    and returns transparent safety recommendations.
    """
    user_id = current_user.id if current_user else None
    file_bytes = await file.read()

    try:
        return process_image_upload_and_scan(
            file_bytes=file_bytes,
            file_name=file.filename or "uploaded_image.png",
            user_id=user_id,
            ocr_override=ocr_text_override,
            db=db
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image processing failed: {str(e)}"
        )

@router.get("/history", response_model=List[ImageHistoryItem])
def get_user_image_history_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve historical screenshot and image scans for the authenticated user."""
    return get_user_image_history(user_id=current_user.id, db=db)

@router.post("/report", response_model=ConvertToReportResponse, status_code=status.HTTP_201_CREATED)
def report_image_scam_to_community(
    payload: ConvertImageToReportRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Escalate a flagged scam screenshot directly into the community threat intelligence queue."""
    user_id = current_user.id if current_user else None
    return convert_image_scan_to_report(
        user_id=user_id,
        scan_id=payload.scan_id,
        target_value=payload.target_value,
        custom_description=payload.description,
        region=payload.region,
        db=db
    )

