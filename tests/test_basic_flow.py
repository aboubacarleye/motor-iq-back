from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_driver_vehicle_and_claim():
    # Register a new driver
    res = client.post(
        "/auth/register",
        json={
            "name": "Test Driver",
            "email": "test@example.com",
            "phone": "+233 55 000 0000",
            "password": "dummy",
        },
    )
    assert res.status_code == 200
    driver = res.json()
    driver_id = driver["id"]

    # Create a vehicle for this driver
    res = client.post(
        f"/drivers/{driver_id}/vehicles",
        json={
            "make": "Honda",
            "model": "Civic",
            "year": 2021,
            "license_plate": "GR-9999-21",
        },
    )
    assert res.status_code == 200
    vehicle = res.json()
    vehicle_id = vehicle["id"]

    # Create a claim
    today = datetime.utcnow().date().isoformat()
    res = client.post(
        "/claims",
        json={
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "description": "Front bumper damage",
            "date_created": today,
            "status": "Submitted",
        },
    )
    assert res.status_code == 200
    claim = res.json()
    claim_id = claim["id"]

    # List claims for this driver
    res = client.get(f"/claims/driver/{driver_id}")
    assert res.status_code == 200
    claims = res.json()
    assert any(c["id"] == claim_id for c in claims)

