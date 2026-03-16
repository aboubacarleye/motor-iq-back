from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.schemas import Vehicle, VehicleCreate
from app.models.models import Vehicle as VehicleModel, Driver as DriverModel
from app.routes.auth import get_current_user

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

@router.post("/", response_model=Vehicle)
def create_vehicle(
    vehicle: VehicleCreate,
    current_user: DriverModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new vehicle for the authenticated user"""
    db_vehicle = VehicleModel(
        driver_id=current_user.id,
        make=vehicle.make,
        model=vehicle.model,
        year=vehicle.year,
        license_plate=vehicle.license_plate
    )
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@router.get("/my/list")
def get_my_vehicles(
    current_user: DriverModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all vehicles for current user"""
    return db.query(VehicleModel).filter(VehicleModel.driver_id == current_user.id).all()

@router.get("/{vehicle_id}", response_model=Vehicle)
def get_vehicle(
    vehicle_id: int,
    current_user: DriverModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get vehicle details - user can only view their own vehicles"""
    db_vehicle = db.query(VehicleModel).filter(VehicleModel.id == vehicle_id).first()
    if not db_vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    if db_vehicle.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own vehicles"
        )
    return db_vehicle