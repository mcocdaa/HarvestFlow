# @file backend/config/settings.py
# @brief 项目配置：端口、目录、插件、数据库
# @create 2026-03-18

import os
from enum import Enum
from dotenv import load_dotenv

load_dotenv()


class Environment(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


API_VERSION = os.getenv("API_VERSION", "v1")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BASE_DIR)

DATA_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "data", "db", "harvestflow.db"))

RAW_SESSIONS_DIR = os.path.join(DATA_DIR, "raw_sessions")
AGENT_CURATED_DIR = os.path.join(DATA_DIR, "agent_curated")
HUMAN_APPROVED_DIR = os.path.join(DATA_DIR, "human_approved")
EXPORT_DIR = os.path.join(DATA_DIR, "export")

PLUGINS_DIR = os.getenv("PLUGINS_DIR", os.path.join(ROOT_DIR, "plugins"))

HOST = os.getenv("HOST", "0.0.0.0")
# 容器内部端口，固定为3000，外部端口通过docker-compose映射
PORT = 3000

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

COLLECTOR_CONFIG = {
    "watch_folders": [],
    "poll_interval": 60,
}

CURATOR_CONFIG = {
    "default_enabled": True,
    "auto_approve_threshold": 4,
}

EXPORT_CONFIG = {
    "default_format": "sharegpt",
    "output_dir": EXPORT_DIR,
}

__all__ = [
    "API_VERSION",
    "BASE_DIR",
    "ROOT_DIR",
    "DATA_DIR",
    "DB_PATH",
    "RAW_SESSIONS_DIR",
    "AGENT_CURATED_DIR",
    "HUMAN_APPROVED_DIR",
    "EXPORT_DIR",
    "PLUGINS_DIR",
    "HOST",
    "PORT",
    "CORS_ORIGINS",
    "COLLECTOR_CONFIG",
    "CURATOR_CONFIG",
    "EXPORT_CONFIG",
]

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(RAW_SESSIONS_DIR, exist_ok=True)
os.makedirs(AGENT_CURATED_DIR, exist_ok=True)
os.makedirs(HUMAN_APPROVED_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(PLUGINS_DIR, exist_ok=True)
