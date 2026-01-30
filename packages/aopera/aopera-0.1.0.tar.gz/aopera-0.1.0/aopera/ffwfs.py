"""
Created on Fri Nov 11 19:00:43 2022
Fourier-Filtering Wavefront Sensor
@author: v.chambouleyron r.fetick
"""

import numpy as np
from scipy.signal import fftconvolve
from numpy.fft import fft2, fftshift, rfft2, irfft2
from aopera.readconfig import read_config_file, read_config_tiptop, set_attribute
from functools import lru_cache
import logging

#%% FF-WFS BASIC FUNCTIONS

@lru_cache(maxsize=2)
def modulation(nx, rmod, samp):
    """
    Build the modulation ring
    
    Parameters
    ----------
    nx : number of pixels.
    rmod : modulation radius [lambda/D].
    samp : sampling (2=Shannon).
    """
    rmod_px = rmod*samp
    xx,yy = np.mgrid[0:nx,0:nx] - nx//2
    rr = np.sqrt(xx**2+yy**2)
    return (rr<(rmod_px+0.5))*(rr>=(rmod_px-0.5))


@lru_cache(maxsize=2)
def pyramid_mask(nx, nFaces, angle=0.35, theta_ref=0, four_pixels=False):
    """
    Build the pyramid mask
    
    Parameters
    ----------
    nx : number of pixels.
    nFaces : number of faces for the pyramidal mask.
    angle : angle of the pyramid  #TODO: definition? which unit?
    theta_ref : rotation angle of the pyramid faces.
    """
    if four_pixels:
        center = nx//2 - 0.5
    else:
        center = nx//2
    xx,yy = np.mgrid[0:nx,0:nx] - center
    theta = np.mod(np.arctan2(xx,yy)+np.pi-theta_ref, 2*np.pi)
    theta_face = 2*np.pi/nFaces
    msk = np.zeros((nx,nx), dtype=complex)

    for k in range(0,nFaces):
        # Tesselation
        theta_bnd = ((k*theta_face)<=theta) * (theta<((k+1)*theta_face))
        # Tip-Tilt 
        theta_direction = (k+0.5)*theta_face
        c_tip = np.sin(theta_direction+theta_ref)
        c_tilt = np.cos(theta_direction+theta_ref)
        # Complex mask on each face
        msk += theta_bnd * np.exp(2j*np.pi*angle*(c_tip*xx+c_tilt*yy))
        
    return msk
    

def ffwfs_impulse_response(mask, modu, psf):
    """
    Compute the impulse response of a FF-WFS.
    """
    wtot = fftshift(irfft2(rfft2(modu)*rfft2(psf), s=psf.shape))
    wtot = wtot/np.sum(wtot)
    mask_ft = fft2(fftshift(mask)) / np.size(mask)
    return 2*np.imag(np.conj(mask_ft)*fft2(fftshift(mask*wtot)))


def ffwfs_transfer_function(*args, **kwargs):
    """
    Compute the transfer function of a FF-WFS.
    """
    return fftshift(fft2(ffwfs_impulse_response(*args, **kwargs)))


def ffwfs_sensitivity(mask, modu, psf_calib, psf):
    """
    Compute the sensitivity map of a FF-WFS in the (fx,fy) domain.
    
    Parameters
    ----------
    mask : the complex mask of the FF-WFS.
    modu : the modulation circle mask.
    psf_calib : PSF used as reference for calibration.
    psf : current PSF shape to compute optical gains.
    """
    otf_calib = rfft2(psf_calib)
    TF = ffwfs_transfer_function(mask, modu, psf)
    return np.sqrt(np.real(fftshift(irfft2(rfft2(np.abs(TF)**2)*otf_calib, s=psf.shape))))


def ffwfs_reconstructor(*args, thresh=1e-2):
    """
    Compute the reconstructor map of a FF-WFS in the (fx,fy) domain.
    See also: ffwfs_sensitivity
    """
    sensi = ffwfs_sensitivity(*args)
    rec = np.zeros(sensi.shape)
    vld = np.where(sensi>thresh)
    rec[vld] = 1/sensi[vld]
    return rec


def ffwfs_visibility(*args, **kwargs):
    """
    Compute the FF-WFS visible frequencies.
    See also: ffwfs_sensitivity, ffwfs_reconstructor
    """
    sensi = ffwfs_sensitivity(*args)
    rec = ffwfs_reconstructor(*args, **kwargs)
    return np.real(sensi*rec)


def optical_gain(mask, modu, psf_calib, psf_onsky, obj_sky=None, modu_sky=True):
    """
    Compute optical gains map in the (fx,fy) domain.
    
    Parameters
    ----------
    mask : the complex mask of the FF-WFS.
    modu : the modulation circle mask.
    psf_calib : PSF used as reference for calibration.
    psf_onsky : current PSF shape to compute optical gains.
    
    Keywords
    --------
    obj_sky : the extended object image (if applicable)
    modu_sky : should we modulate onsky?
    """
    if modu_sky:
        modu_onsky = modu
    else:
        modu_onsky = modulation(modu.shape[0], 0, 2) # Dirac
    if obj_sky is not None:
        psf_onsky = fftconvolve(psf_onsky, obj_sky/np.sum(obj_sky), mode='same')
    sensi_calib = ffwfs_sensitivity(mask, modu, psf_calib, psf_calib)
    sensi_sky   = ffwfs_sensitivity(mask, modu_onsky, psf_calib, psf_onsky)
    return sensi_sky/sensi_calib


#%% POWER SPECTRAL DENSITIES

def ffwfs_psd_aliasing(fx, fy, psd_input, ffwfsrec, pix):
    """
    Aliasing PSD of a FF-WFS.
    Assume a constant FF-WFS sensitivity at high-frequency.
    
    Parameters
    ----------
    fx : np.array
        The spatial frequencies on X [1/m].
    fy : np.array
        The spatial frequencies on Y [1/m].
    psd_input : function
        The input PSD to be aliased. Should be called as: psd=psd_input(fx,fy)
    ffwfsrec : np.array
        see ffwfs_reconstructor
    pix : float
        Pixel size in the pupil plane [m].
    """
    psd_alias = np.zeros(fx.shape)
    fcut = 1/(2*pix)
    nshift = 3
    ffwfssensi = 1/np.mean(ffwfsrec[0,:]) # constant sensitivity at HF
    psdfilter = np.abs(ffwfsrec*ffwfssensi)**2
    for i in range(-nshift,nshift+1):
        for j in range(-nshift,nshift+1):
            if (i!=0) or (j!=0):
                fx_shift = fx - i*2*fcut
                fy_shift = fy - j*2*fcut
                psd_atmo_shift = psd_input(fx_shift,fy_shift)
                pix_filter = np.sinc(fx_shift*pix)*np.sinc(fy_shift*pix)
                psd_alias += psd_atmo_shift * psdfilter * pix_filter**2
    return psd_alias


def psd_pyrwfs_noise_ron(mask, modu, nphot, var_ron, nssp, psf_onsky, psf_calib):
    """
    Compute the phase PSD due to the AO RON.
    The PSD is given on the (fx,fy) after reconstruction of the phase,
    but before the loop temporal noise filtering.
    
    Parameters
    ----------
    mask : the complex mask of the Pyramid-WFS.
    modu : the modulation circle mask.
    nphot : float (>=0)
        Number of photons available for the neasurement in total.
    var_ron : camera RON in photons unit/frame/px
    nssp = number of pixels in one pupil image
    psf_onsky : current PSF shape to compute sensitivity on-sky.
    psf_calib : PSF used as reference for calibration.
    
    Return
    ------
    the AO error PSD [rad²m²].
    The PSD is given at the measurement wvl !!!
    To get it at the scientific wvl, it should be multiplied by (wvl_wfs/wvl_sci)**2.
    
    References
    ----------
    V. Chambouleyron, 2021, PhD thesis: section 3.1
    """
    sensi_ron = ffwfs_sensitivity(mask,modu,psf_calib,psf_onsky)
    var_ron = (nssp*var_ron)/nphot**2 * (1/sensi_ron)**2
    return var_ron


def psd_pyrwfs_noise_photon(mask, nfaces, modu, nphot, psf_onsky, psf_calib, emccd=False):
    """
    Compute the phase PSD due to the photon noise.
    The PSD is given on the (fx,fy) after reconstruction of the phase,
    but before the loop temporal noise filtering.
    
    Parameters
    ----------
    mask : the complex mask of the Pyramid-WFS.
    nfaces : number of faces of the Pyramid-WFS
    modu : the modulation circle mask.
    nphot : float (>=0)
        Number of photons available for the neasurement in total.
    psf_onsky : current PSF shape to compute sensitivity on-sky.
    
    Keywords
    --------
    emccd : boolean
        Multiply result by excess factor if camera is EMCCD
    
    Return
    ------
    the AO error PSD [rad²m²].
    The PSD is given at the measurement wvl !!!
    To get it at the scientific wvl, it should be multiplied by (wvl_wfs/wvl_sci)**2.
    
    References
    ----------
    V. Chambouleyron, 2021, PhD thesis: section 3.1
    """
    #FIXME: this sensitivity gives correct results wrt OOPAO, but why?
    logging.debug('FFWFS sensitivity has been increased to match OOPAO.')
    sensi_phot = ffwfs_sensitivity(mask,modu,psf_calib,psf_onsky) / np.sqrt(nfaces/2.5) #/ np.sqrt(nfaces) # Rough formula, to be checked more !!!
    var_phot = 1/nphot*(1/sensi_phot)**2
    if emccd:
        var_phot *= 2 # excess factor squared
    return var_phot

#%% FFWFS CLASS
class PWFS:
    def __init__(self, dictionary):
        self.nface = 4
        self.angle = 0.35
        set_attribute(self, dictionary, 'pwfs')
           
    def __repr__(self):
        s  = 'aopera.PWFS\n'
        s += '------------\n'
        s += 'lenslet : %u \n'%self.lenslet
        s += 'ron     : %.1f e-\n'%self.ron
        s += 'EMCCD   : %s\n'%self.emccd
        s += 'R_modul : %.1f l/D\n'%self.modulation
        s += 'OG comp : %s\n'%self.og_compensation
        return s
           
    @staticmethod
    def from_file(filepath, category='pwfs'):
        return PWFS(read_config_file(filepath, category))
    
    @staticmethod
    def from_file_tiptop(filepath):
        return PWFS(read_config_tiptop(filepath)[2])
    
    @staticmethod
    def from_oopao(wfs):
        return PWFS({'lenslet':wfs.nSubap,
                     'ron':wfs.cam.readoutNoise,
                     'emccd':wfs.cam.sensor=='EMCCD',
                     'modulation':wfs.modulation})
    
    def modulation_mask(self, nx, samp):
        return modulation(nx, self.modulation, samp)
    
    def pyramid_mask(self, nx, theta_ref=0):
        return pyramid_mask(nx, self.nface, angle=self.angle, theta_ref=theta_ref)
    
    def sensitivity(self, samp, psf_calib, psf):
        nx = psf.shape[0]
        mask = self.pyramid_mask(nx)
        modu = self.modulation_mask(nx, samp)
        return ffwfs_sensitivity(mask, modu, psf_calib, psf)
    
    def reconstructor(self, samp, psf_calib, thresh=1e-2):
        nx = psf_calib.shape[0]
        mask = self.pyramid_mask(nx)
        modu = self.modulation_mask(nx, samp)
        return ffwfs_reconstructor(mask, modu, psf_calib, psf_calib, thresh=thresh)
    
    def visibility(self, samp, psf_calib, thresh=1e-2):
        nx = psf_calib.shape[0]
        mask = self.pyramid_mask(nx)
        modu = self.modulation_mask(nx, samp)
        return ffwfs_visibility(mask, modu, psf_calib, psf_calib, thresh=thresh)
    
    def optical_gain(self, samp, psf_calib, psf_onsky, **kwargs):
        nx = psf_calib.shape[0]
        mask = self.pyramid_mask(nx)
        modu = self.modulation_mask(nx, samp)
        return optical_gain(mask, modu, psf_calib, psf_onsky, **kwargs)
    
    def psd_aliasing(self, fx, fy, psd_input, ffwfsrec, diameter, nact=np.inf):
        # NOTE : small subtelty on <nact> :
        # if a mode is not shown to the WFS by the DM, it cannot
        # be disantangled by the reconstructor, so it is aliased.
        return ffwfs_psd_aliasing(fx, fy, psd_input, ffwfsrec, diameter/min(self.lenslet,nact-1))
    
    def psd_noise_ron(self, samp, nphot, psf_onsky, psf_calib):
        nx = psf_calib.shape[0]
        mask = self.pyramid_mask(nx)
        modu = self.modulation_mask(nx, samp)
        nssp = np.pi*(self.lenslet/2)**2
        return psd_pyrwfs_noise_ron(mask, modu, nphot, self.ron**2, nssp, psf_onsky, psf_calib)
    
    def psd_noise_photon(self, samp, nphot, psf_onsky, psf_calib):
        nx = psf_calib.shape[0]
        mask = self.pyramid_mask(nx)
        modu = self.modulation_mask(nx, samp)
        return psd_pyrwfs_noise_photon(mask, self.nface, modu, nphot, psf_onsky, psf_calib, emccd=self.emccd)
    