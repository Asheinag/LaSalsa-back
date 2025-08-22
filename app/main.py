from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.firebase_config import initialize_firebase
from app.logging_config import configure_logging
from app.routers import projects, tasks

configure_logging()

# Инициализация Firebase

initialize_firebase()


app = FastAPI(title="LaSalsa API", version="0.1.0")

origins = [
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # на проде лучше ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(projects.router)


@app.get("/")
async def root():
    return {"message": "Welcome to LaSalsa API!"}
