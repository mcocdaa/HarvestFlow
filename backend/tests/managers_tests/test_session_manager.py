# @file backend/tests/managers_tests/test_session_manager.py
# @brief SessionManager 测试
# @create 2026-03-26

import argparse

import pytest

from managers.session_manager import SessionManager


class TestSessionManager:
    def setup_method(self):
        self.manager = SessionManager()

    def test_register_arguments(self):
        parser = argparse.ArgumentParser()
        self.manager.register_arguments(parser)

    def test_init(self, args_minimal):
        self.manager.init(args_minimal)
        assert self.manager.raw_sessions_dir is not None
        assert self.manager.agent_curated_dir is not None
        assert self.manager.human_approved_dir is not None
