from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .IntegralAlgebra import IntegralAlgebra

import sympy as sp 
from ordered_set import OrderedSet

from .IntegralMonomial import IM
from .IntegralPolynomial import IntegralPolynomial 
from .utils import (
    is_int, 
)

from .check_conditions_LM import (
    check_condition_LM_half_reduced_product,
)


def reduction_M_by_P_simple_case(IA: IntegralAlgebra, 
                                 M: IM, 
                                 P: IntegralPolynomial,
                                 compute_W=True) -> tuple[list, IntegralPolynomial]:
    """
    Consider an integral monomial M
    and a nonzero integral polynomiaml P.
	
	If there exists an integral monomial 
    N such that lm{lm{P} · N}=M,
	then introduce
	R =  M-(1/l)P · N
	where l is the leading coefficient of P · N.

    This function returns a list W of "quotients"
    and the polynomial R 
    such that M = (sum of elements of the form (wi\int ... w_n P)) + R
    
    Here, the "sum of elements of the form (wi\int ... w_n P)" 
        is simply equal to (1/l)·N·P 
    Then, W = [ ((1/l)·N , P) ]
    """
    assert not P.is_zero() 

    LM_P,LC_P = IA.LM_LC(P)
    assert float(LC_P) == 1.0, "LC(P) should be normalized"

    N = IA.monomial_division(M,LM_P)
    if N == None:
        return None  
    
    PN = IA.polynomials_product(P,IntegralPolynomial(N))
    PN = IA.normalize_LC_of_P(PN)[0]
    
    assert M == IA.LM_LC(PN)[0]

    R = IA.polynomials_subtraction(
            IntegralPolynomial(M),
            PN
        ) 
    if not R.is_zero():
        LM_R = IA.LM_LC(R)[0]
        assert IA.compare_IM(LM_R,M)
    
    if not compute_W:
        W = []
        return W, R 
    W = [(IntegralPolynomial((1/LC_P)*N),P),] 
    return W, R
 

def reduction_M_by_P_red_power_and_half_red_product(
            IA: IntegralAlgebra, 
            M: IM, 
            P: IntegralPolynomial,
            compute_W=True) -> tuple[list, IntegralPolynomial]:
    """
    Consider an integral monomial M and an integral polynomial P
    with P_I != 0, P_N != 0, and lm{P} = lm{P_I}$.
    
    Assume there exists a positive integer n
    and an integral monomial N such that
    - lm{P_I}[1] lm{lm{P_N}[0]}^{n-1} = M[1],
    - lm{ (P_I[2+]) · (P_N[1+])^{n-1} · N } = M[2+],
    - N[0] = 1.

    If the condition
    of check_condition_LM_half_reduced_product
    (this function checks the condition)
    holds for P^{\reduced_power{n}} half-reduced-prod N,  
    then introduce
	R = M - (1/l) M[0](P^{reduced_power{n}} half-reduced-prod N )
	where
	l is the leading coefficient 
    of M[0](P^{reduced_power{n}} half-reduced-prod N ).

    This function returns a list W of "quotients"
    and the polynomial R 
    such that M = (sum of elements of the form (wi\int ... w_n P)) + R

    Here, we want to write (1/l) M[0](P^{reduced_power{n}} half-reduced-prod N )
    as a sum of elements of the form (wi\int ... w_n P).

    1. P^{reduced_power{n}}                     = d0·P + int( d1·P )
        where d0 = sum_{k=1}^{n} (-1)^{k-1} binom(n,k) P_N ^{n-k} P^{k-1}
              d1 = sum_{k=1}^{n} n binom(n-1,k) P_I]1+] P_N ^{n-k-1} P^{k-1}

    2. P^{reduced_power{n}} half-reduced-prod N = d0·P·N + int( (d1·N-N]1+·d0)·P )
    
    3.  (1/l) M[0](P^{reduced_power{n}} half-reduced-prod N ) = 
            (1/l) M[0] d0·P·N +  (1/l) M[0] int( (d1·N-N]1+·d0)·P )

    We encode 3. as the list W = [ (1/l M0 d0 N, P), ((1/l)M0, d1 N - N]1+ d0, P) ] 
    """
    assert not P.is_zero() 
    LM_P,LC_P = IA.LM_LC(P)
    assert float(LC_P) == 1.0, "LC(P) should be normalized"
    if M.get_nb_int() == 0 : # |M| >= 1
        return None
    P_I = P.get_P_I()
    if P_I.is_zero(): return None 
    LM_P_I,LC_P_I = IA.LM_LC(P_I)
    if LM_P_I != LM_P : # we want lm(P) = lm(P_I)
        return None
    P_N = P.get_P_N()
    if P_N.is_zero(): return None 
    LM_P_N,LC_P_N = IA.LM_LC(P_N)
    M_1 = M.cut("1").get_content()[0]
    LM_P_N_0 = LM_P_N.cut("0").get_content()[0]
    LM_P_I_1 = LM_P_I.cut("1").get_content()[0]

    # we try to find n such that (lm(PI)[1]*lm(PN)[0]**(n-1))/M[1] = 1
    n = sp.Symbol("n_pow")
    pow_dict = ((LM_P_I_1*LM_P_N_0**(n-1))/M_1).as_powers_dict()
    if len(pow_dict) > 1: 
        #for example :
        # expr = ((x(t)*a(t))**n*y(t))/(x(t)**2*y(t))
        # expr.as_powers_dict()
        # {a(t)x(t):n, x(t): -2}
        return None 
    sp_solved = sp.solve(list(pow_dict.values())[0])
    if len(sp_solved)==0: return None
    solved_n = sp_solved[0] 
    if not(is_int(solved_n) and solved_n > 0):
        return None
    #we then have to verify the condition:
    #lm( (lm(P_I)[2+]) cdot (lm(P_N)[1+])**(n-1)) = M[2+]
    LM_P_I_i2plus = IntegralPolynomial(LM_P_I.cut("i2+"))
    LM_P_N_i1plus = IntegralPolynomial(LM_P_N.cut("i1+"))
    LM_P_N_i1plus_pow = IA.polynomial_power(LM_P_N_i1plus,solved_n-1)
    pol = IA.polynomials_product(LM_P_I_i2plus, LM_P_N_i1plus_pow)
    
    Mi2_plus = M.cut("i2+")
    B_P, c_B_P = IA.LM_LC(pol)
    N = IA.monomial_division(Mi2_plus, B_P)
    if N is None or N.get_content()[0] != 1:
        return None
    
    # we compute the reduced power
    P_reduced_pow_n = IA.reduced_power(P,solved_n)
    # we verify the condition on N
    if not check_condition_LM_half_reduced_product(IA, P_reduced_pow_n, N):
        return None
    # we can now compute R
    P_reduced_pow_n_red_prod_N = IA.half_reduced_product(P_reduced_pow_n, N)
    
    M0 = IntegralPolynomial(M.cut("0"))
    M0_P_pow_n = IA.polynomials_product(P_reduced_pow_n_red_prod_N, M0)
    M0_P_pow_n_norm, LC_M0_P_pow_n = IA.normalize_LC_of_P(M0_P_pow_n)
      
    assert M == IA.LM_LC(M0_P_pow_n_norm)[0]
    R = IA.polynomials_subtraction(IntegralPolynomial(M), 
                                  M0_P_pow_n_norm)
    if not R.is_zero():
        LM_R = IA.LM_LC(R)[0]
        assert IA.compare_IM(LM_R,M)

    if not compute_W:
        W = []
        return W, R 
    
    # we have M= 1/l M0 P^{circled(n)} half_red N + R
    # take H = 1/l M0 P^{circled(n)} halfred N 
    # here, H is equal to 1/l * M0( d0 N P + \int ((d1 N - N]1+ d0)P) )
    # with d0 and d1 defined as follows: 
    d0 = IntegralPolynomial(0)
    d1 = IntegralPolynomial(0) 
    for k in range(1,solved_n+1):  
        d0 = IA.polynomials_add(d0,  
                IA.product_P_Coeff( 
                    IA.polynomials_product(
                        IA.polynomial_power(P_N,solved_n-k),
                        IA.polynomial_power(P,k-1)
                    ),
                    (-1)**(k-1)*sp.binomial(solved_n,k)
                )
            )
                             
        d1 = IA.polynomials_add(d1,  
                IA.product_P_Coeff( 
                    IA.polynomials_product(
                        IA.polynomials_product(
                            IA.polynomial_power(P_N,solved_n-k-1),
                            IA.polynomial_power(P,k-1)
                        ),
                        P_I.cut_P("1+")
                    ),
                    solved_n*(-1)**(k-1)*sp.binomial(solved_n-1,k)
                )
            )
    # we want to return
    # W = [ (1/l M0 d0 N, P), ((1/l)M0, d1 N - N]1+ d0, P) ] 
    if N==IM(1): N1p = 0
    else : N1p = N.cut("1+")

    W0 = (IA.product_P_Coeff(
                    IA.polynomials_product(
                        IA.polynomials_product(M0, d0),
                                IntegralPolynomial(N)
                    ), 
                    1/LC_M0_P_pow_n),
            P,
        )

    W1 = (IA.product_P_Coeff(M0, 1/LC_M0_P_pow_n), 
            IA.polynomials_subtraction(
                IA.polynomials_product(d1,IntegralPolynomial(N)),
                IA.polynomials_product(d0,IntegralPolynomial(N1p))
            ),
            P,
        )
    W = [W0,W1] 
    return W, R 

def reduction_M_by_P(IA: IntegralAlgebra, 
                     M: IM, 
                     P: IntegralPolynomial,
                     compute_W=True
                    ) -> tuple[list, IntegralPolynomial]:
    """
    Lemma 14
    
    W is obtained by adding the prefix to the previous list 
        W = [ ((1/l)·N , P) ]
        or
        W = [ (1/l M0 d0 N, P), ((1/l)M0, d1 N - N]1+ d0, P) ] 
    computed by reduction_M_by_P_simple_case or reduction_M_by_P_red_power_and_half_red_product.
    See the functions add_prefix_to_quotients and mult_quotients_by_coeff.
    """
    assert not P.is_zero() 
    e = M.get_nb_int() 
    P_norm, LC_P = IA.normalize_LC_of_P(P)  
    for i in reversed(range(e+1)): 
        prefix = M.get_prefix(i)
        suffix = M.get_suffix(i)   
        res = reduction_M_by_P_simple_case(IA,
                    suffix, P_norm, compute_W=compute_W)  
        if res is not None:
            W, R = res 
            R = IA.add_prefix_to_polynomial(prefix, R) 
            W = add_prefix_to_quotients(IA, prefix, W)  
            W = mult_quotients_by_coeff(IA, W, 1/LC_P) 
            W = [(*elem[:-1],P,)  for elem in W] 
            if not R.is_zero():
                LM_R = IA.LM_LC(R)[0]
                assert IA.compare_IM(LM_R,M)
            return W, R
        res = reduction_M_by_P_red_power_and_half_red_product(IA,
                    suffix, P_norm, compute_W=compute_W) 
        if res is not None:
            W, R = res
            R = IA.add_prefix_to_polynomial(prefix,R) 
            W = add_prefix_to_quotients(IA, prefix, W) 
            W = mult_quotients_by_coeff(IA, W, 1/LC_P) 
            W = [(*elem[:-1],P,) for elem in W]
            if not R.is_zero():
                LM_R = IA.LM_LC(R)[0]
                assert IA.compare_IM(LM_R,M)
            return W, R 
    return None

def reduce_LM(IA:IntegralAlgebra, 
           Q:IntegralPolynomial, 
           T:OrderedSet[IntegralPolynomial],
           compute_W:bool=True,
           W=None) -> tuple[list, IntegralPolynomial]:
    """
    reduce Q by the set of integral polynomials T
    until the LM cannot be reduced

      >>> i.e. this functions computes R
    and the list W of "quotients" such that 
    Q = sum(integral polynomials which uses elements of W) + R

    /!\ R is not the necessarly the normal form of Q w.r.t T
    """ 
    if W is None:
        W = []
    if Q.is_zero(): 
        return W, IntegralPolynomial(0)
    A = Q 

    LM_A,LC_A = IA.LM_LC(A)
    # test if LM can be reduced by a polynomial P of T
    if IA.storage["P_red_to_zero"].get(A):
        return IA.storage["P_red_to_zero"]
    for P in T:  
        res = reduction_M_by_P(IA, LM_A, P,compute_W)  
        # raise NotImplementedError("TODO fix W!")
        if res is not None: 
            Wi, Ri = res 
            Wi = mult_quotients_by_coeff(IA,Wi,LC_A)

            # A=lc_A*lm(A)+B, i.e B is the tail, so we can just delete the leading 
            # monomial of A to obtain B=tail_A
            tail_A = A.get_content_as_dict()
            del tail_A[LM_A]

            # lm(A) has been reduced by P 
            # i.e. lm(A) = ... + Ri
            # and thus lc_A*lm(A) = lc_A*... + lc_A*Ri 
            LC_A_Ri = IA.product_P_Coeff(Ri, LC_A, return_dict=True)
            # A reduced by P:
            # A = ... + R, where R = tail_A+lc_A Ri
            R = IA.polynomials_add(tail_A, LC_A_Ri, return_dict=False)   
            W += Wi
            if R.is_zero():
                return W, R
            return reduce_LM(IA, R, T, compute_W=compute_W, W=W) 
    if A.is_zero():
        IA.storage["P_red_to_zero"][A] = IntegralPolynomial(0)
    return W, A

def reduce_full(IA:IntegralAlgebra, 
           Q:IntegralPolynomial, 
           T:OrderedSet[IntegralPolynomial],
           compute_W:bool=True,
           W=None) -> tuple[list, IntegralPolynomial]:
    """
    reduce Q by the set of integral polynomials T
    until until there are no more possible reductions

    >>> i.e. this functions computes the normal form R
    and the list W of "quotients" such that 
    Q = sum(integral polynomials which uses elements of W) + R
    """ 
    if W is None:
        W = []
    if Q.is_zero(): 
        return W, IntegralPolynomial(0)
    A = Q 
    if IA.storage["P_red_to_zero"].get(A):
        W, pol = IA.storage["P_red_to_zero"][A]
        return W, pol, True
    for Mi, alpha in A.get_content(): 
        for P in T:  
            res = reduction_M_by_P(IA,Mi,P,compute_W=compute_W) 
            if res is not None:
                Wi, Ri = res 
                Wi = mult_quotients_by_coeff(IA,Wi,alpha)
                Ri = IA.product_P_Coeff(Ri,alpha)
                tail_A = A.get_content_as_dict()
                del tail_A[Mi]
                tail_A = IntegralPolynomial(tail_A)
                R = IA.polynomials_add(tail_A, Ri)
                W += Wi 
                return reduce_full(IA, 
                            R, 
                            T,
                            compute_W=compute_W,
                            W=W,)
    if A.is_zero():
        IA.storage["P_red_to_zero"][A] = (W, IntegralPolynomial(0))
    return W, A

 

def reduce(IA:IntegralAlgebra, 
           Q:IntegralPolynomial, 
           T:OrderedSet[IntegralPolynomial],
           reduce_LM_only=True,
           compute_W=True) -> tuple[list,IntegralPolynomial]:
    """
    example: 
    * The list W = [(w0,P), (w1, w2,P)]
        encodes the integral polynomial
        w0*P + w1*int(w2*P)
    * Q = (w0*P + w1*int(w2*P)) + R
    * R corresponds to the polynomial Q reduced by the set T
    """
    if reduce_LM_only: 
        W,R = reduce_LM(IA, Q, T, compute_W=compute_W)
    else: 
        W,R = reduce_full(IA, Q, T, compute_W=compute_W) 
    return W, R



def __auto_reduce(IA:IntegralAlgebra, 
                T:OrderedSet[IntegralPolynomial],
                reduce_LM_only=True) -> tuple:
    T_reduced =  OrderedSet([])
    T_done = OrderedSet([]) 
    one_P_has_been_reduced = False
    for P in T:
        T_done.add(P) 
        T_copy = T - T_done | T_reduced 
        _, P_reduced = reduce(IA, P, T_copy, reduce_LM_only, compute_W=False)
        has_been_reduced = P_reduced != P  
        one_P_has_been_reduced = one_P_has_been_reduced or has_been_reduced 
        if not P_reduced.is_zero(): 
            T_reduced.add(P_reduced) 
        
    return T_reduced, one_P_has_been_reduced

def auto_reduce(IA:IntegralAlgebra, 
                T:OrderedSet[IntegralPolynomial],
                reduce_LM_only:bool=True,
                disable_deletion:bool=False
            ) -> OrderedSet[IntegralPolynomial]:
    T_reduced = T
    has_been_reduced = True 
    while has_been_reduced:  
        T_temp, has_been_reduced = __auto_reduce(IA,
                                                T_reduced,
                                                reduce_LM_only=reduce_LM_only) 
        T_reduced = T_temp  
    if disable_deletion:
        return T | T_reduced 
    else:
        return T_reduced
    






############################# 
# reduction utils functions #
#############################

def add_prefix_to_quotients(IA, prefix, W):
    """
    Example:
    The list W = [(w0,P), (w1, w2,P)]
        encodes the integral polynomial
        w0*P + w1*int(w2*P)
    This function add a prefix to the previous polynomial
    Take prefix = IM(x(t),y(t)**2)
    We compute
    x(t)*int(y(t)**2*int (w0*p)) + x(t)*int(y(t)**2*int(w1*int(w2*P))
    The following list is then returned:

    W_prime = [(IntPol(x(t)), IntPol(y(t)**2),w0,P), 
                (IntPol(x(t)),IntPol(y(t)**2),w1,w2,P)]
    """ 
    if W==[]:
        return W

    # convert prefix (which is an IM) into a list of integral polynomials
    # e.g : IM(x(t),y(t)) -> [IntegralPol(Im(x(t))),IntegralPol(IM(y(t))]
    prefix_pol_list = [
                IntegralPolynomial(IM(elem)) 
                for elem in prefix.get_content()
        ]
    W_prime = [] 
    
    for Wi in W:
        # Wi contains integral polynomials 
        W_prime += [(*prefix_pol_list, *Wi,)] 
    return W_prime



def mult_quotients_by_coeff(IA, W, coeff):  
    """
    Example:
    Consider a list 
    W = [(IntPol(IM(x(t))), IntPol(IM(y(t)**2)),w0,P), 
                (IntPol(IM(x(t))),IntPol(IM(y(t)**2)),w1,w2,P)]
    where w0,w1,w2 are Integral Polynomials.
    W encodes : x(t)*int(y(t)**2*int (w0*p)) + x(t)*int(y(t)**2*int(w1*int(w2*P))
    
    This function multiply the first polynomial of each tuple by coeff.

    The list 
        W_prime = [(IntPol(coeff*IM(x(t))), IntPol(IM(y(t)**2)),w0,P), 
                (IntPol(coeff*IM(x(t))),IntPol(IM(y(t)**2)),w1,w2,P)]
    is then returned.
    W_prime encodes :
        coeff*x(t)*int(y(t)**2*int (w0*p)) + coeff*x(t)*int(y(t)**2*int(w1*int(w2*P))
    """ 
    if W==[]:
        return W
    coeff_pol = IntegralPolynomial(coeff*IM(1))
    W_prime = []   
    for Wi in W: 
        W_prime += [(IA.polynomials_product(Wi[0],coeff_pol),
                    *Wi[1:],),] 
    return W_prime