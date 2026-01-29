from numpy import log, sqrt, log10, tanh, exp, pi
from scipy.optimize import fsolve
from eeslib import lookup_data

def warning(msg,*args):
    print(f"Warning: {msg}	" + '	'.join(args))

def findntuxflow2(epsilon,C_r):
    def __f(x, eps, cr):
        NTU = x[0]
        return eps-(1/(1-exp(-NTU))+cr/(1-exp(-cr*NTU))-1/NTU)**(-1)
    NTU = fsolve(__f, [1.], args=(epsilon,C_r))[0]    
    return NTU  

def findntuxflow(epsilon,C_r):
    def __f(x, eps, cr):
        NTU = x[0]
        return eps - (1-exp((1/cr)*NTU**0.22*(exp(-cr*NTU**0.78)-1)))
    NTU = fsolve(__f, [1.], args=(epsilon,C_r))[0]    
    return NTU  
      
def lmtd_cf(TypeHX, P, R): #
    """
    LMTD_CF determines the correction factor for the log mean temperature difference method of heat exchanger analysis when applying the method to a heat exchanger in a flow configuration other than counterflow. The correction factor is applied based on a counterflow heat exchanger.
     
    Parameters
    ----------
    TypeHX : string
        this string variable specifies the flow configuration. The following strings are acceptable:
        [parallelflow, counterflow, crossflow_both_unmixed, crossflow_both_mixed, crossflow_one_unmixed, shell&tube_N, regenerator]
    P : float
        is equal to (T_2_out-T_2_in)/(T_1_in-T_2_in) where P will always be 0 or positive <=1
    R : float
        is equal to (T_1_in-T_1_out)/(T_2_out-T_2_in)where 0<R<infinity
     
    Returns
    -----------
    LMTD_CF is the log-mean temperature difference correction factor
    
    """
    
    if(P>1) or (P<=0): warning(f'The value for P must be in the range 0<P<=1.  A value of {P}.')
    if(R<0): warning(f'R must be a positive  value. A value of { R}.')
    if(R==0): R=1e-4
    C_max=1    #
    if(R<=1):
        epsilon=P
        C_r=R
        C_min=C_r
    else:
        epsilon=P*R
        C_r=1/R
        C_min=C_r
    LC=TypeHX
    if LC=='crossflow_both_unmixed':
        if(R>4.0) or (R<0.2): warning(f'The value for R must be within the range 0.2<R<4 for the crossflow_both_unmixed heat exchanger. A value of { R}.')
        P_max=1.01*lookup_data.crossflow_limit['R']([R])[0] 
        if(P>P_max): warning(f'The given of P at the specified R requires a heat exchanger efficiency that is not possible. The maximum value for P is {P_max}.')
        if(R>1): 
            P=P*R
            R=1/R
            #
        NTU = findntuxflow(epsilon,C_r)  #
        if(R==1):
            lmtd_cf=-epsilon/(NTU*P-NTU)
        else:
            lmtd_cf=epsilon*log((P-1)/(R*P-1))/NTU/P/(R-1)
    else:
        NTU=hx(TypeHX, epsilon, C_min, C_max, 'NTU')
        if(R==1):
            lmtd_cf=-epsilon/(NTU*P-NTU)
        else:
            lmtd_cf=epsilon*log((P-1)/(R*P-1))/NTU/P/(R-1)
    
    return lmtd_cf
    
    
    
def hx(TypeHX, P, C_1, C_2, return_type): #
    """
    Function HX returns either the NTU or the effectivenss of a heat exchanger.
    
    if return_type is equal to 'epsilon', then HX returns the effectiveness otherwise if return_type is equal to 'Ntu' then HX returns the number of transfer units (Ntu).  
    if return_type is equal to 'epsilon' then P is assumed to be the heat exchanger Ntu which is equal to UA/C_min.
    if return_type is equal to 'Ntu' then P is assumed to be the heat exchanger effectiveness.
     
    if epsilon is known, then it is more efficient to set return_type='Ntu'.
    if Ntu is known, then it is more efficient to set return_type='epsilon'.
     
    There is always a solution for epsilon given any (positive) Ntu but there may not be a solution for Ntu given any epsilon.

    Parameters
    ----------
    TypeHX : string
        Flow configuration. The following strings are acceptable:
        [parallelflow, counterflow, crossflow_both_unmixed, crossflow_both_mixed, crossflow_one_unmixed, shell&tube_N, regenerator]
    P  : float
        Either the NTU or the effectiveness, depending on the setting of return_type
    C_1 : float
        The capacitance rates of the first stream in units of W/K or Btu/hr-R.  Since the ratio is used, it does not matter if, for example, both C_1 and C_2 are in kW/K although EES may raise a warning.
    C_2 : float
        The capacitance rates of the second streams 
     
    Returns
    -----------
    Effectiveness or Ntu depending on the setting of return_type
    
    """
    
    return_type=return_type.lower()
    if(return_type)=='epsilon':
        eps=1
        Ntu=P
        if(Ntu<=0): warning(f' Ntu must be greater than 0.  A value of {Ntu}.')
    else:
        if(return_type)=='ntu':
            eps=0
            epsilon=P
            if((epsilon<=0) or (epsilon>1)): warning(f' epsilon must be between 0 and 1.  A value of {epsilon}.')
            # if(Type$='regenerator') : warning('Ntu can not be directly determined for a regenerator')  
        else:
            warning(f'return_type must be either epsilon or Ntu. {return_type} was supplied.') 
        assert return_type in ['ntu','epsilon']
    if C_1<=0: warning(f' C_1 must be greater than 0.  A value of {C_1}.')
    if C_2<=0: warning(f' C_2 must be greater than 0.  A value of {C_2}.')
    C_min=min(C_1, C_2)
    C_max=max(C_1, C_2)
    C_r=min(0.999999, C_min/C_max)
     
    LC=TypeHX.lower()
     
    if C_r<1e-6: 
        if eps==1:
            hx=1-exp(-Ntu)
        else:
            hx=-log(1-epsilon)
    else:
        if LC =='counterflow':
            if eps==1:
                x=exp(-Ntu*(1-C_r))
                hx=(1-x)/(1-C_r*x) 
            else:
                x=(epsilon-1)/(epsilon*C_r-1)
                if x<0: warning(f'There is no solution for Ntu given epsilon = {epsilon}.')
                hx=log(x)/(C_r-1)
        else:
            if LC=='parallelflow':
                if(  eps == 1):
                    hx=(1-exp(-Ntu*(1+C_r)))/(1+C_r)
                else:
                    x=1-epsilon*(1+C_r)
                    if x<0: warning(f'There is no solution for Ntu given epsilon = {epsilon}.')
                    hx=-log(x)/(1+C_r)
            else:
                if('shell&tube' in LC):
                    N=LC.split('_')[-1]
                    if( '123456789'.find(N)==0): warning(f'The heat exchanger type was not recognized.   A type of {LC} was provided.')
                    N=float(N)
                    if( eps==1):
                        x=sqrt((1+C_r**2))
                        e_1=2/(1+C_r+x*((1+exp(-Ntu*x/N))/(1-exp(-Ntu*x/N))))
                        y=((1-e_1*C_r)/(1-e_1))**N
                        hx=(y-1)/(y-C_r)
                    else:
                        F=((epsilon*C_r-1)/(epsilon-1))**(1/N)
                        e_1=(F-1)/(F-C_r)
                        E=(2/e_1-1-C_r)/(sqrt(1+C_r**2))
                        x=(E-1)/(E+1)
                        if x<0: warning(f'There is no solution for Ntu given epsilon = {epsilon}.')
                        hx=-N*log(x)/ sqrt(1+C_r**2)
                else:
                    if( LC=='crossflow_both_unmixed'):
                        if( eps==1):
                            hx=1-exp((1/C_r)*Ntu**0.22*(exp(-C_r*Ntu**0.78)-1))
                        else:
                            NTU = findntuxflow(epsilon,C_r)
                            hx=NTU
                            #
                    else:
                        if( LC=='crossflow_one_unmixed'):
                            if((C_1==C_min)):
                                if(  eps==1):
                                    hx=(1/C_r)*(1-exp(-C_r*(1-exp(-Ntu))))  #        
                                else:
                                    x=1+(1/C_r)*log(1-epsilon*C_r)
                                    if x<0: warning(f'There is no solution for Ntu given epsilon = {epsilon}.')
                                    hx=-log(1+(1/C_r)*log(1-epsilon*C_r))
                            else:
                                if( eps==1):
                                    hx=(1-exp(-C_r**(-1)*(1-exp(-C_r*Ntu))))  #
                                else: 
                                    x=C_r*log(1-epsilon)+1
                                    if x<0: warning(f'There is no solution for Ntu given epsilon = {epsilon}.')
                                    hx=-(1/C_r)*log(x)
                        else: 
                            if((LC=='regenerator')): 
                                NTU=P
                                U=C_1/C_2 #
                                if(U>1000) : warning('The solution is not provided for U>1000')
                                hx=lookup_data.balanced_regenerator([[U,NTU]])[0] #interpolate2dm('balanced-regenerator', U, NTU)
                            else:
                                if(LC=='crossflow_both_mixed'):
                                    if( eps==1):
                                        hx=(1/(1-exp(-Ntu))+C_r/(1-exp(-C_r*Ntu))-1/Ntu)**(-1)
                                    else:
                                        Ntu = findntuxflow2(epsilon,C_r)
                                        hx=Ntu
                                        #
                                else:
                                    warning(f'The heat exchanger type was not recognized.   A type of {return_type}.')
                                    hx=-999
    return hx


def hx_cof_crfhdr(NTU_co, NTU_cr, CR): #
    """
    Function HX_cof_crfhdr returns the effectiveness of a counterflow heat exchanger with crossflow headers.  
    The effectiveness is calculated using the method outlined by Kays et al. (1968) in which an unmixed/unmixed crossflow heat exchanger is assumed to be in series with a counterflow device
     
    Parameters
    ----------
    NTU_co : float
        number of transfer units in counter flow region
    NTU_cr : float
        number of transfer units in the cross flow region
    CR : float
        capacitance ratio 
     
    Returns
    -----------
    Overall effectiveness of the heat exchanger (defined as total heat transfer/max possible total heat transfer)
    
    """
    
    if NTU_co<=0: warning(f' NTU_co must be greater than 0.  A value of { NTU_co}.')
    if NTU_cr<=0: warning(f' NTU_cr must be greater than 0.  A value of { NTU_cr}.')
    if CR<=0: warning(f' CR must be greater than 0.  A value of { CR}.')
    if CR>1: warning(f' CR must be less than 1.  A value of { CR}.')
     
    eff_co=hx('counterflow', NTU_co, 1, CR, 'epsilon')
    eff_cr=hx('crossflow_both_unmixed', NTU_cr, 1, CR, 'epsilon')
    hx_cof_crfhdr=(eff_cr*(1-eff_co*CR)+eff_co*(1-eff_cr))/(1-eff_co*eff_cr*CR)
     
    return hx_cof_crfhdr
    
    