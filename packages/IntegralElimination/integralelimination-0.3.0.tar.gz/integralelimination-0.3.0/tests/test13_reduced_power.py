import sympy as sp
import unittest
from IntegralElimination import *

class TestIntegralElimination(unittest.TestCase):
    def test_13(self):
        x = sp.Function('x')
        y = sp.Function('y')
        t = sp.Symbol("t")
        theta = sp.Symbol("theta") 

        IA = IntegralAlgebra(order=[x(t),y(t)],
                            parameters=[theta])
        
        P = IntegralPolynomial(IM(1,x(t))-IM(y(t)))
        red_pow_2 = IA.reduced_power(P,2).get_sympy_repr() 
        
        expected = IM(y(t)**2) - 2*IM(1, x(t)*y(t))
        verify = sp.simplify(expected - red_pow_2) == 0 
 
        self.assertTrue(verify)

if __name__ == '__main__':
    unittest.main()