# -*- coding: utf-8 -*-
"""
functions for rear panel external RS485
"""
import time

response_delay = 0.060     # delay before reading command response (sec)

# functions for SuperLogics 8052 digital input module
# address is a string, ie '01', which module on the RS485 bus

def flush(si):
    rec = si.ReceiveExt485()
    if rec[0:1] != b'!':
        return False, rec
    else:
        return True, rec

# get module config
def get_config(si,address):
    adr_bytes = bytes(address,'utf-8')
    si.SendExt485(b'$' + adr_bytes +b'2\r')
    time.sleep(response_delay)
    rec = si.ReceiveExt485()
    if rec[0:1] != b'!':
        return False, rec
    else:
        return True, rec
        
# get module name
def get_name(si,address):
    adr_bytes = bytes(address,'utf-8')
    si.SendExt485(b'$' + adr_bytes + b'M\r')
    time.sleep(response_delay)
    rec = si.ReceiveExt485()
    if rec[0:1] != b'!':
        return False, rec
    else:
        return True, rec
        
# clear latched digital inputs
# if input is low, low state remains latched
# if input is high, high state remains latched
def clear_latches(si,address):
    adr_bytes = bytes(address,'utf-8')
    si.SendExt485(b'$' + adr_bytes + b'C\r')
    time.sleep(response_delay)
    rec = si.ReceiveExt485()
    if rec[0:1] != b'!':
        return False, rec
    else:
        return True, rec

# test for latched high input
# all bits equal to 1 are latched high
def test_latched_high(si,address):
    adr_bytes = bytes(address,'utf-8')
    si.SendExt485(b'$' + adr_bytes + b'L1\r')
    time.sleep(response_delay)
    rec = si.ReceiveExt485()
    if rec[0:1] != b'!':
        return False, rec
    else:
        return True, rec[1:3]
        
# test for latched low input
# bits equal to 1 are latched low
def test_latched_low(si,address):
    adr_bytes = bytes(address,'utf-8')
    si.SendExt485(b'$' + adr_bytes + b'L0\r')
    time.sleep(response_delay)
    rec = si.ReceiveExt485()
    if rec[0:1] != b'!':
        return False, rec
    else:
        return True, rec[1:3]
        
# test for specific bit latched high input
# detects and active-high pulse
# which_bit is an integer 0 to 7
def test_latched_bit_high(si,address,which_bit):
    adr_bytes = bytes(address,'utf-8')
    si.SendExt485(b'$' + adr_bytes + b'L1\r')
    time.sleep(response_delay)
    rec = si.ReceiveExt485()
    if rec[0:1] != b'!':
        return False, rec, None
    else:
        try: 
            is_bit_latched = (int(rec[1:3].decode(),16) & 1<<which_bit) != 0
            return True, rec[1:3], is_bit_latched
        except:
            return False, rec, None
        
# test for specific bit latched low input
# detects and active-low pulse
# which_bit is an integer 0 to 7
def test_latched_bit_low(si,address,which_bit):
    adr_bytes = bytes(address,'utf-8')
    si.SendExt485(b'$' + adr_bytes + b'L0\r')
    time.sleep(response_delay)
    rec = si.ReceiveExt485()
    if rec[0:1] != b'!':
        return False, rec, None
    else:
        try:
            is_bit_latched = (int(rec[1:3].decode(),16) & 1<<which_bit) != 0
            return True, rec[1:3], is_bit_latched
        except:
            return False, rec, None

# repeatedly check for an active-low trigger pulse            
def trigger_test_low(si,address,which_bit,trys,delay):
    print('iter, success, received, is_latched')
    for i in range(int(trys)):
        success,received,is_latched = test_latched_bit_low(si,address,which_bit)
        print(i, success, received, is_latched)
        clear_latches(si,address)
        time.sleep(delay)
        
# repeatedly check for an active-high trigger pulse
def trigger_test_high(si,address,which_bit,trys,delay):
    print('iter, success, received, is_latched')
    for i in range(int(trys)):
        success,received,is_latched = test_latched_bit_high(si,address,which_bit)
        print(i, success, received, is_latched)
        clear_latches(si,address)
        time.sleep(delay)
             