from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ORIGINS
from app.firebase_config import initialize_firebase
from app.logging_config import configure_logging
from app.routers import ai_reviews, pomodoros, projects, tasks

configure_logging()

app = FastAPI(title="LaSalsa API", version="0.1.0")


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on application startup."""
    initialize_firebase()


origins = ORIGINS if ORIGINS != [""] else ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # на проде лучше ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(projects.router)
app.include_router(pomodoros.router)
app.include_router(ai_reviews.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to LaSalsa API!"}


@app.get("/healthz")
def healthz() -> dict[str, bool]:
    return {"ok": True}
