"""
Tests for functions module.
"""
import pytest
import numpy as np
from eeslib import functions as fn
from eeslib.talbot_inversion import talbot_inversion
import sympy


class TestUnitConversions:
    """Test unit conversion functions"""

    def test_temperature_conversion_celsius_to_fahrenheit(self):
        """Test Celsius to Fahrenheit conversion"""
        result = fn.converttemp('C', 'F', 0)
        assert result == 32.0  # 0°C = 32°F

    def test_temperature_conversion_fahrenheit_to_celsius(self):
        """Test Fahrenheit to Celsius conversion"""
        result = fn.converttemp('F', 'C', 32)
        assert result == 0.0  # 32°F = 0°C

    def test_temperature_conversion_celsius_to_kelvin(self):
        """Test Celsius to Kelvin conversion"""
        result = fn.converttemp('C', 'K', 0)
        assert result == 273.15  # 0°C = 273.15K

    def test_temperature_conversion_kelvin_to_celsius(self):
        """Test Kelvin to Celsius conversion"""
        result = fn.converttemp('K', 'C', 273.15)
        assert result == 0.0  # 273.15K = 0°C

    def test_temperature_conversion_fahrenheit_to_kelvin(self):
        """Test Fahrenheit to Kelvin conversion"""
        result = fn.converttemp('F', 'K', 32)
        assert result == 273.15  # 32°F = 273.15K

    def test_temperature_conversion_rankine_to_kelvin(self):
        """Test Rankine to Kelvin conversion"""
        result = fn.converttemp('R', 'K', 491.67)
        assert result == 273.15  # 491.67°R = 273.15K

    def test_unit_conversion_length(self):
        """Test length unit conversion"""
        result = fn.convert('m', 'ft')
        expected = 3.28084  # 1 meter ≈ 3.28 feet
        assert abs(result - expected) < 0.001

    def test_unit_conversion_mass(self):
        """Test mass unit conversion"""
        result = fn.convert('kg', 'lb')
        expected = 2.20462  # 1 kg ≈ 2.20 lb
        assert abs(result - expected) < 0.001

    def test_unit_conversion_energy(self):
        """Test energy unit conversion"""
        result = fn.convert('J', 'cal')
        expected = 1/4.184  # 4.184 J = 1 cal
        assert abs(result - expected) < 0.001

    def test_unit_conversion_power(self):
        """Test power unit conversion"""
        result = fn.convert('W', 'hp')
        expected = 1.0/745.7  # 745.7 W = 1 hp
        assert abs(result - expected) < 0.001

    def test_unit_conversion_pressure(self):
        """Test pressure unit conversion"""
        result = fn.convert('Pa', 'psi')
        expected = 1.0/6894.76  # 6894.76 Pa = 1 psi
        assert abs(result - expected) < 0.001

    def test_unit_conversion_velocity(self):
        """Test velocity unit conversion"""
        result = fn.convert('m/s', 'mph')
        expected = 1.0/0.44704  # 0.44704 m/s = 1 mph
        assert abs(result - expected) < 0.001

    def test_unit_conversion_volume(self):
        """Test volume unit conversion"""
        result = fn.convert('m^3', 'gal')
        expected = 1.0/0.00378541  # 0.00378541 m3 = 1 US gallon
        assert abs(result - expected) < 0.001

    def test_unit_conversion_time(self):
        """Test time unit conversion"""
        result = fn.convert('h', 's')
        expected = 3600.0  # 1 hour = 3600 seconds
        assert result == expected

    @pytest.mark.parametrize("from_unit,to_unit,input_val,expected", [
        ('C', 'F', 0, 32.0),
        ('F', 'C', 32, 0.0),
        ('C', 'K', 0, 273.15),
        ('K', 'C', 273.15, 0.0),
        ('F', 'K', 32, 273.15),
    ])
    def test_temperature_conversions_parametrized(self, from_unit, to_unit, input_val, expected):
        """Test temperature conversions with multiple values"""
        result = fn.converttemp(from_unit, to_unit, input_val)
        assert abs(result - expected) < 0.01

results = {
    'Temperature': 300.0,
    'Pressure': 101325.0,
    'Density': 1.2,
    'Velocity': sympy.symbols('v')**2 + 2*9.81*10,
    'diffeq': sympy.Derivative(sympy.symbols('y'), sympy.symbols('x')) + sympy.symbols('y'),
    'data': np.array([1, 2, 3, 4]),
    'table': np.array([[1, 2], [3, 4]]),
}
for i in range(30):
    results[f'var_{i}'] = i*10.0


class TestResultsTable:
    """Test results table printing functions"""

    def test_print_results_table(self, capsys):
        """
        Test results table with sympy expressions
        
        This needs work
        """
        try:

            fn.print_results_table(results, 
                                   file_save_path='./tests/tmp.pdf',
                                   file_save_note='TEMP TEST FILE - DELETE AFTER TESTING',
                                   file_save_code='run_tests.py',
                                   highlight_vars=['Temperature', 'Pressure', 'Density'],
                                   )

            captured = capsys.readouterr()
            assert 'data' in captured.out
            assert 'table' in captured.out
        except ImportError:
            pytest.skip("SymPy not available")


class TestCurrentFile:
    """Test current file function"""

    def test_current_file_exists(self):
        """Test that current_file returns a valid path"""
        file_path = fn.current_file()
        assert isinstance(file_path, str)
        assert len(file_path) > 0
        # Should be a Python file
        assert file_path.endswith('.py')


class TestTalbotInversion:
    """Test Talbot inversion function"""
    def Laplace1(self,s,T_infinity,gv_max,a,rho,c,tau):
        return T_infinity/(s*tau*(s+1/tau))+gv_max/(rho*c*(s+1/a)*(s+1/tau))+T_infinity/(s+1/tau)

    def test_talbot_inversion_exponential(self):
        """Test Talbot inversion with exponential function"""

        time=np.linspace(0.01,10,101)       #times to evaluate solution

        T2=talbot_inversion( self.Laplace1, time, 64, 300, 1e9, 2, 9000, 500, 1.5)

        assert type(T2) == np.ndarray
        assert pytest.approx(T2.max(), rel=1e-3) == 440.6179 

if __name__ == "__main__":
    T = TestResultsTable()
    T.test_print_results_table(None)  