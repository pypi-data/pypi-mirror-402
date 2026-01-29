import unittest
import sys
import os

# Add the parent directory to the path so we can import cashy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cashy import CurrencyConverter

class TestCurrencyConverter(unittest.TestCase):
    def setUp(self):
        self.converter = CurrencyConverter()

    def test_same_currency(self):
        # Converting USD to USD should give us the same amount back
        self.assertEqual(self.converter.convert(100, 'USD', 'USD'), 100)

    def test_usd_to_eur_exists(self):
        # Can't test exact values since rates change constantly, but we can check the basics
        rate = self.converter.get_exchange_rate('USD', 'EUR')
        self.assertIsInstance(rate, float)
        self.assertGreater(rate, 0)

    def test_convert_function(self):
        # Make sure the convert function works the same as getting rate manually
        amount = 100
        converted = self.converter.convert(amount, 'USD', 'EUR')
        rate = self.converter.get_exchange_rate('USD', 'EUR')
        self.assertAlmostEqual(converted, amount * rate)

if __name__ == '__main__':
    unittest.main()