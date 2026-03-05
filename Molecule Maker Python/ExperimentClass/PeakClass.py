import statsmodels.api as sm
from statsmodels.nonparametric.smoothers_lowess import lowess

import matplotlib.pyplot as plt
import numpy as np
import sys, copy, os
import nmrglue as ng
import pandas as pd
from scipy import optimize
from scipy.signal import savgol_filter
import warnings
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
class Peak:
    """Class for storing information on peaks, used to fit and track behavior over time"""
    def __init__(self, center,height):
        self.type = "none"
        self.center = round(center, ndigits=4)
        self.plot_name = round(center, ndigits=4)
        self.range = (center-1,center+1)
        self.centers=[center]
        self.prefit_centers = [center]
        self.fwhm = float

        #Fitting Ranges
        self.amplitude_var = (0, np.inf)
        self.linewidth_var = (0, 0.05) # 1 default gauss
        self.linewidth_G_initial = 0.01 #initial sharpness guess
        self.center_variance = 0.05
        self.center_var = (min(self.centers)-self.center_variance, max(self.centers)+self.center_variance) #Width to not include duplicate peaks

        self.score = 0
        self.score_list = [] #Used for maintaining score history for plotting

        self.occurances = 1
        self.measurement_times = []
        self.measurement_concentrations = []
        self.starting_volume = 0
        self.heights=[height]
        
        self.fits=[]
        self.real_data=[]
        self.integrated_areas=[]
        self.fit_errors = []
        self.predicted_times = []
        self.times_with_predictions = [] #Stores what times have succsessful time predictions.  Used for plotting
        self.save_folder = ""
        #T0 values
        self.t0_ppm = center
        self.t0_heigh = height
        self.full_fits = []

        

    def new_measurement(self, height, new_center):
        self.heights.append(height)
        self.prefit_centers.append(new_center)
        new_mean_center = (new_center+self.centers[-1])/2
        self.prefit_centers.append(new_center)

        if new_mean_center > self.centers[-1]:
            self.center_var = (self.center_var[0], self.center_var[1]+self.center_variance)
        elif new_mean_center < self.centers[-1]:
            self.center_var = (self.center_var[0]-self.center_variance, self.center_var[1])

        self.occurances +=1

    def update_score(self):
        """Function to determine the 'score' or a peak and classify it as a reactant or product"""
        temp_score = 0
        if len(self.measurement_concentrations) > 1:
            for index, instance in enumerate(self.measurement_concentrations[1:]):
                if self.measurement_concentrations[index-1] > instance:
                    temp_score -= 1
                elif self.measurement_concentrations[index-1] < instance:
                    temp_score += 1
                

            self.score_list.append(temp_score)
            self.score = temp_score

            if self.score >=3 :
                self.type = "product"
            elif self.score <=-3 :
                self.type = "reactant"
            else:
                self.type="none"
    

    def plot_score(self):
        os.makedirs(f"{self.save_folder}/score_plots",exist_ok=True)
        plt.plot(self.score_list, marker='o')
        plt.savefig(f"{self.save_folder}/score_plots/{self.plot_name}_score.png")
        plt.clf()
    def plot_predicted_times(self):
        os.makedirs(f"{self.save_folder}/predicted_time_plots",exist_ok=True)
        print(f"{self.times_with_predictions} With {self.predicted_times}")
        plt.scatter(self.times_with_predictions,self.predicted_times, marker='o')
        plt.savefig(f"{self.save_folder}/predicted_time_plots/{self.plot_name}_times.png")
        plt.clf()

    def plot_fits(self):
  
        self.center_var = (min(self.centers)-self.center_variance, max(self.centers)+self.center_variance)
        for index, fit in enumerate(self.fits):
            os.makedirs(f"{self.save_folder}/fits", exist_ok=True)
            plt.plot(self.real_data[index][0],fit, label=f"{index}", marker='o')
            plt.plot(self.real_data[index][0],self.real_data[index][1], label=f"{index}_data", marker='o')
            plt.axvline(x=self.center_var[0], color='g', linestyle='--', linewidth=0.5)
            plt.axvline(x=self.center_var[1], color='g', linestyle='--', linewidth=0.5)
            plt.axvline(x=self.centers[index], color='r', linestyle='--', linewidth=0.5)
            plt.xlim(self.center_var[0]-0.3, self.center_var[1]+0.3)
            plt.ylim(0,1000000)
            plt.legend()
            plt.savefig(f"{self.save_folder}/fits/{self.plot_name}_{index}_fits.png")
            plt.clf()
        