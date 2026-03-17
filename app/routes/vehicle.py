from fastapi import APIRouter, HTTPException

from app.repositories.memory_db import db
from app.schemas.schemas import Vehicle, VehicleCreate


router = APIRouter(prefix="/drivers", tags=["vehicles"])


@router.post("/{driver_id}/vehicles", response_model=Vehicle)
def create_vehicle(driver_id: int, payload: VehicleCreate) -> Vehicle:
    if not db.get_driver(driver_id):
        raise HTTPException(status_code=404, detail="Driver not found")
    vehicle = db.create_vehicle(
        driver_id=driver_id,
        make=payload.make,
        model=payload.model,
        year=payload.year,
        license_plate=payload.license_plate,
    )
    return Vehicle.model_validate(vehicle.__dict__)
