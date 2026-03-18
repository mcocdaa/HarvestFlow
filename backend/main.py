# @file backend/main.py
# @brief 项目入口
# @create 2026-03-18

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import CORS_ORIGINS, HOST, PORT
from api import register_routers
from core.database import get_database
from core.plugin_loader import plugin_loader


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_database()
    db.initialize_tables()

    plugin_loader.initialize(app)
    await plugin_loader.load_all_plugins()

    yield

    db.close()


app = FastAPI(title="HarvestFlow", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_routers(app)


@app.get("/")
async def root():
    return {"name": "HarvestFlow", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
