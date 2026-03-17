from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.repositories.memory_db import db
from app.schemas.schemas import Claim, ClaimCreate, ClaimUpdate, TimelineStep


router = APIRouter(prefix="/claims", tags=["claims"])


@router.post("/", response_model=Claim)
def create_claim(payload: ClaimCreate) -> Claim:
    # Basic validation
    if not db.get_driver(payload.driver_id):
        raise HTTPException(status_code=404, detail="Driver not found")
    if not db.get_vehicle(payload.vehicle_id):
        raise HTTPException(status_code=404, detail="Vehicle not found")

    created = db.create_claim(
        driver_id=payload.driver_id,
        vehicle_id=payload.vehicle_id,
        description=payload.description,
        status=payload.status,
        date_created=payload.date_created,
    )
    return _to_claim_schema(created)


@router.get("/driver/{driver_id}", response_model=list[Claim])
def list_claims_for_driver(driver_id: int) -> list[Claim]:
    if not db.get_driver(driver_id):
        raise HTTPException(status_code=404, detail="Driver not found")
    claims = db.list_claims_for_driver(driver_id)
    return [_to_claim_schema(c) for c in claims]


@router.get("/{claim_id}", response_model=Claim)
def get_claim(claim_id: int) -> Claim:
    claim = db.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return _to_claim_schema(claim)


@router.patch("/{claim_id}", response_model=Claim)
def update_claim(claim_id: int, payload: ClaimUpdate) -> Claim:
    # Convert Pydantic TimelineStep to dataclass if provided
    timeline = None
    if payload.timeline is not None:
        timeline = [TimelineStep(label=step.label, completed=step.completed) for step in payload.timeline]

    updated = db.update_claim_status(
        claim_id=claim_id,
        status=payload.status,
        fraud_risk_score=payload.fraud_risk_score,
        timeline=timeline,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Claim not found")
    return _to_claim_schema(updated)


def _to_claim_schema(obj) -> Claim:
    return Claim(
        id=obj.id,
        claimId=obj.claim_id,
        description=obj.description,
        status=obj.status,
        date_created=obj.date_created,
        fraud_risk_score=obj.fraud_risk_score,
        vehicle_id=obj.vehicle_id,
        vehicleName=obj.vehicle_name,
        ai_analysis=obj.ai_analysis,
        timeline=[TimelineStep(label=s.label, completed=s.completed) for s in obj.timeline],
    )
