from fastapi import APIRouter, HTTPException

from app.repositories.memory_db import db
from app.schemas.schemas import Driver, DriverCreate


router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("/{driver_id}", response_model=Driver)
def get_driver(driver_id: int) -> Driver:
    driver = db.get_driver(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return Driver.model_validate(driver.__dict__)


@router.put("/{driver_id}", response_model=Driver)
def update_driver(driver_id: int, payload: DriverCreate) -> Driver:
    updated = db.update_driver(
        driver_id=driver_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Driver not found")
    return Driver.model_validate(updated.__dict__)


@router.get("/{driver_id}/vehicles")
def list_driver_vehicles(driver_id: int):
    if not db.get_driver(driver_id):
        raise HTTPException(status_code=404, detail="Driver not found")
    vehicles = db.list_vehicles_for_driver(driver_id)
    return [v.__dict__ for v in vehicles]
