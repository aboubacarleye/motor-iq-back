from datetime import datetime
import random
import threading

import streamlit as st
import uvicorn

from app.main import app as fastapi_app
from app.repositories.memory_db import db


st.set_page_config(page_title="MotorIQ Backend Console", layout="wide")


def _run_fastapi():
    """Lance l'API FastAPI dans un thread séparé.

    Utile sur Streamlit Cloud pour avoir l'API + Swagger dans le même déploiement.
    """
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    server.run()


if "api_started" not in st.session_state:
    # Démarrage unique de l'API FastAPI
    thread = threading.Thread(target=_run_fastapi, daemon=True)
    thread.start()
    st.session_state["api_started"] = True


st.title("MotorIQ Backend Console")
st.caption("Demo dashboard powered by an in-memory FastAPI backend.")

st.markdown(
    """
**API FastAPI**: tourne dans le même conteneur sur `http://localhost:8000`  
Vous pouvez ouvrir directement la doc Swagger sur `/docs`.
"""
)

st.markdown(
    """
<iframe src="http://localhost:8000/docs" width="100%" height="500" style="border:none;"></iframe>
""",
    unsafe_allow_html=True,
)


def format_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


st.markdown("---")

with st.sidebar:
    st.header("Drivers")
    drivers = db.list_drivers()
    driver_options = {f"{d.name} (#{d.id})": d.id for d in drivers}
    selected_driver_label = st.selectbox(
        "Select driver", list(driver_options.keys()), index=0 if driver_options else None
    )
    selected_driver_id = driver_options[selected_driver_label] if driver_options else None

    st.markdown("---")
    st.header("Filters")
    status_filter = st.multiselect(
        "Claim status",
        options=[
            "Submitted",
            "Under Review",
            "Inspection Required",
            "Approved",
            "Rejected",
            "Completed",
        ],
        default=[],
    )


if not selected_driver_id:
    st.warning("No driver available in the demo data.")
    st.stop()

driver = db.get_driver(selected_driver_id)
vehicles = db.list_vehicles_for_driver(selected_driver_id)
claims = db.list_claims_for_driver(selected_driver_id)

if status_filter:
    claims = [c for c in claims if c.status in status_filter]


col1, col2 = st.columns(2)

with col1:
    st.subheader("Driver profile")
    st.write(f"**Name**: {driver.name}")
    st.write(f"**Email**: {driver.email}")
    st.write(f"**Phone**: {driver.phone}")

    policy = db.get_policy_for_driver(driver.id)
    if policy:
        st.markdown("### Active Policy")
        st.write(f"**Name**: {policy.name}")
        st.write(f"**Policy number**: {policy.policyNumber}")
        st.write(f"**Coverage**: {policy.coverageLimit}")
        st.write(f"**Renewal date**: {policy.renewalDate}")

with col2:
    st.subheader("Vehicles")
    if vehicles:
        for v in vehicles:
            st.write(f"- #{v.id} {v.make} {v.model} ({v.year}) – {v.license_plate}")
    else:
        st.info("No vehicles for this driver.")


st.markdown("## Claims")

if not claims:
    st.info("No claims yet for this driver.")
    st.stop()

claim_labels = {f"{c.claim_id} – {c.description[:40]}": c.id for c in claims}
selected_claim_label = st.selectbox("Select claim", list(claim_labels.keys()))
selected_claim_id = claim_labels[selected_claim_label]
claim = db.get_claim(selected_claim_id)

left, right = st.columns(2)

with left:
    st.markdown("### Claim summary")
    st.write(f"**Claim ID**: {claim.claim_id}")
    st.write(f"**Status**: {claim.status}")
    st.write(f"**Created**: {format_date(claim.date_created)}")
    st.write(f"**Vehicle**: {claim.vehicle_name}")
    st.write(f"**Fraud risk score**: {claim.fraud_risk_score:.2f}")
    st.write("**Description**:")
    st.write(claim.description)

    st.markdown("#### Update status")
    new_status = st.selectbox(
        "New status",
        [
            "Submitted",
            "Under Review",
            "Inspection Required",
            "Approved",
            "Rejected",
            "Completed",
        ],
        index=0,
    )
    if st.button("Apply status"):
        db.update_claim_status(claim_id=claim.id, status=new_status)
        st.success("Status updated.")

    if st.button("Recalculate fraud risk score"):
        new_score = random.uniform(0, 1)
        db.update_claim_status(claim_id=claim.id, fraud_risk_score=new_score)
        st.success(f"Fraud risk score updated to {new_score:.2f}")

with right:
    st.markdown("### Timeline")
    for step in claim.timeline:
        icon = "✅" if step.completed else "⏳"
        st.write(f"{icon} {step.label}")

