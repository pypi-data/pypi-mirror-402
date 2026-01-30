import sympy as sp
import unittest
from IntegralElimination import *

class TestIntegralElimination(unittest.TestCase):
    def test_09(self):
        x = sp.Function('x')
        y = sp.Function('y')
        t = sp.Symbol("t")
        theta = sp.Symbol("theta")
        P = IntegralPolynomial(3*IM(x(t))+theta*IM(1,y(t)))
        Q = IntegralPolynomial(IM(1,x(t))+ IM(1))

        IA = IntegralAlgebra(order=[x(t),y(t)],
                            parameters=[theta])
        
        PQ = IA.polynomials_product(P,Q).get_sympy_repr()
        
        expected = theta*IM(1, y(t)) + theta*IM(1, x(t), y(t)) + theta*IM(1, y(t), x(t)) + 3*IM(x(t)) + 3*IM(x(t), x(t))
        verify = sp.simplify(expected - PQ) == 0
        self.assertTrue(verify)

if __name__ == '__main__':
    unittest.main()