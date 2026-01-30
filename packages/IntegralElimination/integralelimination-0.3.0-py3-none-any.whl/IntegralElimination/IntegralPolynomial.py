import sympy as sp
import sympy.printing as printing
 
from .IntegralMonomial import IM
from .utils import is_float  


def task_simplify_coeff(M_coeff, cache_expand_coeff):
    try:
        M,coeff = M_coeff 
        if coeff not in cache_expand_coeff:  
            cache_expand_coeff[coeff] = sp.cancel(coeff)   
        expanded_coeff = cache_expand_coeff[coeff]
        return (M,expanded_coeff) 
    except: 
        raise RuntimeError

def init_coeff_dict(P, cache_expand_coeff={}, simplify_coeff=True):
    """
    P is a dict, a tuple, zero or a sp.Expr
    """
    if type(P) == dict or type(P)==tuple:
        tmp = {} 
        P=dict(P) 
        if simplify_coeff:   
            # args = [(M_coeff, cache_expand_coeff) for M_coeff in P.items()]
            # with ThreadPoolExecutor() as executor:
            #     res = executor.map(task_simplify_coeff, *zip(*args))   

            # sequential
            res = [task_simplify_coeff(
                    M_coeff,cache_expand_coeff) for M_coeff in P.items()] 

            for M, simplified_coeff in res:
                if simplified_coeff != 0:
                    tmp[M] = simplified_coeff
            
        else:
            tmp = P
    elif P == 0:
        tmp = {}
    elif type(P)==IM:
        tmp = {P:1}
    elif isinstance(P, sp.Expr):
        assert P.has(IM) 
        tmp = dict(P.as_coefficients_dict(IM))
    else:
        raise SyntaxError
    return tuple(tmp.items())


class IntegralPolynomial(): 
    # the cache is used to have the same id for two 
    # IntegralPolynomial that have the same content
    _cache = {} 
    _cache_expand_coeff = {}

    def __new__(cls, P, simplify_coeff=True): 
        """
        the cache system allow the check if a polynomial is in a set
        since the id of two integral polynomials with the same content
        will be the same
        """
        tmp = init_coeff_dict(P, 
                IntegralPolynomial._cache_expand_coeff, 
                simplify_coeff
        ) 
 
        # Check the cache to see if we already have this content
        if tmp in cls._cache:
            return cls._cache[tmp]

        # Create a new instance and cache it
        instance = super().__new__(cls)
        cls._cache[tmp] = instance
        return instance

    def __init__(self, 
                P,  
                simplify_coeff=True):  
        
        # Skip initialization if the instance is already initialized
        if hasattr(self, 'content'):
            return
        
        tmp = init_coeff_dict(P,
                IntegralPolynomial._cache_expand_coeff, 
                simplify_coeff
        )  
        self.content = tmp

    def get_content(self):
        """
        return an iterrable such that each item is a tuple (M,coeff)
        """
        return self.content

    def get_content_as_dict(self):
        return dict(self.get_content())


    def get_sympy_repr(self):
        """
        example : 
        a = IntegralPolynomial(IM(x(t))+theta*IM(1,x(t)))
        b = a.get_sympy(repr)
        print(b)
        print(type(b))
        >>> IM(x(t))+theta*IM(1,x(t))
        >>> type(sp.Expr)
        """
        L = self.get_content()
        sympy_repr = sp.Add(*[coeff*M for M,coeff in L]) 
        return sympy_repr
    
    def get_integral_repr(self):
        """ 
        example : 
        a = IntegralPolynomial(IM(x(t))+theta*IM(1,x(t)))
        b = a.get_sympy(repr)
        print(b)
        print(type(b))
        >>> x(t) + theta*int(x(t),t)
        >>> type(sp.Expr)
        """
        L = self.get_content()
        int_repr = sp.Add(*[sp.Mul(coeff,M.get_integral_repr()) for M,coeff in L]) 
        return int_repr
    
    def is_zero(self):
        return len(self.get_content()) ==0
    
    def __repr__(self):
        return f"IntegralPolynomial({self.get_sympy_repr()})"
    
    def repr_display_math(self):
        return '{}'.format(printing.latex(self.get_sympy_repr()))

    def _repr_latex_(self):  
        return '${}$'.format(printing.latex(self.get_sympy_repr()))
     
    def cut_P(self, cut_type: str):
        """
        Definition 8
        We simply extend the cut method of the Integral Monomial class to 
        integral polynomials 
        
        Disclaimer: this method will throw an error if you use it on 
        polynomial that can't be cutted 
        for exemple, trying to cut a pol with monomials of depth < 2 will 
        throw an error if you cut using i2+
        """
        P_cutted = {}
        L = self.get_content()
        for M,coeff in L:
            M_cutted = M.cut(cut_type) 
            if P_cutted.get(M_cutted) is None:
                P_cutted[M_cutted] = coeff 
            else:
                P_cutted[M_cutted] += coeff 
        return IntegralPolynomial(P_cutted)

    def get_P_I(self): 
        P_I = {}
        L = self.get_content()
        for M,coeff in L:
            M0 = M.cut("0") 
            if M.get_nb_int() >= 1 and M0 == IM(1):
                if M not in P_I:
                    P_I[M] = coeff
                else:
                    # we are not supposed to have this case
                    raise ValueError 
        # we avoid the simplification process of the coeffs
        # by using simplify_coeff=False
        return  IntegralPolynomial(P_I, simplify_coeff=False)

    def get_P_N(self): 
        P_N = {}
        L = self.get_content()
        for M,coeff in L: 
            M0 = M.cut("0")
            if M==IM(1): #cst
                P_N[M] = coeff
            elif M0 != IM(1):
                if M not in P_N:
                    P_N[M] = coeff
                else:
                    # we are not supposed to have this case
                    raise ValueError 
        # we avoid the simplification process of the coeffs
        # by using simplify_coeff=False
        return  IntegralPolynomial(P_N, simplify_coeff=False)
    
    def get_cst_terms(self):
        CST = {}
        L = self.get_content()
        for M,coeff in L:
            if M == IM(1):
                if M in CST:
                    CST[M] += coeff 
                else:
                    CST[M] = coeff 
        return  IntegralPolynomial(CST)
    
    def get_time_dependant_functions(self):
        """
        example: if you have 
        P = IntegralPolynomial(IM(x(t)) - x(0)*IM(1) 
                        - theta*IM(1,x(t)*y(t)**2) - IM(1,y(t)))
        it will return {x,y}
        """
        res = set()
        for f in self.get_sympy_repr().atoms(sp.Function):
            if f.func != IM and not is_float(f.args[0]):
                res.add(f) 
        return res