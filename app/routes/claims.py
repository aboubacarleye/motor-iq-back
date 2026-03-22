from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.schemas import Claim, ClaimCreate
from app.models.models import Claim as ClaimModel, Driver as DriverModel, Vehicle
from app.routes.auth import get_current_user
from app.ai.gemini_service import analyze_claim
from app.services.claim_analysis import analyze_claim_service
from datetime import datetime

router = APIRouter(prefix="/claims", tags=["claims"])


# Route pour analyser une claim avec Gemini
from fastapi import Body
from pydantic import BaseModel, Field

class ClaimAnalysisResult(BaseModel):
    fraud_risk_score: float = Field(..., description="Score de risque de fraude entre 0 (aucun risque) et 1 (fraude certaine)")
    explanation: str = Field(..., description="Explication claire du score")
    incoherences: list[dict] = Field(..., description="Liste des incohérences détectées (champ, problème, suggestion)")
    recommendation: str = Field(..., description="Action recommandée (ex: 'Investigate', 'Approve', 'Reject')")

@router.post(
    "/{claim_id}/analyze",
    response_model=ClaimAnalysisResult,
    summary="Analyse une claim avec Gemini AI",
    description="Lance l'analyse AI sur une claim existante et retourne un score, une explication, les incohérences et une recommandation."
)
def analyze_claim_route(
    claim_id: int,
    current_user: DriverModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyse une claim pour fraude via Gemini AI.
    Retourne un score, une explication, les incohérences et une recommandation structurée.
    """
    db_claim = db.query(ClaimModel).filter(ClaimModel.id == claim_id).first()
    if not db_claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if db_claim.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only analyze your own claims"
        )
    result = analyze_claim_service(claim_id, db)
    if not result:
        raise HTTPException(status_code=500, detail="Analysis failed")
    # result is a dict with fraud_risk_score, explanation, incoherences, recommendation
    return result

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
        gps_latitude=claim.gps_latitude,
        gps_longitude=claim.gps_longitude,
        date_of_accident=claim.date_of_accident,
        audio_url=claim.audio_url,
        image_url=claim.image_url,
        status=claim.status,
    )
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
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