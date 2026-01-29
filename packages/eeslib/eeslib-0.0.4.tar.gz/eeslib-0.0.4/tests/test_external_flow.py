import math
import pytest

from eeslib import external_flow as ef


def approx(val, rel=1e-3):
    return pytest.approx(val, rel=rel)

def test_getprops():
    rho,mu,k,cp,Pr = ef.getprops('air', T=300, P=101325)
    assert isinstance(rho, float) and rho > 0  
    assert isinstance(mu, float) and mu > 0
    assert isinstance(k, float) and k > 0
    assert isinstance(cp, float) and cp > 0
    assert isinstance(Pr, float) and Pr > 0

    assert rho == approx(1.177)
    assert mu == approx(1.854e-5)
    assert k == approx(0.02638)
    assert cp == approx(1006.4)
    assert Pr == approx(0.707)

@pytest.mark.parametrize("func,Re,expected_Nu,expected_Cf", [
    (ef.external_flow_plate_nd_local,   1e3, 9.154,  0.021),
    (ef.external_flow_plate_nd_local,   1e6, 1666,   0.003752),
    (ef.external_flow_plate_nd,         1e3, 18.31,  0.042),
    (ef.external_flow_plate_nd,         1e6, 1283,   0.0029),
])
def test_external_flow_plate_nd(func, Re, expected_Nu, expected_Cf, Pr=0.7):

    Nusselt, C_f = func(Re, Pr)

    assert C_f == approx(expected_Cf, rel=1e-2)
    assert Nusselt == approx(expected_Nu)


@pytest.mark.parametrize("func,Re,Re_l,expected_Nu,expected_Cf", [
    (ef.external_flow_plate_l_nd,       1e3, 1e5,   18.31,  0.042),
    (ef.external_flow_plate_l_nd_local, 1e3, 1e5,   9.154,  0.021),
    (ef.external_flow_plate_l_nd,       1e6, 1e5,   1660,   0.004223),
    (ef.external_flow_plate_l_nd_local, 1e6, 1e5,   1489,   0.003759),
    (ef.external_flow_plate_l_nd,       1e6, -75,   581.1,  0.004768),
    (ef.external_flow_plate_l_nd_local, 1e6, -75,   289.5,  0.003759),
    (ef.external_flow_plate_l_nd,       1e6, 1e4,   0,      0),
    (ef.external_flow_plate_l_nd_local, 1e6, 1e4,   0,      0),
])
def test_external_flow_plate_l_nd(func, Re, Re_l, expected_Nu, expected_Cf, capsys, Pr=0.7):
    Nusselt, C_f = func(Re, Pr, Re_l)

    if Re_l > 3e4 or Re_l < 0:
        assert C_f == approx(expected_Cf, rel=1e-2)
        assert Nusselt == approx(expected_Nu, rel=1e-2)
    else: 
        captured = capsys.readouterr()
        assert 'External_Flow_Plate_ND' in captured.out

def test_external_flow_sphere_nd_small_Re():
    # For Re <= 0 the function internally sets Re to 1e-5
    Re_in = 0
    Pr = 0.7
    Nusselt, C_d = ef.external_flow_sphere_nd(Re_in, Pr)

    # Nusselt should be just above 2 for extremely small Re
    assert Nusselt > 2.0
    # Drag coefficient should be very large for the tiny Re substitution
    assert C_d > 1e3


@pytest.mark.parametrize("func,Re,Pr,exp_Nu,exp_C", [
    (ef.external_flow_diamond_nd,       1e4, 0.7, 49.0, 1.6),
    (ef.external_flow_cylinder_nd,      1e4, 0.7, 53.3, 1.095),
    (ef.external_flow_square_nd,        1e4, 0.7, 45.5, 2.1),
    (ef.external_flow_hexagon1_nd,      1e4, 0.7, None, 0.7),
    (ef.external_flow_hexagon2_nd,      1e4, 0.7, None, 1.0),
    (ef.external_flow_verticalplate_nd, 1e4, 0.7, None, 2.0),
])
def test_various_shapes_nd(func, Re, Pr, exp_Nu, exp_C):
    Nusselt, C_d = func(Re, Pr)
    assert isinstance(Nusselt, float)
    assert isinstance(C_d, float)
    # If we provided an expected Nusselt, check approximate numeric agreement
    if exp_Nu is not None:
        assert Nusselt == approx(exp_Nu, rel=2e-2)
    # Check drag coefficient equals expected (where applicable)
    assert C_d == approx(exp_C, rel=1e-3)

def test_inline_bank():
    T_s=328 # [K]
    Fluid ='air'
    P=101300  # [Pa]
    u_inf=0.9 # [m/s]
    D=0.5 # [m]
    T_in=370 # [K]
    T_out=350 # [K]
    N_L=13
    S_T=1.1 # [m]
    S_L=1.0 # [m]
    h, DeltaP, Nusselt, Re = ef.external_flow_inline_bank(Fluid, T_in, T_out, T_s,  P, u_inf, N_L, D,S_T,S_L)
    
    DELTAp_expected = 2.343 # [Pa]
    h_expected = 10.958 # [W/m^2-K]
    Nusselt_expected = 179.7 
    Re_expected = 38055 

    assert DELTAp_expected == approx(DeltaP, rel=1e-2)
    assert h_expected == approx(h, rel=1e-2)      
    assert Nusselt_expected == approx(Nusselt, rel=1e-2)
    assert Re_expected == approx(Re, rel=1e-2)

def test_staggered_bank():
    T_s=328 # [K]
    Fluid ='air'
    P=101300 # [Pa]
    u_inf=0.9 # [m/s]
    D=0.5 # [m]
    T_in=370 # [K]
    T_out=350 # [K]
    N_L=13
    S_T=1.1 # [m]
    S_L=1.0 # [m]

    h, DELTAp, Nusselt, Re = ef.external_flow_staggered_bank(Fluid, T_in, T_out, T_s,  P, u_inf, N_L, D,S_T,S_L)

    DELTAp_expected = 4.494 # [Pa]
    h_expected = 10.55 # [W/m^2-K]
    Nusselt_expected = 171.8 
    Re_expected = 37939 

    assert DELTAp_expected == approx(DELTAp, rel=1e-2)
    assert h_expected == approx(h, rel=1e-2)      
    assert Nusselt_expected == approx(Nusselt, rel=1e-2)
    assert Re_expected == approx(Re, rel=1e-2)

def test_finned_bank1():
    Fluid ='Air'
    T = 400 # [K]
    P=101325 # [Pa]
    V=25 # [m/s]
    N_L=10
    D_t=0.005 # [m]
    S_T=0.025 # [m]
    S_L=0.02 # [m]
    D_f=0.015 # [m]
    th_f=0.002 # [m]
    p_f=0.005 # [m]


    h, DELTAp, Nusselt, Re = ef.external_flow_finned_bank1(Fluid, T,  P, V, N_L, D_t, S_T, S_L, D_f, th_f, p_f)

    DELTAp_expected = 879.7 # [Pa]
    h_expected = 198.4 # [W/m^2-K]
    Nusselt_expected = 30.22 
    Re_expected = 6016 

    assert DELTAp_expected == approx(DELTAp, rel=1e-2)
    assert h_expected == approx(h, rel=2e-2)      
    assert Nusselt_expected == approx(Nusselt, rel=1e-2)
    assert Re_expected == approx(Re, rel=1e-2)

def test_finned_bank2():
    Fluid ='Air'
    T = 400 # [K]
    P=101325 # [Pa]
    V=25 # [m/s]
    N_L=10
    D_t=0.005 # [m]
    S_T=0.025 # [m]
    S_L=0.02 # [m]
    D_f=0.015 # [m]
    th_f=0.002 # [m]
    p_f=0.005 # [m]


    h, DELTAp, Nusselt, Re = ef.external_flow_finned_bank2(Fluid, T,  P, V, N_L, D_t, S_T, S_L, D_f, th_f, p_f)

    DELTAp_expected = 2195 # [Pa]
    h_expected = 296.2 # [W/m^2-K]
    Nusselt_expected = 45.1 
    Re_expected = 6016 

    assert DELTAp_expected == approx(DELTAp, rel=1e-2)
    assert h_expected == approx(h, rel=2e-2)      
    assert Nusselt_expected == approx(Nusselt, rel=1e-2)
    assert Re_expected == approx(Re, rel=1e-2)


if __name__ == "__main__":
    # test_inline_bank()
    # test_staggered_bank()
    # test_finned_bank1()
    # test_finned_bank2()
    pass