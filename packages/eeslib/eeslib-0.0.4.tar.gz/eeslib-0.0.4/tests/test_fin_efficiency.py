"""
Tests for fin_efficiency module.
"""
import pytest
from eeslib import fin_efficiency as fe


class TestConstantCS:
    """Test constant cross-section fin efficiency functions"""
    
    # Class-level variables shared by all test methods
    h_bar = 20  # [W/m^2-K]
    L = 0.1  # [m]
    A_c = 0.001  # [m^2]
    per = 0.01  # [m]
    k = 15  # [W/m-K]

    def test_Eta_Fin_ConstantCS_ConvTip(self):
        """Test Eta_Fin_ConstantCS_ConvTip with convective tip"""
        result = fe.Eta_Fin_ConstantCS_ConvTip(self.A_c, self.per, self.L, self.h_bar, self.k)
        assert result == pytest.approx(0.8680, rel=1e-2)

    def test_Eta_Fin_ConstantCS(self):
        """Test Eta_Fin_ConstantCS with adiabatic tip"""
        result = fe.Eta_Fin_ConstantCS(self.A_c, self.per, self.L, self.h_bar, self.k)
        assert result == pytest.approx(0.9578, rel=1e-2)


class TestSpine:
    """Test spine fin efficiency functions"""

    L=0.075 # [m]
    D=0.005 # [m]
    h=60 # [W/m^2-K]
    k=200 # [W/m-K]

    def test_Eta_Fin_Spine_Rect(self):
        """Test rectangular spine fin efficiency"""
        result = fe.Eta_Fin_Spine_Rect(self.D, self.L, self.h, self.k)
        assert result == pytest.approx(0.7008 , rel=.01)

    def test_Eta_Fin_Spine_Triangular(self):
        """Test triangular spine fin efficiency"""
        result = fe.Eta_Fin_Spine_Triangular(self.D, self.L, self.h, self.k)
        assert result == pytest.approx(0.8309 , rel=.01)

    def test_Eta_Fin_Spine_Parabolic(self):
        """Test concave parabolic spine fin efficiency"""
        result = fe.Eta_Fin_Spine_Parabolic(self.D, self.L, self.h, self.k)
        assert result == pytest.approx(0.883 , rel=.01)

    def test_Eta_Fin_Spine_Parabolic2(self):
        """Test convex parabolic spine fin efficiency"""
        result = fe.Eta_Fin_Spine_Parabolic2(self.D, self.L, self.h, self.k)
        assert result == pytest.approx(0.6634 , rel=.01)


class TestAnnular:
    """Test annular fin efficiency functions"""

    def test_Eta_Fin_Annular_Rect(self):
        r_in=0.01 # [m]
        r_out=0.03  # [m]
        th=0.004  # [m]
        h=60  # [W/m^2-K]
        k=200  # [W/m-K]

        """Test rectangular annular fin efficiency"""
        result = fe.Eta_Fin_Annular_Rect(th, r_in, r_out, h, k)
        assert result == pytest.approx(0.9666, rel=1e-3)


class TestStraight:
    """Test straight fin efficiency functions"""
    L=0.06 # [m]
    th=0.003 # [m]
    h=60 # [W/m^2-K]
    k=200 # [W/m-K]

    def test_Eta_Fin_Straight_Rect(self):
        """Test rectangular straight fin efficiency"""
        result = fe.Eta_Fin_Straight_Rect(self.th, self.L, self.h, self.k)
        assert result == pytest.approx(0.8063, rel=1e-3)

    def test_Eta_Fin_Straight_Triangular(self):
        """Test triangular straight fin efficiency"""
        result = fe.Eta_Fin_Straight_Triangular(self.th, self.L, self.h, self.k)
        assert result == pytest.approx(0.7557, rel=1e-3)

    def test_Eta_Fin_Straight_Parabolic(self):
        """Test concave parabolic straight fin efficiency"""
        result = fe.Eta_Fin_Straight_Parabolic(self.th, self.L, self.h, self.k)
        assert result == pytest.approx(0.6735 , rel=1e-3)

    def test_Eta_Fin_Straight_Parabolic2(self):
        """Test convex parabolic straight fin efficiency"""
        result = fe.Eta_Fin_Straight_Parabolic2(self.th, self.L, self.h, self.k)
        assert result == pytest.approx(0.7879, rel=1e-3)
