from fastapi import APIRouter

from app.repositories.memory_db import db
from app.schemas.schemas import Driver, DriverCreate, Token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Driver)
def register(driver: DriverCreate) -> Driver:
    """Fake register for MVP.

    We ignore password and simply create a new driver in the in-memory store.
    """
    # Very naive: no email uniqueness check for the demo
    created = db.create_driver(name=driver.name, email=driver.email, phone=driver.phone)
    return Driver.model_validate(created.__dict__)


@router.post("/login", response_model=Token)
def login(email: str, password: str) -> Token:
    """Fake login for MVP.

    Returns a static token; the rest of the API does not require auth.
    """
    return Token(access_token="demo-token")
