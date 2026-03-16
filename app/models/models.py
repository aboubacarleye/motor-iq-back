from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(20))
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
    license_plate = Column(String(20))
    driver = relationship("Driver", back_populates="vehicles")

class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    policy_number = Column(String(100))
    provider = Column(String(100))
    driver = relationship("Driver", back_populates="policies")

class Claim(Base):
    __tablename__ = "claims"
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    description = Column(Text)
    status = Column(String(50), default="pending")
    date_created = Column(DateTime)
    location_lat = Column(Float)
    location_lng = Column(Float)
    fraud_risk_score = Column(Float, default=0.0)
    ai_analysis = Column(Text)
    driver = relationship("Driver", back_populates="claims")
    vehicle = relationship("Vehicle")
    evidences = relationship("ClaimEvidence", back_populates="claim")

class ClaimEvidence(Base):
    __tablename__ = "claim_evidences"
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"))
    type = Column(String(50))  # photo, video, document
    url = Column(String(500))
    claim = relationship("Claim", back_populates="evidences")