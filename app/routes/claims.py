from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.schemas import Claim, ClaimCreate
from app.models.models import Claim as ClaimModel
from app.ai.gemini_service import analyze_claim
from datetime import datetime

router = APIRouter(prefix="/claims", tags=["claims"])

@router.post("/", response_model=Claim)
def create_claim(claim: ClaimCreate, db: Session = Depends(get_db)):
    db_claim = ClaimModel(
        driver_id=claim.driver_id,
        vehicle_id=claim.vehicle_id,
        description=claim.description,
        location_lat=claim.location_lat,
        location_lng=claim.location_lng,
        date_created=datetime.utcnow()
    )
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
    # AI analysis
    analysis = analyze_claim({
        "description": claim.description,
        "location": f"{claim.location_lat}, {claim.location_lng}"
    })
    db_claim.fraud_risk_score = analysis["fraud_risk_score"]
    db_claim.ai_analysis = str(analysis)
    db.commit()
    return db_claim

@router.get("/{claim_id}", response_model=Claim)
def get_claim(claim_id: int, db: Session = Depends(get_db)):
    db_claim = db.query(ClaimModel).filter(ClaimModel.id == claim_id).first()
    if not db_claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return db_claim

@router.get("/driver/{driver_id}", response_model=list[Claim])
def get_claims_by_driver(driver_id: int, db: Session = Depends(get_db)):
    return db.query(ClaimModel).filter(ClaimModel.driver_id == driver_id).all()