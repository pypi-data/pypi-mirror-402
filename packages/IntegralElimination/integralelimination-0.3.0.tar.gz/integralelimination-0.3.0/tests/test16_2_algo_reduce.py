import sympy as sp
import unittest
from IntegralElimination import *
from ordered_set import OrderedSet

class TestIntegralElimination(unittest.TestCase):
    def test_16(self):
        x = sp.Function('x')
        y = sp.Function('y')
        t = sp.Symbol("t")
        theta = sp.Symbol("theta") 

        x0,y0 = sp.symbols("x0 y0")
        theta = sp.Symbol("theta")
        A = IntegralAlgebra(order=[x(t),y(t)],
                            parameters=[theta,x0,y0])
        P1 = IntegralPolynomial(IM(x(t))-x0*IM(1) - IM(1,y(t)))
        P2 = IntegralPolynomial(IM(y(t))-y0*IM(1) - theta*IM(1,x(t)**2))
        T = OrderedSet([P1,P2]) 
        T_red = A.auto_reduce(T)
        T_red = set([P.get_sympy_repr() for P in T_red])
        expected_sys = {-x0*IM(1) + IM(x(t)) - IM(1, y(t)), 
                        -theta*x0**2*IM(1, 1) - 2*theta*x0*IM(1, 1, y(t)) \
                        - 2*theta*IM(1, 1, y(t), y(t)) - y0*IM(1) + IM(y(t))}
        verify = len(T_red - expected_sys) == 0
        self.assertTrue(verify)

if __name__ == '__main__':
    unittest.main()