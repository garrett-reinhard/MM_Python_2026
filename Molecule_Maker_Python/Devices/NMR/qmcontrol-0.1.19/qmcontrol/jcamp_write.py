# -*- coding: utf-8 -*-
"""
Created on Sat May  1 18:50:40 2021

@author: John Price
"""
import numpy as np
#import matplotlib.pyplot as plt
import datetime
import os
#import math

#from from_nmrglue import jcampdx
import qmcontrol.interface_constants as ic
#import settings


# takes an integer array data_array = (npoints,)  (real or imag part)
# makes an SQZ format data string
def jcamp_SQZ_string(data_array, time_step, real_or_imag = 'R'):

    nums_per_line = 12
    data_array = data_array.astype('int16') # make sure data is integer
    
    # substitutions for first digit
    SQZ_plus = {'1':'A', '2':'B', '3':'C', '4':'D',
                '5':'E', '6':'F', '7':'G', '8':'H', '9':'I'}   
    SQZ_minus = {'1':'a', '2':'b', '3':'c', '4':'d',
                '5':'e', '6':'f', '7':'g', '8':'h', '9':'i'}   
    
    ri = real_or_imag
    out = '##DATA TABLE=   (X++(' +ri+'..'+ri+ ')), XYDATA\n'
    out = out + '0'   # first time
    line = 1
    
    for i, num in enumerate(data_array):
        sn = str(num)
        sna = str(abs(num))
        if num == 0:
            out = out + '@'
        elif 0 < num < 10:
            out = out + SQZ_plus[sn[0]]
        elif num >= 10:
            out =  out + SQZ_plus[sn[0]] + sn[1:]
        elif -10 < num < 0:
            out = out + SQZ_minus[sna[0]]
        elif num <= -10:
            out = out + SQZ_minus[sna[0]] + sna[1:]
        rem = (i+1) % nums_per_line   # = 0 if end of line
        if rem == 0 and i < len(data_array):
            out = out + '\n'
            out = out + "{:.6f}".format((line*nums_per_line)*time_step)
            line = line + 1
            
    out = out + '\n'      
    return out


# takes an integer array data_array = (npoints,2)
# makes an SQZ format string for an entire fid, real and imag
def jcamp_FID_string(data_array, time_step):
    npoints = len(data_array[0])
    last_time = time_step*(npoints-1)
    out = \
"""##NTUPLES=       NMR FID
##VAR_NAME=         TIME,        FID/REAL,   FID/IMAG,    PAGE NUMBER
##SYMBOL=           X,           R,          I,           N
##VAR_TYPE=         INDEPENDENT, DEPENDENT,  DEPENDENT,   PAGE
##VAR_FORM=         AFFN,        ASDF,       ASDF,        AFFN
"""
    out = out + f'##VAR_DIM=          {npoints},   {npoints},   {npoints},   2\n'
    out = out +  '##UNITS=            SECONDS, ARBITRARY UNITS, ARBITRARY UNITS,\n'
    out = out + f'##FIRST=            0,    {data_array[0,0]},    {data_array[1,0]},     1\n'
    out = out + f'##LAST=       {last_time},    {data_array[0,-1]},    {data_array[1,-1]},     2\n'
    out = out + f'##MIN=              0,    {np.min(data_array[0])},    {np.min(data_array[1])},     1\n'
    out = out + f'##MAX=        {last_time},    {np.max(data_array[0])},    {np.max(data_array[1])},     2\n'
    out = out +  '##FACTOR=           1,    1,    1,     1\n'
    out = out + '##PAGE=  N=1\n'
    out = out + jcamp_SQZ_string(data_array[0], time_step, real_or_imag = 'R')
    out = out + '##PAGE=  N=2\n'
    out = out + jcamp_SQZ_string(data_array[1], time_step, real_or_imag = 'I')
    out = out + '##END TUPLES=  NMR FID\n##END=\n'
    
    return out


# for nscan_pulse_acq run
# takes an integer array data_array = (npoints,2)
# make a complete jcamp file string for one fid
def jcamp_nscan_pulse_acq_string(data_array, fpars, spars, ppars, gpars, mpars, vpars, file_suffix):
    
    # freq bin offset from lowest for MNova
    # this must be in the 3rd slot of SHIFT REFERECE or MNova will
    # offset the spectrum
    samples = len(data_array[0])
    offset = samples/2 +0.5

    delay = spars['pulse time']/2 + spars['Rx delay 1'] + spars['Rx delay 2']
    p = spars["filter atten"] - 4
    decimation  = spars["decimation"]
    gain = decimation**2/2**p
    time_step = (decimation/ic.seqclk_MHz)*10**-6  # data time step in s
    out = ''
    
    out = out + f'##TITLE=   {fpars["data directory"]}/{fpars["data filename"]}{file_suffix}.jdx\n'
    out = out +\
"""##JCAMP-DX=         6.0
##DATA TYPE=        NMR FID
##DATA CLASS=       NTUPLES
"""
    out = out + f'##ORIGIN=  {fpars["user name"]}\n'
    out = out + f'##OWNER=   {fpars["institution"]}\n'
    out = out + f'##LONG DATE= {datetime.datetime.now().isoformat()}\n'
    # out = out + f'##SPECTROMETER/DATA SYSTEM= {vpars["spectrometer"]}\n'
    out = out + f'##SAMPLE DESCRIPTION= {fpars["sample"]}\n'    
    out = out + f'##.SOLVENT NAME= {fpars["solvent"]}\n'
    out = out + f'##.SHIFT REFERENCE= INTERNAL,  ,{offset}  ,0\n'
    out = out + f'##.OBSERVE FREQUENCY= {gpars["Tx freq"]}  $$ MHz\n'
    out = out + f'##.OBSERVE NUCLEUS= ^1H\n'
    out = out + f'##.ACQUISITION MODE= SIMULTANEOUS\n'
    out = out + f'##.DELAY= ({delay},{delay})  $$ us\n'
    out = out + f'##.PULSE SEQUENCE= {fpars["pulse sequence"]}\n'
    out = out + f'##$QM_RUN_NOTES= {fpars["notes"]}\n'
    out = out + f'##$QM_RUN_TYPE= {fpars["run type"]}\n'
    out = out + f'##$QM_TRACK_TX= {ppars["track Tx freq"]}\n'
    out = out + f'##$QM_NSCANS= {spars["scans"]}\n'
    out = out + f'##$QM_EQUILIB_SCANS= {spars["equilib. scans"]}\n'
    out = out + f'##$QM_PULSE_LENGTH= {spars["pulse time"]}  $$ us\n'
    out = out + f'##$QM_ACQUISITION_SAMPLES= {len(data_array[0])}\n'
    out = out + f'##$QM_RX_RECOVERY_1= {spars["Rx delay 1"]}  $$ us\n'
    out = out + f'##$QM_RX_RECOVERY_2= {spars["Rx delay 2"]}  $$ us\n'
    out = out + f'##$QM_T1_DELAY= {spars["recovery time"]}  $$ s\n'
    out = out + f'##$QM_SPECTRAL_WIDTH= {spars["spectral width"]}  $$ kHz\n'
    out = out + f'##$QM_DECIMATION= {decimation}\n'
    out = out + f'##$QM_FILTER_ATTENUATION= 1/2**{p}\n'
    out = out + f'##$QM_GAIN= {decimation}**2/2**{p} = {gain}\n'
    out = out + f'##$QM_TEMPERATURE_SET_POINT= {mpars["set point T"]}  $$ C\n'
    out = out + f'##$QM_ADC_SAMPLING_CLOCK= {ic.seqclk_MHz}  $$ MHz\n'
    out = out + f'##$QM_HARDWARE_FILTER= {ic.hardware_filter}\n'
    out = out + f'##$QM_SOFTWARE_FILTER= {ppars["software filter"]}\n'

    out = out + jcamp_FID_string(data_array, time_step)
    return out

# for nscan_pulse_acq run
# takes an integer array data_array = (npoints,2)
# make a complete jcamp file string for one fid and write it to a file
def jcamp_npa_write(data_array, fpars, spars, ppars, gpars, mpars, vpars, file_suffix):
    
    filestring = jcamp_nscan_pulse_acq_string(
                       data_array, fpars, spars, ppars, gpars, mpars, vpars, file_suffix)
    
    filename = fpars['data directory'] +'/' + fpars['data filename'] + file_suffix + '.jdx'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename,'wb') as jfile:  
        code=jfile.write(bytes(filestring,'utf-8'))
    
    return code


# ######
# ## test code, write one file
# rsets = settings.nscan_pulse_acquire_settings
# gsets = settings.global_settings
# file_suffix = '002'

# # generate data for test
# bits = 16
# int_max = 2**(bits-1)  # randrange wont include the upper bound
# int_min = -2**(bits-1)

# time_step = 1/(1000*rsets['spec_width_kHz'])
# points = int(1 + rsets['acquire_s']/time_step)
# fid_freq = 10.0   # Hz offset

# last_time = (points-1)*time_step
# time_series = np.linspace(0,last_time,points)
# data_real = (2**15-1)*np.cos(2*np.pi*fid_freq*time_series)
# data_real = data_real.astype('int16')
# data_imag = (2**15-1)*np.sin(2*np.pi*fid_freq*time_series)
# data_imag = data_imag.astype('int16')
# data_array = np.array([data_real, data_imag])

# # plot the data
# fig,ax = plt.subplots()    
# ax.plot(time_series,data_real,time_series,data_imag)
# ax.set_title('Original time series')

# # create jcamp-dx file string and write to file
# code = jcamp_npa_write(data_array, rsets, gsets, file_suffix)

# # read it back in and plot it again
# filename = rsets["base_filename"] + file_suffix + '.jdx'
# readResult = jcampdx.read(filename)

# dreal = readResult[1][0]
# dimag = readResult[1][1]

# fig,ax = plt.subplots()    
# ax.plot(time_series,dreal,time_series,dimag)
# ax.set_title('Read back time series from test.jdx')
