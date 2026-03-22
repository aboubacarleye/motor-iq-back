from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(String(20))
    license_number = Column(String(100))
    license_issued_date = Column(String(20))
    address = Column(String(255))
    phone = Column(String(20))
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    vehicles = relationship("Vehicle", back_populates="driver")
    policies = relationship("InsurancePolicy", back_populates="driver")
    claims = relationship("Claim", back_populates="driver")

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    make = Column(String(100))
    model = Column(String(100))
    year = Column(Integer)
    registration_number = Column(String(50))
    vin = Column(String(100))
    color = Column(String(50))
    driver = relationship("Driver", back_populates="vehicles")

class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    company = Column(String(100))
    policy_number = Column(String(100))
    start_date = Column(String(20))
    end_date = Column(String(20))
    coverage_type = Column(String(100))
    driver = relationship("Driver", back_populates="policies")

class Claim(Base):
    __tablename__ = "claims"
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    insurance_id = Column(Integer, ForeignKey("insurance_policies.id"), nullable=True)
    date_of_accident = Column(String(20))
    # location = Column(String(255))  # Removed: use only gps_latitude and gps_longitude
    description = Column(Text)
    audio_url = Column(String(500))
    image_url = Column(String(500))
    gps_latitude = Column(Float)
    gps_longitude = Column(Float)
    status = Column(String(50), default="pending")
    fraud_risk_score = Column(Float, default=0.0)
    ai_analysis = Column(Text)
    driver = relationship("Driver", back_populates="claims")
    vehicle = relationship("Vehicle")
    insurance = relationship("InsurancePolicy")
    evidences = relationship("ClaimEvidence", back_populates="claim")

class ClaimEvidence(Base):
    __tablename__ = "claim_evidences"
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"))
    type = Column(String(50))  # photo, video, document
    url = Column(String(500))
    claim = relationship("Claim", back_populates="evidences")