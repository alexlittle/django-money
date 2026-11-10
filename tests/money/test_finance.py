from datetime import datetime, timedelta
from unittest import TestCase

from money.finance import xirr

START = datetime(2020, 1, 1)


class XirrTests(TestCase):
    def test_simple_growth(self):
        flows = [(START, -100), (START + timedelta(days=365), 110)]
        self.assertAlmostEqual(xirr(flows), 0.10, places=6)

    def test_negative_return(self):
        flows = [(START, -100), (START + timedelta(days=365), 90)]
        self.assertAlmostEqual(xirr(flows), -0.10, places=6)

    def test_zero_return_with_intermediate_flow(self):
        flows = [
            (START, -1000),
            (START + timedelta(days=100), -1000),
            (START + timedelta(days=730), 2000),
        ]
        self.assertAlmostEqual(xirr(flows), 0.0, places=6)

    def test_none_when_all_flows_same_sign(self):
        self.assertIsNone(xirr([(START, -100), (START + timedelta(days=30), -50)]))

    def test_none_when_no_flows(self):
        self.assertIsNone(xirr([]))
