# @file backend/tests/managers_tests/test_session_manager.py
# @brief SessionManager 测试
# @create 2026-03-26

import argparse


from managers.session_manager import SessionManager


class TestSessionManager:
    def setup_method(self):
        self.manager = SessionManager()

    def test_register_arguments(self):
        parser = argparse.ArgumentParser()
        self.manager.register_arguments(parser)
