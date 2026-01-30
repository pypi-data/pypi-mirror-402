"""
Some useful functions to run the library
"""

import numpy as np


_RAD2ARCSEC = 180/np.pi * 3600


def rad2arcsec(rad):
    """Convert radians to arcsec"""
    return rad * _RAD2ARCSEC


def arcsec2rad(arcsec):
    """Convert arcsec to radians"""
    return arcsec / _RAD2ARCSEC


def polar(npix, center=None):
    """Compute polar coordinates (rho[pix], theta[rad])"""
    if center is None:
        center = npix//2
    xx,yy = (np.mgrid[0:npix,0:npix] - center)
    return np.sqrt(xx**2 + yy**2), np.arctan2(yy, xx)


def polar_radius(*args, **kwargs):
    """Compute the polar radius coordinate rho [pix]."""
    return polar(*args, **kwargs)[0]


def circavg(tab, center=None, rmax=None):
    """Compute the circular average of a given array
    
    Parameters
    ----------
    tab : numpy.ndarray (dim=2)
        Two-dimensional array to compute its circular average
    
    Returns
    -------
    vec : numpy.ndarray (dim=1)
        Vector containing the circular average from center
    """
    if tab.ndim != 2:
        raise ValueError("Input `tab` should be a 2D array")
    rr = polar_radius(max(tab.shape), center=center)
    if rmax is None:
        rmax = rr.max()
    avg = np.zeros(int(rmax), dtype=tab.dtype)
    for i in range(int(rmax)):
        index = np.where((rr >= i) * (rr < (i + 1)))
        avg[i] = tab[index[0], index[1]].sum() / index[0].size
    return avg


def circsum(tab, center=None, rmax=None, backward=False):
    """Compute circular sum of a 2D array"""
    if tab.ndim != 2:
        raise ValueError("Input `tab` should be a 2D array")
    rr = polar_radius(max(tab.shape), center=center)
    if rmax is None:
        rmax = rr.max()
    csum = np.zeros(int(rmax), dtype=tab.dtype)
    for i in range(int(rmax)):
        if not backward:
            index = np.where(rr < (i+1))
        else:
            index = np.where(rr >= (i+1))
        csum[i] = tab[index[0], index[1]].sum()
    return csum


def aperture(npix, samp=1, occ=0, center=None):
    """
    Create a circular aperture
    
    Parameters
    ----------
    npix : float
        The size of the output array will be (npix,npix).
    
    Keywords
    --------
    samp : float
        Sampling required for the computations.
        samp=1 means a disc tangent to the array.
        default = 1.
    occ : float
        Occultation ratio (0<=occ<=1).
        default = 0.
    center : int, float, None
        Position of the center of the array.
    """
    rho = polar_radius(npix, center=center)
    aper = rho <= (npix/2/samp)
    if occ>0:
        aper *= rho >= (npix/2/samp*occ)
    return aper


def print_var(var):
    """
    Formatted console print of AO variances budget
    
    Parameter
    ---------
    var : dict
        Dictionary of variances
    """
    var_total = sum([var[j] for j in var.keys()])
    nsq = 20
    print('-'*(16+2+nsq))
    for k in sorted(var.keys(), key=lambda k:-var[k]):
        nbstar = int(round(nsq*var[k]/var_total))
        print('%8s  %4.2f'%(k,var[k]) + '  |' + '\u25a0'*nbstar + ' '*(nsq-nbstar)+'|')
    print()
    print('%8s  %4.2f'%('total',var_total))
    print('-'*(16+2+nsq))
    
    
def print_std(std):
    """
    Formatted console print of AO WFE budget
    
    Parameter
    ---------
    std : dict
        Dictionary of std of WFE
    """
    var_total = sum([std[j]**2 for j in std.keys()])
    nsq = 23
    #print('-'*(17+2+nsq))
    print('-'*17 + '\u25bc' + ('-'*(nsq//4) + '\u25bc')*4 )
    for k in sorted(std.keys(), key=lambda k:-std[k]):
        nbstar = int(round(nsq*std[k]**2/var_total)) # weighting is given by variance, and not std!
        print('%10s %4u'%(k,round(std[k])) + '  |' + '\u25a0'*nbstar + ' '*(nsq-nbstar)+'|')
    print()
    print('%10s %4u'%('total',round(np.sqrt(var_total))))
    print('-'*(17+2+nsq))