import uuid
from fastapi.testclient import TestClient
from app.main import app

def test_claim_analysis():
    client = TestClient(app)
    # Register and login
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/register", json={
        "first_name": "AI",
        "last_name": "Test",
        "date_of_birth": "2000-01-01",
        "license_number": "LICAI123",
        "license_issued_date": "2020-01-01",
        "address": "AI Street",
        "phone": "+233 55 000 0001",
        "email": email,
        "password": "dummy"
    })
    login = client.post("/auth/login", data={"username": email, "password": "dummy"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Create vehicle
    v = client.post("/vehicles/", json={
        "make": "AI",
        "model": "Test",
        "year": 2022,
        "registration_number": "AI-1234-22",
        "vin": "VINAI123456",
        "color": "Black"
    }, headers=headers)
    vehicle_id = v.json()["id"]
    # Create claim (no AI analysis at creation)
    c = client.post("/claims", json={
        "driver_id": login.json().get("id", 1),
        "vehicle_id": vehicle_id,
        "description": "Suspicious accident",
        "date_of_accident": "2024-01-01",
        "gps_latitude": 5.6,
        "gps_longitude": -0.18,
        "status": "pending"
    }, headers=headers)
    assert c.status_code == 200
    claim_id = c.json()["id"]
    # Analyze claim
    res = client.post(f"/claims/{claim_id}/analyze", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "fraud_risk_score" in data
    assert "ai_analysis" in data
    # Check that claim now has analysis fields
    claim = client.get(f"/claims/{claim_id}", headers=headers)
    assert claim.status_code == 200
    claim_data = claim.json()
    assert claim_data["fraud_risk_score"] == data["fraud_risk_score"]
    assert claim_data["ai_analysis"] == data["ai_analysis"]
