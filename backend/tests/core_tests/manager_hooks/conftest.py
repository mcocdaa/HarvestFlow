import pytest
from core.hook_manager import hook_manager


@pytest.fixture(autouse=True)
def clean_hooks():
    """每个测试前清理钩子"""
    hook_manager.clear()
    yield
    hook_manager.clear()
