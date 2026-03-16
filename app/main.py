from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, driver, vehicle, claims

app = FastAPI(title="MotorIQ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(driver.router)
app.include_router(vehicle.router)
app.include_router(claims.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to MotorIQ API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)