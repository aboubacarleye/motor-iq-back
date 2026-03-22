from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from app.logger import logger
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, claims, driver, vehicle


app = FastAPI(title="MotorIQ API", version="1.0.0")

# Handler global pour logger toutes les exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

# Handler pour logger les erreurs de validation Pydantic
@app.exception_handler(FastAPIRequestValidationError)
async def validation_exception_handler(request: Request, exc: FastAPIRequestValidationError):
    logger.error(f"Validation error: {exc}", exc_info=True)
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

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
    return {"message": "Welcome to MotorIQ API", "default_driver_id": 1}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
