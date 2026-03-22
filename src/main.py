import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import Base, engine
from routes.schedule import router as schedule_router
from scheduler import lifespan

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)

# Create all tables on startup (Alembic handles migrations in production)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Fantasy Pitchers API",
    description="Probable starting pitchers for fantasy baseball.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schedule_router)
