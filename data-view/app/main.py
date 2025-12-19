# app/main.py
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from app.config import settings # Import settings instance
from app.database import connect_db, disconnect_db, initialize_database
from app.utils import setup_logging
from app.routers import auth as auth_router
from app.routers import zookeeper as zk_router
from app.routers.zookeeper import shutdown_zk_client # Import shutdown specific function

# Setup logging as early as possible
setup_logging()
logger = logging.getLogger(__name__)


# Asynchronous context manager for application lifespan events (startup/shutdown)
# Replaces deprecated on_event("startup") / on_event("shutdown")
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Code to run on startup ---
    logger.info("Application startup sequence initiated...")
    try:
        # Connect to database
        await connect_db()
        # Initialize database schema and default user
        await initialize_database()
        # Initialize Zookeeper Client (optional here, could be lazy loaded on first request)
        # get_zk_client() # Pre-connect ZK if desired

        logger.info("Database connected and initialized.")
    except Exception as e:
        logger.exception("CRITICAL: Failed to initialize database during startup. Application might not function correctly.")
        # Depending on severity, you might want to prevent the app from fully starting
        # For now, it logs the error and continues.

    logger.info("Application startup complete.")
    yield # Application runs after this point
    # --- Code to run on shutdown ---
    logger.info("Application shutdown sequence initiated...")
    # Close Zookeeper connection
    await shutdown_zk_client()
    # Disconnect from database
    await disconnect_db()
    logger.info("Resources released. Application shutdown complete.")

# Create FastAPI application instance
app = FastAPI(
    title="Data Query Admin Backend",
    description="Backend API for querying data sources and managing access.",
    version="0.1.0",
    lifespan=lifespan # Use the lifespan context manager
)

# Include API routers
logger.info("Including API routers...")
app.include_router(auth_router.router)
app.include_router(zk_router.router)
logger.info("API routers included.")

# --- Optional: Global Exception Handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for Pydantic validation errors to provide clearer messages.
    """
    logger.warning(f"Request validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Generic handler for unexpected server errors.
    """
    logger.exception(f"Unhandled exception during request to {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
    )

# --- Root Endpoint ---
@app.get("/", tags=["Health Check"])
async def read_root():
    """
    Root endpoint for basic health check.
    """
    logger.info("Root endpoint '/' accessed.")
    return {"message": "Welcome to the Data Query Admin Backend!"}

logger.info("FastAPI application configured.")

# --- How to Run (using uvicorn) ---
# Make sure you are in the directory containing the 'app' folder and '.env'
# Install requirements: pip install -r requirements.txt
# Run: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
#
# --reload: Enables auto-reloading on code changes (for development)
# --host 0.0.0.0: Makes the server accessible on your network
# --port 8000: Specifies the port to run on
