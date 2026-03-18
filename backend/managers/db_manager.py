# @file backend/managers/db_manager.py
# @brief 数据库管理器
# @create 2026-03-18

import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from core.database import get_database


class DbManager:
    def __init__(self):
        self.db = None

    async def initialize(self):
        self.db = get_database()
        self.db.initialize_tables()

    async def close(self):
        from core.database import close_database
        close_database()

    def get_db(self):
        if not self.db:
            self.db = get_database()
        return self.db


db_manager = DbManager()
