import sympy as sp
import unittest
from IntegralElimination import *

class TestIntegralElimination(unittest.TestCase):
    def test_12(self):
        x = sp.Function('x')
        y = sp.Function('y')
        t = sp.Symbol("t")
        theta = sp.Symbol("theta") 

        IA = IntegralAlgebra(order=[x(t),y(t)],
                            parameters=[theta])
        
        P = IntegralPolynomial(IM(1,x(t))-IM(y(t)))
        pow_0 = IA.polynomial_power(P,0).get_sympy_repr()
        pow_2 = IA.polynomial_power(P,2).get_sympy_repr()
        
        expected = IM(y(t)**2) - 2*IM(y(t), x(t)) + 2*IM(1, x(t), x(t))
        verify_pow_2 = sp.simplify(expected - pow_2) == 0
        verify_pow_0 = sp.simplify(IM(1) - pow_0) == 0
 
        self.assertTrue(verify_pow_2 and verify_pow_0)

if __name__ == '__main__':
    unittest.main()