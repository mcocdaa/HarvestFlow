# @file backend/tests/core_tests/database_manager/test_session_queries.py
# @brief DatabaseManager Session 查询测试
# @create 2026-03-27

from core.database_manager import DatabaseManager


class TestDatabaseManagerSessionQueries:
    def setup_method(self):
        self.manager = DatabaseManager()

    def teardown_method(self):
        if self.manager.connection:
            self.manager.close()

    def test_session_get_all(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        for i in range(5):
            self.manager.session_create({
                "session_id": f"session-{i}",
                "file_path": f"/tmp/test{i}.json",
                "status": "raw",
            })

        result = self.manager.session_get_all()
        assert result["total"] == 5
        assert len(result["sessions"]) == 5

    def test_session_get_all_with_status(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        for i in range(3):
            self.manager.session_create({
                "session_id": f"raw-{i}",
                "file_path": f"/tmp/raw{i}.json",
                "status": "raw",
            })
        for i in range(2):
            self.manager.session_create({
                "session_id": f"approved-{i}",
                "file_path": f"/tmp/approved{i}.json",
                "status": "approved",
            })

        result = self.manager.session_get_all(status="raw")
        assert result["total"] == 3

    def test_session_get_by_status(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        for i in range(3):
            self.manager.session_create({
                "session_id": f"raw-status-{i}",
                "file_path": f"/tmp/raw{i}.json",
                "status": "raw",
            })

        result = self.manager.session_get_by_status("raw")
        assert len(result) == 3

    def test_session_get_all_pagination(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        for i in range(25):
            self.manager.session_create({
                "session_id": f"page-test-{i}",
                "file_path": f"/test/page{i}.json",
                "status": "raw"
            })

        result_page1 = self.manager.session_get_all(page=1, page_size=10)
        assert result_page1["total"] == 25
        assert len(result_page1["sessions"]) == 10
        assert result_page1["page"] == 1

        result_page2 = self.manager.session_get_all(page=2, page_size=10)
        assert len(result_page2["sessions"]) == 10
        assert result_page2["page"] == 2

        result_page3 = self.manager.session_get_all(page=3, page_size=10)
        assert len(result_page3["sessions"]) == 5

    def test_session_get_all_sort_asc(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        for i in range(3):
            self.manager.session_create({
                "session_id": f"sort-test-{i}",
                "file_path": f"/test/sort{i}.json",
                "status": "raw"
            })

        result = self.manager.session_get_all(sort="oldest")
        assert len(result["sessions"]) == 3

    def test_session_get_for_export_no_filters(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        self.manager.session_create({
            "session_id": "approved-1",
            "file_path": "/test/approved1.json",
            "status": "approved"
        })
        self.manager.session_create({
            "session_id": "raw-1",
            "file_path": "/test/raw1.json",
            "status": "raw"
        })

        result = self.manager.session_get_for_export()
        assert len(result) == 1
        assert result[0]["session_id"] == "approved-1"

    def test_session_get_for_export_with_min_score(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        self.manager.session_create({
            "session_id": "score-80",
            "file_path": "/test/score80.json",
            "status": "approved"
        })
        self.manager.session_create({
            "session_id": "score-50",
            "file_path": "/test/score50.json",
            "status": "approved"
        })
        self.manager.session_update("score-80", {"quality_manual_score": 80})
        self.manager.session_update("score-50", {"quality_manual_score": 50})

        result = self.manager.session_get_for_export(min_score=70)
        assert len(result) == 1
        assert result[0]["session_id"] == "score-80"

    def test_session_get_for_export_with_agent_role(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        self.manager.session_create({
            "session_id": "role-coder",
            "file_path": "/test/coder.json",
            "status": "approved",
            "agent_role": "coder"
        })
        self.manager.session_create({
            "session_id": "role-architect",
            "file_path": "/test/architect.json",
            "status": "approved",
            "agent_role": "architect"
        })

        result = self.manager.session_get_for_export(agent_role="coder")
        assert len(result) == 1
        assert result[0]["session_id"] == "role-coder"

    def test_session_get_for_export_with_tags(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        self.manager.session_create({
            "session_id": "tag-bug",
            "file_path": "/test/bug.json",
            "status": "approved",
            "tags": ["bug", "debugging"]
        })
        self.manager.session_create({
            "session_id": "tag-feature",
            "file_path": "/test/feature.json",
            "status": "approved",
            "tags": ["feature", "new"]
        })

        result = self.manager.session_get_for_export(tags=["bug"])
        assert len(result) == 1
        assert result[0]["session_id"] == "tag-bug"

        result2 = self.manager.session_get_for_export(tags=["bug", "feature"])
        assert len(result2) == 2

    def test_session_get_for_export_filters_tags_correctly(self, args_with_db_path):
        self.manager.init(args_with_db_path)

        self.manager.session_create({
            "session_id": "tag-test",
            "file_path": "/test/tag.json",
            "status": "approved",
            "tags": ["python"]
        })

        result = self.manager.session_get_for_export(tags=["java"])
        assert len(result) == 0
