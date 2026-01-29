from numpy import log, sqrt, log10, tanh, exp, pi, sin, acos
from scipy.special import iv as besseli, kv as besselk
from scipy.optimize import fsolve
import eeslib.fluid_properties as __fp
from eeslib.functions import g, sigma, convert
import eeslib.lookup_data as __ld

def __warning(msg,*args):
    print(f"Warning: {msg}	" + '	'.join(args))

def Nucleate_Boiling(Fluid, T_sat, T_w, C_s_f):
    """
    This function determines the heat flux caused by nucleate boiling of a fluid with a specified surface condition using the Rohsenow correlation - provided for backward compatibility
    
    Parameters
    --------    
    Fluid : string
        string variable representing a fluid/vapor in the EES database
    T_sat : float
        saturation temperature of fluid
    T_w : float
        temperature of surface
    C_s_f : float
        surface fluid coefficient (if not known: estimate as 0.013)
    n : float
        exponent n has value of 1 for water and 1.7 for other liquids
    """
     
    return Nucleate_Boiling_Rohsenow(Fluid, T_sat, T_w, C_s_f)
     
    
def Nucleate_Boiling_Rohsenow(Fluid, T_sat, T_w, C_s_f):
    """
    This function determines the heat flux caused by nucleate boiling of a fluid with a specified surface condition.
    
    Parameters
    --------
    Fluid : string
        string variable representing a fluid/vapor in the EES database
    T_sat : float
        saturation temperature of fluid
    T_w : float
        temperature of surface
    C_s_f : float
        surface fluid coefficient (if not known: estimate as 0.013)
    n : float
        exponent n has value of 1 for water and 1.7 for other liquids
    """
    rho_l=__fp.density(Fluid,T=T_sat,X=0)
    rho_g=__fp.density(Fluid,T=T_sat,X=1)
    # k_l=__fp.conductivity(Fluid,T=T_sat,X=0)
    mu_l=__fp.viscosity(Fluid,T=T_sat,X=0)
    c_l=__fp.specheat(Fluid,T=T_sat,X=0)
    Pr_l=__fp.prandtl(Fluid, T=T_sat, X=0)
    h_fg=__fp.enthalpy(Fluid,T=T_sat,X=1)-__fp.enthalpy(Fluid,T=T_sat,X=0)
    
    if Fluid.lower() in ['water','steam','steam_iapws']:
        n=1 
    else: 
        n=1.7
    sigma_1=__fp.surface_tension(Fluid, T=T_sat)
    DELTAT_e=T_w-T_sat
    return  mu_l*h_fg*((g*(rho_l-rho_g))/(sigma_1))**(1/2)*((c_l*DELTAT_e)/(C_s_f*h_fg*Pr_l**n))**3
    
    
def Nucleate_Boiling_Kutateladze(F,T_sat,T_w): # 
    Tcrit=__fp.t_crit(F)
    Ttriple=__fp.t_triple_point(F)
    if(T_sat>Tcrit): __warning('T_sat is greater than the critical temperature in Nucleate_Boiling_Kutateladze')
    if(T_w>Tcrit): __warning('T_w is greater than the critical temperature in Nucleate_Boiling_Kutateladze')
    if(T_sat<Ttriple): __warning('T_sat is less than the triple point temperature in Nucleate_Boiling_Kutateladze')
    if(T_w<Ttriple): __warning('T_w is less than the triple point temperature in Nucleate_Boiling_Kutateladze')
    if(T_w<=T_sat): __warning('T_w must be greater than T_sat in Nucleate_Boiling_Kutateladze')  
     
    rho_l=__fp.density(F,T=T_sat,X=0)    #density of saturated liquid
    rho_v=__fp.density(F,T=T_sat,X=1)    #density of saturated vapor
    mu_l=__fp.viscosity(F,T=T_sat,X=0)    #viscosity of saturated liquid
    cp_l=__fp.specheat(F,T=T_sat,X=0)            #specific heat capacity of saturated liquid
    Pr_l=__fp.prandtl(F,T=T_sat,X=0)        #Prandtl number of liquid
    sigma=__fp.surface_tension(F,T=T_sat) #surface tension
    Dh_lv=__fp.enthalpy_vaporization(F,T=T_sat) #latent heat
    P_sat=__fp.p_sat(F,T=T_sat)

    K_P=rho_l*P_sat/(rho_v*sqrt(g*sigma*(rho_l-rho_v)))
    Ja=cp_l*(T_w-T_sat)/Dh_lv
    q_dprime=mu_l*Dh_lv*sqrt(g*(rho_l-rho_v)/sigma)*(Ja*K_P**0.7/(Pr_l**0.65*881))**(1/0.3)
    return q_dprime
    
def Flow_Boiling(F, T_sat, G, d, x, q_dprime, Or):
    """
    This function just calls Flow_Boiling_shah.  It is provided for backward compatibility
    """
     #For backward compatibility
    h, T_w = Flow_Boiling_shah(F, T_sat, G, d, x, q_dprime, Or)
    return  h, T_w
    
    
def Flow_Boiling_shah(F, T_sat, G, d, x, q_dprime, Or):
    """
    This def calculates the convective boiling heat transfer coefficient using the Shah(1982): # correlation which is applicable for saturated boiling of Newtonian fluids flowing in pipes.
     
    Parameters
    --------
    F : string
        Fluid name
    T_sat : float
        saturation temperature 
    G : float
        mass velocity 
    d : float
        tube diameter  
    x : float
        quality (0 to 1)
    q_dprime : float
        heat flux 
    Or : string
        either 'Horizontal' or 'Vertical'
     
    Returns
    --------
    h : float
        heat transfer coefficient including convective boiling and nucleate boiling contributions 
    T_w : float
        estimated wall temperature 
    """
     
    x_h=x
         
    rho_l=__fp.density(F,T=T_sat,X=0)    #density of saturated liquid
    rho_v=__fp.density(F,T=T_sat,X=1)    #density of saturated vapor
    k_v=__fp.conductivity(F,T=T_sat,X=1)    #thermal conductivity of saturated vapor
    k_l=__fp.conductivity(F,T=T_sat,X=0)    #thermal conductivity of saturated liquid
    mu_v=__fp.viscosity(F,T=T_sat,X=1)    #viscosity of saturated vapor
    mu_l=__fp.viscosity(F,T=T_sat,X=0)    #viscosity of saturated liquid
    CF=1 #[-]
    h_fg=(__fp.enthalpy(F,T=T_sat,X=1)-__fp.enthalpy(F,T=T_sat,X=0))*CF   #enthalpy of vaporization in J/kg
    # sigma=__fp.surface_tension(F,T=T_sat)    #surface tension
    Pr_l=__fp.prandtl(F,T=T_sat,X=0)    #Prandtl of saturated liquid
    Pr_v=__fp.prandtl(F,T=T_sat,X=1)    #Prandtl of saturated vapor
    Re_l=G*d*(1-x)/mu_l    #Reynold's number for flow of saturated liquid    
    if(Re_l<2300):  
        x=1-2300*mu_l/(G*d)  
        Re_l=2300
    f=(1.58*log(Re_l)-3.28)**(-2)    #single phase liquid friction factor
    Nu_l =(f/2)*(Re_l-1000)*Pr_l/(1+12.7*sqrt(f/2)*(Pr_l**0.6667-1)) #liquid phase Nu - assumed to  be turbulent
    h_l=Nu_l*k_l/d    #saturated liquid phase heat transfer coefficient
    Re_v=G*d/mu_v    #Reynold's number for flow assuming all vapor    
    f=(1.58*log(Re_v)-3.28)**(-2)    #single phase friction factor
    if(Re_v>2300) :
        Nu_v = (f/2)*(Re_v-1000)*Pr_v/(1+12.7*sqrt(f/2)*(Pr_v**0.6667-1))  #vapor phase Nu - assumed to always be turbulent
    else:
        Nu_v=3.66;
        f=64/Re_v
    h_v=Nu_v*k_v/d  #vapor phase heat transfer coefficient, which should be a lower limit
    if(x>0.999): 
        h=h_v
    else:
        if(x<=0.0001):
            h=h_l
        else:
            Fr_L=G**2/(rho_l**2*g*d)    #Froude number
            Co=((1-x)/x)**0.8*(rho_v/rho_l)**0.5    #Convection number    
            Bo=q_dprime/(G*h_fg)    #Boiling number    
            if(Bo<0): __warning('The boiling number is less than zero.  Check the heat flux and mass velocity')
            N=Co
            if(Or.upper()=='HORIZONTAL') and (Fr_L<0.04): 
                N=0.38*Fr_L**(-0.3)*Co
            if(Bo>11e-4): 
                FF=14.7 
            else: 
                FF=15.43
            psi_cb=1.8/N**0.8            
            if(N>1): 
                if(Bo>0.3e-4):  
                    psi_nb=230*Bo**0.5 
                else: 
                    psi_nb=1+46*Bo**0.5
                psi=max(psi_nb,psi_cb)
            if(N<=1) and (N>0.1):
                psi_bs=FF*sqrt(Bo)*exp(2.74*N**(-0.1))
                psi=max(psi_cb,psi_bs)
            if(N<=0.1):
                psi_bs=FF*sqrt(Bo)*exp(2.47*N**(-0.15))
                psi=max(psi_bs,psi_cb)
            h=psi*h_l
    if(x!=x_h): 
        h=h_v+(x_h-1)*(h-h_v)/(x-1)        
    T_w=q_dprime/h+T_sat    #estimated wall temperature
     
    return h, T_w
    
    
def Flow_Boiling_Shah_Avg (F, T_sat, G, d, x_1, x_2, q_dprime, Or='horizontal'):
    """
    This function calculates the average convective boiling heat transfer coefficient by repeated use of the Shah(1982) correlation over the specificed quality range which is applicable for saturated boiling of Newtonian fluids flowing in pipes.  This program calls the Flow_Boiling_Shah procedure to determine the local heat transfer coefficient 
     
    
    Parameters
    --------
    F : string
        Fluid name
    T_sat : float
        saturation temperature 
    G : float
        mass velocity 
    d : float
        tube diameter  
    q_dprime : float
        heat flux    #enter 0 to calculate just the convective boiling contribution
    Or : float
        either 'Horizontal' or 'Vertical'
    x_1 : float
        lower quality limit  (0 to 1)
    x_2 : float
        upper quality limit  (0 to 1)
     
    Output:
    Flow_Boiling_Avg : float
        average heat transfer coefficient  for the specified range in quality including convective boiling and nucleate boiling contributions 
    
    """
    N=10
    SumH=0
    if(x_1<0) or (x_1>1):  __warning('quality must be between 0 and 1')
    if(x_2<0) or (x_2>1):  __warning('quality must be between 0 and 1')
    i=0
    x_last=x_1
    while(i<N+1):
        i=i+1
        x_old=x_last
        x_new=x_1+(x_2-x_1)*(i/N)
        x=(x_old+x_new)/2
        h_x, T_wx = Flow_Boiling(F, T_sat, G, d, x, q_dprime, Or)
        x_last=x_new
        SumH=SumH+h_x
    return SumH/(N)
     
    
def Flow_Boiling_Avg (F, T_sat, G, d, x_1, x_2, q_dprime, Or='horizontal'):
    # Private
    """
    This function just calls Flow_Boiling_Shah_avg.  It is provided for backward compatibility
    """
    return  Flow_Boiling_Shah_Avg(F, T_sat, G, d, x_1, x_2, q_dprime, Or)
    
    
    
def Flow_Boiling_Chen(F, T_sat, G, d, x, T_w): 
    """
    This procedure calculates the convective boiling heat transfer coefficient using the Chen (1966) correlation which is applicable for saturated boiling of pure fluids in vertical pipes
     
    Parameters
    --------
    F : string
        Fluid name
    T_sat : float
        saturation temperature 
    G : float
        mass velocity 
    d : float
        tube hydraulic diameter  
    x : float
        quality (0 to 1)
    T_w : float
        wall temperature 
     
    Returns
    --------
    h : float
        heat transfer coefficient including convective boiling and nucleate boiling contributions 
    q_dprime : float
        heat flux 
    
    """
         
    Tcrit=__fp.t_crit(F)
    Ttriple=__fp.t_triple_point(F)
    if(T_sat>Tcrit): __warning('T_sat is greater than the critical temperature in Flow_Boiling_Chen')
    if(T_w>Tcrit): __warning('T_w is greater than the critical temperature in Flow_Boiling_Chen')
    if(T_sat<Ttriple): __warning('T_sat is less than the triple point temperature in Flow_Boiling_Chen')
    if(T_w<Ttriple): __warning('T_w is less than the triple point temperature in Flow_Boiling_Chen')
    if(T_w<=T_sat): __warning('T_w must be greater than T_sat in Flow_Boiling_Chen')  
    if(G<0): __warning('G must be positive in Flow_Boiling_Chen')  
    if(d<0): __warning('d must be positive in Flow_Boiling_Chen')  
    if(x<0): __warning('x must be between 0 and 1 in Flow_Boiling_Chen')  
    if(x>1): __warning('x must be between 0 and 1 in Flow_Boiling_Chen')  
     
    rho_l=__fp.density(F,T=T_sat,X=0)    #density of saturated liquid
    rho_v=__fp.density(F,T=T_sat,X=1)    #density of saturated vapor
    k_v=__fp.conductivity(F,T=T_sat,X=1)    #thermal conductivity of saturated vapor
    k_l=__fp.conductivity(F,T=T_sat,X=0)    #thermal conductivity of saturated liquid
    mu_v=__fp.viscosity(F,T=T_sat,X=1)    #viscosity of saturated vapor
    mu_l=__fp.viscosity(F,T=T_sat,X=0)    #viscosity of saturated liquid
    cp_l=__fp.specheat(F,T=T_sat,X=0)            #specific heat capacity of saturated liquid
    Pr_l=__fp.prandtl(F,T=T_sat,X=0)        #Prandtl number of liquid
    sigma=__fp.surface_tension(F,T=T_sat) #surface tension
    Dh_lv=__fp.enthalpy_vaporization(F,T=T_sat) #latent heat
    P_sat=__fp.p_sat(F,T=T_sat)
    P_wall=__fp.p_sat(F,T=T_w)
     
    DT_sat=T_w-T_sat
    DP_sat=P_wall-P_sat
    alpha_FZ=0.00122*(k_l**0.79*cp_l**0.45*rho_l**0.49/(sigma**0.5*mu_l**0.29*Dh_lv**0.24*rho_v**0.24))*DT_sat**0.24*DP_sat**0.75
     
    Re_l=d*G*(1-x)/mu_l    #liquid Reynolds number
    alpha_l=0.023*Re_l**0.8*Pr_l**0.4*(k_l/d)    
     
    X_tt=((1-x)/x)**0.9*(rho_v/rho_l)**0.5*(mu_l/mu_v)**0.1
     
    if(Re_l<2800):    
        C = 12    #turbulent - viscous
    else:
        C = 20    #turbulent - turbulent
          
    if(Pr_l<2):    #for Pr_l much greater than unity
        F=(1/X_tt+0.213)**0.736
    else:
        phi_l_2 = 1 + C/X_tt + 1/X_tt**2    
        F=( (Pr_l + 1)/2 * phi_l_2)**.444
          
    Re_tp=Re_l*F**1.25
     
    S=1/(1+0.00000253*Re_tp**1.17)
     
    h=alpha_FZ*S+alpha_l*F
    q_dprime=h*(T_w-T_sat)
    
    return  h, q_dprime
    
    
def Flow_Boiling_Hamilton(F, P_sat, G_u, d_hu, x, q_u_dprime):
    """
    This procedure calculates the convective boiling heat transfer coefficient using the Hamilton(2008) correlation which is applicable for pure fluid and zeotropic mxitures in evaporators.
    
    Parameters
    --------
    F : string
        Fluid name
    P_sat : float
        saturation pressure 
    G : float
        mass velocity 
    d_h : float
        hydraulic diameter of passages  
    x : float
        quality (0 to 1)
    q_dprime : float
        heat flux 
     
    Returns
    --------
    h : float
        local  transfer coefficient 
    T_w : float
        estimated wall temperature 
    
    """
     
    if(x<0) or (x>1): __warning(f'The quality must be 0 and 1.  The value provided is {x}.')
    if(x>=1): x=0.999
    if(x<=0): x=0.001
    x_c=x
    x_l=0.06
    x=min(0.8,x)
    x=max(x_l,x)        

    rho_l=__fp.density(F,P=P_sat,X=0)    #density of saturated liquid
    rho_v=__fp.density(F,P=P_sat,X=1)    #density of saturated vapor        
    T_b=__fp.temperature(F,P=P_sat,X=0)    #bubble point temperature in K
    T_d=__fp.temperature(F,P=P_sat,X=1)    #dew point temperature in K
    k_v=__fp.conductivity(F,P=P_sat,X=1)    #thermal conductivity of saturated vapor
    k_l=__fp.conductivity(F,P=P_sat,X=0)    #thermal conductivity of saturated liquid
    mu_v=__fp.viscosity(F,P=P_sat,X=1)    #viscosity of saturated vapor
    mu_l=__fp.viscosity(F,P=P_sat,X=0)    #viscosity of saturated liquid
    q_dprime=q_u_dprime    #heat flux in SI units
    G=G_u    #total mass velocity in SI units
    if(G<70) or (G>370): __warning(f'The correlation is valid for 70 <G<370 kg/s-m**2.  The value provided for G is {G}.')
    d_h=d_hu    #hydraulic diameter in m
    h_fg=(__fp.enthalpy(F,P=P_sat,X=1)-__fp.enthalpy(F,P=P_sat,X=0))   #enthalpy of vaporization in J/kg
    Pr_l=__fp.prandtl(F,P=P_sat,X=0)    #Prandtl number of saturated liquid
    Re_l=G*d_h*(1-x)/mu_l    #Reynold's number for flow of saturated liquid    
    if(Re_l<2300):  
        x=1-2300*mu_l/G/d_h 
        Re_l=2300    
    P_r=P_sat/__fp.p_crit(F)    #reduced pressure
    M_w=__fp.molarmass(F)    #molar mass of refrigerant
    C1=0.51*x    #coefficients for the Hamilton correlation
    C2=5.57*x-5.21*x**2
    C3=0.54-1.56*x+1.42*x**2
    C4=-0.81+12.56*x-11.00*x**2
    C5=0.25-0.035*x**2
    C6app=1-15.4*(T_d-T_b)/T_b    #from KEDZIERSKI, Science and Technology for the Built Environment (2015) 21, 207–219
    Bo=q_dprime/(G*h_fg)    #Boiling number    
    if(Bo<0): __warning('The boiling number is less than zero.  Check the heat flux and mass velocity')
    h_SI=482.18*k_l/d_h*Re_l**0.3*Pr_l**C1*P_r**C2*Bo**C3*(-log10(P_r))**C4*M_w**C5*C6app #evaporative heat transfer coef. 
    if(x_c<x_l):  #interpolate betweehn the value at x_l and the single-phase liquid result
        f=(1.58*log(Re_l)-3.28)**(-2)    #single phase liquid friction factor
        Nu_l =(f/2)*(Re_l-1000)*Pr_l/(1+12.7*sqrt(f/2)*(Pr_l**0.6667-1)) #liquid phase Nu - assumed to  be turbulent
        h_l=Nu_l*k_l/d_h    #saturated liquid phase heat transfer coefficient
        arg=(0-x_c)/(0-x_l)*pi/2 #*Convert(rad,Utrig)
        h_SI=h_l+(h_SI-h_l)*sin(arg)    #interpolated between x=0 and x=0.1
    if(x_c>0.8):  #interpolate between value at 0.8 and single-phase vapor result
        Re_v=G*x_c*d_h/mu_v    #Reynold's number for vapor
        Pr_v=__fp.prandtl(F,P=P_sat,X=1)    #Prandtl number of saturated vapor
        Nu_v=0.023*Re_v**0.8*Pr_v**0.4    #Dittus-Boelter correlation for vapor
        h_v=Nu_v*k_v/d_h    #heat transfer coefficient for saturated vapor
        arg=(1-x_c)/(1-0.8)*pi/2 #*Convert(rad,Utrig)
        h_SI=h_v+(h_SI-h_v)*sin(arg)
    T_sat=T_b*(1-x)+x*T_d    #assume linear behavior in dome     
    T_wK=q_dprime/h_SI+T_sat    #estimated wall temperature in K
    h=h_SI #*convert('W/m**2-K',UH)    #heat transfer coefficient in user units
    T_w=T_wK #ConvertTemp(K,UT,T_wK)    #estimated wall temperature in user units
    
    return h, T_w 
    
    
def Flow_Boiling_Hamilton_avg(F, P_sat, G, d, x_1, x_2, q_dprime):
    """
    This function calculates the average convective boiling heat transfer coefficient by repeated use of the Hamilton(2008) correlation over the specificed quality range which is applicable for saturated boiling of pure fluids or blends in microfin tubes. This program calls the Flow_Boiling_Hamilton procedure to determine the local heat transfer coefficient 
    
    Parameters
    --------
    F : string
        Fluid name
    P_sat : float
        saturation pressure 
    G : float
        mass velocity 
    d : float
        tube diameter  
    q_dprime : float
        heat flux   
    x_1 : float
        lower quality limit  (0 to 1)
    x_2 : float
        upper quality limit  (0 to 1)
     
    Output:
    Flow_Boiling_avg : float
        average heat transfer coefficient  for the specified range in quality including convective boiling and nucleate boiling contributions 
    
    """
    N=10
    SumH=0
    if(x_1<0) or (x_1>1):  __warning('quality must be between 0 and 1')
    if(x_2<0) or (x_2>1):  __warning('quality must be between 0 and 1')
    i=0
    x_last=x_1
    while(i<N+1):
        i=i+1
        x_old=x_last
        x_new=x_1+(x_2-x_1)*(i/N)
        x=(x_old+x_new)/2
        h_x, T_wx = Flow_Boiling_Hamilton(F, P_sat, G, d, x, q_dprime)
        x_last=x_new
        SumH=SumH+h_x
    return SumH/(N)
    
def Critical_Heat_Flux(Fluid, Geom, L, T_sat):
    """
    Critical_Heat_Flux returns the critical heat flux  for the specified fluid and geometry.  

    Parameters
    --------
    Fluid : string
        a string constant or variable containing the name of a fluid defined in the EES data base.
    Geom : float
        a string constant or variable that is one of the following:  'PLATE', 'CYLINDER', 'SPHERE', 'OTHER'
    L : float
        the characteristic length  of the surface.  For a sphere or cylinder, set L = radius.  For a plate, set L = width. 
    T_sat : float
        saturation temperature of the fluid 
    """
    
    # __fp.enthalpy(Fluid,T=T_sat,X=1)-__fp.enthalpy(Fluid,T=T_sat,X=0)     
    DELTAi_vap=__fp.enthalpy_vaporization(Fluid, T=T_sat)
    rho_v_sat=__fp.density(Fluid,T=T_sat,X=1)
    rho_l_sat=__fp.density(Fluid,T=T_sat,X=0)
    sigma=__fp.surface_tension(Fluid,T=T_sat)
    g=9.81 #[m/s**2]
    L_char=sqrt(sigma/(g*(rho_l_sat-rho_v_sat)))
    C_crit=-1
    L_tilda=L/L_char
    if(Geom.upper()=='PLATE'):
        if(L_tilda>27): 
            C_crit=0.15
        else:
            C_crit=0.15*12*pi*L_char**2/(L**2)
    elif(Geom.upper()=='CYLINDER'):
        C_crit=0.12*L_tilda**(-0.25)
        if(C_crit<0.12): 
            C_crit=0.12  #SAK 9/9/16
    elif(Geom.upper()=='SPHERE'):
        if(L_tilda>4.26):
            C_crit=0.11
        else:
            C_crit=0.227*0.15**(-0.5)
            if(L_tilda>0.15) : 
                C_crit=0.227*L_tilda**(-0.5)   #<<<< TYPO in EES: L_tilta
            else: __warning(f'L_tilda is out of range for the critical heat flux calulation.  The value of L_tilda is {L_tilda}.')
    else:
        __warning(f'Invalid geometry passed to critical heat flux function: {Geom}')
    if(C_crit<0):  C_crit=0.12    #for large finite body

    return C_crit*DELTAi_vap*rho_v_sat*(sigma*g*(rho_l_sat-rho_v_sat)/rho_v_sat**2)**0.25
    
    
def __dp_over_dz_2phase_horiz(Fluid,m_dot_over_A,P,d,x):
    # Private
    """
    __dp_over_dz_2phase_horiz returns the pressure gradient in a horizontal tube in which a fluid is evaporating
    
    Parameters
    --------
    Fluid : string
        name of the real fluid that is evaporating
    m_dot_over_A : float
        mass flow rate divided by the cross-sectional areal
    P : float
        saturation pressure
    d : float
        inner diameter of the tube
    x : float
        local quality
    """
    rho_L=__fp.density(Fluid,P=P,X=0)
    mu_L=__fp.viscosity(Fluid,P=P,X=0)
    rho_g=__fp.density(Fluid,P=P,X=1)
    mu_g=__fp.viscosity(Fluid,P=P,X=1)
    Re_L=m_dot_over_A*d/mu_L
    f_L=0.079/Re_L**0.25
    Re_g=m_dot_over_A*d/mu_g
    f_g=0.079/Re_g**0.25
    a=f_L*2*m_dot_over_A**2/(d*rho_L)
    b=f_g*2*m_dot_over_A**2/(d*rho_g)
    G=a+2*(b-a)*x
    return G*(1-x)**(1/3)+b*x**3
     
    
def __mterm(Fluid,m_dot_over_A,x,P):
    # Private
     #This function returns terms used by DELTAP_2phase_horiz to calculate the momemtum rpessure drop
    if(x<=0): x=0.001
    if(x>=1): x=0.999    
    g=9.81 #[m/s**2]
    T=__fp.temperature(Fluid,P=P,X=x)
    sigma=__fp.surface_tension(Fluid,T=T)
    rho_L=__fp.density(Fluid,P=P,X=0)
    rho_g=__fp.density(Fluid,P=P,X=1)
    C_o=1+0.12*(1-x)
    U_gu=1.18*(1-x)*(g*sigma*(rho_L-rho_g)/rho_L**2)**(1/4)
    epsilon=x/rho_g/(C_o*(x/rho_g+(1-x)/rho_L)+U_gu/m_dot_over_A)

    return ((1-x)**2/(rho_L*(1-epsilon))+x**2/(rho_g*epsilon))
    
    
def Deltap_2Phase_Horiz(Fluid, G, P_i, d, L, x_in, x_out):
    """ 
    Function  DELTAP_2phase_horiz calculates DELTAP, the pressure drop in horizontal tubes in which there is two-phase heat transfer
    
    Parameters
    --------
    Fluid : string
        is a real fluid in the EES data base
    G : float
        is the mass velocity, i.e., the mass flow rate of fluid through the tube divided by the cross-sectional area of the tube
    P_i : float
        is the entering pressure
    d : float
        is the tube diameter
    x_in : float
        entering quality
    x_out : float
        exiting quality
    """

    m_dot_over_A=G
    x_1=x_in
    P=P_i
    N=10
    for i in range(N):
        x_2=x_in+(x_out-x_in)/N * (i+1)
        x=(x_2+x_1)/2
        P_1=P
        dp=__dp_over_dz_2phase_horiz(Fluid,m_dot_over_A,P,d,x)*L/N
        P_2=P_1-dp
        P_2=P_1-dp-(m_dot_over_A**2*(__mterm(Fluid,m_dot_over_A,x_2,P_2)-__mterm(Fluid,m_dot_over_A,x_1,P_1)))
        P_avg=(P_1+P_2)/2
        dp=__dp_over_dz_2phase_horiz(Fluid,m_dot_over_A,P_avg,d,x)*L/N    
        P=P-dp-(m_dot_over_A**2*(__mterm(Fluid,m_dot_over_A,x_2,P_2)-__mterm(Fluid,m_dot_over_A,x_1,P_1)))
        x_1=x_2           

    return abs(P_i-P) #*Convert('Pa',UP)
    
    
def __geth_bar(h_film,h_rad):
    def solve_h(vars):
        h = vars[0]
        lhs = h**(4/3)
        rhs = h_film**(4/3)+h_rad*h**(1/3)+0*h
        return lhs - rhs
    
    h_guess=sqrt(h_film**2+h_rad**2)

    h = fsolve(solve_h, [h_guess])[0]
     
    return h
    
    
    
def Film_Boiling(Fluid,Geom,T_sat,T_s,D,epsilon):
    """
    Film_Boiling returns the surface heat flux for film boiling of a fluid from a horizontal cylinder or sphere surface.
    
    Parameters
    --------
    Fluid : string
        string variable or constant representing a fluid/vapor in the EES data base
    Geom : float
        a string variable or constant specifying either 'SPHERE' or 'CYLINDER'
    T_sat : float
        the saturation temperature of the incoming vapor  
    T_s : float
        the temperature of the inside surface of the tube  
    D : float
        the diameter of the sphere or cylinder 
    epsilon : float
        the emittance of the surface.  (Set to 0 to eliminate radiation)
    Returns:  the film boiling heat flux (including radiation) 
    """
    P_sat=__fp.pressure(Fluid,T=T_sat,X=0)
    T_avg=(T_sat+T_s)/2
    k_v=__fp.conductivity(Fluid,T=T_avg,P=P_sat)
    mu_v=__fp.viscosity(Fluid,T=T_avg,P=P_sat)
    rho_v=__fp.density(Fluid,T=T_avg,P=P_sat)
    rho_l=__fp.density(Fluid,T=T_sat,X=0)
    C_pv=__fp.specheat(Fluid,T=T_avg,P=P_sat)
    h_fg=__fp.enthalpy(Fluid,T=T_sat,X=1)-__fp.enthalpy(Fluid,T=T_sat,X=0)
    C_film=0.62
    if(Geom.upper()=='SPHERE'): 
        C_film=0.67
    h_film=C_film*(g*k_v**3*rho_v*(rho_l-rho_v)*(h_fg+0.4*C_pv*(T_s-T_sat))/(mu_v*D*(T_s-T_sat)))**0.25
    h_rad=epsilon*sigma*(T_s**4-T_sat**4)/(T_s-T_sat)
    h_bar = __geth_bar(h_film,h_rad)
    q_dot_film=h_bar*(T_s-T_sat)
    return q_dot_film
    
    
def CHF_Local(P,G,X,D):
    r"""
    The function CHF_Local(P, G, X, D) returns the critical heat flux for flow boiling of water flowing through a vertical tube.  The function interpolates from the database presented by Groeneveld et al. (2007) which provides tables of CHF for 8 mm diameter tubes in the parameter space of mass flux, quality, and pressure.  The result is corrected for diameter using the method suggested by Groeneveld (2007):

    :math:`CHF_{Local} = CHF_{8 mm} \cdot \sqrt{\frac{0.008}{D}}`
    where CHF8 mm is the critical heat flux obtained by interpolation from the table.

    :math:`X_{in} = \frac{h_in - h_f}{h_g - h_f}`
    where h is the enthalpy and hf and hg are the enthalpies of saturated liquid and vapor, respectively.
    

    Parameters
    --------
    P : float
        pressure 
    G : float
        mass flux 
    X : float
        thermodynamic quality (note that a negative value indicated subcooled):
    D : float
        diameter 

    Returns
    --------
    CHF_Local - critical heat flux (W/m2)
    """        
    P_SI=P
    P_kPa=P*convert('Pa','kPa')
    G_SI=G
    D_SI=D
    
    if(X< -0.5) or (X>1):  __warning('quality must be between -0.5 and 1 in Function CHF_Local')
    if(P_kPa<100) or (P_kPa>21000):  __warning('pressure must be between 100 kPa and 21000 kPa in Function CHF_Local')
    if(G_SI<0) or (G_SI>8000):  __warning('mass flux must be between 0 kg/m**2-s and 8000 kg/m**2-s in Function CHF_Local')
    if(D < 0): __warning('Diameter must be greater than 0 in Function CHF_Local')
     
    P_array=[100, 300, 500, 1000, 2000, 3000, 5000, 7000, 10000, 12000, 14000, 16000, 18000, 20000, 21000]
    Table_array=[__ld.CHF100, __ld.CHF300, __ld.CHF500, __ld.CHF1000, __ld.CHF2000, __ld.CHF3000, __ld.CHF5000, __ld.CHF7000, __ld.CHF10000, __ld.CHF12000, __ld.CHF14000, __ld.CHF16000, __ld.CHF18000, __ld.CHF20000, __ld.CHF21000]
    
    for i in range(1,len(P_array)):
        if(P_kPa>=P_array[i-1]) and (P_kPa<=P_array[i]):
            fraction=(P_kPa-P_array[i-1])/(P_array[i]-P_array[i-1])
            CHF_low  = Table_array[i-1]([X, G_SI])[0]
            CHF_high = Table_array[i]  ([X, G_SI])[0]
            Chf=CHF_low+fraction*(CHF_high-CHF_low)
            Chf=Chf/sqrt(D_SI/0.008)
            break
    if(i==len(P_array)):
        __warning('Pressure is out of range in Function CHF_Local')
    return Chf*convert('kW','W')  #array values are stored as kW/m**2
    
    
def CHF_Tube(D, L, m_dot, P, X_in):
    r"""
    The procedure CHF_Tube(D, L, m_dot, P, X_in: CHF, T_in) returns the critical heat flux for flow boiling of water flowing through a vertical tube as well as the inlet temperature.  The function uses the technique presented by Groeneveld et al. (2007) to determine the maximum uniform heat flux that can be applied to a vertical tube with water flowing through it before the critical heat flux phenomenon is experienced at the outlet. 

    :math:`X_{in} = \frac{h_{in} - h_f}{h_g - h_f}`
    where hin is the inlet enthalpy and hf and hg are the enthalpies of saturated liquid and vapor, respectively.
    
    Parameters
    --------
    D : float
        diameter 
    L : float
        length 
    m_dot : float
        mass flow rate 
    P : float
        pressure 
    X_in : float
        thermodynamic quality at the inlet (note that a negative value indicated subcooled):
    """

    P_kPa=P
    D_SI=D
    m_dot_SI=m_dot #*convert(UMF,'kg/s')
    G_SI=m_dot_SI/(pi*D_SI**2/4)
    G=G_SI #*convert('kg/m**2-s',UG)
    if(X_in< -0.5) or (X_in>1):  __warning('inlet quality must be between -0.5 and 1 in Function CHF_Tube')
    if(P_kPa<100) or (P_kPa>21000):  __warning('pressure must be between 100 kPa and 21000 kPa in Function CHF_Tube')
    if(G_SI<0) or (G_SI>8000):  __warning('mass flux must be between 0 kg/m**2-s and 8000 kg/m**2-s in Function CHF_Tube')
    if(D < 0): __warning('Diameter must be greater than 0 in Function CHF_Tube')
    if(L < 0): __warning('Length must be greater than 0 in Function CHF_Tube')
    h_f=__fp.enthalpy('Water',P=P,X=0)    
    h_g=__fp.enthalpy('Water',P=P,X=1)
    h_fg=h_g-h_f
    h_in=h_f+X_in*h_fg
    T_in=__fp.temperature('Water',h=h_in,P=P)
    q_dot_max=m_dot*(h_g-h_in)
    A_s=pi*D*L
    HF_max=q_dot_max/A_s
    error=999
    HF=HF_max/2
    ic=0
    while(error > 0.001 and ic < 5001): 
        ic=ic+1
        h_out=h_in+HF*A_s/m_dot
        X_out=(h_out-h_f)/h_fg
        CHF=CHF_Local(P, G, X_out, D)
        error=abs(CHF-HF)/HF
        HF=(CHF+HF)/2
    return CHF, T_in


# ------------------------------------------------------------------------------------------
# ---- Condensation ------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------

def __Cond_Efan(t, r_1, r_2, h, k):
    # Private
    """
    Same function as eta_fin_annular_rect
    """
    
    if(h < 0): __warning(f'The heat transfer coefficient given is less than zero. The value for h is { h}.')
    if(k <= 0): __warning(f'The conductivity must be a finite positive value. The value for k is {k}.')
    if(t <= 0): __warning(f'the fin thickness must be a finite positive value. The value for t is {t}.')
    if((r_1<=0) or (r_2<=0)): __warning('Both the inside and outside radius specified must be a finite positive values.')
    if((r_2-r_1)<=0): __warning('The outer disk diameter must be greater than the inner disk diameter.')
    mro = r_2*sqrt(2*h/(k*t))
    ri_over_ro=r_1/r_2
    if(mro<0): __warning('Argument mro provided to eta_fin_annular_rect_ND is less than zero')
    if(ri_over_ro<0) or (ri_over_ro>1): __warning('Argument ri_over_ro provided to eta_fin_annular_rect_ND is less 0 or greater than 1')
    if(mro==0) or (ri_over_ro==1):
        res = 1
    else:
        if(ri_over_ro==0): 
            res=0
        else:
            res = 2*ri_over_ro*(besselk(1, mro*ri_over_ro)*besseli(1, mro)-besseli(1, mro*ri_over_ro)*besselk(1, mro))/(besselk(0, mro*ri_over_ro)*besseli(1, mro)+besseli(0, mro*ri_over_ro)*besselk(1, mro))/(mro*(1-(ri_over_ro)**2))
                
    return res
    
    
    
def Cond_HorizontalTube_Avg(Fluid, m_dot, T_sat, T_w, D, x_1, x_2):
    """
    This procedure determines the average heat transfer coefficient for a single component vapor transitioning to a liquid at saturation temperature. This procedure is for condensation in a pipe of diameter D. It calls the function Cond_HorizontalTube to determine the heat transfer coefficient at discrete values of quality between the values of x_1 and x_2.
    
    Parameters
    --------
    Fluid : string
        string variable corresponding to fluid in EES database
    m_dot : float
        mass flow rate of fluid through pipe
    T_sat : float
        saturation temperature of fluid at desired pressure
    T_w : float
        interior surface temperature of tube
    D : float
        inner diameter of tube 
    x_1 : float
        lower quality limit 
    x_2 : float
        upper quality limit
    """
    
    N=10
    SumH=0
    if(x_1<0) or (x_1>1):  __warning('quality must be between 0 and 1')
    if(x_2<0) or (x_2>1):  __warning('quality must be between 0 and 1')
    for i in range(N):
        x=x_1+(x_2-x_1)*(i/N)
        h_x = Cond_HorizontalTube(Fluid, m_dot,  x, T_sat, T_w, D)[0]
        SumH=SumH+h_x
    h_m=SumH/(N+1)
     
    return  h_m
    
    
    
def Cond_HorizontalTube(Fluid, m_dot,  x, T_sat, T_w, D ):
    """
    Cond_HorizonalTube
    This function determines the heat transfer coefficient for a single component liquid vapor mixture of quality x when forced through a pipe of diameter D at a mass flow rate of m_dot.  If m_dot=0, the procedure returns the heat transfer coefficient corresponding to film condensation.
    
    Parameters
    --------
    Fluid : string
        string variable corresponding to fluid in EES database
    m_dot : float
        mass flow rate of fluid through pipe:  Set to 0 for film condensation"
    x : float
        mass vapor fraction (quality) of fluid/vapor
    T_sat : float
        saturation temperature of fluid at desired pressure
    T_w : float
        interior surface temperature of tube
    D : float
        inner diameter of tube
    
    Returns
    --------
    h_m : float
        heat transfer coefficient
    F : string
        flow regime:  'stratified', 'annular', 'transition', or 'film'
    """
    
    rho_g=__fp.density(Fluid,T=T_sat,X=1)
    rho_l=__fp.density(Fluid,T=T_sat,X=0)
    k_l=__fp.conductivity(Fluid,T=T_sat,X=0)
    mu_l=__fp.viscosity(Fluid,T=T_sat,X=0)
    mu_g=__fp.viscosity(Fluid, T=T_sat, X=1)
    c_l=__fp.specheat(Fluid,T=T_sat,X=0)
    Pr_l=__fp.prandtl(Fluid, T=T_sat, X=0)
    h_fg=__fp.enthalpy(Fluid,T=T_sat,X=1)-__fp.enthalpy(Fluid,T=T_sat,X=0)    #heat of vaporization
    h_fg_prime=(h_fg+0.68*c_l*(T_sat-T_w))
    A_c=pi*D**2/4    #cross sectional area of pipe
    Gc=m_dot/A_c    #mass flow rate per unit area
    if(Gc<=0): Gc=1e-6
    if(x<0): __warning(f'The quality specified must be 0<=x<=1. The quality given was {x}.')
    if(m_dot<0): __warning(f'The mass flow rate must be a finite positive value. The value given was {m_dot}.')
    if(x<=0.001): x=0.001    #approximate value of quality--substituted because the Lockhart-Martinelli parameter is undefined at x=0
    if(x>0.999): x=0.999    #also undefined for x>=1
    X_tt=((1-x)/x)**0.9*(rho_g/rho_l)**(0.5)*(mu_l/mu_g)**0.1    #Lockhart-Martinelli parameter
    Re_Ls=Gc*D*(1-x)/mu_l    #superficial liquid Reynolds number
    Ga_L=(g*rho_l*(rho_l-rho_g)*D**3)/mu_l**2    #unit problems may occur here
    if(Re_Ls<=1250):    #flow transition as formulated by Soliman (1982)
        Fr_so=0.025*Re_Ls**1.59*((1+1.09*X_tt**0.039)/X_tt)**1.5*(1/Ga_L**0.5)
    else:
        Fr_so=1.26*Re_Ls**1.04*((1+1.09*X_tt**0.039)/X_tt)**1.5*(1/Ga_L**0.5)
        #annular flow
    Nusselt_m_a=0.023*Re_Ls**0.8*Pr_l**0.4*(1+(2.22/X_tt**0.89))
    h_m_a=Nusselt_m_a*k_l/D
    #stratified wavy
    alpha_g=1/(1+((1-x)/x)*(rho_g/rho_l)**(2/3))
    circ_frac=acos(2*alpha_g-1)/pi
    Fr_L=(Gc/rho_l)**2/(g*D)
    if Fr_L<=0.7:
        c_1=4.172+5.48*Fr_L-1.564*Fr_L**2
        c_2=1.773-0.169*Fr_L
    else:
        c_1=7.242
        c_2=1.655
    Nusselt_strat=0.0195*Re_Ls**0.8*Pr_l**0.4*(1.376+c_1/X_tt**c_2)**0.5 
    Re_go=Gc*D/mu_g
    Ja_L=c_l*(T_sat-T_w)/h_fg_prime
    if(Ja_L<1e-6): Ja_L=1e-6
    Nusselt_m_s=0.23*Re_go**0.12/(1+1.11*X_tt**0.58)*(Ga_L*Pr_l/Ja_L)**0.25+circ_frac*Nusselt_strat
    h_m_s=Nusselt_m_s*k_l/D
    Gc_cutoff=500
    if(Gc>Gc_cutoff): 
        h_m=h_m_a
        F='annular'
    else:
        if(Fr_so<6):
            h_m=h_m_s
            F='stratified'
        else:
            if(Fr_so<20):
                #proration between stratified wavy and annular
                n=6
                h_m=(h_m_s**(n)+h_m_a**(n))**(1/n)
                F='transition'
            else:
                #annular flow
                h_m=h_m_a
                F='annular'
                if(m_dot==0): #film condensation
                    F='film'
                    h_m=0.555*(g*rho_l*(rho_l-rho_g)*k_l**3*h_fg_prime/(mu_l*(T_sat-T_w)*D))**(1/4)
     
    return  h_m, F
    
    
    
def Cond_Horizontal_Cylinder(Fluid, T_sat, T_w, D):
    """
    Calculates the heat transfer coefficient and Nusselt number for condensation on a horizontal cylinder in quiescent saturated vapor.

    Notes:

    This procedure is responsible for determining the property data of the specified fluid . The latent heat of evaporation is modified based on the correction term given in Rohsenow (1998). This correction term accounts for condensate subcooling. The function Cond_Horizontal_Cylinder uses the correlation provided in Rohsenow (1998) as presented in section 7.4.3 of Nellis and Klein.

    Parameters
    --------
    Fluid : string
        string variable representing a fluid/vapor in the EES data base.
    T_sat : float
        the saturation temperature of the bulk vapor 
    T_w : float
        the wall temperature of the cylinder 
    D : float
        diameter of cylinder 

    Returns
    --------
    h_m : float
        the mean heat transfer coefficient in [W/m^2-K] 
    Nusselt_m : float
        the mean Nusselt number [-]
    """
     
    T_f=(T_sat+T_w)/2 
    rho_l=__fp.density(Fluid,T=T_f,X=0)
    rho_g=__fp.density(Fluid,T=T_sat,X=1)
    k_l=__fp.conductivity(Fluid,T=T_f,X=0)
    mu_l=__fp.viscosity(Fluid,T=T_f,X=0)
    c_l=__fp.specheat(Fluid,T=T_f,X=0)
    h_fg=__fp.enthalpy(Fluid,T=T_sat,X=1)-__fp.enthalpy(Fluid,T=T_sat,X=0)
    h_fg_prime=(h_fg+0.68*c_l*(T_sat-T_w))
    Nusselt_m=0.728*((rho_l*(rho_l-rho_g)*g*h_fg_prime*D**3)/(mu_l*(T_sat-T_w)*k_l))**(1/4)
    h_m=Nusselt_m*k_l/D    #based off of correlation in Handbook of Heat Transfer page 14.15
    
    return h_m, Nusselt_m
    
    
    
def Cond_Horizontal_n_Cylinders(Fluid, T_sat, T_w, D, N):
    """
    Cond_Horizontal_Cylinder_N
    This function returns the heat transfer coefficient for condensation on the exterior of a bank of N isothermal horizontal cylinder where N is the number of tubes in the vertical direction.  This routine calls Cond_Horizontal_Cylinder
    """
    h_m, Nusselt_m = Cond_Horizontal_Cylinder(Fluid,T_sat,T_w,D)
    h_m=h_m*N**(-1/6)   #from Eqn 7.10 of Kakac and Liu, Heat Exchangers
    Nusselt_m=Nusselt_m*N**(-1/6)
    
    return h_m, Nusselt_m
    
    
    
def Cond_Vertical_Plate(Fluid, L, W, T_w, T_sat ):
    """
    Calculates the heat transfer coefficient for condensation on a flat vertical plate in quiescent saturated vapor.  It also returns the equivalent Reynolds number, heat input and mass flow rate  for the condensate film.

    Notes:
    This procedure is responsible for determining the property data of the specifiedfluid . The latent heat of evaporation is modified based on the correction term developed by Rohsenow (1956). This correction term accounts for the nonlinearity of the temperature profile due to convection effects. The function Cond_Vertical_Plate combines three different correlations applying to three different ranges of Reynolds numbers  The correlations are recommended by Butterworth (1981) and partially based off of results determined by Labuntsov (1957)  as presented in section 7.4.3 of Nellis and Klein.
    
    Parameters
    --------
    Fluid : string 
        a fluid/vapor in the EES data base.
    L : float
        length of plate in direction of condensate film flow 
    W : float
        width of the plate 
    T_sat : float
        the saturation temperature of the bulk vapor   
    T_w : float
        the temperature of the plate  

    Returns
    --------
    h_m : float
         the mean heat transfer coefficient in [W/m^2-K] 
    Re_L : float
        Reynolds number for condensate film flow [-]
    q : float
        total heat transfer from plate to condensate [W] 
    m_dot : float
        mass flow rate of condensate film [kg/s] 
    """
     #determining fluid properties
    T_f=(T_sat+T_w)/2     #average temperature of fluid - used in determining fluid properties
    rho_l=__fp.density(Fluid,T=T_f,X=0)
    rho_g=__fp.density(Fluid,T=T_sat,X=1)
    k_l=__fp.conductivity(Fluid,T=T_f,X=0)
    mu_l=__fp.viscosity(Fluid,T=T_f,X=0)
    Pr_l=__fp.prandtl(Fluid, T=T_f, X=0)
    c_l=__fp.specheat(Fluid,T=T_f,X=0)
    h_fg=__fp.enthalpy(Fluid,T=T_sat,X=1)-__fp.enthalpy(Fluid,T=T_sat,X=0)
    h_fg_prime=h_fg+0.68*c_l*(T_sat-T_w)    #correction for enthalpy of vaporization provided by Rohsenow [13] Handbook of Heat Transfer page 14.6. This accounts for the nonlinearity of the condensate temperature profile, which accounts for convection effects
        
    Re_L=100 #guess value for Reynolds number
    Nterm=10
    for i in range(Nterm):
        h_m_l=1.47*(Re_L**(-1/3)*k_l)*(mu_l**2/(rho_l*(rho_l-rho_g)*g))**(-1/3)    #for reynolds numbers less than 30
        q_l=h_m_l*L*W*(T_sat-T_w)
        m_dot_l=q_l/h_fg_prime
        Re_L=(4*m_dot_l)/(mu_l*W)
    Re_L_l=Re_L    #set value for Reynolds number for laminar flow to check whether laminar guess valid
    for j in range(Nterm):
        j=j+1
        if(Re_L<0): Re_L=0.1        
        h_m_m=(Re_L*k_l)/(1.08*Re_L**(1.22)-5.2)*(mu_l**2/(rho_l*(rho_l-rho_g)*g))**(-1/3)    #for reynolds numbers between 30 and 1600 - source is Butterworth [18] is Handbook of Heat Transfer page 14.7
        q_m=h_m_m*L*W*(T_sat-T_w)
        m_dot_m=q_m/h_fg_prime
        Re_L=(4*m_dot_m)/(mu_l*W)
    Re_L_m=Re_L    #set value for Reynolds number for wavy flow to check whether wavy flow guess valid - source is Butterworth [18] if Handbook of Heat Transfer page 14.7
    k=0
    for k in range(Nterm):
        k=k+1    
        if(Re_L>150):    #If statement is present so that the correlation does not generate an error when low Re input--it should not be necessary to reset the value of Re_L prior to this call
            h_m_h=(Re_L*k_l)/(8750+58*Pr_l**(-1/2)*(Re_L**(3/4)-253))*(mu_l**2/(rho_l*(rho_l-rho_g)*g))**(-1/3)    #for reynolds numbers greater than 1600 - source is Labuntsov [23] in Fundamentals of Heat and Mass Transfer page 14.7
            q_h=h_m_h*L*W*(T_sat-T_w)
            m_dot_h=q_h/h_fg_prime
            Re_L=(4*m_dot_h)/(mu_l*W)
    Re_L_h=Re_L    #set value for Reynolds number for turbulent flow to check whether turbulent flow guess valid
     
    if(Re_L_l<=30):
        Re_L=Re_L_l
        h_m=h_m_l
        q=q_l
        m_dot=m_dot_l
    else:
        if((Re_L_m>30) and (Re_L_m<=1600)):
            Re_L=Re_L_m
            h_m=h_m_m
            q=q_m
            m_dot=m_dot_m
        else:
            if(Re_L_h>1600):
                Re_L=Re_L_h
                h_m=h_m_h
                q=q_h
                m_dot=m_dot_h
                    
     
    return h_m, Re_L, q, m_dot
    
    
    
def Cond_Finned_Tube(Fluid, d_r, d_o, t, p, T_w, T_sat, k_f):
    """
    Cond_Finned_Tube
    This function implements correlations suggested by Beatty and Katz [92] on page 14.23 of Handbook of Heat Transfer. This correlation completely neglects surface tension effects in order to derive a more simple expression.
    
    Parameters
    --------
    Fluid : string
        string variable corresponding to a fluid in EES database
    d_r : float
        root diameter of finned tube
    d_o : float
        outer diameter of finned tube
    t : float
        fin thickness
    p : float
        fin pitch
    T_w : float
        wall temperature of finned tube (assumed constant and uniform)
    T_sat : float
        bulk temperature of saturated vapor
    """
    DELTAT=(T_sat-T_w)
    #determining fluid properties
    T_f=(T_sat+T_w)/2    #average temperature of fluid - used in determining fluid properties
    rho_l=__fp.density(Fluid,T=T_f,X=0)
    rho_g=__fp.density(Fluid,T=T_sat,X=1)
    k_l=__fp.conductivity(Fluid,T=T_f,X=0)
    mu_l=__fp.viscosity(Fluid,T=T_f,X=0)
    c_l=__fp.specheat(Fluid,T=T_f,X=0)
    h_fg=__fp.enthalpy(Fluid,T=T_sat,X=1)-__fp.enthalpy(Fluid,T=T_sat,X=0)
    h_fg_prime=h_fg+0.68*c_l*(T_sat-T_w)    #correction for enthalpy of vaporization provided by Rohsenow [13] Handbook of Heat Transfer page 14.6. This accounts for the nonlinearity of the condensate temperature profile, which accounts for convection effects
    L=(1/p)    #unit length
    b=L-t    #unfinned length
    if(b<=0): __warning('The fin pitch and thickness specified result in geometry with undefined fins.')
     
    A_f=pi/2*(d_o**2-d_r**2)    #area of fin flanks
    A_u=pi*d_r*b    #area of unfinned tube
    L_bar=pi*(d_o**2-d_r**2)/(4*d_o)
    h_m=500    #guess value for heat transfer coefficient
    Nterm=3
    for i in range(Nterm):
        eta_f=__Cond_Efan(t, (d_r/2), (d_o/2), h_m, k_f)    #eta_annular_rect equivalent to determine fin efficiency
        A_eff=eta_f*A_f+A_u
        d_eq=1/(1.30*eta_f*(A_f/A_eff)*(1/L_bar**(1/4))+(A_u/A_eff)*(1/d_r**(1/4)))**(4)
        h_m=0.689*((rho_l**2*k_l**3*g*h_fg_prime)/(mu_l*DELTAT*d_eq))**(1/4)    #This correlation does not include condensation on the edges of the fins    
     
    return h_m
    
    
    
def Cond_Horizontal_Up(Fluid, L, T_w, T_sat):
    """
    Cond_Horizontal_plate_Up
    This function determines the average Nusselt number and heat transfer coefficient for a flat horizontal plate facing upwards. The condensate flow is driven by a hydrostatic pressure gradient. The correlation used is approximate and based off of the Nusselt-type analysis.
    
    Parameters
    --------
    Fluid : string
        string variable representing a fluid listed in EES database
    L : float
        characteristic length of the plate
    T_w : float
        temperature of the plate (assumed uniform and constant)
    T_sat : float
        temperature of saturated vapor
    """
    DELTAT=(T_sat-T_w)
    #determining fluid properties
    T_f=(T_sat+T_w)/2    #average temperature of fluid - used in determining fluid properties
    rho_l=__fp.density(Fluid,T=T_f,X=0)
    rho_g=__fp.density(Fluid,T=T_sat,X=1)
    k_l=__fp.conductivity(Fluid,T=T_f,X=0)
    mu_l=__fp.viscosity(Fluid,T=T_f,X=0)
    c_l=__fp.specheat(Fluid,T=T_f,X=0)
    h_fg=__fp.enthalpy(Fluid,T=T_sat,X=1)-__fp.enthalpy(Fluid,T=T_sat,X=0)
    h_fg_prime=h_fg+0.68*c_l*(T_sat-T_w)    #correction for enthalpy of vaporization provided by Rohsenow [13] Handbook of Heat Transfer page 14.6. This accounts for the nonlinearity of the condensate temperature profile, which accounts for convection effects
    Nusselt_m=0.82*((rho_l**2*g*h_fg_prime*L**3)/(mu_l*DELTAT*k_l))**(1/5)    #Nusselt number calculation based on the correlation developed by Nimmo and Leppert [111] in Handbook of Heat Transfer
    h_m=(Nusselt_m*k_l)/L
     
    return h_m, Nusselt_m
    
    
def Cond_Horizontal_Down(Fluid, T_w, T_sat):
    """
    Calculates the heat transfer coefficient and Nusselt number for condensation on a horizontal flat plate with the cooled side facing downward.

    Notes:
    This procedure is responsible for determining the property data of the fluid specified. The latent heat of evaporation is modified based on the correction term developed by Rohsenow (1956). This correction term accounts for the nonlinearity of the temperature profile due to convection effects. The function Cond_Horizontal_Down uses the correlation developed by Gerstmann and Griffith (1967) as presented in Nellis and Klein. This correlation is based on the condensate being removed as droplets, which formed due to Taylor instability on the condensate surface.
    
    Parameters
    --------
    Fluid : string
        string variable representing a fluid/vapor in the EES data base.
    T_w : float
        the temperature of the plate 
    T_sat : float
        the saturation temperature of the bulk vapor 

    Returns
    --------
    h_m : float
         the mean heat transfer coefficient in [W/m^2-K] 
    Nusselt_m : float
        the mean Nusselt number [-]
    """
    DELTAT=(T_sat-T_w)
    #determining fluid properties
    T_f=(T_sat+T_w)/2    #average temperature of fluid - used in determining fluid properties
    rho_l=__fp.density(Fluid,T=T_f,X=0)
    rho_g=__fp.density(Fluid,T=T_sat,X=1)
    k_l=__fp.conductivity(Fluid,T=T_f,X=0)
    mu_l=__fp.viscosity(Fluid,T=T_f,X=0)
    c_l=__fp.specheat(Fluid,T=T_f,X=0)
    h_fg=__fp.enthalpy(Fluid,T=T_sat,X=1)-__fp.enthalpy(Fluid,T=T_sat,X=0)
    h_fg_prime=h_fg+0.68*c_l*(T_sat-T_w)    #correction for enthalpy of vaporization provided by Rohsenow [13] Handbook of Heat Transfer page 14.6. This accounts for the nonlinearity of the condensate temperature profile, which accounts for convection effects
    sigma=__fp.surface_tension(Fluid, T=T_f)
    Ra=g*rho_l*(rho_l-rho_g)*h_fg_prime/(mu_l*DELTAT*k_l)*(sigma/(g*(rho_l-rho_g)))**(3/2)
    if(Ra<1e6) or (Ra>1e10): __warning(f'The Rayleigh number for Cond_Horizontal_Down must be 1e6<Ra<1e10. The Rayleigh number is {Ra}.')
    if(Ra<1e8):
        Nusselt_m=0.69*Ra**(0.20)
    else:
        Nusselt_m=0.81*Ra**(0.193)
    h_m=Nusselt_m*k_l*(sigma/(g*(rho_l-rho_g)))**(-1/2)
        
    return  h_m, Nusselt_m
    
    
    
def __Cond_Shah(OR, Gc, x, D, mu_L, mu_G, rho_L, rho_G, k_L, Pr_L, sigma, pr, CorrNo ):
    # Private
    if(x<=0.001): x=0.001    
    if(x>0.999): x=0.999    
    Re_Lo=Gc*D*(1-x)/mu_L    #superficial liquid Reynolds number
    h_Lo=0.023*Re_Lo**0.8*Pr_L**0.4*k_L/D    #heat transfer coefficient for the liquid phase flowing alone, Eqn. (6)
    Z=(1/x-1)**0.8*pr**0.4   #correlating parameters, Eqn (7)
    h_l=h_Lo*(1+3.8/Z**0.95)*(mu_L/(14*mu_G))**(0.0058+0.557*pr)    #Eqn (1)
    if(CorrNo==2): 
        Re_LT=Gc*D/mu_L    #Reynolds number for all mass as liquid
        h_LT=0.023*Re_LT**0.8*Pr_L**0.4*k_L/D    #Eqn. (16)
        h_l=h_LT*(1+1.128*x**0.817*(rho_L/rho_G)**0.3685*(mu_L/mu_G)**0.2363*(1-mu_G/mu_L)**2.144*Pr_L**(-0.1))    #Eqn (15)
    gg=9.872 #[m/s**2]    #always SI here
    h_Nu=1.32*Re_Lo**(-1/3)*(rho_L*(rho_L-rho_G)*gg*k_L**3/mu_L**2)**(1/3)    #Eqn(2)
    We_GT=Gc**2*D/(rho_G*sigma)    #weber number for all mass as vapor, Eqn (13)
    J_g=x*Gc/(gg*D*rho_G*(rho_L-rho_G))**0.5    #dimensionless vapor velocity, Eqn (10)
    h_TP=-1     
    if(OR.upper()=='HORIZONTAL'):
        if(We_GT>100) and (J_g>=0.98*(Z+0.263)**(-0.62)):  h_TP=h_l   #Regime I
        if(h_TP<0) and (We_GT>20) and (J_g<=0.95/(1.254+2.27*Z**1.249)): h_TP=h_Nu  #Regime III
        if(h_TP<0): h_TP=h_l+h_Nu
    else:
        if(We_GT>100) and (J_g>=1/(2.4*Z+0.73)): 
            h_TP=h_l     #Regime I
        if(h_TP<0) and (We_GT>20) and (J_g<=0.89-0.93*exp(-0.087*Z**(-1.17))): 
            h_TP=h_Nu  #Regime III
        if(h_TP<0): h_TP=h_l+h_Nu
        
    return  h_TP
    
def Cond_Tube(Fluid, theta, m_dot, x, T_sat, D ):
    """
    This function determines the heat transfer coefficient for a single component liquid vapor mixture at quality x according to the correlation of M.M. Shah, Int. J. of Refrigeration, Vol. 67, pp. 22-41, 2016
    
    Parameters
    --------
    Fluid : string
        string variable corresponding to fluid in EES database
    theta : float
        angle of tube between -90° (flow down) and 90° (flow up).  Horizontal is 0°
    m_dot : float
        mass flow rate of fluid through pipe:  
    x : float
        mass vapor fraction (quality) of fluid/vapor
    T_sat : float
        saturation temperature of fluid at desired pressure
    D : float
        inner diameter of tube
    h_TP : float
        heat transfer coefficient
    
    """
    theta_deg = theta * (180/pi) 
    if(x<0) or (x>1): __warning(f'The quality specified must be 0<=x<=1. The quality given was {x}.')
    if(m_dot<0): __warning(f'The mass flow rate must be a finite positive value. The value given was {m_dot}.')
    if(theta_deg<-90) or (theta_deg>90): __warning(f'The inclination must be between -90° (vertical down) and 90° (vertical up).  The value provided was {theta_deg}.')
    if(T_sat>__fp.t_crit(Fluid)): __warning(f'The temperature must be lower than the critical temperature.  The value provided was {T_sat}.')
    rho_L=__fp.density(Fluid,T=T_sat,X=0)
    rho_g=__fp.density(Fluid,T=T_sat,X=1)
    k_L=__fp.conductivity(Fluid,T=T_sat,X=0)
    mu_L=__fp.viscosity(Fluid,T=T_sat,X=0)
    mu_g=__fp.viscosity(Fluid, T=T_sat, X=1)
    Pr_L=__fp.prandtl(Fluid, T=T_sat, X=0)
    pr=__fp.pressure(Fluid,T=T_sat,X=0)/__fp.p_crit(Fluid)    #reduced pressure
    sigma=__fp.surface_tension(Fluid,T=T_sat)        
    m_dot_SI=m_dot
    D_SI=D
    A_c=pi*D_SI**2/4    #cross sectional area of pipe
    Gc=m_dot_SI/A_c    #mass flow rate per unit area
    if(Gc<=1e-6): Gc=1e-6
    mu_L_SI=mu_L
    mu_G_SI=mu_L
    rho_L_SI=rho_L
    rho_G_SI=rho_g
    k_L_SI=k_L
    sigma_SI=sigma
    CorrNo=1
    if(D_SI<0.003): CorrNo=2
    h_TP_SI = __Cond_Shah('horizontal', Gc, x, D_SI, mu_L_SI, mu_G_SI, rho_L_SI, rho_G_SI, k_L_SI, Pr_L, sigma_SI, pr, CorrNo )
    if(theta_deg<-30): 
        h_TP_SI_90 = __Cond_Shah('vertical', Gc, x, D_SI, mu_L_SI, mu_G_SI, rho_L_SI, rho_G_SI, k_L_SI, Pr_L, sigma_SI, pr, CorrNo )
        h_TP_SI=h_TP_SI+(h_TP_SI-h_TP_SI_90)*(theta_deg+(30))/(60)
    h_TP=h_TP_SI

    return  h_TP
    
    
    
def Cond_Tube_Avg(Fluid, theta, m_dot, T_sat, D, x_1, x_2):
    """
    This procedure determines the average heat transfer coefficient for a single component vapor transitioning to a liquid at saturation temperature using the correlations provided by Shah.  condensation in a pipe of diameter D. It calls the function Cond_HorizontalTube to determine the heat transfer coefficient at discrete values of quality between the values of x_1 and x_2.
    
    Parameters
    --------
    Fluid : string
        string variable corresponding to fluid in EES database
    theta : float
        angle of tube between -90° (flow down) and 90° (flow up).  Horizontal is 0°
    m_dot : float
        mass flow rate of fluid through pipe
    T_sat : float
        saturation temperature of fluid at desired pressure
    D : float
        inner diameter of tube 
    x_1 : float
        lower quality limit 
    x_2 : float
        upper quality limit
    """
    
    N=10
    SumH=0
    if(x_1<0) or (x_1>1):  __warning('quality must be between 0 and 1')
    if(x_2<0) or (x_2>1):  __warning('quality must be between 0 and 1')
    for i in range(N):
        x=x_1+(x_2-x_1)*(i/N)
        h_x = Cond_Tube(Fluid, theta, m_dot,  x, T_sat, D)
        SumH=SumH+h_x
    h_Avg=SumH/(N+1)
    
    return  h_Avg
    