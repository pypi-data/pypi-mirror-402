import sympy as sp
import unittest
from IntegralElimination import *

class TestIntegralElimination(unittest.TestCase):
    def test_04(self):
        x = sp.Function('x')
        y = sp.Function('y')
        t = sp.Symbol("t")
        theta = sp.Symbol("theta")
        P = IntegralPolynomial(3*IM(x(t))+theta*IM(y(t),1,y(t))+theta*IM(1,1,y(t)))
        IA = IntegralAlgebra(order=[x(t),y(t)],
                            parameters=[theta])
        
        LM, LC = IA.LM_LC(P) 
        self.assertEqual((LM, LC), (IM(x(t)),3))


if __name__ == '__main__':
    unittest.main()