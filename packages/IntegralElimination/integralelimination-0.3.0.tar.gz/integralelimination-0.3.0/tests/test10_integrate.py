import sympy as sp
import unittest
from IntegralElimination import *

class TestIntegralElimination(unittest.TestCase):
    def test_10(self):
        x = sp.Function('x')
        y = sp.Function('y')
        t = sp.Symbol("t")
        theta = sp.Symbol("theta")
        P = IntegralPolynomial(3*IM(x(t))+theta*IM(1,y(t)))
         

        IA = IntegralAlgebra(order=[x(t),y(t)],
                            parameters=[theta])
        
        PQ = IA.integrate_polynomial(P).get_sympy_repr()
        
        expected = 3*IM(1,x(t))+theta*IM(1,1,y(t))
        verify = sp.simplify(expected - PQ) == 0
        self.assertTrue(verify)

if __name__ == '__main__':
    unittest.main()