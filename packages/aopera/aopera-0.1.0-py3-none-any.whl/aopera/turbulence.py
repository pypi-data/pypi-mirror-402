"""
Set of functions related to turbulence
"""

import numpy as np
import logging
from scipy.special import j1
from aopera.utils import rad2arcsec, arcsec2rad
from aopera.readconfig import read_config_file, read_config_tiptop, set_attribute, INFO_ATMO_CN2DH


WVL_REF_SEEING = 500e-9


def random_noise(shp):
    """Compute a complex noise for a given shp=(nx,ny). See also `random_sample`."""
    # fft2(randn(*sh)) / npix * np.sqrt(2) # other method
    return np.random.randn(*shp)+1j*np.random.randn(*shp)


def random_sample(psd, L, noise=None, t_vxy=None):
    """
    Generate a random screen from a given PSD.
    
    Parameters
    ----------
    psd : np.array
        The PSD array, with null frequency at the center of the array.
    L : float
        Physical extent of the array.
        
    Keywords
    --------
    noise : None or np.array
        Define an array if you want to use the same generating noise.
        See also `random_noise`.
    t_vxy : (float,float)
        The list of (time*Vx,time*Vy) to get frozen flow translation.
    """
    #np.random.seed(seed=seed) # if you want to use same seed...
    if noise is None:
        noise = random_noise(np.shape(psd))
    tab = np.fft.fftshift(np.sqrt(psd)) * noise / L
    if t_vxy is not None:
        if max(t_vxy)>(L/2):
            logging.warning('Time exceeds array size, random sample will suffer circular roll.')
        nx,ny = np.shape(psd)
        xx,yy = np.mgrid[0:nx,0:ny] * 1.0
        xx = xx - nx//2
        yy = yy - ny//2
        tab *= np.exp(2j*np.pi*(t_vxy[0]*xx+t_vxy[1]*yy)/L)
    tab = np.real(np.fft.ifft2(tab)) * np.size(psd)
    return tab


def propagation_spherical_coord(h, L, backward=False):
    """
    Compute the spherical reduced coordinate
    
    If the distance is np.inf (plane wave), then return an array of ones like `h`.
    
    Parameters
    ----------
    h : np.array
        Array of the coordinates along the propagation path.
    L : float
        Distance between source and observer.
    
    Keywords
    --------
    backward : bool (default=False)
        If False, coordinates are increasing from source to observer.
        If True, coordinates are increasing from observer to the source (e.g. altitudes).
    
    Reference
    ---------
    R. Sasiela, 1995, Electromagnetic wave propagation in turbulence (Chapter 2)
    """
    if L==np.inf:
        return np.ones_like(h)
    if backward:
        u = (L-h)/L
    else:
        u = h/L    
    if (np.min(u)<0) or (np.max(u)>1):
        raise ValueError("Incompatible values between array of coordinates and source distance. You must ensure 0<=h<=L")
    return u


def cn2dh_to_r0sph(alt, cn2dh, wvl, src_alt, zenith=0):
    """
    Compute the spherical r0 from a Cn²*dh profile.
    
    Parameters
    ----------
    alt : np.array
        Values of altitudes corresponding to the `cn2dh` [m].
    cn2dh : np.array
        Values of the Cn²*dh profile at the different altitudes [m^(1/3)].
    wvl : float
        Observing wavelength [m].
    src_alt : float, int
        Altitude of the source [m].
        
    Keywords
    --------
    zenith : float (default=0 for zenith)
        Zenital angle in the range [-pi/2,pi/2] radians.
        
    Reference
    ---------
    T. Fusco, 2000, PhD thesis, eq.1.10 (for plane wave only)
    """
    cosz = np.cos(zenith)
    if cosz<=0:
        raise ValueError("Zenital angle must be between -pi/2 and pi/2")
    if len(cn2dh)!=len(alt):
        raise ValueError("`cn2dh` and `alt` must have same number of elements")
    k2 = (2*np.pi/wvl)**2.0
    u = propagation_spherical_coord(alt, src_alt, backward=True)
    return (k2*0.42/cosz*np.sum(cn2dh * u**(5./3.)))**(-3./5.)


def cn2dh_to_r0(cn2dh, wvl, zenith=0):
    """
    Compute the r0 from a Cn²*dh profile.

    Parameters
    ----------
    cn2dh : float, list, tuple or np.array
        Values of the Cn²*dh profile at the different altitudes [m^(1/3)].
    wvl : float
        Observing wavelength [m].
        
    Keywords
    --------
    zenith : float (default=0 for zenith)
        Zenital angle in the range [-pi/2,pi/2] radians.
        
    Note
    ----
    This function is just a wrapper around `cn2dh_to_r0sph` for a source
    located at infinite altitude.
    """
    src_alt = np.inf
    alt = np.zeros_like(cn2dh)
    return cn2dh_to_r0sph(alt, cn2dh, wvl, src_alt, zenith=zenith)


def equivalent_altitude(cn2dh, altitude):
    """Get the equivalent altitude from a profile"""
    return (np.sum(cn2dh*(altitude)**(5/3))/np.sum(cn2dh))**(3/5)


def equivalent_wind_speed(cn2dh, wind_speed):
    """Get the equivalent wind speed from a profile"""
    return (np.sum(cn2dh*(wind_speed)**(5/3))/np.sum(cn2dh))**(3/5)


def coherence_time(r0, wspd):
    """Coherence time of turbulence (often called tau_0)"""
    return 0.314*r0/wspd


def isoplanetic_angle(r0, alt):
    """Isoplanetic angle of turbulence (often called theta_0)"""
    return 0.314*r0/alt


def r0_to_cn2dh(r0, wvl, zenith=0):
    """
    Compute the equivalent mono-layer Cn²*dh from the r0 value.
    
    Parameters
    ----------
    r0 : float
        Fried parameter [m].
    wvl : float
        Observing wavelength [m].
        
    Keywords
    --------
    zenith : float (default=0 for zenith)
        Zenital angle in the range [-pi/2,pi/2] radians.
    """
    cosz = np.cos(zenith)
    if cosz<=0:
        raise ValueError("Zenital angle must be between -pi/2 and pi/2")
    k2 = (2*np.pi/wvl)**2.0
    return r0**(-5./3.) * cosz/0.42/k2


def seeing_to_cn2dh(seeing):
    """Compute Cn2*dh (mono-layer) for a given seeing [arcsec]"""
    r0_ref = WVL_REF_SEEING / arcsec2rad(seeing)
    return r0_to_cn2dh(r0_ref, WVL_REF_SEEING)


def cn2dh_to_seeing(cn2dh):
    """Compute the seeing [arcsec] from a Cn2*dh profile"""
    r0_ref = cn2dh_to_r0(cn2dh, WVL_REF_SEEING)
    return rad2arcsec(WVL_REF_SEEING/r0_ref)


def r0_to_seeing(r0, wvl, zenith=0):
    """Convert r0 [m] to seeing [arcsec]"""
    cn2dh = r0_to_cn2dh(r0, wvl, zenith=zenith)
    return cn2dh_to_seeing([cn2dh])


def piston_filter(freq, D):
    """
    Filter piston mode from a PSD.
    Assumes a non-obstructed circular pupil.
    
    Parameters
    ----------
    freq : np.array
        The spatial frequencies [1/m].
    D : float
        Diameter of the telescope [m].
    
    Reference
    ---------
    https://github.com/oliviermartin-lam/P3/blob/main/aoSystem/FourierUtils.py
    """
    ff = np.pi*D*freq
    out = np.zeros_like(ff)
    idx = (ff!=0)
    out[idx] = 1 - 4*(j1(ff[idx])/ff[idx])**2
    return out


def vonkarmanshape(freq, lext=np.inf, lint=0.0, diameter=None):
    """
    Return the Von-Karman shape without normalisation multiplicative factors.
    
    If you provide `k=2*pi*f` instead of an array of frequencies, the `lext` and `lint`
    parameters must be divided by (2*pi) since they are often given in frequency units
    and not pulsation units.
    
    Parameters
    ----------
    freq : np.array
        The spatial frequencies [1/m].
        
    Keywords
    --------
    lext : float
        Von-Karman external scale [m].
    lint : float
        Modified Von-Karman internal scale [m].
    diameter : None or float
        Pupil diameter, to filter piston from Von-Karman PSD
    """
    if lext<lint:
        raise ValueError("Von-Karman external scale cannot be smaller than internal scale")
    idx_null = np.where(freq==0)
    freq[idx_null] = np.finfo(float).eps
    vks = (freq**2 + (1/lext)**2)**(-11./6.) * np.exp(-(freq*lint)**2.0)
    freq[idx_null] = 0
    vks[idx_null] = 0
    if diameter is not None:
        vks *= piston_filter(freq, diameter)
    return vks


def phase_psd(freq, r0, **kwargs):
    """
    Compute the turbulent phase spatial PSD.
    By default, the Kolmogorov spectrum (lext=inf,lint=0) is generated.
    
    Parameters
    ----------
    freq : float, np.array
        Spatial frequencies for which to compute the phase PSD [1/m].
    r0 : float
        Fried parameter [m].
        
    Keywords
    --------
    See 'vonkarmanshape'
    """
    return 0.023*r0**(-5./3.) * vonkarmanshape(freq, **kwargs)


def logamp_psd(freq, alt, cn2dh, wvl, lext=np.inf, lint=0.0, src_alt=np.inf, zenith=0):
    """
    Compute the log-amplitude spatial PSD.
    By default, the Kolmogorov spectrum (lext=inf,lint=0) is generated.
    
    Parameters
    ----------
    freq : float, np.array
        Spatial frequencies for which to compute the phase PSD [1/m].
    alt : list, tuple or np.array
        Values of altitudes corresponding to the `cn2dh` [m].
    cn2dh : np.array
        Values of the Cn²*dh profile at the different altitudes [m^(1/3)].
    wvl : float
        Observing wavelength [m].
        
    Keywords
    --------
    lext : float, np.inf (default=np.inf)
        External scale [m].
    lint : float (default=0.0)
        Internal scale [m].
    zenith : float (default=0)
        Zenith angle [rad].
    """
    #if src_alt<_np.inf: raise ValueError("The code has not been debugged for spherical wave (src_alt<np.inf). Error in the Mahe SPIE article according to JM.Conan")
    omega = 2*np.pi*freq
    if len(alt)!=len(cn2dh):
        raise ValueError("Arrays `cn2dh` and `alt` must have same number of elements")
    k0 = 2*np.pi/wvl
    factor = 0.207 * (k0**2) * (4*np.pi**2) # last factor to transform pulsation to frequency
    res = np.zeros_like(omega)
    u = propagation_spherical_coord(alt, src_alt, backward=True)
    if src_alt==np.inf:
        vonk = vonkarmanshape(omega,lext=lext/(2*np.pi),lint=lint/(2*np.pi)) # compute once to save time
    for i in range(len(alt)):
        if u[i]!=0: # not at the source because of terms in 1/u, but PSD tends mathematically to zero
            if src_alt<np.inf:
                vonk = vonkarmanshape(omega/u[i],lext=lext/(2*np.pi),lint=lint/(2*np.pi)) # compute in loop
            sin2 = np.sin((alt[i]/np.cos(zenith)/u[i])*omega**2/(2*k0))**2
            res += cn2dh[i] * vonk / (u[i]**2) * sin2
    return factor * res


def logamp_variance(alt, cn2dh, wvl, src_alt=np.inf, zenith=0):
    """
    Log-amplitude variance, assuming Kolmogorov spectrum.
    
    Reference
    ---------
    Sasiela, Electromagnetic wave propagation in turbulence, Eq. 2.128
    """
    k0 = 2*np.pi/wvl
    u = propagation_spherical_coord(alt, src_alt, backward=True)
    return 0.5631 * k0**(7/6) * np.sum(cn2dh*(u*alt/np.cos(zenith))**(5/6))


def check_psd_resolution(samp, nx, D, lext=np.inf, lint=0):
    """Check if Von-Karman PSD is numerically consistent."""
    error = False
    df = 1/(samp*D) # numerical frequency step [1/m]
    
    if (1/lext < df) and (1/D < df):
        logging.warning('The numerical `df` step is the external scale. Consider increasing `samp`.')

    if lint < 1/(df*nx/2):
        logging.warning('The array size is the internal scale. Consider increasing `nx` or decreasing `samp`.')
        
    return error

#%% ATMOSPHERE CLASS
class Atmosphere:
    """
    Representation of a turbulent atmosphere.
    So far, it can only compute parameters for a source located at infinity.
    """
    
    def __init__(self, dictionary):
        self.lint = 0
        if not 'seeing' in dictionary.keys():
            cn2dh = INFO_ATMO_CN2DH['cn2dh'][0](dictionary['cn2dh'])
            dictionary['seeing'] = str(cn2dh_to_seeing(cn2dh))
            dictionary['cn2dh_ratio'] = str(list(cn2dh/np.sum(cn2dh)))
        set_attribute(self, dictionary, 'atmosphere_seeing')
        if np.abs(np.sum(self.cn2dh_ratio)-1) > 0.01:
            raise ValueError('sum(cn2dh_ratio) should be close to unity.')
    
    def __repr__(self):
        s  = 'aopera.ATMOSPHERE\n'
        s += '------------------\n'
        s += 'seeing    : %.2f arcsec\n'%self.seeing
        s += 'nb layer  : %u\n'%self.nlayer
        s += 'altitude  : %.1f km\n'%(self.equivalent_altitude*1e-3)
        s += 'wind speed: %.1f m/s\n'%self.equivalent_wind_speed
        return s
    
    @staticmethod
    def from_file(filepath, category='atmosphere'):
        return Atmosphere(read_config_file(filepath, category))
    
    @staticmethod
    def from_file_tiptop(filepath):
        return Atmosphere(read_config_tiptop(filepath)[1])
    
    @staticmethod
    def from_oopao(atm):
        return Atmosphere({'lext':atm.L0,
                           'altitude':np.array(atm.altitude),
                           'wind_speed':np.array(atm.windSpeed),
                           'wind_direction':np.array(atm.windDirection),
                           'seeing':r0_to_seeing(atm.r0, atm.wavelength, zenith=0),
                           'cn2dh_ratio':np.array(atm.fractionalR0)})
    
    @property
    def nlayer(self):
        return len(self.cn2dh_ratio)
    
    @property
    def cn2dh(self):
        return seeing_to_cn2dh(self.seeing) * self.cn2dh_ratio
    
    @property
    def equivalent_altitude(self):
        return equivalent_altitude(self.cn2dh, self.altitude)
    
    @property
    def equivalent_wind_speed(self):
        return equivalent_wind_speed(self.cn2dh, self.wind_speed)
    
    @property
    def squeeze_layers(self):
        veq = self.equivalent_wind_speed
        heq = self.equivalent_altitude
        self.cn2dh_ratio = np.array([1.0])
        self.wind_speed = np.array([veq])
        self.wind_direction = np.array([0])
        self.altitude = np.array([heq])
    
    def r0(self, wvl, zenith=0):
        return cn2dh_to_r0(self.cn2dh, wvl, zenith=zenith)
    
    def coherence_time(self, *args, **kwargs):
        r0 = self.r0(*args, **kwargs)
        return coherence_time(r0, self.equivalent_wind_speed)
    
    def isoplanetic_angle(self, *args, **kwargs):
        r0 = self.r0(*args, **kwargs)
        return isoplanetic_angle(r0, self.equivalent_altitude)
    
    def phase_psd(self, freq, wvl, zenith=0):
        r0 = self.r0(wvl, zenith=zenith)
        return phase_psd(freq, r0, lext=self.lext, lint=self.lint)
    
    def opd_psd(self, freq, zenith=0):
        wvl = 500e-9 # whatever!
        return self.phase_psd(freq, wvl, zenith=zenith) * (wvl/(2*np.pi))**2
    
    def logamp_psd(self, freq, wvl, zenith=0):
        return logamp_psd(freq, self.altitude, self.cn2dh, wvl, lext=self.lext, lint=self.lint, zenith=zenith)
