import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app import api
import time
import os

# creates a file called app.log inside logs folder, if already present skips creation
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Configure logging globally. Log to file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE,encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("matching_engine")

app = FastAPI(title="Matching Engine Prototype")

@app.on_event("startup")
async def startup_event():
    logger.info("Matching Engine API started successfully.")

# add logger to all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    logger.info(f"Incoming request: {request.method} {request.url}")

    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception(f"Error during request: {exc}")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    process_time = (time.time() - start_time) * 1000
    logger.info(f"Response {response.status_code} ({process_time:.2f} ms)")
    return response

app.include_router(api.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api:app", host="0.0.0.0", port=8000, reload=True)

# uvicorn app.main:app --reload