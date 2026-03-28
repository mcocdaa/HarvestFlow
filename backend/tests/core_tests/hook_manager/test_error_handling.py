import pytest
import asyncio
from core.hook_manager import HookManager


@pytest.fixture
def fresh_hook_manager():
    hm = HookManager()
    yield hm
    hm.clear()


class TestErrorHandling:
    def test_error_isolation(self, fresh_hook_manager):
        results = []

        def error_callback():
            raise ValueError("intentional error")

        def success_callback():
            results.append("success")

        fresh_hook_manager.register("error_test", error_callback)
        fresh_hook_manager.register("error_test", success_callback)

        errors = asyncio.run(fresh_hook_manager.run("error_test"))

        assert results == ["success"]
        assert len(errors) == 1
        assert errors[0][0] == "error_callback"
        assert isinstance(errors[0][1], ValueError)

    def test_run_returns_errors(self, fresh_hook_manager):
        def error1():
            raise RuntimeError("error 1")

        def error2():
            raise ValueError("error 2")

        fresh_hook_manager.register("error_return_test", error1)
        fresh_hook_manager.register("error_return_test", error2)

        errors = asyncio.run(fresh_hook_manager.run("error_return_test"))

        assert len(errors) == 2
        assert errors[0][0] == "error1"
        assert errors[1][0] == "error2"
