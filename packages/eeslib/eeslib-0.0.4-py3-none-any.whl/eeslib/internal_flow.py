"""
This file is for use by students and faculty at the University of Wisconsin-Madison 
as part of the ME564 Heat Transfer course, instructor Mike Wagner. Code is derived 
from Engineering Equation Solver (EES) under license restrictions.
"""

from numpy import log, sqrt, log10, tanh, exp

def warning(msg,*args):
    print(f"Warning: {msg}\t" + '\t'.join(args))


def pipeflow_nd(Re, Pr, LoverD, relRough):
    """
    This procedure calculates the average Nusselt number and friction factor for  flow in a pipe
    given Reynolds number (Re), Prandtl number (Pr), the pipe length diameter ratio (LoverD) and 
    the relative roughness.  The procedure will determine whether the flow is laminar, turbulent 
    or transitional and call the appropriate procedure.
    
    Parameters
    ----------
    Re : float
        Reynolds number 
    Pr : float
        Prandtl number of the fluid
    LoverD : float
        Length to diameter ratio of the pipe
    relRough : float
        Relative roughness of the pipe (epsilon/D)
    
    Returns
    -----------
    Nusselt_T : float
        Nusselt number for constant wall temperature
    Nusselt_H : float
        Nusselt number for constant heat flux
    f : float
        Friction factor
    """
    if (Re<0.001): warning(f'Re in PipeFlow_ND must be > 0.001.  The value is {Re}')
    if (relRough<0) or (relRough>0.05): warning(f'relRough in PipeFlow_ND should be between 0 and 0.05.  The value is {relRough}')
    if (Re> 3000): #{turbulent flow}
        Nusselt_T, f = pipeflow_turbulent(Re, Pr, LoverD, relRough)
        Nusselt_H = Nusselt_T
    
    if (Re<2300): #{laminar flow <2300}
        Nusselt_T, Nusselt_H, f = pipeflow_laminar(Re, Pr, LoverD)
    if (Re<=3000) and (Re>=2300): #{transition from laminar to turblent flow is taken as Re=2300}
        Nusselt_T, f = pipeflow_turbulent(3000, Pr, LoverD, relRough)
        Nusselt_H=Nusselt_T

        Nusselt_lam_T, Nusselt_lam_H, f_lam = pipeflow_laminar(2300, Pr, LoverD)
        Nusselt_T=Nusselt_lam_T+(Re-2300)/(3000-2300)*(Nusselt_T-Nusselt_lam_T) 
        Nusselt_H=Nusselt_lam_H+(Re-2300)/(3000-2300)*(Nusselt_H-Nusselt_lam_H) 
        f=f_lam+(Re-2300)/(3000-2300)*(f-f_lam) 
   
    return Nusselt_T, Nusselt_H, f



def pipeflow_turbulent(Re, Pr, LoverD,relRough): 
    """
    Autoatically called by pipeflow_nd
    Automatically called by ductflow_nd

    This procedure calculates the average Nusselt number and friction factor for turbulent flow in a pipe 
    given Reynolds number (Re), Prandtl number (Pr), the pipe length diameter ratio (LoverD) and the 
    relative roughness

    Parameters
    ----------
    Re : float
        Reynolds number 
    Pr : float
        Prandtl number of the fluid
    LoverD : float
        Length to diameter ratio of the pipe
    
    Returns
    -----------
    Nusselt_H : float
        Nusselt number 
    f : float
        Friction factor
    """
 
    if (Re>5E6):  warning(f'Re in PipeFlow_Turbulent must be < 5E6 for Nusselt number and <1E8 for the friction factor.  The value is {Re}')
    if (Re<2300):  warning(f'Re in PipeFlow_Turbulent must be > 2300.  The value is {Re}')
    if (Pr<0.004) or (Pr>2000): warning(f'Pr number in PipeFlow_turbulent must be between 0.004 and 2000.  The value is {Pr}')
    if (LoverD<=1):  #{7/7/20}
        if (LoverD<0):  warning(f'L / D ratio in PipeFlow_turbulent should be > 1.  The value is {LoverD}')
        LoverD=1
    if (relRough<0) or (relRough>0.05):  warning(f'relRough in PipeFlow_turbulent should be between 0 and 0.05.  The value is {relRough}')
    
    if (relRough>1e-5):  
        #Offor and Alabi, Advances in Chemical Engineering and Science, 2016, 6, 237-245
        f_fd=(-2*log10(relRough/3.71-1.975/Re*log((relRough/3.93)**1.092+7.627/(Re+395.9))))**(-2) 
    else: 
        #From Li, Seem, and Li, "IRJ, "A New Explicity Equation for Accurate Friction Factor Calculation for Smooth Tubes, 2011
        f_fd=(-0.001570232/log(Re)+0.394203137/log(Re)**2+2.534153311/log(Re)**3)*4 
    
    Nusselt_L= ((f_fd/8)*(Re-1000)*Pr)/(1+12.7*sqrt(f_fd/8)*(Pr **(2/3)-1)) #{Gnielinski, V.,, Int. Chem. Eng., 16, 359, 1976}

    if (Pr<0.5): 
        Nusselt_L_lp=4.8+0.0156*Re**0.85*Pr**0.93 #{Notter and Sleicher, Chem. Eng. Sci., Vol. 27, 1972}
        if (Pr<0.1): 
            Nusselt_L=Nusselt_L_lp
        else:
            Nusselt_L=Nusselt_L_lp+(Pr-0.1)*(Nusselt_L-Nusselt_L_lp)/0.4
        
    f=f_fd*(1+(1/LoverD)**0.7) #{account for developing flow}
    Nusselt = Nusselt_L*(1+(1/LoverD)**0.7)  #{account for developing flow}
    
    return Nusselt, f

def pipeflow_laminar(Re, Pr, LoverD): 
    """
    Automatically called by pipeflow_nd

    This procedure calculates the average Nusselt number and friction factor for laminar flow in
    a pipe given Reynolds number (Re), Prandtl number (Pr), the pipe length diameter ratio (LoverD)}
     
    Parameters
    ----------
    Re : float
        Reynolds number 
    Pr : float
        Prandtl number of the fluid
    LoverD : float
        Length to diameter ratio of the pipe

    Returns
    -----------
    Nusselt_T : float
        Nusselt number for constant wall temperature
    Nusselt_H : float
        Nusselt number for constant heat flux
    f : float
        Friction factor
    """
    if (Re>2300):  warning(f'Re in PipeFlow_laminar must be < 2300.  The value is {Re}')
    if (Pr<0.1) :  warning(f'Pr in PipeFlow_laminar must be > 0.1.  The value is {Pr}')
    Z_H=LoverD/(Re*Pr)
    if (Z_H<1e-6) :  warning(f'Z_H (the inverse Graetz number) in PipeFlow_laminar must be > 1e-6.  The value is {Z_H}')
    Z_M=LoverD/Re
    f=4*(3.44/sqrt(Z_M)+(1.25/(4*Z_M)+16-3.44/sqrt(Z_M))/(1+0.00021*Z_M**(-2)))/Re
    # {f$='Shah' {Shah, R.K.  and London, A.L. "Laminar Flow Forced Convection in Ducts", Academic PRess, 1978 ,Eqn 192, p98}}
    Nusselt_T=((5.001/Z_H**1.119+136.0)**0.2978-0.6628)/tanh(2.444*Z_M**(1/6)*(1+0.565*Z_M**(1/3)))
    Nusselt_H=((6.562/Z_H**1.137+220.4)**0.2932-0.5003)/tanh(2.530*Z_M**(1/6)*(1+0.639*Z_M**(1/3)))
    # {Nusselt$='Laminar convection in circular tubes with developing flow, Bennet, T.D., Journal of Heat Transfer, 2020'}
    return Nusselt_T, Nusselt_H, f

def pipeflow_nd_local(Re, Pr, xoverD, relRough): 
    """
    This function returns lower and upper bounds for the local Nusselt number and the local friction factor inside a  smooth pipe by numerically differentiating the average values.  This procedure calls PipeFlow_ND to obtain the integrated values.  See PipeFlow_ND for a discussion of the inputs.

    Parameters
    ----------
    Re : float
        Reynolds number 
    Pr : float  
        Prandtl number of the fluid
    xoverD : float  
        non-dimensional axial position (x/D)
    relRough : float
        Relative roughness of the pipe (epsilon/D)

    Returns
    ----------- 
    Nusselt_T : float
        Local Nusselt number for constant wall temperature
    Nusselt_H : float
        Local Nusselt number for constant heat flux
    f : float
        Local friction factor
    """
    if (xoverD<=0): 
        warning(f'xoverD in PipeFlow_ND_local must be > 0.1.  The value is {xoverD}')
        xoverD=0.100
    
    DELTA=0.01*xoverD
    Nusselt_T_plus,Nusselt_H_plus, f_plus = pipeflow_nd(Re, Pr, xoverD+DELTA, relRough)
    Nusselt_T_minus,Nusselt_H_minus, f_minus = pipeflow_nd(Re, Pr, xoverD-DELTA, relRough)
    Nusselt_T=(Nusselt_T_plus*(xoverD+DELTA)-Nusselt_T_minus*(xoverD-DELTA))/(2*DELTA)
    Nusselt_H=(Nusselt_H_plus*(xoverD+DELTA)-Nusselt_H_minus*(xoverD-DELTA))/(2*DELTA)
    f=(f_plus*(xoverD+DELTA)-f_minus*(xoverD-DELTA))/(2*DELTA)
    return Nusselt_T, Nusselt_H, f

# ============================================================================

def ductflow_laminar(Re,Pr,LoverD,Aspect): 
    """
    Automatically called by ductflow_nd
    
    This function calculates the average Nusselt number and friction factor for laminar flow in a rectangular duct given Reynolds number (Re), Prandtl number (Pr), the pipe length diameter ratio (LoverD), aspect ratio}

    Parameters
    ----------
    Parameters
    ----------
    Re : float
        Reynolds number 
    Pr : float
        Prandtl number of the fluid
    LoverD : float
        Length to diameter ratio of the duct
    Aspect : float
        Aspect ratio of the duct (ratio of smaller side to larger side)

    Returns
    -----------
    Nusselt_T : float
        Nusselt number for constant wall temperature
    Nusselt_H : float
        Nusselt number for constant heat flux
    f : float
        Friction factor
    """
    if (Re<0.001): warning(f'Re in DuctFlow_Laminar must be > 0.001.  The value is {Re}')
    if (Pr<0.001) : warning(f'Pr in DuctFlow_Laminar must be > 0.001.  The value is {Pr}')
    if (LoverD<0.1) : warning(f'LoverD in DuctFlow_Laminar must be > 0.1.  The value is {LoverD}')
    if (Aspect<0) or (Aspect>1): warning(f'Aspect in DuctFlow_Laminar should be between 0 and 1  The value is {Aspect}')
    x=Re*Pr/(LoverD) #Re based on hydraulic diameter
    if (Aspect<0): warning(f'Error: Aspect ratio in DuctFlow_Laminar must be >=0 and <=1.  The value is {Aspect}')
    fR_fd=24*(1-1.3553*Aspect+1.9467*Aspect**2-1.7012*Aspect**3+0.9564*Aspect**4-0.2537*Aspect**5)
    x_plus=LoverD/Re
    fR=3.44/sqrt(x_plus)+(1.25/(4*x_plus)+fR_fd-3.44/sqrt(x_plus))/(1+0.00021*x_plus**(-2))    
    f=4*fR/Re  #Eqn 3.158 in Kakac, Shah and Aung
 
    # "Fully developed flow"    
    Nusselt_T_fd=7.541*(1-2.610*Aspect+4.970*Aspect**2-5.119*Aspect**3+2.702*Aspect**4-0.548*Aspect**5) #Eq. 3.159 in Kakac, Shah and Aung
    Nusselt_H_fd=8.235*(1-2.0421*Aspect+3.0853*Aspect**2-2.4765*Aspect**3+1.0578*Aspect**4-0.1861*Aspect**5) #Eq. 3.161 in Kakac, Shah and Aung
 
    # "Developing flow"
    x_star=(LoverD)/(Re*Pr)
    lnx_star=log(x_star)
 
    # "Constant T, Pr=0.72"
    a_T=0.0357122+0.460756236*Aspect-0.314865737*Aspect**2
    b_T=0.602877+0.0337485/(0.1+Aspect)+0.0377031*Aspect
    if (Aspect<0.167):
       b_T=0.940362+Aspect*(0.739606-0.940362)/0.167
    else:
       b_T=0.801105912 - 0.419264242*Aspect + 0.293641181*Aspect**2
    DNusselt_T=a_T*exp(-b_T*lnx_star)
    
    # "Constant H, Pr=0.72"
    a_H=0.113636994 + 0.712134212*Aspect - 0.392104717*Aspect**2
    if (Aspect<0.25):
      b_H=0.940362+Aspect*(0.699466-0.940362)/0.25
    else:
       b_H=0.774133656 - 0.350363736*Aspect + 0.198543081*Aspect**2
    
    DNusselt_H=a_H*exp(-b_H*lnx_star)
    
    # "Correct for Pr"
    if (Pr>0.72):     
       DNurat=0.6847+0.3153*exp(-1.26544559*(log(Pr)-log(0.72)))
    else:
       DNurat=1.68-0.68*exp(0.32*(log(Pr)-log(0.72)))
    
    Nusselt_T=Nusselt_T_fd+DNurat*DNusselt_T    
    Nusselt_H=Nusselt_H_fd+DNurat*DNusselt_H

    return Nusselt_T, Nusselt_H, f


def ductflow_nd(Re, Pr, LoverD, Aspect, relRough): 
    """
    This procedure calculates the average Nusselt number and friction factor for  flow in a duct
    given Reynolds number (Re), Prandtl number (Pr), the duct length diameter ratio (LoverD), the
    duct aspect ratio (Aspect) and the relative roughness.  The procedure will determine whether 
    the flow is laminar, turbulent or transitional and call the appropriate procedure.
    
    Parameters
    ----------
    Re : float
        Reynolds number 
    Pr : float
        Prandtl number of the fluid
    LoverD : float
        Length to diameter ratio of the duct
    Aspect : float
        Aspect ratio of the duct (ratio of smaller side to larger side)
    relRough : float
        Relative roughness of the duct (epsilon/D)
    
    Returns
    -----------
    Nusselt_T : float
        Nusselt number for constant wall temperature
    Nusselt_H : float
        Nusselt number for constant heat flux
    f : float
        Friction factor
    """
    if (Re<0.001): warning(f'Re in DuctFlow_ND must be > 0.001.  The value is {Re}')
    if (Pr<0.001) : warning(f'Pr in DuctFlow_ND must be > 0.001.  The value is {Pr}')
    if (LoverD<0.1) : #7/7/20
         if (LoverD<0): warning(f'LoverD_h in DuctFlow_ND must be > 0.1.  The value is {LoverD}')
         LoverD=0.1
      
    if (Aspect<0) or (Aspect>1): warning(f'Aspect in DuctFlow_ND should be between 0 and 1  The value is {Aspect}')
    if (relRough<0) or (relRough>0.05): warning(f'relRough in DuctFlow_ND should be between 0 and 0.05  The value is {relRough}')
    if (Re> 2300): #turbulent flow
        Nusselt_T, f = pipeflow_turbulent(Re, Pr, LoverD, relRough)
        Nusselt_H=Nusselt_T
    else: 
        #laminar flow <2300
       
        if (Re>2300) and (Re<3000): #transition from laminar to turblent flow is taken as Re=2300
            Nusselt_lam_T, Nusselt_lam_H, f_lam = ductflow_laminar(Re, Pr, LoverD, Aspect)
            Nusselt_T=Nusselt_lam_T+(Re-2300)/(3000-2300)*(Nusselt_T-Nusselt_lam_T) 
            Nusselt_H=Nusselt_lam_H+(Re-2300)/(3000-2300)*(Nusselt_H-Nusselt_lam_H) 
            f=f_lam+(Re-2300)/(3000-2300)*(f-f_lam) 
        else:
            Nusselt_T, Nusselt_H, f = ductflow_laminar(Re, Pr, LoverD, Aspect)
    
    return Nusselt_T, Nusselt_H, f       
 
def ductflow_nd_local(Re, Pr, xoverD, Aspect, relRough): 
    """
    This function returns lower and upper bounds for the local Nusselt number and the local 
    friction factor inside a rectangular duct given Reynolds number (Re), Prandtl number (Pr), 
    non-dimensional axial position (x/D) and aspect ratio (Aspect) by numerically 
    differentiating the average values.  This def calls DuctFlow_ND to obtain the integrated 
    values.  

    Parameters
    ----------
    Re : float
        Reynolds number 
    Pr : float  
        Prandtl number of the fluid
    xoverD : float  
        non-dimensional axial position (x/D)
    Aspect : float
        Aspect ratio of the duct (ratio of smaller side to larger side)
    relRough : float
        Relative roughness of the pipe (epsilon/D)

    Returns
    ----------- 
    Nusselt_T : float
        Local Nusselt number for constant wall temperature
    Nusselt_H : float
        Local Nusselt number for constant heat flux
    f : float
        Local friction factor
    
    Returns
    -----------
    Nusselt_T : float
        Nusselt number for constant wall temperature
    Nusselt_H : float
        Nusselt number for constant heat flux
    f : float
        Friction factor
    """
    if (xoverD<0.1): #7/7/20
        if (xoverD<0): warning(f'xoverD_h in DuctFlow_ND_local must be > 0.  The value is {xoverD}')
        xoverD=0.1
    
    DELTA=0.01*xoverD
    Nusselt_T_plus,Nusselt_H_plus, f_plus = ductflow_nd(Re, Pr, xoverD+DELTA, Aspect, relRough)
    Nusselt_T_minus,Nusselt_H_minus, f_minus = ductflow_nd(Re, Pr, xoverD-DELTA, Aspect, relRough)
    Nusselt_T=(Nusselt_T_plus*(xoverD+DELTA)-Nusselt_T_minus*(xoverD-DELTA))/(2*DELTA)
    Nusselt_H=(Nusselt_H_plus*(xoverD+DELTA)-Nusselt_H_minus*(xoverD-DELTA))/(2*DELTA)
    f=(f_plus*(xoverD+DELTA)-f_minus*(xoverD-DELTA))/(2*DELTA)

    return Nusselt_T, Nusselt_H, f
 