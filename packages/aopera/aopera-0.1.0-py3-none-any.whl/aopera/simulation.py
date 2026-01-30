"""
Gathers all classes from the library to run a simulation
"""

import os
import numpy as np
from scipy.signal import fftconvolve
import logging
from aopera.utils import arcsec2rad, print_std
from aopera.aopsd import psd_temporal, psd_anisoplanetism, psd_anisoplanetism_extended_object, piston_filter, psd_ncpa, psd_chromatic_filter, air_refractive_index
from aopera.turbulence import Atmosphere
from aopera.otfpsf import Pupil, psd2otf, otf2psf
from aopera.photometry import SourceScience, SourceWFS
from aopera.shwfs import SHWFS
from aopera.ffwfs import PWFS
from aopera.control import RTC
from aopera.readconfig import read_config_tiptop_nx, read_config_tiptop_samp


class TiptopBaseSimulation:
    """Implement baseSimulation from Tiptop"""
    def __init__(self, path, parametersFile, verbose=False):
        self.path = path
        self.parametersFile = parametersFile
        self.verbose = verbose
        
    def doOverallSimulation(self):
        file_ini = os.path.join(self.path, self.parametersFile + '.ini')
        src_sci = SourceScience.from_file_tiptop(file_ini)
        src_wfs = SourceWFS.from_file_tiptop(file_ini)
        atm = Atmosphere.from_file_tiptop(file_ini)
        pupil = Pupil.from_file_tiptop(file_ini)
        rtc = RTC.from_file_tiptop(file_ini)
        try:
            wfs = PWFS.from_file_tiptop(file_ini)
        except:
            wfs = SHWFS.from_file_tiptop(file_ini)
        nx = read_config_tiptop_nx(file_ini)
        samp = read_config_tiptop_samp(file_ini)
        psd, var, param = simulation(nx, samp, pupil, atm, rtc, wfs, src_sci, src_wfs, verbose=self.verbose)
        psd_total = sum([psd[k] for k in psd.keys()])
        wvl_ratio = src_sci.wvl/src_wfs.wvl
        psf_ao_sci = pupil.psf_ao(psd_total, samp, wvl_scale=wvl_ratio)
        psf_diff_sci = pupil.psf_diffraction(nx, samp*wvl_ratio)
        
        df = pupil.frequency_step(samp)
        self.PSDstep = df
        self.N = nx
        self.PSD = psd_total * (src_wfs.wvl_nm/(2*np.pi))**2 * df**2 # Tiptop PSD has units of [nm²]
        self.sr = [np.max(psf_ao_sci)/np.max(psf_diff_sci)]
        self.cubeResultsArray = np.zeros((1, nx, nx))
        self.cubeResultsArray[0,...] = psf_ao_sci
        
    @property
    def cubeResults(self):
        try:
            return list(self.cubeResultsArray)
        except: # not computed yet
            pass
        
    def computeMetrics(self):
        raise NotImplementedError()
    


def simulation(nx, samp, *args, **kwargs):
    """Run a SH-WFS or a P-WFS simulation"""
    for a in args:
        if isinstance(a, SHWFS):
            return simulation_shwfs(nx, samp, *args, **kwargs)
        if isinstance(a, PWFS):
            return simulation_ffwfs(nx, samp, *args, **kwargs)
    raise ValueError('Your simulation must include a SHWFS or a PWFS')


def simulation_shwfs(nx, samp, *args, verbose=False):
    """
    Run a full SH-WFS simulation
    
    Parameters
    ----------
    nx : int : number of pixels
    samp : float : sampling.
    *args : must include a Pupil, Atmosphere, SHWFS, RTC, SourceWFS, SourceScience
    
    Returns
    -------
    dictionary : the PSD list [rad²m²]
    dictionary : the variance list [rad²]
    dictionary : some intermediate values
    """
    
    ### PARSE INPUTS, whatever the order
    for a in args:
        if isinstance(a, Atmosphere):
            atm = a
        if isinstance(a, Pupil):
            tel = a
        if isinstance(a, SourceScience):
            src_sci = a
        if isinstance(a, SourceWFS):
            src_wfs = a
        if isinstance(a, SHWFS):
            wfs = a
        if isinstance(a, RTC):
            rtc = a
    
    for v in ['atm','tel','src_sci','src_wfs','wfs','rtc']:
        if not v in locals():
            raise ValueError('You forgot to define one of the arguments')
            
    ### INIT SOME STUFF
    df = tel.frequency_step(samp) # numerical frequency step [1/m]
    aocutoff = tel.cutoff_frequency(wfs.lenslet) # system AO cutoff [1/m]
    fx,fy = tel.frequency_grid(nx, samp)
    freq = np.sqrt(fx**2+fy**2)
    pstflt = piston_filter(freq, tel.diameter) # filter low freq
    aomskin = wfs.visibility(fx, fy, tel.diameter, thresh=1e-8) * tel.controllability(fx, fy)
    r0_wfs = atm.r0(src_wfs.wvl, zenith=src_sci.zenith_rad)
    nphot_subap = src_wfs.flux * tel.surface / rtc.freq / wfs.lenslet_valid(occ=tel.occultation)
    psdatmo = atm.phase_psd(freq, src_wfs.wvl, zenith=src_sci.zenith_rad)
    psd = {}
    
    ## PSD FITTING
    psd['fitting'] = psdatmo * (1-aomskin) * pstflt
    
    ### PSD ALIASING
    psd_to_alias = lambda fx,fy : atm.phase_psd(np.sqrt(fx**2+fy**2), src_wfs.wvl, zenith=src_sci.zenith_rad)
    psd['aliasing'] = wfs.psd_aliasing(fx, fy, tel.diameter, psd_to_alias) * aomskin
    
    ## PSD TEMPORAL
    psd['temporal'] = np.zeros((nx,nx))
    logging.debug('Use better implementation of LQG.')
    for j in range(atm.nlayer):
        wnd_angle = atm.wind_direction[j]*np.pi/180
        psd_temp = aomskin * psd_temporal(fx, fy, atm.wind_speed[j], psdatmo, rtc.closed_loop_transfer, wnd_angle=wnd_angle)
        psd['temporal'] += psd_temp * atm.cn2dh_ratio[j] * rtc.predictive_factor #TODO: better implementation of LQG
    
    ## PSD RON NOISE
    var_ron = wfs.var_ron(nphot_subap, tel.radial_max, rtc.bandwidth_noise, rtc.freq)
    psd['ron'] = wfs.psd_noise(fx, fy, aocutoff, var_ron, df, D=tel.diameter)
    
    ### PSD PHOTON NOISE
    spot_size = wfs.spot_fwhm(r0_wfs, tel.diameter, src_wfs.wvl, src_size=arcsec2rad(src_wfs.size))
    var_photon = wfs.var_photon(spot_size, nphot_subap, tel.radial_max, rtc.bandwidth_noise, rtc.freq)
    psd['photon'] = wfs.psd_noise(fx, fy, aocutoff, var_photon, df, D=tel.diameter)
    
    ## PSD ANISOPLANETISM MEASURE
    if (src_wfs.size > 0) and (max(atm.altitude) > 0):
        aniso_size = arcsec2rad(src_wfs.size) / (0.5*(np.sqrt(2)+1)) # avg between circle and square
        psd['aniso-mes'] = psd_anisoplanetism_extended_object(fx, fy, atm.cn2dh, atm.altitude, tel.pitch_ao(wfs.lenslet), src_wfs.wvl, aniso_size, src_alt=np.inf, src_zenith=src_sci.zenith_rad, lext=atm.lext, lint=0)
        
    ## PSD ANISOPLANETISM SEPARATION
    if src_wfs.separation > 0:
        sep_x_rad = arcsec2rad(src_wfs.separation_x)
        sep_y_rad = arcsec2rad(src_wfs.separation_y)
        psd_aniso = psd_anisoplanetism(fx, fy, atm.cn2dh, atm.altitude, src_wfs.wvl, sep_x_rad, sep_y_rad, lext=atm.lext, zenith=src_sci.zenith_rad)
        psd['aniso-dist'] = psd_aniso * aomskin
        
    ## NCPA SCIENCE vs WFS
    rad_to_nm = src_wfs.wvl*1e9/(2*np.pi)
    if tel.ncpa > 0:
        psd['ncpa'] = psd_ncpa(tel.ncpa / rad_to_nm, freq, df, tel.diameter)
        
    ## DIFFERENTIAL CHROMATIC INDEX
    if src_sci.wvl != src_wfs.wvl:
        psd['chromatic'] = psdatmo * aomskin * psd_chromatic_filter(src_wfs.wvl_nm, src_sci.wvl_nm)
        theta_refraction = (air_refractive_index(src_sci.wvl_nm*1e-3)-air_refractive_index(src_wfs.wvl_nm*1e-3))*np.tan(src_sci.zenith_rad)
        psd['refraction'] = psd_anisoplanetism(fx, fy, atm.cn2dh, atm.altitude, src_wfs.wvl, theta_refraction, 0, lext=atm.lext, zenith=src_sci.zenith_rad) * aomskin
        
    ### GET VARIANCES
    var = {}
    for k in psd.keys():
        if k in ['ncpa', 'photon', 'ron']:
            filt = 1 # these have already been filtered
        else:
            filt = pstflt
        var[k] = np.sum(filt*psd[k]*df**2)
        
    if verbose:
        rad_to_nm = src_wfs.wvl*1e9/(2*np.pi)
        std_nm = {k:rad_to_nm*np.sqrt(var[k]) for k in var.keys()}
        print()
        print('   WAVEFRONT ERROR [nm RMS]')
        print_std(std_nm)
        
    ### RETURN
    param = {'r0_wfs':r0_wfs,
             'spot_fwhm':spot_size,
             'psd_atmo':psdatmo}
    return psd, var, param
    
    

def simulation_ffwfs(nx, samp, *args, verbose=False, is_modu_sky=True, nb_iter_og=4):
    """
    Run a full FF-WFS simulation
    
    Parameters
    ----------
    nx : int : number of pixels.
    samp : float : sampling of the PSF at the WFS wavelength.
    *args : must include a Pupil, Atmosphere, PWFS, RTC, SourceWFS, SourceScience.
    
    Keywords
    --------
    verbose = False : bool : activate verbose mode.
    is_modu_sky = True : bool : activate modulation on-sky.
    nb_iter_og = 4 : int : number of computations for OG to converge
    
    Returns
    -------
    dictionary : the PSD list [rad²m²]
    dictionary : the variance list [rad²]
    dictionary : some intermediate values
    """
    
    ### PARSE INPUTS, whatever the order
    for a in args:
        if isinstance(a, Atmosphere):
            atm = a
        if isinstance(a, Pupil):
            tel = a
        if isinstance(a, SourceScience):
            src_sci = a
        if isinstance(a, SourceWFS):
            src_wfs = a
        if isinstance(a, PWFS):
            wfs = a
        if isinstance(a, RTC):
            rtc = a
            
    for v in ['atm','tel','src_sci','src_wfs','wfs','rtc']:
        if not v in locals():
            raise ValueError('You forgot to define one of the arguments')
            
    otf_diff = tel.otf_diffraction(nx, samp)
    psf_diff = tel.psf_diffraction(nx, samp)
    obj = src_wfs.image(nx, tel.diameter, samp)
    nphot = src_wfs.flux * tel.surface / rtc.freq
    
    df = tel.frequency_step(samp) # numerical frequency step [1/m]
    fx,fy = tel.frequency_grid(nx, samp)
    freq = np.sqrt(fx**2+fy**2)
    pstflt = piston_filter(freq, tel.diameter) # filter low freq
    aomskin = wfs.visibility(samp, psf_diff, thresh=0.01) * tel.controllability(fx, fy)
    ki0 = rtc.ki
    psdatmo = atm.phase_psd(freq, src_wfs.wvl, zenith=src_sci.zenith_rad)
    psd = {}

    ## PSD FITTING and ALIASING
    psd['fitting'] = psdatmo * (1-aomskin) * pstflt

    psd_to_alias = lambda fx,fy : atm.phase_psd(np.sqrt(fx**2+fy**2), src_wfs.wvl, zenith=src_sci.zenith_rad)
    ffwfsrec = wfs.reconstructor(samp, psf_diff, thresh=0.01)
    psd['aliasing'] = wfs.psd_aliasing(fx, fy, psd_to_alias, ffwfsrec, tel.diameter, nact=tel.nact) * aomskin

    ## PSD TEMPORAL and NOISE (affected by OG)
    og = np.ones((nx,nx))
    psf_ao = np.copy(psf_diff)
    
    if nb_iter_og < 1:
        raise ValueError('You must ensure `nb_iter_og >= 1`')
    
    for i_og in range(nb_iter_og):
        
        ## APPLY OG to LOOP GAIN
        rtc.ki = ki0 * og # apply WFS OG to loop gain
        
        if wfs.og_compensation:
            modal_gain_compensation = og # (1+og)/2 # specific matrix approximation
            rtc.ki = rtc.ki / modal_gain_compensation
            
        ### PSD TEMPORAL
        psd['temporal'] = np.zeros((nx,nx))
        logging.debug('Use better implementation of LQG.')
        for i in range(atm.nlayer):
            wnd_angle = atm.wind_direction[i]*np.pi/180
            psd_temp = aomskin * psd_temporal(fx, fy, atm.wind_speed[i], psdatmo, rtc.closed_loop_transfer, wnd_angle=wnd_angle)
            psd['temporal'] += psd_temp * atm.cn2dh_ratio[i] * rtc.predictive_factor #TODO: better implementation of LQG
        
        ## PSD NOISE
        og_avg = np.mean(og[aomskin>0.5])
        rtc.ki = ki0 * og_avg
        if wfs.og_compensation:
            rtc.ki = rtc.ki / np.mean(modal_gain_compensation[aomskin>0.5])
        freq_temp = np.linspace(0.01, rtc.freq/2, num=3000) # Could also use np.logspace to compute freq_temp!
        ntf2_int = 2/rtc.freq * np.trapezoid(np.abs(rtc.noise_transfer(freq_temp))**2, freq_temp)
        if (src_wfs.size==0):
            psf_onsky = psf_ao
        else:
            psf_onsky = fftconvolve(psf_ao, obj, mode='same')
        psd['ron'] = wfs.psd_noise_ron(samp, nphot, psf_onsky, psf_diff) * ntf2_int * aomskin
        psd['photon'] = wfs.psd_noise_photon(samp, nphot, psf_onsky, psf_diff) * ntf2_int * aomskin
        
        ## PSD ANISOPLANETISM MEASURE
        if (src_wfs.size > 0) and (max(atm.altitude) > 0):
            aniso_size = arcsec2rad(src_wfs.size) / (0.5*(np.sqrt(2)+1)) # avg between circle and square
            psd['aniso-mes'] = psd_anisoplanetism_extended_object(fx, fy, atm.cn2dh, atm.altitude, tel.pitch_ao(wfs.lenslet), src_wfs.wvl, aniso_size, src_alt=np.inf, src_zenith=src_sci.zenith_rad, lext=atm.lext, lint=0) * np.mean(og[aomskin>0])
        
        ### COMPUTE PSD TOTAL, PSF and OG
        psd_total = sum([psd[k] for k in psd.keys()])
        psf_ao = otf2psf(psd2otf(psd_total, df)*otf_diff)
        if i_og < (nb_iter_og-1): # compute OG for next iteration
            og = wfs.optical_gain(samp, psf_diff, psf_ao, obj_sky=obj, modu_sky=is_modu_sky)
        
        ### VERBOSE
        if verbose:
            rad_to_nm = src_wfs.wvl*1e9/(2*np.pi)
            wfe = np.sqrt(np.sum(pstflt*psd_total)*df**2)*rad_to_nm
            print('[OG iter. %u/%u]   OG = %.2f   WFE = %3u nm'%(i_og+1, nb_iter_og, og_avg, wfe))
        
    ## SET AGAIN CORRECT KI BEFORE EXITING
    rtc.ki = ki0

    ## PSD ANISOPLANETISM SEPARATION
    ## after OG computation since it affects only science!
    if src_wfs.separation > 0:
        sep_x_rad = arcsec2rad(src_wfs.separation_x)
        sep_y_rad = arcsec2rad(src_wfs.separation_y)
        psd_aniso = psd_anisoplanetism(fx, fy, atm.cn2dh, atm.altitude, src_wfs.wvl, sep_x_rad, sep_y_rad, lext=atm.lext, zenith=src_sci.zenith_rad)
        psd['aniso-dist'] = psd_aniso * aomskin
        
    ## NCPA SCIENCE vs WFS
    ## after OG computation since it affects only science!
    rad_to_nm = src_wfs.wvl*1e9/(2*np.pi)
    if tel.ncpa > 0:
        psd['ncpa'] = psd_ncpa(tel.ncpa / rad_to_nm, freq, df, tel.diameter)
        
    ## DIFFERENTIAL CHROMATIC INDEX
    ## after OG computation since it affects only science!
    if src_sci.wvl != src_wfs.wvl:
        psd['chromatic'] = psdatmo * aomskin * psd_chromatic_filter(src_wfs.wvl_nm, src_sci.wvl_nm)
        theta_refraction = (air_refractive_index(src_sci.wvl_nm*1e-3)-air_refractive_index(src_wfs.wvl_nm*1e-3))*np.tan(src_sci.zenith_rad)
        psd['refraction'] = psd_anisoplanetism(fx, fy, atm.cn2dh, atm.altitude, src_wfs.wvl, theta_refraction, 0, lext=atm.lext, zenith=src_sci.zenith_rad) * aomskin
        
    ### GET VARIANCES
    var = {}
    for k in psd.keys():
        if k in ['ncpa', 'photon', 'ron']:
            filt = 1 # these have already been filtered
        else:
            filt = pstflt
        var[k] = np.sum(filt*psd[k]*df**2)
        
    if verbose:
        rad_to_nm = src_wfs.wvl*1e9/(2*np.pi)
        std_nm = {k:rad_to_nm*np.sqrt(var[k]) for k in var.keys()}
        print()
        print('   WAVEFRONT ERROR [nm RMS]')
        print_std(std_nm)
        
    ### RETURN
    param = {'r0_wfs':atm.r0(src_wfs.wvl,zenith=src_sci.zenith_rad),
             'og_avg':og_avg,
             'psf':psf_ao,
             'psd_atmo':psdatmo}
    return psd, var, param
