# @file backend/tests/managers_tests/test_reviewer_manager.py
# @brief ReviewerManager 测试
# @create 2026-03-26

import argparse


from managers.reviewer_manager import ReviewerManager


class TestReviewerManager:
    def setup_method(self):
        self.manager = ReviewerManager()

    def test_register_arguments(self):
        parser = argparse.ArgumentParser()
        self.manager.register_arguments(parser)
