import statsmodels.api as sm
from statsmodels.nonparametric.smoothers_lowess import lowess

import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
from scipy.optimize import curve_fit
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



slow_x = [1,2,3,4,5,6,7,8,9,10]
slow_y = [0.02, 0.03, 0.07, 0.1, 0.14, 0.18, 0.17, 0.15, 0.2, 0.24]

time_y = pd.read_csv(r"C:\Users\dryan.local\Desktop\Molecule Maker Python\ExperimentClass\NotSystemIntegrated\progress.csv")["X"].to_list()
conc_x = pd.read_csv(r"C:\Users\dryan.local\Desktop\Molecule Maker Python\ExperimentClass\NotSystemIntegrated\progress.csv")["Y"].to_list()

def conc_rate_of_change_to_time(x,k,n):
    return 1 / k * (1 - x)**(-n)
def time_to_conc_rate_of_change(t, k, n):
    return 1 - (t * k)**(-1/n)

def second_order_conc_to_time(x, k,amp = 1):
    return (amp * ((1/(-x+1))-(1/(1)) ) / k )

def nth_order_conc_to_time(x, k,n, amp=1):
    "Working"
    A0 = 0 #Initial conc. guess.  Fixed at 0
    ul = 1 / ( (1-x) ** (n-1) )
    ur = 1 /((1-A0)**(n-1))
    bottom = k * (n - 1)
    return ((amp * (ul-ur)/bottom) )



# # # PRODUCT FORMULAS # # #
def time_to_nth_order_conc(t, k, n, amp=1):
    C = (k * (n - 1) / (amp)) * t
    return 1 - (1 / (1 + C)) ** (1 / (n - 1))

def time_to_nth_order_conc_derivative(t, k, n, amp=1):
    C = (k * (n - 1) / amp) * t
    return (k / amp) * (1 + C)**(-n / (n - 1))

def time_to_nth_order_conc_derivative_inverted(x, k, n, amp=1):
    return (amp / (k * (n - 1))) * ((x * amp / k)**(-(n - 1) / n) - 1)

def nth_order_time_to_conc(x, k,n, amp=1):
    A0 = 0.000 #Initial conc. guess.  Fixed at 0
    bl = 1/(A0**(n-1))
    br = k*x*(n-1)
    bottom = bl-br
    return (amp * (1/bottom)**(1/(n-1)))

# # # REACTANT FORMULAS # # #
def reactant_time_to_conc(t,k,n, A0=1):
    #A0 = 1 #A0 is initial amount in reaction; currently assumed to be 100%
    return (A0**(1 - n) + (n - 1) * k * t) ** (1 / (1 - n))

def reactant_time_to_conc_derivative(t, k, n, A0=1):
    inside = A0**(1 - n) + (n - 1) * k * t
    return -k * inside**(n / (1 - n))

def reactant_time_to_conc_derivative_inverted(y, k, n, A0=1):
    # y is the derivative value: y = dC/dt
    inside = (-y / k)**((1 - n) / n)
    return (inside - A0**(1 - n)) / ((n - 1) * k)

norm = [i/max(conc_x) for i in conc_x]
sigma = [1/(x) for x in conc_x]
#popt, pcov = curve_fit(second_order_conc_to_time, conc_x, time_y, bounds=((0, 1),(1, np.inf)), p0=( 0.1, 10))
fit_type = 7 # 1=Nth, 2=2nd, 4=nth with amp (time to conc), 5: Fit Conc->time, use ROC to find next point
match fit_type:
    case 1:
        popt, pcov = curve_fit(nth_order_conc_to_time, conc_x, time_y, bounds=((0, 1.0001),(10, np.inf)), p0=(0.005, 3))

        k, n = popt
        error = np.sqrt(np.diag(pcov))
        #plot_points = np.arange(0,t, t/1000)

        print(popt)
        #print(pcov)


        plt.plot(time_y,conc_x,  label='data')
        plt.legend()
        #plt.show()

        

        print(nth_order_conc_to_time(0.99,k, n))
        y_pred = [nth_order_conc_to_time(x,k, n) for x in conc_x]
        squared_error_sum = 0
        for a in range(len(y_pred)):
            squared_error_sum += (time_y[a]-y_pred[a])**2
        print(len(y_pred))
        MSE = (squared_error_sum**0.5) / len(y_pred)
        print(MSE)
        plt.scatter(y_pred,conc_x , label=f'fit, Cov:{error}')
        plt.legend()
        plt.show()
    case 2:

        popt, pcov = curve_fit(second_order_conc_to_time, conc_x, time_y, bounds=((0),(1)), p0=( 0.25))

        k = popt
        error = perr = np.sqrt(np.diag(pcov))
        #plot_points = np.arange(0,t, t/1000)

        print(popt)
        #print(pcov)


        plt.plot(time_y,conc_x,  label='data')
        plt.legend()
        #plt.show()




        y_slow = [second_order_conc_to_time(x,k) for x in conc_x]
        plt.scatter(y_slow,conc_x , label=f'fit, Cov:{error}')
        plt.legend()
        plt.show()

    case 3:

        popt, pcov = curve_fit(nth_order_time_to_conc, time_y, conc_x, bounds=((0, 2),(1, np.inf)), p0=(0.2, 2))

        k, n = popt
        error = perr = np.sqrt(np.diag(pcov))
        #plot_points = np.arange(0,t, t/1000)

        print(popt)
        #print(pcov)


        plt.plot(time_y,conc_x,  label='data')
        plt.legend()
        #plt.show()




        y_slow = [nth_order_conc_to_time(x,k, n) for x in conc_x]
        plt.scatter(y_slow,conc_x , label=f'fit, Cov:{error}')
        plt.legend()
        plt.show()

    case 4:
        #Fit Then Scale
        time_x = time_y
        conc_y = [a*0.7 for a in  conc_x] 
        popt, pcov = curve_fit(time_to_nth_order_conc, time_x,conc_y, bounds=((0, 1.0001),(10, np.inf)), p0=(0.005, 3))

        k, n = popt
        print(popt)
        error = np.sqrt(np.diag(pcov))
      

        def scaled_time_to_nth_order_conc(x, scalar):
            return scalar * time_to_nth_order_conc(x,k,n)
        popt_scaled, pcov_scaled = curve_fit(scaled_time_to_nth_order_conc, time_x,conc_y, bounds=((0),(1)), p0=(0.5))
        print(f"scalar {popt_scaled}")
        scalar = popt_scaled
        #print(pcov)

        
        plt.plot(time_x  ,conc_y,label='data')
        plt.legend()
#        plt.show()

        new_finish_time = nth_order_conc_to_time(0.99, k, n, amp=scalar)
        def scaled_nth_order_conc_to_time(x,scalar):
            return nth_order_conc_to_time(x, k, n) * scalar


        print(f"time for 'completion': {new_finish_time}")
        print(time_to_nth_order_conc(10,k, n, amp=scalar))
        x_list = [a for a in range(0, 50)]
        #print(x_list)
        y_pred = [time_to_nth_order_conc(x,k, n, amp=scalar) for x in time_x]
        y_pred_2 = [time_to_nth_order_conc(x,k, n, amp=scalar) for x in x_list]
        #print(y_pred)
        squared_error_sum = 0

        plt.scatter(time_x, y_pred , label=f'fit, k,n:{popt}\n scalar: {scalar}')
        #plt.scatter(x_list, y_pred_2 , label=f'fit, Cov:{error}') #Linear spread points
        plt.legend()
        plt.show()
    case 5:
        #Fit and scale
        #time_x = time_y
        #conc_y = [a*0.7 for a in  conc_x] 

        #Fit Conc->Time Curve; Plot.
        popt, pcov = curve_fit(nth_order_conc_to_time, conc_x,time_y, bounds=((0, 1.0001),(10, np.inf)), p0=(0.005, 3))
        k, n = popt
        error = np.sqrt(np.diag(pcov))

        #Prep Prediction list; plot
        x_list = [a for a in range(0, 50)]
        y_pred = [nth_order_conc_to_time(x,k, n) for x in conc_x]
        y_pred_2 = [nth_order_conc_to_time(x,k, n) for x in x_list]
        plt.plot(conc_x  ,time_y,label='data') #Plot Data
        plt.scatter(conc_x, y_pred , label=f'fit, k,n:{popt}') #Plot Fit
        plt.legend()
        plt.show()

        rate_of_change = [time_to_conc_rate_of_change(x,k, n) for x in conc_x]
        plt.scatter(conc_x, rate_of_change , label=f'fit, k,n:{popt}') #Plot Fit
      
        plt.show()
        #Calculate Finish Time
        new_finish_time = time_to_conc_rate_of_change(0.95, k, n)
        print(f"time for 'completion': {new_finish_time}")
    case 6:
        #Time to Conc. for product
        #This is goated and works perfectly. Use it. Please.
        max_time_measurements = 20
        current_time =20
        x_scaler = 0.20
        y_scaler = 12
        completed_rate = 0.005 / x_scaler * y_scaler

        time_x = [a*x_scaler for a in time_y if a < max_time_measurements]
        conc_y = [a*y_scaler for a in  conc_x]
        conc_y = conc_y[0:len(time_x)]
        #Fit Conc->Time Curve; Plot.
        popt, pcov = curve_fit(time_to_nth_order_conc, time_x,conc_y, bounds=((0, 1.0001),(10, np.inf)), p0=(0.005, 3))
        k, n = popt
        error = np.sqrt(np.diag(pcov))

        #Prep Prediction list; plot
        x_list = [a for a in range(0, 50)]
        y_pred = [time_to_nth_order_conc(x,k, n) for x in time_x]
        y_pred_2 = [time_to_nth_order_conc(x,k, n) for x in x_list]
        
        

        #rate_of_change = [time_to_nth_order_conc_derivative(x,k, n) for x in time_x]
        #plt.scatter(time_x, rate_of_change , label=f'fit, k,n:{popt}') #Plot Fit
        #plt.show()

        #Calculate Finish Time
        new_finish_time = time_to_nth_order_conc_derivative_inverted(completed_rate, k, n)

        #Plot
        plt.plot(time_x  ,conc_y,label='data') #Plot Data
        plt.scatter(time_x, y_pred , label=f'fit, k,n:{popt}\nPred. End Time: {new_finish_time}\nNext Measure: {(new_finish_time-current_time)/2+current_time}') #Plot Fit
        plt.legend()
        plt.vlines(new_finish_time,min(y_pred),max(y_pred))
        plt.show()
        print(f"time for 'completion': {new_finish_time}")
    case 7:
            #Time to Conc. for reactnat
            #This is goated and works perfectly. Use it. Please.
            max_time_measurements = 20
            current_time =20
            x_scaler = 1
            y_scaler = 0.5
            completed_rate = 0.005 / x_scaler * y_scaler

            time_x = [a*x_scaler for a in time_y if a < max_time_measurements]
            conc_y = [(1-a)*y_scaler for a in  conc_x]
            conc_y = conc_y[0:len(time_x)]
            #Fit Conc->Time Curve; Plot.
            popt, pcov = curve_fit(reactant_time_to_conc, time_x,conc_y, bounds=((0, 1.0001, 0),(10, np.inf, 1)), p0=(0.005, 3, 1))
            k, n, A0 = popt
            error = np.sqrt(np.diag(pcov))

            #Prep Prediction list; plot
            x_list = [a for a in range(0, 50)]
            y_pred = [reactant_time_to_conc(x,k, n, A0) for x in time_x]
            y_pred_2 = [reactant_time_to_conc(x,k, n, A0) for x in x_list]
            
            

            #rate_of_change = [time_to_nth_order_conc_derivative(x,k, n) for x in time_x]
            #plt.scatter(time_x, rate_of_change , label=f'fit, k,n:{popt}') #Plot Fit
            #plt.show()

            #Calculate Finish Time
            new_finish_time = reactant_time_to_conc_derivative_inverted(completed_rate, k, n, A0)

            #Plot
            plt.plot(time_x  ,conc_y,label='data') #Plot Data
            plt.scatter(time_x, y_pred , label=f'fit, k,n:{popt}\nPred. End Time: {new_finish_time}\nNext Measure: {(new_finish_time-current_time)/2+current_time}') #Plot Fit
            plt.legend()
            plt.vlines(new_finish_time,min(y_pred),max(y_pred))
            plt.show()
            print(f"time for 'completion': {new_finish_time}")

