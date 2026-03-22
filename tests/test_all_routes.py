import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_all_routes():
    # Register
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    register_data = {
        "first_name": "Test",
        "last_name": "User",
        "date_of_birth": "2000-01-01",
        "license_number": "LIC12345",
        "license_issued_date": "2020-01-01",
        "address": "123 Main St",
        "phone": "+233 55 000 0000",
        "email": unique_email,
        "password": "dummy"
    }
    res = client.post("/auth/register", json=register_data)
    print("/auth/register:", res.status_code, res.json())
    assert res.status_code == 200
    driver_id = res.json()["id"]

    # Login
    res = client.post("/auth/login", data={"username": unique_email, "password": "dummy"})
    print("/auth/login:", res.status_code, res.json())
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get current user
    res = client.get("/auth/me", headers=headers)
    print("/auth/me:", res.status_code, res.json())
    assert res.status_code == 200

    # Create vehicle
    vehicle_data = {
        "make": "Toyota",
        "model": "Corolla",
        "year": 2022,
        "registration_number": "GR-1234-22",
        "vin": "VIN1234567890",
        "color": "Red"
    }
    res = client.post("/vehicles/", json=vehicle_data, headers=headers)
    print("/vehicles/:", res.status_code, res.json())
    assert res.status_code == 200
    vehicle_id = res.json()["id"]

    # Get my vehicles
    res = client.get("/vehicles/my/list", headers=headers)
    print("/vehicles/my/list:", res.status_code, res.json())
    assert res.status_code == 200

    # Get vehicle by id
    res = client.get(f"/vehicles/{vehicle_id}", headers=headers)
    print(f"/vehicles/{{vehicle_id}}:", res.status_code, res.json())
    assert res.status_code == 200

    # Get my profile
    res = client.get("/drivers/profile/me", headers=headers)
    print("/drivers/profile/me:", res.status_code, res.json())
    assert res.status_code == 200

    # Get driver by id
    res = client.get(f"/drivers/{driver_id}", headers=headers)
    print(f"/drivers/{{driver_id}}:", res.status_code, res.json())
    assert res.status_code == 200

    # Create claim
    claim_data = {
        "driver_id": driver_id,
        "vehicle_id": vehicle_id,
        "description": "Test accident",
        "date_of_accident": "2024-01-01",
        "gps_latitude": 5.6037,
        "gps_longitude": -0.1870,
        "status": "pending"
    }
    res = client.post("/claims", json=claim_data, headers=headers)
    print("/claims:", res.status_code, res.json())
    assert res.status_code == 200
    claim_id = res.json()["id"]

    # Get my claims
    res = client.get("/claims/my/list", headers=headers)
    print("/claims/my/list:", res.status_code, res.json())
    assert res.status_code == 200

    # Get claim by id
    res = client.get(f"/claims/{claim_id}", headers=headers)
    print(f"/claims/{{claim_id}}:", res.status_code, res.json())
    assert res.status_code == 200

    # Get claims by driver
    res = client.get(f"/claims/driver/{driver_id}", headers=headers)
    print(f"/claims/driver/{{driver_id}}:", res.status_code, res.json())
    assert res.status_code == 200

    # Analyze claim (Gemini)
    res = client.post(f"/claims/{claim_id}/analyze", headers=headers)
    print(f"/claims/{{claim_id}}/analyze:", res.status_code, res.json())
    assert res.status_code in (200, 500)  # AI may fail if Gemini not configured
