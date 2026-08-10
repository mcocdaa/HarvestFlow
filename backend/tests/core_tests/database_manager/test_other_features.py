# @file backend/tests/core_tests/database_manager/test_other_features.py
# @brief DatabaseManager 其他功能测试（审计日志、导出记录、插件）
# @create 2026-03-27

from core.database_manager import DatabaseManager


class TestDatabaseManagerOtherFeatures:
    def setup_method(self):
        self.manager = DatabaseManager()

    def teardown_method(self):
        if self.manager.connection:
            self.manager.close()

    def test_audit_log_create_and_get(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        self.manager.audit_log_create("session-001", "approve", "admin", "Approved by admin")

        logs = self.manager.audit_log_get("session-001")
        assert len(logs) == 1
        assert logs[0]["action"] == "approve"
        assert logs[0]["operator"] == "admin"

    def test_audit_log_get_all(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        self.manager.audit_log_create("session-001", "create")
        self.manager.audit_log_create("session-002", "create")

        logs = self.manager.audit_log_get()
        assert len(logs) == 2

    def test_audit_log_get_with_limit(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        for i in range(10):
            self.manager.audit_log_create(f"session-{i}", "action")

        logs = self.manager.audit_log_get(limit=5)
        assert len(logs) == 5

    def test_export_record_create_and_get_history(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        self.manager.export_record_create(
            export_format="json",
            file_path="/tmp/export.json",
            filters={"status": "approved"},
            record_count=10,
            version="v1"
        )

        history = self.manager.export_record_get_history()
        assert len(history) == 1
        assert history[0]["export_format"] == "json"
        assert history[0]["record_count"] == 10

    def test_export_record_get_history_limit(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        for i in range(10):
            self.manager.export_record_create(
                export_format="json",
                file_path=f"/tmp/export{i}.json",
                filters={},
                record_count=i,
                version="v1"
            )

        history = self.manager.export_record_get_history(limit=5)
        assert len(history) == 5

    def test_stats_get_includes_curated_status(self, args_with_db_path):
        """P1.4: stats_get should count curated sessions and include reviewed_sessions."""
        self.manager.init(args_with_db_path)

        for i in range(3):
            self.manager.session_create({
                "session_id": f"raw-{i}", "status": "raw", "file_path": f"/tmp/raw{i}.json",
            })
        for i in range(2):
            self.manager.session_create({
                "session_id": f"curated-{i}", "status": "curated", "file_path": f"/tmp/curated{i}.json",
            })
        self.manager.session_create({
            "session_id": "approved-1", "status": "approved", "file_path": "/tmp/approved1.json",
        })
        self.manager.session_create({
            "session_id": "rejected-1", "status": "rejected", "file_path": "/tmp/rejected1.json",
        })

        stats = self.manager.stats_get()

        assert stats["total_sessions"] == 7
        assert stats["raw_sessions"] == 3
        assert stats["curated_sessions"] == 2
        assert stats["approved_sessions"] == 1
        assert stats["rejected_sessions"] == 1
        assert stats["reviewed_sessions"] == 2
        assert "avg_auto_score" in stats

    def test_deserialize_tolerates_bad_json(self):
        """_deserialize_session_fields 不应在非 JSON 标签上崩溃"""
        from core.database_manager import database_manager

        session = {"tags": "not-json", "tools_used": "[1,2,3]", "content": None}
        result = database_manager._deserialize_session_fields(session)
        assert result["tags"] == "not-json"  # kept as string
        assert result["tools_used"] == [1, 2, 3]  # valid JSON still parsed
        assert result["content"] is None
