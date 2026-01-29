"""
Tests for radiation module.
"""
import pytest
import numpy as np
from eeslib import radiation as rad


class TestBlackbodyFunctions:
    """Test blackbody radiation functions"""

    def test_Blackbody(self):
        """Test Blackbody function returns fraction between 0 and 1"""
        result = rad.Blackbody(1000, 4, 5)  # T=1000K, lambda 4-5 microns
        assert isinstance(result, float)
        assert result == pytest.approx(0.1529, rel=0.005)  # Should be positive

    def test_Eb(self):
        """Test spectral emissive power function"""
        result = rad.Eb(1000, 5)  # T=1000K, lambda=5 microns
        assert isinstance(result, float)
        assert result == pytest.approx(7140, rel=0.005)  # Should be positive


class Test2DViewFactors:
    """Test 2D view factor functions"""

    def test_f2d_01(self):
        """Test view factor between two infinitely long plates"""
        """Doc example: hs101.htm -- h=1 m, w=2 m, Solution F=0.618"""
        result = rad.f2d_01(h=1, w=2)  # doc: hs101.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.618, rel=0.005)

    def test_f2d_02(self):
        """Test view factor between angled plates with common edge"""
        """Doc example: hs102.htm -- alpha=45deg, w=1 => F=0.6173"""
        result = rad.f2d_02(alpha=np.pi/4, w=1)  # doc: hs102.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.6173, rel=0.005)

    def test_f2d_03(self):
        """Test view factor from plate to parallel cylinder"""
        """Doc example: hs103.htm -- r=0.2, a=0.5, b_1=1.5, b_2=0.5 => F=0.07379"""
        result = rad.f2d_03(r=0.2, a=0.5, b_1=1.5, b_2=0.5)  # doc: hs103.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.07379, rel=0.005)

    def test_f2d_04(self):
        """Test view factor between parallel cylinders of same diameter"""
        """Doc example: hs104.htm -- r=0.2, s=0.5 => F=0.07198"""
        result = rad.f2d_04(r=0.2, s=0.5)  # doc: hs104.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.07198, rel=0.005)

    def test_f2d_05(self):
        """Test view factor between concentric cylinders"""
        """Doc example: hs105.htm -- r_1=0.1, r_2=0.2 => F=0.5"""
        result = rad.f2d_05(r_1=0.1, r_2=0.2)  # doc: hs105.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.5, rel=0.005)

    def test_f2d_06(self):
        """Test view factor from plate to parallel cylinder (simplified)"""
        """Doc example: hs106.htm -- a=1, b=1 => F=0.25"""
        result = rad.f2d_06(a=1, b=1)  # doc: hs106.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.25, rel=0.005)

    def test_f2d_07(self):
        """Test view factor between infinite plane and row of cylinders"""
        """Doc example: hs107.htm -- d=0.1, s=0.2 => F=0.6576"""
        result = rad.f2d_07(d=0.1, s=0.2)  # doc: hs107.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.6576, rel=0.005)

    def test_f2d_08(self):
        """Test view factor for semicircle with coaxial cylinder"""
        """Doc example: hs108.htm -- r1=0.1, r2=0.2 => F=0.282"""
        result = rad.f2d_08(r1=0.1, r2=0.2)  # doc: hs108.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.282, rel=0.005)

    def test_f2d_09(self):
        """Test view factor between parallel cylinders of different radii"""
        """Doc example: hs109.htm -- r_1=0.1, r_2=0.2, s=1 => F=0.04922"""
        result = rad.f2d_09(r_1=0.1, r_2=0.2, s=1)  # doc: hs109.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.04922, rel=0.005)

    def test_f2d_10(self):
        """Test view factor between parallel plates of different widths"""
        """Doc example: hs110.htm -- a=1, b=1, c=2 => F=0.6847"""
        result = rad.f2d_10(a=1, b=1, c=2)  # doc: hs110.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.6847, rel=0.005)

    def test_f2d_11(self):
        """Test view factor in enclosure formed by three surfaces"""
        """Doc example: hs111.htm -- A1=1, A2=1, A3=1 => F=0.5"""
        result = rad.f2d_11(A1=1, A2=1, A3=1)  # doc: hs111.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.5, rel=0.005)

    def test_f2d_12(self):
        """Test view factor between perpendicular plates"""
        """Doc example: hs112.htm -- w=5, h=3 => F=0.2169"""
        result = rad.f2d_12(w=5, h=3)  # doc: hs112.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.2169, rel=0.005)

    def test_f2d_13(self):
        """Test view factor between plates at angle alpha"""
        """Doc example: hs113.htm -- a=1, b=0.5, alpha=30deg => F=0.8803"""
        result = rad.f2d_13(b=0.5, a=1, alpha=np.pi/6)  # doc: hs113.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.8803, rel=0.005)

    def test_f2d_14(self):
        """Test view factor between parallel plates"""
        """Doc example: hs114.htm -- W1=1, W2=2, H=1.2, a=0.5 => F=0.4261"""
        result = rad.f2d_14(W1=1, W2=2, H=1.2, a=0.5)  # doc: hs114.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.4261, rel=0.005)

    def test_f2d_15(self):
        """Test view factor between plates without common edge"""
        """Doc example: hs115.htm -- x1=1, x2=2, y1=1, y2=3, alpha=45deg => F=0.4915"""
        result = rad.f2d_15(x1=1, x2=2, y1=1, y2=3, alpha=np.pi/4)  # doc: hs115.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.4915, rel=0.005)

    def test_f2d_16(self):
        """Test view factor from surface to tube array (in-line)"""
        """Doc example: hs116.htm -- d=1, s=4, n=2 => F=0.592"""
        result = rad.f2d_16(d=1, s=4, n=2)  # doc: hs116.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.592, rel=0.005)

    def test_f2d_17(self):
        """Test view factor from surface to second row of triangular array"""
        """Doc example: hs117.htm -- d=1, p=2 => F=0.1943"""
        result = rad.f2d_17(d=1, p=2)  # doc: hs117.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.1943, rel=0.005)


class Test3DViewFactors:
    """Test 3D view factor functions"""

    def test_f3d_01(self):
        """Test view factor between identical opposite rectangles"""
        """Doc example: hs201.htm -- a=1, b=1.5, c=0.5 => F=0.4756"""
        result = rad.f3d_01(a=1, b=1.5, c=0.5)  # doc: hs201.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.4756, rel=0.005)

    def test_f3d_02(self):
        """Test view factor between perpendicular rectangles with common edge"""
        """Doc example: hs202.htm -- a=1, b=1, c=0.5 => F=0.1493"""
        result = rad.f3d_02(a=1, b=1, c=0.5)  # doc: hs202.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.1493, rel=0.005)

    def test_f3d_03(self):
        """Test view factor between coaxial parallel disks"""
        """Doc example: hs203.htm -- r_1=0.1, r_2=0.2, a=0.5 => F=0.1339"""
        result = rad.f3d_03(r_1=0.1, r_2=0.2, h=0.5)  # doc: hs203.htm (a->h)
        assert isinstance(result, float)
        assert result == pytest.approx(0.1339, rel=0.005)

    def test_f3d_04(self):
        """Test view factor between concentric cylinders of finite length"""
        """Doc example: hs204.htm -- r_1=0.1, r_2=0.2, w=0.5 => F=0.8589"""
        result = rad.f3d_04(r_1=0.1, r_2=0.2, w=0.5)  # doc: hs204.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.8589, rel=0.005)

    def test_f3d_05(self):
        """Test view factor from outer concentric cylinder to itself"""
        """Doc example: hs205.htm -- r_1=0.1, r_2=0.2, w=0.5 => F=0.357"""
        result = rad.f3d_05(r_1=0.1, r_2=0.2, L=0.5)  # doc: hs205.htm (w->L)
        assert isinstance(result, float)
        assert result == pytest.approx(0.357, rel=0.005)

    def test_f3d_06(self):
        """Test view factor between cylinder outer surface and annular disk"""
        """Doc example: hs206.htm -- r_1=0.1, r_2=0.2, l=0.5 => F=0.07056"""
        result = rad.f3d_06(r1=0.1, r2=0.2, l=0.5)  # doc: hs206.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.07056, rel=0.005)

    def test_f3d_07(self):
        """Test view factor between sphere and perpendicular rectangle"""
        """Doc example: hs207.htm -- l1=0.5, l2=0.5, d=0.5, r=0.1 => F=0.04167"""
        result = rad.f3d_07(l1=0.5, l2=0.5, d=0.5, r=0.1)  # doc: hs207.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.04167, rel=0.005)

    def test_f3d_08(self):
        """Test view factor between sphere and coaxial cylinder interior"""
        """Doc example: hs208.htm -- r1=0.25, r2=0.5, a1=0.5, a2=1 => F=0.09366"""
        result = rad.f3d_08(r1=0.25, r2=0.5, a1=0.5, a2=1)  # doc: hs208.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.09366, rel=0.005)

    def test_f3d_09(self):
        """Test view factor between enclosed sphere and cylinder interior"""
        """Doc example: hs209.htm -- r1=0.25, r2=0.5, a=0.5 => F=0.7071"""
        result = rad.f3d_09(r1=0.25, r2=0.5, a=0.5)  # doc: hs209.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.7071, rel=0.005)

    def test_f3d_10(self):
        """Test view factor between two perpendicular rectangles"""
        """Doc example: hs210.htm -- a=0.5, b1=0.2, b2=0.3, c=0.5 => F=0.07235"""
        result = rad.f3d_10(a=0.5, b_1=0.2, b_2=0.3, c=0.5)  # doc: hs210.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.07235, rel=0.005)

    def test_f3d_11(self):
        """Test view factor between two perpendicular rectangles (complex)"""
        """Doc example: hs211.htm -- a_1=0.1, a_2=0.5, b_1=0.2, b_2=0.3, c=0.5 => F=0.07182"""
        result = rad.f3d_11(a_1=0.1, a_2=0.5, b_1=0.2, b_2=0.3, c=0.5)  # doc: hs211.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.07182, rel=0.005)

    def test_f3d_12(self):
        """Test view factor between two perpendicular rectangles (different)"""
        """Doc example: hs212.htm -- a=0.1, b=0.5, c1=0.2, c2=0.3 => F=0.0605"""
        result = rad.f3d_12(a=0.1, b=0.5, c_1=0.2, c_2=0.3)  # doc: hs212.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.0605, rel=0.005)

    def test_f3d_13(self):
        """Test view factor between non-adjacent perpendicular rectangles"""
        """Doc example: hs213.htm -- a1=0.1,a2=0.2,b1=0.5,b2=0.5,c1=0.5,c2=0.05,c3=0.5 => F=0.01626"""
        result = rad.f3d_13(a1=0.1, a2=0.2, b1=0.5, b2=0.5, c1=0.5, c2=0.05, c3=0.5)  # doc: hs213.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.01626, rel=0.005)

    def test_f3d_14(self):
        """Test view factor between arbitrarily positioned parallel rectangles"""
        """Doc example: hs214.htm -- x1=0.1,x2=0.2,y1=0.1,y2=0.2,a1=0.1,a2=0.2,b1=0.1,b2=0.2,z=0.05 => F=0.4153"""
        result = rad.f3d_14([0.1, 0.2], [0.1, 0.2], [0.1, 0.2], [0.1, 0.2], 0.05)  # doc: hs214.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.4153, rel=0.005)

    def test_f3d_15(self):
        """Test view factor between finite cylinder and rectangle"""
        """Doc example: hs215.htm -- l=0.5, n=0.2, z=0.5, d=0.25 => F=0.2435"""
        result = rad.f3d_15(l=0.5, n=0.2, z=0.5, d=0.25)  # doc: hs215.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.2435, rel=0.005)

    def test_f3d_16(self):
        """Test view factor between sphere and disk"""
        """Doc example: hs216.htm -- r=1, h=0.5 => F=0.2764 (scaled input used here for variety)"""
        result = rad.f3d_16(r=1, h=0.5)  # doc: hs216.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.2764, rel=0.005)

    def test_f3d_17(self):
        """Test view factor between cylinder base and cylinder interior"""
        """Doc example: hs217.htm -- r=1, h=0.5 => F=0.3904"""
        result = rad.f3d_17(r=1, h=0.5)  # doc: hs217.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.3904, rel=0.005)

    def test_f3d_18(self):
        """Test view factor of cylinder interior to itself"""
        """Doc example: hs218.htm -- r=1, h=0.5 => F=0.2192"""
        result = rad.f3d_18(r=1, h=0.5)  # doc: hs218.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.2192, rel=0.005)

    def test_f3d_19(self):
        """Test view factor between annular ring and cylinder interior"""
        """Doc example: hs219.htm -- r_1=0.1, r_2=0.2, h=0.5 => F=0.8806"""
        result = rad.f3d_19(r_1=0.1, r_2=0.2, h=0.5)  # doc: hs219.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.8806, rel=0.005)

    def test_f3d_20(self):
        """Test view factor between parallel square planes of different sizes"""
        """Doc example: hs220.htm -- a=0.1, b=0.2, c=0.2 => F=0.2285"""
        result = rad.f3d_20(a=0.1, b=0.2, c=0.2)  # doc: hs220.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.2285, rel=0.005)

    def test_f3d_21(self):
        """Test view factor between rectangle and coaxial parallel disk (Monte Carlo)"""
        """Doc example: hs221.htm -- a=0.1, b=0.2, c=0.2, r=0.1, N=0 => F≈0.184 (Monte Carlo)"""
        result = rad.f3d_21(a=0.1, b=0.2, c=0.2, r=0.1, N=100000)  # doc: hs221.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.184, rel=0.1)  # Monte Carlo, looser tolerance

    def test_f3d_22(self):
        """Test view factor between two spheres"""
        """Doc example: hs222.htm -- r_1=0.1, r_2=0.2, s=0.5 => F=0.04174"""
        result = rad.f3d_22(r_1=0.1, r_2=0.2, s=0.5)  # doc: hs222.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.04174, rel=0.005)

    def test_f3d_23(self):
        """Test view factor between finite cylinder and sphere"""
        """Doc example: hs223.htm -- l=0.1, d=0.05, y=0.5, r1=0.1, r2=0.2 => F=0.1222"""
        result = rad.f3d_23(l=0.1, d=0.05, y=0.5, r1=0.1, r2=0.2)  # doc: hs223.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.1222, rel=0.005)

    def test_f3d_24(self):
        """Test view factor between sphere and rectangular enclosure"""
        """Doc example: hs224.htm -- x=0.1, y=0.2, z=0.1, r1=0.05, r2=0.1 => F=0.4928"""
        result = rad.f3d_24(x=0.1, y=0.2, z=0.1, r1=0.05, r2=0.1)  # doc: hs224.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.4928, rel=0.005)

    def test_f3d_25(self):
        """Test view factor between sphere and cylindrical enclosure"""
        """Doc example: hs225.htm -- x=0.1, y=0.2, l=0.9, r1=0.05, r2=0.1 => F=0.8264"""
        result = rad.f3d_25(x=0.1, y=0.2, l=0.9, r1=0.05, r2=0.1)  # doc: hs225.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.8264, rel=0.005)

    def test_f3d_26(self):
        """Test view factor between sphere and conical enclosure"""
        """Doc example: hs226.htm -- x=0.02, l=0.1, z=0.1, r1=0.05, r2=0.1 => F=0.8988"""
        result = rad.f3d_26(x=0.02, l=0.1, z=0.1, r1=0.05, r2=0.1)  # doc: hs226.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.8988, rel=0.005)

    def test_f3d_27(self):
        """Test view factor for hemispherical enclosure"""
        """Doc example: hs227.htm -- tau=90 [deg] => F=0.5"""
        # Doc used degrees; preserve test argument name but pass documented example (90)
        result = rad.f3d_27(tau=90*np.pi/180)  # doc: hs227.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.5, rel=0.005)

    def test_f3d_28(self):
        """Test view factor for tilted rectangular enclosure"""
        """Doc example: hs228.htm -- a=1, b=1, c=1, theta=45 [deg] => F=0.4833"""
        # doc uses degrees for theta; pass documented numeric value
        result = rad.f3d_28(a_2=1, b_2=1, H=1, theta=45*np.pi/180)  # doc: hs228.htm (mapped)
        assert isinstance(result, float)
        assert result == pytest.approx(0.4833, rel=0.005)

    def test_f3d_29(self):
        """Test view factor for complex enclosure geometry"""
        """Doc example: hs229.htm -- a1=0.1, a2=0.5, b1=0.2, b2=0.3, c=0.5, theta=45 => F=0.2276
        Mapped to existing keyword names where possible."""
        result = rad.f3d_29(a_1=0.1, a_2=0.5, b_1=0.2, b_2=0.3, H=0.5, phi=45*np.pi/180)  # doc: hs229.htm (mapped)
        assert isinstance(result, float)
        assert result == pytest.approx(0.2276, rel=0.005)

    def test_f3d_30(self):
        """Test view factor for rectangles with arbitrary angle between planes"""
        """Doc example: hs230.htm -- x1=0, x2=1, y1=0, y2=1, eta1=0, eta2=1, z1=1, z2=2, theta=45deg => F=0.0728"""
        result = rad.f3d_30(x_1=0, x_2=1, y_1=0, y_2=1, eta_1=0, eta_2=1, z_1=1, z_2=2, theta=np.pi/4)  # doc: hs230.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.0728, rel=0.005)

    def test_f3d_31(self):
        """Test view factor between rectangle and cylinder (Monte Carlo)"""
        """Doc example: hs231.htm -- w=0.50, h=1.00, d=0.10, k=1.00, s=0.10, N=100000 => F≈0.221"""
        result = rad.f3d_31(w=0.50, h=1.00, d=0.10, k=1.00, s=0.10, N=100000)  # doc: hs231.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.221, rel=0.02) # Monte Carlo, looser tolerance

    def test_f3d_32(self):
        """Test view factor between rectangle and cylinder with front/back spacing"""
        """Doc example: hs232.htm -- w=0.50, h=1.00, d=0.10, k=1.00, s_f=0.05, s_b=0.05, N=100000 => F≈0.52"""
        result = rad.f3d_32(w=0.50, h=1.00, d=0.10, k=1.00, s_f=0.05, s_b=0.05, N=100000)  # doc: hs232.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.52, rel=0.04) # Monte Carlo, looser tolerance

    def test_f3d_33(self):
        """Test view factor from rectangle to perpendicular disk"""
        result = rad.f3d_33(R=1, B=1, L=1)  # R>0, B>0, L>0, ratios in valid range
        assert isinstance(result, float)
        assert result == pytest.approx(0.3116, rel=0.01) 

    def test_f3d_34(self):
        """Test view factor between aligned rectangular enclosures"""
        result = rad.f3d_34(x_1=1, x_2=1, s=0.2, b=1, d=2)
        assert isinstance(result, float)
        assert result == pytest.approx(0.1294, rel=0.01) 

    def test_f3d_35(self):
        """Parallel cylinders of finite and equal lengths"""
        r_1=0.1
        r_2=0.2
        L=0.2
        s=0.1
        result = rad.f3d_35(r_1,r_2,L,s)
        assert isinstance(result, float)
        assert result == pytest.approx(0.1028, rel=0.005)

    def test_f3d_36(self):
        """Perpendicular right triangles with coincident base"""
        D=0.1
        L=0.05
        W=0.2
        result = rad.f3d_36(W,L,D)
        assert isinstance(result, float)
        assert result == pytest.approx(0.3177, rel=0.005)

    def test_f3d_37(self):
        """Right triangle to perpendicular rectangle with coincident base"""
        D=0.1
        L=0.05
        W=0.2
        result = rad.f3d_37(W,L,D)
        assert isinstance(result, float)
        assert result == pytest.approx(0.3531, rel=0.005)

    def test_f3d_38(self):
        """Right triangle to perpendicular right triangle sharing the same base but oriented oppositely"""
        D=0.1
        L=0.05
        W=0.2
        result = rad.f3d_38(W,L,D)
        assert isinstance(result, float)
        assert result == pytest.approx(0.3027, rel=0.005)

    def test_f3d_39(self):
        """Right triangle to perpendicular rectangle sharing a common base.&nbsp; Base of right triangle is half that of rectangle"""
        D=0.1
        L=0.05
        W=0.2
        result = rad.f3d_39(W,L,D)
        assert isinstance(result, float)
        assert result == pytest.approx(0.4689, rel=0.005)

    def test_f3d_40(self):
        """Isosceles triangle to perpendicular rectangle sharing a common base"""
        D=0.1
        L=0.05
        W=0.2
        result = rad.f3d_40(W,L,D)
        assert isinstance(result, float)
        assert result == pytest.approx(0.4689, rel=0.005)

    def test_f3d_41(self):
        """Right triangles that are perpendicular and share a common base.&nbsp; Triangle 1 has half the base length as triangle 2"""
        D=0.1
        L=0.05
        W=0.2
        result = rad.f3d_41(W,L,D)
        assert isinstance(result, float)
        assert result == pytest.approx(0.4310, rel=0.005)

    def test_f3d_42(self):
        """Right triangles that are perpendicular and share a common base.&nbsp; Triangle 1 has half the base length as triangle 2"""
        D=0.1
        L=0.05
        W=0.2
        result = rad.f3d_42(W,L,D)
        assert isinstance(result, float)
        assert result == pytest.approx(0.4312, rel=0.005)

    def test_f3d_43(self):
        """Right triangles that are perpendicular with bases that share a common line and touch"""
        D=0.1
        L=0.1
        W=0.2
        result = rad.f3d_43(W,L,D)
        assert isinstance(result, float)
        assert result == pytest.approx(0.04728, rel=0.005)

    def test_f3d_44(self):
        """Parallel, directly opposed right triangles"""
        c=0.1
        b=0.1
        theta = np.pi/4
        result = rad.f3d_44(c,b,theta)
        assert isinstance(result, float)
        assert result == pytest.approx(0.1186, rel=0.005)

    def test_f3d_45(self):
        """Parallel, directly opposed rectangles with 30 triangular extensions"""
        a=0.1
        b=0.1
        c=0.2
        result = rad.f3d_45(a,b,c)
        assert isinstance(result, float)
        assert result == pytest.approx(0.08397, rel=0.005)

    def test_f3d_46(self):
        """Parallel, directly opposed rectangles with 45 triangular extensions"""
        a=0.1
        b=0.1
        c=0.2
        result = rad.f3d_46(a,b,c)
        assert isinstance(result, float)
        assert result == pytest.approx(0.09684, rel=0.005)

    def test_f3d_47(self):
        """Rectangular floor to a rectangular endwall with a 30 triangular extension"""
        a=0.1
        b=0.1
        c=0.2
        result = rad.f3d_47(a,b,c)
        assert isinstance(result, float)
        assert result == pytest.approx(0.1784, rel=0.005)

    def test_f3d_48(self):
        """Rectangular floor to a rectangular endwall with a 45 triangular extension"""
        a=0.1
        b=0.1
        c=0.2
        result = rad.f3d_48(a,b,c)
        assert isinstance(result, float)
        assert result == pytest.approx(0.1857, rel=0.005)

    def test_f3d_49(self):
        """Adjacent walls of a hexagonal prism"""
        l=0.1
        h=0.5
        result = rad.f3d_49(l,h)
        assert isinstance(result, float)
        assert result == pytest.approx(0.1229, rel=0.005)

    def test_f3d_50(self):
        """Two walls of a hexagonal prism once removed from each other"""
        l=0.1
        h=0.5
        result = rad.f3d_50(l,h)
        assert isinstance(result, float)
        assert result == pytest.approx(0.1888, rel=0.005)

    def test_f3d_51(self):
        """Two opposite walls of a hexagonal prism"""
        l=0.1
        h=0.5
        result = rad.f3d_51(l,h)
        assert isinstance(result, float)
        assert result == pytest.approx(0.2089, rel=0.005)

    def test_f3d_52(self):
        """Parallel regular triangles"""
        h=1
        l=0.5
        result = rad.f3d_52(l,h)
        assert isinstance(result, float)
        assert result == pytest.approx(0.032, rel=0.005)

    def test_f3d_53(self):
        """Parallel regular pentagons"""
        h=0.25
        l=0.5
        result = rad.f3d_53(l,h)
        assert isinstance(result, float)
        assert result == pytest.approx(0.4974, rel=0.005)

    def test_f3d_54(self):
        """Parallel regular hexagons"""
        h=0.25
        l=0.5
        result = rad.f3d_54(l,h)
        assert isinstance(result, float)
        assert result == pytest.approx(0.5671, rel=0.005)

    def test_f3d_55(self):
        """Parallel regular octagons"""
        h=0.25
        l=0.5
        result = rad.f3d_55(l,h)
        assert isinstance(result, float)
        assert result == pytest.approx(0.6634, rel=0.005)

    def test_f3d_56(self):
        """Rectangular floor to a circular end wall segment"""
        b=1
        c=1
        theta=50
        result = rad.f3d_56(b,c,theta)
        assert isinstance(result, float)
        assert result == pytest.approx(0.1009, rel=0.005)

    def test_f3d_57(self):
        """Rectangular floor to a perpendicular end wall with a circular segment"""
        a=1
        b=1
        c=1
        theta=30
        result = rad.f3d_57(a,b,c,theta)
        assert isinstance(result, float)
        assert result == pytest.approx(0.2662, rel=0.005)

    def test_f3d_58(self):
        """Circular disk to parallel right triangle"""
        r=0.5
        d=1
        l_1=5
        l_2=0.7
        result = rad.f3d_58(r,d,l_1,l_2)
        assert isinstance(result, float)
        assert result == pytest.approx(0.1194, rel=0.005)

    def test_f3d_59(self):
        """Disk to second coaxial disk within a cone"""
        x=0.5
        e=0.2
        theta=30*np.pi/180
        result = rad.f3d_59(e,x,theta)
        assert isinstance(result, float)
        assert result == pytest.approx(0.1627, rel=0.005)

    def test_f3d_60(self):
        """Disk to second disk in a sphere with intersection between disks."""
        h_1=0.25
        h_2=0.15
        r_s=0.5
        result = rad.f3d_60(h_1,h_2,r_s)
        assert isinstance(result, float)
        assert result == pytest.approx(0.4667, rel=0.005)

    def test_f3d_61(self):
        """Disk to second disk in a sphere with intersection outside of disks."""
        h_1=0.25
        h_2=0.15
        r_s=0.5
        result = rad.f3d_61(h_1,h_2,r_s)
        assert isinstance(result, float)
        assert result == pytest.approx(0.8667, rel=0.005)

    def test_f3d_62(self):
        """Disk to concentric ring that is parallel."""
        a=0.3
        r_1=0.15
        r_2=0.1
        r_3=0.2
        result = rad.f3d_62(a,r_1,r_2,r_3)
        assert isinstance(result, float)
        assert result == pytest.approx(0.4867, rel=0.005)

    def test_f3d_63(self):
        """Disk to coaxial cone."""
        r_1=0.2
        r_2=1
        s=0.1
        alpha = np.pi/4
        result = rad.f3d_63(r_1,r_2,alpha,s)
        assert isinstance(result, float)
        assert result == pytest.approx(0.4584, rel=0.005)

    def test_f3d_64(self):
        """Annular disk to truncated coaxial cone"""
        h=1
        r_1=1
        r_2=0.2
        alpha = np.pi/4
        result = rad.f3d_64(h,r_1,r_2,alpha)
        assert isinstance(result, float)
        assert result == pytest.approx(0.5481, rel=0.005)

    def test_f3d_65(self):
        """Annular ring to inside of outer cylinder"""
        r_c=0.2
        r_1=0.4
        r_2=0.5
        h=0.5
        result = rad.f3d_65(r_c,r_1,r_2,h)
        assert isinstance(result, float)
        assert result == pytest.approx(0.5228, rel=0.005)

    def test_f3d_66(self):
        """Annular rings at the ends of an inscribed cylinder"""
        r_c=0.1
        r_1=0.3
        r_2=0.2
        h=0.5
        result = rad.f3d_66(r_c,r_1,r_2,h)
        assert isinstance(result, float)
        assert result == pytest.approx(0.1413, rel=0.005)

    def test_f3d_67(self):
        """Cylinder to flat annular ring below the base"""
        r_c=0.1
        r_1=0.15
        r_2=0.5
        h_1=0.1
        h_2=0.4
        result = rad.f3d_67(r_c,r_1,r_2,h_1, h_2)
        assert isinstance(result, float)
        assert result == pytest.approx(0.1213, rel=0.005)

    def test_f3d_68(self):
        """Annular ring1 to annular ring2 with the presence of an inner cylinder"""
        r_c=0.1
        r_1=0.2
        r_2=0.3
        r_3=0.4
        r_4=0.5
        h=0.5
        result = rad.f3d_68(r_c,r_1,r_2,r_3, r_4,h)
        assert isinstance(result, float)
        assert result == pytest.approx(0.0596, rel=0.005)
    
    def test_f3d_69(self):
        """Annular ring1 to annular ring2 with the presence of an inner cylinder"""
        r_c=0.2
        r_1=0.4
        r_2=0.5
        r_3=0.8
        h_1=0.5
        h_2=1.0
        result = rad.f3d_69(r_c,r_1,r_2,r_3, h_1,h_2)
        assert isinstance(result, float)
        assert result == pytest.approx(0.2412, rel=0.005)

    def test_f3d_70(self):
        """Cylinder inner surface to an adjacent surface on the same cylinder"""
        r_c=0.5
        r=1
        s=0.1
        h_1=0.25
        h_2=0.5
        result = rad.f3d_70(r_c,r,s,h_1,h_2)
        assert isinstance(result, float)
        assert result == pytest.approx(0.09284, rel=0.005)

    # def test_f3d_74(self):
    #     """A square surface to a second square surface located in a perpendicular plane"""
    #     s1=1
    #     s2=2
    #     alpha=30
    #     N_rays=1e6
    #     result = rad.f3d_74(N_rays, s1, s2, alpha)
    #     assert isinstance(result, float)
    #     assert result == pytest.approx(0.316, rel=0.005)

    def test_f3d_75(self):
        """Two half-circles of the same radius sharing a common edge"""
        alpha=1.5
        result = rad.f3d_75(alpha)
        assert isinstance(result, float)
        assert result == pytest.approx(0.273, rel=0.005)

    def test_f3d_76(self):
        """Half circle to enclosure formed by second half-circle with common edge"""
        alpha = np.pi/3
        result = rad.f3d_76(alpha)
        assert isinstance(result, float)
        assert result == pytest.approx(0.5556, rel=0.005)

    # def test_f3d_77(self):
    #     """Sector of circular disk to sector of parallel circular disk"""
    #     r1=1.5
    #     r2=2
    #     h=1
    #     beta=np.pi/2
    #     alpha=np.pi
    #     N_rays=10000
    #     result = rad.f3d_77(N_rays, r1, r2, h, beta, alpha)
    #     assert isinstance(result, float)
    #     assert result == pytest.approx(0.5186, rel=0.005)




class TestDifferentialViewFactors:
    """Test differential view factor functions"""

    def test_fdiff_01(self):
        """Test view factor between differential element and plane parallel rectangle"""
        """Doc example: hs301.htm -- a=3, b=2, c=0.5, Solution F=0.2409"""
        result = rad.fdiff_01(a=3, b=2, c=0.5)  # doc: hs301.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.2409, rel=0.005)

    def test_fdiff_02(self):
        """Test view factor from strip element to rectangle in parallel plane"""
        """Doc example: hs302.htm -- a=3, b=2, c=0.5, Solution F=0.3886"""
        result = rad.fdiff_02(a=3, b=2, c=0.5)  # doc: hs302.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.3886, rel=0.005)

    def test_fdiff_03(self):
        """Test view factor from plane element to rectangle in perpendicular plane"""
        """Doc example: hs303.htm -- a=1, b=2, c=0.5, Solution F=0.1355"""
        result = rad.fdiff_03(a=1, b=2, c=0.5)  # doc: hs303.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.1355, rel=0.005)

    def test_fdiff_04(self):
        """Test view factor from strip element to rectangle in perpendicular plane"""
        """Doc example: hs304.htm -- a=1, b=2, c=0.5, Solution F=0.2153"""
        result = rad.fdiff_04(a=1, b=2, c=0.5)  # doc: hs304.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.2153, rel=0.005)

    def test_fdiff_05(self):
        """Test view factor between spherical point and plane rectangle"""
        """Doc example: hs305.htm -- a=1, b=2, c=0.5, Solution F=0.0836"""
        result = rad.fdiff_05(a=1, b=2, c=0.5)  # doc: hs305.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.0836, rel=0.005)

    def test_fdiff_06(self):
        """Test view factor between differential ring element and coaxial ring on disk"""
        """Doc example: hs306.htm -- example evaluated at r/2 leads to F=0.7155"""
        result = rad.fdiff_06(r_1=0.5, r_2=1, h=1)  # doc: hs306.htm (mapped conservatively)
        assert isinstance(result, float)
        assert result == pytest.approx(0.7155, rel=0.005)

    def test_fdiff_07(self):
        """Test view factor between ring element on cylinder interior and disk at cylinder end"""
        """Doc example: hs307.htm -- r=1, h=2 => Solution F=0.06066 (h mapped to x)"""
        result = rad.fdiff_07(r=1, x=2)  # doc: hs307.htm (mapped)
        assert isinstance(result, float)
        assert result == pytest.approx(0.06066, rel=0.005)

    def test_fdiff_08(self):
        """Test view factor between differential ring on disk 1 and coaxial parallel disk 2"""
        """Doc example: hs308.htm -- r1=0.5, r2=1, a=2, Solution F=0.1847"""
        result = rad.fdiff_08(r_1=0.5, r_2=1, a=2)  # doc: hs308.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.1847, rel=0.005)

    def test_fdiff_09(self):
        """Test view factor between ring element on cylinder base and circumferential ring on interior"""
        """Doc example: hs309.htm -- r2=1, x1=0, x2=2 => Solution F=0.8153
        EES value differs from documentation value"""
        result = rad.fdiff_09(r_1=0.5, r_2=1, x_1=0, x_2=2)  # doc: hs309.htm (r1 mapped conservatively)
        assert isinstance(result, float)
        assert result == pytest.approx(0.8153, rel=0.005)

    def test_fdiff_10(self):
        """Test view factor between element on longitudinal strip and cylinder base"""
        """Doc example: hs310.htm -- r=1, h=2 (h mapped to sz) => Solution F=0.06066"""
        result = rad.fdiff_10(r=1, sz=2)  # doc: hs310.htm (mapped)
        assert isinstance(result, float)
        assert result == pytest.approx(0.06066, rel=0.005)

    def test_fdiff_11(self):
        """Test view factor between element on longitudinal strip and cylinder interior surface"""
        """Doc example: hs311.htm -- r=1, h=2 (h mapped to sh), gives F=0.6053"""
        result = rad.fdiff_11(r=1, sz=0.5, sh=2)  # doc: hs311.htm (mapped sz conservatively)
        assert isinstance(result, float)
        assert result == pytest.approx(0.6053, rel=0.005)

    def test_fdiff_12(self):
        """Test view factor between element on longitudinal strip and disk on cylinder base"""
        """Doc example: hs312.htm -- r1=1, r2=1, h=0.5 (h mapped to sz) => Solution F=0.2957"""
        result = rad.fdiff_12(r1=1, r2=1, sz=0.5)  # doc: hs312.htm (mapped)
        assert isinstance(result, float)
        assert result == pytest.approx(0.2957, rel=0.005)

    def test_fdiff_13(self):
        """Test view factor between element on longitudinal strip and exterior of concentric smaller cylinder"""
        """Doc example: hs313.htm -- r1=0.5, r2=1, h=2 (h mapped to sh), sz mapped conservatively => F=0.4397"""
        result = rad.fdiff_13(r_1=0.5, r_2=1, sz=0.5, sh=2)  # doc: hs313.htm (mapped)
        assert isinstance(result, float)
        assert result == pytest.approx(0.4397, rel=0.005)

    def test_fdiff_14(self):
        """Test view factor between element on longitudinal strip and outer concentric cylinder"""
        """Doc example: hs314.htm -- r1=0.5, r2=1, h=2 (h mapped to sh), sz conservatively => F=0.3414"""
        result = rad.fdiff_14(r_1=0.5, r_2=1, sz=0.5, sh=2)  # doc: hs314.htm (mapped)
        assert isinstance(result, float)
        assert result == pytest.approx(0.3414, rel=0.005)

    def test_fdiff_15(self):
        """Test view factor between element on longitudinal strip and annular end space between coaxial cylinders"""
        """Doc example: hs315.htm -- r1=0.2, r2=0.3, z=0.3 (z mapped to sz) => F=0.2966"""
        result = rad.fdiff_15(r_1=0.2, r_2=0.3, sz=0.3)  # doc: hs315.htm (mapped)
        assert isinstance(result, float)
        assert result == pytest.approx(0.2966, rel=0.005)

    def test_fdiff_16(self):
        """Test view factor between differential area and parallel disk"""
        """Doc example: hs316.htm -- H=1, a=0.5, R=1 => F=0.4380"""
        result = rad.fdiff_16(H=1, a=0.5, R=1)  # doc: hs316.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.4380, rel=0.005)

    def test_fdiff_17(self):
        """Test view factor between differential area and cylinder (area at midpoint)"""
        """Doc example: hs317.htm -- R=1, L=2, H=1.5 => F=0.6594"""
        result = rad.fdiff_17(R=1, L=2, H=1.5)  # doc: hs317.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.6594, rel=0.005)

    def test_fdiff_18(self):
        """Test view factor between differential area and cylinder (area at end point)"""
        """Doc example: hs318.htm -- R=1, L=2, H=1.5 => F=0.3297"""
        result = rad.fdiff_18(R=1, L=2, H=1.5)  # doc: hs318.htm
        assert isinstance(result, float)
        assert result == pytest.approx(0.3297, rel=0.005)


if __name__ == "__main__":
    T = Test3DViewFactors()
    T.test_f3d_44()