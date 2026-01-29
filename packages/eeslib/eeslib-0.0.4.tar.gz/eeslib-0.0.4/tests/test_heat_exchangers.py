"""
Tests for heat_exchangers module.
"""
import pytest
import numpy as np
from eeslib import heat_exchangers as hx


class TestHeatExchangers:
    """Test heat exchanger calculations"""

    def test_lmtd_cf_counterflow(self):
        """Test LMTD correction factor for counterflow"""
        TypeHX = "counterflow"
        P = 0.8  # P = (T2_out - T2_in)/(T1_in - T2_in)
        R = 0.5  # R = (T1_in - T1_out)/(T2_out - T2_in)

        cf = hx.lmtd_cf(TypeHX, P, R)

        assert isinstance(cf, float)
        # For counterflow, CF should be 1.0
        assert abs(cf - 1.0) < 0.001

    def test_lmtd_cf_parallel_flow(self):
        """Test LMTD correction factor for parallel flow"""
        TypeHX = "parallelflow"
        P = 0.2
        R = 0.8

        cf = hx.lmtd_cf(TypeHX, P, R)

        assert isinstance(cf, float)
        assert 0 < cf < 1  # Correction factor should be between 0 and 1

    def test_lmtd_cf_crossflow_unmixed(self):
        """Test LMTD correction factor for crossflow unmixed"""
        TypeHX = "crossflow_both_unmixed"
        P = 0.7
        R = 0.6

        cf = hx.lmtd_cf(TypeHX, P, R)

        assert isinstance(cf, float)
        assert 0 < cf < 1

    def test_lmtd_cf_invalid_p(self, capsys):
        """Test LMTD correction factor with invalid P value"""
        TypeHX = "counterflow"
        P = 1.5  # Invalid (should be <= 1)
        R = 0.5

        cf = hx.lmtd_cf(TypeHX, P, R)

        # Should still return a value but with warning
        assert isinstance(cf, float)

        # Check warning was printed
        captured = capsys.readouterr()
        assert "Warning" in captured.out

    def test_lmtd_cf_invalid_r(self, capsys):
        """Test LMTD correction factor with invalid R value"""
        TypeHX = "counterflow"
        P = 0.8
        R = -0.5  # Invalid (should be >= 0)

        cf = hx.lmtd_cf(TypeHX, P, R)

        # Should still return a value but with warning
        assert isinstance(cf, float)

        # Check warning was printed
        captured = capsys.readouterr()
        assert "Warning" in captured.out

    def test_findntuxflow(self):
        """Test NTU calculation for crossflow"""
        epsilon = 0.8  # Effectiveness
        C_r = 0.5     # Capacity ratio

        NTU = hx.findntuxflow(epsilon, C_r)

        assert isinstance(NTU, float)
        assert NTU > 0

    def test_findntuxflow2(self):
        """Test alternative NTU calculation"""
        epsilon = 0.7
        C_r = 0.4

        NTU = hx.findntuxflow2(epsilon, C_r)

        assert isinstance(NTU, float)
        assert NTU > 0
    @pytest.mark.parametrize("config,rettype,C_1,C_2,P", [
        ('parallelflow'          , 'NTU',         1., 2., 0.3),  
        ('parallelflow'          , 'epsilon',     1., 2., 2.5),  
        ('parallelflow'          , 'epsilon',     1., 1., 2.5),  
        ('counterflow'           , 'NTU',         1., 2., 0.3),  
        ('counterflow'           , 'epsilon',     1., 2., 2.5),  
        ('counterflow'           , 'epsilon',     1., 1., 2.5),  
        ('crossflow_both_unmixed', 'NTU',         1., 2., 0.3),  
        ('crossflow_both_unmixed', 'epsilon',     1., 2., 2.5),  
        ('crossflow_both_unmixed', 'epsilon',     1., 1., 2.5),  
        ('crossflow_both_mixed'  , 'NTU',         1., 2., 0.3),  
        ('crossflow_both_mixed'  , 'epsilon',     1., 2., 2.5),  
        ('crossflow_both_mixed'  , 'epsilon',     1., 1., 2.5),  
        ('crossflow_one_unmixed' , 'NTU',         1., 2., 0.3),  
        ('crossflow_one_unmixed' , 'epsilon',     1., 2., 2.5),  
        ('crossflow_one_unmixed' , 'epsilon',     1., 1., 2.5),  
        ('shell&tube_3'          , 'NTU',         1., 2., 0.3),   
        ('shell&tube_3'          , 'epsilon',     1., 2., 2.5),   
        ('shell&tube_3'          , 'epsilon',     1., 1., 2.5),   
        ('regenerator'           , 'NTU',         1., 2., 0.3),  
        ('regenerator'           , 'epsilon',     1., 2., 2.5),  
        ('regenerator'           , 'epsilon',     1., 1., 2.5),  
    ])
    def test_hx_function(self, config, rettype, C_1, C_2, P):
        """Test main heat exchanger function"""
        result = hx.hx(config, P, C_1, C_2, rettype)

        assert isinstance(result, (int, float))
        if config == 'NTU':
            assert result >= 0
        else:
            assert 0 <= result <= 1  # Effectiveness should be between 0 and 1

    def test_hx_cof_crfhdr(self):
        """Test heat exchanger coefficient calculation"""
        NTU_co = 2.0
        NTU_cr = 1.5
        CR = 0.8

        result = hx.hx_cof_crfhdr(NTU_co, NTU_cr, CR)

        assert isinstance(result, (int, float))
        assert result > 0