# -*- coding: utf-8 -*-
"""
Utility functions for runs
"""
import time
import math
import matplotlib.pyplot as plt
import numpy as np
import json
import glob
import logging

import qmcontrol.shim_system as ss
import qmcontrol.jcamp_write as jw
from qmcontrol.interface_constants import seqclk_MHz, s, settings_file, shims_dir

logger = logging.getLogger(__name__)

__author__ = "John Price"
__copyright__ = "Copyright 2021, Q Magnetics, LLC"
__credits__ = ["John Price"]
__license__ = "undecided"
__version__ = "0.0.1"
__maintainer__ = "John Price"
__email__ = "john@qmagnetics.com"
__status__ = "development"

class InterfaceError(Exception):
    """custom exception, sequencer interface operation failed"""
    pass

def initialize_hardware(si, spars, gpars, verbose=True):
    """
    Initialize sequencer hardware for any run that uses: 
        a single acquire time
        a single Tx frequency (may track)
        
    1. find decimation and exact spectral width
    2. find filter attenuation and system gain
    3. initialize hardware

    Parameters
    ----------
    si: QMagNMR object, the sequencer interface
    
    spars dict must define values for these keys: 
        'auto_decim'
        'decimation'
        'spec_width_kHz'
        'acquire_s'
        'auto_atten'
        'filter_atten'
        'gain_offset'
        'page'
        
    gpars dict must define values for these keys:
        'shimfile'
        'gain_target'
        'tx_freq_MHz'
        
    Returns
    -------
    filter_atten
    decimation
    exact_spec_width_kHz
    
    """
    # # load shims to hardware
    # logger.info('Load shims...')
    # shim_file = shims_dir / (gpars['shim file'] + '.json')
    # with open(shim_file,'r') as jfile:
        # shims = json.load(jfile)
    # ss.set_shims(si, shims, setDACs=True)
    # time.sleep(0.10)  # make sure shim currents have time to settle
    
    # find decimation, exact spectral width, guaranteed number of samples, memory page size
    if spars['auto decim']:
        decimation = round(seqclk_MHz*1000/spars['spectral width'])
    else:
        decimation = spars['decimation']
    exact_spec_width_kHz = seqclk_MHz*1000/decimation    
    gt_strobes = math.floor(spars['acquire time']*s/decimation)-1  # min no. strobes
    gt_nsamples = 4*math.floor(gt_strobes/4)  # min no. samples, mem controller uses 16 byte words
    page_size = math.ceil(gt_nsamples/4)+20   # x4 for samples, x16 for bytes
    
    # find filter attenuation and system gain
    if spars['auto atten']:
        filter_atten = round( 4 - np.log(gpars['gain target']/decimation**2)/np.log(2) )
        filter_atten = max(4, min(filter_atten,31))
    else:
        filter_atten = spars['filter atten']    # legal values 4 to 31
    
    if verbose:
        logger.info(f'Decimation = {decimation}')
        logger.info(f'Exact spectral width = {exact_spec_width_kHz:0.4f} kHz')
        logger.info(f'Acquire at least {gt_nsamples} samples per scan')
        logger.info(f'p = {filter_atten-4}, Gain = Dec**2/2**p = {decimation**2/2**(filter_atten-4):0.2f}')
    
    # initialize hardware
    si.NormalOperation()       # put mux'es and other controls in normal mode
    si.SetRefNCOFreq0(gpars['Tx freq'])
    si.SetDecimation(decimation)
    si.SetCICAtten(filter_atten)
    si.SetMemPageSize(page_size)
    si.EnableMemPageMode(spars['page mode'])
    
    return filter_atten, decimation, exact_spec_width_kHz

# mw is mainWindow object
def simulated_pulse_acquire_run(mw):
    
    gpars = mw.param_dict(['Global'])
    fpars = mw.param_dict(['Pulse Acquire Run','Files'])
    spars = mw.param_dict(['Pulse Acquire Run','Sequencer'])
    ppars = mw.param_dict(['Pulse Acquire Run','Processing'])
    mpars = mw.param_dict(['Global','Magnet'])
    vpars = mw.param_dict(['Global','Service'])
    
    if (fpars['save indiv. fids'] or fpars['save average fid']) and not(gpars['test scan']):
        if glob.glob(fpars['data directory']+'/'+fpars['data filename']+'*'):
            raise FileExistsError('Data file(s) in same dir with same base name already exist')
    
    logger.info(f"Generating simulated data...")
    Tacq = spars['acquire time']
    SW = spars['spectral width']
    zero_fill = ppars['zero pad']
    fL = mw.p.child('Global','Tx freq').value()
    mw.fid, mw.times, mw.spect, mw.freqs = \
                 simulate_fid(fL, Tacq, SW, zero_fill)
    mw.plot_fid()
    if mw.plots_blank:
        xa=True; ya=True
        mw.plots_blank = False
    else:
        xa=False; ya=False
    mw.plot_spectrum(xauto=xa, yauto=ya)
    mw.runTabCanvas.draw()
    
    # write individual fids to .jdx files
    # ##.OBSERVE FREQUENCY = starting value of tx_freq_MHz even if tracking
    fids = [mw.fid]
    if fpars['save indiv. fids'] and len(fids) > 0 and not(gpars['test scan']):
        fn = fpars['data directory']+'/'+fpars['data filename']+ '_nnn'
        logger.info(f'Saving individual FIDs to files {fn}...')
        for ii in range(len(fids)):
            fid_parts = np.array([fids[ii].real,fids[ii].imag])
            jw.jcamp_npa_write(fid_parts, fpars, spars, ppars, gpars, mpars, vpars, '_'+str(ii+1).zfill(3))
    
    # save settings
    # state = mw.p.saveState()
    # print(f'Saving settings...')
    # with open(settings_file,'w') as sfile:
        # json.dump(state,sfile, indent=4)
    
    logger.info(f'Run complete')
    mw.runMessageLabel.setText('Sumulated run complete')
    
# mw is mainWindow object
def simulated_shim_run(mw):
    
    gpars = mw.param_dict(['Global'])
    vpars = mw.param_dict(['Global','Service'])
    spars = mw.param_dict(['Shim Run','Sequencer'])
    ppars = mw.param_dict(['Shim Run','Processing'])
    
    logger.info(f"Generating simulated data...")
    Tacq = spars['acquire time']
    SW = spars['spectral width']
    zero_fill = ppars['zero pad']
    fL = mw.p.child('Global','Tx freq').value()
    mw.fid, mw.times, mw.spect, mw.freqs = \
                 simulate_fid(fL, Tacq, SW, zero_fill)
    mw.plot_fid()
    if mw.plots_blank:
        xa=True; ya=True
        mw.plots_blank = False
    else:
        xa=False; ya=False
    mw.plot_spectrum(xauto=xa, yauto=ya)
    mw.runTabCanvas.draw()
    
    # # save settings
    # state = mw.p.saveState()
    # print(f'Saving settings...')
    # with open(settings_file,'w') as sfile:
        # json.dump(state,sfile, indent=4)
    
    logger.info(f'Run complete')
    mw.runMessageLabel.setText('Simulated run complete')

def simulate_fid(fL, Tacq, SW, zero_fill):
    """
    simulate fid, times, spectrum, and frequencies
    simulate a doublet and a triplet with noise
    include phase and phase gradient errors

     fL         Larmor frequency (MHz), only for ppm
     Tacq       acquisition time (s)
     SW         spectral width, dec sampling rate (kHz)
     zero_fill  zero filling, total # points

     returns: fid, times, spectrum, frequecies
    """
    T2 = 1/np.pi        # T2 (s)
    dA = 1000           # doublet amplitude
    cs = 4              # chemical shift between multiplets (ppm)
    J = 6.0             # J coupling, splitting (Hz)
    phi0 = -45          # phase error in degrees
    phi1 = 0.03         # phase gradient error in degrees/Hz
    nAmp = 60            # rms noise amplitude
    fcenter = +421      # center frequency of spectrum (Hz)
    SW= SW*1000         # convert to Hz
    nsamples = int(Tacq*SW) 
    csHz = cs*fL                  # chem shift to Hz
    t = np.arange(nsamples)/SW    # time series
    noise = np.random.normal(0,nAmp,nsamples) + 1j*np.random.normal(0,nAmp,nsamples)

    # make doublet
    fp = fcenter+csHz/2+J/2
    fm = fcenter+csHz/2-J/2
    doublet_fid = dA*np.exp(1j*2*np.pi*(phi0+phi1*fp)/360)*np.exp((1j*2*np.pi*fp-1/T2)*t)+\
                  dA*np.exp(1j*2*np.pi*(phi0+phi1*fm)/360)*np.exp((1j*2*np.pi*fm-1/T2)*t)
                  
    # make triplet
    fp = fcenter-csHz/2+J
    f0 = fcenter-csHz/2
    fm = fcenter-csHz/2-J
    triplet_fid = 0.25*dA*np.exp(1j*2*np.pi*(phi0+phi1*fp)/360)*np.exp((1j*2*np.pi*fp-1/T2)*t)+\
                  0.50*dA*np.exp(1j*2*np.pi*(phi0+phi1*f0)/360)*np.exp((1j*2*np.pi*f0-1/T2)*t)+\
                  0.25*dA*np.exp(1j*2*np.pi*(phi0+phi1*fm)/360)*np.exp((1j*2*np.pi*fm-1/T2)*t)
    fid = doublet_fid + triplet_fid + noise
     
    spect = np.fft.fft(fid, zero_fill)/nsamples
    spect = np.fft.fftshift(spect)
    freqs = np.fft.fftfreq(zero_fill, 1/SW)
    freqs = np.fft.fftshift(freqs)
    return fid, t, spect, freqs
