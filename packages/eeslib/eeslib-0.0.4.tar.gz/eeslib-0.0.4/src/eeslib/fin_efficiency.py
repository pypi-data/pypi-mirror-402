from numpy import log, sqrt, log10, tanh, exp, pi
from scipy.special import iv as besseli, kv as besselk

def __warning(msg,*args):
    print(f"Warning: {msg}	" + '	'.join(args))

def Eta_Fin_ConstantCS_ConvTip(A_c, per, L, h, k): #
    """
    This function determines the efficiency of a fin with a constant cross-section of any shape given the area, perimeter, length, convection coefficient, and fin conductivity.
    The tip is assumed to convect.  The area used to define the fin efficiency INCLUDES the tip.
     
    Parameters
    --------
    A_c : float
        cross-sectional area
    per : float
        perimeter
    L : float
        length
    h : float
        heat transfer coefficient
    k : float
        fin conductivity
    """
    
    if(h < 0): __warning(f'The heat transfer coefficient given is less than zero. The value for h is { h}.')
    if(k <= 0): __warning(f'The conductivity must be a finite positive value. The value for k is {k}.')
    if(L <= 0): __warning(f'The fin depth must be a finite positive value. The value for L is {L}.')
    if(A_c <= 0): __warning(f'The cross-sectional area must be a finite positive value. The value for A_c is {A_c}.')
    if(per <= 0): __warning(f'The perimeter must be a finite positive value. The value for per is {per}.')
    m=sqrt(h*per/(k*A_c))
    mL=m*L
    AR_tip=A_c/(per*L)
    Eta_Fin_ConstantCS_ConvTip=Eta_Fin_ConstantCS_ConvTip_ND(mL,AR_tip)
    return Eta_Fin_ConstantCS_ConvTip
    
    
def Eta_Fin_ConstantCS_ConvTip_ND(mL, AR_tip): #
    """
    This function determines the efficiency of a fin with constant cross-section and convection from the tip given the dimensionless terms mL and AR_tip
    
    Parameters
    --------
    mL : float
        sqrt(h*per/(k*A_c))*L, dimensionless
    AR_tip : float
        A_c/(per*L)

    
     
    Returns
    --------
    fin efficiency : float
        the ratio of the heat transfer to the heat transfer if the fin had infinite conductivity
    """
    
    if(mL < 0): __warning('Argument mL provided to Eta_Fin_ConstantCS_ConvTip_ND is less than zero')
    if(AR_tip < 0): __warning('Argument AR_tip provided to Eta_Fin_ConstantCS_ConvTip_ND is less than zero')
    if(mL==0):
        Eta_Fin_ConstantCS_ConvTip_ND=1.0
    else:
        Eta_Fin_ConstantCS_ConvTip_ND= (tanh(mL)+mL*AR_tip)/(mL*(1+mL*AR_tip*tanh(mL))*(1+AR_tip))        
        
    return Eta_Fin_ConstantCS_ConvTip_ND
    
    
def Eta_Fin_ConstantCS(A_c, per, L, h, k): #
    """
    This function determines the efficiency of a fin with a constant cross-section of any shape given the area, perimeter, length, convection coefficient, and fin conductivity.
    The tip is assumed to be adiabatic and the length is NOT corrected to account for this.
    Parameters
    --------
    A_c : float
        cross-sectional area
    per : float
        perimeter
    L : float
        length
    h : float
        heat transfer coefficient
    k : float
        fin conductivity
    """
    
    if(h < 0): __warning(f'The heat transfer coefficient given is less than zero. The value for h is { h}.')
    if(k <= 0): __warning(f'The conductivity must be a finite positive value. The value for k is {k}.')
    if(L <= 0): __warning(f'The fin depth must be a finite positive value. The value for L is {L}.')
    if(A_c <= 0): __warning(f'The cross-sectional area must be a finite positive value. The value for A_c is {A_c}.')
    if(per <= 0): __warning(f'The perimeter must be a finite positive value. The value for per is {per}.')
    m=sqrt(h*per/(k*A_c))
    mL=m*L
    Eta_Fin_ConstantCS=Eta_Fin_ConstantCS_ND(mL)
    return Eta_Fin_ConstantCS
    
    
    
def Eta_Fin_ConstantCS_ND(mL): #
    """
    This function determines the efficiency of a fin with constant cross-section given the dimensionless term mL
    
    Parameters
    --------
    mL : float
        sqrt(h*per/(k*A_c))*L, dimensionless, where h - heat transfer coefficient, L - length of fin, b - fin thickness, k - conductivity
     
    Returns
    --------
    fin efficiency : float
        the ratio of the heat transfer to the heat transfer if the fin had infinite conductivity
    """
    
    if(mL < 0): __warning('Argument mL provided to Eta_Fin_ConstantCS_ND is less than zero')
    if(mL==0):
        Eta_Fin_ConstantCS_ND=1.0
    else:
        Eta_Fin_ConstantCS_ND= tanh(mL)/mL        
        
    return Eta_Fin_ConstantCS_ND
    
    
    
def Eta_Fin_Spine_Rect(D, L, h, k): #
    """
    This function determines the efficiency of a spine fin with a rectangular profile given the dimensions, convection coefficient, and fin conductivity

    Parameters
    --------
    h : float
        heat transfer coefficient
    k : float
        fin conductivity
    L : float
        fin length or depth
    D : float
        base diameter of fin
    """
    
    if(h < 0): __warning(f'The heat transfer coefficient given is less than zero. The value for h is { h}.')
    if(k <= 0): __warning(f'The conductivity must be a finite positive value. The value for k is {k}.')
    if(L <= 0): __warning(f'The fin depth must be a finite positive value. The value for L is {L}.')
    if(D <= 0): __warning(f'The base diameter must be a finite positive value. The value for D is {D}.')
    m=sqrt(4*h/(k*D))
    L_c=L+(D/4)
    mL=m*L_c
    Eta_Fin_Spine_Rect=Eta_Fin_Spine_Rect_ND(mL)
    return Eta_Fin_Spine_Rect
    
    
    
def Eta_Fin_Spine_Rect_ND(mL): #
    """
    This function determines the efficiency of a spine fin with a rectangular profile given the dimensionless term mL
    
    Parameters
    --------
    mL : float
        sqrt(4*h/(k*b))*L, dimensionless, where h - heat transfer coefficient, L - length of fin, b - fin thickness, k - conductivity

    Returns
    --------
    fin efficiency : float
        the ratio of the heat transfer to the heat transfer if the fin had infinite conductivity
    """
    
    if(mL < 0): __warning('Argument mL provided to Eta_Fin_Spine_Rect_ND is less than zero')
    if(mL==0):
        Eta_Fin_Spine_Rect_ND=1.0
    else:
        Eta_Fin_Spine_Rect_ND= tanh(mL)/mL        
        return Eta_Fin_Spine_Rect_ND
    
    
    
def Eta_Fin_Spine_Triangular(D, L, h, k): #
    """
    This function determines the efficiency of a spine fin with a triangular profile given the dimensions, convection coefficient, and fin conductivity

    Parameters
    --------
    h : float
        heat transfer coefficient
    k : float
        fin conductivity
    L : float
        fin length or depth
    D : float
        base diameter of fin
    """
    
    if(h < 0): __warning(f'The heat transfer coefficient given is less than zero. The value for h is { h}.')
    if(k <= 0): __warning(f'The conductivity must be a finite positive value. The value for k is {k}.')
    if(L <= 0): __warning(f'The fin depth must be a finite positive value. The value for L is {L}.')
    if(D <= 0): __warning(f'The base diameter must be a finite positive value. The value for D is {D}.')
    m=sqrt(4*h/(k*D))
    mL=m*L
    Eta_Fin_Spine_Triangular=Eta_Fin_Spine_Triangular_ND(mL)
    return Eta_Fin_Spine_Triangular
    
    
    
def Eta_Fin_Spine_Triangular_ND(mL): #
    """
    This function returns the efficiency of a spine fin with a triangular profile given the dimensionless parameter mL

    Parameters
    --------
    mL : float
        sqrt(4*h/(k*b))*L, dimensionless, where h - heat transfer coefficient, L - length of fin, b - fin thickness, k - conductivity
     
    Returns
    --------
    fin efficiency : float
        the ratio of the heat transfer to the heat transfer if the fin had infinite conductivity
    """
    
    if(mL < 0): __warning('Argument mL provided to Eta_Fin_Spine_Triangular_ND is less than zero')
    if(mL==0):
        Eta_Fin_Spine_Triangular_ND=1.0
    else:
        Eta_Fin_Spine_Triangular_ND = 2*besseli(2,2*mL)/(mL*besseli(1,2*mL))
        return Eta_Fin_Spine_Triangular_ND
    
    
    
def Eta_Fin_Spine_Parabolic(D, L, h, k): #
    """
    This function determines the efficiency of a spine fin with a concave parabolic profile given the dimensions, convection coefficient, and fin conductivity

    Parameters
    --------
    h : float
        heat transfer coefficient
    k : float
        fin conductivity
    L : float
        fin length or depth
    D : float
        base diameter of fin
    """
    
    if(h < 0): __warning(f'The heat transfer coefficient given is less than zero. The value for h is { h}.')
    if(k <= 0): __warning(f'The conductivity must be a finite positive value. The value for k is {k}.')
    if(L <= 0): __warning(f'The fin depth must be a finite positive value. The value for L is {L}.')
    if(D <= 0): __warning(f'The base diameter must be a finite positive value. The value for D is {D}.')
    m=sqrt(4*h/(k*D))
    mL=m*L
    Eta_Fin_Spine_Parabolic=Eta_Fin_Spine_Parabolic_ND(mL)
    return Eta_Fin_Spine_Parabolic
    
    
    
def Eta_Fin_Spine_Parabolic_ND(mL): #
    """
    This function returns the efficiency of a spine fin with a concave parabolic profile given the dimensionless parameter mL    
    Parameters
    --------
    mL : float
        sqrt(4*h/(k*b))*L, dimensionless, where h - heat transfer coefficient, L - length of fin, b - fin thickness, k - conductivity
     
    Returns
    --------
    fin efficiency : float
        the ratio of the heat transfer to the heat transfer if the fin had infinite conductivity
    """
    
    if(mL < 0): __warning('Argument mL provided to Eta_Fin_Spine_Parabolic_ND is less than zero')
    if(mL==0):
        Eta_Fin_Spine_Parabolic_ND=1.0
    else:
        Eta_Fin_Spine_Parabolic_ND = 2/(sqrt(4*mL**2/9+1)+1)
        
    return Eta_Fin_Spine_Parabolic_ND
    
    
    
def Eta_Fin_Annular_Rect(t, r_1, r_2, h, k): #
    """
    This function determines the efficiency of an annular spine fin with a rectangular profile given the dimensions, convection coefficient, and fin conductivity

    Parameters
    --------
    t : float
        thickness of fin
    r_1 : float
        inner diameter of annular disk
    r_2 : float
        outer diameter of annular disk
    h : float
        heat transfer coefficient
    k : float
        fin conductivity
    """
    
    if(h < 0): __warning(f'The heat transfer coefficient given is less than zero. The value for h is { h}.')
    if(k <= 0): __warning(f'The conductivity must be a finite positive value. The value for k is {k}.')
    if(t <= 0): __warning(f'The fin thickness must be a finite positive value. The value for t is {t}.')
    if((r_1<=0) or (r_2<=0)): __warning('Both the inside and outside radius specified must be a finite positive values.')
    if((r_2-r_1)<=0): __warning('The outer disk diameter must be greater than the inner disk diameter.')
    mro=r_2*sqrt(2*h/(k*t))
    ri_over_ro=r_1/r_2
    Eta_Fin_Annular_Rect=Eta_Fin_Annular_Rect_ND(mro, ri_over_ro)
    return Eta_Fin_Annular_Rect
    
    
    
def Eta_Fin_Annular_Rect_ND(mro,ri_over_ro): #
    """
    This function returns the efficiency of an annular fin with a rectangular profile given the dimensionless parameters mro and ri_over_ro

    
    h - heat transfer coefficient
    ro - outer radius of fin
    ri - inner radius of fin
    b - fin thickness
    k - conductivity

    Parameters
    --------
    mro : float
        sqrt(2*h/(k*b))*ro, dimensionless
    ri_over_ro : float
        ri/ro    
     
     
    Returns
    --------
    fin efficiency : float
        the ratio of the heat transfer to the heat transfer if the fin had infinite conductivity
    """
    
    if(mro<0): __warning('Argument mro provided to Eta_Fin_Annular_Rect_ND is less than zero')
    if(ri_over_ro<0) or (ri_over_ro>1): __warning('Argument ri_over_ro provided to Eta_Fin_Annular_Rect_ND is less 0 or greater than 1')
    if(mro==0) or (ri_over_ro==1):
        Eta_Fin_Annular_Rect_ND = 1
    else:
        if(ri_over_ro==0): 
            Eta_Fin_Annular_Rect_ND=0
        else:
            Eta_Fin_Annular_Rect_ND = 2*ri_over_ro*(besselk(1, mro*ri_over_ro)*besseli(1, mro)-besseli(1, mro*ri_over_ro)*besselk(1, mro))/(besselk(0, mro*ri_over_ro)*besseli(1, mro)+besseli(0, mro*ri_over_ro)*besselk(1, mro))/(mro*(1-(ri_over_ro)**2))
                
    return Eta_Fin_Annular_Rect_ND
    
    
    
def Eta_Fin_Straight_Rect(t, L, h, k): #
    """
    This function determines the efficiency of a straight fin with a rectangular profile given the dimensions, convection coefficient, and fin conductivity

    Parameters
    --------
    h : float
        heat transfer coefficient
    k : float
        fin conductivity
    L : float
        fin length or depth
    t : float
        base thickness of fin
    """
    
    if(h < 0): __warning(f'The heat transfer coefficient given is less than zero. The value for h is { h}.')
    if(k <= 0): __warning(f'The conductivity must be a finite positive value. The value for k is {k}.')
    if(L <= 0): __warning(f'The fin depth must be a finite positive value. The value for L is {L}.')
    if(t <= 0): __warning(f'The fin thickness must be a finite positive value. The value for t is {t}.')
    m=sqrt(2*h/(k*t))
    L_c=L+(t/2)
    mL=m*L_c
    Eta_Fin_Straight_Rect=Eta_Fin_Straight_Rect_ND(mL)
    return Eta_Fin_Straight_Rect
    
    
    
def Eta_Fin_Straight_Rect_ND(mL): #
    """
    This function returns the efficiency of a straight fin with a rectangular profile given the dimensionless parameter mL
    
    Parameters
    --------
    mL : float
        sqrt(h*2/(k*b))*L, dimensionless, where h - heat transfer coefficient, L - length of fin, b - fin thickness, k - conductivity
     
    Returns
    --------
    fin efficiency : float
        the ratio of the heat transfer to the heat transfer if the fin had infinite conductivity
    """
    
     
    if(mL < 0): __warning('Argument mL provided to Eta_Fin_Straight_Rect_ND is less than zero')
    if(mL==0):
        Eta_Fin_Straight_Rect_ND=1.0
    else:
        Eta_Fin_Straight_Rect_ND = tanh(mL)/mL        
        return Eta_Fin_Straight_Rect_ND
    
    
    
def Eta_Fin_Straight_Triangular(t, L, h, k): #
    """
    This function determines the efficiency of a straight fin with a triangular profile given the dimensions, convection coefficient, and fin conductivity

    Parameters
    --------
    h : float
        heat transfer coefficient
    k : float
        fin conductivity
    L : float
        fin length or depth
    t : float
        base thickness of fin
    """
    
    if(h < 0): __warning(f'The heat transfer coefficient given is less than zero. The value for h is { h}.')
    if(k <= 0): __warning(f'The conductivity must be a finite positive value. The value for k is {k}.')
    if(L <= 0): __warning(f'The fin depth must be a finite positive value. The value for L is {L}.')
    if(t <= 0): __warning(f'The fin thickness must be a finite positive value. The value for t is {t}.')
    m=sqrt(2*h/(k*t))
    mL=m*L
    Eta_Fin_Straight_Triangular=Eta_Fin_Straight_Triangular_ND(mL)
    return Eta_Fin_Straight_Triangular
    
    
    
def Eta_Fin_Straight_Triangular_ND(mL): #
    """
    This function returns the efficiency of a straight fin with a triangular profile given the dimensionless input mL    
    
    Parameters
    --------
    m : float
        sqrt(2*h/(k*b))*L, dimensionless, where h - heat transfer coefficient, L - length of fin, b - fin thickness, k - conductivity
     
    Returns
    --------
    fin efficiency : float
        the ratio of the heat transfer to the heat transfer if the fin had infinite conductivity
    """
    
    if(mL < 0): __warning('Argument mL provided to Eta_Fin_Straight_Triangular_ND is less than zero')
    if(mL==0):
        Eta_Fin_Straight_Triangular_ND=1.0
    else:
        Eta_Fin_Straight_Triangular_ND = besseli(1,2*mL)/(mL*besseli(0,2*mL))
        return Eta_Fin_Straight_Triangular_ND
    
    
    
def Eta_Fin_Straight_Parabolic(t, L, h, k): #
    """
    This function determines the efficiency of a straight fin with a concave parabolic profile given the dimensions, convection coefficient, and fin conductivity

    Parameters
    --------
    h : float
        heat transfer coefficient
    k : float
        fin conductivity
    L : float
        fin length or depth
    t : float
        base thickness of fin
    """
    
    if(h < 0): __warning(f'The heat transfer coefficient given is less than zero. The value for h is { h}.')
    if(k <= 0): __warning(f'The conductivity must be a finite positive value. The value for k is {k}.')
    if(L <= 0): __warning(f'The fin depth must be a finite positive value. The value for L is {L}.')
    if(t <= 0): __warning(f'The fin thickness must be a finite positive value. The value for t is {t}.')
    m=sqrt(2*h/(k*t))
    mL=m*L
    Eta_Fin_Straight_Parabolic=Eta_Fin_Straight_Parabolic_ND(mL)
    return Eta_Fin_Straight_Parabolic
    
    
    
def Eta_Fin_Straight_Parabolic_ND(mL): #
    """
    This function returns the efficiency of a straight fin with a concave parabolic profile given the dimensionless mL
    
    Parameters
    --------
    m : float
        sqrt(2*h/(k*b))*L, dimensionless, where h - heat transfer coefficient, L - length of fin, b - fin thickness, k - conductivity
     
    Returns
    --------
    fin efficiency : float
        the ratio of the heat transfer to the heat transfer if the fin had infinite conductivity
    """
    
    if(mL < 0): __warning('Argument mL provided to Eta_Fin_Straight_Parabolic_ND is less than zero')
    if(mL==0):
        Eta_Fin_Straight_Parabolic_ND=1.0
    else:
        Eta_Fin_Straight_Parabolic_ND = 2/(sqrt(4*mL**2+1)+1)
        return Eta_Fin_Straight_Parabolic_ND
    
    
    
def Eta_Fin_Spine_Parabolic2(D, L, h, k): #
    """
    This function determines the efficiency of a spine fin with a convex profile given the dimensions, convection coefficient, and fin conductivity

    Parameters
    --------
    h : float
        heat transfer coefficient
    k : float
        fin conductivity
    L : float
        fin length or depth
    D : float
        base diameter of fin
    """
    
    if(h < 0): __warning(f'The heat transfer coefficient given is less than zero. The value for h is { h}.')
    if(k <= 0): __warning(f'The conductivity must be a finite positive value. The value for k is {k}.')
    if(L <= 0): __warning(f'The fin depth must be a finite positive value. The value for L is {L}.')
    if(D <= 0): __warning(f'The base diameter must be a finite positive value. The value for D is {D}.')
    m=sqrt(4*h/(k*D))
    mL=m*L
    Eta_Fin_Spine_Parabolic2=Eta_Fin_Spine_Parabolic2_ND(mL)
    return Eta_Fin_Spine_Parabolic2
    
    
    
def Eta_Fin_Spine_Parabolic2_ND(mL): #
    """
    This function returns the efficiency of a spine fin with a parabolic convex profile given the dimensionless input mL    
    Parameters
    --------
    mL : float
        sqrt(4*h/(k*b))*L, dimensionless, where h - heat transfer coefficient, L - length of fin, b - fin thickness, k - conductivity 
    
    Returns
    --------
    fin efficiency : float
        the ratio of the heat transfer to the heat transfer if the fin had infinite conductivity
    """
    
    if(mL < 0): __warning('Argument mL provided to Eta_Fin_Spine_Parabolic2_ND is less than zero')
    if(mL==0):
        Eta_Fin_Spine_Parabolic2_ND=1.0
    else:
        Eta_Fin_Spine_Parabolic2_ND = 3/(2*sqrt(2))*(besseli(1,(4/3)*sqrt(2)*mL))/(mL*besseli(0,(4/3)*sqrt(2)*mL))
        #
    return Eta_Fin_Spine_Parabolic2_ND
    
    
    
def Eta_Fin_Straight_Parabolic2(t, L, h, k): #
    """
    This function determines the efficiency of a straight fin with a convex parabolic profile given the dimensions, convection coefficient, and fin conductivity

    Parameters
    --------
    h : float
        heat transfer coefficient
    k : float
        fin conductivity
    L : float
        fin length or depth
    t : float
        base thickness of fin
    """
    
    if(h < 0): __warning(f'The heat transfer coefficient given is less than zero. The value for h is { h}.')
    if(k <= 0): __warning(f'The conductivity must be a finite positive value. The value for k is {k}.')
    if(L <= 0): __warning(f'The fin depth must be a finite positive value. The value for L is {L}.')
    if(t <= 0): __warning(f'The fin thickness must be a finite positive value. The value for t is {t}.')
    m=sqrt(2*h/(k*t))
    mL=m*L
    Eta_Fin_Straight_Parabolic2=Eta_Fin_Straight_Parabolic2_ND(mL)
    return Eta_Fin_Straight_Parabolic2
    
    
    
def Eta_Fin_Straight_Parabolic2_ND(mL):
    """
    This function returns the efficiency of a straight fin with a convex parabolic shape    
    Parameters
    --------
    m : float
        sqrt(2*h/(k*b))*L, dimensionless, where h - heat transfer coefficient, L - length of fin, b - fin thickness, k - conductivity 
    
    Returns
    --------
    fin efficiency : float
        the ratio of the heat transfer to the heat transfer if the fin had infinite conductivity
    """
    
    
    if(mL < 0): __warning('Argument mL provided to Eta_Fin_Straight_Parabolic_ND is less than zero')
    if(mL==0):
        Eta_Fin_Straight_Parabolic2_ND=1.0
    else:
        Eta_Fin_Straight_Parabolic2_ND = 1/(mL)*besseli(2/3,4/3*mL)/besseli(-1/3,4/3*mL)
    return Eta_Fin_Straight_Parabolic2_ND
     