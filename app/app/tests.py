"""
Sample tests
"""
from django.test import SimpleTestCase
from .calc import add, subtract


class CalcTests(SimpleTestCase):
    def test_add_numbers(self):
        self.assertEqual(add(3, 8), 11)

    def test_subtract_numbers(self):
        res = subtract(3, 8)
        self.assertEqual(res, -5)
