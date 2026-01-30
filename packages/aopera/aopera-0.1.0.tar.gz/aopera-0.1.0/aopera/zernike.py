"""
Computation of Zernike polynomials.
"""

import numpy as np
from scipy.special import binom, jv
from aopera.utils import polar


def ansi2nm(j):
    """Convert Zernike J (ANSI) indexing to (n,m) indexing."""
    j = np.array(j)
    n = np.int_(np.sqrt(8*j+1)-1)//2
    m = 2*j-n*(n+2)
    return n,m


def nm2ansi(n, m):
    """Convert (n,m) indexing to J ANSI indexing."""
    n = np.array(n)
    m = np.array(m)
    return np.int_((n*(n+2)+m)//2)


def nm2noll(n, m):
    """Convert (n,m) indexing to J Noll indexing."""
    n = np.array(n)
    m = np.array(m)
    n23 = np.logical_or((n%4)==2, (n%4)==3)
    b = np.logical_or((m>=0) * n23, (m<=0) * np.logical_not(n23))
    return n*(n+1)//2 + np.abs(m) + b


def noll2nm(j, abs_m=False):
    """Convert from Noll indexing (j) to radian-azimuthal indexing (n, m)."""
    j = np.asarray(j, dtype=int)
    n = np.sqrt(8*(j-1) + 1).astype(int)//2 - 1
    p = j - (n*(n + 1))//2
    k = n%2
    m = 2*((p+k)//2) - k
    m = m*(m != 0)*(1 - 2*(j%2))
    if abs_m:
        m = np.abs(m)
    return n, m


def ansi2noll(jansi):
    """Convert ANSI to Noll indexing"""
    return nm2noll(*ansi2nm(jansi))


def noll2ansi(jnoll):
    """Convert Noll to ANSI indexing"""
    return nm2ansi(*noll2nm(jnoll))


def ansi_name(j):
    """Return the Zernike usual name associated to ANSI index."""
    znames = ["piston","tilt vertical","tilt horizontal","astigmatism x","defocus","astigmatism +","trefoil +","coma vertical","coma horizontal","trefoil x","quadrafoil x","secondary astig. x","primary spherical","secondary astig. +","quadrafoil +"]
    if j<len(znames):
        return znames[j]
    return "high order"


def noll_name(j):
    """Return the Zernike usual name associated to Noll index"""
    return ansi_name(noll2ansi(j))


def radial_poly(n, m, rho, outside=0):
    """Compute the radial contribution of a Zernike polynomial.

    Parameters
    ----------
    n : int, radial order.
    m : int, azimuthal order.
    rho : ndarray, the radial values where to compute the polynomial. Must be normalized to a unit circle.

    Keywords
    --------
    outside : float or np.nan, the value to fill the array for ``rho > 1``. Default: ``np.nan``.
    """
    nmm = (n - np.abs(m)) / 2
    if nmm<0:
        raise ValueError('Zernike azimuthal order cannot be greater than radial order')
    if nmm%1:
        raise ValueError('Zernike `n-|m|` must be even')
    aperture = rho <= 1.0
    rr = np.zeros(rho.shape)
    rr[~aperture] = outside
    for k in range(0, int(nmm) + 1):
        rr[aperture] += ((-1)**k * binom(n - k, k) * binom(n - 2 * k, nmm - k) * rho[aperture]**(n - 2 * k))
    return rr


def azimuthal_poly(m, theta):
    """Compute the azimuthal contribution of a Zernike polynomial.

    Parameters
    ----------
    m : int, azimuthal order.
    theta : array, angles [rad] where to compute the polynomial.
    """
    if m >= 0:
        return np.cos(m * theta)
    else:
        return np.sin(np.abs(m) * theta)


def nollnorm(n, m):
    """Compute the Noll Zernike polynomials normalization factor.
        sum(Zi*Zj)/sum(disk) = delta_ij * pi
    """
    neumann = 2 - (m != 0)
    return np.sqrt((2*n + 2) / neumann)


def ansinorm(n, m):
    """Compute the ANSI Zernike polynomials normalization factor.
        sum(Zi*Zj)/sum(disk) = delta_ij
    """
    return nollnorm(n, m) / np.sqrt(np.pi)


def zernike(n, m, npix, samp=1, norm="noll", outside=0):
    """
    Return the (radial=n, azimut=m) Zernike polynomial.
    
    The default norm (`noll`) verifies the normalization:
        
    .. math::
        \\frac{1}{\\pi}\\iint_P|Z(x,y)|^2dxdy \\simeq \\text{Var}(Z_{k,l}[P_{k,l}]) = 1
        
    where `P` denotes a circular non-obstructed pupil.
    
    Warning: the piston mode behaves differently due to its not null average.
    Its L2 norm equals 1, but the variance over the pupil equals 0.
        
    Parameters
    ----------
    n : int, Zernike radial index.
    m : int, Zernike azimuthal index.
    npix : int, size of the output array is (npix, npix).

    Keywords
    --------
    samp : float, samp of the Zernike disk
    norm : "ansi" or "noll"
    outside : float or np.nan, the value to fill the array for rho>1.
    """
    
    rho, theta = polar(npix)
    dx = samp / (npix/2)
    rho = dx * rho
    Z = radial_poly(n, m, rho, outside=outside) * azimuthal_poly(m, theta)
    
    if norm.lower() == "noll":
        norm_coef = nollnorm(n, m)
    elif norm.lower() == "ansi":
        norm_coef = ansinorm(n, m)
    else:
        raise ValueError("``norm`` must be either 'noll' or 'ansi'.")

    return Z * norm_coef


def zernike_fourier(n, m, npix, samp=1, norm="ansi"):
    """
    Compute the Fourier transform of a Zernike polynomial.
    
    The default norm (`ansi`) verifies the normalization:
        
    .. math::
        \\iint |\\hat{Z}(f_x,f_y)|^2 df_xdf_y \\simeq \\sum_{k,l}{|\\hat{Z}_{k,l}|^2 \\delta f^2} = 1
        
    with the frequency step:
        
    .. math::
        \\delta f = \\frac{1}{L} = \\frac{1}{N_p \\delta x} = \\frac{1}{2\\times\\text{samp}}
    """
    rho, theta = polar(npix)
    df = 1/(2*samp)
    rho = rho * df
    rho[np.where(rho==0)] = 1e-8
    norm_coef = (-1+0j)**(n/2-np.abs(m))*np.sqrt(n+1)
    if m!=0:
        norm_coef *= np.sqrt(2)
    if norm.lower()=="ansi":
        norm_coef = norm_coef / np.sqrt(np.pi)
    ztf = azimuthal_poly(m, theta)*jv(n+1, 2*np.pi*rho)/rho
    return ztf * norm_coef
    
    