from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .IntegralAlgebra import IntegralAlgebra
 
import sympy as sp
from ordered_set import OrderedSet

from .IntegralMonomial import IM
from .IntegralPolynomial import IntegralPolynomial 
from .utils import (
    expr_has_symbols
)

def find_A_A0_G_F(IA: IntegralAlgebra,
                    P:IntegralPolynomial) -> tuple[IntegralPolynomial]:
    """
    This algorithm 
    takes an integral polynomial P
    and tries to write it in the form
    P = A - (A_0 + int{ A · G + F })$
    where 
    A_0 is a constant, 
    A,G,F are integral polynomials,
    A and G are nonzero.
    """
    #try to write P as A − (A0 +int Q)
    P_N = P.get_P_N()
    CST = P.get_cst_terms()
    A = IA.polynomials_subtraction(P_N ,CST)
    A0 = IA.product_P_Coeff(CST,-1)
    P_I = P.get_P_I()
    Q = IA.product_P_Coeff(P_I.cut_P("1+"),-1) 

    # check that A != 0
    if A.is_zero(): return None
    # and check that A is in K[X]  
    # TODO : this constraint can be removed but the computations are much slower
    if any([M.get_nb_int() for M,_ in A.get_content()]): 
        return None
    
    # we want that reduce(Q,A) returns W=[(g0,A),...(gn,A), (h0,h1,A),(..,..,..,..,A)] and R
    W, R = IA.reduce(Q, [A], compute_W=True, reduce_LM_only=False)
    # G is a list of tuple of 2 elements where sum(g_i) = G
    # i.e. we filter each tuple of W and we only keep the tuples of two elements
    # the rest (i.e. polynomials of the forme h0*int(h1*...int(hn*A))) is added to R to obtain F
  

    G = IntegralPolynomial(0)
    F = R
    for elem in W:
        if len(elem)==2:
            gi,_ = elem
            G = IA.polynomials_add(G,gi)
        else:
            # Fi = hn*A  where hn=elem[-2] and A=elem[-1]
            Fi = IA.polynomials_product(elem[-2],elem[-1])
            for pol in reversed(elem[:-2]):
                # Fi = int(Fi)*pol
                Fi = IA.polynomials_product(IA.integrate_polynomial(Fi),
                                        pol) 
            # at this step, Fi = h0*int(h1*int(...*int(hn*A)))
            F = IA.polynomials_add(F,Fi) 
 

    if G.is_zero(): 
        return None
    
    # check that P = A-(A0+\int (AG+F))
    # going from right to left :
    temp = IA.polynomials_product(A,G)
    temp = IA.integrate_polynomial(IA.polynomials_add(temp,F))
    temp = IA.polynomials_add(A0, temp)
    temp = IA.polynomials_subtraction(A,temp)
    assert sp.simplify(P.get_sympy_repr() - temp.get_sympy_repr()) == 0
    return (A,A0,G,F)



def update_exp(IA: IntegralAlgebra,
                T_prime: OrderedSet[IntegralPolynomial],
                E: OrderedSet[sp.Function, sp.Function, IntegralPolynomial],
                reduce_LM_only:bool=True
                ) -> tuple:
    """
    When find_A_A0_G_F succeeds,
    a new polynomial A - (AA_0 u + u int{ vF }) can be introduced
    where u and v are new indeterminates encoding 
    u = e^{int{G}} and 
    v = e^{-int{G}}.
    """
    T_E = OrderedSet()
    E_prime = OrderedSet([elem for elem in E])
    t = IA.t 
    for P in T_prime:
        temp = IA.find_A_A0_G_F(P)
        if temp != None:
            A, A0, G, F = temp
            int_G = IA.integrate_polynomial(G)

            # this allow to not introduce an encoding of an exp
            # that is already in E_prime 
            _,int_G = IA.reduce(int_G, T_prime,
                                reduce_LM_only=reduce_LM_only,
                                compute_W=False) 
            
            # check that int G != from all Q_i in Eprime
            check = [
                    IA.polynomials_subtraction(int_G, Q_i).is_zero() 
                    for _, _, Q_i in E_prime
                    ]

            if F.is_zero():
                pass #divide instead of exp ?
            
            if not any(check):
                k = len(E_prime) + 1
                uk = sp.Function(f"u{k}")
                vk = sp.Function(f"v{k}")
                new_item = (uk(t), vk(t), int_G)
                E_prime.add(new_item)
                uk_pol = IntegralPolynomial(IM(uk(t)))
                vk_pol = IntegralPolynomial(IM(vk(t)))
            else: 
                index_True_in_check = [ 
                                        i for i in range(len(check)) 
                                        if check[i] is True
                                      ][0]
                uk,vk,_ = list(E_prime)[index_True_in_check]
                uk_pol = IntegralPolynomial(IM(uk))
                vk_pol = IntegralPolynomial(IM(vk))
            # then, we compute P_exp = A - (A0 u_k + u_k \int (v_k F))
            # from right to left 
            temp = IA.integrate_polynomial(IA.polynomials_product(vk_pol, F))
            temp = IA.polynomials_product(uk_pol,temp)
            temp = IA.polynomials_add(IA.polynomials_product(A0,uk_pol), temp)
            P_exp = IA.polynomials_subtraction(A, temp)
            if not P_exp.is_zero():
                T_E.add(P_exp)

    return T_E, E_prime


def update_log(IA: IntegralAlgebra,
                T_prime: OrderedSet[IntegralPolynomial],
                L: OrderedSet[sp.Function, IntegralPolynomial],
                reduce_LM_only:bool=True
                ) -> tuple:
    """
    When find_A_A0_G_F succeeds,
    a new polynomial l-int{G} can be introduced
    where l is a new indeterminates encoding 
    l = ln{A/A_0}.
    """
    T_L = OrderedSet()
    L_prime = OrderedSet([elem for elem in L])
    t = IA.t 
    for P in T_prime:
        temp = IA.find_A_A0_G_F(P)
        if temp != None:
            A, A0, G, F = temp 
            if F.is_zero():
                assert len(A0.get_content()) == 1
                A0_val = A0.get_content()[0][1]
                A_div_A0 = IA.product_P_Coeff(A,1/A0_val)
 
                # this allow to not introduce an encoding of an exp
                # that is already in E_prime 
                _,A_div_A0_red = IA.reduce(A_div_A0, 
                                    T_prime,
                                    reduce_LM_only=reduce_LM_only,
                                    compute_W=False)
                
                # check that A != from all Q_i in Lprime
                check = [
                        IA.polynomials_subtraction(A_div_A0_red, Q_i).is_zero() 
                        for _, Q_i in L_prime
                        ]
                
                
                if not any(check):
                    k = len(L_prime) + 1
                    lk = sp.Function(f"l{k}") 
                    new_item = (lk(t), A_div_A0_red)
                    L_prime.add(new_item)
                    lk_pol = IntegralPolynomial(IM(lk(t))) 
                else: 
                    index_True_in_check = [ 
                                            i for i in range(len(check)) 
                                            if check[i] is True
                                        ][0]
                    lk,_ = list(L_prime)[index_True_in_check]
                    lk_pol = IntegralPolynomial(IM(lk)) 
                # then, we compute 
                # P_log  =  ln(A/A0) - int(G)
                # from right to left
                int_G = IA.integrate_polynomial(G)
                P_log = IA.polynomials_subtraction(
                    lk_pol,
                    int_G
                )
                
                if not P_log.is_zero():
                    T_L.add(P_log)

    return T_L, L_prime
 

def extend_X_with_exp_and_log(IA: IntegralAlgebra,
                    E: OrderedSet[sp.Function, sp.Function, IntegralPolynomial],
                    L: OrderedSet[sp.Function, IntegralPolynomial]
                    ) -> list:
    """
    Algorithm 5
    Here, X is inside the IntegralAlgebra object (self.order)
    We will return a modified X and replace the self.used_order 
    after this function call to update self.compare_IM according to
    the new X'
    """ 
    X_prime = IA.order
    EL = E | L 
    all_funcs = set()
    for elem in EL:
        all_funcs = all_funcs | {*elem[:-1]}

    i=1 
    while len(EL) > 0:
        elem = EL.pop(0)
        #elem is (Func,Func,Pol) for exp or (Func, Pol) for log
        new_funcs, Qi = elem[:-1], elem[-1]
        if expr_has_symbols(Qi.get_sympy_repr(), X_prime):
            indeterminates = Qi.get_time_dependant_functions()
            greatest_inds = None

            #from left (greatest) to right
            for inds, k in zip(X_prime, range(len(X_prime))): 
                if inds in indeterminates:
                    greatest_inds = inds
                    X_prime = X_prime[:k] + [*new_funcs] + X_prime[k:]
                    break;
            assert greatest_inds is not None
        else:
            if expr_has_symbols(Qi.get_sympy_repr(), all_funcs):
                EL.add(elem)
            else:
                X_prime = X_prime + [*new_funcs]
 
        if i == 1000000:
            raise RuntimeError("infinite loop: cyclic graph")
        i+=1
    return X_prime