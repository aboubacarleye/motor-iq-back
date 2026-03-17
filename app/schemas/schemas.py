from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class DriverBase(BaseModel):
    name: str
    email: str
    phone: str


class DriverCreate(DriverBase):
    """For MVP we ignore password but keep the field for future use."""

    password: Optional[str] = None


class Driver(DriverBase):
    id: int


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


class TimelineStep(BaseModel):
    label: str
    completed: bool


class ClaimBase(BaseModel):
    description: str
    status: str
    date_created: datetime
    driver_id: int
    vehicle_id: int


class ClaimCreate(BaseModel):
    driver_id: int
    vehicle_id: int
    description: str
    date_created: datetime
    status: str = "Submitted"


class Claim(BaseModel):
    id: int
    claimId: str
    description: str
    status: str
    date_created: datetime
    fraud_risk_score: float
    vehicle_id: int
    vehicleName: str
    ai_analysis: Optional[str] = None
    timeline: List[TimelineStep]


class ClaimUpdate(BaseModel):
    status: Optional[str] = None
    fraud_risk_score: Optional[float] = None
    timeline: Optional[List[TimelineStep]] = None


class Policy(BaseModel):
    id: str
    name: str
    policyNumber: str
    coverageLimit: str
    renewalDate: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
