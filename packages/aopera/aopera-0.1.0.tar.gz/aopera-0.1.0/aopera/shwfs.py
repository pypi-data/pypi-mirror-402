"""
Shack-Hartmann WFS
"""

import numpy as np
from aopera.aopsd import aomask_in
from aopera.turbulence import piston_filter
from aopera.readconfig import read_config_file, read_config_tiptop, set_attribute
import logging

#%% SH BASIC FUNCTIONS

def shwfs_sensitivity(fx, fy, dpup):
    """
    Compute the sensitivity map of a SH-WFS in the (fx,fy) domain.
    
    Parameters
    ----------
    fx : np.array
        Array of X frequencies [1/m].
    fy : np.array
        Array of Y frequencies [1/m].
    dpup : float (>0)
        Sub-aperture size [m].
        
    References
    ----------
    Rigaut, 1998, SPIE proceedings
    Neichel, 2008, PhD thesis, pp 138-139, eq 6.10
    Olivier Martin, https://github.com/oliviermartin-lam/P3/blob/main/aoSystem/fourierModel.py
    """
    tfpup = np.sinc(fx*dpup)*np.sinc(fy*dpup) # ok with definition: np.sinc(x)=sinc(pi*x)
    #TODO: check 'dpup' normalisation factor on 'sx' and 'sy'
    logging.debug('Check SH-WFS sensitivity.')
    sx = 2j*np.pi*fx * dpup * tfpup
    sy = 2j*np.pi*fy * dpup * tfpup
    return sx, sy # angle in rad? lambda/dpup ?


def shwfs_reconstructor(*args, thresh=1e-2):
    """
    Compute the reconstructor map of a SH-WFS in the (fx,fy) domain.
    See also: shwfs_sensitivity
    """
    sx,sy = shwfs_sensitivity(*args)
    sensi2 = np.abs(sx)**2 + np.abs(sy)**2
    vld = np.where(sensi2 > thresh**2) # filter frequencies if sensitivity is too low
    recx = np.zeros(sx.shape, dtype=complex)
    recy = np.zeros(sy.shape, dtype=complex)
    recx[vld] = np.conj(sx[vld])/sensi2[vld]
    recy[vld] = np.conj(sy[vld])/sensi2[vld]
    return recx, recy


def shwfs_visibility(*args, thresh=1e-2):
    """
    Compute the SH-WFS visible frequencies.
    See also: shwfs_sensitivity, shwfs_reconstructor
    """
    sx,sy = shwfs_sensitivity(*args)
    rx,ry = shwfs_reconstructor(*args, thresh=thresh)
    return np.real(rx*sx+ry*sy)


def shwfs_spot_fwhm(r0, pitch, wvl, src_size, samp):
    """
    Compute Shack-Hartmann spot FWHM (in units of wvl/D).
    
    Parameters
    ----------
    r0 : float (>0)
        Fried parameter at WFS wavelength [m].
    pitch : float (>0)
        DM actuator pitch [m].
    wvl : float (>0)
        WFS wavelength [m].
    src_size : float (>=0)
        Source physical extension [rad].
    samp : float (>0)
        SH detector sampling.
    """
    SNd2 = (src_size*pitch/wvl)**2 # taille source sur diffraction d'une sous-pup (au carré)
    NpixNd2 = (1.0/samp)**2 # (D*pix)/(2*wvl*F) = taille pixel sur la diffraction d'une sous-pup (au carré)
    NturbNd2 = (pitch/r0)**2 # taille turbulence sur la diffraction d'une sous-pup (au carré)
    return np.sqrt(SNd2 + NpixNd2 + NturbNd2 + 1) # le +1 compte pour la taille diffraction divisée par elle même (au carré)
   

#%% ANALYTICAL ERROR BREAKDOWN

def shwfs_var_ron_subpupil(pix_size, ron_nphot, npix_cog=10):
    """
    Compute the AO variance due to the readout-noise on one subpupil
    """
    return pix_size**2 * np.pi**2 / 3 * ron_nphot**2 * npix_cog**2


def shwfs_var_ron(pix_size, ron_nphot, nradial, bandwidth, freq, npix_cog=10):
    """
    Compute the AO variance due to the readout-noise (propagated in the loop).
    
    Parameters
    ----------
    pix_size : float (>0)
        SH pixel size (in units of wvl/D).
    ron_nphot : float (>=0)
        Pixel read-out noise over number of photons per subaperture per frame.
    nradial : int (>0)
        Number of radial corrected modes.
    bandwidth : float (>0)
        AO loop correction bandwidth [Hz].
    freq : float (>0)
        AO loop camera frequency (framerate) [Hz].
    npix_cog : int (>0)
        Total number of pixels used in the CoG measurement.
    
    Return
    ------
    the AO error variance [rad²].
    The variance is given at the measurement wvl !!!
    To get it at the scientific wvl, it should be multiplied by (wvl_wfs/wvl_sci)**2.
    
    References
    ----------
    Thierry Fusco (ONERA), year?, internal document, "Budget OA.docx".
    VERSO team (ONERA), 2021, internal document, "RF-VERSOBC3.docx".
    Magalie Nicolle, 2007, PhD thesis, "Analyse de front d'onde pour les OA de nouvelle génération". Section 10.2.1.
    """
    var_ron = shwfs_var_ron_subpupil(pix_size, ron_nphot, npix_cog=npix_cog)
    spatial_fltr = sum([0.2/(n+1) for n in range(1,nradial+1)])
    tempo_fltr = 2*bandwidth/freq
    return var_ron * spatial_fltr * tempo_fltr
    

def shwfs_var_photon_subpupil(spot_size, nphot, emccd=False, weight=None):
    """
    Compute the AO variance due to the photon-noise on one subpupil
    
    Parameters
    ----------
    spot_size : float (>0)
        SH spot size (in units of wvl/Dpup).
    nphot : float (>=0)
        Number of photons per subaperture per frame.
    
    Keywords
    --------
    emccd : boolean
        Multiply result by excess factor if camera is EMCCD
    weight : None or float
        Weighting CoG (in units of wvl/Dpup)
    
    Reference
    ---------
    Magalie Nicolle, 2006, PhD thesis, p.234
    """
    var_phot = spot_size**2 * np.pi**2/(2*np.log(2)*nphot)
    if weight is not None:
        var_phot *= ((spot_size**2 + weight**2)/(2*spot_size**2 + weight**2))**2
    if emccd:
        var_phot *= 2 # excess factor squared
    return var_phot


def shwfs_var_photon(spot_size, nphot, nradial, bandwidth, freq, **kwargs):
    """
    Compute the variance of the AO photon-noise error (propagated in the loop).
    
    Parameters
    ----------
    spot_size : float (>0)
        SH spot size (in units of wvl/Dpup).
    nphot : float (>=0)
        Number of photons per subaperture per frame.
    nradial : int (>0)
        Number of radial corrected modes.
    bandwidth : float (>0)
        AO loop correction bandwidth [Hz].
    freq : float (>0)
        AO loop camera frequency (framerate) [Hz].
    
    Keywords
    --------
    See `shwfs_var_photon_subpupil`
    
    Return
    ------
    the AO error variance [rad²].
    The variance is given at the measurement wvl !!!
    To get it at the scientific wvl, it should be multiplied by (wvl_wfs/wvl_sci)**2.
    
    References
    ----------
    Thierry Fusco (ONERA), year?, internal document, "Budget OA.docx".
    VERSO team (ONERA), 2021, internal document, "RF-VERSOBC3.docx".
    Magalie Nicolle, 2007, PhD thesis, "Analyse de front d'onde pour les OA de nouvelle génération". Section 10.2.1, Annexe D.2.1.
    Jean-Marc Conan, 1994, PhD thesis, section 2.2.4.3
    """
    var_phot = shwfs_var_photon_subpupil(spot_size, nphot, **kwargs)
    spatial_fltr = sum([0.2/(n+1) for n in range(1,nradial+1)])
    tempo_fltr = 2*bandwidth/freq
    return var_phot * spatial_fltr * tempo_fltr


#%% POWER SPECTRAL DENSITIES

def shwfs_psd_aliasing(fx, fy, dpup, psd_input):
    """
    Aliasing PSD of a Shack-Hartmann
    
    Parameters
    ----------
    fx : np.array
        The spatial frequencies on X [1/m].
    fy : np.array
        The spatial frequencies on Y [1/m].
    dpup : float
        Size of the subaperture on sky [m].
    psd_input : function
        The input PSD to be aliased by the SH. Should be called as: psd=psd_input(fx,fy)
    """
    rx, ry = shwfs_reconstructor(fx, fy, dpup)
    psd_alias = np.zeros(fx.shape)
    fcut = 1/(2*dpup)
    nshift = 3
    for i in range(-nshift,nshift+1):
        for j in range(-nshift,nshift+1):
            if (i!=0) or (j!=0):
                fx_shift = fx - i*2*fcut
                fy_shift = fy - j*2*fcut
                psd_atmo_shift = psd_input(fx_shift,fy_shift)
                sx_shift, sy_shift = shwfs_sensitivity(fx_shift, fy_shift, dpup)
                psd_rec = psd_atmo_shift * np.abs(sx_shift*rx+sy_shift*ry)**2
                psd_alias += psd_rec
    return psd_alias


def shwfs_psd_noise(fx, fy, aocutoff, var, df, D=None, **kwargs):
    """
    Compute the noise PSD, assuming a f^(-2) power law.
    Valid for a SH-WFS.
    TODO: use a more accurate formula.
    """
    logging.debug('Is SH PSD noise accurate enough ?')
    msk = aomask_in(fx, fy, aocutoff, **kwargs)
    f2 = fx**2 + fy**2
    fnull = np.where(f2==0)
    f2[fnull] = 1 # avoid numerical issue in f=0
    noiseshape = msk / f2
    if D is not None:
        noiseshape *= piston_filter(np.sqrt(fx**2+fy**2), D)
    noiseshape[fnull] = 0
    return var*noiseshape/np.sum(noiseshape*df**2)

#%% SHWFS CLASS
class SHWFS:
    def __init__(self, dictionary):
        set_attribute(self, dictionary, 'shwfs')
           
    def __repr__(self):
        s  = 'aopera.SHWFS\n'
        s += '-------------\n'
        s += 'lenslet : %u \n'%self.lenslet
        s += 'ron     : %.1f e-\n'%self.ron
        s += 'EMCCD   : %s\n'%self.emccd
        s += 'sampling: %.1f\n'%self.samp
        s += 'npix CoG: %u\n'%self.npix_cog
        return s
    
    @staticmethod
    def from_file(filepath, category='shwfs'):
        return SHWFS(read_config_file(filepath, category))
    
    @staticmethod
    def from_file_tiptop(filepath):
        return SHWFS(read_config_tiptop(filepath)[2])
    
    @staticmethod
    def from_oopao(wfs, npix_cog):
        return SHWFS({'lenslet':wfs.nSubap,
                      'ron':wfs.cam.readoutNoise,
                       'emccd':wfs.cam.sensor=='EMCCD',
                       'samp':1.0+wfs.shannon_sampling*1.0,
                       'npix_cog':npix_cog})
    
    def lenslet_valid(self, occ=0):
        return round(np.pi/4*(self.lenslet**2)*(1-occ**2))
    
    def sensitivity(self, fx, fy, diameter):
        return shwfs_sensitivity(fx, fy, diameter/self.lenslet)
    
    def reconstructor(self, fx, fy, diameter):
        return shwfs_reconstructor(fx, fy, diameter/self.lenslet)
    
    def visibility(self, fx, fy, diameter, thresh=1e-2):
        return shwfs_visibility(fx, fy, diameter/self.lenslet, thresh=thresh)
    
    def spot_fwhm(self, r0, diameter, wvl, src_size=0):
        return shwfs_spot_fwhm(r0, diameter/self.lenslet, wvl, src_size, self.samp)
    
    def var_ron_subpupil(self, pix_size, nphot):
        return shwfs_var_ron_subpupil(pix_size, self.ron/nphot, npix_cog=self.npix_cog)
    
    def var_ron(self, nphot, nradial, bandwidth, freq):
        return shwfs_var_ron(1/self.samp, self.ron/nphot, nradial, bandwidth, freq, npix_cog=self.npix_cog)
    
    def var_photon_subpupil(self, spot_size, nphot):
        return shwfs_var_photon_subpupil(spot_size, nphot, emccd=self.emccd, weight=self.weight)
    
    def var_photon(self, spot_size, nphot, nradial, bandwidth, freq):
        return shwfs_var_photon(spot_size, nphot, nradial, bandwidth, freq, emccd=self.emccd, weight=self.weight)
    
    def psd_aliasing(self, fx, fy, diameter, psd_input):
        return shwfs_psd_aliasing(fx, fy, diameter/self.lenslet, psd_input)
    
    def psd_noise(self, fx, fy, aocutoff, var, df, D=None, **kwargs):
        return shwfs_psd_noise(fx, fy, aocutoff, var, df, D=D, **kwargs)