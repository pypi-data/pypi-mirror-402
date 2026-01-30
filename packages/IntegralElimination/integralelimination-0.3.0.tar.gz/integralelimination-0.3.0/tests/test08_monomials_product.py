import sympy as sp
import unittest
from IntegralElimination import *

class TestIntegralElimination(unittest.TestCase):
    def test_08(self):
        x = sp.Function('x')
        y = sp.Function('y')
        t = sp.Symbol("t")
        theta = sp.Symbol("theta")
        M = IM(1,x(t)) 
        N = IM(1,y(t))
        IA = IntegralAlgebra(order=[x(t),y(t)],
                            parameters=[theta])
        
        MN = IA.monomial_product(M,N).get_sympy_repr()
        
        MN_expected = IM(1, x(t), y(t)) + IM(1, y(t), x(t))
        verify = sp.simplify(MN_expected - MN) == 0
        self.assertTrue(verify)

if __name__ == '__main__':
    unittest.main()