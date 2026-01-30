"""
Photometric budget
"""

import numpy as np
from aopera.readconfig import set_attribute, read_config_file, read_config_tiptop
from aopera.utils import rad2arcsec
import logging

CONSTANT = {'h':6.626e-34, 'c':2.998e8, 'kb':1.381e-23}

def black_body(wvl, temp):
    """
    Black body spectrum [W/m2/sr/m]
    
    Parameters
    ----------
    wvl : float, np.array
        Wavelengths [m] at which to compute the spectrum.
    temp : float
        Temperature [K] of the black body.
    """
    return 2*CONSTANT['h']*CONSTANT['c']**2/((np.exp(CONSTANT['h']*CONSTANT['c']/(wvl*CONSTANT['kb']*temp))-1.0)*wvl**5)


def black_body_sun(wvl):
    """
    Sun black body spectrum [W/m2/m] as seen from Earth distance.
    
    Parameters
    ----------
    wvl : float, np.array
        Wavelengths [m] at which to compute the spectrum.
    """
    temp = 5780 # surface temperature [Kelvin]
    solid_angle = 6.8*1e-5 # Sun disk seen from Earth [steradian]
    return black_body(wvl, temp) * solid_angle


def atmospheric_transmission(zenith_rad, t_zenith=0.8):
    """Atmospheric transmission"""
    return t_zenith ** (1/np.cos(zenith_rad))


def satellite_flux(wvl_min, wvl_max, phase_angle=65, albedo=0.15):
    """
    Number of photons per second per steradian per m² of satellite surface.
    The received number of photons on a detector will be:
        N = satellite_flux(...) * T_exposure * S_satellite * S_telescope / distance² * throughput
    """
    incidence = 2/(3*np.pi) * (np.sin(np.deg2rad(phase_angle)) + (np.pi - np.deg2rad(phase_angle)) * np.cos(np.deg2rad(phase_angle)))
    wvl = np.linspace(wvl_min, wvl_max, 2000)
    spectrum = black_body_sun(wvl) * wvl/(CONSTANT['h']*CONSTANT['c'])  # [photon/s/wvl]
    nb_ph_sun = np.trapezoid(spectrum, wvl)
    sun_size_idl_correction_factor = 3.1
    return nb_ph_sun * albedo * incidence / sun_size_idl_correction_factor


class Band:
    # These values come from OOMAO [Conan and Correia]
    # [central wvl, bandwidth, zeropoint]
    BANDS = {
        "V": [ 550e-9,  90e-9, 3.3e12],
        "R": [ 640e-9, 150e-9,   4e12],
        "I": [ 790e-9, 150e-9, 2.7e12],
        "J": [1215e-9, 260e-9, 1.9e12],
        "H": [1654e-9, 290e-9, 1.1e12]
        }
    
    def __init__(self, band):
        self.band = band
      
    @property
    def band(self):
        return self._band
        
    @band.setter
    def band(self, band):
        if band not in Band.BANDS.keys():
            raise KeyError('The required photometric band [%s] has not been implemented'%band)
        self._band = band
        
    @property
    def wavelength(self):
        """Central wavelength of the band [m]"""
        return Band.BANDS[self.band][0]
        
    @property
    def bandwidth(self):
        """Bandwidth [m]"""
        return Band.BANDS[self.band][1]
    
    @property
    def zeropoint(self):
        """Photon per m2 per second at magnitude 0"""
        return Band.BANDS[self.band][2]/368.0 # This factor comes from OOMAO [Conan and Correia]
    
    def photon2mag(self, nphot):
        """Convert number of photons per m2 per second in magnitude"""
        return -2.5*np.log10(nphot/self.zeropoint)
    
    def mag2photon(self, mag):
        """Convert magnitude to number of photons per m2 per second"""
        return self.zeropoint * 10**(-mag/2.5)
    
    
class SourceScience:
    def __init__(self, dictionary):
        set_attribute(self, dictionary, 'source_science')
            
    def __repr__(self):
        s  = 'aopera.SOURCE_SCIENCE\n'
        s += '----------------------\n'
        s += 'wvl    : %u nm\n'%self.wvl_nm
        s += 'zenith : %u deg\n'%self.zenith_deg
        return s
        
    @staticmethod
    def from_file(filepath, category='source_science'):
        return SourceScience(read_config_file(filepath, category))
    
    @staticmethod
    def from_file_tiptop(filepath):
        return SourceScience(read_config_tiptop(filepath)[4])
    
    @staticmethod
    def from_oopao(src):
        return SourceScience({'wvl_nm':src.wavelength*1e9,'zenith_deg':0})
    
    @property
    def wvl(self):
        return self.wvl_nm * 1e-9
    
    @wvl.setter
    def wvl(self, value):
        self.wvl_nm = value * 1e9
        
    @property
    def zenith_rad(self):
        return self.zenith_deg * np.pi/180
    
    @zenith_rad.setter
    def zenith_rad(self, value):
        self.zenith_deg = value * 180/np.pi
        
    @property
    def elevation_rad(self):
        return np.pi/2 - self.zenith_rad
    
    @property
    def elevation_deg(self):
        return 90 - self.zenith_deg
    
    
    
class SourceWFS:
    def __init__(self, dictionary):
        self.square = False
        set_attribute(self, dictionary, 'source_wfs')
            
    def __repr__(self):
        s  = 'aopera.SOURCE_WFS\n'
        s += '------------------\n'
        s += 'wvl       : %u nm\n'%self.wvl_nm
        s += 'flux      : %.2g ph/m²/s\n'%self.flux
        s += 'separation: %.3f arcsec\n'%self.separation
        s += 'size      : %.2f arcsec\n'%self.size
        return s
        
    @staticmethod
    def from_file(filepath, category='source_wfs'):
        return SourceWFS(read_config_file(filepath, category))
    
    @staticmethod
    def from_file_tiptop(filepath):
        return SourceWFS(read_config_tiptop(filepath)[5])
    
    @staticmethod
    def from_oopao(src_wfs, src_sci):
        r_wfs, a_wfs = src_wfs.coordinates
        x_wfs = r_wfs * np.cos(a_wfs*np.pi/180)
        y_wfs = r_wfs * np.sin(a_wfs*np.pi/180)
        r_sci, a_sci = src_sci.coordinates
        x_sci = r_sci * np.cos(a_sci*np.pi/180)
        y_sci = r_sci * np.sin(a_sci*np.pi/180)
        logging.warning('Conversion from OOPAO to aopera assumes a point-like WFS source.')
        return SourceWFS({'wvl_nm':src_wfs.wavelength*1e9,
                          'flux':src_wfs.nPhoton,
                          'separation':np.sqrt((x_sci-x_wfs)**2+(y_sci-y_wfs)**2),
                          'angle':np.arctan2(y_wfs-y_sci, x_wfs-x_sci)*180/np.pi,
                          'size':0})
    
    @property
    def wvl(self):
        return self.wvl_nm * 1e-9
    
    @wvl.setter
    def wvl(self, value):
        self.wvl_nm = value * 1e9
        
    @property
    def separation_x(self):
        return self.separation * np.cos(self.angle*np.pi/180)
    
    @property
    def separation_y(self):
        return self.separation * np.sin(self.angle*np.pi/180)
    
    def image(self, nx, tel_diameter, samp):
        xx,yy = np.mgrid[0:nx,0:nx] - nx//2
        pix_size_arcsec = rad2arcsec((self.wvl/tel_diameter) / samp)
        Robj_pix = (self.size/2) / pix_size_arcsec
        if self.square:
            obj = (np.abs(xx)<=Robj_pix)*(np.abs(yy)<=Robj_pix)
        else:
            rr = np.sqrt(xx**2+yy**2)
            obj = (rr <= Robj_pix)
        return obj / np.sum(obj)
        