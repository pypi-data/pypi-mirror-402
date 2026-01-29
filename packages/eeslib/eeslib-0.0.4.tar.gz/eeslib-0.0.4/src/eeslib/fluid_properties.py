# Author: Mike Wagner | esolab.engr.wisc.edu
# Property lookups are documented at the following URL:
# http://www.coolprop.org/coolprop/HighLevelAPI.html#parameter-table

# Install CoolProp using pip:
# >> pip install CoolProp


# CoolProp lookup strings:
# D: Density (kg/m³)
# C: Specific heat at constant pressure (J/kg-K)
# O: Specific heat at constant volume (J/kg-K)
# U: Internal energy (J/kg)
# H: Enthalpy (J/kg)
# S: Entropy (J/kg-K)
# P: Pressure (Pa)
# T: Temperature (K)
# X: Vapor quality (mol/mol) (mapped to 'Q' for CoolProp)
# V: Viscosity (Pa-s)
# L: Thermal conductivity (W/m-K)

import CoolProp.CoolProp as __CP

def __keymap(k):
    kl = k.lower()
    try:
        return {'x':'q'}[kl].upper()
    except:
        return k.upper()
def __expand_args(args):
    arg_flat = []
    for k,v in args.items():
        arg_flat += [__keymap(k),v]
    return tuple(arg_flat)

def enthalpy(fluid, **kwargs): #[J/kg]
    """
    Returns the specific enthalpy of the specified fluid in J/kg
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Key-value pairs specifying the state properties (e.g., T=300, P=101325, X=0.5, etc.)
    Returns
    -------
    Specific enthalpy in J/kg
    """
    return __CP.PropsSI("H", *__expand_args(kwargs), fluid)
def entropy(fluid, **kwargs):  #[J/kg-K]
    """
    Returns the specific entropy of the specified fluid in J/kg-K
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Key-value pairs specifying the state properties (e.g., T=300, P=101325, X=0.5, etc.)
    Returns
    -------
    Specific entropy in J/kg-K
    """
    return __CP.PropsSI("S", *__expand_args(kwargs), fluid)
def volume(fluid, **kwargs):   #[m^3/kg]
    """
    Returns the specific volume of the specified fluid in m^3/kg
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Key-value pairs specifying the state properties (e.g., T=300, P=101325, X=0.5, etc.)
    Returns
    -------
    Specific volume in m^3/kg
    """
    d = __CP.PropsSI("D", *__expand_args(kwargs), fluid)
    return 1./d
def density(fluid, **kwargs):  #[kg/m^3]
    """
    Returns the density of the specified fluid in kg/m^3
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Key-value pairs specifying the state properties (e.g., T=300, P=101325, X=0.5, etc.)
    Returns
    -------
    Density in kg/m^3
    """
    return __CP.PropsSI("D", *__expand_args(kwargs), fluid)
def temperature(fluid, **kwargs):  #[K]
    """
    Returns the temperature of the specified fluid in K
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Key-value pairs specifying the state properties (e.g., T=300, P=101325, X=0.5, etc.)
    Returns
    -------
    Temperature in K
    """
    return __CP.PropsSI("T", *__expand_args(kwargs), fluid)
def pressure(fluid, **kwargs):  #[K]
    """
    Returns the pressure of the specified fluid in Pa
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Key-value pairs specifying the state properties (e.g., T=300, P=101325, X=0.5, etc.)
    Returns
    -------
    Pressure in Pa
    """
    return __CP.PropsSI("P", *__expand_args(kwargs), fluid)
def quality(fluid, **kwargs):   #[0..1]
    """
    Returns the quality of the specified fluid (0-1)
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Key-value pairs specifying the state properties (e.g., T=300, P=101325, X=0.5, etc.)
    Returns
    -------
    Quality in range [0..1]
    """
    return __CP.PropsSI("Q", *__expand_args(kwargs), fluid)
def t_sat(fluid, P):  #[K]
    """
    Returns the saturation temperature of the specified fluid in K
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Key-value pairs specifying the state properties (e.g., T=300, P=101325, X=0.5, etc.)
    Returns
    -------
    Saturation temperature in K
    """
    return __CP.PropsSI("T", 'P', P, 'Q', 0.5, fluid)
def p_sat(fluid, T):  #[K]
    """
    Returns the saturation pressure of the specified fluid in Pa
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Key-value pairs specifying the state properties (e.g., T=300, P=101325, X=0.5, etc.)
    Returns
    -------
    Saturation pressure in Pa
    """
    return __CP.PropsSI("P", 'T', T, 'Q', 0.5, fluid)
def specheat(fluid, **kwargs):
    """
    Returns the specific heat of the specified fluid in J/kg-K
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Key-value pairs specifying the state properties (e.g., T=300, P=101325, X=0.5, etc.)
    Returns
    -------
    Specific heat in J/kg-K
    """
    return __CP.PropsSI("C", *__expand_args(kwargs), fluid)
def viscosity(fluid, **kwargs):
    """
    Returns the viscosity of the specified fluid in Pa-s
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Key-value pairs specifying the state properties (e.g., T=300, P=101325, X=0.5, etc.)
    Returns
    -------
    Viscosity in Pa-s
    """
    return __CP.PropsSI("V", *__expand_args(kwargs), fluid)
def conductivity(fluid, **kwargs):
    """
    Returns the conductivity of the specified fluid in W/m-K
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Key-value pairs specifying the state properties (e.g., T=300, P=101325, X=0.5, etc.)
    
    Returns
    -------
    Conductivity in W/m-K
    """
    return __CP.PropsSI("L", *__expand_args(kwargs), fluid)
def prandtl(fluid, **kwargs):
    """
    Returns the Prandtl number of the specified fluid
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Key-value pairs specifying the state properties (e.g., T=300, P=101325, X=0.5, etc.)
    Returns
    -------
    Prandtl number (dimensionless)
    """
    return __CP.PropsSI("PRANDTL", *__expand_args(kwargs), fluid)
def surface_tension(fluid, **kwargs):
    """
    Returns the surface tension of the specified fluid in N/m^2
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Key-value pairs specifying the state properties (e.g., T=300, P=101325, X=0.5, etc.)
    Returns
    -------
    Surface tension in N/m^2
    """
    kw = kwargs.copy()
    if 'X' in kw.keys():
        kw['Q'] = kw.pop('X')
    else:
        kw['Q'] = 0.5
    return __CP.PropsSI("surface_tension", *__expand_args(kw), fluid)
def t_triple_point(fluid, **kwargs):
    """
    Returns the triple point temperature of the specified fluid in K
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Not used
    
    Returns
    -------
    Triple point temperature in K
    """
    return __CP.PropsSI("TTRIPLE", fluid)
def p_triple_point(fluid, **kwargs):
    """
    Returns the triple point pressure of the specified fluid in Pa
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Not used
    
    Returns
    -------
    Triple point pressure in Pa
    """
    return __CP.PropsSI("PTRIPLE", fluid)
def t_crit(fluid, **kwargs):
    """
    Returns the critical temperature of the specified fluid in K
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Not used
    
    Returns
    -------
    Critical temperature in K
    """
    return __CP.PropsSI("TCRIT", fluid)
def p_crit(fluid, **kwargs):
    """
    Returns the critical pressure of the specified fluid in Pa
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Key-value pairs specifying the state properties (e.g., T=300, H=500000)
    
    Returns
    -------
    Critical pressure in Pa
    """
    return __CP.PropsSI("PCRIT", fluid)
def molarmass(fluid, **kwargs):
    """
    Returns the molar mass of the specified fluid in kg/kmol
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Not used
    
    Returns
    -------
    Molar mass in kg/kmol
    """
    return __CP.PropsSI("MOLARMASS", fluid)*1e3 #convert from kg/mol to kg/kmol
def enthalpy_vaporization(fluid, **kwargs):
    """
    Returns the enthalpy of vaporization of the specified fluid in J/kg
    
    Parameters
    ----------
    fluid : str
        Name of the fluid (e.g., 'Water', 'R134a', etc.)
    **kwargs : dict
        Not used
    
    Returns
    -------
    Enthalpy of vaporization in J/kg
    """
    kwhi = kwargs.copy()
    kwlo = kwargs.copy()
    kwhi['Q']=1.
    kwlo['Q']=0.
    return __CP.PropsSI('H', *__expand_args(kwhi), fluid) - __CP.PropsSI('H', *__expand_args(kwlo), fluid)

def get_fluids_list():
    """
    Returns a list of all available fluid names in CoolProp
    """
    return __CP.FluidsList()

def print_fluids_list():
    """
    Prints all available fluid names in CoolProp
    """
    fluids = __CP.FluidsList()
    print(f"Available fluids in CoolProp ({len(fluids)} total):")
    for fluid in sorted(fluids):
        print(f"  {fluid}")

