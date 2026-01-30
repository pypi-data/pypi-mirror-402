from .IntegralMonomial import IM

def check_condition_LM_half_reduced_product(IA, P, N): 
    """ 
    Following the definition of the half-reduced product,
    (case where N != 1)
    if (P_{I}⌋1+⌉ · N) > (N⌋1+⌉ · P_{N}) then
    lm{P half-reduced-prod N) = lm{ int ( PI⌋1+⌉ · N ) }  
    
    This function returns True if the condition holds.
    Future work should investigate the other cases.
    """
    if N == IM(1): return True
    lm_PI = IA.LM_LC(P.get_P_I())[0]
    lm_PN = IA.LM_LC(P.get_P_N())[0]

    expr1 = IA.LM_LC(IA.monomial_product(lm_PI.cut("1+"),N))[0]
    expr2 = IA.LM_LC(IA.monomial_product(N.cut("1+"),lm_PN))[0] 

    return  not IA.compare_IM(expr1,expr2)