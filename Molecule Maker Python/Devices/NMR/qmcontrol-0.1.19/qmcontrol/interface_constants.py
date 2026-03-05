# -*- coding: utf-8 -*-
"""
Created on April 23

@author: Rainer Malzbender, John Price
"""
from pathlib import Path
import sys
import os

# shell command to set DEV_MODE env variable
# $env:DEV_MODE=1

module_root = Path(__file__).parent.resolve()


if hasattr(sys,"getwindowsversion"):
    programdata_root = Path("/ProgramData") / "QMagnetics"
else:
    programdata_root = Path.home() / "QMagnetics"

if "DEV_MODE" in os.environ:
    programdata_root = module_root


programdata_root.mkdir(mode=777, parents=True, exist_ok=True)
        
bitfiles_dir = module_root / 'bitfiles'
settings_dir = programdata_root / 'settings'
settings_dir.mkdir(mode=777, parents=True, exist_ok=True)
# Global constants
config_file = bitfiles_dir / "seq_beta_QB231.bit"
settings_file = Path("./qmcontrol/settings/settings.json")
shims_dir = programdata_root / 'shims'
logfile = programdata_root / "logs" / "qmcontrol.log"


seqclk_MHz = 160.000     # must correspond to bitfile.  don't get this from the hardware
                         # use this def so it will be present when hardware is not
hardware_filter = "CIC 2nd order, differential delay = 1"
block_size = 1024        # for USB data transfer. in bytes, a multiple of 16, the memory word size
cSeqTableMaxEntries = 8192
cDataPipeOutEndPoint = 0xA0
cSeqPipeInEndPoint = 0x80

# RS485 baud rates
tempco_baud = 9615.36  # Teensy LC 9600 baud rate is not quite 9600, docs say 0.16% high
shim_baud = 38400      # works for Teensy 4.0
ext_baud = 9600

# constants for converting times to number of clock cycles
ns = seqclk_MHz/1000     # number of clock cycles per ns
us = seqclk_MHz          # per us
ms = seqclk_MHz*1000     # per ms
s = seqclk_MHz*10**6     # per s
        
# constant for converting phase in degrees to 8-bit phase
deg = (256/360)

# Class to define interface register bit fields, arguments are
#    register address
#    width, in bits
#    offset, or which bit in the register contains the LSB of the field
class RegField:
    def __init__(self, regaddr, width, offset):
        self.regaddr = regaddr
        self.width = width
        self.offset = offset
        

# Register addresses
r_miscctrl  = 0x0000
r_trig0     = 0x0003
r_stat0     = 0x0005
r_muifreq   = 0x0007
r_oscfreq   = 0x0008
r_seqfreq   = 0x0009
# LCD
r_lcd       = 0x0010
# RS-485
r_tempco_tx = 0x0020
r_tempco_rx = 0x0021
r_shima_tx  = 0x0022
r_shima_rx  = 0x0023
r_shimb_tx  = 0x0024
r_shimb_rx  = 0x0025
r_ext485_tx = 0x0026
r_ext485_rx = 0x0027
# DAC
r_dac_ctrl  = 0x0030
# ADC
r_adc_ctrl  = 0x0040
r_adc_data  = 0x0041
# Sequencer
r_seq_ctrl    = 0x0050
r_seq_addr    = 0x0051
r_seq_wopcode = 0x0052
r_seq_wdelay  = 0x0053
r_seq_ropcode = 0x0054
r_seq_rdelay  = 0x0055
r_seq_addrout = 0x0056
r_seq_seqtime = 0x0057
# Pattern generator
r_pgen_ctrl   = 0x005F
# NCO
r_refnco_freq0  = 0x0060
r_refnco_freq1  = 0x0061
r_refnco_freq2  = 0x0062
r_refnco_freq3  = 0x0063
r_testnco_freq  = 0x0064
r_testnco_phase = 0x0065
# SPI
r_spi_ctrl  = 0x0070
r_spi_rdata = 0x0071
# Memory controller
r_mem_ctrl          = 0x0080
r_mem_addr          = 0x0081
r_mem_words_m1      = 0x0082
r_pipe_threshold    = 0x0083
r_mem_diag_wd0      = 0x0084
r_mem_diag_wd1      = 0x0085
r_mem_diag_wd2      = 0x0086
r_mem_diag_wd3      = 0x0087
r_mem_diag_rd0      = 0x0088
r_mem_diag_rd1      = 0x0089
r_mem_diag_rd2      = 0x008A
r_mem_diag_rd3      = 0x008B
r_mem_write_count   = 0x008C
r_mem_read_count    = 0x008D
r_mem_addr_acqstart = 0x008E
r_mem_addr_acqend   = 0x008F
r_mem_page_ctrl     = 0x0090
# Miscellaneous
r_sentinel   = 0x1234
r_version    = 0xFFF8
r_time_stamp = 0xFFF9
r_ser_num    = 0xFFFA




# Register Bit Fields. 
# Control register
disable_blinky  = RegField(r_miscctrl, 1, 0)
pc_is_here      = RegField(r_miscctrl, 1, 1)
software_reset  = RegField(r_miscctrl, 1, 2)
decimate_m1     = RegField(r_miscctrl, 16, 3)
cic_usetestnco  = RegField(r_miscctrl, 1, 19)
cic_outselect   = RegField(r_miscctrl, 5, 20)
seqclk_selslow  = RegField(r_miscctrl, 1, 25)
cic_passthrough = RegField(r_miscctrl, 1, 26)

# Trigger register
seq_reset_dav     = RegField(r_trig0, 1, 0)
seq_reset_halt    = RegField(r_trig0, 1, 1)
seq_reset_acqdone = RegField(r_trig0, 1, 2)
spi_go            = RegField(r_trig0, 1, 3)
prepc_trig        = RegField(r_trig0, 1, 4)
lcd_go            = RegField(r_trig0, 1, 5)
tempco_txgo       = RegField(r_trig0, 1, 6)
shima_txgo        = RegField(r_trig0, 1, 7)
shimb_txgo        = RegField(r_trig0, 1, 8)
ext485_txgo       = RegField(r_trig0, 1, 9)
tempco_rxread     = RegField(r_trig0, 1, 10)
shima_rxread      = RegField(r_trig0, 1, 11)
shimb_rxread      = RegField(r_trig0, 1, 12)
ext485_rxread     = RegField(r_trig0, 1, 13)
seq_write_entry   = RegField(r_trig0, 1, 14)
seq_read_entry    = RegField(r_trig0, 1, 15)

# Misc status
seq_dav     = RegField(r_stat0, 1, 0)
seq_halt    = RegField(r_stat0, 1, 1)
seq_acqdone = RegField(r_stat0, 1, 2)
fpga_temp  = RegField(r_stat0, 12, 3)

# Frequencies
muiclk_freq = RegField(r_muifreq, 32, 0)
oscclk_freq = RegField(r_oscfreq, 32, 0)
seqclk_freq = RegField(r_seqfreq, 32, 0)

# LCD
lcd_data = RegField(r_lcd, 8, 0)
lcd_rs   = RegField(r_lcd, 1, 8)

# RS-485
tempco_txdata =   RegField(r_tempco_tx, 8, 0)
tempco_divisor =  RegField(r_tempco_tx, 16, 8)
tempco_rxdata =   RegField(r_tempco_rx, 8, 0)
tempco_rxnavail = RegField(r_tempco_rx, 8, 8)

shima_txdata =   RegField(r_shima_tx, 8, 0)
shima_divisor =  RegField(r_shima_tx, 16, 8)
shima_rxdata =   RegField(r_shima_rx, 8, 0)
shima_rxnavail = RegField(r_shima_rx, 8, 8)

shimb_txdata =   RegField(r_shimb_tx, 8, 0)
shimb_divisor =  RegField(r_shimb_tx, 16, 8)
shimb_rxdata =   RegField(r_shimb_rx, 8, 0)
shimb_rxnavail = RegField(r_shimb_rx, 8, 8)

ext485_txdata   = RegField(r_ext485_tx, 8, 0)
ext485_divisor  = RegField(r_ext485_tx, 16, 8)
ext485_rxdata   = RegField(r_ext485_rx, 8, 0)
ext485_rxnavail = RegField(r_ext485_rx, 8, 8)

# DAC
dac_reset         = RegField(r_dac_ctrl, 1, 0)
rf_atten_override = RegField(r_dac_ctrl, 1, 1)
dac_usetestnco    = RegField(r_dac_ctrl, 1, 2)
rf_atten          = RegField(r_dac_ctrl, 8, 3)

# ADC
adc_reset = RegField(r_adc_ctrl, 1, 0)
adc_data  = RegField(r_adc_data, 16, 0)

# Sequencer
seq_reset    = RegField(r_seq_ctrl, 1, 0)
seq_usepipe   = RegField(r_seq_ctrl, 1, 1)
seq_resetpipe = RegField(r_seq_ctrl, 1, 2)
seq_addr     = RegField(r_seq_addr, 13, 0)
seq_wopcode  = RegField(r_seq_wopcode, 32, 0)
seq_wdelay   = RegField(r_seq_wdelay, 32, 0)
seq_ropcode  = RegField(r_seq_ropcode, 32, 0)
seq_rdelay   = RegField(r_seq_rdelay, 32, 0)
seq_addrout  = RegField(r_seq_addrout, 13, 0)
seq_time     = RegField(r_seq_seqtime, 32, 0)

# Pattern generator
pgen_patsel  = RegField(r_pgen_ctrl, 4, 16)
mem_use_pgen = RegField(r_pgen_ctrl, 1, 20)

# NCO
refnco_phinc0 = RegField(r_refnco_freq0, 32, 0)
refnco_phinc1 = RegField(r_refnco_freq1, 32, 0)
refnco_phinc2 = RegField(r_refnco_freq2, 32, 0)
refnco_phinc3 = RegField(r_refnco_freq3, 32, 0)
testnco_phinc = RegField(r_testnco_freq, 32, 0)
testnco_phase = RegField(r_testnco_phase, 8, 0)

# SPI
spi_devsel = RegField(r_spi_ctrl, 4, 0)
spi_addr   = RegField(r_spi_ctrl, 16, 4)
spi_wdata  = RegField(r_spi_ctrl, 8, 20)
spi_rdata  = RegField(r_spi_rdata, 8, 0)

# Memory controller
mem_reset         = RegField(r_mem_ctrl, 1, 0)
mem_reading       = RegField(r_mem_ctrl, 1, 2)
mem_diagmode      = RegField(r_mem_ctrl, 1, 3)
mem_diag_write    = RegField(r_mem_ctrl, 1, 5)
mem_diag_read     = RegField(r_mem_ctrl, 1, 6)
mem_addr          = RegField(r_mem_addr, 29, 0)
mem_words_m1      = RegField(r_mem_words_m1, 32, 0)
pipe_threshold    = RegField(r_pipe_threshold, 11, 0)
mem_diag_wd0      = RegField(r_mem_diag_wd0, 32, 0)
mem_diag_wd1      = RegField(r_mem_diag_wd1, 32, 0)
mem_diag_wd2      = RegField(r_mem_diag_wd2, 32, 0)
mem_diag_wd3      = RegField(r_mem_diag_wd3, 32, 0)
mem_diag_rd0      = RegField(r_mem_diag_rd0, 32, 0)
mem_diag_rd1      = RegField(r_mem_diag_rd1, 32, 0)
mem_diag_rd2      = RegField(r_mem_diag_rd2, 32, 0)
mem_diag_rd3      = RegField(r_mem_diag_rd3, 32, 0)
mem_write_count   = RegField(r_mem_write_count, 32, 0)
mem_read_count    = RegField(r_mem_read_count, 32, 0)
mem_addr_acqstart = RegField(r_mem_addr_acqstart, 29, 0)
mem_addr_acqend   = RegField(r_mem_addr_acqend, 29, 0)
mem_page_size     = RegField(r_mem_page_ctrl, 20, 0)
mem_page_mode     = RegField(r_mem_page_ctrl, 1, 20)

# Sentinel register
sentinel    = RegField(r_sentinel, 32, 0)
version_id1 = RegField(r_version, 8, 24)
version_id2 = RegField(r_version, 8, 16)
version_num = RegField(r_version, 16, 0)
time_stamp  = RegField(r_time_stamp, 32, 0)
ser_num     = RegField(r_ser_num, 32, 0)    

 
    