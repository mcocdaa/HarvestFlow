# @file backend/tests/core_tests/test_api_common.py
# @brief API 通用响应与错误辅助单元测试
# @create 2026-08-10

from api.v1.common import ok, not_found, bad_request


class TestOk:
    def test_no_data_returns_success_only(self):
        assert ok() == {"success": True}

    def test_success_key_comes_first(self):
        assert list(ok(session=1).keys()) == ["success", "session"]

    def test_data_is_merged(self):
        assert ok(session=1) == {"success": True, "session": 1}


class TestNotFound:
    def test_status_code_and_detail(self):
        exc = not_found("x")
        assert exc.status_code == 404
        assert exc.detail == "x"


class TestBadRequest:
    def test_status_code_and_detail(self):
        exc = bad_request("x")
        assert exc.status_code == 400
        assert exc.detail == "x"
