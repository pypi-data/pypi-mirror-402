import pytest
import numpy as np

from numpy import pi
from eeslib import boiling as B
from eeslib.functions import convert, converttemp
from eeslib.fluid_properties import pressure, t_sat

def approx(val, rel=1e-2):
    return pytest.approx(val, rel=rel)


class TestBoiling:
    def test_Nucleate_Boiling(self):
        Fluid = 'Water'
        C_s_f=0.013
        T_sat=converttemp('C','K',100) #[K]
        T_w=converttemp('C','K',105) #[K]

        q_dprime = B.Nucleate_Boiling(Fluid, T_sat, T_w, C_s_f)
        assert(isinstance(q_dprime, float))
        assert approx(q_dprime) == 17479 

    def test_Nucleate_Boiling_Rohsenow(self):
        Fluid = 'Water'
        C_s_f=0.013
        T_sat=converttemp('C','K',100) #[K]
        T_w=converttemp('C','K',105) #[K]
        q_dprime = B.Nucleate_Boiling_Rohsenow(Fluid, T_sat, T_w, C_s_f)
        assert(isinstance(q_dprime, float))
        assert approx(q_dprime) == 17479 

    def test_Nucleate_Boiling_Kutateladze(self):
        T_sat=100 #[K]
        DT=6 #[K]
        T_w=T_sat+DT
        Fluid='Oxygen'

        q_dprime = B.Nucleate_Boiling_Kutateladze(Fluid,T_sat,T_w)
        assert(isinstance(q_dprime, float))
        assert approx(q_dprime) == 47483 

    @pytest.mark.parametrize("func", [
        B.Flow_Boiling,
        B.Flow_Boiling_shah
        ])
    def test_Flow_Boiling(self, func):
        Fluid='R22'
        T_sat=250   #[K]         boiling saturation temperature
        G=200       #[kg/m^2-s]  mass velocity
        d=0.0172    #[m]         tube inner diameter
        x=0.05               #   quality
        q_dprime=15401    #   heat flux
        Or = 'horizontal'

        h, T_w = func(Fluid, T_sat, G, d, x, q_dprime, Or)
        assert(isinstance(h, float))
        assert approx(h) == 2021.5 
        # NOTE: This value differs from EES, which gives ~1890. The difference is caused by 
        # slight differences in saturated vapor viscosity calculations between EES and CoolProp.
        assert(isinstance(T_w, float))
        assert approx(T_w) == 257.6 

    @pytest.mark.parametrize("func,q_dprime,h_expected", [
        (B.Flow_Boiling_Avg, 18744, 2774.),
        (B.Flow_Boiling_Shah_Avg, 18744, 2774.),
        ])
    def test_Flow_Boiling_Avg(self, func, q_dprime, h_expected):
        # Fluid = 'R134a'
        Fluid='R22'
        T_sat=250   #[K]         boiling saturation temperature
        G=200       #[kg/m^2-s]  mass velocity
        d=0.0172    #[m]         tube inner diameter
        x_1=0.36               #   quality
        x_2=1.0               #   quality
        Or = 'horizontal'

        h = func(Fluid, T_sat, G, d, x_1, x_2, q_dprime)
        assert(isinstance(h, float))
        assert approx(h) == h_expected
        # NOTE: This value differs from EES, which gives ~1890. The difference is caused by 
        # slight differences in saturated vapor viscosity calculations between EES and CoolProp.


    def test_Flow_Boiling_Chen(self):
        Fluid='R245fa'
        T_sat=300 # [K] "boiling saturation temperature"
        G=200 # [kg/m^2-s]
        d=0.01 # [m]
        x=0.9   # "quality"
        T_w=303 # [K]

        h, q_dprime = B.Flow_Boiling_Chen(Fluid, T_sat, G, d, x, T_w)
        assert(isinstance(h, float))
        assert approx(h) == 4735.124
        assert(isinstance(q_dprime, float))
        assert approx(q_dprime) == 14205.37

    def test_Flow_Boiling_Hamilton(self):
        Fluid='R22'
        T_sat=250 # [K]                                "boiling saturation temperature"
        x=0.05   # "quality"
        P_sat=pressure(Fluid,T=T_sat,X=x)   # "saturation pressure"
        G=200 # [kg/m^2-s] "mass velocity"
        d=0.0172 # [m] "tube inner diameter"
        q_dprime=11929 

        h, T_w  = B.Flow_Boiling_Hamilton(Fluid, P_sat, G, d, x, q_dprime)
        assert(isinstance(h, float))
        assert approx(h) == 1408.6
        assert(isinstance(T_w, float))
        assert approx(T_w) == 258.8

    def test_Flow_Boiling_Hamilton_avg(self):
        Fluid='R22'
        T_sat=250   #[K]         boiling saturation temperature
        P_sat = pressure(Fluid,T=T_sat,X=0)   #saturation pressure
        G=200       #[kg/m^2-s]  mass velocity
        d=0.0172    #[m]         tube inner diameter
        x_1=0.36               #   quality
        x_2=1.0               #   quality
        Or = 'horizontal'
        q_dprime=9801
        
        h = B.Flow_Boiling_Hamilton_avg(Fluid, P_sat, G, d, x_1, x_2, q_dprime)
        assert(isinstance(h, float))
        assert approx(h) == 1271.

    def test_Critical_Heat_Flux(self):
        Fluid = 'R134a'
        L=0.035 #[m]                                                                            "width of plate"
        P=550e3 #[Pa]                                                                          "pressure of R134a"
        T_sat=t_sat(Fluid,P=P)                #"saturation temperature of R134a" 
        Geom = 'Plate'

        q_dprime = B.Critical_Heat_Flux(Fluid, Geom, L, T_sat)
        assert(isinstance(q_dprime, float))
        assert approx(q_dprime) == 454766 
        # NOTE: The value reported in EES help is 364437, which is incorrect 
        # based on the computed value in EES using the given parameters

    def test_Deltap_2Phase_Horiz(self):
        Fluid='R134a'
        d=12*convert('mm','m')
        P_i=pressure(Fluid,T=converttemp('C','K',4 ), X=0)
        L=1 #[m]
        x_in=0.35
        x_out=1.0
        m_dot=0.036 #[kg/s]
        A=pi*d**2/4
        G=m_dot/A

        dp = B.Deltap_2Phase_Horiz(Fluid, G, P_i, d, L, x_in, x_out)
        assert(isinstance(dp, float))
        assert approx(dp) == 9115

    def test_Film_Boiling(self):
        Fluid='Water'
        Geom='Cynlinder'
        epsilon=0.05
        D=5*convert('mm','m')
        T_s=converttemp('C','K',350)
        T_sat=converttemp('C','K',100)

        q_dot_film = B.Film_Boiling(Fluid,Geom,T_sat,T_s,D,epsilon)
        assert(isinstance(q_dot_film, float))
        assert approx(q_dot_film) == 59889 

    def test_CHF_Local(self):
        P=1500e3 # [Pa]
        X = 0.32 # [-]
        D=0.009 # [m]
        m_dot=0.1 # [kg/s]
        G=m_dot/(pi*D**2/4) 

        Chf  = B.CHF_Local(P,G,X,D)
        assert(isinstance(Chf, float))
        assert approx(Chf) == 3.608e6

    def test_CHF_Tube(self):
        P=1500e3 # [Pa]
        X_in = 0.32 # [-]
        D=0.009 # [m]
        L=1.0 # [m]
        m_dot=0.1 # [kg/s]

        CHF, T_in = B.CHF_Tube(D, L, m_dot, P, X_in)
        assert(isinstance(CHF, float))
        assert approx(CHF) == 1.079E+06 
        assert(isinstance(T_in, float))
        assert approx(T_in) == 471.4


class TestCondensationR134a:

    Fluid='R134a'
    m_dot=0.005 #[kg/s] 
    T_sat=273.15+50 #[K]
    T_w = 273.15+25 #[K]
    D=0.01 #[m]
    theta=0 #[rad]
    x = 0.2
    x_1=1
    x_2=0

    def test_Cond_HorizontalTube_Avg(self):
        h_m = B.Cond_HorizontalTube_Avg(self.Fluid, self.m_dot, self.T_sat, self.T_w, self.D, self.x_1, self.x_2)
        assert isinstance(h_m, float)
        assert approx(h_m) == 1176 

    def test_Cond_HorizontalTube(self):
        h_m, F = B.Cond_HorizontalTube(self.Fluid, self.m_dot, self. x, self.T_sat, self.T_w, self.D )
        assert isinstance(h_m, float)
        assert isinstance(F, str)
        assert approx(h_m) == 962.9 

    def test_Cond_Tube(self):
        h_TP = B.Cond_Tube(self.Fluid, self.theta, self.m_dot, self.x, self.T_sat, self.D )
        assert isinstance(h_TP, float)
        assert approx(h_TP) == 832.2

    def test_Cond_Tube_Avg(self):
        h_Avg = B.Cond_Tube_Avg(self.Fluid, self.theta, self.m_dot, self.T_sat, self.D, self.x_1, self.x_2)
        assert isinstance(h_Avg, float)
        assert approx(h_Avg) == 1401 

class TestCondensationWater:
    Fluid='water'
    D = 0.05 #[m]
    t=0.003 #[m]
    p=200 #[1/m]
    T_w=50+273.15 #[C]
    T_sat=100+273.15 #[C]

    def test_Cond_Horizontal_Cylinder(self):
        h_m, Nusselt_m = B.Cond_Horizontal_Cylinder(self.Fluid, self.T_sat, self.T_w, self.D)
        assert isinstance(h_m, float)
        assert isinstance(Nusselt_m, float)
        assert approx(h_m) == 6639
        assert approx(Nusselt_m) == 498.8

    def test_Cond_Horizontal_n_Cylinders(self):
        N = 6
        h_m, Nusselt_m = B.Cond_Horizontal_n_Cylinders(self.Fluid, self.T_sat, self.T_w, self.D, N)
        assert isinstance(h_m, float)
        assert isinstance(Nusselt_m, float)
        assert approx(h_m) == 4925 
        assert approx(Nusselt_m) == 371.1

    def test_Cond_Vertical_Plate(self):
        L = 1
        W = 0.25
        h_m, Re_L, q, m_dot = B.Cond_Vertical_Plate(self.Fluid, L, W, self.T_w, self.T_sat )
        assert isinstance(h_m, float)
        assert isinstance(Re_L, float)
        assert isinstance(q, float)
        assert isinstance(m_dot, float)
        assert approx(h_m) == 5247 

    def test_Cond_Finned_Tube(self):
        d_r=0.05 #[m]
        d_o=0.12 #[m]
        k_f=200 #[W/m-K]
        h_m = B.Cond_Finned_Tube(self.Fluid, d_r, d_o, self.t, self.p, self.T_w, self.T_sat, k_f)
        assert isinstance(h_m, float)
        assert approx(h_m) == 7188 

    def test_Cond_Horizontal_Up(self):
        L = 0.6
        h_m, Nusselt_m = B.Cond_Horizontal_Up(self.Fluid, L, self.T_w, self.T_sat)
        assert isinstance(h_m, float)
        assert isinstance(Nusselt_m, float)
        assert approx(h_m) == 749.5
        assert approx(Nusselt_m) == 677.7

    def test_Cond_Horizontal_Down(self):
        h_m, Nusselt_m = B.Cond_Horizontal_Down(self.Fluid, self.T_w, self.T_sat)
        assert isinstance(h_m, float)
        assert isinstance(Nusselt_m, float)
        assert approx(h_m) == 5577 
        assert approx(Nusselt_m) == 21.68


