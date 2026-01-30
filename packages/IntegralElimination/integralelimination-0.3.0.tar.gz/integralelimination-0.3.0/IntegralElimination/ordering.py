import sympy as sp 

from .IntegralMonomial import IM

def LeadingMonomial(m1, m2, order):
    m1_dict =  m1.as_powers_dict()
    m1_tuple = tuple(m1_dict.get(var, 0) for var in order)
    m2_dict =  m2.as_powers_dict()
    m2_tuple = tuple(m2_dict.get(var, 0) for var in order)
    if m1_tuple > m2_tuple:
        return m1
    else:
        return m2 


# compare two monimials w.r.t to the plex order on X
# return true if w1<=w2

def comp_lexico(w1, w2, order):   
    """
    w1 or w2 can be sp.Expr or int
    """
    is_float_w1 = not isinstance(w1,sp.Expr) 
    is_float_w2 = not isinstance(w2,sp.Expr) 

    if (w1 == 0) : return True 
    elif (w2 == 0) : return False 
    elif is_float_w1 and is_float_w2 :
        return w1 <= w2
    elif is_float_w1 and not is_float_w2 :
        return True
    elif not is_float_w1 and is_float_w2 :
        return False
    
    ld = LeadingMonomial(w1, w2, order) 
    if  ld == w2 : 
        return True
    else: 
        return False
    
def comp_lexico_lists(L1,L2,order, reversed=False):
    # return true if L1<=L2
    if len(L1)==0:
        return True
    if len(L2)==0:
        return False
    #add padding
    n1 = len(L1)
    n2 = len(L2)
    n_max = max([n1,n2])
    L1 = [*L1, *[0]*(n_max-n1)]
    L2 = [*L2, *[0]*(n_max-n2)]
    for i in range(len(L1)):
        if L1[i] != L2[i]:
            if reversed:
                return not comp_lexico(L1[i], L2[i], order)
            return comp_lexico(L1[i], L2[i], order)
    return True

#integral monomials ordering
def IMO(M1: IM, M2: IM, order: list):   
    """
    M1 and M2 are integral monomials
    order : list of monomials
    IMO is an elimination ordering

    return True if i1 <= i2 
    """ 
    L1_c = M1.get_content()
    L2_c = M2.get_content()
    n1 = len(L1_c)
    n2 = len(L2_c)
    m1 = sp.Mul(*[L1_c[i] for i in range(n1)])
    m2 = sp.Mul(*[L2_c[i] for i in range(n2)]) 
    
    L1 = [m1, n1, *reversed(L1_c)] 
    L2 = [m2, n2, *reversed(L2_c)] 
    
    return comp_lexico_lists(L1,L2,order)


def IMO_elim_integ(M1: IM, M2: IM, order: list):   
    L1_c = M1.get_content()
    L2_c = M2.get_content()
    n1 = len(L1_c)
    n2 = len(L2_c)
    L1 = [n1, *reversed(L1_c)] 
    L2 = [n2, *reversed(L2_c)] 
    return comp_lexico_lists(L1,L2,order)


def IMO_elim_cst(M1: IM, M2: IM, order: list):   
    L1_c = M1.get_content()
    L2_c = M2.get_content()
    n1 = len(L1_c)
    n2 = len(L2_c) 
    m1 = sp.Mul(*[L1_c[i] for i in range(n1)])
    m2 = sp.Mul(*[L2_c[i] for i in range(n2)]) 
    L1 = [m1, n1, *reversed(L1_c)] 
    L2 = [m2, n2, *reversed(L2_c)] 
    return comp_lexico_lists(L1,L2,order,reversed=True)
