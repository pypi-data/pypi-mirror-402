"""
Convert phase PSD to OTF and to PSF
"""


import numpy as np
from numpy.fft import fft2, ifft2, ifftshift, fftshift
from aopera.utils import aperture
from aopera.readconfig import read_config_file, read_config_tiptop, set_attribute
from aopera.aopsd import piston_filter, psd_wvl_scaling
from functools import lru_cache


def angle2freq(pix_angle,wvl):
    """Computes the PSD frequency step [1/m] to get the corresponding angular
    pixel size [rad] on the PSF."""
    df = pix_angle/wvl
    return df


@lru_cache(maxsize=2)
def otf_diffraction(npix, occ=0, samp=2):
    """
    Compute the diffraction OTF
    
    Parameters
    ----------
    npix : int
        Shape of the output array is (npix,npix).
    
    Keywords
    --------
    occ : float
        Eventual central obstruction (0<=occ<1).
    samp : float
        Required sampling. Must verify the condition samp>=2.
    """
    if samp<2:
        raise ValueError("Sampling cannot be less than 2.0")
    aper = aperture(npix, samp=samp, occ=occ)
    otf = ifftshift(ifft2(np.abs(fft2(aper))**2)) / np.sum(aper)
    return otf


def otf2psf(otf):
    """Get the PSF for a given OTF"""
    psf = np.abs(np.real(fftshift(ifft2(fftshift(otf)))))
    return psf


@lru_cache(maxsize=2)
def psf_diffraction(npix, occ=0, samp=2):
    """Compute the diffraction PSF"""
    return otf2psf(otf_diffraction(npix, occ=occ, samp=samp))


def psd2otf(psd, df, psdsum=None):
    """
    Get the OTF for a given PSD
    
    Parameters
    ----------
    psd : np.array
        The PSD 2D array.
    df : float
        Frequency step of the PSD array [1/m].
        
    Keywords
    --------
    psdsum : float, None
        Integral of the PSD.
        If psdsum=None, the integral is the numerical sum on the array.
        The PSF is then of unit energy, since max(otf)=1.
    """
    Bphi = ifftshift(np.real(fft2(fftshift(psd)))) * df**2
    if psdsum is None:
        psdsum = np.sum(psd) * df**2
    otf = np.exp(-psdsum+Bphi)
    return otf


def otf_jitter(freq, rms):
    """
    Give the Gaussian jitter OTF from its jitter RMS value.
    Not tested yet, do not use.
    """
    return np.exp(-0.5*(2*np.pi*freq*rms)**2)

#%% MODES and DEFORMABLE MIRROR
def number_modes(nact, occ=0):
    """Compute the number of corrected modes"""
    surf_ratio = np.pi*(1-occ**2)/4 #between occulted disk and square
    nact_total = nact**2
    return int(round(nact_total * surf_ratio))
    
    
def number_radial(nact, occ=0):
    """Compute the number of corrected radial modes"""
    nmode = number_modes(nact, occ=occ)
    return int(round(np.sqrt(2*nmode)-0.5)) # nr(nr+1)/2 = nmode


def controllability(fx, fy, D, actuator, nmode_ratio=1):
    """Return a DM frequency map that is 1 on the corrected frequencies, 0 otherwise"""
    cutoff = (actuator-1)/(2*D)
    if cutoff <= 0: # no DM case
        return np.zeros(fx.shape)
    rr = np.sqrt(fx**2+fy**2)
    if nmode_ratio >1:
        raise ValueError('nmode_ratio cannot be above 1.')
    thresh = np.pi/4
    if nmode_ratio > thresh: # smooth transition from square to circle
        modal_radial_cutoff = (1-nmode_ratio)/(1-thresh) * (rr <= cutoff)
        actuator_square_cutoff = (nmode_ratio-thresh)/(1-thresh) * (np.abs(fx)<=cutoff)*(np.abs(fy)<=cutoff)
        return actuator_square_cutoff + modal_radial_cutoff
    else:
        nact_equiv = np.sqrt(nmode_ratio/thresh)
        return (rr <= (nact_equiv*cutoff)).astype(float)


#%% TELESCOPE CLASS
class Pupil:
    def __init__(self, dictionary):
        # self.jitter = 0 # [nm RMS]
        # self.jitter_angle = 0 # [deg]
        # self.jitter_freq = 0 # [Hz]
        set_attribute(self, dictionary, 'pupil')
    
    def __repr__(self):
        s  = 'aopera.PUPIL\n'
        s += '-------------\n'
        s += 'diameter   : %.1f m\n'%self.diameter
        s += 'occultation: %u %%\n'%(100*self.occultation)
        s += 'nb act     : %u\n'%self.nact
        s += 'mode ratio : %.2f\n'%self.nmode_ratio
        s += 'ncpa       : %u nm\n'%self.ncpa
        # if self.jitter:
        #     s += 'jitter     : %u nm\n'%self.jitter
        return s
    
    @staticmethod
    def from_file(filepath, category='pupil'):
        return Pupil(read_config_file(filepath, category))
    
    @staticmethod
    def from_file_tiptop(filepath):
        return Pupil(read_config_tiptop(filepath)[0])
    
    @staticmethod
    def from_oopao(tel, dm, M2C):
        return Pupil({'diameter':tel.D,
                       'occultation':tel.centralObstruction,
                       'nact':dm.nAct,
                       'nmode_ratio':M2C.shape[1]/M2C.shape[0]})
    
    @property
    def surface(self):
        return np.pi * (self.diameter/2)**2 * (1-self.occultation**2)
    
    @property
    def mode_max(self):
        return number_modes(self.nact, occ=self.occultation)
    
    @property
    def radial_max(self):
        return number_radial(self.nact, occ=self.occultation)
    
    @property
    def pitch_dm(self):
        return self.diameter/(self.nact-1)
    
    def pitch_wfs(self, nb_lenslet):
        return self.diameter/nb_lenslet
    
    def pitch_ao(self, nb_lenslet):
        return max(self.pitch_dm, self.pitch_wfs(nb_lenslet))
    
    def cutoff_frequency(self, nb_lenslet):
        return 1/(2*self.pitch_ao(nb_lenslet))
    
    def frequency_step(self, samp):
        return 1/(samp*self.diameter)
    
    def frequency_grid(self, nx, samp):
        return (np.mgrid[0:nx,0:nx]-nx//2) * self.frequency_step(samp)
    
    def piston_filter(self, nx, samp):
        fx,fy = self.frequency_grid(nx, samp)
        return piston_filter(np.sqrt(fx**2+fy**2), self.diameter)
    
    def otf_diffraction(self, nx, samp):
        return otf_diffraction(nx, occ=self.occultation, samp=samp)
    
    def psf_diffraction(self, nx, samp):
        return psf_diffraction(nx, occ=self.occultation, samp=samp)
    
    def controllability(self, fx, fy):
        return controllability(fx, fy, self.diameter, self.nact, nmode_ratio=self.nmode_ratio)
    
    def otf_ao(self, psd, samp, wvl_scale=1):
        if wvl_scale == 1:
            otf_diff = self.otf_diffraction(psd.shape[0], samp)
            df = self.frequency_step(samp)
            return psd2otf(psd, df)*otf_diff
        else:
            psd_scale = psd_wvl_scaling(psd, 1/wvl_scale)
            samp_scale = samp * wvl_scale
            return self.otf_ao(psd_scale, samp_scale)
    
    def psf_ao(self, *args, **kwargs):
        return otf2psf(self.otf_ao(*args, **kwargs))
    