import sympy as sp
import unittest
from IntegralElimination import *
from IntegralElimination.reduction import reduction_M_by_P_simple_case

class TestIntegralElimination(unittest.TestCase):
    def test_14(self):
        x = sp.Function('x')
        y = sp.Function('y')
        t = sp.Symbol("t")
        theta = sp.Symbol("theta") 

        IA = IntegralAlgebra(order=[x(t),y(t)],
                            parameters=[theta])
        
        #is lm(P) is a monomial (not integral)
        P = IntegralPolynomial(IM(x(t))-IM(y(t)))
        M = IM(x(t)**2, y(t),x(t)*y(t))
        R = reduction_M_by_P_simple_case(IA,M,P)[1].get_sympy_repr()
        expected = IM(x(t)*y(t), y(t), x(t)*y(t))
        verify = sp.simplify(expected - R) == 0 
        self.assertTrue(verify) 

        #other case test 1 : M can't be reduced by p
        P = IntegralPolynomial(IM(1,x(t)*y(t))-IM(y(t)))   
        M = IM(x(t)**2, y(t),x(t)*y(t))
        R = reduction_M_by_P_simple_case(IA,M,P)[1]
        # using the anti fusion, you find N = x^2int(y(t))
        # lm(P)*N = x^2 int (y int (xy)) + x^2 int (xy int (y))
        # the leader is x^2 int (y int (xy)), which allow the reduction of M
        expected = IntegralPolynomial(
            IM(x(t)**2*y(t),y(t)) - IM(x(t)**2,x(t)*y(t),y(t))
        ) 
        verify = IA.polynomials_subtraction(R,expected).is_zero() 
        self.assertTrue(verify)

        #other case test 2
        P = IntegralPolynomial(IM(1,x(t)*y(t))-IM(y(t)))   
        M = IM(x(t)**2,x(t)*y(t))
        R = reduction_M_by_P_simple_case(IA,M,P)[1].get_sympy_repr()
        expected = IM(x(t)**2*y(t))
        verify = sp.simplify(expected - R) == 0 
        self.assertTrue(verify) 

        #last test
        P = IntegralPolynomial(IM(1,x(t)*y(t))-IM(y(t)))   
        M = IM(1,x(t)*y(t))
        R = reduction_M_by_P_simple_case(IA,M,P)[1].get_sympy_repr()
        expected = IM(y(t))
        verify = sp.simplify(expected - R) == 0 
        self.assertTrue(verify) 

if __name__ == '__main__':
    unittest.main()