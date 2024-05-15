"""
Sample tests
"""
from django.test import SimpleTestCase
from .calc import add


class CalcTests(SimpleTestCase):
    def test_add_numbers(self):
        self.assertEqual(add(3, 8), 11)
