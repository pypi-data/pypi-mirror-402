import sympy as sp
from ordered_set import OrderedSet
from IPython.display import display, Math

from .ordering import IMO, comp_lexico
from .IntegralMonomial import IM
from .utils import (
    is_int,
    shuffle_list,
    subtract_lists,
    lyndon_decomp,
    dicts_addition,
    dicts_subtraction,
    dict_mul_by_coeff,
    expr_has_symbol
)
from .IntegralPolynomial import IntegralPolynomial
from .reduction import ( 
    reduce,
    auto_reduce
)
from .critical_pairs import (
    critical_pairs_PI_QI,
    critical_pairs_PI_QN,
    critical_pairs_PN_QN,
    critical_pairs
)
from .exp_log import (
    find_A_A0_G_F, 
    update_exp, 
    update_log,
    extend_X_with_exp_and_log
) 
from .integral_elimination import integral_elimination

class IntegralAlgebra():
    """
    integral polynomials will be represented as follows :
    eq = {IM(x(t):3, IM(y(t),1,y(t)):theta+lambda}
    using eq.as_coefficients_dict(IM)
    It means that eq is the sum of the two tuples 
    """
    def __init__(self, order, parameters):
        self.order = order
        self.t = sp.Symbol("t")
        self.used_order = order
        self.used_order_str = str(order)
        self.ordering_func = IMO
        self.compare_IM = lambda m1, m2 : self.ordering_func(m1, 
                                            m2, 
                                            self.used_order) 
        self.parameters = parameters
        self.storage = self.init_storage()

    def init_storage(self):
        storage = {
            "LM_LC": {},
            "P_red_to_zero": {}
        }
        return storage
    
    def change_ordering_func(self, new_ordering_func):
        """
        new_ordering_func is  a function which takes the following arguments:
        M1: IM, M2: IM, order: list
        """
        self.ordering_func = new_ordering_func
        self.storage["LM_LC"] = {}

    def update_order(self, order):
        self.used_order = order
        self.used_order_str = str(order) 
 
    def LM_LC(self, P:IntegralPolynomial) -> tuple[IM, sp.Expr]:
        """
        get leading monomials and coeff
        """
        if P.is_zero():
            return None
        str_order = self.used_order_str
        if not self.storage["LM_LC"].get(str_order):
            self.storage["LM_LC"][str_order]={}
        if not self.storage["LM_LC"][str_order].get(P): 
            L = P.get_content() 
            LC, LM = L[0][1], L[0][0]
            for M,coeff in L:   
                #if True then M <= LM, else M > LM
                if self.compare_IM(M, LM) == False: 
                    LM = M # im > LM
                    LC = coeff
            self.storage["LM_LC"][str_order][P] = (LM,LC)
        LM, LC = self.storage["LM_LC"][str_order][P]
        return LM, LC
    
    def LM_LC_P_I(self, P:IntegralPolynomial) -> tuple[IM, sp.Expr]:
        if P.is_zero():
            return 
        P_I = P.get_P_I()
        if P_I.is_zero(): return None
        return self.LM_LC(P_I)
    
    def LM_LC_P_N(self, P:IntegralPolynomial) -> tuple[IM, sp.Expr]:
        if P.is_zero():
            return 
        P_N = P.get_P_N()
        if P_N.is_zero(): return None
        return self.LM_LC(P_N)

    def is_LM_in_P_I(self, P:IntegralPolynomial) ->  bool:
        LM_P, _ = self.LM_LC(P)
        P_I = P.get_P_I()
        if P_I.is_zero(): return False
        LM_P_I, _ = self.LM_LC(P_I)
        return LM_P_I == LM_P
    
    def is_LM_in_P_N(self, P:IntegralPolynomial) ->  bool:
        LM_P, _ = self.LM_LC(P)
        P_N = P.get_P_N()
        if P_N.is_zero(): return False
        LM_P_N, _ = self.LM_LC(P_N)
        return LM_P_N == LM_P
        
    def display_rules(self, sys):
        display(Math(r"\{")) 
        for eq in sys:
            LM, LC = self.LM_LC(eq)
            key = IntegralPolynomial({LM:LC})
            value = self.polynomials_subtraction(eq, key)
            value = self.product_P_Coeff(value,-1)
            arrow = r"{\Huge \color{red} \mathbf{\rightarrow}}"  
            key_repr = key.repr_display_math()
            value_repr = value.repr_display_math()
            export = Math(f"{key_repr} {arrow} {value_repr}") 
            display(export)
        display(Math(r"\}"))

    def display_rules_without_coeff(self, sys):
        display(Math(r"\{")) 
        for eq in sys:
            LM, LC = self.LM_LC(eq)
            key = IntegralPolynomial({LM:1})
            value = eq.get_content_as_dict()
            del value[LM]
            for k,v in value.items():
                value[k]=1
            value=IntegralPolynomial(value)
            # value = self.product_P_Coeff(value,-1)
            arrow = r"{\Huge \color{red} \mathbf{\rightarrow}}"  
            key_repr = key.repr_display_math()
            value_repr = value.repr_display_math()
            export = Math(f"{key_repr} {arrow} {value_repr}") 
            display(export)
            print(self.parameters)
            print([expr_has_symbol(eq.get_integral_repr(),s) for s in self.parameters])
    
        display(Math(r"\}"))
         
    def display_LMs(self, sys):
        display(Math(r"\{")) 
        for eq in sys:
            LM, LC = self.LM_LC(eq)
            key = IntegralPolynomial({LM:LC})
            arrow = r"{\Huge \color{red} \mathbf{\rightarrow}}"  
            key_repr = key.repr_display_math()
            export = Math(f"{key_repr} {arrow} ...") 
            display(export)
        display(Math(r"\}"))
         

    def normalize_LC_of_P(self, 
                        P: IntegralPolynomial,
                        simplify_coeff=True) -> IntegralPolynomial:
        _, LC = self.LM_LC(P)
        if LC == 1:
            return P,1
        normalized_P = {}
        for M, coeff in P.get_content(): 
            normalized_P[M] = coeff/LC
        P_norm = IntegralPolynomial(normalized_P, simplify_coeff=simplify_coeff)
        return P_norm, LC
    
    def monomial_product(self, 
                          M: IM, 
                          N: IM,
                          simplify_coeff=True)-> IntegralPolynomial:
        e = M.get_nb_int()
        f = N.get_nb_int()
        m0n0 = M.get_content()[0]*N.get_content()[0]
        if e == f == 0:
            MN = {IM(m0n0):1}
        elif e == 0 and f != 0:
            N1p = N.cut("1+").get_content() #N1plus
            MN  = {IM(m0n0,*N1p):1} 
        elif e != 0 and f== 0 :
            M1p = M.cut("1+").get_content() #N1plus
            MN = {IM(m0n0,*M1p): 1}
        else:
            N1p = N.cut("1+").get_content() #N1plus
            M1p = M.cut("1+").get_content() #N1plus
            sh = shuffle_list(M1p,N1p)
            mons_dict = {}
            for elem in sh:
                mons = IM(m0n0,*elem)
                if mons not in mons_dict:
                    mons_dict[mons] =1
                else:
                    mons_dict[mons] += 1 
            MN = mons_dict
        return IntegralPolynomial(MN,simplify_coeff=simplify_coeff)


    def monomial_division(self, M, T):
        """
        find an integral monomial N such that lm(T \cdot N) = M
        i.e. we "divide" M by T.

        return N if N exists. N=1 if M=T
        return None otherwise
        """
        if T.get_nb_int() > M.get_nb_int():
            return None
        if not self.compare_IM(T,M):
            return None
        T_c = T.get_content()
        M_c = M.get_content()
        if T_c[0] == M_c[0] == 1:
            N_0 = 1
        else:
            q, r = sp.div(M_c[0],T_c[0])
            if r != 0: return None
            N_0 = q 
        T_c, M_c = T_c[1:], M_c[1:]
        T_lyn_rev = lyndon_decomp(w      = list(reversed(T_c)), 
                                  cmp_fn = comp_lexico, 
                                  order  = self.used_order)  
        M_lyn_rev = lyndon_decomp(w      = list(reversed(M_c)), 
                                  cmp_fn = comp_lexico, 
                                  order  = self.used_order)  

        N_lyn_rev= subtract_lists(M_lyn_rev, T_lyn_rev)

        if T_lyn_rev != M_lyn_rev and len(N_lyn_rev)==0:
            return None
        N = [N_0]
        for elem in reversed(N_lyn_rev):
            N += [*reversed(elem)]
        N = IM(*N)
        
        #check that lm(T \cdot N) = M
        T_dot_N = self.monomial_product(T, N)
        LM_T_dot_N, _ = self.LM_LC(T_dot_N)
        assert LM_T_dot_N == M
        return N 
    
    def product_P_Coeff(self, 
                        P: {IntegralPolynomial, dict}, 
                        alpha: sp.Expr,
                        simplify_coeff=True,
                        return_dict=False) -> {IntegralPolynomial, dict}:
        """
        alpha is cst 
        """
        if type(P) == dict:
            alpha_P = dict_mul_by_coeff(P, alpha)
        elif type(P) == IntegralPolynomial:
            alpha_P = dict_mul_by_coeff(P.get_content_as_dict(), alpha)
        else:
            raise ValueError
        if return_dict:
            return alpha_P
        return IntegralPolynomial(alpha_P,simplify_coeff=simplify_coeff)

    def polynomials_add(self, 
                        P: {IntegralPolynomial, dict}, 
                        Q: {IntegralPolynomial, dict},
                        simplify_coeff=True,
                        return_dict=False) -> {IntegralPolynomial, dict}: 
        if type(P) == dict and type(Q) == dict:
            L = [P,Q]
        elif type(P) == IntegralPolynomial and type(Q) == IntegralPolynomial:
            L = [P.get_content_as_dict(), Q.get_content_as_dict()]
        else:
            raise ValueError
        PplusQ = dicts_addition(L)
        if return_dict:
            return PplusQ
        return IntegralPolynomial(PplusQ,simplify_coeff=simplify_coeff)
    
    def polynomials_subtraction(self, 
                                P: IntegralPolynomial, 
                                Q: IntegralPolynomial,
                                simplify_coeff=True,
                                return_dict=False) -> {IntegralPolynomial, dict}: 
        if type(P)==dict and type(Q)==dict:
            L = [P,Q]
        elif type(P)==IntegralPolynomial and type(Q)==IntegralPolynomial:
            L = [P.get_content_as_dict(), Q.get_content_as_dict()]
        else:
            raise ValueError
        PminusQ = dicts_subtraction(L)
        if return_dict:
            return PminusQ
        return IntegralPolynomial(PminusQ,simplify_coeff=simplify_coeff)
    

    def polynomials_product(self,
                            P: IntegralPolynomial,
                            Q: IntegralPolynomial,
                            simplify_coeff=True) -> IntegralPolynomial: 
        PQ = IntegralPolynomial(0)
        for M_P, c_P in P.get_content():
            for M_Q, c_Q in Q.get_content(): 
                M_PdotM_Q = self.monomial_product(
                                M_P,
                                M_Q,
                                simplify_coeff=simplify_coeff
                            )
                c_P_c_Q_M_PdotM_Q = self.product_P_Coeff(
                                        M_PdotM_Q,
                                        c_P*c_Q,
                                        simplify_coeff=simplify_coeff
                            )
                PQ = self.polynomials_add(PQ, 
                                          c_P_c_Q_M_PdotM_Q,
                                        simplify_coeff=simplify_coeff
                            )
        return PQ 
    
    def integrate_monomial(self, M: IM):
        return IM(1,*M.get_content())

    def integrate_polynomial(self, 
                             P: IntegralPolynomial,
                             simplify_coeff=False) -> IntegralPolynomial:
        Int_P = {}
        for M, coeff in P.get_content():
            Int_M = self.integrate_monomial(M)
            Int_P[Int_M] = coeff
        return IntegralPolynomial(Int_P,simplify_coeff=simplify_coeff)
 
    def add_prefix_to_polynomial(self, 
                                prefix: IM, 
                                P: IntegralPolynomial) -> IntegralPolynomial:
        new_P = {} 
        for M, coeff in P.get_content():
            pref_M = M.add_prefix(prefix)
            new_P[pref_M] = coeff
        return IntegralPolynomial(new_P)

    def half_reduced_product(self, 
                        P:IntegralPolynomial, 
                        N:IM,
                        simplify_coeff=True) -> IntegralPolynomial:
        """
        Let N an integral monomial and P an integral polynomial
        such that 
        - N[0]=1, 
        - P_I != 0,
        - lm{P} = lm{P_I}.
        1) If N=1:
        half-reduced-product = P 

        2) Otherwise,
        half-reduced-product =   
            P · N - int{ N]1+] · P }
            
        or equivalently 
        
        half-reduced-product = 
            int{ (P_I]1+] · N) - (N]1+] · P_N) } + P_N · N        
        """   
        assert (N.cut("0") == IM(1))
        if N == IM(1): return P

        LM_P,_ = self.LM_LC(P)
        P_I = P.get_P_I()
        assert not P_I .is_zero()
        LM_P_I,_ = self.LM_LC(P_I)
        assert LM_P == LM_P_I 
        N1p = IntegralPolynomial(N.cut("1+"),simplify_coeff=simplify_coeff)
        N = IntegralPolynomial(N,simplify_coeff=simplify_coeff)
        #(P \cdot N)
        PdotN = self.polynomials_product(P,N,simplify_coeff=simplify_coeff) 
        
        #\int (N]1+] \cdot P)
        IntNdotP = self.integrate_polynomial(
                        self.polynomials_product(N1p,P,simplify_coeff=simplify_coeff),
                        simplify_coeff=simplify_coeff
                    ) 

        half_reduced_product = self.polynomials_add(
                            PdotN ,self.product_P_Coeff(IntNdotP, -1,simplify_coeff=simplify_coeff),
                            simplify_coeff=simplify_coeff
                        )
        return half_reduced_product
    
    def reduced_product(self, 
                        P:IntegralPolynomial,
                        Q:IntegralPolynomial,
                        simplify_coeff=True) -> IntegralPolynomial:
        """
        Let P and Q such that
        P_I, P_N, Q_I, Q_N are nonzero
        with lm{P}=lm{P_I} and lm{Q}=lm{Q_I}.
        Then
        reduced-product =  
            -P·Q + P_N·Q  + Q_N·P   
            + int{ (P_I]1+] · Q) + (Q_I]1+] · P) }

        or equivalently 

        reduced-product =  
            int{ (P_I]1+]  · Q_N) + (Q_I]1+]  · P_N) } + P_N · Q_N

        Moreover, the reduced-product is commutative and associative.
        """
        LM_P,_ = self.LM_LC(P)
        P_I = P.get_P_I()
        LM_Q,_ = self.LM_LC(Q)
        Q_I = Q.get_P_I()
        assert not P_I .is_zero()
        assert not Q_I .is_zero()
        LM_P_I,_ = self.LM_LC(P_I)
        LM_Q_I,_ = self.LM_LC(Q_I)
        assert LM_P == LM_P_I 
        assert LM_Q == LM_Q_I  
        P_N = P.get_P_N()
        Q_N = Q.get_P_N()

        # we need to compute redprod(P,Q)= Pn * Qn + int( Q_I[1+] PN  + P_I[1+] QN )
        P_N_dot_Q_N = self.polynomials_product(P_N,Q_N,simplify_coeff=False)

        P_I_cut_1plus = P_I.cut_P("1+")
        Q_I_cut_1plus = Q_I.cut_P("1+")

        P_I_cut_1plus_dot_Q_N = self.polynomials_product(P_I_cut_1plus,Q_N,simplify_coeff=False)
        Q_I_cut_1plus_dot_P_N = self.polynomials_product(Q_I_cut_1plus,P_N,simplify_coeff=False)


        #int(Q_I[1+] PN  + P_I[1+] QN)
        res = self.polynomials_add(
            self.integrate_polynomial(P_I_cut_1plus_dot_Q_N,simplify_coeff=False),
            self.integrate_polynomial(Q_I_cut_1plus_dot_P_N,simplify_coeff=False),
            simplify_coeff=False
        )
        reduced_product = self.polynomials_add(res,P_N_dot_Q_N, simplify_coeff=simplify_coeff)
        return reduced_product

    def polynomial_power(self, 
                        P:IntegralPolynomial,
                        n:int,
                        simplify_coeff=True) -> IntegralPolynomial:
        """
        Return: P^n
        """
        assert is_int(n) 
        assert isinstance(P,IntegralPolynomial)
        if n == 0: return IntegralPolynomial(IM(1))
        P_pow_n = P
        for _ in range(n-1):
            P_pow_n = self.polynomials_product(
                        P_pow_n,
                        P,
                        simplify_coeff=simplify_coeff
            )
        return P_pow_n
    
    def reduced_power(self, 
                      P:IntegralPolynomial, 
                      n:int,
                      simplify_coeff=True) -> IntegralPolynomial:
        """  
        Consider a nonzero integral polynomial P written as
        P = P_I + P_N 
        with P_I !=0, P_N !=0 and lm{P}=lm{P_I}.
        For any positive integer n,
        define
        reduced_power(P,n) =  
            n int{ P_I]1+] · P_N^{n-1} } + P_N^n
        """
        assert is_int(n) and n >= 1 
        if n==1: return P
        P_I = P.get_P_I()
        P_N = P.get_P_N() 
        P_I_1plus = P_I.cut_P("1+") 
        P_N_pow_n_minus_one = self.polynomial_power(
                        P_N, 
                        n-1,
                        simplify_coeff=simplify_coeff
        )

        P_N_pow_n = self.polynomials_product(
            P_N_pow_n_minus_one, 
            P_N,
            simplify_coeff=simplify_coeff
        )

        #lets compute n int{ P_I]1+] · P_N^{n-1} } + P_N^n 
        temp = self.integrate_polynomial(
                    self.polynomials_product(
                        P_I_1plus, 
                        P_N_pow_n_minus_one,
                        simplify_coeff=simplify_coeff
                     ),
                simplify_coeff=simplify_coeff
            )

        temp = self.product_P_Coeff(temp, n, simplify_coeff=simplify_coeff)

        reduced_power = self.polynomials_add(
                    temp, 
                    P_N_pow_n,
                    simplify_coeff=simplify_coeff
            )

        return reduced_power
    
    def reduce(self, 
                Q: IntegralPolynomial, 
                T: OrderedSet[IntegralPolynomial],
                reduce_LM_only:bool=True,
                compute_W:bool=True
            ) -> IntegralPolynomial:
        return reduce(self,Q,T,
                      reduce_LM_only=reduce_LM_only,
                      compute_W=compute_W)
    
    def auto_reduce(self,  
                    T:OrderedSet[IntegralPolynomial],
                    reduce_LM_only:bool=True,
                    disable_deletion:bool=False,
                ) -> OrderedSet[IntegralPolynomial]:
        return auto_reduce(self,T,
                           reduce_LM_only=reduce_LM_only,
                           disable_deletion=disable_deletion)
    
    def critical_pairs_PI_QI(self,
                            P: IntegralPolynomial,
                            Q: IntegralPolynomial) -> IntegralPolynomial:
        return critical_pairs_PI_QI(self,P,Q)
    
    def critical_pairs_PI_QN(self,
                            P: IntegralPolynomial,
                            Q: IntegralPolynomial) -> IntegralPolynomial:
        return critical_pairs_PI_QN(self,P,Q)
    
    def critical_pairs_PN_QN(self,
                            P: IntegralPolynomial,
                            Q: IntegralPolynomial) -> IntegralPolynomial:
        return critical_pairs_PN_QN(self,P,Q)
    
    def critical_pairs(self,
                       R: OrderedSet[IntegralPolynomial]
                    ) -> OrderedSet [IntegralPolynomial]:
        return critical_pairs(self,R)
    
    def find_A_A0_G_F(self, 
                      P:IntegralPolynomial
                      ) -> tuple[IntegralPolynomial]:
        return find_A_A0_G_F(self,P)
    
    def update_exp(self, 
                T_prime: OrderedSet[IntegralPolynomial],
                E: OrderedSet[sp.Function, sp.Function, IntegralPolynomial],
                reduce_LM_only:bool=True
                ) -> tuple:
        return update_exp(self,T_prime,E,
                          reduce_LM_only=reduce_LM_only)
         
    def extend_X_with_exp_and_log(self,
                      E: set[sp.Function, sp.Function, IntegralPolynomial],
                      L: OrderedSet[sp.Function, IntegralPolynomial]
                      ) -> list:
        return extend_X_with_exp_and_log(self, E,L)

    def update_log(self, 
                T_prime: OrderedSet[IntegralPolynomial],
                L: OrderedSet[sp.Function, IntegralPolynomial],
                reduce_LM_only:bool=True
                ) -> tuple:
        return update_log(self,T_prime,L,
                          reduce_LM_only=reduce_LM_only)
    
    def integral_elimination(self,
                            F: OrderedSet[IntegralPolynomial],
                            disable_exp: bool = False,
                            disable_log: bool = False,
                            disable_critical_pairs: bool = False,
                            disable_deletion_auto_reduce: bool = False,
                            reduce_LM_only:bool = True,
                            nb_iter: int = 0) -> tuple:
        return integral_elimination(self, 
                                F, 
                                disable_exp=disable_exp,
                                disable_log=disable_log,
                                disable_critical_pairs=disable_critical_pairs,
                                disable_deletion_auto_reduce=disable_deletion_auto_reduce,
                                reduce_LM_only=reduce_LM_only,
                                nb_iter=nb_iter)