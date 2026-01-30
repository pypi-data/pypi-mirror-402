import sympy as sp
import unittest
from IntegralElimination import *

class TestIntegralElimination(unittest.TestCase):
    def test_11(self):
        x = sp.Function('x')
        y = sp.Function('y')
        t = sp.Symbol("t")
        theta = sp.Symbol("theta") 

        IA = IntegralAlgebra(order=[x(t),y(t)],
                            parameters=[theta])
        
        P = IntegralPolynomial(IM(1,x(t))-IM(y(t)))
        N = IM(1,y(t))
        reduce_product= IA.half_reduced_product(P,N).get_sympy_repr()
        
        expected = IM(1, y(t)**2) - IM(y(t), y(t)) + IM(1, x(t), y(t))
        verify = sp.simplify(expected - reduce_product) == 0
        self.assertTrue(verify)

if __name__ == '__main__':
    unittest.main()