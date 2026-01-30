import sympy as sp
import unittest
from IntegralElimination import *

class TestIntegralElimination(unittest.TestCase):
    def test_06(self):
        x = sp.Function('x')
        y = sp.Function('y')
        t = sp.Symbol("t")
        theta = sp.Symbol("theta")
        P = IntegralPolynomial(3*IM(x(t))+theta*IM(y(t),1,y(t))+theta*IM(1,1,y(t))) 
        P0 = P.cut_P("0").get_sympy_repr()
        expected = 3*IM(x(t))+theta*IM(y(t))+theta*IM(1)
        equal = sp.simplify(P0 - expected) == 0
        self.assertTrue(equal)

if __name__ == '__main__':
    unittest.main()