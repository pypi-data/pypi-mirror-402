"""
This file is for use by students and faculty at the University of Wisconsin-Madison 
as part of the ME564 Heat Transfer course, instructor Mike Wagner. Code is derived 
from Engineering Equation Solver (EES) under license restrictions.
"""

from numpy import sin, cos, tan, exp, arctan, sqrt, pi, arcsin, arccos, log, log10
import numpy as __np
from random import uniform as __uniform
from scipy import integrate as __integrate
from scipy.special import erf as __erf
from eeslib import lookup_data

def __warning(msg,*args):
    print(f"Warning: {msg}\t" + '\t'.join(args))


def Blackbody(T,lambda_1,lambda_2):
    """
    Blackbody returns the fraction of the blackbody emissive power that is emitted between wavelengths lambda_1 and lambda_2
    
    Parameters
    ----------
    T : float
        Absolute temperature in Kelvin
    lambda_1 : float
        Wavelength 1 in microns
    lambda_2 : float
        Wavelength 2 in microns
    """

    if (lambda_1<0 ) or (lambda_2<0 ):
        __warning('Wavelength must be positive in F')
    
    if (T<0):
        __warning('Absolute temperature must be positive in F')
    
    if (lambda_1<1e-4 ): 
        lambda_1=1e-4 
    
    if (lambda_2<1e-4 ):
        lambda_2=1e-4 

    C2=14388 #[micron-K]
    Nt=10 #[-]

    gamma=C2/(lambda_1*T)
    f = __np.zeros(Nt)
    for i in range(1,Nt+1):
        f[i-1]=exp(-i*gamma)*(gamma**3+3*gamma**2/i+6*gamma/i**2+6/i**3)/i
    F1=15*sum(f)/pi**4

    gamma=C2/(lambda_2*T)
    for i in range(1,Nt+1):
       f[i-1]=exp(-i*gamma)*(gamma**3+3*gamma**2/i+6*gamma/i**2+6/i**3)/i
    F2=15*sum(f)/pi**4
    
    return max(F1,F2)-min(F1,F2)

def Eb(T,lam):
    """
    Eb returns the blackbody spectral emissive power at temperature T [K] and wavelength lam [microns].

    :math:`E_b(\\lambda,T) = \\frac{C_1}{\\lambda^5 \\left( e^{\\frac{C_2}{\\lambda T}} - 1 \\right) }`

    Parameters
    ----------
    T : float
        Absolute temperature in Kelvin
    lam : float
        Wavelength in microns
    """
    C1=3.7420e8
    C2=1.4388e4
    sigma=5.670e-8 #[W/m**2-K**4]
    Eb=C1/(lam**5*(exp(C2/(lam*T))-1))
    return Eb

def polygon_area(poly):
    """
    Compute the area of a polygon defined by a list of vertices in 'poly'. 
    The polygon coordinates should be contained within a 2D plane.

    Parameters
    ----------
        poly : numpy.array((n,2))
            The poly data should be of the form:
                [[x1,y1],[x2,y2],...,[xn,yn]]

    Returns
    -------
        area inside the polygon
    """
    x,y = poly.T  #unpack to 2 dimensions
    return 0.5*__np.abs(__np.dot(x,__np.roll(y,1))-__np.dot(y,__np.roll(x,1)))
# ----------------------------------------------------------

def hit_test(poly, points):
    """
    Determines whether each point [x,y] contained in the array of 'points' [[x1,y1],[x2,y2],...]
    lies within a polygon 'poly' defined by a list of vertices [[x1,y1],[x2,y2],...]. 

    Note that there is another function in_polygon above that accepts a single x,y 
    position rather than a numpy array of points.

    Parameters
    ----------
        poly : numpy.array((N,2)) 
            2-D array of polygon vertices. Points are given in terms
            of the x-y coordinates within the polygon's plane
        points : numpy.array((M,2)) OR numpy.array((2,1))
            List of M points to test for inclusion in the polygon. Data should either 
            be of the form:
            [[x1,y2],[x2,y2],...,[xm,ym]]
            OR
            [x,y]

    Returns
    -------
        numpy.array((M,2))
            M-length array with entries of 1 if corresponding point lies within polygon, 0 otherwise
    """
    if len(points.shape)==1:
        points_array = __np.array([points])
    else:
        points_array = points

    pt0 = points_array.T[0]  #all x-values of points
    pt1 = points_array.T[1]  #all y-values of points
    p0,p1 = poly[-1,:] #start with last point
    
    wind = __np.zeros(len(points_array))

    for poly_point in poly:
        d0,d1 = poly_point  #unpack x,y

        fp = __np.where((p1 <= pt1) & (d1 >  pt1) & ((p0 - pt0)*(d1 - pt1) - (p1 - pt1)*(d0 - pt0) > 0))
        fm = __np.where((p1 >  pt1) & (d1 <= pt1) & ((p0 - pt0)*(d1 - pt1) - (p1 - pt1)*(d0 - pt0) < 0))
        
        wind[fp] += 1
        wind[fm] -= 1

        p0=d0
        p1=d1
    
    return __np.abs(wind) == 1




# ============================================================
    
def f2d_01(h,w):
    """
    Function F2D_1 returns the view factor between two infinitely long, direct
    
    ref: Siegel and Howell, Thermal Radiation Heat Transfer, 4th edition, p.843.

    Parameters
    ----------
    h : float
        is the distance between the plates
    w : float
        is the width of the plate;

    """
    if (w<=0): __warning(f'The width of the plates must be greater than zero. The value given for w is {w}')
    if (h<0): __warning(f'The distance between the plates must be greater than or equal to zero. The value given for h is {h}')
    HH=h/w
    f2d_1=sqrt(1+HH**2)-HH
    return f2d_1
    
def f2d_02(alpha,w):
    """
    Function F2D_2 returns the view factor between two infinitely long plates of the same finite width having a common edge and having an included angle alpha to each other
    
    ref: Siegel and Howell, Thermal Radiation Heat Transfer, 4th edition, p.844.
    
    Parameters
    ----------
    alpha : float
        the angle between the plates
    w : float
        the width of each plate;
    """
    # alpha_deg=alpha*convert(D$, deg)
    err1 = f'The angle of inclination between the plates must be 0<alpha<180 [deg]. The value given for alpha is {alpha}.'
    if ((alpha<0) or (alpha>pi)): __warning(err1)
    f2d_2=1-sin(alpha/2)
    return f2d_2
    
def f2d_03(r,a,b_1,b_2):
    """
    This function calculates the View Factor from an infinitely long plane of finite width to a parallel infinitely long cylinder.
    
    Howell, http://www.me.utexas.edu/~howell/sectionc/C-62.html

    Parameters
    ----------
    r : float
        radius of cylinder; 
    a : float
        height from the top surface of the plate the center of the cylinder;
    b_1 : float
        distance from center of cylinder to far end of plate;
    b_2 : float
        from center of cylinder to near end of plate;

    """
    if (r>sqrt(a**2+b_2**2)): __warning('r<=sqrt(a**2+b_2**2), The cylinder cannot intersect the plate for F2D_3.')
    if (a<=0): __warning(f'Function value a outside of range, has value {a}')
    if (b_2>=b_1): __warning('b_2 must be less than b_1 for the function F2D_3 to be valid.')
    if (b_2<=0): __warning(f'Function value b_2 outside of range, has value {b_2}')  
    f2d_3=(1/(2*pi))*(arctan(b_1/a) - arctan(b_2/a))
    return f2d_3
    
def f2d_04(r,s):
    """
    This function provides the view factor from an infinitely long cylinder to a parallel infinitely long cylinder of identical diameter.
    
    Reference: Siegel and Howell, Thermal Radiation Heat Transfer, 4th edition, p.847.

    Parameters
    ----------
    r : float
        radius of the cylinder
    s : float
        distance between the cylinders, measured from the closest points on the cylinders' surfaces.  
    """
    if (s<=0): __warning(f'Function value s outside of range, has value {s}')
    if (r<=0): __warning(f'Function value r outside of range, has value {r}')
    X = 1 + s/(2*r)
    f2d_4 = 1/pi * ( sqrt( X**2 - 1 ) + arcsin( 1/X ) - X )
    return f2d_4
    
def f2d_05(r_1,r_2):
    """
    This function provides the view factor between two infinitely long concentric cylinders.
    
    ref: Siegel and Howell, Thermal Radiation Heat Transfer, 4th edition, p.847

    Parameters
    ----------
    r_1 : float
        radius of cylinder1
    r_2 : float
        radius of cylinder 2
    """
    if (r_1<0): __warning(f'Function value r_1 outside of range, has value {r_1}')
    if (r_2<=r_1): __warning(f'Function value r_2 outside of range, has value {r_2}')
    f2d_5 = 1-r_1/r_2
    return f2d_5 
    
def f2d_06(a,b):
    """
    This function calculates the View Factor from an infinitely long plane of finite width to a parallel infinitely long cylinder.
    
    Reference: Howell, Radiation Configuration Factors,  www.me.utexas.edu/~howell/sectionc/C-61.html.

    Parameters
    ----------
    r : float
        radius of cylinder; 
    a : float
        height from the top surface of the plate the center of the cylinder.
    b : float
        distance from center of cylinder to an end of plate;
    """
    if (a<=0): __warning(f'Function value a outside of range, has value {a}')
    # if (r<=a): __warning('r<=a, the cylinder cannot intersect the plate for function F2D_6.')
    f2d_6=1/pi*arctan(b/a) 
    return f2d_6
    
def f2d_07(d, s):
    """
    This function provides the view factor between an infinite plane and a row of infinite cylinders
    
    Reference: Incropera & DeWitt, Fundamentals of Heat and Mass Transfer, 5th edition, p. 794.

    Parameters
    ----------
    d : float
        diameter of the cylinders
    s : float
        distance between cylinder axes
    """
    if(s<=d): __warning('s<=d in F2D_7, view factor is not valid if the cylinders overlap.')
    if (d<=0): __warning(f'Function value d outside of range, has value {d}')
    if (s<=0): __warning(f'Function value s outside of range, has value {s}')
    f2d_7= 1- (1-(d/s)**2)**(1/2)+(d/s)*arctan(sqrt((s**2-d**2)/d**2))
    return f2d_7
    
def f2d_08(r1,r2):
    """
    This function provides the view factor between the interior of an infinitely long semicircle to itself while  a concentric coaxial cylinder is present.
    
    Reference: Howell, J. 'A Catalog of Radiation Configuration Factors.' New York: McGraw Hill, 1982. p. 145

    Parameters
    ----------
    r1 :float
        radius of the cylinder
    r2 :float
        radius of the semicylinder
    """
    if(r1>=r2): __warning('r1>=r2 in F2D_8, the cylinder radius must be smaller than that of the semicylinder for view factor to be valid.')
    if(r1<=0): __warning(f'Function value r1 outside of range, has value {r1}')
    R=r1/r2
    f2d_8=1-2/pi*((1-R**2)**(1/2)+R*arcsin(R))
    return f2d_8
    
def f2d_09(r_1,r_2,s):
    """
    This function provides the view factor from an infinitely long cylinder of radius r_1 to a parallel infinitely long cylinder of radius r_2.
    
    Reference: Incropera & DeWitt, Fundamentals of Heat and Mass Transfer, 5th edition, p. 794.

    Parameters
    ----------
    r_1 : float
        radius of the emitting cylinder
    r_2 : float
        radius of the recieving cylinder
    s : float
        distance between the cylinders, measured from the closest points on the cylinders' surfaces.  
    """
    if (s<=0): __warning(f'Function value s outside of range, has value {s}')
    if (r_1<=0): __warning(f'Function value r_1 outside of range, has value {r_1}')
    if (r_2<=0): __warning(f'Function value r_2 outside of range, has value {r_2}')
    R=r_2/r_1; Sc=s/r_1; C=1+R+Sc
    f2d_9 = 1/(2*pi)*(pi+(C**2-(R+1)**2)**(1/2)-(C**2-(R-1)**2)**(1/2)+(R-1)*arccos((R/C)-(1/C))-(R+1)*arccos((R/C)+(1/C)))
    return f2d_9
    
def f2d_10(a,b,c):
    """
    This function provides the view factor between two infinitely long parallel plates of differing widths.

    Reference: Rohsenow et al, Handbook of Heat Transfer, 3rd ed, McGraw-Hill, p.7.80
    
    Parameters
    ----------
    a : float 
        is the distance between the plates
    b : float 
        is the width of the plate 1;
    c : float 
        is the width of plate 2

    """
    if (b<=0): __warning(f'The width of the plate must be greater than zero. The value given for bis {b}')
    if (c<=0): __warning(f'The width of the plate must be greater than zero. The value given for cis {b}')
    if (a<0): __warning(f'The distance between the plates must be greater than or equal to zero. The value given for h is {a}')
    BB=b/a
    CC=c/a
    f2d_10=1/(2*BB)*(sqrt((BB+CC)**2+4)-sqrt((CC-BB)**2+4))
    return f2d_10
    
def f2d_11(A1, A2, A3):
    """
    This function provides the view factor between two sides of an infinitely long enclose formed by three planar or convex surfaces.
    
    Reference: Rohsenow et al, Handbook of Heat Transfer, 3rd ed, McGraw-Hill, p.7.80

    Parameters
    ----------
    A1 : float
        area per unit width into the screen of side 1
    A2 : float
        area per unit width into the screen of side 2
    A3 : float
        area per unit width into the screen of side 3
    """
    if (A1<=0): __warning(f'The area of the plate must be greater than zero. The value given for A1 is {A1}')
    if (A2<=0): __warning(f'The area of the plate must be greater than zero. The value given for A2 is {A2}')
    if (A3<=0): __warning(f'The area of the plate must be greater than zero. The value given for A3 is {A3}')
    f2d_11=(A1+A2-A3)/(2*A1)
    return f2d_11
    
def f2d_12(w, h):
    """
    This function provides the view factor between two infinitely long plates of unequal widths h and w, having one common edge, and at an angle of 90o to each other.
    
    Reference:  http://www.me.utexas.edu/~howell/sectionc/C-3.html

    Parameters
    ----------
    w : float
        area per unit width into the screen of surface 1
    h : float
        area per unit width into the screen of surface 2
    """
    if (w<=0): __warning(f'The area of the plate must be greater than zero. The value given for w is {w}')
    if (h<=0): __warning(f'The area of the plate must be greater than zero. The value given for h is {h}')
    BH=h/w
    f2d_12=1/2*(1+BH-sqrt(1+BH**2))
    return f2d_12
    
def f2d_13(b, a,alpha):
    """
    This function provides the view factor between two infinitely long plates of unequal width having a common edge with an included angle alpha.
    
    Reference:  http://www.me.utexas.edu/~howell/sectionc/C-5.html

    Parameters
    ----------
    b : float
        area per unit width into the screen of surface 1
    a : float
        area per unit width into the screen of surface 2 
    alpha : float
        the included angle
    """
    if (a<=0): __warning(f'The area of the plate must be greater than zero. The value given for a is {a}')
    if (b<=0): __warning(f'The area of the plate must be greater than zero. The value given for b is {b}')
    AB=a/b
    f2d_13=(AB+1-sqrt(AB**2+1-2*AB*cos(alpha)))/2
    return f2d_13
    
def f2d_14(W1,W2,H,a):
    """
    F2D_14
    This function provides the view factor between two infinitely long plates that run parallel to one another.  
    
    Reference:  http://www.thermalradiation.net/sectionc/C-2a.htm
    
    Parameters
    ----------
    W1 : float
        area per unit width of surface 1
    W2 : float
        area per unit width of surface 2
    H : float
        separation distance
    a : float
        distance from leading edge of surface 1 to leading edge of surface 2
    """
    if (W1<=0): __warning(f'The area of plate 1 in F2D_14 must be greater than zero. The value given for W1 is {W1}')
    if (W2<=0): __warning(f'The area of plate 2 in F2D_14 must be greater than zero. The value given for W2 is {W2}')
    if (H<=0): __warning(f'The distance between plates in F2D_14 must be greater than zero. The value given for H is {H}')
    
    L1=sqrt((W1-a)**2+H**2)
    L2=sqrt((a+W2)**2+H**2)
    L3=sqrt(a**2+H**2)
    L4=sqrt((a+W2-W1)**2+H**2)
    f2d_14=(L1+L2-L3-L4)/(2*W1)
    return f2d_14
    
def f2d_15(x1, x2, y1, y2, alpha):
    """
    This function provides the view factor between two infinitely long plates of unequal width without a common edge.  
    The included angle between the plates is alpha.
    
    Reference:  http://www.thermalradiation.net/sectionc/C-5a.html

    Parameters
    ----------
    x1 : float
        distance from vertex to leading edge of plate 1
    x2 : float
        distance from vertex to trailing edge of plate 1
    y1 : float
        distance from vertex to leading edge of plate 2
    y2 : float
        distance from vertex to trailing edge of plate 2
    alpha : float
        included angle
    """
    
    if (x1<0): __warning(f'The value of x1 in F2D_14 must be greater than zero. The value given for x1 is {x1}')
    if (x2<0): __warning(f'The value of x2 in F2D_14 must be greater than zero. The value given for x2 is {x2}')
    if (y1<0): __warning(f'The value of y1 in F2D_14 must be greater than zero. The value given for y1 is {y1}')
    if (y2<0): __warning(f'The value of y2 in F2D_14 must be greater than zero. The value given for y2 is {y2}')
    
    N1=sqrt(x1**2-2*x1*y2*cos(alpha)+y2**2)
    N2=sqrt(x2**2-2*x2*y1*cos(alpha)+y1**2)
    N3=sqrt(x2**2-2*x2*y2*cos(alpha)+y2**2)
    N4=sqrt(x1**2-2*x1*y1*cos(alpha)+y1**2)
    f2d_15=(N1+N2-N3-N4)/(2*(x2-x1))
    return f2d_15
    
def f2d_16(d, s, n):
    """
    This function provides the view factor between an infinite surface and n rows of an infinite tube array where the tubes are in-line.  
    
    Reference: http://www.thermalradiation.net/sectionc/C-7.html
    
    Parameters
    ----------
    d : float
        diameter of the cylinders
    s : float
        distance between cylinder axes
    n : float
        number of rows
    """
    
    if (d<0): __warning(f'The value of d in F2D_16 must be greater than zero. The value given for d is {d}')
    if (s<d): __warning(f'The value of s in F2D_16 must be greater than the value of d. The value given for s is {s}')
    if (n<=0): __warning(f'The value of n in F2D_16 must be greater than zero. The value given for n is {n}')
    
    F1=f2d_07(d, s)
    f2d_16=1-(1-F1)**n
    return f2d_16
    
def f2d_17(d, p):
    """
    This function provides the view factor from an infinite surface to the second row of infinite tubes in an equilateral triangular array.
    
    Reference: http://www.thermalradiation.net/sectionc/C-8.html
    
    Parameters
    ----------
    d : float
        diameter of the cylinders
    p : float
        distance between cylinder axes
    """
    
    if (d<0): __warning(f'The value of d in F2D_17 must be greater than zero. The value given for d is {d}')
    if (p<d): __warning(f'The value of p in F2D_17 must be greater than the value of d. The value given for p is {p}')
    
    R=p/d
    f2d_17=0.258341996*(1-exp(-1.7356453*(R-1)))-0.0184580465*(R-1)
    return f2d_17
    
    # _________________________________________________________________
    # $BookMark 3DViewFactors
    
# def f3d_poly(NA,NB,xA,yA,zA,xB,yB,zB):
#     """
#     f3d_poly(NA,NB,xA[1..NA],yA[1..NA],zA[1..NA],xB[1..NB],yB[1..NB],zB[1..NB]:F_AB,F_BA,areaA,areaB)
    
#     F3D_poly
#     The F3D_poly procedure returns the view factors between two polygons as well as their areas provided the following conditions are met: 
#     1) polygons are planar (all vertices lie in the same plane)
#     2) polygons are simple (no self-intersecting polygons)
#     3) polygons are convex (in theory, concave polygons should work, but this remains untested)
    
#     Author: Jacob Kerkhoff, University of Wisconsin-Madison, Solar Energy Laboratory
    
#     Analytical solution derivation:
#     Narayanaswamy, Arvind. "An analytic expression for radiation view factor between two arbitrarily oriented planar polygons." International Journal of Heat and Mass Transfer 91 (2015): 841-847.
    
#     Inputs:
#     NA = number of vertices for polygon A
#     NB = number of vertices for polygon B
    
#     xA[1..NA] = array containing the x-coordinates of polygon A vertices (m or ft)
#     yA[1..NA] = array containing the y-coordinates of polygon A vertices (m or ft)
#     zA[1..NA] = array containing the z-coordinates of polygon A vertices (m or ft)
    
#     xB[1..NA] = array containing the x-coordinates of polygon B vertices (m or ft)
#     yB[1..NA] = array containing the y-coordinates of polygon B vertices (m or ft)
#     zB[1..NA] = array containing the z-coordinates of polygon B vertices (m or ft)
    
#     Outputs:
#     F_AB = view factor from polygon A to polygon B
#     F_BA = view factor from polygon B to polygon A
#     areaA = area of polygon A (m**2 or ft**2)
#     areaB = area of polygon B (m**2 or ft**2)

#     """
    
#     if (NA<3): __warning('Number of vertices for polygon A in F3D_poly must be at least 3')
#     if (NB<3): __warning('Number of vertices for polygon B in F3D_poly must be at least 3')
#     Duplicate i=1,NA
#         xAp[i]=xA[i]
#         yAp[i]=yA[i]
#         zAp[i]=zA[i]
#     End
#     Duplicate i=(NA+1),200
#         xAp[i]=0
#         yAp[i]=0
#         zAp[i]=0
#     End
#     Duplicate i=1,NB
#         xBp[i]=xB[i]
#         yBp[i]=yB[i]
#         zBp[i]=zB[i]
#     End
#     Duplicate i=(NB+1),200
#         xBp[i]=0
#         yBp[i]=0
#         zBp[i]=0
#     End
    
#     Call vfp(NA,NB,xAp[1..200],yAp[1..200],zAp[1..200],xBp[1..200],yBp[1..200],zBp[1..200]:F_AB,F_BA,areaA,areaB) 
    
#     return F_AB,F_BA,areaA,areaB
    
def f3d_01(a,b,c):
    """
    The F3D_1 function returns the view factor between two identical opposite rectangular plates. 

    Siegel and Howell, Thermal Radiation Heat Transfer, 4th edition, p.843.
    
    Parameters
    ----------
    a : float
        dimension of rectangle 1
    b : float
        dimension of rectangle 2
    c : float
        distance between them.
    """
    if (a<=0): __warning(f'Function value a outside of range, has value {a}')
    if (b<=0): __warning(f'Function value b outside of range, has value {b}')
    if (c<=0): __warning(f'Function value c outside of range, has value {c}')
    X = a/c
    Y = b/c
    Term_1 = log(sqrt(((1+X**2)*(1+Y**2))/(1+X**2+Y**2)))
    Term_2 = X*sqrt(1+Y**2)*arctan(X/sqrt(1+Y**2))
    Term_3 = Y*sqrt(1+X**2)*arctan(Y/sqrt(1+X**2))
    Term_4 = -X*arctan(X) - Y*arctan(Y)
    f3d_1 = 2/(pi*X*Y)*(Term_1 + (Term_2 + Term_3 + Term_4))
    return f3d_1
    
def f3d_02(a,b,c): 
    """
    This function returns the view factor from area1 to area 2 of two finite rectangles of the same length, having one common edge and having an angle of 90 degree to each other.
    
    Note: The input values have to be greater than 0!
    Siegel and Howell, Thermal Radiation Heat Transfer, 4th edition, p.844.

    Parameters
    ----------
    a : float 
        height of area 1 
    b : float 
        height of area 2 
    c : float 
        length of common edge
    """
    if (a<=0): __warning(f'Function value a outside of range, has value {a}')
    if (b<=0): __warning(f'Function value b outside of range, has value {b}')
    if (c<=0): __warning(f'Function value c outside of range, has value {c}')
    H=b/c; W=a/c
    A=((1+W**2)*(1+H**2))/(1+W**2+H**2)
    B=((W**2*(1+W**2+H**2))/((1+W**2)*(W**2+H**2)))**(W**2)
    C=((H**2*(1+W**2+H**2))/((1+H**2)*(W**2+H**2)))**(H**2)
    f3d_2=1/(pi*W)*(W*arctan(1/W)+H*arctan(1/H)-sqrt(H**2+W**2)*arctan(1/sqrt(H**2+W**2))+ (1/4)* log(A*B*C))
    return f3d_2
    
def f3d_03(r_1, r_2, h):
    """
    F3D_3  returns the view factor value of one disk (finite area) from another one (finite area) parallel to it which has its center along the same normal.  
    
    Siegel and Howell, Thermal Radiation Heat Transfer, 4th edition, p.845. 

    Parameters
    ----------
    r_1 : float
        the radius of disk 1
    r_2 : float
        the radius of disk 2
    h : float
        the parallel distance between both disks
    """
    if (r_1<=0): __warning(f'Function value r_1 outside of range, has value {r_1}')
    if (r_2<=0): __warning(f'Function value r_2 outside of range, has value {r_2}')
    if (h<=0): __warning(f'Function value h outside of range, has value {h}')
    R1= r_1/h    
    R2 = r_2/h
    X = 1 + (1 + R2**2)/R1**2
    f3d_3= 0.5 * (X - sqrt(X**2 - 4*(R2/R1)**2))
    return f3d_3
    
def f3d_04(r_1,r_2,w):
    """
    This function calculates a radiation view factor between two concentric cylinders of the same finite length .  
    f3d_04(r_1, r_2, w) is the view factor from the smaller of two concentric cylinders to the larger cylinder.  
    
    Siegel and Howell, Thermal Radiation Heat Transfer, 4th edition, p.847

    Parameters
    ----------
    r_1 : float
        radius of the smaller cylinder
    r_2 : float
        radius of the larger cylinder
    w : float
        length of the cylinders
    """
    if (r_1>=r_2): __warning(f'Function value r_1 outside of range, has value {r_1}')
    if (r_1<=0): __warning(f'Function value r_1 outside of range, has value {r_1}')
    if (w<=0): __warning(f'Function value w outside of range, has value {w}')
    R_F32 = r_2/r_1
    L_F32 = w/r_1
    A = L_F32**2+R_F32**2-1
    B = L_F32**2-R_F32**2+1
    F= 1/R_F32-(1/(pi*R_F32))*(arccos(B/A)-(1/(2*L_F32))*(sqrt((A+2)**2-(2*R_F32)**2)*arccos(B/(R_F32*A))+B*arcsin(1/R_F32)-(pi*A)/2))
    f3d_4=r_2/r_1*F
    return f3d_4
    
def f3d_05(r_1, r_2, L):
    """
    F3D_5 returns the configuration factor from the area of the outermost of two concentric cylinders 
    (of the same finite length) to itself.  

    See F3D_4 for the view factor from the inner  to outer cylinder.
    Reference: Howell, http://www.me.utexas.edu/~howell/sectionb/C-91.html 

    Parameters
    ----------
    r_1 : float
        radius of the inner cylinder
    r_2 : float
        radius of the outer cylinder
    L : float
        length of the cylinders
    """
    if (r_1>r_2): __warning(f'Function value r_1 outside of range, has value {r_1}')
    if (r_1<=0): __warning(f'Function value r_1 outside of range, has value {r_1}')
    if (L<=0): __warning(f'Function value L outside of range, has value {L}')
    R1=r_1/L
    R2=r_2/L
    T1=pi*(R2-R1)+arccos(R1/R2)
    T2=-sqrt(1+4*R2**2)*arctan(sqrt((1+4*R2**2)*(R2**2-R1**2))/R1)
    T3=2*R1*arctan(2*sqrt(R2**2-R1**2))
    f3d_5=1/(pi*R2)*(T1+T2+T3)
    return f3d_5
    
def f3d_06(r1,r2,l):
    """
    This function provides the view factor between the outer surface of a cylinder and an annular disk at the end of the cylinder.
    
    Rea, S. Rapid Method for Determining Concentric Cylinder Radiation View Factors. AIAA J., vol. 13, no. 8, pp. 1122-1123, 1975. in Howell, J. 'A Catalog of Radiation Configuration Factors.' New York: McGraw Hill, 1982. p. 161

    Parameters
    ----------
    r1 : float
        radius of the cylinder
    r2 : float
        radius of the outer radius of the annular disk
    l : float
        length of the cylinder
    """
    if (r1>=r2): __warning('r1>=r2 in F3D_6, the disk must have finite area for view factor to be valid.')
    if(r1<=0): __warning(f'Function value r1 outside of range, has value {r1}')
    if(r2<=0): __warning(f'Function value r2 outside of range, has value {r2}')
    if(l<=0): __warning(f'Function value l outside of range, has value {l}')
    R=r1/r2; Lc=l/r2; A=Lc**2+R**2-1;B=Lc**2-R**2+1
    f3d_6=B/(8*R*Lc)+1/(2*pi)*(arccos(A/B)-1/(2*Lc)*((A+2)**2/R**2-4)**(1/2)*arccos(A*R/B)-A/(2*R*Lc)*arcsin(R))
    return f3d_6
    
def f3d_07(l1,l2, d, r):
    """
    This function provides the view factor between a sphere and a rectangle perpendicular to a line through the axis of the sphere.
    
    Reference: Tripp, W., Hwang, C., Crank, R. Radiation Shape Factors for Plane Surfaces and Spheres, Circles or Cylinders, Spec. Rept. 16, Kansas State University Bulletin, vol. 46, no. 4, 1962. in Howell, J. 'A Catalog of Radiation Configuration Factors.' New York: McGraw Hill, 1982. p. 190
    
    Parameters
    ----------
    l1 : float
        half-width of the rectangle
    l2 : float
        half-length of the rectangle
    d : float
        perpendicular distance from the sphere to the rectangle
    r : float
        radius of the sphere
    """
    if (r>d): __warning('r>d in F3D_7, the sphere must be completely outside the rectangle for view factor to be valid.')
    if(l1<=0): __warning(f'Function value l1 outside of range, has value {l1}')
    if(l2<=0): __warning(f'Function value l2 outside of range, has value {l2}')
    if(d<=0): __warning(f'Function value d outside of range, has value {d}')
    if(r<=0): __warning(f'Function value r outside of range, has value {r}')
    D1=d/l1;D2=d/l2
    f3d_7=1/(4*pi)*arctan(1/(D1**2+D2**2+D1**2*D2**2)**(1/2))
    return f3d_7
    
def f3d_08(r1,r2,a1,a2):
    """
    This function provides the view factor between a sphere and the interior surface of a coaxial right circular cylinder. The sphere must be outside the cylinder and its radius smaller than that of the cylinder.
    
    Feingold, A, & Gupta, K. New Analytical Approach to the Evaluation of Configuration Factors in Radiation from Spheres and Infinitely Long Cylinders. ASME J. Heat Transfer, vol. 92, no. 1, pp 69-76. in Howell, J. 'A Catalog of Radiation Configuration Factors.' New York: McGraw Hill, 1982. p. 197

    Parameters
    ----------
    r1 : float
        radius of the sphere
    r2 : float
        radius of the cylinder
    a1 : float
        distance from the centerpoint of the sphere to the plane defining the face of the open end of the cylinder
    a2 : float
        distance from the centerpoint of the sphere to the plane of the closed end of the cylinder
    """
    if(r1>=r2): __warning('r1>=r2 in F3D_8, the radius of the sphere must be less than that of the cylinder for view factor to be valid.')
    if(r1>=a1): __warning('r1>a1 in F3D_8, the sphere must be completely outside the cylinder for view factor to be valid.')
    if(r1<=0):  __warning(f'Function value r1 outside of range, has value {r1}')
    if(a1<=0):  __warning(f'Function value a1 outside of range, has value {a1}')
    if(a2<=a1): __warning(f'Function value a2 outside of range, has value {a2}')
    Rc1=r2/a1;Rc2=r2/a2
    f3d_8=(1/2)*(1/(1+Rc2**2)**(1/2)-1/(1+Rc1**2)**(1/2))
    return f3d_8
    
def f3d_09(r1,r2,a):
    """
    This function provides the view factor between a sphere and the interior surface of a coaxial right circular cylinder. The sphere must be completely enclosed by the cylinder, positioned in the center along the axis of the cylinder, and its radius smaller than that of the cylinder.
    
    Feingold, A, & Gupta, K. New Analytical Approach to the Evaluation of Configuration Factors in Radiation from Spheres and Infinitely Long Cylinders. ASME J. Heat Transfer, vol. 92, no. 1, pp 69-76. in Howell, J. 'A Catalog of Radiation Configuration Factors.' New York: McGraw Hill, 1982. p. 197

    Parameters
    ----------
    r1 : float
        radius of the sphere
    r2 : float
        radius of the cylinder
    a : float
        distance from the centerpoint of the sphere to the plane faces of the sphere
    """
    if (r1>=r2): __warning('r1>=r2 in F3D_9, the sphere must be completely enclosed by the cylinder for view factor to be valid.')
    if (r1>=a): __warning('r1>=a in F3D_9, the sphere must be completely enclosed by the cylinder for view factor to be valid.')
    if(r1<=0): __warning(f'Function value r1 outside of range, has value {r1}')
    R=r2/a
    f3d_9=1/(1+R**2)**(1/2)
    return f3d_9
    
def f3d_10(a,b_1,b_2,c):
    """
    This function provides the view factor between two perpendicular offset rectangles. The base of rectangle 1 is in the same plane as rectangle 2.
    
    Chapman A.J., Fundamentals of Heat Transfer,1984., p.734

    Parameters
    ----------
    a : float
        Length of rectangle 1 in the direction perpendicular to rectangle 2
    b_1 : float
        Offset distance between rectangle 1 and the lower edge of rectangle 2
    b_2 : float
        Height of rectangle 2 
    c : float
        Length of rectangle 1 and rectangle 2 in the direction parallel to the line of intersection of the perpendicular planes
    """
    f3d_10=f3d_02(a,(b_1+b_2),c)-f3d_02(a,b_1,c)
    return f3d_10
    
def f3d_11(a_1, a_2,b_1,b_2,c):
    """
    This function provides the view factor between two perpendicular rectangles that are both offset some distance from the line of intersection of the perpendicular planes.
    
    Chapman A.J., Fundamentals of Heat Transfer,1984., p.734

    Parameters
    ----------
    a_1 : float
        Offset of rectangle 1 in the direction perpendicular to the plane of rectangle 2
    a_2 : float
        Length of rectangle 1 in the direction perpendicular to rectangle 2
    b_1 : float
        Offset of rectangle 2 in the direction perpendicular to the plane of rectangle 1
    b_2 : float
        Length of rectangle 2 in the direction perpendicular to rectangle 1
    c : float
        Length of rectangle 1 and rectangle 2 in the direction parallel to the line of intersection of the perpendicular planes
    """
    A_1=a_2*c
    A_13=(a_1+a_2)*c
    A_3=a_1*c
    f3d_11=(A_13*f3d_02((a_1+a_2),(b_1+b_2),c)+A_3*f3d_02(a_1,b_1,c)-A_3*f3d_02(a_1,(b_1+b_2),c)-A_13*f3d_02((a_1+a_2),b_1,c))/A_1
    return f3d_11
    
def f3d_12(a,b,c_1,c_2):
    """
    This function provides the view factor from area 1 to area 2 of two finite rectangles that are oriented perpendicular to each other and having one common point.

    Chapman A.J., Fundamentals of Heat Transfer,1984., p.736
    
    Parameters
    ----------
    a : float
        length of rectangle 1
    b : float  
        length of rectangle 2, a is perpendicular to b
    c_1 : float
        height of rectangle 1
    c_2 : float
        height of rectangle 2. 
    """
    A_1=a*c_1
    A_3=a* c_2
    F_14=f3d_02(a,b,c_1)
    F_32=f3d_02(a,b,c_2)
    F_13_24=f3d_02(a,b,(c_1+c_2))
    F_12=1/(2*A_1)*((A_1+A_3)*F_13_24-A_1*F_14-A_3*F_32)
    f3d_12=F_12
    return f3d_12
    
def f3d_13(a1, a2, b1, b2, c1, c2, c3):
    """
    F2D_13 
    This function provides the view factor between two perpendicular rectangles that do not share a point.
    
    Chapman A.J., Fundamentals of Heat Transfer,1984., p.738

    Parameters
    ----------
    a1 : float
        offset of rectangle 1 in the direction perpendicular to the plane of rectangle 2
    a2 : float
        length of rectangle 1 in the direction perpendicular to rectangle 2
    b1 : float
        offset of rectangle 2 in the direction perpendicular to the plane of rectangle 1
    b2 : float
        length of rectangle 2 in the direction perpendicular to rectangle 1
    c1 : float
        height of rectangle 1 in the direction parallel to the line of intersection of the perpendicular planes
    c2 : float
        offset between rectangle 1 and 2 in the direction parallel to the line of intersection of the perpendicular planes
    c3 : float
        height of rectangle 2 in the direction parallel to the line of intersection of the perpendicular planes
    """
    KK123456=f3d_02((a1+a2),(b1+b2),(c1+c2+c3))*(a1+a2)*(c1+c2+c3)
    KK2345=f3d_02((a1+a2),(b1+b2),(c1+c2))*(a1+a2)*(c1+c2)
    KK1256=f3d_02((a1+a2),(b1+b2),(c2+c3))*(a1+a2)*(c2+c3)
    KK456=f3d_02(a1,b1,(c1+c2+c3))*a1*(c1+c2+c3)
    K456_123456=f3d_02(a1,(b1+b2),(c1+c2+c3))*a1*(c1+c2+c3)
    K123456_456=f3d_02((a1+a2),b1,(c1+c2+c3))*(a1+a2)*(c1+c2+c3)
    K1256_56=f3d_02((a1+a2),b1,(c2+c3))*(a1+a2)*(c2+c3)
    K2345_45=f3d_02((a1+a2),b1,(c1+c2))*(a1+a2)*(c1+c2)
    K56_1256=f3d_02(a1,(b1+b2),(c2+c3))*a1*(c2+c3)
    K45_2345=f3d_02(a1,(b1+b2),(c1+c2))*a1*(c1+c2)
    KK25=f3d_02((a1+a2),(b1+b2),c2)*(a1+a2)*c2
    K25_5=f3d_02((a1+a2),b1,c2)*(a1+a2)*c2
    KK56=f3d_02(a1,b1,(c2+c3))*a1*(c2+c3)
    KK45=f3d_02(a1,b1,(c1+c2))*a1*(c1+c2)
    K5_25=f3d_02(a1,(b1+b2),c2)*a1*c2
    KK5=f3d_02(a1,b1,c2)*a1*c2
    f3d_13=(KK123456-KK2345-KK1256+KK456-K456_123456-K123456_456+K1256_56+K2345_45+\
            K56_1256+K45_2345+KK25-K25_5-KK56-KK45-K5_25+KK5)/(2*a2*c3)
    return f3d_13
    
def __gf3d14(x,y,n,e,z):
    gf3d14=1/(2*pi)*((y-n)*sqrt((x-e)**2+z**2)*arctan((y-n)/sqrt((x-e)**2+z**2))+(x-e)*sqrt((y-n)**2+z**2)*arctan((x-e)/sqrt((y-n)**2+z**2))-z**2/2*log((x-e)**2+(y-n)**2+z**2))
    return gf3d14
    
def f3d_14(x,y,a,b,z):
    """
    This function provides the view factor from area 1 to area  2 of two arbitrarily-located finite rectangles that are oriented perpendicular to each other.
    
    Parameters
    ----------
    x_1 : float
        x-coordinate of the lower edge of rectangle 1
    x_2 : float
        x-coordinate of the upper edge of rectangle 1
    y_1 : float
        y-coordinate of the lower edge of rectangle 1
    y_2 : float
        y-coordinate of the upper edge of rectangle 1
    a_1 : float
        x-coordinate of the lower edge of rectangle 2
    a_2 : float
        x-coordinate of the upper edge of rectangle 2
    b_1 : float
        y-coordinate of the lower edge of rectangle 2
    b_2 : float
        y-coordinate of the upper edge of rectangle 2
    z : float
        distance between the planes of the two rectangles
    """
    A=(x[1]-x[0])*(y[1]-y[0])
    F=0.
    for i in range(2):
        for j in range(2):
            for k in range(2):
                for l in range(2):
                    F=F+((-1)**(i+j+k+l)*__gf3d14(x[i],y[j],b[k],a[l],z))
    f3d_14=F/A
    return f3d_14
    
    
def f3d_15(l,n,z,d):
    """
    This function provides the view factor between an a finite length cylinder and a rectangle of equal length with two edges parallel to the cylindrical axis.
    
    Wiebelt, J. A. & Ruo, S. Y.  Radiant-interchange configuration factors for finite right circular cylinder to rectangular planes, Int. J. Heat Mas Transfer, vol. 6, no. 2, pp. 143-146, 1963 in Howell, J. 'A Catalog of Radiation Configuration Factors.' New York: McGraw Hill, 1982. p. 154

    Parameters
    ----------
    r : float
        radius of the cylinder
    a : float
        closest distance between the cylindrical axis and the plane
    b : float
        width of the plane
    c : float
        length of both the plane and cylinder
    """
    Lc=l/d; Nc=n/d; Zc=z/d
    if(l<=0): __warning(f'Function value l outside of range, has value {l}')
    if(n<=0): __warning(f'Function value n outside of range, has value {n}')
    if(z<=0): __warning(f'Function value z outside of range, has value {z}')
    if(d<=0): __warning(f'Function value d outside of range, has value {d}')
    if(Zc<2): __warning('Note: function F3D_15 is only valid for ratios 2<z/d<100')
    if(Zc>100): __warning('Note: function F3D_15 is only valid for ratios 2<z/d<100')
    if(Nc<0.5): __warning('Note: function F3D_15 is only valid for ratios of 0.5<n/d<4.5')
    if(Nc>4.5): __warning('Note: function F3D_15 is only valid for ratios 0.5<n/d<4.5')
    if(Lc<0.5): __warning('Note: function F3D_15 is only valid for ratios of 0.5<l/d<4.5')
    if(Lc>4.5): __warning('Note: function F3D_15 is only valid for ratios 0.5<l/d<4.5')
    if (Lc>=0.5) and (Lc<1.0):
        Lmin=0.5; Lmax=1
        F_12_min=lookup_data.CylRec_05([ Nc, Zc])[0]
        F_12_max=lookup_data.CylRec_1([Nc,Zc])[0]
    if (Lc>=1.0) and (Lc<1.5):
        Lmin=1; Lmax=1.5
        F_12_min=lookup_data.CylRec_1([ Nc, Zc])[0]
        F_12_max=lookup_data.CylRec_15([Nc,Zc])[0]
    if (Lc>=1.5) and (Lc<2.5):
        Lmin=1.5 ;Lmax=2.5
        F_12_min=lookup_data.CylRec_15([ Nc, Zc])[0]
        F_12_max=lookup_data.CylRec_25([Nc,Zc])[0]
    if (Lc>=2.5) and (Lc<3.5):
        Lmin=2.5 ; Lmax=3.5
        F_12_min=lookup_data.CylRec_25([ Nc, Zc])[0]
        F_12_max=lookup_data.CylRec_35([Nc,Zc])[0]
    if (Lc>=3.5) and (Lc<=4.5):
        Lmin=3.5 ; Lmax=4.5
        F_12_min=lookup_data.CylRec_35([ Nc, Zc])[0]
        F_12_max=lookup_data.CylRec_45([Nc,Zc])[0]
    f3d_15=(F_12_max-F_12_min)/(Lmax-Lmin)*(Lc-Lmin)+F_12_min
    return f3d_15
    
    
def f3d_16(r,h):
    """
    Function f3d_16(r, h) returns the view factor between a sphere (surface 1) located on a line that is normal to the center of a disk (surface 2).

    Parameters
    ----------
    r : float
        radius of the disk
    h : float
        distance between the center of the sphere and the center of the disk

    """
    f3d_16=1/2*(1-1/sqrt(1+(r/h)**2))
    return f3d_16
    
def f3d_17(r,h):
    """
    returns the view factor between the base of a right circular cylinder (surface 1) to the inside surface of a cylinder (surface 2).

    Parameters
    ----------
    r : float
        radius of the cylinder
    h : float
        height of the cylinder
    """
    BH=h/(2*r)
    f3d_17=2*BH*(sqrt(1+BH**2)-BH)
    return f3d_17
    
def f3d_18(r,h):
    """
    Function f3d_18(r, h) returns the view factor between the inner surface of a right circular cylinder (surface 1) and itself.

    Parameters
    ----------
    r : float
        radius of the cylinder
    h : float
        height of the cylinder
    """
    BH=h/(2*r)
    f3d_18=1+BH-sqrt(1+BH**2)
    return f3d_18
    
def f3d_19(r_1, r_2,h):
    """
    Function f3d_19(r_1, r_2, h) returns the view factor between an annular right at the base (or top)  of a right circular cylinder (surface 1) to the inside surface of a cylinder (surface 2).

    If r_1=0, use function f3d_17.

    Reference:  Howell  http://www.me.utexas.edu/~howell/sectionc/C-83.html

    Parameters
    ----------
    r_1 : float
        inner radius of the annular ring
    r_2 : float
        radius of the cylinder
    h : float
        height of the cylinder
    """
    if (r_1>r_2): 
        R=r_1
        r_1=r_2
        r_2=R
    R=r_2/r_1
    if (R<=1): R=1.00000001
    H=h/r_1
    f3d_19=0.5*(1+1/(R**2-1)*(H*sqrt(4*R**2+H**2)-sqrt((1+R**2+H**2)**2-4*R**2)))
    return f3d_19
    
def f3d_20(a,b,c):
    """
    The F3D_20 function returns the view factor between two finite  parallel square planes of different edge length.
    This is a variation of F3D_14

    Parameters
    ----------
    a : float
        edge length for surface 1
    b : float
        edge length for surface 2
    c : float
        distance between them.
    """
    
    if (a<=0): __warning(f'Function value a outside of range, has value {a}')
    if (b<=0): __warning(f'Function value b outside of range, has value {b}')
    if (c<=0): __warning(f'Function value c outside of range, has value {c}')
    # //f3d_20=f3d_14(0,a,0,b,0,a,0,b,c)
    s=(a-b)/2
    f3d_20=f3d_14([0,a],[0,a],[s,b+s],[s,b+s],c)
    return f3d_20
    
def f3d_21(a,b,c,r,N):
    """
    The F3D_21 function returns the view factor between rectangle (surface 1) and a disk (surface 2) that is in a parallel plane.  The centers of the disk and rectangle coincide.
    
    Parameters
    ----------
    a : float
        length of the rectangle
    b : float
        of the rectangle 
    c : float
        distance between them.
    r : float
        radius of the disk
    N : float
        number of rays to use in the Monte Carlo approximation.  Set to 0 for the default.
    """
    if (N<10): 
        NN=2000 
    else: 
        NN=N
    if (a<=0): __warning(f'Function value a outside of range, has value {a}')
    if (b<=0): __warning(f'Function value b outside of range, has value {b}')
    if (c<=0): __warning(f'Function value c outside of range, has value {c}')
    # f3d_21=f3d_21mc(a,b,c,r,NN)    "implemented in Delphi external function for speed"
    Hit=0        #initialize number of hits
    ict=0        #counter
    while(ict<NN+1):
        ict=ict+1
        x=__uniform(0,1)*b    #randomly select a value of x
        y=__uniform(0,1)*a    #     and y
        P_theta=__uniform(0,1)    #random select the polar angle from the distribution
        sintheta=sqrt(P_theta)
        theta=arcsin(sintheta)
        P_phi=__uniform(0,1)    #random select the azimuthal angle from the distribution
        phi=P_phi*2*pi
        x_i=c*tan(theta)*cos(phi)+x    #determine the intersection of the random ray with the plane for surface 2
        y_i=c*tan(theta)*sin(phi)+y
        x_c=b/2
        y_c=a/2    #test to see if the intersection point is within surface 2
        if ((x_i-x_c)**2+(y_i-y_c)**2<r**2): Hit=Hit+1
    # until (ict>NN)    "repeat N times"
    F3D_21=Hit/ict    #fraction of the total rays that strike surface 2
    return F3D_21
    
def f3d_22(r_1,r_2,s):
    """
    The F3D_22 function returns the view factor between a smaller sphere 1 and a larger sphere 2.  
    Parameters
    ----------
    r_1 : float
        radius of the smaller sphere 1 
    r_2 : float
        radius of the larger sphere 2
    s : float
        distance between the center of the two spheres
    Reference:  Howell  http://www.me.utexas.edu/~howell/sectionc/C-137.html
    """
    if (r_1<=0): __warning(f'Function value r_1 outside of range, has value {r_1}')
    if (r_2<=0): __warning(f'Function value r_2 outside of range, has value {r_2}')
    if (r_2<r_1): __warning('Function F3D_22 is only valid if r_1 < r_2')
    if (s<=(r_1+r_2)): __warning(f'Function value s outside of range, has value {s}')
    ss=s-r_1-r_2
    SN=ss/r_2
    RN=r_1/r_2
    f3d_22=(1-sqrt(1-1/(SN+RN+1)**2))/2
    return f3d_22
    
def f3d_23(l,d,y,r1,r2):
    """
    The F3D_23 function returns the view factor between a smaller cylinder 1 and a larger cylinder 2.  Cylinder 1 is completely outside of cylinder 2  

    Reference:  Howell  http://www.me.utexas.edu/~howell/sectionc/C-98.html

    Parameters
    ----------
    l : float
        length of cylinder 1
    d : float
        distance between the ends of the cylinder
    y : float
        length of cylinder 2
    r1 : float
        radius of the smaller cylinder 1 
    r2 : float
        radius of the larger cylinder 2
    """
    if (r1<=0): __warning(f'Function value r1 outside of range, has value {r1}')
    if (r2<=0): __warning(f'Function value r2 outside of range, has value {r2}')
    if (r2<r1): __warning('Function F3D_23 is only valid if r1 < r2')
    if (l<0): __warning(f'Function value l outside of range, has value {l}')
    if (d<0): __warning(f'Function value d outside of range, has value {d}')
    if (y<0): __warning(f'Function value y outside of range, has value {y}')
    DN=d/r2
    YN=y/r2
    LN=l/r2
    RN=r1/r2
    eD=DN
    AD=eD**2+RN**2-1
    BD=eD**2-RN**2+1
    FD=BD/(8*RN*eD)+(1/(2*pi))*(arccos(AD/BD)-(1/(2*eD))*sqrt((AD+2)**2/RN**2-4)*arccos(AD*RN/BD)-AD*arcsin(RN)/(2*eD*RN))
    eLpD=LN+DN
    ALpD=eLpD**2+RN**2-1
    BLpD=eLpD**2-RN**2+1
    FLpD=BLpD/(8*RN*eLpD)+(1/(2*pi))*(arccos(ALpD/BLpD)-(1/(2*eLpD))*sqrt((ALpD+2)**2/RN**2-4)*arccos(ALpD*RN/BLpD)-ALpD*arcsin(RN)/(2*eLpD*RN))
    eYpD=YN+DN
    AYpD=eYpD**2+RN**2-1
    BYpD=eYpD**2-RN**2+1
    FYpD=BYpD/(8*RN*eYpD)+(1/(2*pi))*(arccos(AYpD/BYpD)-(1/(2*eYpD))*sqrt((AYpD+2)**2/RN**2-4)*arccos(AYpD*RN/BYpD)-AYpD*arcsin(RN)/(2*eYpD*RN))
    eLpDpY=LN+DN+YN
    ALpDpY=eLpDpY**2+RN**2-1
    BLpDpY=eLpDpY**2-RN**2+1
    FLpDpY=BLpDpY/(8*RN*eLpDpY)+(1/(2*pi))*(arccos(ALpDpY/BLpDpY)-(1/(2*eLpDpY))*sqrt((ALpDpY+2)**2/RN**2-4)*arccos(ALpDpY*RN/BLpDpY)-ALpDpY*arcsin(RN)/(2*eLpDpY*RN))
    f3d_23=(LN+DN)*FLpD/LN+(YN+DN)*FYpD/LN-DN*FD/LN-(LN+DN+YN)*FLpDpY/LN
    return f3d_23
    
def f3d_24(x,y,z,r1,r2):
    """
    F3D_24 
    The F3D_24 function returns the view factor between a smaller cylinder 1 and a larger cylinder 2.
    Both ends of cylinder 1 extend outside of cylinder 2  

    Parameters
    ----------
    x : float
        distance that cylinder 1 extends beyond cylinder 2 on the left 
    y : float
        length of cylinder 2
    z : float
        distance that cylinder 1 extends beyond cylinder 2 on the right
    r1 : float
        radius of the smaller cylinder 1 
    r2 : float
        radius of the larger cylinder 2
    Reference:  Howell  http://www.me.utexas.edu/~howell/sectionc/C-97.html
    """
    if (r1<=0): __warning(f'Function value r1 outside of range, has value {r1}')
    if (r2<=0): __warning(f'Function value r2 outside of range, has value {r2}')
    if (r2<r1): __warning('Function F3D_24 is only valid if r1 < r2')
    if (x<0): __warning(f'Function value x outside of range, has value {x}')
    if (y<0): __warning(f'Function value y outside of range, has value {y}')
    if (z<0): __warning(f'Function value z outside of range, has value {z}')
    l=x+y+z
    XN=x/r2
    YN=y/r2
    ZN=z/r2
    LN=l/r2
    RN=r1/r2
    eX=XN
    AX=eX**2+RN**2-1
    BX=eX**2-RN**2+1
    FX=BX/(8*RN*eX)+(1/(2*pi))*(arccos(AX/BX)-(1/(2*eX))*sqrt((AX+2)**2/RN**2-4)*arccos(AX*RN/BX)-AX*arcsin(RN)/(2*eX*RN))
    eZ=ZN
    AZ=eZ**2+RN**2-1
    BZ=eZ**2-RN**2+1
    FZ=BZ/(8*RN*eZ)+(1/(2*pi))*(arccos(AZ/BZ)-(1/(2*eZ))*sqrt((AZ+2)**2/RN**2-4)*arccos(AZ*RN/BZ)-AZ*arcsin(RN)/(2*eZ*RN))
    eXpY=XN+YN
    AXpY=eXpY**2+RN**2-1
    BXpY=eXpY**2-RN**2+1
    FXpY=BXpY/(8*RN*eXpY)+(1/(2*pi))*(arccos(AXpY/BXpY)-(1/(2*eXpY))*sqrt((AXpY+2)**2/RN**2-4)*arccos(AXpY*RN/BXpY)-AXpY*arcsin(RN)/(2*eXpY*RN))
    eYpZ=YN+ZN
    AYpZ=eYpZ**2+RN**2-1
    BYpZ=eYpZ**2-RN**2+1
    FYpZ=BYpZ/(8*RN*eYpZ)+(1/(2*pi))*(arccos(AYpZ/BYpZ)-(1/(2*eYpZ))*sqrt((AYpZ+2)**2/RN**2-4)*arccos(AYpZ*RN/BYpZ)-AYpZ*arcsin(RN)/(2*eYpZ*RN))
    f3d_24=YN/LN+XN*FX/LN+ZN*FZ/LN-(XN+YN)*FXpY/LN-(ZN+YN)*FYpZ/LN
    return f3d_24
    
def f3d_25(x,y,l,r1,r2):
    """
    F3D_25 
    The F3D_25 function returns the view factor between a smaller cylinder 1 and a larger cylinder 2.  Cylinder 1 extends beyond one side of cylinder 2.  

    Reference:  Howell  http://www.me.utexas.edu/~howell/sectionc/C-96.html

    Parameters
    ----------
    x : float
        distance that cylinder 1 extends beyond cylinder 2 on the left
    y : float
        length of cylinder 2
    l : float
        length of cylinder 1
    r1 : float
        radius of the smaller cylinder 1 
    r2 : float
        radius of the larger cylinder 2
    """
    if (r1<=0): __warning(f'Function value r1 outside of range, has value {r1}')
    if (r2<=0): __warning(f'Function value r2 outside of range, has value {r2}')
    if (r2<r1): __warning('Function F3D_25 is only valid if r1 < r2')
    if (x<0): __warning(f'Function value x outside of range, has value {x}')
    if (y<0): __warning(f'Function value y outside of range, has value {y}')
    if (l<0): __warning(f'Function value l outside of range, has value {l}')
    if (l<x): __warning('Function F3D_25 is only valid if cylinder 1 is within cylinder 2 so l must be < x')
    XN=x/r2
    YN=y/r2
    LN=l/r2
    RN=r1/r2
    eX=XN
    AX=eX**2+RN**2-1
    BX=eX**2-RN**2+1
    FX=BX/(8*RN*eX)+(1/(2*pi))*(arccos(AX/BX)-(1/(2*eX))*sqrt((AX+2)**2/RN**2-4)*arccos(AX*RN/BX)-AX*arcsin(RN)/(2*eX*RN))
    eLmX=LN-XN
    ALmX=eLmX**2+RN**2-1
    BLmX=eLmX**2-RN**2+1
    FLmX=BLmX/(8*RN*eLmX)+(1/(2*pi))*(arccos(ALmX/BLmX)-(1/(2*eLmX))*sqrt((ALmX+2)**2/RN**2-4)*arccos(ALmX*RN/BLmX)-ALmX*arcsin(RN)/(2*eLmX*RN))
    eYpXmL=YN+XN-LN
    AYpXmL=eYpXmL**2+RN**2-1
    BYpXmL=eYpXmL**2-RN**2+1
    FYpXmL=BYpXmL/(8*RN*eYpXmL)+(1/(2*pi))*(arccos(AYpXmL/BYpXmL)-(1/(2*eYpXmL))*sqrt((AYpXmL+2)**2/RN**2-4)*arccos(AYpXmL*RN/BYpXmL)-AYpXmL*arcsin(RN)/(2*eYpXmL*RN))
    eXpY=XN+YN
    AXpY=eXpY**2+RN**2-1
    BXpY=eXpY**2-RN**2+1
    FXpY=BXpY/(8*RN*eXpY)+(1/(2*pi))*(arccos(AXpY/BXpY)-(1/(2*eXpY))*sqrt((AXpY+2)**2/RN**2-4)*arccos(AXpY*RN/BXpY)-AXpY*arcsin(RN)/(2*eXpY*RN))
    f3d_25=XN*FX/LN+(LN-XN)*(1-FLmX)/LN+(YN+XN-LN)*FYpXmL/LN-(XN+YN)*FXpY/LN
    return f3d_25
    
def f3d_26(x,l,z,r1,r2):
    """
    F3D_26 
    The F3D_26 function returns the view factor between a smaller cylinder 1 and a larger cylinder 2. Cylinder 1 is completely within cylinder 2.  

    Parameters
    ----------
    x : float
        distance from the left side of cylinder 1 and the end of cylinder 2([m] or [ft])
    l : float
        length of cylinder 1([m] or [ft])
    z : float
        distance from the right side of cylinder 1 and the end of cylinder 2([m] or [ft])
    r1 : float
        radius of the smaller cylinder 1([m] or [ft]) 
    r2 : float
        radius of the larger cylinder 2([m] or [ft])
    Reference:  Howell  http://www.me.utexas.edu/~howell/sectionc/C-95.html
    """
    if (r1<=0): __warning(f'Function value r1 outside of range, has value {r1}')
    if (r2<=0): __warning(f'Function value r2 outside of range, has value {r2}')
    if (r2<r1): __warning('Function F3D_26 is only valid if r1 < r2')
    if (x<0): __warning(f'Function value x outside of range, has value {x}')
    if (l<=0): __warning(f'Function value l outside of range, has value {l}')
    if (z<0): __warning(f'Function value z outside of range, has value {z}')
    DtoR=1 # not using
    if (x == 0): x=l/1e6
    if (z == 0): z=l/1e6
    XN=x/r2
    ZN=z/r2
    LN=l/r2
    RN=r1/r2
    eX=XN
    AX=eX**2+RN**2-1
    BX=eX**2-RN**2+1
    FX=BX/(8*RN*eX)+(1/(2*pi))*(arccos(AX/BX)-(1/(2*eX))*sqrt((AX+2)**2/RN**2-4)*arccos(AX*RN/BX)-AX*arcsin(RN)/(2*eX*RN))
    eZ=ZN
    AZ=eZ**2+RN**2-1
    BZ=eZ**2-RN**2+1
    FZ=BZ/(8*RN*eZ)+(1/(2*pi))*(arccos(AZ/BZ)-(1/(2*eZ))*sqrt((AZ+2)**2/RN**2-4)*arccos(AZ*RN/BZ)-AZ*arcsin(RN)/(2*eZ*RN))
    eLpX=LN+XN
    ALpX=eLpX**2+RN**2-1
    BLpX=eLpX**2-RN**2+1
    FLpX=BLpX/(8*RN*eLpX)+(1/(2*pi))*(arccos(ALpX/BLpX)-(1/(2*eLpX))*sqrt((ALpX+2)**2/RN**2-4)*arccos(ALpX*RN/BLpX)-ALpX*arcsin(RN)/(2*eLpX*RN))
    eLpZ=LN+ZN
    ALpZ=eLpZ**2+RN**2-1
    BLpZ=eLpZ**2-RN**2+1
    FLpZ=BLpZ/(8*RN*eLpZ)+(1/(2*pi))*(arccos(ALpZ/BLpZ)-(1/(2*eLpZ))*sqrt((ALpZ+2)**2/RN**2-4)*arccos(ALpZ*RN/BLpZ)-ALpZ*arcsin(RN)/(2*eLpZ*RN))
    f3d_26=1+XN*FX/LN+ZN*FZ/LN-(LN+XN)*FLpX/LN-(LN+ZN)*FLpZ/LN
    return f3d_26
    
def f3d_27(tau):
    """
    F3D_27 
    The F3D_27 function returns the view factor between the upper surface of a finite rectangle tilted relative to an infinite plane.  

    Reference:  Howell  http://www.me.utexas.edu/~howell/sectionc/C-9.html

    Parameters
    ----------
    tau : float
        tilt angle between the rectangle and the plane (units of radians)
    """
    if (tau<0): __warning('Function F3D_27 is only valid if tau>=0')
    f3d_27=(1-cos(tau))/2
    return f3d_27
    
def __sf3d_28(a_2,b_2,H,PHI):
    
    B = a_2/H
    A = b_2/H
    C = A**2+B**2-2*A*B*cos(PHI)
    D = (1+A**2*(sin(PHI))**2 )**(1/2)
    
    def integrand(xi):
        return sqrt(1+xi**2*(sin(PHI))**2)*(arctan((xi*cos(PHI))/sqrt(1+xi**2*(sin(PHI))**2))+arctan((A-xi*cos(PHI))/sqrt(1+xi**2*(sin(PHI))**2)))
    
    intF_1_2 = __integrate.quad(integrand,0,B)[0]

    F_1_2 = - sin(2*PHI)/(4*pi*B)*(A*B*sin(PHI)+(pi/2-PHI)*(A**2+B**2)+B**2*arctan((A-B*cos(PHI))/(B*sin(PHI)))+A**2*arctan((B-A*cos(PHI))/(A*sin(PHI)))) \
        +(sin(PHI))**2/(4*pi*B)*((2/(sin(PHI))**2-1)*log(((1+A**2)*(1+B**2))/(1+C))+B**2*log((B**2*(1+C))/((1+B**2)*C))+A**2*log((A**2*(1+A**2)**(cos(2*PHI)))/(C*(1+C)**(cos(2*PHI))))) \
        +1/pi*arctan(1/B)+A/(pi*B)*arctan(1/A)-sqrt(C)/(pi*B)*arctan(1/sqrt(C)) \
        +sin(PHI)*sin(2*PHI)/(2*pi*B)*A*D*(arctan(A*cos(PHI)/D)+arctan((B-A*cos(PHI))/D)) \
        +cos(PHI)/(pi*B)*intF_1_2
    return F_1_2
    
def f3d_28(a_2,b_2,H,theta):
    """
    This function returns the view factor from area1 to area 2 of two finite rectangles of the same length, having one common edge and having an angle of theta to each other where theta can be any angle.
    
    Parameters
    ----------
    a  : float
        height of area 1 
    b : float
        height of area 2 
    c=length of common edge
    Note: The input values have to be greater than 0!
    http://www.me.utexas.edu/~howell/sectionc/C-16.html.
    """
    F_12 = __sf3d_28(a_2,b_2,H,theta)
    return F_12
    
def f3d_29(a_1,a_2,b_1,b_2,H,phi):
    """
    This function returns the view factor from area1 to area 4 of two finite rectangles of the same length in different planes that have an angle of phi to each other.  See the figure for the geometry
    This function uses F3D_28 and view factor relations
    
    Parameters
    ----------
    a_1  : float
        height of area 1 
    a_2  : float
        height of area 1 
    b_1 : float
        height of area 3 
    b_4 : float
        height of area 3 
    h : float
        length of common edge
    phi : float
        angle between the planes
    """
    Area1 = a_2*H
    Area2 = a_1*H
    Area3 = b_1*H
    Area4 = b_2*H
    F_2_3 = f3d_28(a_1,b_1,H,phi)
    F_2_34 = f3d_28(a_1,b_1+b_2,H,phi)
    F_12_34 = f3d_28(a_1+a_2,b_1+b_2,H,phi)
    F_12_3 = f3d_28(a_1+a_2,b_1,H,phi)
    F_4_1 = (Area1+Area2)/Area4*(F_12_34-F_12_3) - Area2/Area4*(F_2_34-F_2_3)
    F_1_4 = (Area1+Area2)/Area1*(F_12_34-F_12_3) - Area2/Area1*(F_2_34-F_2_3)
    f3d_29=F_1_4
    return f3d_29
    
# "Function with Subprogram to calculate the G variable for the F3D_30 program"
def __calg(x,y,eta,xi_1,xi_2,theta):
    def integrand(xi):
        return ((x-xi*cos(theta))*cos(theta)-xi*(sin(theta))**2)/((x**2-2*x*xi*cos(theta)+xi**2)**(1/2)*(sin(theta))**2)*arctan((eta-y)/(x**2-2*x*xi*cos(theta)+xi**2)**(1/2)) \
        + cos(theta)/((eta-y)*(sin(theta))**2)*((xi**2*(sin(theta))**2+(eta-y)**2)**(1/2)*arctan((x-xi*cos(theta))/(xi**2*(sin(theta))**2+(eta-y)**2)**(1/2))-xi*sin(theta)*arctan((x-xi*cos(theta))/(1*sin(theta)))) \
                    + xi/(2*(eta-y))*log((x**2-2*x*xi*cos(theta)+xi**2+(eta-y)**2)/(x**2-2*x*xi*cos(theta)+xi**2))
    
    integratedG = __integrate.quad(integrand,xi_1,xi_2)[0]
    G = - (eta-y)*(sin(theta))**2/(2*pi)*integratedG
    return G

def  __g3d30(x,y,eta,xi_1,xi_2,alpha):
    if y==eta:
        y = y + 1e-06
    if (x==0) and (xi_1==0):
        x = 1e-06
    return __calg(x,y,eta,xi_1,xi_2,alpha)
    
def f3d_30(x_1,x_2,y_1,y_2,eta_1,eta_2,z_1,z_2,theta):
    """
    Function for calculating the view factor for rectangles with parallel and perpendicular edges and with an arbitrary angle theta between their intersecting planes, the rectangles can't be flush in the direction of the intersection line. "
    Reference: http://www.me.utexas.edu/~howell/sectionc/C-17.html.
    """
    G_1_1_1 = __g3d30(x_1,y_1,eta_1,z_1,z_2,theta)
    G_1_1_2 = __g3d30(x_1,y_1,eta_2,z_1,z_2,theta)
    G_1_2_1 = __g3d30(x_1,y_2,eta_1,z_1,z_2,theta)
    G_1_2_2 = __g3d30(x_1,y_2,eta_2,z_1,z_2,theta)
    G_2_1_1 = __g3d30(x_2,y_1,eta_1,z_1,z_2,theta)
    G_2_1_2 = __g3d30(x_2,y_1,eta_2,z_1,z_2,theta)
    G_2_2_1 = __g3d30(x_2,y_2,eta_1,z_1,z_2,theta)
    G_2_2_2 = __g3d30(x_2,y_2,eta_2,z_1,z_2,theta)
    F_1_2   =(-G_1_1_1+G_2_1_1+G_1_2_1-G_2_2_1+G_1_1_2-G_2_1_2-G_1_2_2+G_2_2_2)/((x_2-x_1)*(y_2-y_1))
    f3d_30=F_1_2
    return f3d_30
    
def f3d_31(w,h,d,k,s,N):
    """
    F3D_31 function returns the view factor between a rectangle (surface 1) and a cylinder (surface 2), which includes both ends of the cylinder. The cylinder must be parallel to the rectangle and centered in both the x and y-direction. 

    Parameters
    ----------
    w : float
        width of the rectangle
    h : float
        length of the rectangle
    d : float
        diameter of the cylinder
    k : float
        length of the cylinder 
    s : float
        distance between the center of the cylinder and the rectangle surface
    N : float
        number of rays to use in the Monte Carlo approximation. Set to 0 for the default.
    """
    NN=N
    if (NN<10): NN=100000
    if(w<=0): __warning('w must be >0')
    if(h<=0): __warning('h must be >0')
    if(d<=0): __warning('d must be >0')
    if(k<=0): __warning('k must be >0')
    if(s<d/2): __warning('s must be >d/2')    # cylinder is too close to plate- although this may work
    if(((h-k)/2)<0): __warning('(h-k)/2 must be >0')    # error when cylinder is longer than plate
    if(d>w): __warning(f'Function value d2 outside of range, has value {d}')    # cylinder diameter is too large
    # f3d_31=f3d_31mc(w,h,d,k,s,NN)    # implemented in Delphi external function for speed
    hit=0             # initialize number of hits
    ict=0             # counter
    while(ict < N+1):
        ict=ict+1
        x=__uniform(0,1)*w    # randomly select an x-location to start at
        y=__uniform(0,1)*h     # randomly select a y-location to start at
        P_theta=__uniform(0,1)     # randomly select the polar angle from the distribution
        sintheta=sqrt(P_theta)
        theta=arcsin(sintheta)
        P_phi=__uniform(0,1)     # randomly select the azimuthal angle from the distribution
        phi=P_phi*2*pi
        dL=d/10        # incremental length segment
        L=((s-d/2)-dL)    # initial length of the ray
        done=0        # condition for terminating repeat loop
        finish=0
        escape=0
        while(True):
            L=L+dL    # increase the length segment
            x_i=x+L*cos(phi)*sin(theta)    # x-location of the end of the ray
            y_i=y+L*sin(phi)*sin(theta)    # y-location of the end of the ray
            z_i=L*cos(theta)    # z-location of the end of the ray
            if (y_i>=((h-k)/2)) and (y_i<=(((h-k)/2)+k)) and (sqrt((x_i-0.5*w)**2+(z_i-s)**2)<=0.5*d): 
                hit=hit+1 
                done=1
            if (y_i<0) or (y_i>h) or (x_i<0) or (x_i>w) or (z_i<0) or (z_i>s+d/2):
                finish=1
            else:
                escape=0

            if ((done==1) or (finish==1)):
                break
    # until (ict>N)
    F3D_31=hit/ict
    return F3D_31
    
def f3d_32(w,h,d,k,s_f,s_b,N):
    """
    F3D_32 function returns the view factor between two equal sized rectangular surfaces with a circular cylinder placed between them. The circular cylinder must be of equal or lesser length (y-direction) than the flat plates and centered in both the x- and y-direction. 

    Parameters
    ----------
    w : float
        width of the rectangles 
    h : float
        length of the rectangles
    d : float
        diameter of the cylinder
    k : float
        length of the cylinder'
    s_f : float
        distance between the center of the cylinder and rectangular surface 1
    s_b : float
        distance between the center of the cylinder and rectangular surface 2
    N : float
        number of rays to use in the Monte Carlo approximation. Set to 0 for the default.
    """
    NN=N
    if (NN<10): NN=100000
    if(N<1000): __warning('N must be greater than 1000')
    if(w<=0): __warning('w must be >0')
    if(h<=0): __warning('h must be >0')
    if(d<=0): __warning('d must be >0')
    if(k<=0): __warning('k must be >0')
    if(s_f<d/2): __warning('s_f must be >d/2')
    if(s_b<d/2): __warning('s_b must be >d/2')
    if(((h-k)/2)<0): __warning('(h-k)/2 must be >0' )
    if(d>w): __warning('d must be <w') 
    # f3d_32=f3d_32mc(w,h,d,k,s_f,s_b,NN)    # implemented in Delphi external function for speed
    hit=0                # initialize the number of hits
    ict=0                # ray counter
    while(ict <= N+1):
        ict=ict+1
        x=__uniform(0,1)*w    # randomly select an x-location to start at
        y=__uniform(0,1)*h     # randomly select a y-location to start at
        P_theta=__uniform(0,1)     # randomly select the polar angle from the distribution
        sintheta=sqrt(P_theta)
        theta=arcsin(sintheta)
        P_phi=__uniform(0,1)     # randomly select the azimuthal angle from the distribution
        phi=P_phi*2*pi
        dL=d/10        # incremental length segment
        L=((s_f-d/2)-dL)    # initial length of the ray
        done=0        # condition for terminating repeat loop
        finish=0
        escape=0
        while(True):
            L=L+dL    # increase the length segment
            x_i=x+L*cos(phi)*sin(theta)    # x-location of the end of the ray
            y_i=y+L*sin(phi)*sin(theta)    # y-location of the end of the ray
            z_i=L*cos(theta)    # z-location of the end of the ray
            if (y_i>=((h-k)/2)) and (y_i<=(((h-k)/2)+k)) and (sqrt((x_i-0.5*w)**2+(z_i-s_f)**2)<=0.5*d):  
                done=1
            if (y_i<0) or (y_i>h) or (x_i<0) or (x_i>w) or (z_i<0) or (z_i>s_f+d/2):
                finish=1
            else:
                escape=0
            if ((done==1) or (finish==1)): break
        while(True):
            L=(s_f+s_b)/cos(theta)
            x_i=x+L*cos(phi)*sin(theta)
            y_i=y+L*sin(phi)*sin(theta)
            if (finish==1) and (y_i>0) and (y_i<h) and (x_i>0) and (x_i<w):
                hit=hit+1
                escape=1
            else:
                escape=1
            if((escape==1)): break
    # until (ict>N)
    F3D_32=hit/ict
    return F3D_32
    
def f3d_33(R,B,L):
    """
    This function returns the view factor from a rectangle to a disk that lies in a perpendicular plane.  The disc is centered and touches one side as shown in the figure.
    
    Parameters
    ----------
    R  : float
        radius of disk
    B : float
        width of rectangle perpendicular to disk
    L : float
        length of rectangle parallel to disk
    """
    
    if(R<0): __warning('R must be greater than 0 in F3D_33')
    if(B<0): __warning('B must be greater than 0 in F3D_33')
    if(L<0): __warning('L must be greater than 0 in F3D_33')
    
    LND=L/R
    BND=B/R
    if(LND<=0.1): __warning('L/R must be greater than 0.1 in F3D_33')
    if(LND>=10): __warning('L/R must be less than 10 in F3D_33')
    if(BND<=0.1): __warning('B/R must be greater than 0.1 in F3D_33')
    if(BND>=10): __warning('B/R must be less than 10 in F3D_33')
    
    Num=0.5974*(0.5*LND+LND**2)**0.4976*(0.05*BND+BND**2)**0.2091+0.5974*(0.1*BND*LND+(BND*LND)**2)**0.0613
    Den=(LND+LND**4)**0.4685+(BND+BND**4)**0.30775+(BND*LND+(BND*LND)**2)**0.7457
    
    f3d_33=Num/Den
    return f3d_33
    
def f3d_34(x_1,x_2,s,b,d):
    """
    This function returns the view factor from the interior of two rectangular encosures that are aligned as shown in the figure.
    
    Parameters
    ----------
    x_1 : float
        width of enclosure 1
    x_2 : float
        width of enclosure 2
    s : float
        gap between enclosures
    b : float
        dimensions of enclosure as viewed along axis joining enclosures
    d : float
        dimensions of enclosure as viewed along axis joining enclosures
    """
    
    if(x_1<0): __warning('x_1 must be greater than 0 in F3D_34')
    if(x_2<0): __warning('x_2 must be greater than 0 in F3D_34')
    if(s<0): __warning('s must be greater than 0 in F3D_34')
    if(b<0): __warning('b must be greater than 0 in F3D_34')
    if(d<0): __warning('d must be greater than 0 in F3D_34')
    
    BND=b/d
    SND=s/d
    X1ND=x_1/d
    X2ND=x_2/d
    
    f3d_34=(__g3d34(BND,SND+X1ND+X2ND)-__g3d34(BND,SND+X1ND)+__g3d34(BND,SND)-__g3d34(BND,SND+X2ND))/(pi*(BND+1)*X1ND)
    return f3d_34
    
def  __g3d34(BND,Z):
    res=BND*sqrt(Z**2+1)*arctan(BND/sqrt(Z**2+1))-BND*Z*arctan(BND/Z)+sqrt(Z**2+BND**2)*arctan(1/sqrt(Z**2+BND**2))
    res=res-Z*arctan(1/Z)+(Z**2/2)*log((Z**2+BND**2)*(Z**2+1)/(Z**2*(Z**2+BND**2+1)))
    return  res
    
def f3d_35(r_1,r_2,L,s):
    """
    This function returns the view factor between two finite length parallel cylinders.
    
    Parameters
    ----------
    r_1 : float
        radius of cylinder 1
    r_2 : float
        radius of cylinder 2
    L : float
        length of both cylinders
    s : float
        distance between edges of cylinders
    """
    
    if(r_1<0): __warning('r_1 must be greater than 0 in F3D_35')
    if(r_2<0): __warning('r_2 must be greater than 0 in F3D_35')
    if(L<0): __warning('L must be greater than 0 in F3D_35')
    if(s<0): __warning('s must be greater than 0 in F3D_35')
    
    c=s+r_1+r_2    # center to center distance
    F_12_infinity=(sqrt((c/r_1)**2-(r_2/r_1+1)**2)-sqrt((c/r_1)**2-(r_2/r_1-1)**2)+pi+(r_2/r_1-1)*arccos((r_2-r_1)/c)-(r_2/r_1+1)*arccos((r_2+r_1)/c))/(2*pi)
    # infinite cylinder solution
    R0=r_2*sqrt((2*sqrt((c/r_2)**2-1)-pi)/(2*arcsin(r_2/c))+1)
    CND=(L/r_2)**2-(R0/r_2)**2+(r_1/r_2)**2
    BND=(L/r_2)**2+(R0/r_2)**2-(r_1/r_2)**2
    T1=sqrt((CND+2*(R0/r_2)**2)**2-(2*R0/r_2*r_1/r_2)**2)*arccos(r_1*CND/(R0*BND))
    F_12_N=1-(1/pi)*(arccos(CND/BND)-r_2**2/(2*r_1*L)*(T1+CND*arcsin(r_1/R0)-pi*BND/2))
    f3d_35=F_12_N*F_12_infinity
    return f3d_35
    
def f3d_36(W,L,D):
    """
    This function returns the view factor between two perpendicular right triangles sharing a common base.
    
    Parameters
    ----------
    W : float
        height of triangle 2
    L : float
        height of triangle 1
    D : float
        base of both triangles
    """
    
    if(W<0): __warning('W must be greater than 0 in F3D_36')
    if(L<0): __warning('L must be greater than 0 in F3D_36')
    if(D<0): __warning('D must be greater than 0 in F3D_36')
    
    WND=W/D
    LND=L/D
    
    if(WND<0.1): __warning('W/D must be greater than 0.1 in F3D_36')
    if(LND<0.1): __warning('L/D must be greater than 0.1 in F3D_36')
    if(WND>10): __warning('W/D must be less than 10 in F3D_36')
    if(LND>10): __warning('L/D must be less than 10 in F3D_36')
    
    logW=log10(WND)
    logL=log10(LND)
    f3d_36=2.05150283E-01+1.37525885E-01*logW-5.81382217E-02*logW**2+1.84307668E-03*logW**3-2.57978714E-01*logL+1.95079034E-02*logL**2+5.49667153E-02*logL**3-2.30045593E-02*logW*logL-9.09197817E-02*logW*logL**2+5.17038809E-02*logW**2*logL+3.35538317E-02*logW**2*logL**2
    if (f3d_36<0): f3d_36=0
    
    return f3d_36
    
def f3d_37(W,L,D):
    """
    This function returns the view factor between a right triangle and a perpendicular rectangle sharing a common base
    
    Parameters
    ----------
    W : float
        height of rectangle
    L : float
        height of triangle
    D : float
        base of both surfaces
    """
    
    if(W<0): __warning('W must be greater than 0 in F3D_37')
    if(L<0): __warning('L must be greater than 0 in F3D_37')
    if(D<0): __warning('D must be greater than 0 in F3D_37')
    
    WND=W/D
    LND=L/D
    
    if(WND<0.1): __warning('W/D must be greater than 0.1 in F3D_37')
    if(LND<0.1): __warning('L/D must be greater than 0.1 in F3D_37')
    if(WND>10): __warning('W/D must be less than 10 in F3D_37')
    if(LND>10): __warning('L/D must be less than 10 in F3D_37')
    
    logW=log10(WND)
    logL=log10(LND)
    f3d_37=2.56696015E-01+1.11818175E-01*logW-7.86689176E-02*logW**2+6.36623912E-03*logW**3-2.50144540E-01*logL-1.74685885E-02*logL**2+5.45121472E-02*logL**3+7.90230489E-04*logW*logL-7.98057449E-02*logW*logL**2+2.76556078E-02*logW**2*logL+6.15874030E-02*logW**2*logL**2
    if (f3d_37<0): f3d_37=0
    
    return f3d_37
    
def f3d_38(W,L,D):
    """
    This function returns the view factor between two right triangles that are perpendicular and share a common base.  The height of the triangles are on opposite sides of the base.
    
    Parameters
    ----------
    W : float
        height of triangle 2
    L : float
        height of triangle 1
    D : float
        base of both surfaces
    """
    
    if(W<0): __warning('W must be greater than 0 in F3D_37')
    if(L<0): __warning('L must be greater than 0 in F3D_37')
    if(D<0): __warning('D must be greater than 0 in F3D_37')
    
    WND=W/D
    LND=L/D
    
    if(WND<0.1): __warning('W/D must be greater than 0.1 in F3D_38')
    if(LND<0.1): __warning('L/D must be greater than 0.1 in F3D_38')
    if(WND>10): __warning('W/D must be less than 10 in F3D_38')
    if(LND>10): __warning('L/D must be less than 10 in F3D_38')
    
    logW=log10(WND)
    logL=log10(LND)
    f3d_38=1.84171604E-01+1.59773247E-01*logW-2.04912173E-02*logW**2-3.02091664E-02*logW**3-2.24939763E-01*logL+3.81670780E-02*logL**2+3.08709779E-02*logL**3-6.10198677E-02*logW*logL-5.03960644E-02*logW*logL**2+4.84285660E-02*logW**2*logL-9.56813955E-03*logW**2*logL**2
    if (f3d_38<0): f3d_38=0
    
    return f3d_38
    
def f3d_39(W,L,D):
    """
    This function returns the view factor between a right triangle and a perpendicular rectangle.  The right triangle base is coincident with the rectangle base but half as long.  
    
    Parameters
    ----------
    W : float
        height of the rectangle
    L : float
        twice the height of triangle
    D : float
        base of rectangle (twice the base of triangle)
    """
    
    if(W<0): __warning('W must be greater than 0 in F3D_39')
    if(L<0): __warning('L must be greater than 0 in F3D_39')
    if(D<0): __warning('D must be greater than 0 in F3D_39')
    
    WND=W/D
    LND=L/D
    
    if(WND<0.1): __warning('W/D must be greater than 0.1 in F3D_39')
    if(LND<0.2): __warning('L/D must be greater than 0.2 in F3D_39')
    if(WND>10): __warning('W/D must be less than 10 in F3D_39')
    if(LND>10): __warning('L/D must be less than 10 in F3D_39')
    
    logW=log10(WND)
    logL=log10(LND)
    f3d_39=3.75941597E-01+1.15553771E-01*logW-1.02430871E-01*logW**2+1.18225392E-02*logW**3-2.84182668E-01*logL-1.07197559E-01*logL**2+1.04113326E-01*logL**3+4.40362999E-02*logW*logL-9.71192632E-02*logW*logL**2+9.44514790E-04*logW**2*logL+9.76560977E-02*logW**2*logL**2
    if (f3d_39<0): f3d_39=0
    
    return f3d_39
    
def f3d_40(W,L,D):
    """
    This function returns the view factor between a right triangle and a perpendicular rectangle.  The right triangle base is coincident with the rectangle base.  
    
    Parameters
    ----------
    W : float
        height of the rectangle
    L : float
        twice the height of triangle
    D : float
        base of rectangle and triangle
    """
    
    if(W<0): __warning('W must be greater than 0 in F3D_40')
    if(L<0): __warning('L must be greater than 0 in F3D_40')
    if(D<0): __warning('D must be greater than 0 in F3D_40')
    
    WND=W/D
    LND=L/D
    
    if(WND<0.1): __warning('W/D must be greater than 0.1 in F3D_40')
    if(LND<0.2): __warning('L/D must be greater than 0.2 in F3D_40')
    if(WND>10): __warning('W/D must be less than 10 in F3D_40')
    if(LND>10): __warning('L/D must be less than 10 in F3D_40')
    
    f3d_40=f3d_39(W,L,D)
    
    return f3d_40
    
def f3d_41(W,L,D):
    """
    This function returns the view factor between two right triangles that are perpendicular and share a base.  The base of triangle 1 is half as long as the base of triangle 2.
    
    Parameters
    ----------
    W : float
        height of triangle 2
    L : float
        twice the height of triangle 1
    D : float
        base of triangle 2 (twice the base of triangle 1)
    """
    
    if(W<0): __warning('W must be greater than 0 in F3D_41')
    if(L<0): __warning('L must be greater than 0 in F3D_41')
    if(D<0): __warning('D must be greater than 0 in F3D_41')
    
    WND=W/D
    LND=L/D
    
    if(WND<0.1): __warning('W/D must be greater than 0.1 in F3D_41')
    if(LND<0.2): __warning('L/D must be greater than 0.2 in F3D_41')
    if(WND>10): __warning('W/D must be less than 10 in F3D_41')
    if(LND>10): __warning('L/D must be less than 10 in F3D_41')
    
    logW=log10(WND)
    logL=log10(LND)
    f3d_41=2.77212471E-01+2.22598390E-01*logW-9.90756945E-02*logW**2-4.94677224E-02*logW**3+3.02887821E-02*logW**4-3.46039854E-01*logL+6.35881662E-02*logL**2+1.97548996E-01*logL**3-1.41330547E-01*logL**4-1.88298836E-02*logW*logL-1.89077048E-01*logW*logL**2+6.55217337E-02*logW*logL**3+1.42290393E-01*logW**2*logL+6.60235926E-02*logW**2*logL**2-1.22139031E-01*logW**2*logL**3-4.68340451E-02*logW**3*logL+5.50661188E-02*logW**3*logL**2+1.80244045E-02*logW**3*logL**3
    if (f3d_41<0): f3d_41=0
    
    return f3d_41
    
def f3d_42(W,L,D):
    """
    This function returns the view factor between two right triangles that are perpendicular and share a base.  The base of triangle 1 is half as long as the base of triangle 2 and oriented in the opposite manner as F3D_41.
    
    Parameters
    ----------
    W : float
        height of triangle 2
    L : float
        twice the height of triangle 1
    D : float
        base of triangle 2 (twice the base of triangle 1)
    """
    
    if(W<0): __warning('W must be greater than 0 in F3D_42')
    if(L<0): __warning('L must be greater than 0 in F3D_42')
    if(D<0): __warning('D must be greater than 0 in F3D_42')
    
    WND=W/D
    LND=L/D
    
    if(WND<0.1): __warning('W/D must be greater than 0.1 in F3D_42')
    if(LND<0.2): __warning('L/D must be greater than 0.2 in F3D_42')
    if(WND>10): __warning('W/D must be less than 10 in F3D_42')
    if(LND>10): __warning('L/D must be less than 10 in F3D_42')
    
    logW=log10(WND)
    logL=log10(LND)
    f3d_42=3.13294284E-01+1.32724286E-01*logW-9.30472140E-02*logW**2+9.94151005E-03*logW**3+1.13906611E-02*logW**4-3.28287393E-01*logL+3.99706694E-03*logL**2+1.33425597E-01*logL**3-5.84836263E-02*logL**4+6.44510805E-02*logW*logL-9.34246169E-02*logW*logL**2-3.32453243E-02*logW*logL**3+9.73917808E-02*logW**2*logL+9.63805638E-02*logW**2*logL**2-1.04480232E-01*logW**2*logL**3-9.60639976E-02*logW**3*logL-3.14846046E-02*logW**3*logL**2+9.83815518E-02*logW**3*logL**3
    if (f3d_42<0): f3d_42=0
    
    return f3d_42
    
def f3d_43(W,L,D):
    """
    This function returns the view factor between two right triangles that are perpendicular with bases that touch and are of equal length. 
    
    Parameters
    ----------
    W : float
        twice the height of triangle 2
    L : float
        twice the height of triangle 1
    D : float
        twice the base of both triangles
    """
    
    if(W<0): __warning('W must be greater than 0 in F3D_42')
    if(L<0): __warning('L must be greater than 0 in F3D_42')
    if(D<0): __warning('D must be greater than 0 in F3D_42')
    
    WND=W/D
    LND=L/D
    
    if(WND<0.1): __warning('W/D must be greater than 0.1 in F3D_43')
    if(LND<1): __warning('L/D must be greater than 1 in F3D_43')
    if(WND>10): __warning('W/D must be less than 10 in F3D_43')
    if(LND>10): __warning('L/D must be less than 10 in F3D_43')
    
    logW=log10(WND)
    logL=log10(LND)
    f3d_43=3.31499740E-02+4.39166058E-02*logW+1.06640086E-02*logW**2-1.95097662E-03*logW**3-1.55520973E-02*logL-4.33640289E-02*logL**2+3.20327801E-02*logL**3-1.37314130E-02*logW*logL-1.91277987E-02*logW*logL**2+1.79430736E-02*logW**2*logL-2.29717475E-02*logW**2*logL**2
    if (f3d_43<0): f3d_43=0
    
    return f3d_43
    
def f3d_44(c,b,theta):
    """
    This function returns the view factor between two right triangles that are parallel to one another and aligned.
    
    Parameters
    ----------
    c : float
        distance between triangles
    b : float
        base of triangles
    theta : float
        angle of triangles
    """

    # theta=theta*convert(D$,deg)
    if(b<0): __warning('b must be greater than 0 in F3D_44')
    if(c<0): __warning('c must be greater than 0 in F3D_44')
    
    CND=c/b
    
    if(CND<0.1): __warning('c/b must be greater than 0.1 in F3D_44')
    if(theta<15*__np.pi/180): __warning('theta must be greater than 45 degree in F3D_44')
    if(CND>10): __warning('c/b must be less than 10 in F3D_44')
    if(theta>90*__np.pi/180): __warning('theta must be less than 90 degree in F3D_44')
    
    theta_deg = theta*180/__np.pi

    logC=log10(CND)
    f3d_44=-1.32890797E-02+1.70807986E-03*theta_deg+6.27765706E-05*theta_deg**2-1.11141522E-06*theta_deg**3+7.12646272E-09*theta_deg**4+2.97636058E-02*logC+2.34317947E-01*logC**2-1.44258483E-01*logC**3-1.08344064E-01*logC**4-1.32181842E-02*theta_deg*logC+8.13164666E-03*theta_deg*logC**2+1.98518845E-03*theta_deg*logC**3+1.00562253E-04*theta_deg**2*logC-1.47942443E-04*theta_deg**2*logC**2+6.02804780E-05*theta_deg**2*logC**3-3.03659903E-07*theta_deg**3*logC+7.09959330E-07*theta_deg**3*logC**2-5.70309241E-07*theta_deg**3*logC**3
    
    if (f3d_44<0): f3d_44=0.
    
    return f3d_44
    
def f3d_45(a,b,c):
    """
    This function returns the view factor between two directly opposed rectangles with 30 degree triangular extensions
    
    Parameters
    ----------
    a : float
        height of rectangle
    b : float
        depth of rectangle
    c : float
        distance between rectangles
    """
    
    if(a<0): __warning('a must be greater than 0 in F3D_45')
    if(b<0): __warning('b must be greater than 0 in F3D_45')
    if(c<0): __warning('c must be greater than 0 in F3D_45')
    
    AND=a/b
    CND=c/b
    if(CND<0.2): __warning('c/b must be greater than 0.2 in F3D_45')
    if(AND<0.1): __warning('a/b must be greater than 0.1 in F3D_45')
    if(CND>5): __warning('c/b must be less than 5 in F3D_45')
    if(AND>10): __warning('a/b must be less than 10 in F3D_45')
    
    logC=log10(CND)
    logA=log10(AND)
    f3d_45=2.22861271E-01+1.99639058E-01*logA+1.74092160E-02*logA**2-5.28712316E-02*logA**3-1.83829424E-03*logA**4-5.88545286E-01*logC+3.77528465E-01*logC**2+2.19844098E-01*logC**3-2.34602038E-01*logC**4-2.41090665E-01*logA*logC-2.13687386E-01*logA*logC**2+2.70383096E-01*logA*logC**3+7.37173783E-02*logA**2*logC-8.09881875E-02*logA**2*logC**2-1.47217808E-02*logA**2*logC**3+8.14540769E-02*logA**3*logC+5.80562927E-02*logA**3*logC**2-4.05848897E-02*logA**3*logC**3
    
    if (f3d_45<0): f3d_45=0
    
    return f3d_45
    
def f3d_46(a,b,c):
    """
    This function returns the view factor between two directly opposed rectangles with 45 degree triangular extensions
    
    Parameters
    ----------
    a : float
        height of rectangle
    b : float
        depth of rectangle
    c : float
        distance between rectangles
    """
    
    if(a<0): __warning('a must be greater than 0 in F3D_46')
    if(b<0): __warning('b must be greater than 0 in F3D_46')
    if(c<0): __warning('c must be greater than 0 in F3D_46')
    
    AND=a/b
    CND=c/b
    if(CND<0.2): __warning('c/b must be greater than 0.2 in F3D_46')
    if(AND<0.1): __warning('a/b must be greater than 0.1 in F3D_46')
    if(CND>5): __warning('c/b must be less than 5 in F3D_46')
    if(AND>10): __warning('a/b must be less than 10 in F3D_46')
    
    logC=log10(CND)
    logA=log10(AND)
    f3d_46=2.43238710E-01+1.70912431E-01*logA+2.04764336E-02*logA**2-4.95406880E-02*logA**3-7.25509679E-03*logA**4-6.10178437E-01*logC+3.61009702E-01*logC**2+2.47858861E-01*logC**3-2.66445896E-01*logC**4-1.56748174E-01*logA*logC-2.00114114E-01*logA*logC**2+1.37630265E-01*logA*logC**3+4.98486588E-02*logA**2*logC-4.93571301E-02*logA**2*logC**2+2.84702994E-03*logA**2*logC**3+4.25740231E-02*logA**3*logC+6.40125604E-02*logA**3*logC**2+1.84137489E-02*logA**3*logC**3
    
    if (f3d_46<0): f3d_46=0
    
    return f3d_46
    
def f3d_47(a,b,c):
    """
    This function returns the view factor between a rectangular floor to an endwall with 30 degree triangular extensions
    
    Parameters
    ----------
    a : float
        height of endwall rectangle
    b : float
        half-width of floor rectangle
    c : float
        length of floor rectangle
    """
    
    if(a<0): __warning('a must be greater than 0 in F3D_47')
    if(b<0): __warning('b must be greater than 0 in F3D_47')
    if(c<0): __warning('c must be greater than 0 in F3D_47')
    
    AND=a/b
    CND=c/b
    if(CND<0.1): __warning('c/b must be greater than 0.1 in F3D_47')
    if(AND<0.1): __warning('a/b must be greater than 0.1 in F3D_47')
    if(CND>10): __warning('c/b must be less than 10 in F3D_47')
    if(AND>10): __warning('a/b must be less than 10 in F3D_47')
    
    logC=log10(CND)
    logA=log10(AND)
    f3d_47=2.64079239E-01+1.19106598E-01*logA-3.98630611E-02*logA**2-3.41687677E-02*logA**3+1.20675290E-02*logA**4-2.90939510E-01*logC-3.99146351E-03*logC**2+8.41698428E-02*logC**3-9.00308712E-03*logC**4+3.59114343E-02*logA*logC-9.90939133E-02*logA*logC**2-2.92119139E-02*logA*logC**3+5.22263456E-02*logA**2*logC+2.78988412E-02*logA**2*logC**2-3.94363420E-02*logA**2*logC**3-2.46095379E-02*logA**3*logC+3.92710766E-02*logA**3*logC**2+2.39003182E-02*logA**3*logC**3
    
    if (f3d_47<0): f3d_47=0
    
    return f3d_47
    
def f3d_48(a,b,c):
    """
    This function returns the view factor between a rectangular floor to an endwall with 45 degree triangular extensions
    
    Parameters
    ----------
    a : float
        height of endwall rectangle
    b : float
        half-width of floor rectangle
    c : float
        length of floor rectangle
    """
    
    if(a<0): __warning('a must be greater than 0 in F3D_48')
    if(b<0): __warning('b must be greater than 0 in F3D_48')
    if(c<0): __warning('c must be greater than 0 in F3D_48')
    
    AND=a/b
    CND=c/b
    if(CND<0.1): __warning('c/b must be greater than 0.1 in F3D_48')
    if(AND<0.1): __warning('a/b must be greater than 0.1 in F3D_48')
    if(CND>10): __warning('c/b must be less than 10 in F3D_48')
    if(AND>10): __warning('a/b must be less than 10 in F3D_48')
    
    logC=log10(CND)
    logA=log10(AND)
    f3d_48=2.70366034E-01+1.03588433E-01*logA-9.92494456E-03*logA**2-3.49962662E-02*logA**3-4.15247347E-03*logA**4-2.86058855E-01*logC-5.96880812E-03*logC**2+7.71918560E-02*logC**3-1.50627834E-02*logC**4+7.01385424E-02*logA*logC-7.41205980E-02*logA*logC**2-6.33168211E-02*logA*logC**3+4.01846263E-02*logA**2*logC+2.29669774E-02*logA**2*logC**2-2.63587674E-02*logA**2*logC**3-3.69288576E-02*logA**3*logC+3.32229727E-02*logA**3*logC**2+4.20573262E-02*logA**3*logC**3
    
    if (f3d_48<0): f3d_48=0
    
    return f3d_48
    
def f3d_49(l,h):
    """
    This function returns the view factor between one wall of a hexagonal enclosure and the adjacent wall
    
    Parameters
    ----------
    l : float
        length of wall
    h : float
        height of enclosure
    """
    
    if(l<0): __warning('l must be greater than 0 in F3D_49')
    if(h<0): __warning('h must be greater than 0 in F3D_49')
    
    LND=l/h
    if(LND<0.05): __warning('l/h must be greater than 0.05 in F3D_49')
    if(LND>20): __warning('l/h must be less than 20 in F3D_49')
    
    logL=log10(LND)
    f3d_49=0.0864018485 - 0.0738207006*logL - 0.0158496633*logL**2 + 0.0279049384*logL**3 + 0.00444143166*logL**4 - 0.00652106847*logL**5
    
    if (f3d_49<0): f3d_49=0
    
    return f3d_49
    
def f3d_50(l,h):
    """
    This function returns the view factor between one wall of a hexagonal enclosure and the wall one removed
    
    Parameters
    ----------
    l : float
        length of wall
    h : float
        height of enclosure
    """
    
    if(l<0): __warning('l must be greater than 0 in F3D_50')
    if(h<0): __warning('h must be greater than 0 in F3D_50')
    
    LND=l/h
    if(LND<0.05): __warning('l/h must be greater than 0.05 in F3D_50')
    if(LND>20): __warning('l/h must be less than 20 in F3D_50')
    
    logL=log10(LND)
    f3d_50=0.0893164311 - 0.149080196*logL + 0.0352925987*logL**2 + 0.0616386551*logL**3 - 0.0130749312*logL**4 - 0.0134928922*logL**5
    
    if (f3d_50<0): f3d_50=0
    
    return f3d_50
    
def f3d_51(l,h):
    """
    This function returns the view factor between one wall of a hexagonal enclosure and the opposite wall
    
    Parameters
    ----------
    l : float
        length of wall
    h : float
        height of enclosure
    """
    
    if(l<0): __warning('l must be greater than 0 in F3D_51')
    if(h<0): __warning('h must be greater than 0 in F3D_51')
    
    LND=l/h
    if(LND<0.05): __warning('l/h must be greater than 0.05 in F3D_51')
    if(LND>20): __warning('l/h must be less than 20 in F3D_51')
    
    logL=log10(LND)
    f3d_51=0.0901853816 - 0.162825837*logL + 0.0566119213*logL**2 + 0.0575787447*logL**3 - 0.0205544698*logL**4 - 0.0105808558*logL**5
    
    if (f3d_51<0): f3d_51=0
    
    return f3d_51
    
def f3d_52(l,h):
    """
    This function returns the view factor between two parallel regular triangles.
    
    Parameters
    ----------
    l : float
        side of triangle
    h : float
        distance between triangles
    """
    
    if(l<0): __warning('l must be greater than 0 in F3D_52')
    if(h<0): __warning('h must be greater than 0 in F3D_52')
    
    LND=l/h
    logL=log10(LND)
    if (logL<=-3): 
        f3d_52=0
    else:
        if (logL<=-1):
            f3d_52=(logL+3)*0.00002316/2
        else:
            if (logL<=1):
                f3d_52=0.220767234+0.501146052*__erf(1.60036751*(logL-0.278527905))+0.278527905*__erf(1.04974816*(logL-0.60824689)**2)
            else:
                if (logL<=3):
                    f3d_52=0.7207+(1-0.7207)*(logL-1)/2
                else:
                    f3d_52=1
    
    return f3d_52
    
def f3d_53(l,h):
    """
    This function returns the view factor between two parallel regular polygons.
    
    Parameters
    ----------
    l : float
        side of pentagon
    h : float
        distance between pentagons
    """
    
    if(l<0): __warning('l must be greater than 0 in F3D_53')
    if(h<0): __warning('h must be greater than 0 in F3D_53')
    
    LND=l/h
    logL=log10(LND)
    if (logL<=-3): 
        f3d_53=0
    else:
        if (logL<=-1):
            f3d_53=(logL+3)*0.008449/2
        else:
            if (logL<=1):
                f3d_53=0.464692284+0.46296928*__erf(1.37646492*(logL-0.255480317))
            else:
                if (logL<=3):
                    f3d_53=0.8595+(1-0.8595)*(logL-1)/2
                else:
                    f3d_53=1
    return f3d_53
    
def f3d_54(l,h):
    """
    This function returns the view factor between two parallel regular hexagons.
    
    Parameters
    ----------
    l : float
        side of hexagon
    h : float
        distance between hexagons
    """
    
    if(l<0): __warning('l must be greater than 0 in F3D_54')
    if(h<0): __warning('h must be greater than 0 in F3D_54')
    
    LND=l/h
    logL=log10(LND)
    if (logL<=-3): 
        f3d_54=0
    else:
        if (logL<=-1):
            f3d_54=(logL+3)*0.001841/2
        else:
            if (logL<=1):
                f3d_54=0.469048797+0.476380451*__erf(1.41382458*(logL-0.1706059))
            else:
                if (logL<=3):
                    f3d_54=0.8991+(1-0.8991)*(logL-1)/2
                else:
                    f3d_54=1
    
    return f3d_54
    
def f3d_55(l,h):
    """
    This function returns the view factor between two parallel regular octagons.
    
    Parameters
    ----------
    l : float
        side of octagon
    h : float
        distance between octagons
    """
    
    if(l<0): __warning('l must be greater than 0 in F3D_55')
    if(h<0): __warning('h must be greater than 0 in F3D_55')
    
    LND=l/h
    logL=log10(LND)
    if (logL<=-3): 
        f3d_55=0
    else:
        if (logL<=-1):
            f3d_55=(logL+3)*0.01641/2
        else:
            if (logL<=1):
                f3d_55=0.448998209 + 0.746896594*logL - 0.000853906882*logL**2 - 0.394617646*logL**3 + 0.0174054468*logL**4 + 0.0968595809*logL**5
            else:
                if (logL<=3):
                    f3d_55=0.9147+(1-0.9147)*(logL-1)/2
                else:
                    f3d_55=1
    
    return f3d_55
    
def f3d_56(b,c,theta):
    """
    This function returns the view factor between a rectangular floor to an endwall that is a perpendicular circular segment
    
    Parameters
    ----------
    b : float
        twice the width of the rectangular floor
    c : float
        length of the rectangular floor
    theta : float
        angle between floor and center of segment
    """

    if(b<0): __warning('b must be greater than 0 in F3D_56')
    if(c<0): __warning('c must be greater than 0 in F3D_56')
    if(theta<0): __warning('theta must be greater than 0 in F3D_56')
    if(theta>90*__np.pi/180): __warning('theta must be less than 90 in F3D_56')
    
    CND=c/b
    if(CND<0.1): __warning('c/b must be greater than 0.1 in F3D_56')
    if(CND>10): __warning('c/b must be less than 10 in F3D_56')
    
    logC=log10(CND)
    f3d_56=2.08377184E-01-1.17255833E-03*theta-4.57674222E-05*theta**2+7.28601785E-07*theta**3-4.08449621E-09*theta**4-2.95203060E-01*logC+5.15062145E-02*logC**2+8.85757500E-02*logC**3-2.36938399E-02*logC**4+9.53707055E-04*theta*logC-3.25542389E-04*theta*logC**2+8.04101295E-04*theta*logC**3+3.65214394E-06*theta**2*logC+7.33661021E-05*theta**2*logC**2-7.20250799E-05*theta**2*logC**3+2.46881417E-07*theta**3*logC-8.06883401E-07*theta**3*logC**2+5.73856834E-07*theta**3*logC**3
    
    if (f3d_56<0): f3d_56=0
    
    return f3d_56
    
def f3d_57(a,b,c,theta):
    """
    This function returns the view factor between a rectangular floor to a perpendicular endwall with a circular segment on top
    
    Parameters
    ----------
    a : float
        height of the rectangular portion of the end wall
    b : float
        half-width of the floor
    c : float
        length of the rectangular floor
    theta : float
        angle between endwall and center of segment
    """

    if(a<0): __warning('a must be greater than 0 in F3D_57')
    if(b<0): __warning('b must be greater than 0 in F3D_57')
    if(c<0): __warning('c must be greater than 0 in F3D_57')
    if(theta<0): __warning('theta must be greater than 0 in F3D_57')
    if(theta>45*__np.pi/180): __warning('theta must be less than 90 in F3D_57')
    
    CND=c/b
    if(CND<0.1): __warning('c/b must be greater than 0.1 in F3D_57')
    if(CND>10): __warning('c/b must be less than 10 in F3D_57')
    logC=log10(CND)
    
    AND=a/b
    if(AND<0.1): __warning('a/b must be greater than 0.1 in F3D_57')
    if(AND>10): __warning('a/b must be less than 10 in F3D_57')
    logA=log10(AND)
    
    f3d_57=2.83153937E-01-4.87276722E-02*theta+5.92535023E-03*theta**2-2.16186416E-04*theta**3+2.40623330E-06*theta**4+7.89787845E-02*logA-8.55760730E-03*logA**2-2.68975717E-02*logA**3-5.10404748E-04*logA**4-2.89325788E-01*logC-3.94517894E-02*logC**2+8.40645451E-02*logC**3+8.20630578E-03*logC**4+5.35899516E-04*theta*logA-3.57455956E-04*theta*logA**2+3.64623003E-04*theta*logA**3-2.30160397E-04*theta*logC+5.49564759E-04*theta*logC**2+2.80321135E-04*theta*logC**3-5.78095806E-06*theta**2*logA+1.31973754E-05*theta**2*logA**2-2.20464382E-05*theta**2*logA**3+1.87457613E-05*theta**2*logC-1.89357731E-05*theta**2*logC**2-2.93328055E-05*theta**2*logC**3+2.93395100E-07*theta**3*logA-2.75796904E-07*theta**3*logA**2+1.72610716E-07*theta**3*logA**3-2.23519403E-07*theta**3*logC+4.58309702E-07*theta**3*logC**2+4.63580626E-07*theta**3*logC**3+4.81094653E-02*logA*logC-7.32373149E-02*logA*logC**2-3.69419093E-02*logA*logC**3+3.12251619E-02*logA**2*logC+1.98976232E-02*logA**2*logC**2-1.94585372E-02*logA**2*logC**3-2.19365112E-02*logA**3*logC+3.12198402E-02*logA**3*logC**2+1.91476647E-02*logA**3*logC**3
    
    if (f3d_57<0): f3d_57=0
    
    return f3d_57
    
def f3d_58(r,d,l_1,l_2):
    """
    This function returns the view factor between a circular disk to a parallel right triangle with an acute vertex on the center
    
    Parameters
    ----------
    r : float
        radius of circular disk
    d : float
        distance between disk and triangle
    l_1 : float
        length of leg of triangle that is opposite center
    l_2 : float
        length of leg of triange that is adjacent center
    """
    
    if(r<0): __warning('r must be greater than 0 in F3D_58')
    if(d<0): __warning('d must be greater than 0 in F3D_58')
    if(l_1<0): __warning('l_1 must be greater than 0 in F3D_58')
    if(l_2<0): __warning('l_2 must be greater than 0 in F3D_58')
    
    X=r/d
    if(X<0): __warning('r/d must be greater than 0 in F3D_58')
    if(X>0.75): __warning('r/d must be less than 0.75 in F3D_58')
    
    YND=d/l_1
    if(YND<0.1): __warning('d/l_1 must be greater than 0.1 in F3D_58')
    if(YND>20): __warning('d/l_1 must be less than 20 in F3D_58')
    logY=log10(YND)
    
    ZND=d/l_2
    if(ZND<0.2): __warning('d/l_2 must be greater than 0.2 in F3D_58')
    if(ZND>3.5): __warning('d/l_2 must be less than 3.5 in F3D_58')
    logZ=log10(ZND)
    
    f3d_58=6.85593337E-02-1.21777288E-01*X+8.96687233E-01*X**2-1.97880106E+00*X**3+1.31188397E+00*X**4-1.08834719E-01*logY+3.02816114E-02*logY**2+3.26735718E-02*logY**3-1.51666781E-02*logY**4-2.26168465E-02*logZ-1.51216720E-01*logZ**2+4.66689632E-02*logZ**3+1.42932067E-01*logZ**4-3.49554647E-03*X*logY+9.17638677E-06*X*logY**2+2.68850976E-03*X*logY**3-2.40332914E-02*X*logZ+1.49103065E-02*X*logZ**2+2.23914235E-02*X*logZ**3+1.69492691E-02*X**2*logY+6.14993602E-03*X**2*logY**2-1.10372070E-02*X**2*logY**3+3.10099551E-02*X**2*logZ-4.69150191E-02*X**2*logZ**2-5.10912160E-02*X**2*logZ**3-5.10328944E-03*X**3*logY-4.92188429E-03*X**3*logY**2+7.68782937E-03*X**3*logY**3-3.98399227E-02*X**3*logZ+6.23487001E-02*X**3*logZ**2+1.01014600E-01*X**3*logZ**3+8.49955224E-02*logY*logZ+1.15588874E-01*logY*logZ**2-1.05390278E-01*logY*logZ**3-5.76586274E-02*logY**2*logZ+4.37820531E-02*logY**2*logZ**2+4.90356346E-02*logY**2*logZ**3+4.06489755E-03*logY**3*logZ-6.48026123E-02*logY**3*logZ**2+1.68708471E-02*logY**3*logZ**3
    
    if (f3d_58<0): f3d_58=0
    
    return f3d_58
    
def f3d_59(e,x,theta):
    """
    This function returns the view factor betweena disk and a second disk inside a cone
    
    Parameters
    ----------
    e : float
        distance from the tip of the cone and disk 1
    x : float
        distance from the tip of the cone and disk 2
    theta : float
        angle of the cone
    """
    
    if(e<0): __warning('e must be greater than 0 in F3D_59')
    if(x<0): __warning('x must be greater than 0 in F3D_59')
    if(theta<0): __warning('theta must be greater than 0 in F3D_59')
    
    # theta_D=theta*convert(D$,'Degree')
    if(theta*180./pi>90): __warning('theta must be less than 90 degree in F3D_59')
    
    XND=e/x
    Num=1+XND**2-2*XND*(cos(theta/2))**2
    Num=Num-abs(1-XND)*sqrt((XND+1)**2-4*XND*(cos(theta/2))**2)
    Den=2*XND**2*(sin(theta/2))**2
    f3d_59=Num/Den
    
    if (f3d_59<0): f3d_59=0
    
    return f3d_59
    
def f3d_60(h_1,h_2,r_s):
    """
    This function returns the view factor between a two non-intersecting disks that are inscribed in a sphere.  The axes of the disks intersect between the disks.
    
    Parameters
    ----------
    h_1 : float
        distance from the center of sphere to disk 1 along its axis
    h_2 : float
        distance from the center of sphere to disk 2 along its axis
    r_s : float
        radius of sphere
    """
    
    if(h_1<0): __warning('h_1 must be greater than 0 in F3D_60')
    if(h_2<0): __warning('h_2 must be greater than 0 in F3D_60')
    h_min=min(h_1,h_2)
    if(r_s<h_min): __warning('r_2 must be greater than the minimum of h_1 and h_2 in F3D_60')
    
    r_1=sqrt(r_s**2-h_1**2)
    r_2=sqrt(r_s**2-h_2**2)
    
    HND1=h_1/r_s
    HND2=h_2/r_s
    RND=r_1/r_s
        
    f3d_60=(1-HND1)*(1-HND2)/RND**2
    
    return f3d_60
    
def f3d_61(h_1,h_2,r_s):
    """
    This function returns the view factor between a two non-intersecting disks that are inscribed in a sphere.  The axes of the disks intersect outside of the disks.
    
    Parameters
    ----------
    h_1 : float
        distance from the center of sphere to disk 1 along its axis
    h_2 : float
        distance from the center of sphere to disk 2 along its axis
    r_s : float
        radius of sphere
    """
    
    if(h_1<0): __warning('h_1 must be greater than 0 in F3D_61')
    if(h_2<0): __warning('h_2 must be greater than 0 in F3D_61')
    h_min=min(h_1,h_2)
    if(r_s<h_min): __warning('r_2 must be greater than the minimum of h_1 and h_2 in F3D_61')
    
    r_1=sqrt(r_s**2-h_1**2)
    r_2=sqrt(r_s**2-h_2**2)
    
    HND1=h_1/r_s
    HND2=h_2/r_s
    RND=r_1/r_s
        
    f3d_61=(1-HND1)*(1+HND2)/RND**2
    
    return f3d_61
    
def f3d_62(a,r_1,r_2,r_3):
    """
    This function returns the view factor between a disk and a coaxial, parallel ring
    
    Parameters
    ----------
    a : float
        distance from disk to ring
    r_1 : float
        radius of disk
    r_2 : float
        inner radius of ring
    r_3 : float
        outer radius of ring
    """
    
    if(a<0): __warning('a must be greater than 0 in F3D_62')
    if(r_1<0): __warning('r_1 must be greater than 0 in F3D_62')
    if(r_2<0): __warning('r_2 must be greater than 0 in F3D_62')
    if(r_3<0): __warning('r_3 must be greater than 0 in F3D_62')
    
    HND=a/r_1
    R2ND=r_2/r_1
    R3ND=r_3/r_1
        
    f3d_62=(1/2)*(R3ND**3-R2ND**2-sqrt((1+R3ND**2+HND**2)**2-4*R3ND**2)+sqrt((1+R2ND**2+HND**2)**2-4*R2ND**2))
    
    return f3d_62
    
def f3d_63(r_1,r_2,alpha,s):
    """
    This function returns the view factor between a disk and a coaxial, cone
    
    Parameters
    ----------
    r_1 : float
        radius of disk
    r_2 : float
        radius of cone at its base
    alpha : float
        angle of cone
    s : float
        distance from disk to tip of cone
    """
    
    if(r_1<0): __warning('r_1 must be greater than 0 in F3D_63')
    if(r_2<0): __warning('r_2 must be greater than 0 in F3D_63')
    if(alpha<0): __warning('alpha must be greater than 0 in F3D_63')
    if(alpha*180./pi>90): __warning('alpha must be less than 90 degree in F3D_63')
    
    SND=s/r_1
    RND=r_2/r_1
    XND=(SND+RND/tan(alpha))
    AND=sqrt(XND**2+(1+RND)**2)
    BND=sqrt(XND**2+(1-RND)**2)
    CND=sqrt(cos(alpha)+SND*sin(alpha))
    DND=sqrt(cos(alpha)-SND*sin(alpha))
    END=RND/tan(alpha)-SND
        
    if (alpha>arctan(1/SND)):
        f3d_63=(1/2)*(RND**2+XND**2+1-sqrt((1+RND**2+XND**2)**2-4*RND**2))
    else:
        Term1=-AND*BND*arctan(AND*CND/(BND*DND))
        Term2=(1+SND**2)*arctan(CND/DND)
        Term3=(sin(alpha)/(cos(alpha))**2)*(XND*END*arctan(CND*DND/XND)+SND**2*arctan(CND*DND/SND)+(CND*DND)**2*(arctan(XND/(CND*DND))-arctan(SND/(CND*DND))))
        Term4=(RND*(XND+SND)/sin(2*alpha)-SND*RND*tan(alpha))*arccos(-SND*tan(alpha))
        f3d_63=(1/pi)*(Term1+Term2+Term3+Term4)
    
    return f3d_63
    
def f3d_64(h,r_1,r_2,alpha):
    """
    This function returns the view factor between an annular disk and a truncated coaxial cone
    
    Parameters
    ----------
    h : float
        length of cone
    r_1 : float
        outer radius of disk
    r_2 : float
        inner radius of disk and cone at its base
    alpha : float
        angle of cone
    """
    
    if(r_2<0): __warning('r_2 must be greater than 0 in F3D_64')
    if(r_1<r_2): __warning('r_1 must be greater than r_2 in F3D_64')
    if(h<0): __warning('h must be greater than 0 in F3D_64')
    if(alpha*180/pi>90): __warning('alpha must be less than 90 degree in F3D_64')
    if(alpha*180/pi<-90): __warning('alpha must be greater than -90 degree in F3D_64')
    
    HND=h/r_1
    RND=r_2/r_1
    AND=sqrt(HND**2+(1+RND+HND*tan(alpha))**2)
    BND=sqrt(HND**2+(1-RND-HND*tan(alpha))**2)
    CND=sqrt(1-RND)
    DND=sqrt(1+RND)
    END=(cos(alpha))**2*(1-RND**2)
        
    Term1=1/(pi*(1-RND**2))
    Term2= -AND*BND*arctan(AND*CND/(BND*DND))
    Term3=(CND*DND)**2*arctan(DND/CND)
    Term4=sin(alpha)/(cos(alpha))**2
    Term5=(HND**2+2*HND*RND/tan(alpha))*arctan(sqrt(END)/HND)
    Term6=END*arctan(HND/sqrt(END))
    Term7=(HND**2/(2*(cos(alpha))**2)+HND*RND*tan(alpha))*arccos(RND)
    f3d_64=Term1*(Term2+Term3+Term4*(Term5+Term6)+Term7)
    return f3d_64
    
def  f3d_65(r_c, r_1,r_2,h):
    """
    This function provides the view factor between an annular ring between two concentric cylinders to ininside of an outer cylinder
    ReferenceL  H.J. van Antwerpen and G.P. Greyvenstein, Nuclear Engineering and Design, V. 238, pp. 2985-2994, 2008
    """
    f3d_65=0
    if (h<=0): return
    R1=r_1/h
    R2=r_2/h
    Rc=r_c/h
    A=R1**2-Rc**2
    B=R2**2-Rc**2
    C=R2+R1
    D=R2-R1
    Y=sqrt(A)+sqrt(B)
    arg1=sqrt(((1+C**2)*(Y**2-D**2))/((1+D**2)*(C**2-Y**2)))
    F2=1/(pi*A)*(B/2*(pi-arccos(Rc/R2))-2*Rc*(arctan(Y)-arctan(sqrt(B)))-0.5*arccos(Rc/R1)+\
    sqrt((1+C**2)*(1+D**2))*arctan(arg1)-\
    sqrt((1+(R2+Rc)**2)*(1+(R2-Rc)**2))*arctan(sqrt((1+(R2+Rc)**2)*(R2-Rc)/((1+(R2-Rc)**2)*(R2+Rc))))-\
    (R2**2-R1**2)*arctan(C/D*sqrt((Y**2-D**2)/(C**2-Y**2))))
    f3d_65=F2
    return f3d_65
    
def  f3d_66(r_c, r_1,r_2,h):
    """
    This function provides the view factor between annular rinngs at the ends of an inscribed cylinder
    Reference:  H.J. van Antwerpen and G.P. Greyvenstein, Nuclear Engineering and Design, 238, pp. 2985-2994, 2008
    """
    f3d_66=0;
    if (h<=0): return
    A=r_c/h
    B=r_1/h
    C=r_2/h
    Y=sqrt(C**2-A**2)+sqrt(B**2-A**2)
    F3=1./(pi*(C**2-A**2))*(1/2*(C**2-A**2)*arccos(A/B)+1/2*(B**2-A**2)*arccos(A/C) +\
    2*A*(arctan(sqrt(C**2-A**2)+sqrt(B**2-A**2))-arctan(sqrt(C**2-A**2))-arctan(sqrt(B**2-A**2))) -\
    sqrt((1+(C+B)**2)*(1+(C-B)**2))*arctan(sqrt((1+(C+B)**2)/(1+(C-B)**2)*(Y**2-(C-B)**2)/((C+B)**2-Y**2))) +\
    sqrt((1+(C+A)**2)*(1+(C-A)**2))*arctan(sqrt((1+(C+A)**2)/(1+(C-A)**2)*(C-A)/(C+A)))+\
    sqrt((1+(B+A)**2)*(1+(B-A)**2))*arctan(sqrt((1+(B+A)**2)/(1+(B-A)**2)*(B-A)/(B+A))))
    f3d_66=F3
    return  f3d_66
    
def  f3d_67(r_c, r_1,r_2,h_1,h_2):
    """
    This function provides the view factor between the outer surface of a cylinder (A_2) to a flat annular ring below the base of the cylinder (A_1)"
    Reference:  H.J. van Antwerpen and G.P. Greyvenstein, Nuclear Engineering and Design, 238, pp. 2985-2994, 2008
    """
    f3d_67=0
    if (h_1<=0): return
    if (h_2<=0): return
    A3=pi*(2*r_c)*h_2
    A1=pi*(2*r_c)*h_1
    A5=(pi*2*r_c)*(h_2-h_1)
    F1_34=f3d_06(r_c,r_2,h_2)
    F1_36=f3d_06(r_c,r_1,h_2)
    F1_54=f3d_06(r_c,r_2,h_2-h_1)
    F1_56=f3d_06(r_c,r_1,h_2-h_1)
    f3d_67=A3/A1*(F1_34-F1_36)-A5/A1*(F1_54-F1_56)
    return f3d_67
    
def  f3d_68(r_c, r_1,r_2,r_3,r_4,h):
    """
    This function provides the view factor between two annular rings including the presence of an inner cylinder."
    Reference:  H.J. van Antwerpen and G.P. Greyvenstein, Nuclear Engineering and Design, 238, pp. 2985-2994, 2008
    """
    f3d_68=0
    if (h<=0): return
    if (r_4<=r_c): return
    if (r_4<=r_3): return
    A3=pi*(r_4**2-r_c**2)
    A1=pi*(r_4**2-r_3**2)
    A5=pi*(r_3**2-r_c**2)
    F34=f3d_66(r_c,r_2,r_4,h) 
    F36=f3d_66(r_c,r_1,r_4,h) 
    F54=f3d_66(r_c,r_2,r_3,h) 
    F56=f3d_66(r_c,r_1,r_3,h) 
    f3d_68=A3/A1*(F34-F36)-A5/A1*(F54-F56)
    xx=f3d_66(r_c,r_1,r_4,h) 
    return  f3d_68
    
def  f3d_69(r_c, r_1,r_2,r_3,h_1,h_2):
    """
    This function provides the view factor between the outer surface of a cylinder (A_2) to a flat annular ring section below the base of the cylinder (A_1)"
    Reference:  H.J. van Antwerpen and G.P. Greyvenstein, Nuclear Engineering and Design, 238, pp. 2985-2994, 2008
    """
    f3d_69=0
    if (h_1<=0): return
    if (h_2<=0): return
    A3=pi*(r_2**2-r_c**2)
    A1=pi*(r_2**2-r_1**2)
    A5=pi*(r_1**2-r_c**2)
    F1_34=f3d_65(r_c,r_2,r_3,h_2)
    F1_36=f3d_65(r_c,r_2,r_3,h_1)
    F1_54=f3d_65(r_c,r_1,r_3,h_2)
    F1_56=f3d_65(r_c,r_1,r_3,h_1)
    f3d_69=A3/A1*(F1_34-F1_36)-A5/A1*(F1_54-F1_56)
    return f3d_69
    
def  f3d_70(r_c,r,s,h_1,h_2):
    """
    This function provides the view factor a cylinder inner surface to an adjacent surface on the same cylinder"
    Reference:  H.J. van Antwerpen and G.P. Greyvenstein, Nuclear Engineering and Design, 238, pp. 2985-2994, 2008
    """
    f3d_70=0
    if (h_1<=0): return
    if (h_2<=0): return
    F1=(h_1+h_2+s)/(2*h_1)*f3d_05(r_c,r,h_1+h_2+s)
    F2=(h_1+s)/(2*h_1)*f3d_05(r_c,r,h_1+s)
    F3=(h_2+s)/(2*h_1)*f3d_05(r_c,r,h_2+s)
    F4=s/(2*h_1)*f3d_05(r_c,r,s)
    f3d_70=F1-F2-F3+F4
    return  f3d_70
    # ____________________________________________________________________________
    
# Procedure f3d_71(D, L, W, S, N_rays: F1, F2, F3, F4, F5)
#     """
#     This procedure provides the view factors between a plane and each of five cylinders that run parallel to the plane and are stacked
#     on top of one another.  Reference: Brennan Fentzlaff thesis
#     """
    
#     if (N_rays<=0): N_rays=1e5
#     if (D<=0): __warning('D must be greater than 0 in F3D_71')
#     if (L<=0): __warning('L must be greater than 0 in F3D_71')
#     if (W<=0): __warning('W must be greater than 0 in F3D_71')
#     if (S<=0): __warning('S must be greater than 0 in F3D_71')
        
#     D_SI=D*convert(U$,m)
#     L_SI=L*convert(U$,m)
#     W_SI=W*convert(U$,m)
#     S_SI=S*convert(U$,m)
#     Call f3d71(N_rays,D_SI,L_SI,W_SI,S_SI:F1,F2,F3,F4,F5)

#     return f3d71
# # ____________________________________________________________________________
    
# Procedure f3d_72(N_rays, N_cyl, D, H, L, W: F1, F2, F3, F4, F5, F6, F7, F8, F9, F10)
#     """
#     This procedure provides the view factors between a plane and each of up to ten cylinders that run parallel to the plane and are stacked
#     next to one another.  Reference: Brennan Fentzlaff thesis
#     """
    
#         if (N_rays<=0): N_rays=1e5
#         if (N_cyl<1): __warning('N_cyl must be greater than 0 in F3D_72')
#         if (N_cyl>10): __warning('N_cyl cannot be greater than 10 in F3D_72')
#         if (D<=0): __warning('D must be greater than 0 in F3D_72')
#         if (H<=0): __warning('H must be greater than 0 in F3D_72')
#         if (L<=0): __warning('L must be greater than 0 in F3D_72')
#         if (W<=0): __warning('W must be greater than 0 in F3D_72')
            
#         D_SI=D*convert(U$,m)
#         L_SI=L*convert(U$,m)
#         W_SI=W*convert(U$,m)
#         H_SI=H*convert(U$,m)
#         Call f3d72(N_rays,N_cyl,D_SI,H_SI,L_SI,W_SI:F1,F2,F3,F4,F5,F6,F7,F8,F9,F10)
    
#     return f3d72
#     # ____________________________________________________________________________
    
#     Procedure f3d_73(N_rays, N_cyl, D, L_cyl, L, W: F1, F2, F3, F4, F5, F6, F7, F8, F9, F10)
#     """
#     This procedure provides the view factors between a plane and each of up to ten cylinders that run perpendicular to the plane like pillars and are stacked
#     next to one another.  Reference: Brennan Fentzlaff thesis
#     """
    
#         if (N_rays<=0): N_rays=1e5
#         if (N_cyl<1): __warning('N_cyl must be greater than 0 in F3D_73')
#         if (N_cyl>10): __warning('N_cyl cannot be greater than 10 in F3D_73')
#         if (D<=0): __warning('D must be greater than 0 in F3D_73')
#         if (L_cyl<=0): __warning('L_cyl must be greater than 0 in F3D_73')
#         if (L<=0): __warning('L must be greater than 0 in F3D_73')
#         if (W<=0): __warning('W must be greater than 0 in F3D_73')
            
#         D_SI=D*convert(U$,m)
#         L_cyl_SI=L_cyl*convert(U$,m)
#         L_SI=L*convert(U$,m)
#         W_SI=W*convert(U$,m)
#         Call f3d73(N_rays,N_cyl,D_SI,L_cyl_SI,L_SI,W_SI:F1,F2,F3,F4,F5,F6,F7,F8,F9,F10)
#     return f3d73
#     # ____________________________________________________________________________
# 
# def f3d_74(N_rays, s1, s2, alpha):
#     """
#     This procedure provides the view factors between a square and a second square in a perpendicular plane tilted relative to the first.  The corners of the squares touch.
#     N_rays - number of rays to use in Monte Carlo simulation
#     s1 - size of square 1
#     s2 - size of square 2
#     alpha - angle of tilt
#     """
    
#         if (N_rays<=0): N_rays=1e6
#         if (s1<=0): __warning('s1 must be greater than 0 in F3D_74')
#         if (s2<=0): __warning('s2 must be greater than 0 in F3D_74')
#         alpha_rad=alpha*convert(D$,Rad)
#         Call f3d74(N_rays, s1, s2, alpha: F)
#         f3d_74=F
#     return f3d_74
#     # ____________________________________________________________________________
    
def f3d_75(alpha):
    """
    This procedure provides the view factor between two half-circles of the same radius with a common edge tilted by angle alpha
    """
    
    if (alpha<0): __warning('alpha must be greater than 0 in F3D_75')
    if (alpha>pi): __warning('alpha must be less than pi radian in F3D_75')
    f3d_75=1-2*alpha/pi+(alpha/pi)**2
    return f3d_75
    # ____________________________________________________________________________
    
def f3d_76(alpha):
    """
    This procedure provides the view factor between one half-circle and the sector of the sphere formed between it and a second 
    half-circle of the same radius with a common edge tilted by angle alpha
    """
    if (alpha<0): __warning('alpha must be greater than 0 in F3D_76')
    if (alpha>pi): __warning('alpha must be less than pi radian in F3D_76')
    f3d_76=2*alpha/pi-(alpha/pi)**2
    return f3d_76
    # ____________________________________________________________________________
    
# def f3d_77(N_rays, r1, r2, h, beta, alpha):
#     """
#     This procedure provides the view factor between a sector of a disk to a parallel sector of a disk
#     """
    
#     if (r1<0): __warning('r1 must be greater than 0 in F3D_77')
#     if (r2<0): __warning('r2 must be greater than 0 in F3D_77')
#     if (h<0): __warning('h must be greater than 0 in F3D_77')
#     if (beta<0): __warning('beta must be greater than 0 in F3D_77')
#     if (alpha<0): __warning('alpha must be greater than 0 in F3D_77')
#     if (alpha>(2*pi)): __warning('alpha must be less than 2*pi radian in F3D_77')
#     if (beta>(2*pi)): __warning('beta must be less than 2*pi radian in F3D_77')
#     if (N_rays<=0): N_rays=1e6
#     Call f3d77(N_rays, r1, r2, h, beta, alpha: F)
#     f3d_77=F
#     return f3d_77
#     # ____________________________________________________________________________
    
def fdiff_01(a,b,c):
    """
    returns the view factor between a differential element dA_1 and a plane parallel rectangle.
    A normal to the element passes through the corner of the rectangle.
    
    Siegel and Howell, Thermal Radiation Heat Transfer, 4th edition, p.842.

    Parameters
    ----------
    a : float
        height of the rectangle
    b : float
        width of the rectangle
    c : float
        is the distance between the plane of the rectangle and the plane of the element dA_1.
    """
    if (a == 0): a=1e-9
    if (b == 0): b=1e-9
    if (c == 0): c=1e-9
    if (a<=0): __warning(f'Function value a outside of range, has value {a}')
    if (b<=0): __warning(f'Function value b outside of range, has value {b}')
    if (c<=0): __warning(f'Function value c outside of range, has value {c}')
    X = a/c
    Y = b/c
    fdiff_1 = 1/(2*pi)*(X/sqrt(1+X**2)*arctan(Y/sqrt(1+X**2)) + Y/sqrt(1+Y**2)*arctan(X/sqrt(1+Y**2)))
    return fdiff_1
    
def fdiff_02(a,b,c):
    """
    Returns the view factor value from a strip element to a rectangle in a plane parallel to it.  
    
    Siegel and Howell, Thermal Radiation Heat Transfer, 4th edition, p.842.
    
    Parameters
    ----------
    a : float
        width of the rectangle
    b : float
        length of the rectangle
    c : float
        distance between the plane of the rectangle and the plane of the strip element.
    """
    if (a == 0): a=1e-9
    if (b == 0): b=1e-9
    if (c == 0): c=1e-9
    if (c<=0): __warning(f'Function value c outside of range, has value {c}')
    if (b<=0): __warning(f'Function value b outside of range, has value {b}')
    if (a <=0): __warning(f'Function value a outside of range, has value {a}')
    X = a/c
    Y =b/c
    fdiff_2= 1/(pi*Y)*( sqrt(1 + Y**2)*arctan(X/(sqrt(1+Y**2))) - arctan(X) + ((X*Y)/(sqrt(1+X**2)))*arctan(Y/(sqrt(1+X**2))))
    return fdiff_2
    
def fdiff_03(a,b,c):
    """
    This function calculates the View Factor from a plane element dA_1 to a rectangle in plane 90 degrees to plane of element.
    The element is located above one corner of the rectangle.

    Siegel and Howell, Thermal Radiation Heat Transfer, 4th edition, p.842.

    Parameters
    ----------
    a : float
       height of rectangle;
    b : float
       length of rectangle;
    c : float
       distance from element dA_1 to rectangle.
    """
    if (a == 0): a=1e-9
    if (b == 0): b=1e-9
    if (c == 0): c=1e-9
    if (a <= 0): __warning(f'Function value a outside of range, has value {a}')
    if (b <= 0): __warning(f'Function value b outside of range, has value {b}')
    if (c <= 0): __warning(f'Function value c outside of range, has value {c}')
    X= a/b
    Y= c/b
    fdiff_3 = 1/(2*pi)* ( arctan(1/Y) - Y/(sqrt(X**2 + Y**2))*arctan(1/(sqrt(X**2 + Y**2))) )
    return fdiff_3
    
def fdiff_04(a,b,c):
    """
    FDiff_4 provides the view factor from a strip element to a rectangle in a plane 90 degrees to the plane of the strip.
    
    Refer to Siegel and Howell, Thermal Radiation Heat Transfer, 4th edition, p.843.

    Parameters
    ----------
    a : float
        height of the rectangle above the plane of the strip
    b : float
        width of the rectangle and of the strip
    c : float
        distance from the rectangle to the strip in the plane of the strip
    """
    if (a == 0): a=1e-9
    if (b == 0): b=1e-9
    if (c == 0): c=1e-9
    if (a<=0): __warning(f'Function value a outside of range, has value {a}')
    if (b<=0): __warning(f'Function value b outside of range, has value {b}')
    if (c<=0): __warning(f'Function value c outside of range, has value {c}')
    X = a/b
    Y = c/b
    fdiff_4 = 1/pi * ( arctan(1/Y) +Y/2 *log(Y**2*(X**2+Y**2+1)/((Y**2+1)*(X**2+Y**2)))-Y/sqrt(X**2+Y**2)*arctan(1/sqrt(X**2+Y**2)) )
    return fdiff_4
    
def fdiff_05(a,b,c):
    """
    fdiff_05(a, b, c)  provides the view factor from a spherical point source to a plane rectangle.  

    Parameters
    ----------
    a : float
        height of the rectangle above the spherical point 
    b : float
        width of the rectangle
    c : float
        distance from the rectangle to the spherical point in the plane of the sphere
    """
    AA=a/c
    BB=b/c
    fdiff_5=arctan((AA*BB)/sqrt(1+AA**2+BB**2))/(4*pi)
    return fdiff_5
    
    
def fdiff_06(r_1,r_2,h):
    """
    This function provides the view factor between a differential ring element to a ring element on a coaxial disk.
    
    Howell, http://www.me.utexas.edu/~howell/sectionb/B-91.html from Feingold and Gupta, 1970
    
    Parameters
    ----------
    r_1 : float
        radius of the first differential ring
    r_2 : float
        radius of the second differential ring
    h : float
        perpendicular distance from the centerpoints of each ring element
    """
    R1=r_1/h
    R2=r_2/h
    fdiff_6=R2**2/(1+R1**2)**1.5
    return fdiff_6
    
    
def fdiff_07(r,x):
    """
    This function provides the view factor between ring element on interior of right circular cylinder to circular disk at end of cylinder
    
    Howell, http://www.me.utexas.edu/~howell/sectionb/B-93.html 
    
    Parameters
    ----------
    r : float
        radius of the cylinder
    x : float
        axial position of the differential element
    """
    XX=x/(2*r)
    fdiff_7=(XX**2+1/2)/(sqrt(1+XX**2))-XX
    return fdiff_7
    
def fdiff_08(r_1, r_2, a):
    """
    This function provides the view factor between a differential element or ring on disk 1 to coaxial parallel disk 2
    
    Howell, http://www.me.utexas.edu/~howell/sectionb/B-22.html 
    
    Parameters
    ----------
    r_1 : float
        radius of the differential ring
    r_2 : float
        radius of the disk
    a : float
        distance between the disk and the ring
    """
    if(a<=0): a=1e-6
    R1=r_1/a
    R2=r_2/a
    fdiff_8=1/2*(1-((R1**2-R2**2+1)/sqrt((R1**2+R2**2+1)**2-4*R1**2*R2**2)))
    return fdiff_8
    
    
def fdiff_09(r_1, r_2, x_1, x_2):
    """
    This function provides the view factor between a ring element (1) on base of right circular cylinder to finite circumferential ring (2) on interior of cylinder
    
    This view factor is determined by differencing the view factor between two disks enclosing the circumferential ring to the differential ring element using FDiff_8.
    
    Parameters
    ----------
    r_1 : float
        radius of the differential ring
    r_2 : float
        radius of the cylinder
    x_1  : float
        lower axial position of the circumferential ring
    x_2 : float
        upper axial position of the circumferential ring
    """
    fdiff_9=fdiff_08(r_1,r_2,x_1)-fdiff_08(r_1,r_2,x_2)
    return fdiff_9
    
    
def fdiff_10(r,sz):
    """
    This function provides the view factor between an element (1) on a longitudinal strip on the inside of of a right circular cylinder to the base of the cylinder (2).
    
    Reference: Howell, http://www.me.utexas.edu/~howell/sectionb/B-52.html 
    
    Parameters
    ----------
    r : float
        radius of the cylinder 
    sz : float
        height of the element above the base
    """
    Z=sz/r
    if (Z<0): Z=0
    fdiff_10=(Z**2+2)/(2*sqrt(Z**2+4))-Z/2
    return fdiff_10
    
    
def fdiff_11(r,sz,sh):
    """
    This function provides the view factor between an element (1) on a longitudinal strip on the inside of of a right circular cylinder to the inside surface of the cylinder (2).
    
    Reference: Howell, http://www.me.utexas.edu/~howell/sectionb/B-51.html 
    
    Parameters
    ----------
    r : float
        radius of the cylinder 
    sz : float
        height of the element above the base
    sh : float
        height of the cylinder
    """
    Z=sz/(2*r)
    H=sh/(2*r)
    fdiff_11=1+H-(Z**2+0.5)/sqrt(Z**2+1)-((H-Z)**2+0.5)/sqrt((H-Z)**2+1)
    return fdiff_11
    
    
def fdiff_12(r1,r2,sz):
    """
    This function provides the view factor between an element (1) on a longitudinal strip on the inside of of a right circular cylinder to  a disk on the base of the cylinder (2).
    
    Reference: Howell, http://www.me.utexas.edu/~howell/sectionb/B-53.html 
    
    Parameters
    ----------
    r1 : float
        radius of the cylinder 
    r2 : float
        radius of the disk where (r2<r1)
    sz : float
        height of the element above the base
    """
    Z=sz/r1
    R=r2/r1
    if (R>=1): R=1+1e-8
    X=1+Z**2+R**2
    fdiff_12=Z/2*(X/sqrt(X**2-4*R**2)-1)
    return fdiff_12
    
    
def fdiff_13(r_1,r_2, sz, sh):
    """
    This function provides the view factor between an element (1) on a longitudinal strip on the inside of a right circular cylinder to the exterior of concentric smaller right circular cylinder.
    
    Reference: Howell, http://www.me.utexas.edu/~howell/sectionb/B-57.html 
    
    Parameters
    ----------
    r_1 : float
        radius of the inner cylinder 
    r_2 : float
        radius of the outer cylinder
    sz : float
        height of the element above the base
    sh : float
        height of the cylinders
    """
    R=r_2/r_1
    H=sh/r_1
    Z=sz/r_1
    A=R**2-1
    B=max(1e-6,(H-Z)**2)
    C=Z**2+R**2+1
    D=Z**2-A
    T1=1/R-1/(2*pi*R)*(arccos(D/(C-2))+arccos((B-A)/(B+A)))
    T2=Z/(2*pi*R)*(C/sqrt(C**2-4*R**2)*arccos(D/(R*(C-2))))
    T3=sqrt(B)/(2*pi*R)*((B+R**2+1)/sqrt((B+R**2+1)**2-4*R**2)*arccos((B-A)/(R*(B+A))))-H/(2*pi*R)*arccos(1/R)
    fdiff_13=T1+T2+T3
    return fdiff_13
    
def fdiff_14(r_1,r_2, sz, sh):
    """
    This function provides the view factor between an element (1) on a longitudinal strip on the inside of a right circular cylinder to the outer concentric right circular cylinder.
    
    Reference: Howell, http://www.me.utexas.edu/~howell/sectionb/B-56.html 
    
    Parameters
    ----------
    r_1 : float
        radius of the inner cylinder 
    r_2 : float
        radius of the outer cylinder
    sz : float
        height of the element above the base
    sh : float
        height of the cylinders
    """
    if (sz<1e-9): sz=1e-9
    if (sz>=sh): sz=sh*0.999999
    R=r_2/r_1
    H=sh/r_1
    Z=sz/r_1
    A=R**2-1
    B=max(1e-6,(H-Z)**2)
    T1=1-1/R+H/(4*R)-(Z**2+2*R**2)/(4*R*sqrt(4*R**2+Z**2))-(B+2*R**2)/(4*R*sqrt(4*R**2+B))
    T2=1/pi*(1/R*(arctan(2*sqrt(A)/Z)+arctan(2*sqrt(A/B)))+H/(2*R)*arcsin(1-2/R**2))
    T3=-(Z**2+2*R**2)/(2*pi*R*sqrt(4*R**2+Z**2))*arcsin((4*A+Z**2*(1-2/R**2))/(Z**2+4*A))
    T4=-(B+2*R**2)/(2*pi*R*sqrt(4*R**2+B))*arcsin((4*A+B*(1-2/R**2))/(B+4*A))
    fdiff_14=T1+T2+T3+T4
    return fdiff_14
    
def fdiff_15(r_1,r_2, sz):
    """
    This function provides the view factor between an element (1) on a longitudinal strip on the inside of a right circular cylinder to the annual end enclosing space between coaxial cylinders.
    
    Reference: Howell, http://www.me.utexas.edu/~howell/sectionb/B-56.html 
    
    Parameters
    ----------
    r_1 : float
        radius of the inner cylinder 
    r_2 : float
        radius of the outer cylinder
    sz : float
        height of the element above the base
    """
    if (sz<1e-9): sz=1e-9
    Z=sz/r_1
    R=r_2/r_1
    A=R**2-1
    if (A<=0): A=1e-6
    C=Z**2+R**2+1
    D=Z**2-A
    
    T1=-Z/(4*R)+(Z**2+2*R**2)/(4*R*sqrt(4*R**2+Z**2))*(1+2/pi*arcsin((4*A+Z**2*(1-2/R**2))/(Z**2+4*A)))
    T2=1./(2*pi*R)*(arccos(D/(C-2))-2*arctan(2*sqrt(A)/Z)-Z*arcsin(1-2/R**2)+C*Z/sqrt(C**2-4*R**2)*arccos(D/(R*(C-2)))-Z*arccos(1/R))
    fdiff_15=T1+T2
    return fdiff_15
    
def fdiff_16(H, a, R):
    """
    This function provides the view factor between a differential area and a parallel disk.
    
    Reference: Cryogenic Heat Transfer, 2nd Edition, Randall Barron and Greg Nellis, 2016

    Parameters
    ----------
    H : float
        distance between the plane of the differential area and the plane of the disk
    a : float
        distance between the center of the disk and the area in the plane of the disk
    R : float
        radius of the disk
    """
    if (R<=0): __warning('R must be >0 in FDiff_16')
    if (H<0): __warning('H must be >=0 in FDiff_16')
    X=H/R
    Y=a/R
    fdiff_16=(1-(X**2+Y**2-1)/sqrt((X**2+Y**2+1)**2-4*Y**2))/2
    return fdiff_16
    
def fdiff_17(R, L, H):
    """
    This function provides the view factor between a differential area and a cylinder when the area is facing the cylinder and located at its midpoint.
    
    Reference: Cryogenic Heat Transfer, 2nd Edition, Randall Barron and Greg Nellis, 2016
    
    Parameters
    ----------
    R : float
        radius of the cylinder
    L : float
        length of the cylinder
    H : float
        distance between the centerline of  the cylinder and the area
    """
    if (R<=0): __warning('R must be >0 in FDiff_17')
    if (L<=0): __warning('L must be >0 in FDiff_17')
    if (H<R):  __warning('H must be >R in FDiff_17')
    X=L/R
    Y=H/R
    Z1=X**2+(1+Y)**2
    Z2=X**2+(1-Y)**2
    fdiff_17=2/(pi*Y)*(arctan(X/sqrt(Y**2-1))+X*(1+X**2+Y**2)/sqrt(Z1*Z2)*arctan(sqrt(Z1*(Y-1)/(Z2*(Y+1))))-X*arctan(sqrt((Y-1)/(Y+1))))
    
    return fdiff_17
    
def fdiff_18(R, L, H):
    """
    This function provides the view factor between a differential area and a cylinder when the area is facing the cylinder and located at its end point.
    
    Reference: Hamilton, D.C. and Morgan, W.R., 1952, "Radiant-interchange configuration factors," NASA TN 2836. 
    
    Parameters
    ----------
    R : float
        radius of the cylinder
    L : float
        length of the cylinder
    H : float
        distance between the centerline of  the cylinder and the area
    """
    if (R<=0): __warning('R must be >0 in FDiff_17')
    if (L<=0): __warning('L must be >0 in FDiff_17')
    if (H<R):  __warning('H must be >R in FDiff_17')
    LL=L/R
    HH=H/R
    XX=LL**2+(1+HH)**2
    YY=LL**2+(1-HH)**2
    fdiff_18=1/(pi*HH)*arctan(LL/sqrt(HH**2-1))+LL/pi*((XX-2*HH)/(HH*sqrt(XX*YY))*arctan(sqrt((XX*(HH-1))/(YY*(HH+1))))-arctan(sqrt((HH-1)/(HH+1)))/HH)
    
    return fdiff_18


if __name__ == "__main__":
    print(Blackbody(5800, 0.38, 0.78) )

    print(hit_test(__np.array([[-1,-1],[1,-1],[1,1],[-1,1]]),__np.array([.5,.5])))
    print(hit_test(__np.array([[-1,-1],[1,-1],[1,1],[-1,1]]),__np.array([[.5,.5],[-.5,-5]])))

