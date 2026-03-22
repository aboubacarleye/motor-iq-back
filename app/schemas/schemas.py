from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DriverBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    license_number: str
    license_issued_date: str
    address: str
    phone: str
    email: str

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
    registration_number: str
    vin: str
    color: str

class VehicleCreate(VehicleBase):
    pass

class Vehicle(VehicleBase):
    id: int
    driver_id: int
    class Config:
        from_attributes = True


class InsurancePolicyBase(BaseModel):
    company: str
    policy_number: str
    start_date: str
    end_date: str
    coverage_type: str

class InsurancePolicyCreate(InsurancePolicyBase):
    pass

class InsurancePolicy(InsurancePolicyBase):
    id: int
    driver_id: int
    class Config:
        from_attributes = True

class ClaimBase(BaseModel):
    description: str
    date_of_accident: str
    # location: str  # Removed: use only gps_latitude and gps_longitude
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    status: str

class ClaimCreate(ClaimBase):
    driver_id: int
    vehicle_id: int
    insurance_id: Optional[int] = None

class Claim(ClaimBase):
    id: int
    driver_id: int
    vehicle_id: int
    insurance_id: Optional[int] = None
    fraud_risk_score: Optional[float] = None
    ai_analysis: Optional[str] = None
    class Config:
        from_attributes = True

class ClaimEvidenceBase(BaseModel):
    type: str
    url: str

class ClaimEvidenceCreate(ClaimEvidenceBase):
    claim_id: int

class ClaimEvidence(ClaimEvidenceBase):
    id: int
    claim_id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None