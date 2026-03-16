from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.schemas import Driver
from app.models.models import Driver as DriverModel

router = APIRouter(prefix="/drivers", tags=["drivers"])

@router.get("/{driver_id}", response_model=Driver)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    db_driver = db.query(DriverModel).filter(DriverModel.id == driver_id).first()
    if not db_driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return db_driver

@router.put("/{driver_id}", response_model=Driver)
def update_driver(driver_id: int, driver: Driver, db: Session = Depends(get_db)):
    db_driver = db.query(DriverModel).filter(DriverModel.id == driver_id).first()
    if not db_driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    for key, value in driver.dict().items():
        setattr(db_driver, key, value)
    db.commit()
    db.refresh(db_driver)
    return db_driver