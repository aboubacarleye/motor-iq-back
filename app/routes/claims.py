from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.schemas import Claim, ClaimCreate
from app.models.models import Claim as ClaimModel, Driver as DriverModel, Vehicle
from app.routes.auth import get_current_user
from app.ai.gemini_service import analyze_claim
from datetime import datetime

router = APIRouter(prefix="/claims", tags=["claims"])

@router.post("/", response_model=Claim)
def create_claim(
    claim: ClaimCreate,
    current_user: DriverModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a claim for the authenticated user"""
    # Verify the vehicle belongs to the current user
    vehicle = db.query(Vehicle).filter(Vehicle.id == claim.vehicle_id).first()
    if not vehicle or vehicle.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create claims for your own vehicles"
        )
    
    db_claim = ClaimModel(
        driver_id=current_user.id,
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

@router.get("/my/list", response_model=list[Claim])
def get_my_claims(
    current_user: DriverModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all claims for the current user"""
    return db.query(ClaimModel).filter(ClaimModel.driver_id == current_user.id).all()

@router.get("/{claim_id}", response_model=Claim)
def get_claim(
    claim_id: int,
    current_user: DriverModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get claim details - user can only view their own claims"""
    db_claim = db.query(ClaimModel).filter(ClaimModel.id == claim_id).first()
    if not db_claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    if db_claim.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own claims"
        )
    return db_claim

@router.get("/driver/{driver_id}", response_model=list[Claim])
def get_claims_by_driver(
    driver_id: int,
    current_user: DriverModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get claims for a specific driver - user can only view their own"""
    if current_user.id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own claims"
        )
    return db.query(ClaimModel).filter(ClaimModel.driver_id == driver_id).all()