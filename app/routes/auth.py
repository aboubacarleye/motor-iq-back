from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.schemas import DriverCreate, Driver, Token
from app.models.models import Driver as DriverModel
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/register", response_model=Driver)
def register(driver: DriverCreate, db: Session = Depends(get_db)):
    db_driver = db.query(DriverModel).filter(DriverModel.email == driver.email).first()
    if db_driver:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(driver.password)
    db_driver = DriverModel(
        name=driver.name,
        email=driver.email,
        phone=driver.phone,
        hashed_password=hashed_password
    )
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver

@router.post("/login", response_model=Token)
def login(email: str, password: str, db: Session = Depends(get_db)):
    db_driver = db.query(DriverModel).filter(DriverModel.email == email).first()
    if not db_driver or not verify_password(password, db_driver.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_driver.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}