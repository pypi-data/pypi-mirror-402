import sympy as sp
from ordered_set import OrderedSet

from .utils import expr_has_symbol
from .IntegralMonomial import IM
from .IntegralPolynomial import IntegralPolynomial

def add_alpha_M(d, alpha, M):
        if M in d:
            new_coeff = sp.cancel(alpha + d[M])
            if new_coeff !=0:
                d[M] = new_coeff
            else:
                del d[M]
        else:
            d[M] = alpha

def first_order_ODE_to_IntegralPolynomial(
                                        expr:sp.Expr, 
                                        var=sp.Symbol("t"),
                                        use_symbol=False
                                        ) -> IntegralPolynomial:
        expr = sp.expand(expr)
        dict_coeff = dict(expr.as_coefficients_dict(var))
        res = {}
        if expr_has_symbol(expr, sp.Integral): raise ValueError
        expr_has_der = expr_has_symbol(expr,sp.Derivative)
        for mons, coeff in dict_coeff.items():
            if mons.func == sp.Derivative : 
                assert mons.args[1][1] == 1 
                m = mons.args[0]
                if use_symbol:
                    IC = sp.Symbol(f"{m.func}0")
                else:
                    IC = m.func(0)
                M = IM(m)
                add_alpha_M(res,coeff,M)
                add_alpha_M(res,-IC,IM(1)) 
            else:
                if expr_has_der:
                    M = IM(1,mons) 
                    add_alpha_M(res,coeff,M)
                else:
                    M = IM(mons)
                    add_alpha_M(res,coeff,M)
        return IntegralPolynomial(res)

def ODE_sys_to_Integral_sys(sys: list[sp.Expr]
                            ) -> OrderedSet[IntegralPolynomial]:
    sys = OrderedSet([first_order_ODE_to_IntegralPolynomial(eq) for eq in sys])
    return  sys