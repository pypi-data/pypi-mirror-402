"""
AOPERA initialization file
"""

#%% SETUP LOGGING
import logging
import os

class COLORS:
	GREEN = "\x1b[32;20m"
	BLUE = "\033[34m"
	YELLOW = "\x1b[33;20m"
	RED = "\x1b[31;20m"
	CYAN = '\033[36m'
	RESET = '\033[0m'

log_in_file = False
loglvl = logging.INFO # set logging.DEBUG to see all internal issues

if log_in_file:
    datefmt='%Y-%m-%d %H:%M:%S'
    logfmt = '[%(asctime)s] %(levelname)s in <%(funcName)s> : %(message)s' # %(module)s
    aoerrorpath = os.sep.join(__file__.split(os.sep)[:-2])
    logpath = aoerrorpath + os.sep + 'log'
    if not os.path.isdir(logpath):
        os.mkdir(logpath)
    logging.basicConfig(filename=logpath+os.sep+'default.log', encoding='utf-8',
                        level=loglvl, format=logfmt, datefmt=datefmt)
else:
    logfmt = COLORS.YELLOW + '%(levelname)s' + COLORS.RESET + ' in <%(funcName)s> : %(message)s' # %(module)s
    logging.basicConfig(level=loglvl, format=logfmt)

logging.debug('Load <aoerror> library')
del log_in_file, logfmt, loglvl, os, logging


#%% IMPORT MODULES
from . import utils
from . import zernike
from . import readconfig
from . import variance
from . import control
from . import turbulence
from . import aopsd
from . import shwfs
from . import ffwfs
from . import otfpsf
from . import photometry
from . import fiber
from . import simulation
from . import trajectory
