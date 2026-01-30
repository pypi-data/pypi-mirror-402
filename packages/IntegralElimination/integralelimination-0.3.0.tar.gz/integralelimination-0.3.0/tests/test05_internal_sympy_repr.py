import sympy as sp
import unittest
from IntegralElimination import *

class TestIntegralElimination(unittest.TestCase):
    def test_05(self):
        x = sp.Function('x')
        y = sp.Function('y')
        t = sp.Symbol("t")
        theta = sp.Symbol("theta")
        P_expected = 3*IM(x(t))+theta*IM(y(t),1,y(t))+theta*IM(1,1,y(t))
        P = IntegralPolynomial(P_expected)                
        P_sp= P.get_sympy_repr()
        equal = sp.simplify(P_sp - P_expected) == 0
        self.assertTrue(equal)

if __name__ == '__main__':
    unittest.main()