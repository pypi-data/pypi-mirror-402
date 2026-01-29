"""
This file is for use by students and faculty at the University of Wisconsin-Madison 
as part of the ME564 Heat Transfer course, instructor Mike Wagner. Code is derived 
from Engineering Equation Solver (EES) under license restrictions.
"""

from numpy import log, sqrt, log10, tanh, exp, pi
import numpy as __np
from scipy import integrate as __integrate
import eeslib.fluid_properties as __fp
from eeslib import lookup_data

def warning(msg,*args):
    print(f"Warning: {msg}\t" + '\t'.join(args))

def getprops(fluid, T, P):
    """
    Retrieve fluid properties at the specified temperature and pressure.
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    T : float
        Temperature [K]
    P : float
        Pressure [Pa]

    Returns
    ----------
    rho : float
        Density [kg/m^3]
    mu : float
        Viscosity [Pa-s]
    k : float
        Thermal conductivity [W/m-K]
    c : float
        Specific heat capacity [J/kg-K]
    Pr : float
        Prandtl number, Pr=mu*c/k [-]
    """
    rho = __fp.density(fluid, T=T, P=P)
    mu = __fp.viscosity(fluid, T=T, P=P)
    k = __fp.conductivity(fluid, T=T, P=P)
    c = __fp.specheat(fluid, T=T, P=P)
    Pr = mu*c/k
    assert Pr > 0.  
    return rho, mu, k, c, Pr

def external_flow_plate_nd_local(Re, Pr ): 
    r"""
    This function returns the local Nusselt number [-] and friction coefficient C_f [-] for a flow over a flat plate.
    The critical Reynolds number is :math:`Re_{crit} = 5\times 10^5`
    
    Parameters
    ----------
    Re : float
        Reynolds number of the fluid evaluated at the local 'x' position over the plate. :math:`Re=\frac{\rho\ u_{\infty}\ x}{\mu}`  
    Pr : float
        Prandtl number of the fluid evaluated at the film temperature

    Returns
    ---------
    Nusselt : float
        Local Nusselt number
    C_f : float
        Local friction coefficient
    """
 
    Re_crit = 5e5 
    Pe=Re*Pr
    if(Re<0):  warning('The value of the Reynolds number in External_Flow_Plate_ND_local should be positive')
    if(Re>1e8):  warning(f'The value of the Reynolds number in External_Flow_Plate_ND_local should be less than 1e8.  The value is {Re}')
    if (Pr>60) and (Re>Re_crit):  warning(f'The value of the Prandtl number in External_Flow_Plate_ND_local should be less than 60 in the turbulent regime.  The value is {Pr}')
    if (Pr<0.5) and (Re>Re_crit):  warning(f'The value of the Prandtl number in External_Flow_Plate_ND_local should be greater than 0.5 in the turbulent regime.  The value is {Pr}')
    if(Pe<100):  warning(f'The value of the Peclet number in External_Flow_Plate_ND_local should be greater than about 100. The value is {Pe}')
 
    if (Re<Re_crit): 
        C_f = 0.664/Re**(0.5)
        Nusselt =  0.3387*Re**(1/2)*Pr**(1/3)/((1+(0.0468/Pr)**(2/3))**(1/4))
    else:
        C_f = 0.027/Re**(1/7)
        Nusselt = 0.0135*Re**(6/7)*Pr**(1/3)
    
    return  Nusselt,C_f
 

def external_flow_plate_nd(Re,Pr): 
    r"""
    This function returns the average Nusselt number [-] and average friction coefficient C_f [-] for a flow over a flat plate of finite length.    
    The critical Reynolds number is :math:`Re_{crit} = 5\times 10^5`
    
    Parameters
    ----------
    Re : float
        Reynolds number of the fluid evaluated using the characteristic length of the plate. :math:`Re=\frac{\rho\ u_{\infty}\ L}{\mu}`  
    Pr : float
        Prandtl number of the fluid evaluated at the film temperature

    Returns
    ---------
    Nusselt : float
        Average Nusselt number
    C_f : float
        Average friction coefficient
    """
 
    Re_crit = 5e5 
    Pe=Re*Pr
    if(Re<0):  warning('The value of the Reynolds number in External_Flow_Plate_ND_local should be positive')
    if(Re>1e8):  warning(f'The value of the Reynolds number in External_Flow_Plate_ND_local should be less than 1e8.  The value is {Re}')
    if (Pr>60) and (Re>Re_crit):  warning(f'The value of the Prandtl number in External_Flow_Plate_ND_local should be less than 60 in the turbulent regime.  The value is {Pr}')
    if (Pr<0.5) and (Re>Re_crit):  warning(f'The value of the Prandtl number in External_Flow_Plate_ND_local should be greater than 0.5 in the turbulent regime.  The value is {Pr}')
    if(Pe<100):  warning(f'The value of the Peclet number in External_Flow_Plate_ND_local should be greater than about 100. The value is {Pe}')
 
    if (Re<Re_crit): 
        C_f = 1.328/Re**(0.5)
        Nusselt =  0.6774*Re**(1/2)*Pr**(1/3)/((1+(0.0468/Pr)**(2/3))**(1/4))
    else:
        C_f = (1/Re)*(1.328*Re_crit**0.5+0.0315*(Re**(6/7)-Re_crit**(6/7)))
        Nusselt = 0.6774*Re_crit**(1/2)*Pr**(1/3)/((1+(0.0468/Pr)**(2/3))**(1/4))+0.0158*Pr**(1/3)*(Re**(6/7)-Re_crit**(6/7))
    
    return Nusselt,C_f

 
 
def external_flow_plate_l_nd_local(Re, Pr, Re_l): 
    r"""
    This function returns the local Nusselt number [-] and friction coefficient C_f [-] for a 
    flow over a flat plate using the **Lienhard correlation**. The inputs needed are the local
    Reynold and Prandtl number as well as the Reynolds number at which the transition region starts
    Alternatively, the turbulence intensity can be provided
    
    Parameters
    ----------
    Re : float
        Reynolds number of the fluid evaluated at the local 'x' position over the plate. :math:`Re=\frac{\rho\ u_{\infty}\ x}{\mu}`  
    Pr : float
        Prandtl number of the fluid evaluated at the film temperature
    Re_l : float
        Reynolds number at the transition between laminar and turbulent flow. :math:`3\times 10^4 \leq Re_{l} \leq 5\times 10^5`. A negative value indicates a percentage of turbulence intensity -(0-100]
        
    Returns
    ---------
    Nusselt : float
        Local Nusselt number
    C_f : float
        Local friction coefficient
    """
 
    Pe=Re*Pr
    if(Pe<100):  warning(f'The value of the Peclet number in External_Flow_Plate_ND_local should be greater than about 100. The value is {Pe}')
    if (Re_l>5e5):  warning(f'The value of Re_l in External_Flow_Plate_ND_local should be between 3e4 and 5e5. The value is { Re_l}')
    if (Re_l<3e4):  
        if (Re_l>0):  
            warning(f'The value of Re_l in External_Flow_Plate_ND_local must be between 3e4 and 5e5. The value is { Re_l}')
        else:
            # #Re_l<0 indicates that turbulence intensity is given (interpret absolute value as upoveru on %)
            upoveru=abs(Re_l)
            if (upoveru>100):  warning('The value of upoveru in External_Flow_Plate_ND_local must be between 0 and 100')
            Re_l=(3.6e5)*upoveru**(-5/4)
    
    Nusselt_lam =  0.3387*Re**(1/2)*Pr**(1/3)/((1+(0.0468/Pr)**(2/3))**(1/4))
    C_f_lam=0.664/Re**(0.5)
    
    c=0.9922*log10(Re_l)-3.013
    Nusselt_lam_l=0.3387*Re_l**(1/2)*Pr**(1/3)/((1+(0.0468/Pr)**(2/3))**(1/4))
    C_f_lam_l=0.664/Re_l**(0.5)
    Nusselt_trans=Nusselt_lam_l*(Re/Re_l)**c
    C_f_trans=C_f_lam_l*(Re/Re_l)**c
    
    C_f_turb=0.455/(log(0.06*Re))**2
    Nusselt_turb=Re*Pr*(C_f_turb/2)/(1+12.7*(Pr**(2/3)-1)*sqrt(C_f_turb/2))
    
    Nusselt=(Nusselt_lam**5+(Nusselt_trans**(-10)+Nusselt_turb**(-10))**(-1/2))**(1/5)
    C_f=(C_f_lam**5+(C_f_trans**(-10)+C_f_turb**(-10))**(-1/2))**(1/5)
 
    return Nusselt,C_f

 
def external_flow_plate_l_nd(Re,Pr,Re_l): 
    r"""
    This function returns the average Nusselt number [-] and average friction coefficient C_f [-] for a flow over a flat plate of finite length using the **Lienhard correlation**.    
 
    Parameters
    ----------
    Re : float
        Reynolds number of the fluid using the characteristic length of the plate. :math:`Re=\frac{\rho\ u_{\infty}\ L}{\mu}`  
    Pr : float
        Prandtl number of the fluid evaluated at the film temperature
    Re_l : float
        Reynolds number at the transition between laminar and turbulent flow. :math:`3\times 10^4 \leq Re_{l} \leq 5\times 10^5`
        
    Returns
    ---------
    Nusselt : float
        Average Nusselt number
    C_f : float
        Average friction coefficient
    """


    Pe=Re*Pr
    if(Pe<100):  warning(f'The value of the Peclet number in External_Flow_Plate_ND should be greater than about 100. The value is {Pe}')
    if (Re_l>5e5):  warning(f'The value of Re_l in External_Flow_Plate_ND_local should be between 3e4 and 5e5. The value is { Re_l}')
    if (Re_l<3e4):  
        if (Re_l>0):  
            warning(f'The value of Re_l in External_Flow_Plate_ND_local must be between 3e4 and 5e5. The value is { Re_l}')
        else:
            #Re_l<0 indicates that turbulence intensity is given (interpret absolute value as upoveru on %)
            upoveru=abs(Re_l)
            if (upoveru>100):  warning('The value of upoveru in External_Flow_Plate_ND_local must be between 0 and 100')
            Re_l=(3.6e5)*upoveru**(-5/4)
        

    
    if (Re<Re_l): 
        Nusselt_bar=0.6774*Re**(1/2)*Pr**(1/3)/((1+(0.0468/Pr)**(2/3))**(1/4))
        C_f_bar=1.328/Re**(1/2)
    else:
        Nusselt_lam_l=0.6774*Re_l**(1/2)*Pr**(1/3)/((1+(0.0468/Pr)**(2/3))**(1/4))
        C_f_lam_l=1.328/Re_l**(0.5)
        DNusselt, DC_f = __external_plate_nd_aux4(Pr, Re_l, Re) 
        C_f_bar=(1/Re)*(1.328*Re_l**(1/2)+DC_f)
        Nusselt_bar = Nusselt_lam_l+DNusselt

    Nusselt = Nusselt_bar
    C_f=C_f_bar
    return Nusselt, C_f

 
def __external_plate_nd_aux4(Pr, Re_l, Re): 
    # returns: DNusselt_bar, DC_f_bar
    #IntegralAutoStep Vary = 10 Min = 50 Max = 2000 Reduce = 1e-2 Increase = 1e-4
    #VarInfo  Rei  Guess=1e5  Lower=0.1  Upper=1e20

    Nusselt = __integrate.quad(lambda Rei: external_flow_plate_l_nd_local(Rei, Pr, Re_l)[0]/Rei, Re_l, Re)
    C_f = __integrate.quad(lambda Rei: external_flow_plate_l_nd_local(Rei, Pr, Re_l)[1], Re_l, Re)
    # external_flow_plate_l_nd_local(Rei, Pr, Re_l: Nusselt,C_f)
    # DNusselt_bar=integral(Nusselt/Rei,Rei, Re_l, Re)
    # DC_f_bar=integral(C_f, Rei, Re_l,Re)
    return Nusselt[0], C_f[0]
 
    
def __external_plate_nd_aux2(Pr, Re_u, Re_L): 
    # Returns: Nusselt_bar_turb, C_f_bar_turb
    #IntegralAutoStep Vary = 1 Min = 50 Max = 2000 Reduce = 1e-3 Increase = 1e-6
    # C_f_turb=(0.455/(log(0.06*Re)))**2
    def cfbar(Re):
        return (0.455/(log(0.06*Re)))**2
    C_f_bar = __integrate.quad(lambda Re: cfbar(Re), Re_u, Re_L)
    # Nusselt_turb=Re*Pr*(C_f_turb/2)/(1+12.7*(Pr**(2/3)-1)*sqrt(C_f_turb/2))
    Nusselt_bar_turb= __integrate.quad(lambda Re: Pr*(cfbar(Re)/2)/(1+12.7*(Pr**(2/3)-1)*sqrt(cfbar(Re)/2)), Re_u, Re_L)
    
    # Nusselt_bar_turb=integral(Nusselt_turb/Re,Re,Re_u,Re_L)
    # C_f_bar_turb=integral(C_f_turb,Re,Re_u,Re_L)
    return Nusselt_bar_turb[0], C_f_bar[0]
 
 
# Subprogram external_plate_nd_aux3(Pr, Re_u, Re_L: C_f_bar_turb)
#     #IntegralAutoStep Vary = 1 Min = 50 Max = 2000 Reduce = 1e-3 Increase = 1e-6
#     C_f_turb=0.455/(log(0.06*Re))**2
#     C_f_bar_turb=integral(C_f_turb,Re,Re_u,Re_L)
# }
 
 
def external_flow_inline_bank(fluid, T_in, T_out, T_s,  P, V, N_L, D,S_T,S_L): 
    r"""
    Calculates the average heat transfer coefficient, and total pressure drop over an inline bank of tubes.  Properties are evaluated at the film temperature.

    Parameters
    -----------
    fluid : str
        The fluid can be an ideal gas, a real fluid, a brine, or an incompressible fluid 
    T_in : float
        The free stream fluid temperature at the inlet.  
    T_out : float
        The free stream fluid temperature at the outlet.  
    T_s : float
        The surface temperature of the sphere.  
    P : float
        Pressure [Pa]
    u_inf  : float
        free stream velocity of flow in [m/s]
    N_L : float
        The number of rows of tubes
    D : float
          tube diameter in [m]
    S_T : float
        The transverse tube pitch in [m]
    S_L : float
        The longitudinal tube pitch in [m]

    Returns
    --------
    h : float
        average heat transfer coefficient in [W/m^2-K] 
    deltap : float
        total pressure drop 
    Nusselt : float
        average Nusselt number [-]
    Re : float
        Reynolds number [-], defined as :math:`Re=\frac{\rho\ V_{max}\ D}{\mu}` where :math:`V_{max} = \frac{S_T}{S_T-D} u_{\infty}`
    """
 
    a=S_T/D; b=S_L/D    #"pitch to diameter ratios"
    T_m=(T_in+T_out)/2    #"mean temperature of fluid, used to calculate fluid properties"
    rho, mu, k, c, Pr = getprops(fluid, T_m, P)
    rho_s, mu_s, k_s, c_s, Pr_s = getprops(fluid, T_s, P)
    
    V_max=S_T/(S_T-D)*V
    Re=rho*V_max*D/mu
    if (Re>2E6):  warning(f'Re is out of range for ExternalFlow_Inline_Bank.  The maximum value is {Re}')
    if (Re<30):  warning(f'Re is out of range for ExternalFlow_Inline_Bank.  The minimum value is {Re}')
    if (Pr<0.5):  warning(f'The range of Prandtl number in ExternalFlow_Inline_Bank should be greater than 0.5. The value is {Pr}')
    if (Pr>500):  warning(f'The range of Prandtl number in ExternalFlow_Inline_Bank should be less than 500. The value is {Pr}')
    if(b<1.25):  warning(f'The longitudinal pitch, S_L/D is out of range for ExternalFlow_Inline_bank. The minimum value is {b}')
    if(b>2.5):  warning(f'The longitudinal pitch, S_L/D is out of range for ExternalFlow_Inline_bank. The maximum value is {b}')    #"Note that EES will automatically interpolate to find value regardless of validity"
    if (10<Re) and (Re<=100):  
        C=0.80
        m=0.40

    if (100<Re) and (Re<=1000): 
        T_inf=T_in
        Re2=rho*V*D/mu
        Nusselt,C_d = external_flow_cylinder_nd(Re2,Pr_s) #"at Reynolds numbers between 100 and 1000, the Nusselt number can be approximated as a single isolated cylinder-"

    if (1000<Re) and (Re<=2e5): 
        if(S_T/S_L>0.7): 
            C=0.27
            m=0.63
        else:
            warning('S_T/S_L<0.7. For values of S_T/S_L< 0.7, experimental results show that heat transfer is inefficient and aligned tubes should not be used.')
        

    if (2e5<Re) and (Re<=2e6): 
        C=0.021
        m=0.84

    if (N_L<20) and ((Re<1e2) or (Re>1e3)):     #"question heRe-to apply the correction factor for rows of tubes less than 20 for small Re where the flow will definitely be laminar"
        C_2=lookup_data.Tube_Bank_Corr['Aligned']([N_L])[0]    #"Credit of Zukauskas from p. 484, Heat Transfer handbook by bejan and kraus"
        Nusselt=C_2*C*Re**m*Pr**0.36*(Pr/Pr_s)**(1/4)

    if (N_L>=20) and ((Re<1e2) or (Re>1e3)): 
        Nusselt=C*Re**m*Pr**0.36*(Pr/Pr_s)**(1/4)

    
    # "pressure drop"
    var=(a-1)/(b-1)
    Eu=lookup_data.inline_friction([b, Re])[0]
    xi=lookup_data.inline_xi([Re, var])[0]
    DELTAp_row=(1/2)*Eu*rho*V_max**2*xi    #"average pressure drop across 1 row"
    DELTAp=DELTAp_row*N_L  #*convert('Pa',UP#)
    h=Nusselt*k/D 
    return  h, DELTAp, Nusselt, Re
 
 
def external_flow_staggered_bank(fluid, T_in, T_out, T_s,  P, V, N_L, D,S_T,S_L): 
    r"""
    Calculates the heat transfer coefficient, h,  in [W/m**2-K] and pressure drop[Pa] for external cross flow through a staggered bank of cylinders    
    Properties are evaluated at the film temperature.

    Parameters
    -----------
    fluid : str
        The fluid can be an ideal gas, a real fluid, a brine, or an incompressible fluid 
    T_in : float
        The free stream fluid temperature at the inlet.  
    T_out : float
        The free stream fluid temperature at the outlet.  
    T_s : float
        The surface temperature of the sphere.  
    P : float
        Pressure [Pa]
    V  : float
        free stream velocity of flow in [m/s]
    N_L : float
        The number of rows of tubes
    D : float
          tube diameter in [m]
    S_T : float
        The transverse tube pitch in [m]
    S_L : float
        The longitudinal tube pitch in [m]

    Returns
    --------
    h : float
        average heat transfer coefficient in [W/m^2-K] 
    deltap : float
        total pressure drop 
    Nusselt : float
        average Nusselt number [-]
    Re : float
        Reynolds number [-], defined as :math:`Re=\frac{\rho\ V_{max}\ D}{\mu}` with V_max occuring in either the transverse or diagonal plane.
    """

    a=S_T/D; b=S_L/D    #"pitch to diameter ratios"
    T_m=(T_in+T_out)/2    #"mean temperature of fluid, used to calculate fluid properties"
    rho, mu, k, c, Pr = getprops(fluid,T_m, P)
    rho_s, mu_s, k_s, c_s, Pr_s = getprops(fluid,T_s, P)
    S_D=(S_L**2+(S_T/2)**2)**(1/2)
    if(S_D<(S_T+D)/2): 
        V_max=S_T/(2*(S_D-D))*V
    else:
        V_max=S_T/(S_T-D)*V

    Re=rho*V_max*D/mu
    if (Re>2E6):  warning(f'Re is out of range for ExternalFlow_StaggereD_Bank.  The maximum value is {Re}')
    if (Re<30):  warning(f'Re is out of range for ExternalFlow_Staggered_Bank.  The minimum value is {Re}')
    if (Pr<0.5):  warning(f'The range of Prandtl number in ExternalFlow_Staggered_Bank should be greater than 0.5. The value is {Pr}')
    if (Pr>500):  warning(f'The range of Prandtl number in ExternalFlow_Staggered_Bank should be less than 500. The value is {Pr}')
    if(a<1.25):  warning(f'The transverse pitch, S_T/D is out of range for ExternalFlow_Staggered_Bank. The minimum value is {a}')
    if(a>2.5):  warning(f'The transverse pitch, S_T/D is out of range for ExternalFlow_Staggered_Bank. The maximum value is {a}')    #"Note that EES will automatically interpolate to find value regardless of validity"
    if (10<Re) and (Re<=100):  
        C=0.90
        m=0.40
        Nusselt=C*(Re**m)*(Pr**(0.36))

    if (100<Re) and (Re<=1000): 
        T_inf=T_in
        Re2=rho*V*D/mu
        Nusselt,C_d = external_flow_cylinder_nd(Re2,Pr_s)  #"at Reynolds numbers between 100 and 1000, the Nusselt number can be approximated as a single isolated cylinder-"

    if (1000<Re) and (Re<=2e5): 
        if(S_T/S_L<2): 
            C=0.35*(S_T/S_L)**(1/5)
            m=0.60
        else:
            C=0.40    
            m=0.60
        
        Nusselt=C*(Re**m)*(Pr**(0.36))

    if (2e5<Re) and (Re<2e6): 
        if (Pr>0.65) and (Pr<0.75): 
            C=0.027*(S_T/S_L)**0.2
            m=0.8
            Nusselt=C*(Re**m)*(Pr**(0.36))    
        
        if (Pr>=0.75): 
            C=0.031*(S_T/S_L)**0.20
            m=0.80
            Nusselt=C*(Re**m)*(Pr**(0.36))    
        
        
    if (N_L<20) and (Re>1e3):     
        C_2=lookup_data.Tube_Bank_Corr['Staggered_High']([N_L])[0]    #"Credit of Zukauskas from p. 484, Heat Transfer handbook by bejan and kraus"
        Nusselt=C_2*C*Re**m*Pr**0.36*(Pr/Pr_s)**(1/4)

    if (N_L>=20) and ((Re<1e2) or (Re>1e3)): 
        Nusselt=C*Re**m*Pr**0.36*(Pr/Pr_s)**(1/4)

    
    "pressure drop"
    var=a/b
    Eu=lookup_data.staggered_friction([a, Re])[0]
    xi=lookup_data.staggered_xi([Re, var])[0]
    deltap_row=(1/2)*Eu*rho*V_max**2*xi    #"average pressure drop across 1 row"
    deltap=deltap_row*N_L #*convert('Pa',UP#)
    h=Nusselt*k/D 
    return  h, deltap, Nusselt, Re
 
 
def external_flow_finned_bank1(fluid, T,  P, V, N_L, D_t, S_T, S_L, D_f, th_f, p_f): 
    r"""
    This function returns the heat transfer coefficient, h,  in [W/m**2-K] and pressure drop[Pa] for external cross flow through an in-line bank of finned tubes    

    Parameters
    -----------
    fluid : string
        name of fluid
    T : float
        Mean temperature of fluid
    P : float
        average pressure of fluid
    V : float
        approach velocity
    N_L : float
        number of tube rows in flow direction
    D_t : float
        outer diameter of tube
    S_T : float
        transferse pitch
    S_L : float
        longitudinal pitch
    D_f : float
        outer diameter of fin
    th_f : float
        thickness of fin
    p_f : float
        fin pitch
    
    Returns
    --------
    h : float
        average heat transfer coefficient in [W/m^2-K] 
    deltap : float
        total pressure drop 
    Nusselt : float
        average Nusselt number [-]
    Re : float
        Reynolds number [-], defined as :math:`Re=\frac{\rho\ V_{max}\ D}{\mu}` with V_max occuring in either the transverse or diagonal plane.
    """

    if (V<=0):       warning(f'V must be positive in External_Flow_Finned_Bank1.  The value provided is {V}.')
    if (D_t<=0):     warning(f'D_t must be positive in External_Flow_Finned_Bank1.  The value provided is {D_t}.')
    if (p_f<=th_f):  warning(f'p_f must be greater than th_f in External_Flow_Finned_Bank1')
    
    L=1
    A_tube=L*pi*D_t*(p_f-th_f)/p_f   # "bare tube area per unit length"
    if (D_f<=D_t):  warning('D_f must be greater than D_t in External_Flow_Finned_Bank1')
    A_fin=2*pi*(D_f**2-D_t**2)/4*L/p_f   # "fin area per unit length"
    d_star=D_t*A_tube/(A_tube+A_fin)+A_fin*sqrt(0.785*(D_f**2-D_t**2))/(A_tube+A_fin)
    d_e=2*(p_f*(S_T-D_t)-2*th_f*(D_f-D_t)/2)/((D_f-D_t)+p_f)
    if (S_T<=D_t):  warning('S_T must be greater than D_t in External_Flow_Finned_Bank1')
    a=S_T/D_t
    if (S_L<=D_t):  warning('S_L must be greater than D_t in External_Flow_Finned_Bank1')
    b=S_L/D_t
    u=V*a/(a-1)   # "maximum velocity"
    rho, mu, k, c, Pr = getprops(fluid,T, P)
    Re=rho*u*d_star/mu
    if (Re>1.6E5):  warning(f'Re is out of range for External_Flow_Finned_Bank1.  The maximum value is {Re}')
    if (Re<4e3):  warning(f'Re is out of range for External_Flow_Finned_Bank1.  The minimum value is {Re}')
    
    Drat=d_star/d_e
    if (Drat>11.5):  warning(f'The value of d_star/d_e in External_Flow_Finned_Bank1 is out of range.  The maximum value is {Drat}')
    if (Drat<0.85):  warning(f'The value of d_star/d_e in External_Flow_Finned_Bank1 is out of range.  The minimum value is {Drat}')
    
    Prat=(b-1)/(a-1)
    if (Prat>2):  warning(f'The value of (b-1)/(a-1) in External_Flow_Finned_Bank1 is out of range.  The maximum value is {Drat}')
    if (Prat<0.5):  warning(f'The value of (b-1)/(a-1) in External_Flow_Finned_Bank1 is out of range.  The minimum value is {Drat}')
    
    Cz=0.738+1.509/(N_L-0.25)
    if (N_L>=6):  Cz=1
    Eu = 0.52*(Drat**0.3)*(Prat**0.68)*(Re**(-0.08))*Cz
    DELTAp=Eu*rho*u**2*N_L/2
    
    Re=rho*u*D_t/mu
    eps=(A_tube+A_fin)/A_tube
    if (Re>1E5):  warning(f'Re is out of range for External_Flow_Finned_Bank1.  The maximum value is {Re}')
    if (Re<5e3):  warning(f'Re is out of range for External_Flow_Finned_Bank1.  The minimum value is {Re}')
    if (eps>12):  warning(f'eps is out of range for External_Flow_Finned_Bank1.  The maximum value is {eps}')
    if (eps<5):  warning(f'eps is out of range for External_Flow_Finned_Bank1.  The minimum value is {eps}')
    Nusselt=0.29*(Re**0.633)*(eps**(-0.17))*(Pr**(1/3))*0.67
    h=Nusselt*k/D_t
 
    return  h, DELTAp, Nusselt, Re
 
 
def external_flow_finned_bank2(fluid, T,  P, V, N_L, D_t, S_T, S_L, D_f, th_f, p_f): 
    #returns:  h, DELTAp, Nusselt, Re
    #RequiredOutputs 1
    
    r"""
    This function returns the heat transfer coefficient, h,  in [W/m**2-K] and pressure drop[Pa] for external cross flow through a staggered bank of finned tubes    

    Parameters
    -----------
    fluid : string
        name of fluid
    T : float
        Mean temperature of fluid
    P : float
        average pressure of fluid
    V : float
        approach velocity
    N_L : float
        number of tube rows in flow direction
    D_t : float
        outer diameter of tube
    S_T : float
        transferse pitch
    S_L : float
        longitudinal pitch
    D_f : float
        outer diameter of fin
    th_f : float
        thickness of fin
    p_f : float
        fin pitch
    
    Returns
    --------
    h : float
        average heat transfer coefficient in [W/m^2-K] 
    deltap : float
        total pressure drop 
    Nusselt : float
        average Nusselt number [-]
    Re : float
        Reynolds number [-], defined as :math:`Re=\frac{\rho\ V_{max}\ D}{\mu}` with V_max occuring in either the transverse or diagonal plane.
    """

    if (V<=0):       warning(f'V must be positive in External_Flow_Finned_Bank1.  The value provided is {V}.')
    if (D_t<=0):     warning(f'D_t must be positive in External_Flow_Finned_Bank1.  The value provided is {D_t}.')
    if (p_f<=th_f):  warning(f'p_f must be greater than th_f in External_Flow_Finned_Bank1')

    L=1
    A_tube=L*pi*D_t*(p_f-th_f)/p_f    #"bare tube area per unit length"
    if (D_f<=D_t):  warning('D_f must be greater than D_t in External_Flow_Finned_Bank1')
    A_fin=2*pi*(D_f**2-D_t**2)/4*L/p_f   # "fin area per unit length"
    d_star=D_t*A_tube/(A_tube+A_fin)+A_fin*sqrt(0.785*(D_f**2-D_t**2))/(A_tube+A_fin)
    d_e=2*(p_f*(S_T-D_t)-2*th_f*(D_f-D_t)/2)/((D_f-D_t)+p_f)
    if (S_T<=D_t):  warning('S_T must be greater than D_t in External_Flow_Finned_Bank1')
    a=S_T/D_t
    if (S_L<=D_t):  warning('S_L must be greater than D_t in External_Flow_Finned_Bank1')
    b=S_L/D_t
    u=V*a/(a-1)   # "maximum velocity"
    if(a>(2*b**2-0.5)):  u=V*a/(2*sqrt((a**2/4)+b**2)-1)
    
    rho, mu, k, c, Pr = getprops(fluid,T, P)
    Re=rho*u*d_star/mu
    if (Re<2.2e3):  warning(f'Re is out of range for External_Flow_Finned_Bank1.  The minimum value is {Re}')
    
    Drat=d_star/d_e
    Cz=0.934+0.355/(N_L-0.667)
    if (N_L>=6):  Cz=1
    if (Re<1.8e5): 
        Eu = 5.4*(Drat**0.3)*(Re**(-0.25))*Cz
    else:
        Eu = 0.26*(Drat**0.3)*Cz

    DELTAp=Eu*rho*u**2*N_L/2
    
    Re=rho*u*D_t/mu
    eps=(A_tube+A_fin)/A_tube
    if (Re>1E5):  warning(f'Re is out of range for External_Flow_Finned_Bank1.  The maximum value is {Re}')
    if (Re<5e3):  warning(f'Re is out of range for External_Flow_Finned_Bank1.  The minimum value is {Re}')
    if (eps>12):  warning(f'eps is out of range for External_Flow_Finned_Bank1.  The maximum value is {eps}')
    if (eps<5):  warning(f'eps is out of range for External_Flow_Finned_Bank1.  The minimum value is {eps}')
    Nusselt=0.29*(Re**0.633)*(eps**(-0.17))*(Pr**(1/3))
    h=Nusselt*k/D_t
    return  h, DELTAp, Nusselt, Re

def external_flow_sphere_nd(Re,Pr): 
    r"""
    This function returns the Nusselt number[-] and drag coefficient C_d [-] for sphere in external flow.    
    The Reynolds number is calculated in terms of the diameter :math:`Re = \frac{\rho\ u_{\infty}\ D}{\mu}`. 
    Properties are evaluated at the film temperature, assuming an isothermal surface.

    Parameters
    ----------
    Re : float
        Reynolds number of the fluid
    Pr : float
        Prandtl number of the fluid

    Returns
    ----------
    Nusselt : float
        average Nusselt number [-]
    C_d : float
        drag coefficient, :math:`C_d = \frac{F_d}{\rho\ A_f\ u_{\infty}/2}`, where :math:`F_d` is the drag force and :math:`A_f` is the projected frontal area.
    """
    if (Re<=0):  Re=1e-5
    Nusselt=2+(0.4*Re**0.5+0.06*Re**(2/3))*Pr**0.4
    if (Re>2E5):  warning(f'Re is out of range for External_Flow_Sphere The maximum values is 2E5 and the value is {Re}')
    if (Pr<0.5) or (Pr>380):  warning(f'The range of Prandtl number in External_Flow_Sphere should be between 0.5 and 380.  The value is {Pr}')
    C_d=24/Re+6/(1+sqrt(Re))+0.4
    return Nusselt, C_d

 
def external_flow_cylinder_nd(Re,Pr): 
    r"""
    This function determines the Nusselt number[-] and the coefficient of drag, C_d [-],  for convection of a cylinder in crossflow relative to the cylinder's axis given the non-dimensional Reynold and Prandtl number
    The Reynolds number is calculated in terms of the diameter :math:`Re = \frac{\rho\ u_{\infty}\ D}{\mu}`. 
    Properties are evaluated at the film temperature, assuming an isothermal surface.

    Parameters
    ----------
    Re : float
        Reynolds number of the fluid
    Pr : float
        Prandtl number of the fluid

    Returns
    ----------
    Nusselt : float
        average Nusselt number [-]
    C_d : float
        drag coefficient, :math:`C_d = \frac{F_d}{\rho\ A_f\ u_{\infty}/2}`, where :math:`F_d` is the drag force and :math:`A_f` is the projected frontal area.
    """
    if (Re<=0):  Re=1e-5
    Nusselt=0.3+(0.62*Re**(1/2)*Pr**(1/3))/(1+(0.4/Pr)**(2/3))**(1/4)*(1+(Re/282000)**(5/8))**(4/5)    #"Churchill and Bernstein- valid for all Re tested experimentally and 0.2<Pr---FLUID properties are evaluated at film temperature"
    Pe=Pr*Re
    if (Pe<=0.2):  warning(f'The Peclet number (Pr*Re) in External_Flow_Cylinder should be greater than 0.2. The value is {Pe}')
    C_d=1.18+6.8/Re**0.89+1.96/Re**0.5-0.0004*Re/(1+3.64e-7*Re**2)  #"White 1991"
    if (Re>=1e7):  warning(f'The Reynolds number in External_Flow_Cylinder should be less than 1e7. The value is {Re}')
    return Nusselt, C_d

 
def external_flow_diamond_nd(Re,Pr): 
    r"""
    This function returns the Nusselt number[-] and drag coefficient C_d [-] for a diamond shape rod (no edge effects).    
    The Reynolds number is calculated in terms of the corner-to-corner length in the plane normal to the flow direction :math:`Re = \frac{\rho\ u_{\infty}\ W}{\mu}`. 
    Properties are evaluated at the film temperature, assuming an isothermal surface.

    Parameters
    ----------
    Re : float
        Reynolds number of the fluid
    Pr : float
        Prandtl number of the fluid

    Returns
    ----------
    Nusselt : float
        average Nusselt number [-]
    C_d : float
        drag coefficient, :math:`C_d = \frac{F_d}{\rho\ A_f\ u_{\infty}/2}`, where :math:`F_d` is the drag force and :math:`A_f` is the projected frontal area.
    """

    if (Re<5E3):  warning(f'Re is out of range for External_Flow_Diamond.  The minimum value is {Re}')
    if (Re>1E5):  warning(f'Re is out of range for ExternalFlow_Diamond The maximum value is {Re}')
    Nusselt=0.246*Re**0.588*Pr**(1/3)
    C_d=1.6 #{from White 5th ed Table 7.2 for Re>1E4}
    return Nusselt, C_d
    
 
def external_flow_square_nd(Re,Pr): 
    r"""
    # This function returns the Nusselt number[-] and drag coefficient C_d [-] for a square rod (no edge effects).    
    The Reynolds number is calculated in terms of the edge-to-edge length in the plane normal to the flow direction :math:`Re = \frac{\rho\ u_{\infty}\ W}{\mu}`. 
    Properties are evaluated at the film temperature, assuming an isothermal surface.

    Parameters
    ----------
    Re : float
        Reynolds number of the fluid
    Pr : float
        Prandtl number of the fluid

    Returns
    ----------
    Nusselt : float
        average Nusselt number [-]
    C_d : float
        drag coefficient, :math:`C_d = \frac{F_d}{\rho\ A_f\ u_{\infty}/2}`, where :math:`F_d` is the drag force and :math:`A_f` is the projected frontal area.
    """

    if (Re<5E3):  warning(f'Re is out of range for External_Flow_Square.  The minimum value is {Re}')
    if (Re>1E5):  warning(f'Re is out of range for External_Flow_Square.  The maximum value is {Re}')
    Nusselt=0.102*Re**0.675*Pr**(1/3)
    C_d=2.1 #{from White 5th ed Table 7.2 for Re>1E4}
    return Nusselt, C_d

  
def external_flow_hexagon1_nd(Re,Pr): 
    #returns: Nusselt, C_d
    #ExternalFlow_Square_ND
    # Inputs required are:
    # Reynolds and Prandtl number}
    r"""
    This function returns the Nusselt number[-] and drag coefficient C_d [-] for a hexagonal rod with the flat surface perpendicular to the flow (no edge effects).    
    The Reynolds number is calculated in terms of the point-to-point length in the plane normal to the flow direction :math:`Re = \frac{\rho\ u_{\infty}\ W}{\mu}`. 
    Properties are evaluated at the film temperature, assuming an isothermal surface.

    Parameters
    ----------
    Re : float
        Reynolds number of the fluid
    Pr : float
        Prandtl number of the fluid

    Returns
    ----------
    Nusselt : float
        average Nusselt number [-]
    C_d : float
        drag coefficient, :math:`C_d = \frac{F_d}{\rho\ A_f\ u_{\infty}/2}`, where :math:`F_d` is the drag force and :math:`A_f` is the projected frontal area.
    """
    if (Re<5E3):  warning(f'Re is out of range for External_Flow_Hexagon1.  The minimum value is {Re}')
    if (Re>1E5):  warning(f'Re is out of range for External_Flow_Hexagon1.  The maximum value is {Re}')
    C=0.160  
    n=0.668
    if (Re>1.95E4):  
        C=0.0385
        n=0.782

    Nusselt=C*Re**n*Pr**(1/3)
    C_d=0.7 
    return Nusselt, C_d

def external_flow_hexagon2_nd(Re,Pr): 
    r"""
    This function returns the Nusselt number[-] and drag coefficient C_d [-] for a hexagonal rod with the flat surface parallel to the flow (no edge effects).    
    The Reynolds number is calculated in terms of the edge-to-edge length in the plane normal to the flow direction :math:`Re = \frac{\rho\ u_{\infty}\ W}{\mu}`. 
    Properties are evaluated at the film temperature, assuming an isothermal surface.

    Parameters
    ----------
    Re : float
        Reynolds number of the fluid
    Pr : float
        Prandtl number of the fluid

    Returns
    ----------
    Nusselt : float
        average Nusselt number [-]
    C_d : float
        drag coefficient, :math:`C_d = \frac{F_d}{\rho\ A_f\ u_{\infty}/2}`, where :math:`F_d` is the drag force and :math:`A_f` is the projected frontal area.
    """    
    if (Re<5E3):  warning(f'Re is out of range for External_Flow_Hexagon2.  The minimum value is {Re}')
    if (Re>1E5):  warning(f'Re is out of range for External_Flow_Hexagon2.  The maximum value is {Re}')
    Nusselt=0.153*Re**0.638*Pr**(1/3)
    C_d=1.0 #{from White 5th ed Table 7.2 for Re>1E4}
    return Nusselt, C_d

 
def external_flow_verticalplate_nd(Re,Pr): 
    #returns: Nusselt, C_d
    #ExternalFlow_VerticalPlate_ND
    # Inputs required are:
    # Reynolds and Prandtl number}
    r"""
    # This function returns the Nusselt number[-] and drag coefficient C_d [-] for a vertical plate (no edge effects).    
    The Reynolds number is calculated in terms of the length of the plate in the plane normal to the flow direction :math:`Re = \frac{\rho\ u_{\infty}\ W}{\mu}`. 
    Properties are evaluated at the film temperature, assuming an isothermal surface.

    Parameters
    ----------
    Re : float
        Reynolds number of the fluid
    Pr : float
        Prandtl number of the fluid

    Returns
    ----------
    Nusselt : float
        average Nusselt number [-]
    C_d : float
        drag coefficient, :math:`C_d = \frac{F_d}{\rho\ A_f\ u_{\infty}/2}`, where :math:`F_d` is the drag force and :math:`A_f` is the projected frontal area.
    """
    if (Re<4E3):  warning(f'Re is out of range for External_Flow_VerticalPlate.  The minimum value is {Re}')
    if (Re>1.5E4):  warning(f'Re is out of range for External_Flow_VerticalPlate.  The maximum value is {Re}')
    Nusselt=0.228*Re**0.731*Pr**(1/3)
    C_d=2.0 #{from White 5th ed Table 7.2 for Re>1E4}
    return Nusselt, C_d


