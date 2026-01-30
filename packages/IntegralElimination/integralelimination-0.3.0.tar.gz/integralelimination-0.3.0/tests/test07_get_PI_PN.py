import sympy as sp
import unittest
from IntegralElimination import *

class TestIntegralElimination(unittest.TestCase):
    def test_07(self):
        x = sp.Function('x')
        y = sp.Function('y')
        t = sp.Symbol("t")
        theta = sp.Symbol("theta")
        P = IntegralPolynomial(3*IM(x(t))+theta*IM(y(t),1,y(t))+theta*IM(1,1,y(t))) 
        
         
        P_N = P.get_P_N().get_sympy_repr()
        P_I = P.get_P_I().get_sympy_repr()
 
        expected_P_N = 3*IM(x(t))+theta*IM(y(t),1,y(t))
        expected_P_I = theta*IM(1,1,y(t)) 

        verifiy_P_N = sp.simplify(expected_P_N-P_N) == 0
        verifiy_P_I = sp.simplify(expected_P_I-P_I) == 0
        
        self.assertTrue(verifiy_P_N and verifiy_P_I)

if __name__ == '__main__':
    unittest.main()