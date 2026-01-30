"""
Analytical formulas for AO terms variances
"""

import numpy as np
import logging

def var_noll(r0,D):
    """
    Compute the Noll phase variance [rad²], corresponding to the
    expected error without correction. 

    Parameters
    ----------
    r0 : float (>0)
        Fried parameter [m].
    D : float (>0)
        Pupil diameter [m].

    References
    ----------
    Robert J. Noll, "Zernike polynomials and atmospheric turbulence*," 
    J. Opt. Soc. Am. 66, 207-211 (1976)  
    """
    return 1.03*(D/r0)**(5./3.)

def var_fitting(r0, freq_cutoff, dmtype='continuous', lint=0):
    """
    Compute the variance [rad²] of the AO fitting error.
    
    Parameters
    ----------
    r0 : float (>0)
        Fried parameter [m].
    freq_cutoff : float (>0)
        AO cutoff frequency [1/m], typically 1/(2*pitch).
    dmtype : string ('continuous','piston','ptt')
        DM segmentation type.
    lint : float (>=0)
        Turbulence internal scale [m].
    
    References
    ----------
    Thierry Fusco (ONERA), year?, internal document, "Budget OA.docx".
    VERSO team (ONERA), 2021, internal document, "RF-VERSOBC3.docx".
    """
    #TODO: use actuator geometry (Neichel PhD, p148, sec 6.6.3)
    # coef = 0.232 (square) or 0.275 (round) or 0.2 (hexa)
    # below: dmCoef['continuous'] * 2**(5/3) corresponds to round shape
    dmCoef = {'continuous':0.023*6*np.pi/5,
              'ptt':0.18 * 2**(-5./3.),
              'piston':1.26 * 2**(-5./3.)}
    if dmtype not in dmCoef.keys():
        msg = 'Requested <dmtype> has not been implemented'
        logging.error(msg)
        raise ValueError(msg)
    var = dmCoef[dmtype] * (r0*freq_cutoff)**(-5./3.) # fittign error is due to the minimal cutoff between wfs and dm
    var -= dmCoef[dmtype] * (lint/r0)**(5./3.) # remove internal scale
    return var


def var_aliasing(*args, aliasing=0.35, **kwargs):
    """
    Compute the variance [rad²] of the AO aliasing error.
    
    Parameters
    ----------
    *args : see `aovar_fitting`
    aliasing : float (>=0)
        The variance aliasing factor (typically=0.35 for SH).
    **kwargs : see `aovar_fitting`
    
    References
    ----------
    Thierry Fusco (ONERA), year?, internal document, "Budget OA.docx".
    VERSO team (ONERA), 2021, internal document, "RF-VERSOBC3.docx".
    """
    return aliasing * var_fitting(*args, **kwargs)
    

def var_temporal(D, r0, nradial, windspeed, bandwidth):
    """
    Compute the variance [rad²] of the AO temporal error.
    
    Parameters
    ----------
    D : float (>0)
        Pupil diameter [m].
    r0 : float (>0)
        Fried parameter [m].
    nradial : int (>0)
        Number of radial modes corrected by the AO system.
    windspeed : float (>0)
        turbulence equivalent windspeed [m/s].
    bandwidth : float (>0)
        AO loop cutoff bandwidth [Hz].
    
    References
    ----------
    Thierry Fusco (ONERA), year?, internal document, "Budget OA.docx".
    Thierry Fusco (ONERA), 2005, internal document, "AO temporal behavior".
    Jean-Marc Conan, 1994, PhD thesis, section 2.2.4.3
    
    Note
    ----
    This formula does not account for frequency-domain overshoot and might slightly under-estimate the variance
    """
    if (3*bandwidth)<(0.32*(nradial+1)*windspeed/D):
        logging.warning('AO bandwidth is too low, temporal error might be unconsistent')
    s = sum([(n+1)**(-2./3.) for n in range(1,nradial+1)])
    var = 0.045*s*(windspeed/(D*bandwidth))**2 * (D/r0)**(5./3.)
    return var