from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .IntegralAlgebra import IntegralAlgebra

import sympy as sp 
from ordered_set import OrderedSet
from itertools import combinations

from .IntegralMonomial import IM
from .IntegralPolynomial import IntegralPolynomial 
from .utils import (
    expr_has_symbol,
    expr_has_symbols
)

from .check_conditions_LM import (
    check_condition_LM_half_reduced_product,
)


def critical_pairs_PI_QI(A: IntegralAlgebra, 
                         P: IntegralPolynomial,
                         Q: IntegralPolynomial) -> IntegralPolynomial:
    """
    Let P, Q such that
	P_I, P_N, Q_I, Q_N are nonzero
	and
	lm{P} = lm{P_I}, lm{Q} = lm{Q_I}.
	
	Let alpha, beta positive integers
	and 
    B_U = lm{P^{reduced power {alpha}}}[2+],
	B_V = lm{Q^{reduced power {beta}}}[2+].
	%
	If
	lm{P^{reduced power {alpha}}}[1] = lm{Q^{reduced power {beta}}}[1]
	and if the condition of 
    check_condition_LM_half_reduced_product
    (this function checks the condition)
    holds for
	both 
    P^{reduced power {alpha}} half-reduced-product  B_V
        (this expression is denoted U)
    and 
    Q^{reduced power {beta}} half-reduced-product  B_U 
        (this expression is denoted V),
	then  define

    S(P,Q) = (1/l_U) U - (1/l_V) V 
    
	where  l_U (resp. l_V) is the leading coefficient of
	U (resp. V).
    """  
    if P.is_zero() or Q.is_zero():
        return None
    #first, we check that lm(P)=lm(PI) and same for Q
    LM_P,LC_P = A.LM_LC(P)
    LM_Q,LC_Q = A.LM_LC(Q)
    assert float(LC_P) == 1.0, "LC(P) should be normalized"
    assert float(LC_Q) == 1.0, "LC(Q) should be normalized"
    P_I = P.get_P_I()
    Q_I = Q.get_P_I()
    if P_I.is_zero() or Q_I.is_zero():
        return None
    LM_P_I,LC_P_I = A.LM_LC(P_I)
    LM_Q_I,LC_Q_I = A.LM_LC(Q_I)
    if (LM_P_I != LM_P) or (LM_Q_I != LM_Q):
        return None
    

    # now, we have to find if there exist 
    # positives integers alpha and beta such that 
    # lm(P_I)[1]*lm(P_N)[0]**(alpha-1) = lm(Q_I)[1]*lm(Q_N)[0]**(beta-1)
    
    # first, we have to create all the variables
    alpha = sp.Symbol("alphaaa") # to avoid having alpha if the user use it 
    beta = sp.Symbol("betaaa")
    P_N = P.get_P_N()
    Q_N = Q.get_P_N()
    if P_N.is_zero() or Q_N.is_zero():
        return None
    LM_P_N,LC_P_N = A.LM_LC(P_N)
    LM_Q_N,LC_Q_N = A.LM_LC(Q_N)
    LM_P_I_1 = LM_P_I.cut("1").get_content()[0] # lm(P_I)[1]
    LM_Q_I_1 = LM_Q_I.cut("1").get_content()[0] # lm(Q_I)[1]
    LM_P_N_0 = LM_P_N.cut("0").get_content()[0]# lm(P_N)[0]
    LM_Q_N_0 = LM_Q_N.cut("0").get_content()[0]# lm(P_N)[0]
    # let's try to solve the equation to find alpha and beta 
    eq = (LM_P_I_1*LM_P_N_0**(alpha-1))/(LM_Q_I_1*LM_Q_N_0**(beta-1))  
    # we search alpha and beta such that eq = 1
    eq_pow = eq.as_powers_dict() 
    if len(eq_pow) != 2:
        return None 
    for k,v in eq_pow.items():
        # exclude the cases such as LM_PI = \int \int C, LM_PN = C
        # LM_QI = \int I, LM_QN = C 
        # we search alpha beta such that 
        # C^(alpha-1) = C^(beta-1) I
        # but it's not possible
        if not expr_has_symbols(v, [alpha,beta]):
            return None
    solved_pows = sp.solve(list(eq_pow.values())) 
    alpha_value = solved_pows[alpha] 
    beta_value = solved_pows[beta] 

    if alpha_value < 1 or beta_value < 1:
        return None

    # we verify that 
    # lm(P_I)[1]*lm(P_N)[0]**(alpha-1) = lm(Q_I)[1]*lm(Q_N)[0]**(beta-1)
    sanity_check = sp.simplify(
                            LM_P_I_1*LM_P_N_0**(alpha_value-1) -\
                            (LM_Q_I_1*LM_Q_N_0**(beta_value-1)) 
                            ) == 0
    assert sanity_check


    # we first compute the reduced power of P and Q
    P_circled_alpha = A.reduced_power(P,alpha_value) 
    Q_circled_beta  = A.reduced_power(Q, beta_value)

    # we compute BV and BU
    # 1) B_V:
    #---------
    LM_Q_I_i2plus = IntegralPolynomial(LM_Q_I.cut("i2+")) # lm(Q_I)[i2+] 
    # we need to convert LM_Q_N_i1plus to Int pol to use power
    LM_Q_N_i1plus = IntegralPolynomial(LM_Q_N.cut("i1+")) 
    LM_Q_N_i1plus_pow = A.polynomial_power(LM_Q_N_i1plus, beta_value-1)
    B_V = A.LM_LC(A.polynomials_product(LM_Q_I_i2plus, LM_Q_N_i1plus_pow))[0]
    # 2) B_U:
    #---------
    LM_P_I_i2plus = IntegralPolynomial(LM_P_I.cut("i2+")) # lm(P_I)[i2+]
    LM_P_N_i1plus = IntegralPolynomial(LM_P_N.cut("i1+"))
    LM_P_N_i1plus_pow = A.polynomial_power(LM_P_N_i1plus, alpha_value-1)
    B_U = A.LM_LC(A.polynomials_product(LM_P_I_i2plus, LM_P_N_i1plus_pow))[0]

 
    # we verify the condition on BV and BU
    if not check_condition_LM_half_reduced_product(A,
        P_circled_alpha, B_V):
        return None
    if not check_condition_LM_half_reduced_product(A,
        Q_circled_beta, B_U):
        return None
 

    # we can now compute S(P,Q)
    # we start by computing U
    U = A.half_reduced_product(P_circled_alpha, B_V)

    # we divide by the coeff of lm(U): 
    _,LC_U = A.LM_LC(U)
    U = A.product_P_Coeff(U, 1/(LC_U))

    # Now we compute V 
    V = A.half_reduced_product(Q_circled_beta, B_U)
 
    # we divide by the coeff of lm(V): 
    _,LC_V= A.LM_LC(V)
    V = A.product_P_Coeff(V, -1/(LC_V)) 
    
    #check that lm(U) == lm(V)
    LM_U,LC_U = A.LM_LC(U)
    LM_V,LC_V = A.LM_LC(V)
    #we verify that lc_U = lc_V BUT since we already multiplied 
    #lc_V by minus 1, we need to check that lc_U = -lc_V ! 
    assert (LM_U == LM_V) and (LC_U + LC_V ==0)

    # We can compute S(P,Q):
    S = A.polynomials_add(U,V)

    # if S(P,Q) != 0 assert that lm(S(P,Q)) < lm(U)
    if not S.is_zero():
        assert A.compare_IM(A.LM_LC(S)[0], A.LM_LC(U)[0])
    return S










def critical_pairs_PI_QN(A: IntegralAlgebra, 
                         P: IntegralPolynomial,
                         Q: IntegralPolynomial) -> IntegralPolynomial:
    """
    Let P, Q such that
	P_I, P_N, Q_I, Q_N are nonzero
	and
	lm{P} = lm{P_I}, lm{Q} = lm{Q_N}.
	Let alpha, beta positive integers,
	a monomial m and
    B_U = lm{P^{reduced power {alpha}}}[2+],
    B_V = lm{Q}[1+].
	If
	$lm{P^{reduced power {alpha}}}[1] =
		m lm{Q_N}[0]$
	and if the condition of 
    check_condition_LM_half_reduced_product
    (this function checks the condition)
    holds for 
	P^{reduced power {alpha}} half-reduced-product  B_V
        (this expression is denoted U),
	then define

    S(P,Q) = (1/l_U) U - (1/l_V) V 
    
	where  
    V = int{m Q · B_U}
    and
    l_U (resp. l_V) is the leading coefficient of
	U (resp. V).
    """
    if P.is_zero() or Q.is_zero():
        return None
    
    #first, we check that lm(P)=lm(PI) and lm(Q) = lm(PN)

    is_LM_in_P_I = A.is_LM_in_P_I(P)
    is_LM_in_Q_N = A.is_LM_in_P_N(Q)
    if is_LM_in_P_I != is_LM_in_Q_N:
        return None #case P_I Q_I or P_N Q_n
    elif not is_LM_in_P_I and not is_LM_in_Q_N:
        # we need to swap p and q
        P,Q = Q,P

    _,LC_P = A.LM_LC(P)
    _,LC_Q = A.LM_LC(Q)
    assert float(LC_P) == 1.0, "LC(P) should be normalized"
    assert float(LC_Q) == 1.0, "LC(Q) should be normalized"
    LM_P_I, _ = A.LM_LC(P.get_P_I())
    LM_Q_N, _ = A.LM_LC(Q.get_P_N())

    # now, we have to find if there exist 
    # a positive integers alpha and a monomial (not integral) m such that
    # lm(P_I)[1] lm(PN)[0]**(alpha-1) = m lm(QN)[0]

    # first, we have to create all the variables
    alpha = sp.Symbol("alphaaa") # to avoid having alpha if the user use it 
    P_N = P.get_P_N()
    if P_N.is_zero():
        return None
    LM_P_N,_ = A.LM_LC(P_N) 

    LM_P_I_1 = LM_P_I.cut("1").get_content()[0] # lm(P_I)[1]
    LM_P_N_0 = LM_P_N.cut("0").get_content()[0]# lm(P_N)[0]
    LM_Q_N_0 = LM_Q_N.cut("0").get_content()[0]# lm(P_N)[0]
    
    # let's try to solve the equation to find alpha and m
    # we will devide lm(P_I)[1] lm(PN)[0]**(alpha-1) by lm(QN)[0]
    # the power dict will give one or two things: 
    # 1. only an alpha dependent term, wich mean m will 
    # be 1 after solving alpha
    # 2. one term in alpha an the other will be like {"x(t):2"},
    # then we will pick m = x(t) to cancel it.
    eq = (LM_P_I_1*LM_P_N_0**(alpha-1))/(LM_Q_N_0)  
    # we search alpha  such that eq = 1 
    eq_pow = eq.as_powers_dict()  
    if len(eq_pow) == 1:
        m=1
        alpha_value = sp.solve(list(eq_pow.values()))[alpha]
    elif len(eq_pow) == 2:
        for k,v in eq_pow.items():
            if expr_has_symbol(v, alpha):
                alpha_value = sp.solve(v)[0]
            else:
                # we don't want m to be 1/y(t) (for example)
                if v == -1:
                    return None
                m = k**v
    else:
        return None
     
    if alpha_value < 1:
        return None

    # we verify that 
    # lm(P_I)[1] lm(PN)[0]**(alpha-1) = m lm(QN)[0]
    sanity_check = sp.simplify(
                            (LM_P_I_1*LM_P_N_0**(alpha_value-1)) - \
                            (m*LM_Q_N_0)
                            ) == 0
    assert sanity_check

    # we first compute the reduced power of P 
    P_circled_alpha = A.reduced_power(P,alpha_value) 

    # we compute B_U and B_V
    # 1) B_V
    B_V = LM_Q_N.cut("i1+") 
    # 2) B_U
    LM_P_I_i2plus = IntegralPolynomial(LM_P_I.cut("i2+")) # lm(P_I)[i2+]
    LM_P_N_i1plus = IntegralPolynomial(LM_P_N.cut("i1+"))
    LM_P_N_i1plus_pow = A.polynomial_power(LM_P_N_i1plus, alpha_value-1)
    B_U = A.LM_LC(A.polynomials_product(LM_P_I_i2plus, LM_P_N_i1plus_pow))[0]


    # we verify the condition on BV 
    if not check_condition_LM_half_reduced_product(A,
        P_circled_alpha, B_V):
        return None

    # we can now compute S(P,Q)
    # we start by computing U 
    U = A.half_reduced_product(P_circled_alpha, B_V)
    # we divide by the coeff of lm(U): 
    _,LC_U = A.LM_LC(U)
    U = A.product_P_Coeff(U, 1/(LC_U))

    # Now we compute V
    m = IM(m) # to use the monomial product
    m_B_U = A.monomial_product(m,B_U)
    V = A.integrate_polynomial(A.polynomials_product(Q,m_B_U))
    # we divide by the coeff of lm(V): 
    _,LC_V= A.LM_LC(V)
    V = A.product_P_Coeff(V, 1/(LC_V)) 
     
    #check that lm(U) == lm(V)
    LM_U,LC_U = A.LM_LC(U)
    LM_V,LC_V = A.LM_LC(V)
    #we verify that lc_U = lc_V  
    assert (LM_U == LM_V) 
    assert (LC_U - LC_V ==0)

    # We can compute S(P,Q):
    S = A.polynomials_subtraction(U,V)

    # if S(P,Q) != 0 assert that lm(S(P,Q)) < lm(U)
    if not S.is_zero():
        assert A.compare_IM(A.LM_LC(S)[0], A.LM_LC(U)[0])
    return S










def critical_pairs_PN_QN(A: IntegralAlgebra, 
                         P: IntegralPolynomial,
                         Q: IntegralPolynomial) -> IntegralPolynomial:
    """
    Let P, Q such that  
	lm{P} = lm{P_N}, lm{Q} = lm{Q_N}.
	We denote by L the least common multiple (LCM) of
	lm{P}[0] and lm{Q}[0],
	i.e.  $L=LCM(lm{P}[0], lm{Q}[0])$.

    1) if  lm{Q_N}[1+] != lm{P_N}[1+]
        U = (L/lm{P_N}[0]) · P · lm{Q_N}[1+] 
        V = (L/lm{Q_N}[0]) · Q · lm{P_N}[1+]


    2) if  \LtQdot[1+]=\LtPdot[1+]
        U = (L/lm{P_N}[0]) · P 
        V = (L/lm{Q_N}[0]) · Q 

    Let us define:

    S(P,Q) = (1/l_U) U - (1/l_V) V  
     
    where  
    l_U (resp. l_V) is the leading coefficient of
	U (resp. V).
    """
    if P.is_zero() or Q.is_zero():
        return None
    LM_P,LC_P = A.LM_LC(P)
    LM_Q,LC_Q = A.LM_LC(Q)
    assert float(LC_P) == 1.0, "LC(P) should be normalized"
    assert float(LC_Q) == 1.0, "LC(Q) should be normalized"

    #first, we check that lm(P)=lm(PN) and lm(Q) = lm(PN)
    P_N = P.get_P_N()
    Q_N = Q.get_P_N()
    if P_N.is_zero() or Q_N.is_zero():
        return None
    LM_P_N,LC_P_N = A.LM_LC(P_N)
    LM_Q_N,LC_Q_N = A.LM_LC(Q_N)
    if (LM_P_N != LM_P) or (LM_Q_N != LM_Q):
        return None
    
    # we first compute L = LCM(lm(P_N)[0], lm(Q_N)[0])
    LM_P_N_0 = LM_P_N.cut("0").get_content()[0]
    LM_Q_N_0 = LM_Q_N.cut("0").get_content()[0]
    L = sp.lcm(LM_P_N_0,LM_Q_N_0)
    if L == LM_P_N_0*LM_Q_N_0:
        return None
    # we have to determine in which case we are :
    # it means we must determine if lm(QN)[i1+] equal lm(PN)[i1+] or not
    LM_P_N_i1plus = LM_P_N.cut("i1+")
    LM_Q_N_i1plus = LM_Q_N.cut("i1+")
    # before that, to optimize, we can already 
    # compute the common part of U and V
    l_P = LC_P_N
    mons_U = IntegralPolynomial(IM(L/LM_P_N_0))
    U = A.product_P_Coeff(A.polynomials_product(mons_U, P), 1/(l_P))
    l_Q = LC_Q_N
    mons_V = IntegralPolynomial(IM(L/LM_Q_N_0))
    V = A.product_P_Coeff(A.polynomials_product(mons_V, Q), 1/(l_Q))
    if LM_P_N_i1plus != LM_Q_N_i1plus:
        LM_P_N_i1plus = IntegralPolynomial(LM_P_N_i1plus)
        LM_Q_N_i1plus = IntegralPolynomial(LM_Q_N_i1plus)
        U = A.polynomials_product(U,LM_Q_N_i1plus)
        V = A.polynomials_product(V,LM_P_N_i1plus)
    # we divide by the coeff of lm(U): 
    _,LC_U = A.LM_LC(U)
    U = A.product_P_Coeff(U, 1/(LC_U))
    # we divide by the coeff of lm(V): 
    _,LC_V= A.LM_LC(V)
    V = A.product_P_Coeff(V, 1/(LC_V)) 
    #check that lm(U) == lm(V)
    LM_U,LC_U = A.LM_LC(U)
    LM_V,LC_V = A.LM_LC(V)
    #we verify that lc_U = lc_V   
    assert (LM_U == LM_V) and (LC_U - LC_V ==0)

    # We can compute S(P,Q):
    S = A.polynomials_subtraction(U,V)

    # if S(P,Q) != 0 assert that lm(S(P,Q)) < lm(U)
    if not S.is_zero():
        assert A.compare_IM(A.LM_LC(S)[0], A.LM_LC(U)[0])
    return S










def critical_pairs(A: IntegralAlgebra, 
                   R: OrderedSet[IntegralPolynomial]
                ) -> OrderedSet[IntegralPolynomial]:
    """
    see Algorithm 2
    """
    S = OrderedSet()
    
    all_distinct_pairs_in_R = list(combinations(R, 2)) 
    
    for P,Q in all_distinct_pairs_in_R: 
        P_norm,_ = A.normalize_LC_of_P(P)
        Q_norm,_ = A.normalize_LC_of_P(Q)
        S_P_Q = A.critical_pairs_PI_QI(P_norm,Q_norm)
        if S_P_Q is not None:
            S.append(S_P_Q)
        S_P_Q = A.critical_pairs_PI_QN(P_norm,Q_norm)
        if S_P_Q is not None:
            S.append(S_P_Q)
        S_P_Q = A.critical_pairs_PN_QN(P_norm,Q_norm)
        if S_P_Q is not None:
            S.append(S_P_Q)

    return S
        

 

