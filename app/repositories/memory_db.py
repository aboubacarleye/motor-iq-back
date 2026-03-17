from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Driver:
    id: int
    name: str
    email: str
    phone: str


@dataclass
class Vehicle:
    id: int
    driver_id: int
    make: str
    model: str
    year: int
    license_plate: str


@dataclass
class TimelineStep:
    label: str
    completed: bool


@dataclass
class Claim:
    id: int
    claim_id: str
    driver_id: int
    vehicle_id: int
    description: str
    status: str
    date_created: datetime
    fraud_risk_score: float
    vehicle_name: str
    ai_analysis: Optional[str] = None
    timeline: List[TimelineStep] = field(default_factory=list)


@dataclass
class Policy:
    id: str
    name: str
    policyNumber: str
    coverageLimit: str
    renewalDate: str


class InMemoryDB:
    """Simple in-memory store for the MotorIQ demo.

    This mimics a repository layer so we can later plug a real DB.
    """

    def __init__(self) -> None:
        self._drivers: Dict[int, Driver] = {}
        self._vehicles: Dict[int, Vehicle] = {}
        self._claims: Dict[int, Claim] = {}
        self._policies: Dict[str, Policy] = {}

        self._driver_id_seq = 0
        self._vehicle_id_seq = 0
        self._claim_id_seq = 0

        self._seed_demo_data()

    # --- internal helpers ---

    def _next_driver_id(self) -> int:
        self._driver_id_seq += 1
        return self._driver_id_seq

    def _next_vehicle_id(self) -> int:
        self._vehicle_id_seq += 1
        return self._vehicle_id_seq

    def _next_claim_id(self) -> int:
        self._claim_id_seq += 1
        return self._claim_id_seq

    def _generate_claim_code(self, internal_id: int) -> str:
        return f"CLM-{1000 + internal_id}"

    def _seed_demo_data(self) -> None:
        # Default driver for MVP
        driver_id = self._next_driver_id()
        amira = Driver(
            id=driver_id,
            name="Amira Mensah",
            email="amira.mensah@example.com",
            phone="+233 55 123 4567",
        )
        self._drivers[driver_id] = amira

        # Two vehicles
        v1_id = self._next_vehicle_id()
        vehicle1 = Vehicle(
            id=v1_id,
            driver_id=driver_id,
            make="Toyota",
            model="Corolla",
            year=2020,
            license_plate="GR-1234-20",
        )
        self._vehicles[v1_id] = vehicle1

        v2_id = self._next_vehicle_id()
        vehicle2 = Vehicle(
            id=v2_id,
            driver_id=driver_id,
            make="Hyundai",
            model="Tucson",
            year=2022,
            license_plate="GR-5678-22",
        )
        self._vehicles[v2_id] = vehicle2

        # Policy for the driver
        policy = Policy(
            id="POL-001",
            name="Comprehensive Auto Policy",
            policyNumber="MIQ-2026-0001",
            coverageLimit="$50,000",
            renewalDate="2026-12-31",
        )
        self._policies[policy.id] = policy

        # A couple of demo claims with different statuses
        self.create_claim(
            driver_id=driver_id,
            vehicle_id=v1_id,
            description="Rear-end collision at traffic light",
            status="Under Review",
            date_created=datetime(2026, 3, 10),
        )
        self.create_claim(
            driver_id=driver_id,
            vehicle_id=v2_id,
            description="Minor scratch on right door",
            status="Completed",
            date_created=datetime(2026, 3, 5),
        )

    # --- Driver operations ---

    def list_drivers(self) -> List[Driver]:
        return list(self._drivers.values())

    def get_driver(self, driver_id: int) -> Optional[Driver]:
        return self._drivers.get(driver_id)

    def create_driver(self, name: str, email: str, phone: str) -> Driver:
        new_id = self._next_driver_id()
        driver = Driver(id=new_id, name=name, email=email, phone=phone)
        self._drivers[new_id] = driver
        return driver

    def update_driver(self, driver_id: int, name: str, email: str, phone: str) -> Optional[Driver]:
        driver = self._drivers.get(driver_id)
        if not driver:
            return None
        driver.name = name
        driver.email = email
        driver.phone = phone
        return driver

    # --- Vehicle operations ---

    def list_vehicles_for_driver(self, driver_id: int) -> List[Vehicle]:
        return [v for v in self._vehicles.values() if v.driver_id == driver_id]

    def create_vehicle(
        self,
        driver_id: int,
        make: str,
        model: str,
        year: int,
        license_plate: str,
    ) -> Vehicle:
        new_id = self._next_vehicle_id()
        vehicle = Vehicle(
            id=new_id,
            driver_id=driver_id,
            make=make,
            model=model,
            year=year,
            license_plate=license_plate,
        )
        self._vehicles[new_id] = vehicle
        return vehicle

    def get_vehicle(self, vehicle_id: int) -> Optional[Vehicle]:
        return self._vehicles.get(vehicle_id)

    # --- Policy operations ---

    def list_policies(self) -> List[Policy]:
        return list(self._policies.values())

    def get_policy_for_driver(self, driver_id: int) -> Optional[Policy]:
        # For the demo we just return the single policy
        return next(iter(self._policies.values()), None)

    # --- Claim operations ---

    def create_claim(
        self,
        driver_id: int,
        vehicle_id: int,
        description: str,
        status: str = "Submitted",
        date_created: Optional[datetime] = None,
    ) -> Claim:
        internal_id = self._next_claim_id()
        claim_code = self._generate_claim_code(internal_id)
        vehicle = self._vehicles.get(vehicle_id)
        vehicle_name = f"{vehicle.make} {vehicle.model}" if vehicle else "Unknown vehicle"

        if date_created is None:
            date_created = datetime.utcnow()

        timeline = [
            TimelineStep(label="Report Submitted", completed=True),
            TimelineStep(label="Investigation", completed=status not in {"Submitted"}),
            TimelineStep(label="Verification", completed=status in {"Approved", "Rejected", "Completed"}),
            TimelineStep(label="Decision", completed=status in {"Approved", "Rejected", "Completed"}),
            TimelineStep(label="Completed", completed=status == "Completed"),
        ]

        claim = Claim(
            id=internal_id,
            claim_id=claim_code,
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            description=description,
            status=status,
            date_created=date_created,
            fraud_risk_score=0.2,
            vehicle_name=vehicle_name,
            timeline=timeline,
        )
        self._claims[internal_id] = claim
        return claim

    def list_claims_for_driver(self, driver_id: int) -> List[Claim]:
        claims = [c for c in self._claims.values() if c.driver_id == driver_id]
        claims.sort(key=lambda c: c.date_created, reverse=True)
        return claims

    def get_claim(self, claim_id: int) -> Optional[Claim]:
        return self._claims.get(claim_id)

    def update_claim_status(
        self,
        claim_id: int,
        status: Optional[str] = None,
        fraud_risk_score: Optional[float] = None,
        timeline: Optional[List[TimelineStep]] = None,
    ) -> Optional[Claim]:
        claim = self._claims.get(claim_id)
        if not claim:
            return None
        if status is not None:
            claim.status = status
        if fraud_risk_score is not None:
            claim.fraud_risk_score = fraud_risk_score
        if timeline is not None:
            claim.timeline = timeline
        return claim


# Singleton instance used by FastAPI and Streamlit
db = InMemoryDB()

