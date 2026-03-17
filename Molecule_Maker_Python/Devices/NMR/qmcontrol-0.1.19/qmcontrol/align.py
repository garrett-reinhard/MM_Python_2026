# -*- coding: utf-8 -*-
"""
Created on Mon May  3 23:16:12 2021

@author: John Price
"""
import logging
import numpy as np

logger = logging.getLogger(__name__)

# align a fid to a reference fid using peak of magnitude of cross spectrum
# return df_opt and aligned fid if test_mode is False
# if test_mode is True, also return phi_opt, cross spect, cross spect freqs
def align(reference_fid, fid, spec_width_kHz, test_mode=False):
    
    freq_resolution = 0.03        # determines how much zero padding
    points = len(reference_fid)
    time_step = 1/(1000*spec_width_kHz)
    cspec_points = int(1/(freq_resolution*time_step))
    zero_pad = points if points >= cspec_points else cspec_points 
    
    inner = reference_fid*fid.conj()
    cspect = np.fft.fft(inner, zero_pad)  # compute cross spectrum
    cspect = np.fft.fftshift(cspect)
    freqs = np.fft.fftfreq(zero_pad, time_step)
    freqs = np.fft.fftshift(freqs)
    
    index_max = np.argmax(np.abs(cspect))  # find max(mag(cross spectrum))
    df_opt = freqs[index_max]
    phi_opt = np.angle(cspect[index_max])
    time_series = np.linspace(0, (points-1)*time_step, points)
    aligned_fid = fid*np.exp(1j*phi_opt)*np.exp(2*np.pi*1j*df_opt*time_series)
    
    if test_mode:
         return df_opt, aligned_fid, phi_opt, cspect, freqs
    else:
         return df_opt, aligned_fid


if __name__ == '__main__':

    import time
    from matplotlib import pyplot as plt

    # make a simulated reference fid and a simulated drifted fid
    spec_width_kHz = 10.0  # exact
    acquire_s = 3.0        # approx
    
    f1 = 10.0        # Hz, offset frequency of reference fid
    df = 11.0        # Hz, frequency drift
    dphi = 0.10      # radians, phase drift
    noise_rms = 500  # add noise to both fids
    tau = 0.4        # s, exp decay of both fids
    
    time_step = 1/(1000*spec_width_kHz)    # exact
    points = int(1 + acquire_s/time_step)  # exact
    
    noise1_real = noise_rms*np.random.randn(points)
    noise1_imag = noise_rms*np.random.randn(points)
    noise1 = noise1_real + 1j*noise1_imag
    noise2_real = noise_rms*np.random.randn(points) 
    noise2_imag = noise_rms*np.random.randn(points)
    noise2 = noise2_real + 1j*noise2_imag
    
    time_series = np.linspace(0,(points-1)*time_step,points)
    fid1 = (2**15-1)*np.exp((2*np.pi*1j*f1-1/tau)*time_series)
    fid2 = fid1*np.exp(1j*dphi)*np.exp(2*np.pi*1j*df*time_series)
    fid1 = fid1 + noise1
    fid2 = fid2 + noise2
    
    #  call align()
    tic = time.perf_counter()
    df_opt, aligned_fid, phi_opt, cspect, freqs = align(fid1, fid2, spec_width_kHz, True)
    toc = time.perf_counter()
    logger.info(f'time for alignment (s): {toc-tic:.6f}')
    
    # report results
    logger.info(f'df_opt: {df_opt:.4f} Hz')
    logger.info(f'phi_opt: {phi_opt:.4f} rad')
    logger.info(f'cross spectrum points: {len(cspect)}')
    logger.info(f'frequency resolution: {1/(time_step*len(cspect)):.4f} Hz')
    
    # plot the fids
    offset = 8000               # offset curves
    fig,ax = plt.subplots(1,1)
    fig.canvas.manager.window.move(100,100)    
    ax.plot(time_series, fid1.real, label="reference fid")
    ax.plot(time_series,fid2.real+offset, label="drifted fid")
    ax.plot(time_series,aligned_fid.real-offset, label="aligned fid")
    ax.set_title('fids')
    ax.legend()
    plt.xlabel("Time (s)")
    
    # plot the cross spectrum
    fig,ax = plt.subplots(1,1)
    fig.canvas.manager.window.move(200,200)    
    ax.plot(freqs, cspect.real, label="real cross spectrum")
    ax.plot(freqs, cspect.imag, label="imaginary cross spectrum")
    ax.plot(freqs, np.abs(cspect), label="mag cross spectrum")
    ax.set_title('cross spectrum')
    ax.legend()
    plt.xlabel("Frequency (Hz)")
