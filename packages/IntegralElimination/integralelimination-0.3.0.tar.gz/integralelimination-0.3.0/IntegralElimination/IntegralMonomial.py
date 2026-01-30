import sympy as sp
from functools import lru_cache

from .utils import (
    has_add_in_list,
    is_float
)

def has_multiplicative_constant(expr): 
    """
    Search if expr has a multiplicative cst != than 1
    """ 
    if is_float(expr):
        if expr == 1:
            return False
        else:
            return True
    elif expr.is_Mul:
        factors = expr.as_ordered_factors() 
        for factor in factors:
            if factor.is_number and factor != 1:
                return True  
    return False


class IM(sp.Function):
    @lru_cache(None)  # Cache unlimited number of calls
    def __new__(cls, *args):
        obj = super(IM, cls).__new__(cls, *args)
        obj.c = args
        obj.t = sp.Symbol("t")
        assert "IM" not in str(obj.c)
        assert not has_add_in_list(obj.c)

        #check if parameters (symbols) are in self.c
        assert not any([
                        len(elem.free_symbols - {obj.t}) 
                        for elem in obj.c if not is_float(elem)
                       ])
        #check that every multiplicative csts are 1
        assert not any([
                        has_multiplicative_constant(elem) 
                        for elem in obj.c
                       ])
        return obj

    def get_nb_int(self):
        return len(self.c) - 1

    def get_content(self):
        return self.c
    
    def cut(self, cut_type):
        """
        See Definition 7 
        """
        if cut_type ==  "0":
            return IM(self.c[0])
        
        elif cut_type ==  "1":
            assert self.get_nb_int() >= 1
            return IM(self.c[1])
        
        elif cut_type ==  "1+":
            assert self.get_nb_int() >= 1
            return IM(*self.c[1:])
        
        elif cut_type ==  "i1+":
            if self.get_nb_int() == 0:
                return IM(1)
            else:
                return IM(1,*self.c[1:])
          
        elif cut_type == "i2+":
            if self.get_nb_int() == 1: 
                return IM(1)
            else:
                assert self.get_nb_int() >= 2
                return IM(1,*self.c[2:])
        else:
            raise NotImplementedError
        
    def get_suffix(self, i):
        assert 0 <= i <= self.get_nb_int()
        return IM(*self.get_content()[i:])
    
    def get_prefix(self, i):
        assert 0 <= i <= self.get_nb_int()
        return IM(*self.get_content()[:i])

    def add_prefix(self, M):
        prefixed_M = IM(*M.get_content(),*self.get_content())
        return prefixed_M

    def __str__(self):
        return f"IM({str(self.c)[1:-1]})"
    
    def get_integral_repr(self): 
        if len(self.c) > 1:
            expr = sp.Integral(self.c[-1], self.t)
            for e in reversed(self.c[1:-1]): 
                expr = (sp.Integral(e*expr, self.t))
            expr = self.c[0]*expr
        elif len(self.c) == 1:
            expr = self.c[0]
        return expr

    def _latex(self, printer=None):  
        return f"{printer.doprint(self.get_integral_repr())}"
    