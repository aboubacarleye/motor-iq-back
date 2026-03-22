from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_driver_vehicle_and_claim():
    # Register a new driver
    import uuid
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/auth/register",
        json={
            "first_name": "Test",
            "last_name": "Driver",
            "date_of_birth": "2000-01-01",
            "license_number": "ABC12345",
            "license_issued_date": "2020-01-01",
            "address": "123 Main St",
            "phone": "+233 55 000 0000",
            "email": unique_email,
            "password": "dummy",
        },
    )
    assert res.status_code == 200
    driver = res.json()
    driver_id = driver["id"]

    # Login to get token
    res = client.post(
        "/auth/login",
        data={"username": unique_email, "password": "dummy"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]

    # Create a vehicle for this driver using /vehicles/ endpoint
    res = client.post(
        "/vehicles/",
        json={
            "make": "Honda",
            "model": "Civic",
            "year": 2021,
            "registration_number": "GR-9999-21",
            "vin": "1HGCM82633A004352",
            "color": "Blue",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    vehicle = res.json()
    vehicle_id = vehicle["id"]

    # Create a claim
    res = client.post(
        "/claims",
        json={
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "description": "Front bumper damage",
            "date_of_accident": "2024-01-01",
            "gps_latitude": 5.6037,
            "gps_longitude": -0.1870,
            "status": "pending",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    claim = res.json()
    claim_id = claim["id"]

    # List claims for this driver
    res = client.get(
        f"/claims/driver/{driver_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    claims = res.json()
    assert any(c["id"] == claim_id for c in claims)

