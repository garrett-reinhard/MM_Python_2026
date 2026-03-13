import statsmodels.api as sm
from statsmodels.nonparametric.smoothers_lowess import lowess

import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
import sys, copy, os
import nmrglue as ng
import pandas as pd
from scipy import optimize
from scipy.signal import savgol_filter
import warnings
import math
import sys
import json
from datetime import datetime
import statistics as stat
from BaselineRemoval import BaselineRemoval
from astropy.modeling import models
from astropy.modeling import fitting
from astropy import units as u
from specutils.spectra import Spectrum1D, SpectralRegion
from specutils.fitting import fit_lines, find_lines_threshold, find_lines_derivative 
# from specutils.manipulation import box_smooth, gaussian_smooth, trapezoid_smooth
from specutils.manipulation import noise_region_uncertainty
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from sklearn import preprocessing
# warnings.filterwarnings('ignore')
# warnings.simplefilter('ignore', (AstropyWarning, AstropyUserWarning))
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
from nmrglue import fileiobase
from ExperimentClass.PeakClass import Peak
def repeat_point(points, low, high):
    """Check a list to see if a value"""
    for point in points:
        if low < point < high:
            return True
    return False
def delete_between(lst, min_val, max_val):
    """Deletes elements from a list that are between two given values"""
    lst[:] = [x for x in lst if not (min_val <= x <= max_val)]

def read_NMR(filepath, offset=0):
    """Read NMR file from QM, Verify if scan is good prior to returning data\n
    Input: filepath\n
    Output: goodScan(bool), """
    #Method 1: UC guess,
    #Method 2: QM method
    METHOD =  2
    print(f"Loading file: {filepath}")
    dic, data = ng.fileio.jcampdx.read(filepath)
    udic = ng.fileio.jcampdx.guess_udic(dic, data)

    match METHOD:
        case 1:
            #"""Method 1: Github convo, trying to recreate UC"""
            npoints = int(40000)
            tdata = np.empty((npoints,), dtype='complex128')
            tdata.real = data[0][:]
            tdata.imag = data[1][:]

            # Spectra (Y Axis)
            tdata = ng.proc_base.fft(tdata)
            tdata = ng.proc_autophase.autops(tdata, fn='peak_minima') #This may need adjusted
            tdata = ng.proc_base.di(tdata)

            #PPM - guessing (X axis)
            udic = ng.jcampdx.guess_udic(dic,tdata)
            uc = ng.fileiobase.uc_from_udic(udic)
            ppm_scale = uc.ppm_scale()

            final_data = {}
            final_data["intensity"] = tdata
            final_data["PPM"] = ppm_scale

        case 2:
            #Method 2: QM method
            """
            #From QM methods for reference
            seqclk_MHz = 160
            fL = self.p.child('Global','Tx freq').value() OR 124.2
            exact_spec_width_kHz = seqclk_MHz*1000/decimation 
            decimation = round(seqclk_MHz*1000/spars['spectral width'])

            self.mw.freqs = np.fft.fftfreq(self.ppars['zero pad'], 1/(self.exact_spec_width_kHz*1000))
            self.mw.freqs = np.fft.fftshift(self.mw.freqs)
            pfreqs = (self.freqs-offset)/fL   # convert freqs to ppm with offset
            """
            tdata = np.array(data)
            tdata = tdata[0, :] + 1.0j * tdata[1, :]

            #Paramater Identifying
            offset = 0
            fL = udic[0]['obs']
            fL_static = 124.2
            spectral_width = 10 # udic[0]['sw']?
            seqclk_MHz = 160
            zero_pad = 200000
            decimation = round(seqclk_MHz*1000/spectral_width)
            kHz_freqs = fL*1000
            exact_spec_width_kHz = seqclk_MHz*1000/decimation

            #Intensity (Y axis)
            # Spectra (Y Axis)
            tdata = ng.proc_base.fft(tdata)
            tdata = ng.proc_autophase.autops(tdata, fn='peak_minima') #This may need adjusted
            tdata = ng.proc_base.di(tdata)
            spect = tdata
            #spect = np.fft.fft(tdata, zero_pad)
            #spect = np.fft.fftshift(spect)

            zero_pad = len(spect)
            #PPM axis (X axis)
            freqs = np.fft.fftfreq(zero_pad, 1/(exact_spec_width_kHz*1000))
            #freqs = np.fft.fftshift(freqs)  
            freqs = (freqs-offset)/fL

            #Try making Udic with this data method
            """
            udic = ng.jcampdx.guess_udic(dic,spect)
            uc = ng.fileiobase.uc_from_udic(udic)
            ppm_scale = uc.ppm_scale()
            """
            final_data = {}
            final_data["intensity"] = spect
            final_data["PPM"] = freqs


    #plt.scatter(final_data["PPM"],final_data["intensity"])
    #plt.xlim(25,40)
    #plt.savefig(fr"./")
    good_scan = verify_NMR_data(final_data)
    print(good_scan)
    return good_scan, final_data, udic

# Algorithm to determine whether or not the spectrum is good or not for analysis
def verify_NMR_data( data, phasing_range=None):
    """Confirm if NMR data is good or bad\n
    input: data(dict with intensity and PPM), phasing range(optional, legacy)"""
    isGood = True
    data["intensity"] = [point.real for point in data["intensity"]]
    data_in_range = []
    if not phasing_range==None:
        for y in data.index:
            if min(phasing_range) <= data['PPM'][y] <= max(phasing_range):
                data_in_range.append(data["intensity"][y])
    else:
        data_in_range = data["intensity"]

    # If spectrum is not good, tell ARES to re-run NMR loop
    average_signal = sum(data_in_range)/len(data_in_range)
    noise = stat.stdev(data_in_range)
    snr = calculate_snr(data)
    signals_above_average = (len([i for i in data_in_range if i >= average_signal])/len(data_in_range)*100)
    signals_above_noise = (len([i for i in data_in_range if i >= noise])/len(data_in_range)*100)

    average_signal_full = sum(data["intensity"])/len(data["intensity"])
    noise_full = stat.stdev(data["intensity"])
    snr_full = calculate_snr(data)
    signals_above_average_full = (len([i for i in data["intensity"] if i >= average_signal_full])/len(data["intensity"])*100)
    signals_above_noise_full = (len([i for i in data["intensity"] if i >= noise_full])/len(data["intensity"])*100)
    
    #Rejected Rationale#
    rejected_spectrum_rationale = []
    if signals_above_average > 30:
        isGood = False
        rejected_spectrum_rationale.append('Fragment Above Average')
    if signals_above_noise > 50:
        # isGood = False
        rejected_spectrum_rationale.append('Testing: Fragment Above Noise')
    if snr < 9:
        # isGood = False
        rejected_spectrum_rationale.append('Testing: Fragment Below SNR')
    if signals_above_average_full > 30:
        isGood = False
        rejected_spectrum_rationale.append('Full Above Average')
    if signals_above_noise_full > 50:
        isGood = False
        rejected_spectrum_rationale.append('Full Above Noise')
    if snr_full < 9:
        # isGood = False
        rejected_spectrum_rationale.append('Testing: Full Below SNR')               


    if len(rejected_spectrum_rationale) > 0:
        print("Data rejected")
        print(rejected_spectrum_rationale)
        
    # If spectrum is good, continue with analysis

    # Return value of isGood
    return isGood



def peak_finding(data, good_peaks = []):
    """Input data dictionary with PPM and intensity, returns: ?"""
    ppm = data["PPM"]
    intensities = data["intensity"]

    #Filter noise from data
    intensities = savgol_filter(intensities,41, 3)
    spectrum = Spectrum1D(flux=[y for y in intensities]*u.dimensionless_unscaled, spectral_axis=[x for x in ppm]*u.Hz)
    
    ### Auto Peak Detection ###
    noise_region = SpectralRegion(min(ppm)*u.Hz, max(ppm)*u.Hz)
    noise = noise_region_uncertainty(spectrum, spectral_region=noise_region)
    #Pick one?
    spectral_lines = find_lines_threshold(noise, noise_factor=0.20) #OPTIMIZE 0.21 good, 0.15
    #spectral_lines = find_lines_derivative(noise)
    #plt.plot(ppm, intensities, label='data')
    #plt.savefig("./")
    #plt.clf()
    #Convert Spectral Lines to Peaks
    spectral_dataframe = pd.DataFrame()
    spectral_dataframe['Line Center'] = spectral_lines['line_center']
    spectral_dataframe['Line Type'] = spectral_lines['line_type']
    spectral_peaks =  [spectral_dataframe['Line Center'][i].value for i in spectral_dataframe.index if spectral_dataframe['Line Type'][i] == 'emission']
    peak_centers = spectral_peaks.copy()

 
    # Gaussian Lineshapes #FIXME implement pseodo~voight fitting
    # Setting up the fitting function with Gaussian lineshapes
    print("solvent peak length before: ", len(peak_centers))

    #peaks_to_fit = models.Gaussian1D
    peaks_to_fit = []
    if len(peak_centers) > 0:

        #Shift peak centers to PPM scale and remove duplicates
        #TODO peak radius merging
        for peak in peak_centers:
            peak = closest_value(peak, ppm)
        peak_centers = list(set(peak_centers))

        for peak_ppm_center in peak_centers:
            peak_height = float(intensities[ppm.tolist().index(peak_ppm_center)])

            #If peak height is negative, remove
            if peak_height <= 0:
                print("Bad Peak: Negative,",peak_ppm_center)
                continue
            
            ### ONLY GOOD PEAKS BEYOND THIS POINT ###
            
            #If peak is in Goodpeaks already, add the amplitude to the list of amplitudes and increase occurences
            #Else, add it to Good Peaks
            #TODO This is where I can add shifting for PPM shifts
         
            already_exists = False
            
        for peak in good_peaks:
            
            delete_between(peak_centers, peak.center_var[0],peak.center_var[1])
            
            
            #height= max(intensities[ppm.tolist().index(peak_ppm_center)])
            peak.new_measurement(peak.heights[-1])
        #input()

        for peak_ppm_center in peak_centers:
            peak_height = float(intensities[ppm.tolist().index(peak_ppm_center)])
            good_peaks.append(Peak(center=peak_ppm_center, height=peak_height))
                
                    

    #Setup Fit
    for peak in good_peaks:
            peaks_to_fit.append( models.Gaussian1D(mean=peak.centers[-1], amplitude = peak.heights[-1], stddev=peak.linewidth_G_initial,
                                                bounds={
                                                    'mean':peak.center_var,
                                                    'amplitude':peak.amplitude_var,
                                                    'stddev':peak.linewidth_var
                                                }
                                                ))
            
    #Execute Fitting
    spectrum_fit = [0 for a in ppm]
 
    for index, fit in enumerate(peaks_to_fit):
        #Paramaters: Amp, Mean, Stddev
        #Create the fit for peak, convert to a list for data management
        this_fitting = fit_lines(spectrum, fit, fitter=fitting.TRFLSQFitter(),maxiter=100, get_fit_info=True, window=[good_peaks[index].centers[-1]*u.Hz - 0.3*u.Hz, good_peaks[index].centers[-1]*u.Hz+0.3*u.Hz])
        this_fit = list(this_fitting(ppm*u.Hz))
        this_fit = [a.value for a in this_fit]

        parameters = this_fitting.parameters
        #total_fit_list += this_fit
       
        #fig = px.scatter(x=ppm,y=this_fit)
        #fig.show()
        #del fig
        #plt.scatter(ppm, intensities)
        #plt.scatter(ppm, this_fit)
        

        #plt.savefig(f"./{index}")
        
        #Add params and fit to coresponding peak
        good_peaks[index].fwhm = parameters[2]
        good_peaks[index].centers.append(parameters[1]) 
        good_peaks[index].integrals.append(sum(this_fit))
        good_peaks[index].fit_scores.append(sum(abs(this_fit-intensities)))
        good_peaks[index].fits.append(this_fit)
        good_peaks[index].real_data.append([ppm, intensities])
        spectrum_fit = [spectrum_fit[a] + this_fit[a] for a in range(len(spectrum_fit))]
    #fig.show()  
    
    plt.plot(ppm, spectrum_fit, label="fit", linestyle=None)
    plt.plot(ppm, intensities, label="data", linestyle=None)
    plt.xlim(30, 40)
    plt.legend()
    plt.savefig("./full_fit.png")
    plt.clf()
    return good_peaks, spectrum_fit







def closest_value(value, values, within = np.inf):
    """Shifts a value to the closest value in a list, within a range if specified
    Input: Value to shift, List of values"""
    closest = max([v for v in values if v <= value])
    if abs(closest-value) < within:
        return closest
    else:
        return value


def _get_peak_index(instances, target_value):
    """Returns index of desired peak PPM"""
    for index, instance in enumerate(instances):
        if instance.center == target_value:
            return index


def calculate_snr(data): 

    """Calculate the signal-to-noise ratio of an NMR spectrum""" 
    signal = max(data["intensity"])
    noise = stat.stdev(data["intensity"])
    snr = signal / noise 
    return snr

def end_point_fit(x,t, c):
    """This function is the function to determin end point of reaction
    Inputs: x point, t(end time guess), c(steepness guess)"""
    
    if x < t/2:
        y = ((2*x/t)**c)/2
    else:
        y = 1 - ((((2*x/t)-2)**c)/2)
    
    return y

