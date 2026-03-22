from app.ai.gemini_service import analyze_claim
from app.models.models import Claim as ClaimModel
from sqlalchemy.orm import Session

def analyze_claim_service(claim_id: int, db: Session):
    """
    Service to analyze a claim for fraud using Gemini AI
    """
    db_claim = db.query(ClaimModel).filter(ClaimModel.id == claim_id).first()
    if not db_claim:
        return None
    claim_data = {
        "description": db_claim.description,
        "gps_latitude": db_claim.gps_latitude,
        "gps_longitude": db_claim.gps_longitude,
        "vehicle_id": db_claim.vehicle_id,
        "driver_id": db_claim.driver_id,
        # "date_created": str(db_claim.date_created)  # Remove if not present
    }
    analysis = analyze_claim(claim_data)
    db_claim.fraud_risk_score = analysis["fraud_risk_score"]
    db_claim.ai_analysis = str(analysis)
    db.commit()
    db.refresh(db_claim)
    return {
        "fraud_risk_score": db_claim.fraud_risk_score,
        "ai_analysis": db_claim.ai_analysis
    }
