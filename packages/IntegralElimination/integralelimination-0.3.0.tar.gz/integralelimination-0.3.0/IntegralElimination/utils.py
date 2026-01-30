import sympy as sp 

def is_float(expr):
    try:
        float(expr)
        return True
    except:
        return False

def is_int(expr):
    try:
        f = float(expr) 
        return f.is_integer()
    except:
        return False

def has_add_in_list(l):  
    for e in l:
        if not is_float(e) or not is_int(e):
            if e.has(sp.Add):
                return True
    return False
 

def expr_has_symbol(expr, symbol): 
    try: 
        return expr.has(symbol)
    except:
        return False


def expr_has_symbols(expr, symbols): 
    has_symbols = False
    for symbol in symbols:
        has_symbols = has_symbols or expr_has_symbol(expr,symbol)
    return has_symbols
 

def dicts_subtraction(L:list[dict]):
    assert len(L) == 2 #to admit the same signature as dicts_addition
    P,Q = L[0],L[1]
    PminusQ = P
    for N,c_N in Q.items(): 
        if N not in PminusQ:
            PminusQ[N] = -c_N
        else:
            PminusQ[N] -= c_N 
    keys_to_remove = [M for M, coeff in PminusQ.items() if coeff == 0]
    for key in keys_to_remove:
        del PminusQ[key] 
    return PminusQ

def dicts_addition(L:list[dict]):
    assert len(L) == 2 #to admit the same signature as dicts_addition
    P,Q = L[0],L[1]
    PpluqQ = P
    for N,c_N in Q.items(): 
        if N not in PpluqQ:
            PpluqQ[N] = c_N
        else:
            PpluqQ[N] += c_N 
    keys_to_remove = [M for M, coeff in PpluqQ.items() if coeff == 0]
    for key in keys_to_remove:
        del PpluqQ[key] 
    return PpluqQ

def dict_mul_by_coeff(d:dict, coeff:sp.Expr):
    for key in d:
        d[key] = d[key]*coeff
    return d


def subtract_lists(L1,L2): 
    if len(L2) > len(L1) or len(L1) == 0: return []
    if len(L2) == 0: return L1 
    res = []
    for i in range(len(L1)):
        if L2[0] == L1[i]:
            return res + subtract_lists(L1[:i]+L1[i+1:], L2[1:])
    return res     

def shuffle_list(l1, l2):
    """
    shuffle two lists
    u1.u >< v1.v = u1.(u >< v1.v) + v1.(u1.u >< v)
    with >< the shuffle operation
     
    return [u1, u2, ..., un] such that l1 >< l2 = u1 + u2 + ... + un,
    """
    res = []
    if len(l1) == 0:
        res = [l2]
    elif len(l2) == 0 :
        res = [l1]
    else:
        sh1 = shuffle_list(l1[1:], l2) # (u >< v1.v)
        sh2 = shuffle_list(l1, l2[1:]) # (u1.u >< v)
        for l in sh1:
            res = [*res, [l1[0], *l]] # u1.(u >< v1.v)
                
        for l in sh2:
            res = [*res, [l2[0], *l]] # v1.(u1.u >< v)
    return res


def lyndon_decomp(w:list, cmp_fn:callable, order:list):
    """
    w      is a word 
    cmp_fn is the comparison function used to compare two elements
            of the alphanets.
            In this context, we will use comp_lexico from ordering.py
    order  is the order used for comp
    """
    n=len(w)
    lyn_idx = []
    k = -1
    while k < n-1:
        i = k+1
        j = k+2
        while j < n and cmp_fn(w[i],w[j],order) :
            if w[i] == w[j]:
                i = i+1
            else :
                i = k+1
            j = j+1
        while k < i:
            lyn_idx += [k+1]
            k = k+j-i
    lyn_idx += [n]
    lyn_words =  [tuple(w[lyn_idx[i]:lyn_idx[i+1]])
                  for i in range(len(lyn_idx)-1)]
    return lyn_words

 