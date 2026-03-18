from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.schemas import Driver, DriverCreate
from app.models.models import Driver as DriverModel
from app.routes.auth import get_current_user, get_password_hash

router = APIRouter(prefix="/drivers", tags=["drivers"])

@router.get("/profile/me", response_model=Driver)
def get_my_profile(current_user: DriverModel = Depends(get_current_user)):
    """Get current driver's profile"""
    return current_user

@router.get("/{driver_id}", response_model=Driver)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """Get driver info by ID"""
    db_driver = db.query(DriverModel).filter(DriverModel.id == driver_id).first()
    if not db_driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return db_driver

@router.put("/{driver_id}", response_model=Driver)
def update_driver(
    driver_id: int,
    driver: DriverCreate,
    current_user: DriverModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update driver - user can only update their own profile"""
    if current_user.id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    db_driver = db.query(DriverModel).filter(DriverModel.id == driver_id).first()
    if not db_driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    # Update only safe fields
    db_driver.name = driver.name
    db_driver.phone = driver.phone
    if driver.password:
        db_driver.hashed_password = get_password_hash(driver.password)
    
    db.commit()
    db.refresh(db_driver)
    return db_driver