from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import analyze
import os

app = FastAPI(title="JuniorDebug API", version="1.0.0")

# CORS middleware to allow frontend. Add `FRONTEND_URL` env var (no trailing slash)
# when deploying to ensure the deployed frontend origin is allowed.
default_origins = ["http://localhost:8080", "http://localhost:5173", "http://localhost:3000"]
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    # strip trailing slash if present
    frontend_url = frontend_url.rstrip("/")
    default_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=default_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, tags=["analyze"])
from app.routers import api_keys
app.include_router(api_keys.router, tags=["api_keys"])

from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("uvicorn.error")


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log exception server-side without exposing secrets to clients
    logger.exception(f"Unhandled error for request {request.method} {request.url}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.get("/")
async def root():
    return {"message": "JuniorDebug API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}