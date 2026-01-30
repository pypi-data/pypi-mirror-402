"""
General functions to compute PSD terms of the AO system
"""

import numpy as np
from scipy.special import j1
from aopera.turbulence import propagation_spherical_coord, vonkarmanshape, phase_psd, cn2dh_to_r0
from aopera.zernike import zernike_fourier
from scipy.interpolate import RegularGridInterpolator
import logging

def piston_filter(ff, D):
    """Piston filtering function, to be applied on a PSD"""
    ff = np.pi*D*ff
    out = np.zeros_like(ff)
    idx = (ff!=0)
    out[idx] = 1 - (2*j1(ff[idx])/(ff[idx]))**2
    return out


def aomask_in(fx, fy, aocutoff, shape='circle'):
    """Mask that is equal to 1 for the corrected frequencies."""
    print(DeprecationWarning('Function `aomask_in` is deprecated, use `controllability`.'))
    if shape=='circle':
        msk = ((fx**2 + fy**2) < aocutoff**2)
    elif shape=='square':
        msk = (np.abs(fx)<aocutoff)*(np.abs(fy)<aocutoff)
    else:
        raise ValueError('Your mask shape is not available')
    return msk


def aomask_out(*args, **kwargs):
    """
    Mask that is equal to 1 outside the correction area.
    See `aomask_in` for input arguments.
    """
    return 1 - aomask_in(*args, **kwargs)


def psd_wvl_scaling(psd_1, w1_over_w2):
    """
    Scale a PSD [rad²m²] from one wavelength to another.
    The frequecy step verifies df_2 = df_1 * w1_over_w2
    
    Parameters
    ----------
    psd_1 : np.array
        The PSD given at wvl_1
    w1_over_w2 : float
        Ratio wvl_1 / wvl_2
    """
    nx = psd_1.shape[0]
    xx_1 = np.arange(nx)-nx//2
    xx_2 = np.tile(xx_1 * w1_over_w2, (nx,1))
    interp = RegularGridInterpolator((xx_1,xx_1), psd_1, bounds_error=False, fill_value=0)
    psd_2 = interp((xx_2.T,xx_2)) * w1_over_w2**2
    return psd_2


def psd_fitting(fx, fy, psdatmo, aocutoff, **kwargs):
    """
    Return the fitting error of the AO system.
    
    Parameters
    ----------
    fx : np.array
        The spatial frequencies on X [1/m].
    fy : np.array
        The spatial frequencies on Y [1/m].
    psdatmo : np.array
        The atmospherical PSD (for example Von-Karman) at the corresponding frequencies.
    aocutoff : float
        The AO cutoff frequency [1/m]
    """
    return psdatmo * aomask_out(fx, fy, aocutoff, **kwargs)


def psd_aliasing(fx, fy, aocutoff, var, df, **kwargs):
    """
    Return the aliasing error of the AO system.
    The aliasing PSD is considered as constant on the corrected area.
    
    Parameters
    ----------
    fx : np.array
        The spatial frequencies on X [1/m].
    fy : np.array
        The spatial frequencies on Y [1/m].
    aocutoff : float
        The AO cutoff frequency [1/m].
    var : float
        The required aliasing variance [rad²].
    df : float
        Frequency step of the `freq` array [1/m].
    """
    # TODO: remove this function and use dedicated aliasing functions from SH-WFS and FF-WFS
    print(DeprecationWarning('The generic function `psd_aliasing` is deprecated, use aliasing from shwfs or ffwfs instead.'))
    mask = aomask_in(fx, fy, aocutoff, **kwargs)
    f2 = fx**2 + fy**2
    mask[np.where(f2==0)] = 0
    psd = var*mask/(np.sum(mask)*df**2)
    return psd
    

def psd_temporal(fx, fy, wspd, psdatmo, cltf, aocutoff=None, wnd_angle=0, **kwargs):
    """
    Compute servolag error of the AO system.
    Computation is based on input PSD filtered by the ETF.
    
    Parameters
    ----------
    fx : np.array
        The spatial frequencies on X [1/m].
    fy : np.array
        The spatial frequencies on Y [1/m].
    wspd : float
        Turbulence equivalent windspeed [m/s].
    psdatmo : np.array
        The turbulent phase PSD [eg. rad2 m2].
    cltf : callable
        Closed-loop transfer function, to be evaluated on temporal frequencies (Hz).
    aocutoff : float
        The AO cutoff frequency [1/m].
    """
    ft = (fx*np.cos(wnd_angle)+fy*np.sin(wnd_angle))*wspd
    ftnull = np.where(ft==0)
    ft[ftnull] = 1e-8 # avoid numerical issue in f=0
    etf2 = np.abs(cltf(ft))**2.0
    if aocutoff is not None:
        mask = aomask_in(fx, fy, aocutoff, **kwargs)
    else:
        mask = np.ones(fx.shape)
    mask[ftnull] = 0
    return psdatmo*etf2*mask


def air_refractive_index(wvl_um):
    return 1 + 0.0579/(238.02-wvl_um**(-2)) + 0.0017/(57.4-wvl_um**(-2))


def psd_chromatic_filter(wvl_wfs_nm, wvl_sci_nm):
    n_wfs = air_refractive_index(wvl_wfs_nm*1e-3)
    n_sci = air_refractive_index(wvl_sci_nm*1e-3)
    return (1-(n_sci-1)/(n_wfs-1))**2


def psd_ncpa(ncpa_rms, freq, df, diameter, ncpa_exp=2.2):
    """
    Compute the PSD from Non-Common Path Aberrations.
    
    Parameters
    ----------
    ncpa_rms : float
        RMS value of NCPA [unit]. Output PSD is given in [unit²m²].
    freq : np.array
        Array of spatial frequencies [1/m].
    df : float
        Frequency step [1/m].
    diameter : float
        Telescope diameter [m].
    """
    pstflt = piston_filter(freq, diameter)
    ncpa = pstflt / (1e-8 + freq**ncpa_exp)
    ncpa_total = np.sum(ncpa)*df**2
    return ncpa * ncpa_rms**2 / ncpa_total


def psd_jitter(jitter_x_rms, jitter_y_rms, npix, samp):
    """
    Compute jitter PSD
    
    Parameters
    ----------
    jitter_x_rms : float
        RMS value [unit] of jitter along X. Output PSD is given in [unit²m²].
    jitter_y_rms : float
        RMS value [unit] of jitter along Y.
    npix : int
        Number of pixels of the output array.
    samp : float
        PSF sampling.
    """
    zx = np.abs(zernike_fourier(1, -1, npix, samp))**2
    return zx * jitter_x_rms**2 + zx.T * jitter_y_rms**2


def psd_anisoplanetism(fx, fy, cn2dh, alt, wvl, theta_x, theta_y, lext=np.inf, lint=0, zenith=0):
    """
    Compute the anisoplanetism PSD, for a source located at infinite distance.
    
    Parameters
    ----------
    fx : np.array(float)
        Array of spatial frequencies on the X axis [1/m].
    fy : np.array(float)
        Array of spatial frequencies on the Y axis [1/m].
    cn2dh : list(float)
        List of the cn2*dh of the atmosphere layers [m^(1/3)].
    alt : list(float)
        List of the altitudes corresponding to cn2dh [m].
        The zero altitude is the pupil of the telescope.
    wvl : float
        Wavelength of wavefront [m].
    theta_x : float
        Separation angle along the X coordinate [rad].
    theta_y : float
        Separation angle along the Y coordinate [rad].
        
    Reference
    ---------
    Rigaut, 1998, SPIE Vol. 3353
    """
    
    psd = np.zeros(fx.shape)
    psd_norm = phase_psd(np.sqrt(fx**2+fy**2), 1, lext=lext, lint=lint)
    
    for i in range(len(alt)):
        r0 = cn2dh_to_r0([cn2dh[i]], wvl, zenith=zenith)
        psd += psd_norm * r0**(-5/3) * 2 * (1-np.cos(2*np.pi*alt[i]*(theta_x*fx+theta_y*fy)))
        
    return psd


def psd_anisoplanetism_extended_object(fx, fy, cn2dh, alt, dpup, wvl, objsize, src_alt=np.inf, src_zenith=0, lext=np.inf, lint=0, return_all=False):
    """
    Return the phase, scintillation and coupling anisoplanetism PSD from the WFS measurement on extended object.
    The result is a PSD array in units of rad²m², evaluated on [fx,fy].
    
    Parameters
    ----------
    fx : np.array(float)
        Array of spatial frequencies on the X axis [1/m].
    fy : np.array(float)
        Array of spatial frequencies on the Y axis [1/m].
    cn2dh : list(float)
        List of the cn2*dh of the atmosphere layers [m^(1/3)].
    alt : list(float)
        List of the altitudes corresponding to cn2dh [m].
        The zero altitude is the pupil of the telescope.
    dpup : float
        Size of a subpupil of the WFS [m].
    wvl : float
        Wavelength of wavefront sensing [m].
    objsize : float
        Characterisitic apparent size of a square-like object [rad].
    src_alt : float
        Source altitude [m].
    src_zenith : float
        Source zenital angle [rad].
        A zero angle means a source at zenith.
    lext : float
        Atmospheric turbulence external scale [m].
    lint : float
        Atmospheric turbulence internal scale [m].
    return_all : boolean
        Activate to return all the PSD terms.
    
    Note
    ----
    Multiply the result by `(wvl_wfs/wvl_sci)**2` to get the PSD at the science wavelength.
    Multiply the result by mask of AO corrected frequencies, see the function `aomask_in`.
    
    Reference
    ---------
    Vedrenne et al, 2007, JOSAA.
    """
    
    nlayer = len(cn2dh)
    npix = fx.shape[0]
    k0 = 2*np.pi/wvl
    
    freq = np.sqrt(fx**2+fy**2)
    vldx = np.where(fx!=0)
    vldy = np.where(fy!=0)
    
    tfpup = np.sinc(fx*dpup)*np.sinc(fy*dpup) # ok with definition: np.sinc(x)=sinc(pi*x)

    psd = np.zeros((nlayer,npix,npix))
    FF = np.zeros((nlayer,npix,npix))
    GG = np.zeros((nlayer,npix,npix))
    HH = np.zeros((nlayer,npix,npix), dtype=complex)
    Dx = np.zeros((nlayer,npix,npix), dtype=complex)
    Dy = np.zeros((nlayer,npix,npix), dtype=complex)
    EE = np.zeros((nlayer,npix,npix), dtype=complex)

    xx,yy = np.mgrid[0:npix,0:npix] - npix//2

    fconv = k0*dpup # facteur de conversion angle vers phase (cf. codes IDL)

    for i in range(nlayer):
        if (alt[i]>0) and (alt[i]<src_alt):
            ze_z = 1/propagation_spherical_coord(alt[i], src_alt, backward=True)
            ze = alt[i]*ze_z / np.cos(src_zenith)
            u = np.pi*ze*wvl*freq**2
            vk = vonkarmanshape(freq, lext=lext*ze_z, lint=lint*ze_z)
            psd[i,...] = vk * k0**2 *0.033*cn2dh[i]*ze_z**(-5/3) * (2*np.pi)**(-2/3) # [eq A4]*dh
            psd[i,...] = psd[i,...]/np.cos(src_zenith) # zenithal angle effect on cn2dh
            FF[i,...] = 4*psd[i,...] * tfpup**2 * np.sin(u)**2 # [eq A3]
            GG[i,...] = (2*np.pi*dpup)**2 * psd[i,...] * tfpup**2 * np.cos(u)**2 # [eq A7]
            HH[i,...] = 2j*np.pi*dpup * psd[i,...] * tfpup**2 * np.sin(2*u) # [eq A9]/fconv car fconv porté par Dx
            Dx[i,...][vldx] = 1j*fconv*np.sinc(ze*fy[vldx]*objsize)/(2*np.pi*ze*fx[vldx])*(np.cos(np.pi*ze*fx[vldx]*objsize)-np.sinc(ze*fx[vldx]*objsize))
            Dy[i,...][vldy] = 1j*fconv*np.sinc(ze*fx[vldy]*objsize)/(2*np.pi*ze*fy[vldy])*(np.cos(np.pi*ze*fy[vldy]*objsize)-np.sinc(ze*fy[vldy]*objsize))
            EE[i,...] = np.sinc(ze*fx*objsize)*np.sinc(ze*fy*objsize) - 1
        
    psd_aa = {}
    psd_aa["xx"] = np.sum(np.conjugate(Dx)*Dx*FF,axis=0)
    psd_aa["xy"] = np.sum(np.conjugate(Dx)*Dy*FF,axis=0)
    psd_aa["yy"] = np.sum(np.conjugate(Dy)*Dy*FF,axis=0)

    psd_cc = {}
    psd_cc["xx"] = np.sum(GG*np.abs(EE)**2,axis=0)*fx*fx
    psd_cc["xy"] = np.sum(GG*np.abs(EE)**2,axis=0)*fx*fy
    psd_cc["yy"] = np.sum(GG*np.abs(EE)**2,axis=0)*fy*fy

    psd_acca = {}
    psd_acca["xx"] = np.sum((fx*EE*np.conjugate(Dx)+fx*Dx*np.conjugate(EE))*HH,axis=0)
    psd_acca["xy"] = np.sum((fx*EE*np.conjugate(Dy)+fy*Dx*np.conjugate(EE))*HH,axis=0)
    psd_acca["yy"] = np.sum((fy*EE*np.conjugate(Dy)+fy*Dy*np.conjugate(EE))*HH,axis=0)

    Mx = 2j*np.pi*fx*tfpup
    My = 2j*np.pi*fy*tfpup
    
    logging.debug('Measurement anisoplanetism has been scaled to match IDL codes.')
    Mx *= dpup * np.pi/2 #FIXME : factor to match IDL codes
    My *= dpup * np.pi/2 #FIXME : factor to match IDL codes

    def reconstructor(psd):
        """Slope PSD to phase PSD [eq B5]"""
        denom = np.abs(Mx)**4 + np.abs(My)**4
        vld = np.where(denom>0)
        not_vld = np.where(denom==0)
        psd_wfe = np.real(psd["xx"]*np.abs(Mx)**2 + psd["yy"]*np.abs(My)**2 + 2*np.conjugate(Mx)*My*psd["xy"])
        psd_wfe[vld] /= denom[vld]
        psd_wfe[not_vld] = 0
        return psd_wfe

    psd_wfe_aa = reconstructor(psd_aa)
    psd_wfe_cc = reconstructor(psd_cc)
    psd_wfe_acca = reconstructor(psd_acca)
    psd_wfe_tot = psd_wfe_aa + psd_wfe_cc + psd_wfe_acca
    if return_all:
        return psd_wfe_tot, psd_wfe_aa, psd_wfe_cc, psd_wfe_acca
    return psd_wfe_tot
