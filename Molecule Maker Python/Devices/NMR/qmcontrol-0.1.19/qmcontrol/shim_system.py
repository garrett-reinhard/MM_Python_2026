# -*- coding: utf-8 -*-
"""
functions for setting and manipulating shims
"""
import numpy as np
import math
import time
import random

# the 'get' commands retry if the response is invalid
# the 'set' commands only try once, but they return a flag
response_delay = 0.02      # default delay before reading command response (sec)
max_trys = 5               # try for valid reponse this many times 

# To use these functions in IPython when testing and debugging:
#
# launch powershell
# cd "C:\Users\John Price\Q Mag Code\qmcontrol" or equivalent
# ipython
# import qmcontrol.host_interface as hi
# import qmcontrol.shim_system as ss
# si = hi.SpectrometerInterface()
# ss.flush(si)
# ss.get_VER(si) etc...

# test writing and reading back a shim vector of random integers
# *** this has not been updated since shim drive firmware sets limit on total current
# *** currently it will fail when test_vector exceeds limit (most of the time)
# *** shim drive board v37 imposes total current limit of 2.4 A
# *** to use as is, must set MAX_CURRENT in firmware to 18*0.68A
# *** then unplug shim ribbons so actual total current will be small
# use for communication test only with shim coils disconnected, or only one connected
# no failures in 100 iterations with delay = 0.050, max set time = 0.674s
# no failures in 100 iterations with delay = 0.040, max set time = 0.64s
# no failures in 100 iterations with delay = 0.030, max set time = 0.47s <-- best choice, also tested for 500 iter
# no failures in 100 iterations with delay = 0.020, max set time = 0.44s
# many failures with delay = 0.010s, some with 0.015s
def error_test_set_DACs(si, delay, samples):
    all_success = True
    max_set_time = 0
    for i in range(samples):
        test_vec = [random.randint(-65535,65535) for i in range(18)]
        tic = time.perf_counter()
        set_success, set_trys_vec = set_DACs(si, test_vec, delay)
        toc = time.perf_counter()
        get_success, get_trys_vec, get_vec = get_DACs(si, delay)
        print(i+1)
        print(test_vec)
        print(set_trys_vec)
        print(get_trys_vec)
        success = (test_vec == get_vec) and set_success and get_success
        if not success: 
             print('\a')  # beep
             all_success = False
        set_time = toc-tic
        if set_time > max_set_time: max_set_time = set_time
        print(f'{set_time:0.5f}s {success}','\n')
    set_ZER(si)
    print('all iterations successful? ', all_success)
    print(f'max set time = {max_set_time:0.5f}s')
        
def error_test_set_MD2(si, values, delay, samples):
    for i in range(samples):
        success, trys, response = set_MD2(si,values,delay)
        if trys > 1: print('\a')  # beep   
        print(i, success, trys, response)

# error rate with robust version of set_DAC
def error_test_set_DAC(si, channel, value, delay, samples):
    for i in range(samples):
        success, trys, response = set_DAC(si,channel, value, delay)
        if trys > 1: print('\a')   # beep   
        print(i, success, trys, response)
        
def error_test_get_DAC(si, channel, delay, samples):
    for i in range(samples):
        success, trys, response, value = get_DAC(si,channel, delay)
        if trys > 1:
             print(i, success, trys, response, value, '\a')  # beep   
        else:
             print(i, success, trys, response, value)
        
def error_test_set_ZER(si, samples):
    for i in range(samples):
        success, trys, response = set_ZER(si)
        if trys > 1:
             print(i, success, trys, response, '\a')  # beep   
        else:
             print(i, success, trys, response)

def flush(si):
    rec = si.ReceiveShimA()
    print(rec)

# read shim drive board firmware version string
# 4th item returned is a 2-digit integer
def get_VER(si):
    version = None
    for i in range(max_trys):
        si.SendShimA(b':VER?\n')
        time.sleep(response_delay)
        res = si.ReceiveShimA()
        if res[0:1] != b'!':   # nack response
            bad_res =  res     
        else:                  # ack response
            try:
                version = int(res[6:-1])
            except:
                bad_res = res
            else:
                if i == 0:
                    return True, 1, res, version
                else:
                    return True, i+1, bad_res, version
    return False, i+1, bad_res, version   # max_trys reached
    
# read status, efuse current and shim coil continuity bits
# normal respose for coils0 and coils1 is '0x20000' since
# the last (18th) channel is not connected to a coil
# coils0 is pos polarity test, coils1 is negative polarity test
def get_STA(si):
    current = None
    coils0 = None
    coils1 = None
    for i in range(max_trys):
        si.SendShimA(b':STA?\n')
        time.sleep(response_delay)
        res = si.ReceiveShimA()
        if res[0:1] != b'!':   # nack response
            bad_res =  res     
        else:                  # ack response
            try:
                res_list = res[6:-1].split(b',')  
                current = float(res_list[0])
                coils0 = res_list[1].decode()
                coils1 = res_list[2].decode()
            except:
                bad_res = res
            else:
                if i == 0:
                    return True, 1, res, current, coils0, coils1
                else:
                    return True, i+1, bad_res, current, coils0, coils1
    return False, i+1, bad_res, current, coils0, coils1   # max_trys reached

# set all channels to zero
def set_ZER(si):
    for i in range(max_trys):
        si.SendShimA(b':ZER\n')
        time.sleep(response_delay)
        res = si.ReceiveShimA()
        if res[0:1] != b'!':      # nack response
            bad_res = res_list
        else:                     # ack response
            if i == 0:
                return True, 1, res
            else:
                return True, i+1, bad_res
    return False, i+1, bad_res    # max_trys reached

# save current DAC settings and signs to flash
def SAV(si):
    for i in range(max_trys):
        si.SendShimA(b':SAV\n')
        time.sleep(response_delay)
        res = si.ReceiveShimA()
        if res[0:1] != b'!':      # nack response
            bad_res = res_list
        else:                     # ack response
            if i == 0:
                return True, 1, res
            else:
                return True, i+1, bad_res
    return False, i+1, bad_res    # max_trys reached
        
# restore current DAC settings and signs from flash
def RES(si):
    for i in range(max_trys):
        si.SendShimA(b':RES\n')
        time.sleep(response_delay)
        res = si.ReceiveShimA()
        if res[0:1] != b'!':
            bad_res = res_list
        else:
            if i == 0:
                return True, 1, res
            else:
                return True, i+1, bad_res
    return False, i+1, bad_res

# set DAC value, one channel
# channel: integer 0 to 17
# value: integer 0 to +/- 2^16-1 = +/- 65535
# delay: delay in s before reading response
# return: success, trys, rec
#    success: True or False
#    trys: number of attempts to get valid response
#    res: response, most recent nack response if any
def set_DAC(si, channel, value, delay):
    channel_bytes = bytes(str(channel),'utf-8')
    value_bytes = bytes(str(value),'utf-8')
    for i in range(max_trys):
        si.SendShimA(b':DAC ' + channel_bytes + b',' + value_bytes + b'\n')
        time.sleep(delay)
        res = si.ReceiveShimA()
        if res[0:1] != b'!':
            bad_res = res       # nack response received
        else:                   # ack response received
            if i == 0:
                return True, 1, res        # on first attempt
            else:
                return True, i+1, bad_res  # on a later attempt
    return False, i+1, bad_res             # max_trys reached, command failed

# get DAC value for one channel
# channel: integer 0 to 17
# delay: delay in s before reading response
# return: success, trys, rec, value
#    success: True or False
#    trys: number of attempts to get valid response
#    res: valid response or most recent invalid response if any
#    value: DAC value
def get_DAC(si, channel, delay):
    value = None
    channel_bytes = bytes(str(channel),'utf-8')
    for i in range(max_trys):
        si.SendShimA(b':DAC ' + channel_bytes + b'?\n')
        time.sleep(delay)
        res = si.ReceiveShimA()
        if res[0:1] != b'!':  # nack response received
            bad_res =  res
        else:                 # ack response received
            try:              # try to read value
               res_list = res[6:-1].split(b',')  
               value = int(res_list[1])
            except:           # response was bad
               bad_res = res                     
            else:
                if i == 0:        # on first attempt
                    return True, 1, res, value
                else:             # on a later attempt
                    return True, i+1, bad_res, value
    return False, i+1, bad_res, value  # max_trys reached, command failed

# get all DAC values
# return success, values, trys
def get_DACs(si,delay):
    all_success = True
    values = []
    all_trys = []
    for channel in range(18):
        success, trys, response, value = get_DAC(si, channel, delay)
        if not success: all_success = False
        values.append(value)
        all_trys.append(trys)
    return all_success, all_trys, values

# set all DAC values
# protected for total current limit by shim drive board firmware
# return success, values, trys
def set_DACs(si, values, delay):
    all_success = True
    all_trys = []
    success, trys, response = set_MD0(si,values[0:3], delay)
    if not success: all_success = False
    all_trys.append(trys)
    success, trys, response = set_MD1(si,values[3:6], delay)
    if not success: all_success = False
    all_trys.append(trys)
    success, trys, response = set_MD2(si,values[6:9], delay)
    if not success: all_success = False
    all_trys.append(trys)
    success, trys, response = set_MD3(si,values[9:12], delay)
    if not success: all_success = False
    all_trys.append(trys)
    success, trys, response = set_MD4(si,values[12:15], delay)
    if not success: all_success = False
    all_trys.append(trys)
    success, trys, response = set_MD5(si,values[15:18], delay)
    if not success: all_success = False
    all_trys.append(trys)
    return all_success, all_trys

# set DAC channels 0,1,2
# values: list of integer values to set [123,234,-23244]
#         range of integers 0 to +/- 2^16-1 = +/- 65535
# delay: delay in seconds before reading response
# if successful, return True, trys, good response or last bad response
# if not successful, return False, trys, last bad response
def set_MD0(si,values,delay):
        value0_bytes = bytes(str(values[0]),'utf-8')
        value1_bytes = bytes(str(values[1]),'utf-8')
        value2_bytes = bytes(str(values[2]),'utf-8')
        for i in range(max_trys):
            bytes_to_send = b':MD0 ' + value0_bytes + b',' + value1_bytes + b',' + value2_bytes + b'\n'
            si.SendShimA(bytes_to_send)
            time.sleep(delay)
            res = si.ReceiveShimA()
            if res[0:1] != b'!':  # nack response received
                bad_res =  res    
            else:                 # ack response received
                if i == 0:
                    return True, 1, res       # on first attempt
                else:
                    return True, i+1, bad_res # on a later attempt
        return False, i+1, bad_res  # max_trys reached, command failed

# set DAC channels 3,4,5
def set_MD1(si,values,delay):
        value0_bytes = bytes(str(values[0]),'utf-8')
        value1_bytes = bytes(str(values[1]),'utf-8')
        value2_bytes = bytes(str(values[2]),'utf-8')
        for i in range(max_trys):
            bytes_to_send = b':MD1 ' + value0_bytes + b',' + value1_bytes + b',' + value2_bytes + b'\n'
            si.SendShimA(bytes_to_send)
            time.sleep(delay)
            res = si.ReceiveShimA()
            if res[0:1] != b'!':  # nack response received
                bad_res =  res    
            else:                 # ack response received
                if i == 0:
                    return True, 1, res       # on first attempt
                else:
                    return True, i+1, bad_res # on a later attempt
        return False, i+1, bad_res  # max_trys reached, command failed
        
# set DAC channels 6,7,8
def set_MD2(si,values,delay):
        value0_bytes = bytes(str(values[0]),'utf-8')
        value1_bytes = bytes(str(values[1]),'utf-8')
        value2_bytes = bytes(str(values[2]),'utf-8')
        for i in range(max_trys):
            bytes_to_send = b':MD2 ' + value0_bytes + b',' + value1_bytes + b',' + value2_bytes + b'\n'
            #print(bytes_to_send)
            si.SendShimA(bytes_to_send)
            time.sleep(delay)
            res = si.ReceiveShimA()
            if res[0:1] != b'!':  # nack response received
                bad_res =  res
            else:                 # ack response received
                if i == 0:
                    return True, i+1, res     # on first attempt
                else:
                    return True, i+1, bad_res # on a later attempt
        return False, i+1, bad_res  # max_trys reached, command failed
        
# set DAC channels 9,10,11
def set_MD3(si,values,delay):
        value0_bytes = bytes(str(values[0]),'utf-8')
        value1_bytes = bytes(str(values[1]),'utf-8')
        value2_bytes = bytes(str(values[2]),'utf-8')
        for i in range(max_trys):
            bytes_to_send = b':MD3 ' + value0_bytes + b',' + value1_bytes + b',' + value2_bytes + b'\n'
            #print(bytes_to_send)
            si.SendShimA(bytes_to_send)
            time.sleep(delay)
            res = si.ReceiveShimA()
            if res[0:1] != b'!':  # nack response received
                bad_res =  res
            else:                 # ack response received
                if i == 0:
                    return True, i+1, res     # on first attempt
                else:
                    return True, i+1, bad_res # on a later attempt
        return False, i+1, bad_res  # max_trys reached, command failed
        
# set DAC channels 12,13,14
def set_MD4(si,values,delay):
        value0_bytes = bytes(str(values[0]),'utf-8')
        value1_bytes = bytes(str(values[1]),'utf-8')
        value2_bytes = bytes(str(values[2]),'utf-8')
        for i in range(max_trys):
            bytes_to_send = b':MD4 ' + value0_bytes + b',' + value1_bytes + b',' + value2_bytes + b'\n'
            #print(bytes_to_send)
            si.SendShimA(bytes_to_send)
            time.sleep(delay)
            res = si.ReceiveShimA()
            if res[0:1] != b'!':  # nack response received
                bad_res =  res
            else:                 # ack response received
                if i == 0:
                    return True, i+1, res     # on first attempt
                else:
                    return True, i+1, bad_res # on a later attempt
        return False, i+1, bad_res  # max_trys reached, command failed
        
# set DAC channels 15,16,17
def set_MD5(si,values,delay):
        value0_bytes = bytes(str(values[0]),'utf-8')
        value1_bytes = bytes(str(values[1]),'utf-8')
        value2_bytes = bytes(str(values[2]),'utf-8')
        for i in range(max_trys):
            bytes_to_send = b':MD5 ' + value0_bytes + b',' + value1_bytes + b',' + value2_bytes + b'\n'
            #print(bytes_to_send)
            si.SendShimA(bytes_to_send)
            time.sleep(delay)
            res = si.ReceiveShimA()
            if res[0:1] != b'!':  # nack response received
                bad_res =  res
            else:                 # ack response received
                if i == 0:
                    return True, i+1, res     # on first attempt
                else:
                    return True, i+1, bad_res # on a later attempt
        return False, i+1, bad_res  # max_trys reached, command failed


def shim_str2vec(shim_str):
    """
    convert string shim vector in format used in UI to list of floats
    example input string:  
    "[0;0.0003,0.001,0.001;0.002,0.002,0.002,0.002,0.002;0,0,0,0,0,0,0;0]"
    example output list:
    [0,0.0003,0.001,0.001,0.002,0.002,0.002,0.002,0.002,0,0,0,0,0,0,0,0]
    """
    
    stripped = shim_str.strip(']').strip('[').split(';')
    shim_vec = []
    for item in stripped:
        split = item.split(',')
        for str_num in split:
            shim_vec.append(float(str_num))
    return shim_vec
    

def update_shims_record(shims_record, active_shims_vec, incs):
    """
    update a shims record with changed active shims
    
    update shims record with entrys in active vector for which the
    corresponding entry in incs is not zero
    
    Parameters
    ----------
    shims_record : shims record
    active_shims_vec : active vector, list of floats
    incs : list of floats

    Returns
    -------
    new_shims_record : updated shims record
    """
    
    shim_vec = [0]*17
    j=0
    for i in range(len(incs)):
        if incs[i] == 0 :
            shim_vec[i] = shims_record[1][i]
        else:
            shim_vec[i] = active_shims_vec[j]
            j = j+1
    new_shims_record = \
        [shims_record[0], shim_vec, shims_record[2]]
    return new_shims_record
    

def make_simplex(shims_record, incs):
    """
    make a simplex and a vector of active shims from a shims record and incs
    
    Parameters
    ----------
    shims_record : shims record
    incs : list of floats

    Returns
    -------
    active_vec : list of floats
        active vector spanning subspace for which incs[i] are not zero.
    init_simplex : list of list of floats
        initial simplex starting at active_vec
    """
    
    shims_vec = shims_record[1]
    active_vec = [val for i, val in enumerate(shims_vec) if incs[i]!=0]
    active_incs = [val for i, val in enumerate(incs) if incs[i]!=0]
    init_simplex = [active_vec]
    for ii in range(len(active_vec)):
        row = active_vec.copy()
        row[ii] = row[ii] +active_incs[ii]
        init_simplex.append(row)
    return active_vec, init_simplex


def set_shims(si, shims, setDACs=True, test=False):
    """
    set output currents on 18-channel shim drive board, 17 channels being used
    shims are nested lists of floats outside of this function but are converted
    to np.array() here
    
    shims vector in multipole order:
    0  1  2  3  4  5  6  7    8  9  10  11  12    13  14 15 16 
    1  Z  X  Y  Z2 XZ YZ X2Y2 XY Z3 XZ2 YZ2 X2Y2Z XYZ X3 Y3 Z4
    
    arguments:
    si: instance of SpectrometerInterface host interface
    if test = False (default is False)
        shims: a nested list of floats
        shims[0]: magnet temperature for these shims
        shims[1]: a row vector with 17 elements, amps in nominal coil
        shims[2]: shim matrix converting shim[1] to DAC settings
    if test = True
        shims: a row vector with 17 elements, amps in nominal coil
        if shim matrix has unit entries
    If setDACs = True set DACs (default is True), else don't set DACs
    
    the shim matrix generates currents in coils other than the nominal coils
    to create approximately pure multipoles
    
    returns:
    set_DACs_success: True if DACs were set
        False if total current limit would be exceeded by setting DACs
        False if comms error or shim board firmware prevents DACs from being set
        False if setDACs input flag was set
    Iamps:  row vector of currents generated by each driver channel (A)
    satflags:  row vector showing which channels are saturated (+1/0/-1)
        DACs for these are set to +/- binmax unless total current limit would be exceeded
    Itotal: sum of magnitude of all currents in amps
    power: total power dissipated in shims boards (Watts) 
           (not including cables, filters)
    
     coil names and shim drive board channel numbers
     1_Z_up   Z2   Z3   Z4   X    XZ   1_Z_low  Y    YZ   
     0        1    2    3    4    5    6        7    8

     XY_XYZ_up  XY_XYZ_low  YZ2  X3  Y3  XZ2  X2Y2_X2Y2Z_up  X2Y2_X2Y2Z_low   N/C
     9          10          11   12  13  14        15             16           17
    """
    
    binmax = 65535          # 2^16-1
    Itotal_max = 2.3        # max allowed shim current magnitude, amps
                            # note that shim board firmware sets a slightly higher limit (2.4 amps in v37)
    set_DACs_delay = 0.030  # delay before reading RS485 response, seconds
    
    # DAC full-scale currents for setting +/- binmax
    # precision channels 0,1,6 are 0.6791 A full scale
    # others are 0.6720 A full scale
    # shim firmware uses conversion 95999/A or 0.683 A full scale
    Imax = np.array([0.6791,0.6791,0.672,0.672,0.672,0.672,0.6791,0.672,0.672,
                         0.672,0.672,0.672,0.672,0.672,0.672,0.672,0.672])
                         
    # shim coil resistances for each DAC channel, not including filter board or ribbon cables
    # 090222 updated for version 7/8 shim coils
    coilR = np.array([0.332,0.598,0.599,0.994,1.189,1.253,0.281,1.096,1.222,
                      0.998,0.916,1.271,1.701,1.304,1.3356,1.064,0.985])
    
    if test:
        shimvec = shims
      
#          0  1  2  3  4  5  6  7    8    9    10   11    12    13    14    15    16
#          1  Z  X  Y  Z2 XZ YZ X2Y2 XY   Z3   XZ2  YZ2   X2Y2Z XYZ   X3    Y3    Z4   <--multipole       
        shimmat =np.array(
         [[1, 1, 0, 0, 0, 0, 0, 0,   0,   0,   0,   0,    0,    0,    0,    0,   0],   # 0: 1_Z_up
          [0, 0, 0, 0, 1, 0, 0, 0,   0,   0,   0,   0,    0,    0,    0,    0,   0],   # 1: Z2
          [0, 0, 0, 0, 0, 0, 0, 0,   0,   1,   0,   0,    0,    0,    0,    0,   0],   # 2: Z3
          [0, 0, 0, 0, 0, 0, 0, 0,   0,   0,   0,   0,    0,    0,    0,    0,   1],   # 3: Z4
          [0, 0, 1, 0, 0, 0, 0, 0,   0,   0,   0,   0,    0,    0,    0,    0,   0],   # 4: X
          [0, 0, 0, 0, 0, 1, 0, 0,   0,   0,   0,   0,    0,    0,    0,    0,   0],   # 5: XZ
          [1,-1, 0, 0, 0, 0, 0, 0,   0,   0,   0,   0,    0,    0,    0,    0,   0],   # 6: 1_Z_low
          [0, 0, 0, 1, 0, 0, 0, 0,   0,   0,   0,   0,    0,    0,    0,    0,   0],   # 7: Y
          [0, 0, 0, 0, 0, 0, 1, 0,   0,   0,   0,   0,    0,    0,    0,    0,   0],   # 8: YZ
          [0, 0, 0, 0, 0, 0, 0, 0,   1,   0,   0,   0,    0,    1,    0,    0,   0],   # 9: XY_XYZ_up
          [0, 0, 0, 0, 0, 0, 0, 0,   1,   0,   0,   0,    0,   -1,    0,    0,   0],   # 10: XY_XYZ_low
          [0, 0, 0, 0, 0, 0, 0, 0,   0,   0,   0,   1,    0,    0,    0,    0,   0],   # 11: YZ2
          [0, 0, 0, 0, 0, 0, 0, 0,   0,   0,   0,   0,    0,    0,    1,    0,   0],   # 12: X3
          [0, 0, 0, 0, 0, 0, 0, 0,   0,   0,   0,   0,    0,    0,    0,    1,   0],   # 13: Y3
          [0, 0, 0, 0, 0, 0, 0, 0,   0,   0,   1,   0,    0,    0,    0,    0,   0],   # 14: XZ2
          [0, 0, 0, 0, 0, 0, 0, 1,   0,   0,   0,   0,    1,    0,    0,    0,   0],   # 15: X2Y2_X2Y2Z_up
          [0, 0, 0, 0, 0, 0, 0, 1,   0,   0,   0,   0,   -1,    0,    0,    0,   0]])  # 16: X2Y2_X2Y2Z_low
 #                                                                             board/channel: coil   
    else:
        shimvec = np.array(shims[1])
        shimmat = np.array(shims[2])
    
    Iamps = shimmat @ shimvec            # DAC channel outputs in amps
    # saturation flags, +/-1 means channel is saturated, 0 means it is not
    satflags = [0 if abs(Iamps[n])<Imax[n] else int(math.copysign(1,Iamps[n])) for n in range(len(Iamps))]
    # clip magnitude of Iamps[n] to Imax[n]
    Iamps = [Iamps[n] if abs(Iamps[n])<Imax[n] else math.copysign(Imax[n],Iamps[n]) 
                        for n in range(len(Iamps))]  
    Iamps = np.array(Iamps)
    Itotal = np.sum(np.abs(Iamps))       # total current
    power = np.sum(Iamps**2 * coilR)     # total power in coils
    
    Iamps_bin = np.int32(binmax*Iamps/Imax)      # convert shims currents to integer range of DACs
    Iamps_bin_extended = np.append(Iamps_bin,0)  # add unused channel
    print(Iamps_bin_extended)  # for tests only
    
    set_DACs_success = False        # will stay False if setDACs flag is False, too much total current, or set_DACs() fails
    if Itotal < Itotal_max and setDACs == True:  # dont set DACs if total current would be too large
        set_DACs_success,_ = set_DACs(si, Iamps_bin_extended, set_DACs_delay)
    
    return set_DACs_success, Iamps, satflags, Itotal, power
    
