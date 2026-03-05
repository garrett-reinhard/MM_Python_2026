# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 11:24:48 2021
JP mods 031721

@author: Rainer Malzbender, John Price
"""
import datetime
import time
import math
import logging

import numpy as np 

from qmcontrol.ok import okTDeviceInfo, okCFrontPanel, GetAPIVersionString
import qmcontrol.interface_constants as ic

logger = logging.getLogger(__name__)

# note OpenBySerial() sometimes returns 0 even when the USB is not connected
class SpectrometerInterface:
    def __init__(self, configure=False, verbose=True):
        self.configured = False
        logger.info(f"Open USB connection and configure FPGA...")
        self.dev = okCFrontPanel()
        open_return = self.dev.OpenBySerial()
        self.is_present = open_return == 0
        
        if open_return != 0:
            logger.info(f"No spectrometer present on USB")
            return
        self.di = okTDeviceInfo()
        self.dev.GetDeviceInfo(self.di)
        
        if verbose:  
            logger.info(f"Open returns: {open_return}")     # 0 means success
            logger.info(f"Q Mag model and serial number: {self.GetModelSerial()}")
            logger.info(f"Hardware key: {self.HardwareKey()}")
            logger.info(f"USB interface: {self.USB_Interface()}")
            logger.info(f"USB speed: {self.USB_Speed()}")
            logger.info(f"OK Product name: {self.OKProductName()}")
            logger.info(f"OK API version: {self.API_Version()}")
        if configure:
            config_returns = self.Configure(str(ic.config_file.absolute()))
            if verbose:
                logger.info(f"Configuration file: {ic.config_file}")
                logger.info(f"Configure returns: {config_returns}")
            logger.info(f"FPGA configured")
        else:
            logger.info(f"Use preloaded fpga configuration")  
        time.sleep(1.0)
        threshold = self.SetPipeFIFOThreshold()
        self.NormalOperation()
        self.SetTempCOBaud(ic.tempco_baud)
        self.SetShimABaud(ic.shim_baud)
        self.SetExt485Baud(ic.ext_baud)
        self.DisableBlinky()
        self.InitDAC()
        self.LCD_ControlEnable() 
        self.LCD_StartScreen()        
        if verbose:
            logger.info(f"FPGA config sentinel value = {self.Sentinel()}")
            logger.info(f"FPGA config version = {self.ConfigVersion()}")
            logger.info(f"FPGA config time stamp = {self.BuildTime()}")
            # logger.info(f"FPGA serial number = {self.ConfigSerialNumber()}")
            logger.info(f"block size = {ic.block_size} bytes")
            logger.info(f"FIFO threshold = {threshold} 32-bit words")
            logger.info(f"Read clock frequencies from harware:")
            logger.info(f"  Memory interface: {self.MUIMHz():0.7f} MHz")
            logger.info(f"  OCXO: {self.OscMHz():0.7f} MHz")
            logger.info(f"  Sequencer: {self.SeqMHz():0.7f} MHz")
            logger.info(f"FPGA temperature = {self.GetFPGATemperature():0.3f} C")
        self.configured = True
        
    ###################################
    # Methods: Initialization and Close
    ###################################
    # Close the host interface
    def Close(self):
        self.dev.Close()
        
    # Load the FPGA config from a .bit file
    def Configure(self, bitfile):
        config_returns = self.dev.ConfigureFPGA(bitfile)
        return config_returns
        
    def API_Version(self):
        return GetAPIVersionString()
    
    # example: "QM-125-020 220124"
    def GetModelSerial(self):
        return self.dev.GetDeviceID()
    
    # up to 32 characters
    def SetModelSerial(self,string):
        return self.dev.SetDeviceID(string)

    def USB_Speed(self):
        return self.di.usbSpeed
    
    # each OK module has a unique 10-character serial number programmed at the factory
    def HardwareKey(self):
        return self.di.serialNumber
    
    def USB_Interface(self):
        return self.di.deviceInterface

    def OKProductName(self):
        return self.di.productName
    
    # Return the FPGA configuration version, which consists of two chars and a number
    def ConfigVersion(self):
        return chr(self.GetRegField(ic.version_id1)) + \
            chr(self.GetRegField(ic.version_id2)) + \
            str(self.GetRegField(ic.version_num))

    # Return the sentinel register value
    def Sentinel(self):
        return self.GetRegField(ic.sentinel)
    
    # Return the build time from the time stamp register
    def BuildTime(self):
        return datetime.datetime.fromtimestamp(self.GetRegField(ic.time_stamp)).strftime('%Y-%m-%d %H:%M:%S')
        
    # Return the serial number register, which should be in the range 0-9999
    def ConfigSerialNumber(self):
        return self.GetRegField(ic.ser_num)
    
    def EnableBlinky(self):
        self.SetRegField(ic.disable_blinky, 0)

    def DisableBlinky(self):
        self.SetRegField(ic.disable_blinky, 1)
    
    # Send a SPI command to a device (0 = DAC, 1 = ADC)
    # To write a SPI register, use data sheet register address
    # To read a SPI register, also set bit 7 of regaddr = 1
    # (0, 0xA, 4) DAC mix mode, (0, 0xA, 0) DAC normal mode
    def _SpiSend(self, device, regaddr, regval): 
        self.SetRegField(ic.spi_devsel, (1<<device))
        self.SetRegField(ic.spi_addr, regaddr)
        self.SetRegField(ic.spi_wdata, regval)
        self.SetRegField(ic.spi_go, 1)
        return self.GetRegField(ic.spi_rdata)
    
    # Initialize the DAC
    def InitDAC(self):
        self.SetRegField(ic.dac_reset, 1) 
        self.SetRegField(ic.dac_reset, 0)
        # Set SMP = 27 (alpha version)
        # Set SMP = 16 (beta version)
        # self._SpiSend(0, 0x05, 16) # example
        self._SpiSend(0, 0x05, 22)
        # Set mix mode
        self._SpiSend(0, 0x0A, 4)
    
    ###############################################
    # Methods: Direct Control Register Manipulation
    ###############################################
    def GetRegister(self, addr):
        return self.dev.ReadRegister(addr)
    
    def SetRegister(self, addr, value):
        self.dev.WriteRegister(addr, value)

    def GetRegField(self, rf):
        regval = self.GetRegister(rf.regaddr)
        mask = ((2**rf.width)-1) << rf.offset
        return (regval & mask) >> rf.offset

    def SetRegField(self, rf, val):
        regval = self.dev.ReadRegister(rf.regaddr)
        mask = ((2**rf.width)-1) << rf.offset
        wrval = (val << rf.offset) & mask
        # Clear the bits
        regval = regval & ~mask
        # Or in the new bits
        regval = regval | wrval
        # Write it back out
        self.dev.WriteRegister(rf.regaddr, regval)

    ##########################
    # Methods: Pulse Sequences
    ##########################
    def GetSequencerEntry(self, addr):
        self.SetRegField(ic.seq_addr, addr)
        self.SetRegField(ic.seq_read_entry, 1)
        opcode = self.GetRegField(ic.seq_ropcode)
        delay = self.GetRegField(ic.seq_rdelay)
        return opcode, delay

    def SetSequencerEntry(self, addr, opcode, delay):
        self.SetRegField(ic.seq_addr, addr)
        self.SetRegField(ic.seq_wopcode, opcode)
        self.SetRegField(ic.seq_wdelay, delay)
        self.SetRegField(ic.seq_write_entry, 1)

    # Set the first N words of the pulse sequence to constant values
    def ClearPulseSequence(self, opcode, delay, N):
        for i in range(0,N):
            self.SetSequencerEntry(i, opcode, delay)
            
    # Load pulse sequence one opcode at a time
    # [delays,opcodes] are in a nested list of 32-bit-range ints 
    # Assert sequencer reset during load
    # Reset all flags after load
    # Do not release sequencer reset until ready to run the sequence
    def LoadPulseSequence(self, int_opcodes):
        self.AssertSeqReset()
        for i in range(0,len(int_opcodes)):
            self.SetSequencerEntry(i, int_opcodes[i][1], int_opcodes[i][0])
        self.ResetSeqFlag()
        self.ResetSeqHaltFlag()
        self.ResetMemAcqDoneFlag()
        
    # Load pulse sequence using a block transfer
    # [delays,opcodes] are in a nested list of 32-bit-range ints 
    # Assert sequencer reset during load
    # Reset all flags after load
    # Do not release sequencer reset until ready to run the sequence
    def LoadPulseSequenceFast(self, int_opcodes):
        self.AssertSeqReset()
        
        self.SetRegField(ic.seq_usepipe, 1)    # set "use pipe" bit
        self.SetRegField(ic.seq_resetpipe, 1)  # toggle "reset pipe" bit
        self.SetRegField(ic.seq_resetpipe, 0)

        # Create a byte array the size of the whole sequencer table
        # initialized to zero
        seqbytes = bytearray(ic.cSeqTableMaxEntries*8)
        # Load the bytearray with the nested list [delays,opcodes]
        for i in range(0, len(int_opcodes)):
            bi = i * 8
            seqbytes[bi+3] = (int_opcodes[i][1] & 0xFF000000) >> 24
            seqbytes[bi+2] = (int_opcodes[i][1] & 0x00FF0000) >> 16
            seqbytes[bi+1] = (int_opcodes[i][1] & 0x0000FF00) >> 8
            seqbytes[bi+0] = (int_opcodes[i][1] & 0x000000FF) >> 0
            seqbytes[bi+7] = (int_opcodes[i][0] & 0xFF000000) >> 24
            seqbytes[bi+6] = (int_opcodes[i][0] & 0x00FF0000) >> 16
            seqbytes[bi+5] = (int_opcodes[i][0] & 0x0000FF00) >> 8
            seqbytes[bi+4] = (int_opcodes[i][0] & 0x000000FF) >> 0
        self.dev.WriteToPipeIn(ic.cSeqPipeInEndPoint, seqbytes)
        self.SetRegField(ic.seq_usepipe, 0) # reset "use pipe" bit
        
        self.ResetSeqFlag()
        self.ResetSeqHaltFlag()
        self.ResetMemAcqDoneFlag()
    
    # Read N words of the pulse sequencer memory starting at address 0
    def ReadPulseSequence(self,nwords):
        int_opcodes = []
        for i in range(nwords):
            opcode, delay = self.GetSequencerEntry(i)
            int_opcodes.append([delay, opcode])
        return int_opcodes
        
    ########################################
    # Methods: Oscillator Control Registers
    ########################################
    # Set the phase increment of NCO 0 from a frequency in MHz
    # %1.0 gets fractional part
    def SetRefNCOFreq0(self, freqMHz):
        phaseinc = np.uint32((2**32)*( abs(freqMHz/ic.seqclk_MHz)%1.0 ))
        self.SetRegField(ic.refnco_phinc0, int(phaseinc))
        
    # Set the phase increment of NCO 1
    def SetRefNCOFreq1(self, freqMHz):
        phaseinc = np.uint32((2**32)*( abs(freqMHz/ic.seqclk_MHz)%1.0 ))
        self.SetRegField(ic.refnco_phinc1, int(phaseinc))        
        
    # Set the phase increment of NCO 2
    def SetRefNCOFreq2(self, freqMHz):
        phaseinc = np.uint32((2**32)*( abs(freqMHz/ic.seqclk_MHz)%1.0 ))
        self.SetRegField(ic.refnco_phinc2, int(phaseinc))        
        
    # Set the phase increment of NCO 3
    def SetRefNCOFreq3(self, freqMHz):
        phaseinc = np.uint32((2**32)*( abs(freqMHz/ic.seqclk_MHz)%1.0 ))
        self.SetRegField(ic.refnco_phinc3, int(phaseinc))        

    # Set the phase increment of the test NCO
    def SetTestNCOFreq(self, freqMHz):
        phaseinc = np.uint32((2**32)*( abs(freqMHz/ic.seqclk_MHz)%1.0 ))
        self.SetRegField(ic.testnco_phinc, int(phaseinc))

    # Set the starting phase of the test NCO, positive phase in degrees
    def SetTestNCOPhase(self, phaseDeg):
        phase_word = np.uint8(256*phaseDeg/360)
        self.SetRegField(ic.testnco_phase, int(phase_word))

    #################################
    # Methods: CIC Filters and Decimation
    #################################
    # Set the decimation factor for the CIC filter
    def SetDecimation(self, d):
        self.SetRegField(ic.decimate_m1, d-1)
    
    # Set the 5-bit attenuation of the 43-bit CIC filter outputs
    # 0b11111 = 0d31 is the 16 MSBs, 0b00100 = 0d4 is the 16 LSBs
    # 0d3 and 0d2 output all ones, 0d1 and 0d0 all zeroes
    def SetCICAtten(self, val):
        self.SetRegField(ic.cic_outselect, val)
    
    ######################################
    # Methods: Sequencer Flags and Control
    ######################################
    # Force sequencer to sit at opcode memory location 0
    def AssertSeqReset(self):
        self.SetRegField(ic.seq_reset, 1)
    
    # Start sequencer from opcode memory location 0
    def ReleaseSeqReset(self):     
        self.SetRegField(ic.seq_reset, 0)
    
    # Get the "sequencer time", which is a counter driven by seq_clk with
    # a 16-bit prescale, converted to seconds. Starts from zero when
    # sequencer reset is released.
    def GetSeqTime(self):
        return self.GetRegField(ic.seq_time)*2**16/(ic.seqclk_MHz*10**6)
    
    # Return the value the flag raised by a seqFlag bit in an opcode
    def SeqFlag(self):
        return self.GetRegField(ic.seq_dav)
    
    # Reset the sequencer flag
    def ResetSeqFlag(self):
        self.SetRegField(ic.seq_reset_dav, 1)
    
    # Wait for the sequencer flag
    def WaitSeqFlag(self):
        while True:
            flag = self.SeqFlag()
            if flag:
                break
        self.ResetSeqFlag()
    
    # Return the value of the halt flag from the sequencer
    def SeqHaltFlag(self):
        return self.GetRegField(ic.seq_halt)
    
    # Reset the halt flag
    def ResetSeqHaltFlag(self):
        self.SetRegField(ic.seq_reset_halt, 1)
    
    # Wait for the halt flag
    def WaitSeqHaltFlag(self):
        while True:
            flag = self.SeqHaltFlag()
            if flag:
                break
        self.ResetSeqHaltFlag()
        
    # Return the value of the acquisition done flag from the mem controller
    def MemAcqDoneFlag(self):
        return self.GetRegField(ic.seq_acqdone)
    
    # Reset the acquisition done flag
    def ResetMemAcqDoneFlag(self):
        self.SetRegField(ic.seq_reset_acqdone, 1)
        
    # Wait for the acquisition done flag
    def WaitMemAcqDoneFlag(self):
        while True:
            flag = self.MemAcqDoneFlag()
            if flag:
                break
        self.ResetMemAcqDoneFlag()
    
    ########################
    # Methods: Data memory
    ########################
    # Set pipe fifo threshold, derived from block_size.
    def SetPipeFIFOThreshold(self):
        threshold = int(ic.block_size / 4 - 1)
        self.SetRegField(ic.pipe_threshold, threshold)
        return threshold
    
    # Set the memory address, either for diagnostics, or for reading
    # (This does not control where data is written into memory)
    def SetMemoryAddress(self, ma):
        self.SetRegField(ic.mem_addr, ma)
        
    # Allow the memory controller to retrieve data and send it to the Opal
    # Kelly pipe fifo.
    def EnableMemReading(self, tf):
        self.SetRegField(ic.mem_reading, tf)
        
    # Enable page mode
    def EnableMemPageMode(self, tf):
        self.SetRegField(ic.mem_page_mode, tf)
        
    # Set memory page size, a 20-bit integer
    # units are 4 samples or 16 bytes
    def SetMemPageSize(self, size):
        self.SetRegField(ic.mem_page_size, size)
        
    # Transfer data from memory to USB through the Opal Kelly pipe.
    def GetPipeData(self, bytedata):
        nbytes = self.dev.ReadFromBlockPipeOut(ic.cDataPipeOutEndPoint, ic.block_size, bytedata)
        return nbytes
    
    # Return the number of 128-bit words the memory controller wrote.
    def GetMemWriteCount(self):
        return self.GetRegField(ic.mem_write_count)
    
    # Get memory address where last acquisition started
    def GetMemAddrAcqStart(self):
        return self.GetRegField(ic.mem_addr_acqstart)
    
    # Get memory address where last acquisition ended
    def GetMemAddrAcqEnd(self):
        return self.GetRegField(ic.mem_addr_acqend)
    
    # Transfer N samples from data memory at start_address 
    # a sample is 4 bytes, a block is block_size bytes
    # block_size is always a multiple of 16, the memory word size
    # data[0.:] int16s from cos mixer output "real" (numpy array)
    # data[1,:] int16s from sin mixer output "imag", but need sign change
    # minus sign --> positive signal frequency goes CCW in complex plane
    #    and is a positive frequency under numpy fft conventions.
    # This works equally in 1st and second Nyquist zones
    # Note data packing is special in CIC_Bypass() mode
    def GetSamples(self, nsamples, start_address):

        self.SetMemoryAddress(start_address)  # address for reading
        blocks_to_transfer = math.ceil(4*nsamples/ic.block_size)
        bytes_to_transfer = ic.block_size*blocks_to_transfer
        bytedata = bytearray(bytes_to_transfer)
        self.EnableMemReading(1)
        nbytes_received = self.GetPipeData(bytedata)
        self.EnableMemReading(0)
        dataflat=np.frombuffer(bytedata, dtype=np.int16, count=2*nsamples)
        data=dataflat.reshape((int(np.size(dataflat)/2)),2).transpose()
        data[1,:] = -data[1,:]               # change sign of imaginary part
        return data, blocks_to_transfer, bytes_to_transfer, nbytes_received
    
    ##############################
    # Methods: RS-485
    ##############################
    # Set the baud rate for the temperature controller RS-485
    def SetTempCOBaud(self, baud):
        # The main clock is 100.8 MHz
        divisor = int(100800000 / baud);
        self.SetRegField(ic.tempco_divisor, divisor - 1)

    # Set the baud rate for the SHIMA RS-485
    def SetShimABaud(self, baud):
        # The main clock is 100.8 MHz
        divisor = int(100800000 / baud);
        self.SetRegField(ic.shima_divisor, divisor - 1)
    
    # # Set the baud rate for the SHIMB RS-485
    # def SetShimBBaud(self, baud): 
        # # The main clock is 100.8 MHz
        # divisor = int(100800000 / baud);
        # self.SetRegField(ic.shimb_divisor, divisor - 1)
    
    # Set the baud rate for the spare RS-485
    def SetExt485Baud(self, baud):
        # The main clock is 100.8 MHz
        divisor = int(100800000 / baud);
        self.SetRegField(ic.ext485_divisor, divisor - 1)
        
    # Send bytes to the temperature controller RS-485
    # data to and from RS485 is type bytes or type bytearray
    # type str is dangerous because unicode includes chars bigger than a byte
    def SendTempCo(self, s):
        for i in range(len(s)):
            self.SetRegField(ic.tempco_txdata, s[i])
            self.SetRegField(ic.tempco_txgo, 1)
    
    # Retrieve bytes from the temperature controller RS-485
    # a bytearray is returned
    def ReceiveTempCo(self):
        nbytes = self.GetRegField(ic.tempco_rxnavail)
        #print('bytes available: ', nbytes)                    # for tests
        s = bytearray(nbytes)                                 
        for i in range(nbytes):
            self.SetRegField(ic.tempco_rxread, 1)
            s[i] = self.GetRegField(ic.tempco_rxdata)
        return s
        
    # Send bytes to the SHIMA RS-485
    def SendShimA(self, s):
        for i in range(len(s)):
            self.SetRegField(ic.shima_txdata, s[i])
            self.SetRegField(ic.shima_txgo, 1)
            
    # Retrieve bytes from the SHIMA RS-485
    def ReceiveShimA(self):
        nbytes = self.GetRegField(ic.shima_rxnavail)
        s = bytearray([])
        for i in range(nbytes):
            self.SetRegField(ic.shima_rxread, 1)
            s += bytes([self.GetRegField(ic.shima_rxdata)])
        return s
            
    # Send bytes to the spare RS-485
    def SendExt485(self, s):
        for i in range(len(s)):
            self.SetRegField(ic.ext485_txdata, s[i])
            self.SetRegField(ic.ext485_txgo, 1)
 
    # Retrieve bytes from the spare RS-485
    def ReceiveExt485(self):
        nbytes = self.GetRegField(ic.ext485_rxnavail)
        s = bytearray([])
        for i in range(nbytes):
            self.SetRegField(ic.ext485_rxread, 1)
            s += bytes([self.GetRegField(ic.ext485_rxdata)])
        return s
    
    ###############
    # Methods: LCD
    ###############
    # Enable control of the LCD by the host
    def LCD_ControlEnable(self):
        self.SetRegField(ic.pc_is_here, 1)

    # Send an LCD command
    # RS=0 command register
    # RS=1 data register
    def _LCD_Send(self, x, rs):
        self.SetRegField(ic.lcd_data, x)
        self.SetRegField(ic.lcd_rs, rs)
        self.SetRegField(ic.lcd_go, 1)

    # Clear the entire LCD display
    def LCD_Clear(self):
        self._LCD_Send(1, 0)

    # Go to the beginning of the first LCD row
    def LCD_Home(self):
        self._LCD_Send(128, 0)

    # Go to the beginning of the second LCD row
    def LCD_Line2(self):
        self._LCD_Send(128+40, 0)
    
    # Display a string at the current LCD position
    def LCD_String(self, s):
        for i in range(0, len(s)):
            self._LCD_Send(ord(s[i]), 1)

    # Display two strings, one on each line of the LCD display
    def LCD_Display(self, s1, s2):
        self.LCD_Clear()
        self.LCD_Home()
        self.LCD_String(s1)
        self.LCD_Line2()
        self.LCD_String(s2)
        
    # shift characters to the right
    def LCD_RightShift(self):
        self._LCD_Send(28, 0)
        
    # shift characters to the left
    def LCD_LeftShift(self):
        self._LCD_Send(24, 0)
        
    def LCD_StartScreen(self):
        ms = self.GetModelSerial()
        vs = self.ConfigVersion()
        self.LCD_Clear()
        self.LCD_Home()
        self.LCD_String(ms[:6] + ' SN' + ms[11:])   
        self.LCD_Line2()
        self.LCD_String('config V' + vs[2] + '.' + vs[3:]) 
    
    #######################################
    # Methods: Test and Diagnostic Features
    #######################################
    
    # Get FPGA temperature in degrees C. Max junction T = 125 C
    def GetFPGATemperature(self):
        regval = self.GetRegField(ic.fpga_temp)
        temperatureC = regval*503.975/4096 - 273.15
        return temperatureC
        
    # Enable or disable the test NCO as input to the mixers
    # instead of the ADC
    def SetMixerInputTestNCO(self, tf):
        self.SetRegField(ic.cic_usetestnco, tf)
            
    # Enable or disable the pattern generator as memory input
    def SetMemInputPGen(self, tf):
        self.SetRegField(ic.mem_use_pgen, tf)
        
    # Set pattern generator mode
    def SetPGenMode(self, mode):
        self.SetRegField(ic.pgen_patsel, mode)
        
    # Enable or disable the test NCO as input to the DAC
    def SetDacInputTestNCO(self, tf):
        self.SetRegField(ic.dac_usetestnco, tf)
        
    # Allow the host to set the RF attenuation value
    def SetDacAttenOverride(self, tf):
        self.SetRegField(ic.rf_atten_override, tf)
        
    # Set the RF attenuation override value
    def SetDacAtten(self, att):
        self.SetRegField(ic.rf_atten, att)
        
    # Return the memory user interface clock frequency
    # These are measured by a frequency counter implemented in the FPGA
    # and are relative to the 100.8 MHz clock from the USB interface
    def MUIMHz(self):
        regfreq = self.GetRegField(ic.muiclk_freq)
        # return (200.0 * float(regfreq)) / 1048575.0  # before version 2.20
        return (1024.0 * 1024.0 * 100.8) / float(regfreq)
    
    # Return the OCXO frequency
    def OscMHz(self):
        regfreq = self.GetRegField(ic.oscclk_freq)
        # return (200.0 * float(regfreq)) / 1048575.0  # before version 2.20
        return (1024.0 * 1024.0 * 100.8) / float(regfreq)
    
    # Return the sequencer clock frequency
    def SeqMHz(self):
        regfreq = self.GetRegField(ic.seqclk_freq)
        # return (200.0 * float(regfreq)) / 1048575.0  # before version 2.20 
        return (1024.0 * 1024.0 * 100.8) / float(regfreq)
    
    # write 14-bit ADC data directly to memory at sampling clock freq
    # writing is still under control of sequencer memAcq and memZero bits
    # 14-bit samples are packed d[0,0], d[1,0], d[0,1], d[1,1], d[0,2],...
    # where d=data[] the output of GetData() method.
    # also there is a mod(15) counter c packed in with the data 
    # d[0,n](15,14) = c(1,0), d[1,n](15,14) = c(3,2)
    # the counter can be used to check if there are missing samples
    def CIC_Bypass(self, tf):
        self.SetRegField(ic.cic_passthrough, tf)    
    
    # Set all the muxes for normal ADC/DAC operation, not test modes
    def NormalOperation(self):
        # Make sure Mixer input is not test NCO
        self.SetMixerInputTestNCO(0)
        # Make sure memory input is not pattern generator
        self.SetMemInputPGen(0)
        # Set Tx DAC input to reference NCO (not test NCO)
        self.SetDacInputTestNCO(0)
        # Let the sequencer control RF attenuation
        self.SetDacAttenOverride(0)
        # Don't bypass mixers, CIC filters and decimation
        self.CIC_Bypass(0)
    
    # Return one 14-bit ADC sample, sign extended to to 16-bits.
    def ADC_Data(self):
        return np.int16(4*self.GetRegField(ic.adc_data))/4


    