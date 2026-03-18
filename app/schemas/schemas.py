from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DriverBase(BaseModel):
    name: str
    email: str
    phone: str

class DriverCreate(DriverBase):
    password: Optional[str] = None

class Driver(DriverBase):
    id: int
    class Config:
        from_attributes = True

class VehicleBase(BaseModel):
    make: str
    model: str
    year: int
    license_plate: str

class VehicleCreate(VehicleBase):
    pass

class Vehicle(VehicleBase):
    id: int
    driver_id: int
    class Config:
        from_attributes = True

class ClaimBase(BaseModel):
    description: str
    location_lat: float
    location_lng: float

class ClaimCreate(ClaimBase):
    vehicle_id: int

class Claim(ClaimBase):
    id: int
    driver_id: int
    vehicle_id: int
    status: str
    date_created: datetime
    fraud_risk_score: float
    ai_analysis: Optional[str]
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None