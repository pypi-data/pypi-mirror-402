import numpy as np
from math import pi

def talbot_inversion(f_s, t, M, *args):
    """
    Returns an approximation to the inverse Laplace transform of function
    handle f_s evaluated at each value in t (1xn) using Talbot's method as
    summarized in the source below.

    This implementation is very coarse; use talbot_inversion_sym for better
    precision. Further, please see example_inversions.m for discussion.
    
    Abate, Joseph, and Ward Whitt. "A Unified Framework for Numerically 
    Inverting Laplace Transforms." INFORMS Journal of Computing, vol. 18.4 
    (2006): 408-421. Print.

    The paper is also online: http://www.columbia.edu/~ww2040/allpapers.html.

    Tucker McClure
    Copyright 2012, The MathWorks, Inc.

    Python implementation, 2022: Mike Wagner/UW-Madison

    Parameters
    ----------
    f_s : Handle to function of s
    t : Times at which to evaluate the inverse Laplace transformation of f_s
    M : Number of terms to sum for each t (64 is a good guess). Highly oscillatory
        functions require higher M, but this can grow
        unstable; see test_talbot.m for an example of stability.
    *args :  list of arguments that are passed to the function f_s(...) in 
            the order provided. 
    
    Returns
    -------
    The inverse Laplace transform of f_s evaluated at each value in t.
    """

    cot = lambda x: 1/np.tan(x)

    # Make sure t is n-by-1.
    if len(t.shape) > 1:
        raise RuntimeError('Input times, t, must be a vector.')
    
    # Vectorized Talbot's algorithm
    
    k = np.array(range(1,M)) #Iteration index
    
    # Calculate delta for every index.
    delta = np.zeros(M, dtype=np.complex128)
    delta[0] = 2*M/5
    delta[1:] = 2*pi/5 * k * (cot(pi/M*k)+1j);
    
    # Calculate gamma for every index.
    gamma = np.zeros(M, dtype=np.complex128)
    gamma[0] = 0.5*np.exp(delta[0])
    gamma[1:] = (1 + 1j*pi/M*k*(1+cot(pi/M*k)**2)-1j*cot(pi/M*k))* np.exp(delta[1:])
    
    # Make a mesh so we can do this entire calculation across all k for all
    # given times without a single loop (it's faster this way).
    delta_mesh, t_mesh = np.meshgrid(delta, t)
    gamma_mesh = np.meshgrid(gamma.T, t)[0]
    
    # Finally, calculate the inverse Laplace transform for each given time.
    return 0.4/t * np.sum( (gamma_mesh * f_s(delta_mesh/t_mesh, *args)).real, 1)

