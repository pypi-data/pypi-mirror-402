"""
Number of controlled modes and transfer functions management
"""

import math
import numpy as np
import logging
from aopera.readconfig import read_config_file, read_config_tiptop, check_dictionary, INFO_RTC
from scipy.linalg import solve_discrete_are

#%% TEMPORAL FILTERING FUNCTION
def open_loop_transfer(freq, ao_freq, ki, nb_frame_delay, kp=0, discrete=False, leak=1.0):
    """
    Return the temporal open loop transfer function for a proportional-integrator controller.
    
    Parameters
    ----------
    freq : np.array
        Array of temporal frequencies to evaluate the CLTF on.
    ao_freq : float
        The sampling temporal frequency of the AO loop.
    ki : float
        Integrator gain.
    nb_frame_delay : float
        Number of frame delay.
        Must include: RTC, pixel transfert, DM rise.
        Must not include: WFS integration, DM zero-order-hold.
    kp : float (default:0)
        Proportional gain.
    discrete : bool  (default:False)
        Choose to use discrete formalism.
    leak : float (default=1.0)
        Leaky integrator.
    """
    
    if not discrete:
        Tp = 2j*np.pi*freq/ao_freq
        H = kp + ki/(Tp+(1.0-leak)) # controler
        H *= np.exp(-Tp*nb_frame_delay) # delay
        H *= (1-np.exp(-Tp))/Tp # WFS
        H *= 1 # zero order holder
    else:
        # Tp = 2j*np.pi*freq/ao_freq
        z = np.exp(2j*np.pi*freq/ao_freq) # it is one method to pass from Tp to z
        H = kp + ki/(1-leak/z) # controler
        H *= 1/z**(nb_frame_delay+1) # delay + WFS + zero order hold
        
    return H


def closed_loop_transfer(*args, **kwargs):
    """
    Return the temporal closed loop transfer function.
    See the open_loop_transfer arguments.
    """
    return 1/(1+open_loop_transfer(*args, **kwargs))


def noise_transfer(*args, **kwargs):
    """
    Return the noise transfer function.
    See the open_loop_transfer arguments.
    """
    return open_loop_transfer(*args, **kwargs) * closed_loop_transfer(*args, **kwargs)


def bandwidth(ki, nb_frame_delay, ao_freq, db=0):
    """
    Compute the AO bandwidth for an integrator control law.
    
    .. math::
        BW_{db} = \\frac{F}{2\\pi}\\frac{k_i}{\\sqrt{k_i(2N_d+1)+10^{-db}-1}}
    
    Parameters
    ----------
    ki : float
        Gain of the integrator law
    nb_frame_delay : float
        Number of frame delay (exposure frame excluded)
    ao_freq : float
        Loop frequency [Hz]
    
    Keywords
    --------
    db : float (≤0)
        The cutoff in decibel (default=0).
    
    References
    ----------
    Thierry Fusco (ONERA), 2005, internal document, "AO temporal behavior".
    Completed by R.Fetick.
    """
    cst = 10**(db/10)
    alpha = (nb_frame_delay+0.5)*ki
    # The polynomial equation comes from the development of `sin((nd+0.5)wT)`
    p0 = 1
    p1 = 1 - 1/cst - 2*alpha**1 / math.factorial(1)
    # p2 =             2*alpha**3 / math.factorial(3)
    # delta = p1**2 - 4*p0*p2
    # rsol = (np.sqrt(delta)-p1)/(2*p2) # order 2 solution
    rsol = -p0/p1 # order 1 solution
    bw = np.sqrt(rsol)*ki*ao_freq/(2*np.pi)
    
    # Check afterwards if the 1st order development of sine was valid
    sine_argu = (nb_frame_delay+0.5)*2*np.pi*bw/ao_freq
    rel_error = np.abs(sine_argu - np.sin(sine_argu))/sine_argu
    if  np.max(rel_error) > 0.07:
        logging.warning('Bandwidth computation might be unconsistent')
        
    return bw


def bandwidth_noise(ki, nb_frame_delay, ao_freq, db=-4):
    """
    Compute the noise bandwidth for an integrator control law.
    
    Parameters
    ----------
    ki : float
        Gain of the integrator law
    nb_frame_delay : float
        Number of frame delay (exposure frame excluded)
    ao_freq : float
        Loop frequency [Hz]
    
    Keywords
    --------
    db : float (<0)
        The cutoff in decibel (default=-4).
        
    Note
    ----
    A bandwidth at -4 dB is chosen so we get the equality between the integration
    of |NTF|² (in the discrete domain) and the bandwidth_noise expression.
    
    .. math::
        BW_{noise} \\simeq \\int_0^{+\\infty}|NTF(f)|^2 df
    
    So it has to be multiplied by 2 to account for both positive and negative frequencies.
    
    Reference
    ---------
    R.Fetick, personnal work.
    """
    cst = 10**(db/10)
    alpha = (nb_frame_delay+0.5)*ki
    # The polynomial equation comes from the development of `sin((nd+0.5)wT)`
    p3 =   - 2 * alpha**5 / math.factorial(5)
    p2 =     2 * alpha**3 / math.factorial(3)
    p1 = 1 - 2 * alpha**1 / math.factorial(1)
    p0 = 1 - 1/cst
    r = np.roots([p3,p2,p1,p0])
    rsol = min(r[r>0]) # the bandwidth is >0, and I choose the min solution (justified?)
    bwn = np.sqrt(rsol)*ki*ao_freq/(2*np.pi)
    return bwn


#%% LQG
def lqg_controller(fx, fy, phase_psd, noise_psd, cn2dh_ratio, wind_speed, wind_direction, ao_freq, delta_wind_speed=0.1, diameter=np.inf, verbose=False):
    """
    Compute LQG controller for each spatial frequency (fx,fy).
    Only valid for two frames delay (1 for WFS integration, 1 for pixel transfer and RTC computation).
    
    Parameters
    ----------
    fx : list of floats
        Spatial frequencies [1/m] along X.
    fy : list of floats
        Spatial frequencies [1/m] along Y.
    phase_psd : list of floats
        PSD of the turbulent phase [rad²m²] at (fx,fy).
    noise_psd : list of floats
        PSD of the noise [rad²m²] at (fx,fy).
    cn2dh_ratio : list of floats
        Cn²*dh ratio (sum=1) of turbulence layers.
    wind_speed : list of floats
        Wind speed [m/s] of turbulence layers.
    wind_direction : list of floats
        Wind direction [deg] of turbulence layers.
    ao_freq : float
        AO loop frequency [Hz].
    
    Keywords
    --------
    delta_wind_speed : float
        Uncertainty on wind speed estimation [m/s].
    diameter : float
        Telescope diameter [m].
    verbose : bool
        Print iterations while you drink a cup of tea.
    
    Return
    ------
    List of LQG controllers (functions) for each spatial frequency, to be evaluated on Z transform domain.
    Thus `output[i](z)` is the LQG controller of (fx[i], fy[i]) evaluated at `z`.
    
    Reference
    ---------
    Correia et al, 2017,
    Modelling astronomical adaptive optics performance with temporally-filtered Wiener reconstruction of slope data
    """
    
    logging.warning('Check LQG state covariance V and command regularization R')
    
    controllers = []
    RG = 1.0 # Measurement and reconstructor
    eigval_dump = 0.99999 # ensure solution for LQG
    Ts = 1/ao_freq
    # ff = np.sqrt(np.array(fx)**2+np.array(fy)**2)
    nfreq = len(fx)
    nlayer = len(wind_speed)
    dk = 1/diameter # aocutoff / (pupil.nact-1) / 2 # attempt to account for integral over frequencies for one mode

    # DISCRETE ARE
    # x{k+1} = A.x{k} + B.u{k} + v{k}  (state evolution)
    # y{k}   = C.x{k} + w{k}  (measurement)
    # J = ||xT.Q.x + uT.R.u||          (criterion)
    
    A = np.zeros((nlayer+5, nlayer+5), dtype=complex)
    B = np.zeros((nlayer+5,1))
    C = np.zeros((1,nlayer+5))
    Q = np.zeros((nlayer+5,nlayer+5))
    V = np.zeros((nlayer+5,nlayer+5), dtype=complex)
    
    vx = wind_speed*np.cos(wind_direction*np.pi/180)
    vy = wind_speed*np.sin(wind_direction*np.pi/180)
    poke_freq_avg = np.sinc(Ts*vx*dk) * np.sinc(Ts*vy*dk) # frequency averaging (modal frequencial width)
    # cvx = 2 - np.cos(2*np.pi*Ts*vx*dk/2)
    # cvy = 2 - np.cos(2*np.pi*Ts*vy*dk/2)
    # poke_avg_x = cvx - np.sqrt(cvx**2 - 1)
    # poke_avg_y = cvy - np.sqrt(cvy**2 - 1)
    # poke_freq_avg = poke_avg_x * poke_avg_y
    
    # FILL MATRICES with CONSTANT TERMS
    Q[nlayer+2, nlayer+2] = 1
    Q[nlayer+4, nlayer+4] = 1
    Q[nlayer+4, nlayer+2] = -1
    Q[nlayer+2, nlayer+4] = -1
    
    A[nlayer+1,nlayer] = 1
    A[nlayer+2,nlayer+1] = 1
    A[nlayer+4,nlayer+3] = 1
    
    B[nlayer+3,0] = 1
    
    C[0,nlayer+2] = RG
    C[0,nlayer+4] = -RG
    
    # DEFINE LQG CONTROLLER (cf. Correia et al, 2017)
    class CTRL:
        def __init__(self, A, B, C, K, L):
            self.I = np.eye(nlayer+5)
            self.K = np.copy(K)
            self.L = np.copy(L)
            self.B_KCB = B - self.K @ C @ B
            self.KCA_A = self.K @ C @ A - A
        def __call__(self, z):
            if hasattr(z, '__len__'): # object is iterable
                return [self.__call__(elem) for elem in z]
            else:
                L_Lambda_e = self.L @ np.linalg.pinv(self.I + self.KCA_A/z) # Eq 44 du papier
                return - (L_Lambda_e@self.K)[0,0] / (1+L_Lambda_e@self.B_KCB/z)[0,0]
    
    # ITERATE OVER SPATIAL FREQUENCIES
    for i in range(nfreq):
        
        if verbose and ((((i+1)%10) == 0) or (i == (nfreq-1))):
            print('\rLQG controller %4u/%u'%(i+1,nfreq), end='')
        
        nu = vx*fx[i] + vy*fy[i]
        ccx = 2 - np.cos(2*np.pi*Ts*fx[i]*delta_wind_speed/2)
        ccy = 2 - np.cos(2*np.pi*Ts*fy[i]*delta_wind_speed/2)
        wind_avg_x = ccx - np.sqrt(ccx**2 - 1) # np.sinc(Ts*fx[i]*delta_wind_speed) * np.sinc(Ts*fy[i]*delta_wind_speed) # windspeed averaging (uncertainty)
        wind_avg_y = ccy - np.sqrt(ccy**2 - 1)
        a_jj = np.exp(2j*np.pi*Ts*nu) * eigval_dump * poke_freq_avg * wind_avg_x * wind_avg_y
        
        np.fill_diagonal(A[0:nlayer,0:nlayer], a_jj)
        A[nlayer,0:nlayer] = a_jj
        
        # MODEL NOISE (EXCITATION)
        V[0:nlayer, 0:nlayer] = phase_psd[i] * np.diag(cn2dh_ratio) * (1-np.abs(a_jj)**2)  # Yule-Walker

        # MEASUREMENT NOISE
        W = np.eye(1) * noise_psd[i]
        
        # REGUL COMMANDE #TODO: pondérer par rapport à Q
        logging.debug('LQG command matrix should be properly scaled.')
        R = np.ones(1) * 1e-3

        P = solve_discrete_are(np.conjugate(A.T), C.T, V, W, balanced=True)
        K = P@C.T@np.linalg.pinv(C@P@C.T+W) # Kalman estimation gain

        S = solve_discrete_are(A, B, Q, R, balanced=True)
        L = np.linalg.pinv(B.T@S@B+R)@B.T@S@A # command gain
        
        controllers += [CTRL(A, B, C, K, L)]
        
    return controllers


#%% RTC CLASS
class RTC:
    def __init__(self, dictionary):
        self.kp = 0.0 # proportional gain
        self.leak = 1.0 # leaky gain (default = no leaky)
        self.discrete = True # discrete time controler
        self.predictive_factor = 1 # temporal PSD reducing due to predictive controler
        check_dictionary(dictionary, 'rtc')
        for k in INFO_RTC.keys():
            setattr(self, k, INFO_RTC[k][0](dictionary[k]))
        
    def __repr__(self):
        s  = 'aopera.RTC\n'
        s += '-----------\n'
        s += 'freq  : %u Hz\n'%self.freq
        s += 'delay : %.1f ms\n'%self.delay
        s += 'ki    : %.2f\n'%self.ki
        if self.predictive_factor != 1:
            s += 'predic: %.2f\n'%self.predictive_factor
        return s
        
    @staticmethod
    def from_file(filepath, category='rtc'):
        return RTC(read_config_file(filepath, category))
    
    @staticmethod
    def from_file_tiptop(filepath):
        return RTC(read_config_tiptop(filepath)[3])
    
    @staticmethod
    def from_oopao(ao_freq, oopao_frame_delay, gainCL, leak=1):
        rtc = RTC({'freq':ao_freq, 'ki':gainCL, 'delay':(oopao_frame_delay-1)/ao_freq*1000})
        rtc.leak = leak
        return rtc
    
    @property
    def nb_frame_delay(self):
        return self.delay*1e-3 * self.freq
    
    @property
    def bandwidth(self):
        return bandwidth(self.ki, self.nb_frame_delay, self.freq)
    
    @property
    def bandwidth_noise(self):
        return bandwidth_noise(self.ki, self.nb_frame_delay, self.freq)
    
    def open_loop_transfer(self, ft):
        return open_loop_transfer(ft, self.freq, self.ki, self.nb_frame_delay, kp=self.kp, discrete=self.discrete, leak=self.leak)
    
    def closed_loop_transfer(self, ft):
        return closed_loop_transfer(ft, self.freq, self.ki, self.nb_frame_delay, kp=self.kp, discrete=self.discrete, leak=self.leak)
    
    def noise_transfer(self, ft):
        return noise_transfer(ft, self.freq, self.ki, self.nb_frame_delay, kp=self.kp, discrete=self.discrete, leak=self.leak)
