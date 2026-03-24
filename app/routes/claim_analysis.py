"""Claim analysis endpoint — the entry point for the fraud-detection pipeline.

POST /v1/claims/analyze   → run full analysis on uploaded evidence
GET  /v1/claims/{id}/analysis → retrieve a previous analysis result
"""

import json
import os
from datetime import datetime
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import (
    AnalysisLog,
    Claim as ClaimModel,
    ClaimEvidence,
    Driver as DriverModel,
    InsurancePolicy,
)
from app.routes.auth import get_current_user
from app.schemas.schemas import AnalysisFlag, AnalysisResponse
from app.services.claim_analyzer import analyze
from app.utils.hashing import sha256_file
from app.workers.document_worker import process_report
from app.workers.image_worker import process_images

router = APIRouter(prefix="/v1/claims", tags=["claim-analysis"])

# ── Config ──────────────────────────────────────────────────────────────
UPLOAD_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
ALLOWED_REPORT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_IMAGES = 10
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB per file


# ── Helpers ─────────────────────────────────────────────────────────────

def _save_file(claim_id: int, filename: str, data: bytes) -> str:
    """Persist a file to local storage (simulates S3) and return its path."""
    claim_dir = os.path.join(UPLOAD_ROOT, str(claim_id))
    os.makedirs(claim_dir, exist_ok=True)
    filepath = os.path.join(claim_dir, filename)
    with open(filepath, "wb") as f:
        f.write(data)
    return filepath


# ── POST /v1/claims/analyze ────────────────────────────────────────────

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_claim_endpoint(
    policy_number: str = Form(...),
    vehicle_id: int = Form(...),
    claim_images: List[UploadFile] = File(...),
    police_report: UploadFile = File(...),
    description: str = Form(""),
    current_user: DriverModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    """Accept evidence files, run the fraud-detection pipeline, return analysis."""

    # ── 1. Validate policy ──────────────────────────────────────────────
    policy = (
        db.query(InsurancePolicy)
        .filter(InsurancePolicy.policy_number == policy_number)
        .first()
    )
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy '{policy_number}' not found.",
        )
    if policy.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This policy does not belong to you.",
        )

    # ── 2. Validate files ───────────────────────────────────────────────
    if not claim_images or len(claim_images) < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one claim image is required.",
        )
    if len(claim_images) > MAX_IMAGES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Maximum {MAX_IMAGES} images allowed.",
        )

    for img in claim_images:
        if img.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Invalid image type '{img.content_type}' for '{img.filename}'. "
                    f"Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}."
                ),
            )

    if police_report.content_type not in ALLOWED_REPORT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid report type '{police_report.content_type}'. "
                f"Allowed: {', '.join(ALLOWED_REPORT_TYPES)}."
            ),
        )

    # ── 3. Create claim record ──────────────────────────────────────────
    db_claim = ClaimModel(
        driver_id=current_user.id,
        vehicle_id=vehicle_id,
        description=description,
        status="analyzing",
        date_created=datetime.utcnow(),
    )
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)

    # ── 4. Read files, store locally, save evidence records ─────────────
    image_data_list: List[tuple] = []
    for img_file in claim_images:
        data = await img_file.read()
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"File '{img_file.filename}' exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit.",
            )
        path = _save_file(db_claim.id, img_file.filename, data)
        file_hash = sha256_file(data)
        evidence = ClaimEvidence(
            claim_id=db_claim.id,
            type="photo",
            url=path,
            file_hash=file_hash,
        )
        db.add(evidence)
        image_data_list.append((img_file.filename, data))

    report_data_bytes = await police_report.read()
    if len(report_data_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Police report exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit.",
        )
    report_path = _save_file(db_claim.id, police_report.filename, report_data_bytes)
    report_hash = sha256_file(report_data_bytes)
    report_evidence = ClaimEvidence(
        claim_id=db_claim.id,
        type="document",
        url=report_path,
        file_hash=report_hash,
    )
    db.add(report_evidence)
    db.commit()

    # ── 5. Run image worker ─────────────────────────────────────────────
    image_results = process_images(image_data_list)

    # Store EXIF metadata back on evidence records
    evidences = (
        db.query(ClaimEvidence)
        .filter(
            ClaimEvidence.claim_id == db_claim.id,
            ClaimEvidence.type == "photo",
        )
        .all()
    )
    for ev, img_res in zip(evidences, image_results):
        ev.exif_metadata = json.dumps(img_res["exif"], default=str)
    db.commit()

    # ── 6. Run document worker ──────────────────────────────────────────
    report_result = process_report(report_data_bytes, police_report.filename)

    # ── 7. Run correlation engine ───────────────────────────────────────
    analysis = analyze(image_results, report_result, db_claim.id)

    # ── 8. Update claim with results ────────────────────────────────────
    db_claim.fraud_risk_score = analysis.risk_score
    db_claim.ai_analysis = analysis.explanation
    db_claim.status = analysis.status
    db.commit()

    # ── 9. Save analysis log ────────────────────────────────────────────
    log = AnalysisLog(
        claim_id=db_claim.id,
        risk_score=analysis.risk_score,
        status=analysis.status,
        flags=json.dumps([f.model_dump() for f in analysis.flags]),
        explanation=analysis.explanation,
        raw_results=json.dumps(
            {"images": image_results, "report": report_result},
            default=str,
        ),
        created_at=datetime.utcnow(),
    )
    db.add(log)
    db.commit()

    # ── 10. Return response ─────────────────────────────────────────────
    return analysis


# ── GET /v1/claims/{claim_id}/analysis ─────────────────────────────────

@router.get("/{claim_id}/analysis", response_model=AnalysisResponse)
def get_analysis(
    claim_id: int,
    current_user: DriverModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    """Retrieve the latest analysis result for a claim."""
    claim = db.query(ClaimModel).filter(ClaimModel.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")
    if claim.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own claim analyses.",
        )

    log = (
        db.query(AnalysisLog)
        .filter(AnalysisLog.claim_id == claim_id)
        .order_by(AnalysisLog.created_at.desc())
        .first()
    )
    if not log:
        raise HTTPException(
            status_code=404,
            detail="No analysis found for this claim.",
        )

    flags = [AnalysisFlag(**f) for f in json.loads(log.flags)]
    return AnalysisResponse(
        claim_id=claim_id,
        risk_score=log.risk_score,
        status=log.status,
        flags=flags,
        explanation=log.explanation,
    )
