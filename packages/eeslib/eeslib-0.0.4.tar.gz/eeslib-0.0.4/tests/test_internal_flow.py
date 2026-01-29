"""
Tests for internal_flow module.
"""
import pytest
import numpy as np
from eeslib import internal_flow as iflow

def approx(val, rel=1.e-3):
    return pytest.approx(val, rel=rel)

class TestInternalFlow:
    """Test internal flow heat transfer calculations"""

    def test_pipeflow_laminar(self):
        """Test laminar pipe flow calculations"""
        Re = 1000  # Laminar flow
        Pr = 0.7   # Prandtl number (water-like)
        LoverD = 50.0  # Length to diameter ratio

        Nusselt_T, Nusselt_H, f = iflow.pipeflow_laminar(Re, Pr, LoverD)

        assert isinstance(Nusselt_T, (int, float))
        assert isinstance(Nusselt_H, (int, float))
        assert isinstance(f, (int, float))

        assert abs(Nusselt_H - 5.315) < .01 
        assert abs(Nusselt_T - 4.651) < .01 

        # Friction factor for laminar flow
        assert abs(f - 0.08687) < 0.001

    @pytest.mark.parametrize("Pr, relRough, expected_f, expected_Nusselt", [
        (0.7, 1e-6, 0.01916, 190.2),    # Li, Seem, & Li
        (0.7, 0.001, 0.0236, 238.1),    # Offor & Alabi
        (0.4, 0.001, 0.0236, 158.9),    # Notter and Sleicher
        (0.01, 0.001, 0.0236, 9.187),   # low Pr number
    ])
    def test_pipeflow_turbulent(self, Pr, relRough, expected_f, expected_Nusselt):
        """Test turbulent pipe flow calculations"""
        LoverD = 50.0
        Re = 1e5  # Turbulent flow
        
        Nusselt, f = iflow.pipeflow_turbulent(Re, Pr, LoverD, relRough)
        assert isinstance(Nusselt, (int, float))
        assert isinstance(f, (int, float))
        assert f == approx(expected_f, rel=1e-3)
        assert Nusselt == approx(expected_Nusselt, rel=1e-3)



    @pytest.mark.parametrize("Re, min_nusselt", [
        (1000, 3),  # laminar
        (2500, 3),  # transitional
        (5000, 5),  # turbulent
    ])
    def test_pipeflow_nd(self, Re, min_nusselt):
        """Test pipeflow_nd for laminar, transitional, and turbulent flow"""
        Pr = 5.0
        LoverD = 20.0
        relRough = 0.001

        Nusselt_T, Nusselt_H, f = iflow.pipeflow_nd(Re, Pr, LoverD, relRough)

        assert isinstance(Nusselt_T, (int, float))
        assert isinstance(Nusselt_H, (int, float))
        assert isinstance(f, (int, float))

        assert Nusselt_T > min_nusselt
        assert Nusselt_H > min_nusselt

    def test_pipeflow_nd_invalid_reynolds(self, capsys):
        """Test pipeflow_nd with invalid Reynolds number"""
        Re = -100  # Invalid
        Pr = 5.0
        LoverD = 20.0
        relRough = 0.001

        result = iflow.pipeflow_nd(Re, Pr, LoverD, relRough)

        # Should still return values but with warning
        assert isinstance(result, tuple)
        assert len(result) == 3

        # Check that warning was printed
        captured = capsys.readouterr()
        assert "Warning" in captured.out or "Re in PipeFlow_ND must be > 0.001" in captured.out

    def test_pipeflow_nd_invalid_roughness(self, capsys):
        """Test pipeflow_nd with invalid roughness"""
        Re = 5000
        Pr = 5.0
        LoverD = 20.0
        relRough = 0.1  # Too high

        result = iflow.pipeflow_nd(Re, Pr, LoverD, relRough)

        # Should still return values but with warning
        assert isinstance(result, tuple)
        assert len(result) == 3

        # Check that warning was printed
        captured = capsys.readouterr()
        assert "Warning" in captured.out or "relRough" in captured.out

    def test_pipeflow_nd_local(self):
        """Test pipeflow_nd_local for local values"""
        Re=1000
        Pr=2
        xoverD=1.1
        relRough=0

        Nusselt_T, Nusselt_H, f = iflow.pipeflow_nd_local(Re, Pr, xoverD, relRough)

        assert isinstance(Nusselt_T, (int, float))
        assert isinstance(Nusselt_H, (int, float))
        assert isinstance(f, (int, float))

        assert Nusselt_T == approx(15.02)
        assert Nusselt_H == approx(16.08)
        assert f == approx(.2156)

    def test_ductflow_laminar(self):
        """Test laminar duct flow calculations"""
        Re = 1000  # Laminar flow
        Pr = 0.7   # Prandtl number
        LoverD = 50.0  # Length to hydraulic diameter ratio
        Aspect = 0.5   # Aspect ratio

        Nusselt_T, Nusselt_H, f = iflow.ductflow_laminar(Re, Pr, LoverD, Aspect)

        assert isinstance(Nusselt_T, (int, float))
        assert isinstance(Nusselt_H, (int, float))
        assert isinstance(f, (int, float))

        assert Nusselt_T == approx(4.479)
        assert Nusselt_H == approx(6.197)
        assert f == approx(0.08524)

    def test_ductflow_nd(self):
        """Test ductflow_nd for duct flow"""
        Re=4500
        Pr=2
        Aspect=0.25
        LoverD=20
        relRough=0

        Nusselt_T, Nusselt_H, f = iflow.ductflow_nd(Re, Pr, LoverD, Aspect, relRough)

        assert isinstance(Nusselt_T, (int, float))
        assert isinstance(Nusselt_H, (int, float))
        assert isinstance(f, (int, float))

        assert Nusselt_T == approx(24.96)
        assert Nusselt_H == approx(24.96)
        assert f == approx(0.0433)

    def test_ductflow_nd_local(self):
        """Test ductflow_nd_local for local duct flow"""
        Re=4500
        Pr=2
        Aspect=0.25
        xoverD=20
        relRough=0

        Nusselt_T, Nusselt_H, f = iflow.ductflow_nd_local(Re, Pr, xoverD, Aspect, relRough)

        assert isinstance(Nusselt_T, (int, float))
        assert isinstance(Nusselt_H, (int, float))
        assert isinstance(f, (int, float))

        assert Nusselt_T == approx(23.05)
        assert Nusselt_H == approx(23.05)
        assert f == approx(0.03999)