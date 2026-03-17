# -*- coding: utf-8 -*-
"""
temperature controller code
"""
import time
import statistics
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

# the 'get' commands retry if the response is invalid
# the 'set' commands only try once, but they return a flag
response_delay = 0.060     # delay before reading command response (sec)
max_trys = 5               # try for valid reponse this many times 

# To use these functions in IPython when testing and debugging:
#
# launch powershell
# cd "C:\Users\John Price\Q Mag Code\qmcontrol" or equivalent
# ipython
# import qmcontrol.host_interface as hi
# import qmcontrol.temp_ctrl as tc
# si = hi.SpectrometerInterface()
# tc.flush(si)
# tc.get_TA1(si)
# tc.logger(si)   etc...


# two-point thermistor calibration of one channel
# uses starting calibration parameters, indicated and actual temperatures at 2 points
# returns refined calibration parameters
# optionally sets new cal parameters and saves them to flash
def two_point(si, Tr_C, Br_K, Rr, T1i_C, T1a_C, T2i_C, T2a_C, set_and_save, set_to):

    # # example
    # Tr_C = 25.0     # starting cal constant
    # Br_K = 3964     # starting cal constant
    # Rr = 10000      # needed to set and save cal parameters, not refined
    
    # T1i_C = 27.484  # indicated temperature, first point
    # T1a_C = 28.1    # actual temperature, first point
    # T2i_C = 39.941  # indicated temperature, second point
    # T2a_C = 40.3    # actual temperature, second point
    
    # set_and_save = True # set and save cal to flash
    # set_to = 'magnet'   # select channel: 'magnet', 'TA1', 'TA2'

    # starting cal constants
    Tr_K = Tr_C + 273.15  

    # indicated and actual temperatures at 2 points
    T1i = T1i_C + 273.15    # indicated
    T1a = T1a_C + 273.15    # actual
    T2i = T2i_C + 273.15
    T2a = T2a_C + 273.15
    
    a = 1.0/Tr_K
    b = 1.0/Br_K
    
    p = (T1i*T2a - T1a*T2i)/((T1a*T2a)*(T1i - T2i))
    q = (1/T1a - 1/T2a)/(1/T1i - 1/T2i)
    
    Tr_refined = 1/(p + a*q)
    Br_refined = 1/(b*q)
    
    print(f'Tr_refined (C) = {Tr_refined - 273.15}')
    print(f'Br_refined (K)= {Br_refined}')
    print(f'Rr = {Rr}')
    
    if set_and_save:
        if set_to == 'magnet':
            set_CMG(si,Tr_refined, Rr, Br_refined)
        elif set_to == 'TA1':
            set_CA1(si,Tr_refined, Rr, Br_refined)
        elif set_to == 'TA2':
            set_CA2(si,Tr_refined, Rr, Br_refined)
        else:
            print('invalid channel name')
        print('set cal parameters to channel ' + set_to)
        SAV(si)
        print('save cal parameters to flash')


def initialize_cal(si):

    # # starting values
    # mag_Rr = 10000
    # TA1_Rr = 15000
    # TA2_Rr = 10000
                
    # mag_Tr = 273.15 + 25.0
    # mag_B = 3964
    # TA1_Tr = 273.15 + 25.0
    # TA1_B = 3964
    # TA2_Tr = 273.15 + 25.0
    # TA2_B = 3964
    
    # refined values
    mag_Rr = 10000
    TA1_Rr = 15000
    TA2_Rr = 10000
    
    mag_Tr = 273.15 + 25.665
    mag_B = 4060.448
    TA1_Tr = 273.15 + 23.488
    TA1_B = 3974.42
    TA2_Tr = 273.15 + 23.1680
    TA2_B = 3986.97

    set_CMG(si,Tr_refined, Rr, Br_refined)
    set_CA1(si,Tr_refined, Rr, Br_refined)
    set_CA2(si,Tr_refined, Rr, Br_refined)
    SAV(si)

# check error rate, one try
def error_test(si, delay, samples):
    for i in range(int(samples)):
        mt, rec = get_TMG_simple(si)
        print(i, mt, rec)  # beep
        time.sleep(delay)
        
# error rate with robust version of get_TMG
# works with delay = 0, in 1000 samples max value of trys returned is 3.
def error_test_robust(si, delay, samples):
    for i in range(int(samples)):
        mt, trys, received = get_TMG(si)
        if trys > 1:
             print(i, trys, mt, received, '\a')  # beep   
        else:
             print(i, trys, mt, received)
        time.sleep(delay)
        
# error rate with robust version of get_MAP
# works with delay = 0, in 1000 samples max value of trys returned is 3.
def error_test_robust2(si, delay, samples):
    for i in range(int(samples)):
        mt, at, trys, received = get_MAP(si)
        if trys > 1:
             print(i, trys, mt, at, received, '\a')  # beep   
        else:
             print(i, trys, mt, at, received)
        time.sleep(delay)

def flush(si):
    rec = si.ReceiveTempCo()
    print(rec)

# read temperature of magnet channel
def get_TMG_simple(si):
    magnet_temperature = None
    si.SendTempCo(b':TMG?\n')
    time.sleep(response_delay)           # wait for response buffer to fill 0.060
    rec = si.ReceiveTempCo()
    if rec[0:1] == b'!':
        magnet_temperature = float(rec[6:-1])
    return magnet_temperature, rec

# read version string
# first item returned is a 2-digit integer
def get_VER(si):
    version = None
    for i in range(max_trys):
        si.SendTempCo(b':VER?\n')
        time.sleep(response_delay)
        rec = si.ReceiveTempCo()
        if rec[0:1] != b'!':
            bad_rec =  rec
        else:
            version = int(rec[6:-1])
            if i == 0:
                return version, i+1, rec
            else:
                return version, i+1, bad_rec
    return version, i+1, bad_rec


# read magnet temperature up to max_trys times until no error
# return temperature, number of trys needed, raw message received
# if 1 try was needed return received message
# if more than one try was needed, return last bad message
# if reach max_trys, return temperature = None
def get_TMG(si):
    temperature = None
    for i in range(max_trys):
        si.SendTempCo(b':TMG?\n')
        time.sleep(response_delay)
        rec = si.ReceiveTempCo()
        if rec[0:1] != b'!':
            bad_rec =  rec
        else:
            temperature = float(rec[6:-1])
            if i == 0:
                return temperature, i+1, rec
            else:
                return temperature, i+1, bad_rec
    return temperature, i+1, bad_rec
    
# read ambient1 temperature up to max_trys times until no error
def get_TA1(si):
    temperature = None
    for i in range(max_trys):
        si.SendTempCo(b':TA1?\n')
        time.sleep(response_delay) 
        rec = si.ReceiveTempCo()
        if rec[0:1] != b'!':
            bad_rec =  rec
        else:
            temperature = float(rec[6:-1])
            if i == 0:
                return temperature, i+1, rec
            else:
                return temperature, i+1, bad_rec
    return temperature, i+1, bad_rec
    
# read ambient2 temperature up to max_trys times until no error
def get_TA2(si):
    temperature = None
    for i in range(max_trys):
        si.SendTempCo(b':TA2?\n')
        time.sleep(response_delay)
        rec = si.ReceiveTempCo()
        if rec[0:1] != b'!':
            bad_rec =  rec
        else:
            temperature = float(rec[6:-1])
            if i == 0:
                return temperature, i+1, rec
            else:
                return temperature, i+1, bad_rec
    return temperature, i+1, bad_rec
    
# read heater power up to max_trys times until no error
def get_PWR(si):
    power = None
    for i in range(max_trys):
        si.SendTempCo(b':PWR?\n')
        time.sleep(response_delay)
        rec = si.ReceiveTempCo()
        if rec[0:1] != b'!':
            bad_rec =  rec
        else:
            power = float(rec[6:-1])
            if i == 0:
                return power, i+1, rec
            else:
                return power, i+1, bad_rec
    return power, i+1, bad_rec
    
# read proportional term of heater power up to max_trys times until no error
def get_PWP(si):
    power = None
    for i in range(max_trys):
        si.SendTempCo(b':PWP?\n')
        time.sleep(response_delay)
        rec = si.ReceiveTempCo()
        if rec[0:1] != b'!':
            bad_rec =  rec
        else:
            power = float(rec[6:-1])
            if i == 0:
                return power, i+1, rec
            else:
                return power, i+1, bad_rec
    return power, i+1, bad_rec
    
# read integral term of heater power up to max_trys times until no error
def get_PWI(si):
    power = None
    for i in range(max_trys):
        si.SendTempCo(b':PWI?\n')
        time.sleep(response_delay)
        rec = si.ReceiveTempCo()
        if rec[0:1] != b'!':
            bad_rec =  rec
        else:
            power = float(rec[6:-1])
            if i == 0:
                return power, i+1, rec
            else:
                return power, i+1, bad_rec
    return power, i+1, bad_rec
    
# read derivative terms of heater power up to max_trys times until no error
def get_PWD(si):
    power = None
    for i in range(max_trys):
        si.SendTempCo(b':PWD?\n')
        time.sleep(response_delay)
        rec = si.ReceiveTempCo()
        if rec[0:1] != b'!':
            bad_rec =  rec
        else:
            power = float(rec[6:-1])
            if i == 0:
                return power, i+1, rec
            else:
                return power, i+1, bad_rec
    return power, i+1, bad_rec

# set temperature control set point in deg C
def set_TMS(si,set_point):
    set_point_bytes = bytes(str(set_point),'utf-8')
    si.SendTempCo(b':TMS ' + set_point_bytes + b'\n')
    time.sleep(response_delay)
    rec = si.ReceiveTempCo()
    if rec[0:1] != b'!':
        return None, rec
    else:
        return 1, rec
        
# read temperature control set point in deg C
def get_TMS(si):
    set_point = None
    for i in range(max_trys):
        si.SendTempCo(b':TMS?\n')
        time.sleep(response_delay)
        rec = si.ReceiveTempCo()
        if rec[0:1] != b'!':
            bad_rec =  rec
        else:
            set_point = float(rec[6:-1])
            if i == 0:
                return set_point, i+1, rec
            else:
                return set_point, i+1, bad_rec
    return set_point, i+1, bad_rec

# set PID parameters
# might not work, not sure how be FPGA character bu
def set_PID(si, P, I, D):
    P_bytes = bytes(str(P),'utf-8')
    I_bytes = bytes(str(I),'utf-8')
    D_bytes = bytes(str(D),'utf-8')
    si.SendTempCo(b':PID ' + P_bytes + b',' + I_bytes + b',' + D_bytes + b'\n')
    time.sleep(response_delay)
    rec = si.ReceiveTempCo()
    if rec[0:1] != b'!':
        return None, rec
    else:
        return 1, rec
        
# read PID parameters
def get_PID(si):
    P = None; I = None; D = None
    for i in range(max_trys):
        si.SendTempCo(b':PID?\n')
        time.sleep(response_delay)
        time.sleep(response_delay)
        rec = si.ReceiveTempCo()
        if rec[0:1] != b'!':
            bad_rec =  rec
        else:
            result_list = rec[6:-1].split(b',')
            P = float(result_list[0]);
            I = float(result_list[1]);
            D = float(result_list[2]);
            if i == 0:
                return P, I, D, i+1, rec
            else:
                return P, I, D, i+1, bad_rec
    return P, I, D, i+1, bad_rec

# set heater enable (0=off, 1=on)
def set_HEN(si,value):
    enable_bytes = bytes(str(int(value)),'utf-8')
    si.SendTempCo(b':HEN ' + enable_bytes + b'\n')
    time.sleep(response_delay)
    rec = si.ReceiveTempCo()
    if rec[0:1] != b'!':
        return None, rec
    else:
        return 1, rec
        
# read heater enable
def get_HEN(si):
    heater_enable = None
    for i in range(max_trys):
        si.SendTempCo(b':HEN?\n')
        time.sleep(response_delay)
        rec = si.ReceiveTempCo()
        if rec[0:1] != b'!':
            bad_rec =  rec
        else:
            heater_enable = int(rec[6:-1])
            if i == 0:
                return heater_enable, i+1, rec
            else:
                return heater_enable, i+1, bad_rec
    return heater_enable, i+1, bad_rec

# read magnet channel calibration parameters
def get_CMG(si):
    Tr = None; Rr = None; B = None
    for i in range(max_trys):
        si.SendTempCo(b':CMG?\n')
        time.sleep(response_delay)
        rec = si.ReceiveTempCo()
        if rec[0:1] != b'!':
            bad_rec =  rec
        else:
            result_list = rec[6:-1].split(b',')
            Tr = float(result_list[0]);
            Rr = float(result_list[1]);
            B = float(result_list[2]);
            if i == 0:
                return Tr, Rr, B, i+1, rec
            else:
                return Tr, Rr, B, i+1, bad_rec
    return Tr, Rr, B, i+1, bad_rec
    
# read ambient1 channel calibration parameters
def get_CA1(si):
    Tr = None; Rr = None; B = None
    for i in range(max_trys):
        si.SendTempCo(b':CA1?\n')
        time.sleep(response_delay)
        rec = si.ReceiveTempCo()
        if rec[0:1] != b'!':
            bad_rec =  rec
        else:
            result_list = rec[6:-1].split(b',')
            Tr = float(result_list[0]);
            Rr = float(result_list[1]);
            B = float(result_list[2]);
            if i == 0:
                return Tr, Rr, B, i+1, rec
            else:
                return Tr, Rr, B, i+1, bad_rec
    return Tr, Rr, B, i+1, bad_rec
    
# read ambient2 channel calibration parameters
def get_CA2(si):
    Tr = None; Rr = None; B = None
    for i in range(max_trys):
        si.SendTempCo(b':CA2?\n')
        time.sleep(response_delay)
        rec = si.ReceiveTempCo()
        if rec[0:1] != b'!':
            bad_rec =  rec
        else:
            result_list = rec[6:-1].split(b',')
            Tr = float(result_list[0]);
            Rr = float(result_list[1]);
            B = float(result_list[2]);
            if i == 0:
                return Tr, Rr, B, i+1, rec
            else:
                return Tr, Rr, B, i+1, bad_rec
    return Tr, Rr, B, i+1, bad_rec

# set magnet channel calibration
def set_CMG(si,Tr,Rr,B):
    Tr_bytes = bytes(str(Tr),'utf-8')
    Rr_bytes = bytes(str(Rr),'utf-8')
    B_bytes = bytes(str(B),'utf-8')
    si.SendTempCo(b':CMG ' + Tr_bytes + b',' + Rr_bytes + b',' + B_bytes + b'\n')
    time.sleep(response_delay)
    rec = si.ReceiveTempCo()
    if rec[0:1] != b'!':
        return None, rec
    else:
        return 1, rec
        
# set ambient1 channel calibration
def set_CA1(si,Tr,Rr,B):
    Tr_bytes = bytes(str(Tr),'utf-8')
    Rr_bytes = bytes(str(Rr),'utf-8')
    B_bytes = bytes(str(B),'utf-8')
    si.SendTempCo(b':CA1 ' + Tr_bytes + b',' + Rr_bytes + b',' + B_bytes + b'\n')
    time.sleep(response_delay)
    rec = si.ReceiveTempCo()
    if rec[0:1] != b'!':
        return None, rec
    else:
        return 1, rec
        
# set ambient2 channel calibration
def set_CA2(si,Tr,Rr,B):
    Tr_bytes = bytes(str(Tr),'utf-8')
    Rr_bytes = bytes(str(Rr),'utf-8')
    B_bytes = bytes(str(B),'utf-8')
    si.SendTempCo(b':CA2 ' + Tr_bytes + b',' + Rr_bytes + b',' + B_bytes + b'\n')
    time.sleep(response_delay)
    rec = si.ReceiveTempCo()
    if rec[0:1] != b'!':
        return None, rec
    else:
        return 1, rec

# save cal parameters, PID parameters, and set point to flash
def SAV(si):
    si.SendTempCo(b':SAV\n')
    time.sleep(response_delay)
    rec = si.ReceiveTempCo()
    if rec[0:1] != b'!':
        return None, rec
    else:
        return 1, rec
        
# restore cal parameters, PID parameters, and set point from flash
def RES(si):
    si.SendTempCo(b':RES\n')
    time.sleep(response_delay)
    rec = si.ReceiveTempCo()
    if rec[0:1] != b'!':
        return None, rec
    else:
        return 1, rec

# get magnet temperature and ambient temperature with a single RS485 command
# the temperatures are aliased to physical channels by the MAP command
def get_MAP(si):
    mag_temperature = None
    ambient_temperature =  None
    # power = None
    for i in range(max_trys):
        si.SendTempCo(b':MAP?\n')
        time.sleep(response_delay)
        rec = si.ReceiveTempCo()
        if rec[0:1] != b'!':
            bad_rec =  rec
        else:
            result_list = rec[6:-1].split(b',')
            mag_temperature = float(result_list[0])
            ambient_temperature = float(result_list[1])
            # power = float(result_list[2])  
            if i == 0:
                # return mag_temperature, ambient_temperature, power, i+1, rec
                return mag_temperature, ambient_temperature, i+1, rec
            else:
                # return mag_temperature, ambient_temperature, power, i+1, bad_rec
                return mag_temperature, ambient_temperature, i+1, bad_rec
    # return mag_temperature, ambient_temperature, power, i+1, bad_rec
    return mag_temperature, ambient_temperature, i+1, bad_rec


# plot temperature of each channel and heater power
# optionally set the set point and PID parameters at the beginning
# optionally make a step in the set point after sample_delay samples
def logger(si, set_params=False):
    
    set_point = 29.9
    Pvalue = 8E9
    Ivalue = 6E8
    Dvalue = 2E10
    sample_delay = 12.0   # get a point every sample_delay seconds
    stats_samples = 25    # show stats for last stats_samples samples
    
    setpoint_step = False
    step_sample = 50
    set_point_increment = 0.2    
    
    if set_params:
        set_TMS(si, set_point)
        set_PID(si, Pvalue,Ivalue,Dvalue)
        SAV(si)
        
    magnet=[]; ambient=[]; power=[]; times=[]
    
    fig, ax = plt.subplots(3,1)
    plt.subplots_adjust(left=0.20)
    
    plt.pause(0.10)

    j=0
    while True:
        
        mag_temperature, ambient_temperature,_,_ = get_MAP(si)  # get aliased temperature
        heater_power,_,_ = get_PWR(si)
        time = j*sample_delay/60.0
        
        print(time, mag_temperature, ambient_temperature, heater_power)
        
        magnet.append(mag_temperature)
        ambient.append(ambient_temperature)
        power.append(heater_power)
        times.append(time)
        
        if j>0:
            ax[0].clear()
            ax[1].clear()
            ax[2].clear()

        line0, = ax[0].plot(times, magnet, 'b-')
        line1, = ax[1].plot(times, ambient, 'b-')
        line2, = ax[2].plot(times, power, 'b-')
        
        ax[0].set_ylabel('magnet (C)')
        #ax[0].set_xticklabels([])
        ax[0].yaxis.set_major_formatter(FormatStrFormatter('% 2.6f'))
        ax[0].set_title('Magnet Temperature Controller')
        
        ax[1].set_ylabel('ambient (C)')
        #ax[1].set_xticklabels([])
        ax[1].yaxis.set_major_formatter(FormatStrFormatter('% 2.6f'))
        
        ax[2].set_xlabel('time (minutes)')
        ax[2].set_ylabel('heater power (W)')
        ax[2].yaxis.set_major_formatter(FormatStrFormatter('% 2.6f'))
        
        if len(magnet) > stats_samples:
            aveT = statistics.mean(magnet[-(stats_samples+1):-1])
            sigmaT = statistics.stdev(magnet[-(stats_samples+1):-1])
            msg = f'mean = {aveT:2.6f} C, std. dev. = {sigmaT*1000:0.3f} mC (5 min)'
            ax[0].text(0.03, 0.80, msg, transform=ax[0].transAxes, fontsize = 12)
        
        # if len(ambient) > stats_samples:
            # aveT = statistics.mean(ambient[-(stats_samples+1):-1])
            # sigmaT = statistics.stdev(ambient[-(stats_samples+1):-1])
            # msg = f'mean = {aveT:2.5f} C, std. dev. = {sigmaT*1000:0.3f} mC (5 min)'
            # ax[1].text(0.03, 0.80, msg, transform=ax[1].transAxes, fontsize = 12)
                   
        if setpoint_step and j == step_sample:
            set_TMS(si, set_point + set_point_increment)    
        
        plt.pause(sample_delay)
        
        j += 1

# plot aliased magnet temperature from MAP command
# plot heater power, and P, I, D parts of heater power
# optionally set the set point and PID parameters at the beginning
# optionally make a step in the set point after sample_delay samples
def tuner(si, set_params=False):
    
    set_point = 30.0
    Pvalue = 8.0E9
    Ivalue = 6.0E8
    Dvalue = 2.0E10
    sample_delay = 12.0   
    stats_samples = 25  
    
    setpoint_step = False
    step_sample = 25
    set_point_increment = 0.020    
    
    if set_params:
        set_TMS(si, set_point)
        set_PID(si, Pvalue, Ivalue, Dvalue)
        SAV(si)        
        
    magnet=[]; power=[]; power_p=[]; power_i=[]; power_d=[]; times=[]
    
    fig, ax = plt.subplots(5,1)
    plt.subplots_adjust(left=0.20)
    
    plt.pause(0.10)

    j=0
    while True:
        
        mag_temperature,_,_,_ = get_MAP(si)  # get aliased magnet temperature
        heater_power,_,_ = get_PWR(si)
        heater_power_p,_,_ = get_PWP(si)
        heater_power_i,_,_ = get_PWI(si)
        heater_power_d,_,_ = get_PWD(si)
        
        time = j*sample_delay/60.0
        
        print(time, mag_temperature, heater_power, heater_power_p, heater_power_i, heater_power_d)
        
        magnet.append(mag_temperature)
        power.append(heater_power)
        power_p.append(heater_power_p)
        power_i.append(heater_power_i)
        power_d.append(heater_power_d)
        times.append(time)
        
        if j>0:
            ax[0].clear()
            ax[1].clear()
            ax[2].clear()
            ax[3].clear()
            ax[4].clear()

        line0, = ax[0].plot(times, magnet, 'b-')
        line1, = ax[1].plot(times, power, 'b-')
        line2, = ax[2].plot(times, power_p, 'b-')
        line3, = ax[3].plot(times, power_i, 'b-')
        line4, = ax[4].plot(times, power_d, 'b-')
        
        ax[0].set_title('Magnet Temperature Controller')
        ax[0].set_ylabel('magnet (C)')
        ax[0].yaxis.set_major_formatter(FormatStrFormatter('% 2.6f'))
        
        ax[1].set_ylabel('heater power (W)')
        ax[1].yaxis.set_major_formatter(FormatStrFormatter('% 2.6f'))
        
        ax[2].set_ylabel('power P (W)')
        ax[2].yaxis.set_major_formatter(FormatStrFormatter('% 2.6f'))
        
        ax[3].set_ylabel('power I (W)')
        ax[3].yaxis.set_major_formatter(FormatStrFormatter('% 2.6f'))
        
        ax[4].set_xlabel('time (minutes)')
        ax[4].set_ylabel('power D (W)')
        ax[4].yaxis.set_major_formatter(FormatStrFormatter('% 2.6f'))
        
        if len(magnet) > stats_samples:
            aveT = statistics.mean(magnet[-(stats_samples+1):-1])
            sigmaT = statistics.stdev(magnet[-(stats_samples+1):-1])
            msg = f'mean = {aveT:2.6f} C, std. dev. = {sigmaT*1000:0.3f} mC (5 min)'
            ax[0].text(0.03, 0.80, msg, transform=ax[0].transAxes, fontsize = 12)
        
        if setpoint_step and j == step_sample:
            set_TMS(si, set_point + set_point_increment) 
        
        plt.pause(sample_delay)
        
        j += 1
