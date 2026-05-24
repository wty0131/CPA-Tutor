"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import init_db
from api.subjects import router as subjects_router
from api.questions import router as questions_router
from api.practice import router as practice_router
from api.wrongbook import router as wrongbook_router
from api.knowledge_points import router as kp_router
from api.scraper import router as scraper_router
from api.exam import router as exam_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Register demo scraper for testing
    from scraper.sites.demo_scraper import DemoCPAScraper
    from scraper.registry import register_scraper
    for code in ["CPA-01", "CPA-02", "CPA-03", "CPA-04", "CPA-05", "CPA-06"]:
        register_scraper(code, DemoCPAScraper())
    yield


app = FastAPI(
    title="CPA Tutor",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(subjects_router)
app.include_router(questions_router)
app.include_router(practice_router)
app.include_router(wrongbook_router)
app.include_router(kp_router)
app.include_router(scraper_router)
app.include_router(exam_router)


@app.get("/api/health")
def health():
    from core.ai_client import get_ai_client
    ai = get_ai_client()
    return {
        "status": "ok",
        "ai_available": ai.is_available,
    }
