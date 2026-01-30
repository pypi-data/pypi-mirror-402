
import sympy as sp
from ordered_set import OrderedSet


from .IntegralPolynomial import IntegralPolynomial
from .utils import expr_has_symbols


def get_IO_equations(T: OrderedSet[IntegralPolynomial],
                    X_prime: list[sp.Function],
                    unknowns: list[sp.Function]):
        """
        unknowns are the unknowns function without the exponentials
        example : 
        T = {
        IntegralPolynomial(-x0*y0*IM(1, u1(t)*u2(t)) - y0*IM(1) + y0*IM(u2(t)))
        IntegralPolynomial(-x0*IM(u1(t)) + IM(x(t)))
        IntegralPolynomial(-y0*IM(u2(t)) + IM(y(t)))
        IntegralPolynomial(x0*IM(1, u1(t)) + x0*IM(1)/theta - x0*IM(u1(t))/theta)
        }
        X_prime = [x(t), y(t), u2(t), v2(t), u1(t), v1(t)]
        unknowns = [x(t)]

        return :
        I = {
        IntegralPolynomial(-x0*y0*IM(1, u1(t)*u2(t)) - y0*IM(1) + y0*IM(u2(t)))
        IntegralPolynomial(-y0*IM(u2(t)) + IM(y(t)))
        IntegralPolynomial(x0*IM(1, u1(t)) + x0*IM(1)/theta - x0*IM(u1(t))/theta)
        }
        """
        if len(unknowns) == 0:
            return T
        i = 0
        M = X_prime[i]
        while (i < len(X_prime)) and (M != unknowns[-1]):
            i+=1
            M = X_prime[i]
        idx_last_unk = i 
        
        new_unknows = X_prime[:idx_last_unk+1]

        I = []
        for eq in T:
            if not expr_has_symbols(eq.get_sympy_repr(), new_unknows):
                I += [eq]
        return I


def convert_IO_equation(eq)->sp.Expr:
    """
    convert an IntegralPolynomial to integral repr if needed
    """
    if isinstance(eq, IntegralPolynomial):
        return eq.get_integral_repr()
    else: 
        return eq

def convert_IO_equations(T)->OrderedSet[sp.Expr]:
    """
    convert a list of IntegralPolynomial to integral repr if needed
    """
    T_conv = []
    for eq in T: 
        T_conv += [convert_IO_equation(eq)]
    return T_conv

def replace_exp_in_IO_eqs(
        E: OrderedSet[sp.Function, sp.Function, IntegralPolynomial],
        I: list[IntegralPolynomial]) -> list[sp.Expr]:
    """
    example: 
    E = {
        (u1(t), v1(t), IntegralPolynomial(theta*IM(1, 1)))
        (u2(t), v2(t), IntegralPolynomial(-x0*IM(1)/theta + x0*IM(u1(t))/theta))
    }
    I = {
        IntegralPolynomial(-x0*y0*IM(1, u1(t)*u2(t)) - y0*IM(1) + y0*IM(u2(t)))
        IntegralPolynomial(-y0*IM(u2(t)) + IM(y(t)))
        IntegralPolynomial(x0*IM(1, u1(t)) + x0*IM(1)/theta - x0*IM(u1(t))/theta)
    }

    return : 
    I_exp = {
        -x0*y0*Integral(exp(theta*Integral(1, t))*exp(x0*exp(theta*Integral(1, t))/theta - x0/theta), t) + y0*exp(x0*exp(theta*Integral(1, t))/theta - x0/theta) - y0
        -y0*exp(x0*exp(theta*Integral(1, t))/theta - x0/theta) + y(t)
        x0*Integral(exp(theta*Integral(1, t)), t) - x0*exp(theta*Integral(1, t))/theta + x0/theta
    }
    """
    I_exp = [replace_exp_in_IO_eq(E, eq) for eq in I] 
    return I_exp


def replace_ln_in_IO_eqs(
        L: OrderedSet[sp.Function, IntegralPolynomial],
        I: list[IntegralPolynomial]) -> list[sp.Expr]: 
    L_ln = [replace_ln_in_IO_eq(L, eq) for eq in I] 
    return L_ln



def replace_exp_in_IO_eq(
        E: OrderedSet[sp.Function, sp.Function, IntegralPolynomial],
        eq: IntegralPolynomial) -> sp.Expr:
    eq = convert_IO_equation(eq)
    eq_subs = eq
    for (u,v,IntG) in reversed(E):
        IntG = IntG.get_integral_repr()
    
        eq_subs = eq_subs.subs({u: sp.exp(IntG),
                                v: sp.exp(-IntG)})
    return eq_subs

def replace_ln_in_IO_eq(
        L: OrderedSet[sp.Function, IntegralPolynomial],
        eq: IntegralPolynomial) -> sp.Expr: 
    eq = convert_IO_equation(eq)
    eq_subs = eq
    for (li, AdivA0) in reversed(L):
        AdivA0 = AdivA0.get_integral_repr()
    
        eq_subs = eq_subs.subs({li: sp.ln(AdivA0)})
    return eq_subs

def replace_new_variables_IO_eqs(E, L, I):
    list_of_allnew_variables = [elem[0] for elem in E] + \
                               [elem[1] for elem in E] + \
                               [elem[0] for elem in L]
    I_subs = []
    for eq in I:
        eq = convert_IO_equation(eq)
        while expr_has_symbols(eq,list_of_allnew_variables):
            eq = replace_ln_in_IO_eq(L,eq)
            eq = replace_exp_in_IO_eq(E,eq) 
        I_subs += [eq]
    return I_subs


def change_integral_bounds(expr: sp.Expr,
                           bound):
    """
    bound can be a symbol or a tuple
    example: change sp.Integral(x(t),t) to sp.Integral(x(t),(t,0,t))
            the inverse is also possible using bound = t
    """ 
    if len(expr.args) == 0:
        return expr
    elif expr.func == sp.Integral:
        new_arg = change_integral_bounds(expr.args[0], bound)
        return sp.Integral(new_arg, bound)
    else:
        new_args = [change_integral_bounds(arg,bound) for arg in expr.args] 
        new_fn = expr.func(*new_args)
        return new_fn


def simplify_IO_equations(I: list[sp.Expr],
                        order: list[sp.Function],
                        parameters: list[sp.Symbol]) -> list[sp.Expr]:
    
    t = sp.Symbol("t")
    I_bounds  = [change_integral_bounds(eq, (t,0,t)) for eq in I]
    params_subs = {
        p: sp.Symbol(str(p), nonzero=True, real=True) 
            for p in parameters
        }
    ci_subs = { 
        sp.Symbol(f"{m.func}0"): sp.Symbol(f"{m.func}0", 
                                           nonzero=True, 
                                           real=True) 
        for m in order
        }
    subs_dict = params_subs | ci_subs
    I_simp = [sp.simplify(eq.subs(subs_dict).doit()) for eq in I_bounds]
    I_simp = [change_integral_bounds(eq, t) for eq in I_simp]
    return I_simp