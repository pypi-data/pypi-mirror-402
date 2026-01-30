"""
Step-index single-mode fibers (SMF)

date: 2025-02-15
author: astriffling, rfetick
"""

from functools import lru_cache
import numpy as np


def normalized_frequency(r_core:float, na:float, wl:float):
    """
    Compute the normalized frequency of the fiber

    Parameters
    ----------
    r_core : float, radius of the fiber core [m].
    na     : float, numerical aperture of the fiber.
    wl     : float, wavelength of interest [m].
    """
    return (2 * np.pi * r_core * na) / wl


def mode_field_radius(*args):
    """
    Compute the fondamental MFR in [m]
    """
    v = normalized_frequency(*args)
    return args[0] * (0.65 + 1.619/v**(3/2) + 2.879/v**6 - (0.016 + 1.561*v**(-7))) 
    

@lru_cache(maxsize=1)
def fundamental_mode(nx:int, sampling:int, *args):
    """
    Compute the fundamental mode of the fiber, using gaussian approximation of
    the mode LP01/TEM00.
    
    Parameters
    ----------
    nx : int, number of pixel of table.
    """
    mfr = mode_field_radius(*args)
    xx,yy = (np.mgrid[0:nx,0:nx]-nx//2) * args[2] / (2 * args[1] * sampling)
    return np.exp(-(xx**2 + yy**2) / (mfr**2))


def coupling_efficiency(field:np.array, *args):
    """
    Compute the SMF coupling efficiency for a focal plane EM field 
    
    From G. P. P. L. Otten et al, A&A, 2021, p4
    https://doi.org/10.1051/0004-6361/202038517

    Parameters
    ----------
    field : array.
    """
    nx = field.shape[0]
    mode = fundamental_mode(nx, *args)
    return np.abs(np.sum(mode * np.conj(field)))**2 / (np.sum(np.abs(mode)**2) * np.sum(np.abs(field)**2))