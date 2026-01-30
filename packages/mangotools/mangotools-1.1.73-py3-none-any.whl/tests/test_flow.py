# -*- coding: utf-8 -*-
# @Project: 芒果测试平台
# @Description: 
# @Time   : 2025-09-26 18:13
# @Author : 毛鹏
import unittest

from mangotools.mangos import build_decision_tree


class TestFlow(unittest.TestCase):
    def setUp(self):
        """在每个测试方法前初始化"""
        with open('tests/test-flow.json', 'r', encoding='utf-8') as f:
            import json
            self.data = json.load(f)

    def test_flow(self):
        """测试基本缓存操作"""
        # 测试设置和获取缓存
        data = build_decision_tree(self.data)
        assert data is not None
