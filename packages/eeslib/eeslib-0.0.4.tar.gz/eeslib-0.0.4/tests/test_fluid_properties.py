"""
Tests for fluid_properties module.
"""
import sys; sys.path.insert(0, 'C:\\repositories\\eeslib\\src')

import pytest
from eeslib import fluid_properties as fp


class TestFluidProperties:
    """Test fluid property calculations"""

    def test_density_water(self, water_fluid, sample_temperature, sample_pressure):
        """Test density calculation for water"""
        density = fp.density(water_fluid, T=sample_temperature, P=sample_pressure)
        assert isinstance(density, float)
        assert density > 0  # Density should be positive
        assert 990 < density < 1010  # Water density around 1000 kg/m³ at 27°C

    def test_enthalpy_water(self, water_fluid, sample_temperature, sample_pressure):
        """Test enthalpy calculation for water"""
        enthalpy = fp.enthalpy(water_fluid, T=sample_temperature, P=sample_pressure)
        assert isinstance(enthalpy, float)
        assert enthalpy > 0  # Enthalpy should be positive

    def test_entropy_water(self, water_fluid, sample_temperature, sample_pressure):
        """Test entropy calculation for water"""
        entropy = fp.entropy(water_fluid, T=sample_temperature, P=sample_pressure)
        assert isinstance(entropy, float)
        assert entropy > 0  # Entropy should be positive

    def test_temperature_calculation(self, water_fluid, sample_pressure):
        """Test temperature retrieval"""
        temp = fp.temperature(water_fluid, P=sample_pressure, D=997.0)  # Water density
        assert isinstance(temp, float)
        assert temp > 273  # Should be above freezing

    def test_pressure_calculation(self, water_fluid, sample_temperature):
        """Test pressure retrieval"""
        pressure = fp.pressure(water_fluid, T=sample_temperature, D=997.0)
        assert isinstance(pressure, float)
        assert pressure > 0  # Pressure should be positive

    def test_quality_calculation(self, water_fluid, sample_temperature):
        """Test vapor quality calculation"""
        enthalpy = fp.enthalpy(water_fluid, T=sample_temperature, X=0.5)
        assert isinstance(enthalpy, float)
        assert abs(enthalpy - 1331209.48) < 1  # enthalpy should be close to value at 0.5 quality

    def test_volume_calculation(self, water_fluid, sample_temperature, sample_pressure):
        """Test specific volume calculation"""
        volume = fp.volume(water_fluid, T=sample_temperature, P=sample_pressure)
        assert isinstance(volume, float)
        assert volume > 0  # Volume should be positive
        # Volume should be reciprocal of density
        density = fp.density(water_fluid, T=sample_temperature, P=sample_pressure)
        assert abs(volume - 1/density) < 1e-6

    def test_specific_heat(self, water_fluid, sample_temperature, sample_pressure):
        """Test specific heat calculation"""
        cp = fp.specheat(water_fluid, T=sample_temperature, P=sample_pressure)
        assert isinstance(cp, float)
        assert cp > 0  # Specific heat should be positive
        assert 4100 < cp < 4300  # Water Cp around 4186 J/kg-K

    def test_viscosity(self, water_fluid, sample_temperature, sample_pressure):
        """Test viscosity calculation"""
        viscosity = fp.viscosity(water_fluid, T=sample_temperature, P=sample_pressure)
        assert isinstance(viscosity, float)
        assert viscosity > 0  # Viscosity should be positive
        assert 0.0008 < viscosity < 0.0012  # Water viscosity around 0.001 Pa-s at 27°C

    def test_conductivity(self, water_fluid, sample_temperature, sample_pressure):
        """Test thermal conductivity calculation"""
        conductivity = fp.conductivity(water_fluid, T=sample_temperature, P=sample_pressure)
        assert isinstance(conductivity, float)
        assert conductivity > 0  # Conductivity should be positive
        assert 0.5 < conductivity < 0.7  # Water conductivity around 0.6 W/m-K at 27°C

    def test_saturation_temperature(self, water_fluid):
        """Test saturation temperature calculation"""
        p_sat = 101325.0  # 1 atm
        t_sat = fp.t_sat(water_fluid, p_sat)
        assert isinstance(t_sat, float)
        assert 373 < t_sat < 374  # Water boils around 373K at 1 atm
    
    def test_surface_tension(self, water_fluid, sample_pressure):
        """Test surface tension calculation"""
        s = fp.surface_tension(water_fluid, P=sample_pressure, X=0.5)
        assert isinstance(s, float)
        assert 0.05 < s < 0.06

    def test_triple_point(self, water_fluid):
        """Test triple point calculation"""
        t = fp.t_triple_point(water_fluid)
        p = fp.p_triple_point(water_fluid)
        assert isinstance(t, float)
        assert 273 < t < 274
        assert isinstance(p, float)
        assert 611 < p < 612
    
    def test_t_crit(self, water_fluid):
        """Test critical point calculation"""
        t = fp.t_crit(water_fluid)
        assert isinstance(t, float)
        assert 647 < t < 648
    
    def test_p_crit(self, water_fluid):
        """Test critical point calculation"""
        p = fp.p_crit(water_fluid)
        assert isinstance(p, float)
        assert 22063000 < p < 22065000
    
    def test_molarmass(self, water_fluid):
        """Test molar mass"""
        p = fp.molarmass(water_fluid)
        assert isinstance(p, float)
        assert 18 < p < 19

    def test_enthalpy_vaporization(self, water_fluid):
        """Enthalpy of vaporization"""
        dh = fp.enthalpy_vaporization(water_fluid, P=101325.)
        assert isinstance(dh, float)
        assert 2256000 < dh < 2257000

    def test_fluids_list(self):
        """Test that fluids list is returned"""
        fluids = fp.get_fluids_list()
        assert isinstance(fluids, list)
        assert len(fluids) > 0  # Should have some fluids
        assert "Water" in fluids  # Water should be available
