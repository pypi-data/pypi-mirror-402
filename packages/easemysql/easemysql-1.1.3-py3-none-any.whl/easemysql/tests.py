import sys
import unittest
from . import where_in, where_simple


class TestWhereIn(unittest.TestCase):
    """测试 where_in 函数"""

    def test_integer_list(self):
        """测试整数列表"""
        result = where_in([1, 2, 3])
        self.assertEqual(result, "1,2,3")

    def test_string_list(self):
        """测试字符串列表"""
        result = where_in(['a', 'b', 'c'])
        self.assertEqual(result, "'a','b','c'")

    def test_mixed_list(self):
        """测试混合类型列表"""
        result = where_in([1, 'a', 2.5])
        self.assertEqual(result, "1,'a',2.5")

    def test_single_value(self):
        """测试非列表值"""
        result = where_in(100)
        self.assertEqual(result, 100)

    def test_empty_list(self):
        """测试空列表 - 边界情况"""
        result = where_in([])
        self.assertEqual(result, "")


class TestWhereComplex(unittest.TestCase):
    def test_01(self):
        condition = [
            {'is_open': 1},
            'is_safe >= 10'
        ]
        a = where_simple(['AND', *condition])
        b = where_simple(condition)
        self.assertEqual(a, b)

    def test_02(self):
        condition = [
            'OR',
            [
                'AND',
                {'is_open': 1},
                'is_safe >= 10',
                ['>=', 'id', 100]
            ],
            ['IN', 'device_id', [1, 2, 3]]
        ]
        condition2 = [
            'OR',
            [
                {'is_open': 1},
                'is_safe >= 10',
                ['>=', 'id', 100]
            ],
            ['IN', 'device_id', [1, 2, 3]]
        ]
        result = where_simple(condition)
        self.assertEqual(
            '(((is_open = 1) AND (is_safe >= 10) AND (id >= 100)) OR (device_id IN (1,2,3)))',
            result
        )
        self.assertEqual(where_simple(condition2), result)
