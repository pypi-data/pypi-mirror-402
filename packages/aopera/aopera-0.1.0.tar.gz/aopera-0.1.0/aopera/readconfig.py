"""
Load data from a .INI configuration file
"""

import os
from configparser import ConfigParser
import logging
import numpy as np
# from aopera.turbulence import WVL_REF_SEEING
from aopera.utils import arcsec2rad

WVL_REF_SEEING = 500e-9 # TODO: solve circular import issue

def np_array(x):
    try:
        return np.array(eval(x))
    except:
        return np.array(x)

def make_bool(x):
    if type(x) is bool:
        return x
    else:
        return x.lower()=='true'

def float_or_none(x):
    if (x is None) or (x == 'None'):
        return None
    else:
        return float(x)

# INFO have following structure:
#   key : (string to type converter, mandatory boolean, default value if optional)

INFO_ATMO_ABSTRACT = {'lext':(float,True,None), # [m]
                      'altitude':(np_array,True,None), # [m]
                      'wind_speed':(np_array,True,None), # [m/s]
                      'wind_direction':(np_array,True,None)} # [deg]

INFO_ATMO_SEEING = dict(INFO_ATMO_ABSTRACT)
INFO_ATMO_SEEING.update({'seeing':(float,True,None), # [arcsec]
                         'cn2dh_ratio':(np_array,True,None)}) # [no unit]

INFO_ATMO_CN2DH = dict(INFO_ATMO_ABSTRACT)
INFO_ATMO_CN2DH.update({'cn2dh':(np_array,True,None)}) # [m^(-1/3)]

INFO_SOURCE_SCIENCE = {'wvl_nm':(float,True,None), # [nm]
                       'zenith_deg':(float,True,None)} # [deg]

INFO_SOURCE_WFS = {'wvl_nm':(float,True,None), # [nm]
                   'flux':(float,True,None),  # [ph/m²/s]
                   'separation':(float,True,None), # [arcsec]
                   'angle':(float,True,None), # [deg]
                   'size':(float,True,None)} # [arcsec]

INFO_PUPIL = {'diameter':(float,True,None), # [m]
              'occultation':(float,True,None), # [no unit]
              'nact':(int,True,None), # [no unit]
              'ncpa':(float,False,0), # [nm RMS]
              'nmode_ratio':(float,False,1.0)}

INFO_RTC = {'freq':(float,True,None), # [Hz]
            'delay':(float,True,None), # [ms]
            'ki':(float,True,None)} # [no unit]

INFO_WFS_ABSTRACT = {'lenslet':(int,True,None), # [no unit]
                     'ron':(float,True,None), # [e-/pixel]
                     'emccd':(make_bool,True,None)} # [no unit]

INFO_PWFS = dict(INFO_WFS_ABSTRACT)
INFO_PWFS.update({'modulation':(float,True,None),
                  'og_compensation':(bool,False,False)}) # [lambda/D]

INFO_SHWFS = dict(INFO_WFS_ABSTRACT)
INFO_SHWFS.update({'samp':(float,True,None), # [no unit]
                   'npix_cog':(int,True,None),
                   'weight':(float_or_none,False,None)}) # [no unit]


INFO = {'atmosphere_seeing':INFO_ATMO_SEEING,
        'atmosphere_cn2dh':INFO_ATMO_CN2DH,
        'source_science':INFO_SOURCE_SCIENCE,
        'source_wfs':INFO_SOURCE_WFS,
        'pupil':INFO_PUPIL,
        'rtc':INFO_RTC,
        'pwfs':INFO_PWFS,
        'shwfs':INFO_SHWFS}


def read_config_file(filepath, category):
    """Generic function to read a specific category of a INI file"""
    cfg = ConfigParser()
    cfg.optionxform = str
    out = cfg.read(filepath)
    if len(out)==0:
        # Try in the 'data' folder
        filepath_data = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + 'data' + os.path.sep + filepath
        out = cfg.read(filepath_data)
        if len(out)==0:
            raise FileNotFoundError("The configuration file has not been found")
        else:
            logging.info('File <%s> has been found in <aopera/data/>'%filepath)
    if not category in cfg.keys():
        raise ValueError("The category [%s] does not appear in the configuration file"%category)
    return cfg[category]


def read_config_tiptop(filepath):
    """
    Read a TIPTOP INI file to generate aopera compatible dictionaries
    """
    cfg = ConfigParser()
    cfg.optionxform = str
    out = cfg.read(filepath)
    if len(out)==0:
        raise FileNotFoundError("The configuration file has not been found")
    
    cfg_tel = cfg['telescope']
    cfg_atm = cfg['atmosphere']
    dm_act = eval(cfg['DM']['NumberActuators'])
    
    if len(dm_act)>1: #TODO: SCAO only
        raise ValueError('TIPTOP file has more than one DM, this is not compatible with aopera')
    
    if float(cfg_atm['Wavelength']) != WVL_REF_SEEING:
        raise ValueError('TIPTOP file must define seeing at %u nm'%(WVL_REF_SEEING*1e9))
    
    if 'SensorFrameRate_LO' in cfg['RTC'].keys():
        raise ValueError('Cannot use a Low Order split with aopera')
    
    area_shape = cfg['DM']['AoArea'].replace('\'','')
    if area_shape == 'circle':
        nmode_ratio = np.pi/4
    elif area_shape == 'square':
        nmode_ratio = 1
    else:
        raise ValueError('Error when reading Tiptop file, the DM AoArea must be `circle` or `square`')
    
    pupil = {'diameter':float(cfg_tel['TelescopeDiameter']),
             'occultation':float(cfg_tel['ObscurationRatio']),
             'nact':dm_act[0],
             'nmode_ratio':nmode_ratio}
    
    atmosphere = {'seeing':float(cfg_atm['Seeing']),
                  'cn2dh_ratio':np_array(cfg_atm['Cn2Weights']),
                  'lext':float(cfg_atm['L0']),
                  'altitude':np_array(cfg_atm['Cn2Heights']),
                  'wind_speed':np_array(cfg_atm['WindSpeed']),
                  'wind_direction':90 - np_array(cfg_atm['WindDirection'])}
    
    nb_frame_delay = float(cfg['RTC']['LoopDelaySteps_HO']) - 1 # TIPTOP counts WFS integration as frame delay
    freq = float(cfg['RTC']['SensorFrameRate_HO'])
    
    rtc = {'freq':freq,
           'delay':nb_frame_delay/freq*1e3,
           'ki':float(cfg['RTC']['LoopGain_HO'])}
    
    if eval(cfg['sources_science']['Zenith'])[0] != 0:
        raise ValueError('aopera evaluates performance at center of array, source science zenith angle should be null.')
    
    src_sci_wvl = eval(cfg['sources_science']['Wavelength'])
    if len(src_sci_wvl) > 1:
        raise NotImplementedError('No compatibility between TIPTOP and aopera for multiple science wavelengths.')
    src_sci = {'wvl_nm':src_sci_wvl[0]*1e9,
               'zenith_deg':float(cfg_tel['ZenithAngle'])}
    
    cfg_src_wfs = cfg['sources_HO']
    cfg_wfs = cfg['sensor_HO']
    
    wfs_type = cfg_wfs['WfsType']
    if int(cfg_wfs['ExcessNoiseFactor']) == 1:
        emccd = False
    elif int(cfg_wfs['ExcessNoiseFactor']) == 2:
        emccd = True
    else:
        raise ValueError('Can only process ExcessNoiseFactor with value 1 or 2')
    
    wfs_nb_lenslet = eval(cfg_wfs['NumberLenslets'])
    if len(wfs_nb_lenslet) > 1:
        raise ValueError('TIPTOP file has more than one WFS, this is not compatible with aopera')
    
    wfs = {'lenslet':wfs_nb_lenslet[0],
           'ron':float(cfg_wfs['SigmaRON']),
           'emccd':emccd}
    
    nb_phot_wfs = eval(cfg_wfs['NumberPhotons'])[0] # nb photon/subap/frame
    wfs_flux = nb_phot_wfs * rtc['freq'] * wfs['lenslet']**2 / pupil['diameter']**2
    
    
    src_wfs = {'wvl_nm':float(cfg_src_wfs['Wavelength'])*1e9,
               'flux':wfs_flux,
               'separation':eval(cfg_src_wfs['Zenith'])[0],
               'angle':eval(cfg_src_wfs['Azimuth'])[0],
               'size':0}
    
    if 'Pyramid' in wfs_type:
        wfs['modulation'] = float(cfg_wfs['Modulation'])
    elif 'Shack-Hartmann' in wfs_type:
        logging.warning('TIPTOP and aopera definitions for SH spot CoG algorithm have to be checked.')
        pix_rad = arcsec2rad(float(cfg_wfs['PixelScale'])*1e-3)
        lmbd_dpup = src_wfs['wvl_nm'] * 1e-9 / (pupil['diameter']/wfs['lenslet'])
        wfs['samp'] = lmbd_dpup / pix_rad
        wfs['npix_cog'] = 10
    else:
        raise ValueError('Unknown TIPTOP WFS type')
    
    return pupil, atmosphere, wfs, rtc, src_sci, src_wfs
    

def read_config_tiptop_samp(filepath):
    """Read a TIPTOP INI file and compute PSF sampling at WFS wavelength"""
    cfg = ConfigParser()
    cfg.optionxform = str
    out = cfg.read(filepath)
    if len(out)==0:
        raise FileNotFoundError("The configuration file has not been found")
    diameter = float(cfg['telescope']['TelescopeDiameter'])
    wvl_wfs = float(cfg['sources_HO']['Wavelength'])
    pix_mas = float(cfg['sensor_science']['PixelScale'])
    return (wvl_wfs/diameter) / arcsec2rad(pix_mas*1e-3)


def read_config_tiptop_nx(filepath):
    """Read a TIPTOP INI file and compute PSF sampling at WFS wavelength"""
    cfg = ConfigParser()
    cfg.optionxform = str
    out = cfg.read(filepath)
    if len(out)==0:
        raise FileNotFoundError("The configuration file has not been found")  
    return int(cfg['sensor_science']['FieldOfView'])
    

def check_dictionary(dictionary, category_name):
    """
    Check keywords.
    Return a dictionary with optional keywords filled with default value.
    """
    for k in INFO[category_name].keys():
        if not k in dictionary.keys():
            if INFO[category_name][k][1]: # Keyword is mandatory
                logging.error('The keyword \'%s\' is mandatory in the category \'%s\''%(k,category_name))
            else:
                # logging.warning('The keyword \'%s\' has not been defined in the category \'%s\', it is set to default value \'%s\''%(k,category_name,INFO[category_name][k][2]))
                logging.warning('Undefined keyword set to default value \'%s.%s=%s\''%(category_name,k,INFO[category_name][k][2]))
                try:
                    dictionary[k] = INFO[category_name][k][2]
                except: # config parser requires strings
                    dictionary[k] = str(INFO[category_name][k][2])
        else:
            try:
                INFO[category_name][k][0](dictionary[k]) # try type conversion
            except:
                logging.error('The keyword \'%s\' in the category \'%s\' does not have the correct type'%(k,category_name))
    for k in dictionary.keys():
        if not k in INFO[category_name].keys():
            logging.warning('The keyword \'%s\' is ignored by the category \'%s\''%(k,category_name))
    return dictionary


def set_attribute(slf, dictionary, category_name):
    """
    Set a disctionary as attribute of the Python object `slf`
    """
    dictionary = check_dictionary(dictionary, category_name)
    for k in INFO[category_name].keys():
        setattr(slf, k, INFO[category_name][k][0](dictionary[k]))
            