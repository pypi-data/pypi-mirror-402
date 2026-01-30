import sympy as sp
import unittest
from IntegralElimination import *
from IntegralElimination.reduction import reduction_M_by_P_red_power_and_half_red_product

class TestIntegralElimination(unittest.TestCase):
    def test_15(self):
        x = sp.Function('x')
        y = sp.Function('y')
        t = sp.Symbol("t")
        theta = sp.Symbol("theta") 

        IA = IntegralAlgebra(order=[x(t),y(t)],
                            parameters=[theta])
        
        #is lm(P) is a monomial (not integral)
        P = IntegralPolynomial(IM(x(t))-IM(y(t)))
        M = IM(x(t)**2, y(t),x(t)*y(t))
        res = reduction_M_by_P_red_power_and_half_red_product(IA,M,P) 
        expected = None
        verify = expected == res
        self.assertTrue(verify) 

        # other test
        P = IntegralPolynomial(IM(1,x(t)*y(t))-IM(y(t)))   
        M = IM(x(t)**2, x(t)*y(t)**2)
        R = reduction_M_by_P_red_power_and_half_red_product(
                                    IA,M,P)[1].get_sympy_repr()
        expected = IM(x(t)**2*y(t)**2)/2
        verify = sp.simplify(expected - R) == 0 
        self.assertTrue(verify)

        # other test
        P = IntegralPolynomial(IM(1,x(t)*y(t),y(t))-IM(y(t)))   
        M = IM(x(t)**2, x(t)*y(t)**2)
        res = reduction_M_by_P_red_power_and_half_red_product(IA,M,P)
        expected = None
        verify = expected == res
        self.assertTrue(verify)

if __name__ == '__main__':
    unittest.main()