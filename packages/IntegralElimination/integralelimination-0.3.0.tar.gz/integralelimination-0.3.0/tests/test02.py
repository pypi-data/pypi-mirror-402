import sympy as sp
import unittest
from IntegralElimination import *

class TestIntegralElimination(unittest.TestCase):
    def test_02(self):
        x = sp.Function('x')
        y = sp.Function('y')
        t = sp.Symbol("t")
        test_OK = False
        try:
            IM(x(t),IM(y(t)))
        except AssertionError:
            test_OK = True
        self.assertTrue(test_OK)


if __name__ == '__main__':
    unittest.main()