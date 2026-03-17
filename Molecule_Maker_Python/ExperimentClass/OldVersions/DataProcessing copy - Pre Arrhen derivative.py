import statsmodels.api as sm
from statsmodels.nonparametric.smoothers_lowess import lowess

import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
import sys, copy, os
import nmrglue as ng
import pandas as pd
from scipy import optimize
from scipy.optimize import curve_fit
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
from skimage import restoration
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
class ScanData:
    def __init__(self, ppm, intensities):
        self.ppm = ppm
        """ppm data as a list"""

        self.intensities = intensities
        """Intensity data as a list"""
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
        case 3:
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
            tdata = ng.proc_autophase.autops(tdata, fn='acme') #This may need adjusted
            tdata = ng.proc_base.di(tdata)
            spect = tdata
            #spect = np.fft.fft(tdata, zero_pad)
            spect = np.fft.fftshift(spect)

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
        case 3:
            #The Random Method
            dic, data = ng.fileio.jcampdx.read(fn)
            udic = ng.fileio.jcampdx.guess_udic(dic, data)
   
            tdata = np.array(data)
            tdata = tdata[0, :] + 1.0j * tdata[1, :]

        
            data_ft = ng.proc_base.fft(tdata)
            data_aph = ng.proc_autophase.autops(data_ft, fn='peak_minima')
            data_aph = np.real(data_aph)
                
            npts = len(data_aph)
            xax_max = np.argmax(data_aph)
            
            #FIXME ADD OFFSET CORRECTION
            offset = 0
            left_pt =offset - udic[0]['sw']/2
            right_pt = offset+ udic[0]['sw']/2
            xax = np.linspace(right_pt, left_pt, npts)
            final_data = {}
            final_data["intensity"] = spect
            final_data["PPM"] = list(data_aph)
            

    good_scan = verify_NMR_data(final_data)
    return_data = ScanData(final_data["PPM", final_data["intensity"]])
    print(f"Is good scan?: {good_scan}")
    return good_scan, return_data, udic

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

def find_indices_in_range(data, lower_bound, upper_bound):
    """
    Finds the indices of values within a specified range in a list.
    """
    indices = []
    for index, value in enumerate(data):
        if lower_bound <= value <= upper_bound:
            indices.append(index)
    return indices

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
    spectral_lines = find_lines_threshold(noise, noise_factor=0.21) #OPTIMIZE 0.21 good, 0.15
    #spectral_lines = find_lines_derivative(noise)

    #Convert Spectral Lines to Peaks
    spectral_dataframe = pd.DataFrame()
    spectral_dataframe['Line Center'] = spectral_lines['line_center']
    spectral_dataframe['Line Type'] = spectral_lines['line_type']
    spectral_peaks =  [spectral_dataframe['Line Center'][i].value for i in spectral_dataframe.index if spectral_dataframe['Line Type'][i] == 'emission']
    peak_centers = spectral_peaks.copy()

    #TODO: Rolling ball algorithm for reducing noise
    background = restoration.rolling_ball(intensities, radius=1)
    intensities = background

    #Plot spectra with peaks marked
    for peak in peak_centers:
        plt.axvline(x=peak, color='g', linestyle='--', linewidth=.5)
    plt.xlim(-15,5)
    plt.savefig("./spectrum_with_marked_peaks.png")
    plt.legend()
    plt.clf()
 

    if len(peak_centers) > 0:

        #Shift peak centers to PPM scale and remove duplicates
        #TODO peak radius merging improvements
        for peak in peak_centers:
            peak = closest_value(peak, ppm)
        peak_centers = list(set(peak_centers))
        fitting_peaks = [] #List of peaks present in this particular spectra to fit

        for peak_ppm_center in peak_centers:
            peak_height = float(intensities[ppm.index(peak_ppm_center)])

            #If peak height is negative, remove
            if peak_height <= 0:
                print("Bad Peak: Negative,",peak_ppm_center)
                continue
            
            #Select Peaks for fitting:
            #Check if the peak is within the search range of existing peaks, if so new measurement
            already_exists = False
            for peak in good_peaks:
                if (peak.center_var[0] <= peak_ppm_center) and (peak_ppm_center <= peak.center_var[1]):
                    peak.new_measurement(peak_height)
                    fitting_peaks.append(peak)
                    already_exists = True
                    break

            #If it's a new peak, create a peak and append it to the peaks to fix
            if not already_exists:
                temp_peak = Peak(peak_ppm_center, peak_height)
                good_peaks.append(temp_peak)
                fitting_peaks.append(temp_peak)

            ### ONLY GOOD PEAKS BEYOND THIS POINT: THEY WILL NOT BE PARSED FURTHER AND FITS BEGIN ###
        
    
    #Setup Fit
    peaks_to_fit_list = []
    peak_fit_windows = [] #Stores the fitting window for each peak
    
    FIT_TYPE = 2
    ### Creating list of Fits to perform.  FIT_TYPE controls what algo. to use ###
    for peak in fitting_peaks:
        peak_fit_windows.append([peak.center_var[0],peak.center_var[1]])
        match FIT_TYPE:
            case 1:
                peaks_to_fit_list.append( models.Lorentz1D(x_0=peak.centers[-1], amplitude = peak.heights[-1], fwhm=peak.linewidth_G_initial,
                                                    bounds={
                                                        'x_0':peak.center_var,
                                                        'amplitude':peak.amplitude_var,
                                                        'fwhm':peak.linewidth_var
                                                    }
                                                    ))
            case 2:       
                peaks_to_fit_list.append( models.Gaussian1D(mean=peak.centers[-1], amplitude = peak.heights[-1], stddev=peak.linewidth_G_initial,
                                                    bounds={
                                                        'mean':peak.center_var,
                                                        'amplitude':peak.amplitude_var,
                                                        'stddev':peak.linewidth_var
                                                    }
                                                    ))
            case 3:            
                peaks_to_fit_list.append( models.Voigt1D(x_0=peak.centers[-1], amplitude_L = peak.heights[-1], fwhm_G=peak.linewidth_G_initial,fwhm_L=peak.linewidth_G_initial,
                                                    bounds={
                                                        'x_0':peak.center_var,
                                                        'amplitude_L':peak.amplitude_var,
                                                        'fwhm_L':peak.linewidth_var,
                                                        'fwhm_G':peak.linewidth_var
                                                    }
                                                    ))
    
    #Execute Fitting
    spectrum_fit = [0 for a in ppm]
    lists_to_add = []
    for index, fit in enumerate(peaks_to_fit_list):


        #Paramaters: Amp, Mean, Stddev
        #Create the fit for peak, convert to a list for data management
        this_fitting = fit_lines(spectrum, fit, fitter=fitting.TRFLSQFitter(),maxiter=10000, get_fit_info=True, window=peak_fit_windows[index]*u.dimensionless_unscaled, weights=intensities)
        this_fit = list(this_fitting(ppm*u.Hz))
        this_fit = [a.value for a in this_fit]

        parameters = this_fitting.parameters
        lists_to_add.append(this_fit)
        index = _get_peak_index(good_peaks,fitting_peaks[index].center)

        #Add params and fit to coresponding peak
        good_peaks[index].fwhm = parameters[2]
        good_peaks[index].centers.append(parameters[1]) 
        good_peaks[index].integrals.append(sum(this_fit))
        good_peaks[index].fit_scores.append(sum(abs(this_fit-intensities)))
        good_peaks[index].fits.append(this_fit)
        good_peaks[index].real_data.append([ppm, intensities])



        
        #spectrum_fit = [spectrum_fit[a] + this_fit[a] for a in range(len(spectrum_fit))]
    for fit in lists_to_add:
        spectrum_fit = [spectrum_fit[a] + fit[a] for a in range(len(spectrum_fit))]
    for peak in good_peaks:
        peak.full_fits.append(spectrum_fit)

    plt.plot(ppm, spectrum_fit, label="fit", linestyle=None,markersize =0.5)
    plt.plot(ppm, intensities, label="data", linestyle=None,markersize =0.5)
    plt.legend()
    plt.xlim(-15,5)
    plt.savefig(f"./full_fit.png")
    plt.clf()

    return good_peaks, spectrum_fit
    



def offset_nmr_data(ppm, intensities, reference):
    """Shift PPM scale to center largest peak to known reference position\n
    Input: PPM, intensities, reference_ppm\n
    Output: ppm"""
    reference_index = intensities.index(max(intensities))
    ppm_shift = ppm[reference_index] - reference
    ppm_shifted = [a - ppm_shift for a in ppm]
    return ppm_shifted
def get_shim_linewidth(ppm, intensities, reference_point):
    """Fit the largest peak (shim peak) and return linewidth\n
    Input: ppm, intensities, reference_point\n
    output: linewidth"""
    ppm = list(ppm)
    peak_index = ppm.index(reference_point)

    fits = models.Lorentz1D(x_0=reference_point, amplitude = intensities[peak_index], fwhm=0.05,
                                        bounds={
                                            'x_0':(reference_point-0.5,reference_point+0.5),
                                            'amplitude':(intensities[peak_index]-1000,intensities[peak_index]+1000),
                                            'fwhm':(0.03,0.1)
                                        }
                                        )

    
    fitter=fitting.TRFLSQFitter()
    this_fit = fitter(fits, ppm, intensities)
    print(this_fit)
    plt.plot(ppm,intensities, label=f"Data")
    plt.plot(ppm, this_fit(ppm))
    plt.savefig("./shimfit.png")
    params = this_fit.parameters
    print(params)
    return params[2]


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




#Have conc. at times
def find_90p_time(times, concentrations):

    arrhen_fit,  pcov= curve_fit(second_order_conc_to_time, xdata=concentrations,ydata=times, bounds=(0, [1, np.inf]))
    print(arrhen_fit(0.9))
    return arrhen_fit(0.9)

def second_order_arrhen_time_to_conc(t, A0, k):
    """Return arrheneous func."""
    return (1 - ( 1 / (k * t + 1 / (1-A0))))

def second_order_conc_to_time(x, A0, k):
    return ( ((1/(-x+1))-(1/(1-A0)) ) / k )

def nth_order_conc_to_time_product(x, k,n, amp=1):
    """Arrhen. equation for Nth order Product"""
    A0 = 0 #Initial conc. guess.  Fixed at 0
    ul = 1 / ( (1-x) ** (n-1) )
    ur = 1 /( ((1-A0)**(n-1))  )
    bottom = k * (n - 1)
    return (((ul-ur)/bottom) )


def product_90p_time(conc_x, time_y):
    """Return when arrhen. fit predicts a product to be at 90%\n Input: conc_list, time_list"""
    popt, pcov = curve_fit(nth_order_conc_to_time_product, conc_x, time_y, bounds=((0, 1.0001),(10, np.inf)), p0=(0.005, 3))

    k, n = popt
    error = np.sqrt(np.diag(pcov))

    print(nth_order_conc_to_time_product(0.99,k, n))
    y_pred = [nth_order_conc_to_time_product(x,k, n) for x in conc_x]
    squared_error_sum = 0
    for a in range(len(y_pred)):
        squared_error_sum += (time_y[a]-y_pred[a])**2
    MSE = (squared_error_sum**0.5) / len(y_pred)
    print(f"MSE: {MSE}")
    
    return (nth_order_conc_to_time_product(0.90,k, n))