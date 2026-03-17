# -*- coding: utf-8 -*-
"""
Created 042421

@author: John Price
"""
import logging

from qmcontrol.interface_constants import s, ms, us, deg, seqclk_MHz, cSeqTableMaxEntries

logger = logging.getLogger(__name__)

# base class for creating pulse sequences
class PulseSequence:
    def __init__(self):
        
        # define sequencer opcode fields
        # dict containing field names, bit positions, and max decimal value
        # 'delay' has its own 32-bit word, in a separate 32-bit word
        self.opcode_fields = {'delay': [0,2**32-1], 'seqFlag': [31,1], 
                'seqHalt': [30,1], 'seqOut': [26,15], 'memAcq': [25,1],
                'memZero': [24,1], 'CICreset': [23,1],'RFreset': [22,1],
                'RFphase': [14,255], 'RFatten': [6,255], 'RFfreq': [4,3]}
        
        # fixed delays, in integer number of clock cycles
        self.min_delay = round(0.1*us)   # very short delay
        self.short_delay = round(10*us)  # short delay for resets
        #self.rx_delay1 =  round(10*us)   # receiver recovery time before toggle T/R switch
        #self.rx_delay2 =  round(100*us)  # receiver recovery time after toggle T/R switch
   
    # Convert opcodes as a list of dicts to a nested list of 32-bit-range integers
    # Check that all fields are present and that values are valid
    def _MakeIntOpcodes(self):
        opcodes32=[]
        for opcode in self.opcodes:
            if not(opcode.keys() == self.opcode_fields.keys()):
                raise Exception("incorrect or missing field in opcode")
            opcodes32.append([0,0])
            for key, value in self.opcode_fields.items():
                if key == 'delay':
                    opcodes32[-1][0] = opcode[key]
                else:
                    opcodes32[-1][1] = opcodes32[-1][1] + opcode[key]*2**value[0]
                if not isinstance(opcode[key], int):
                    raise Exception('all fields must be integers')
                if opcode[key]<0 or opcode[key]>value[1]:
                    raise Exception('illegal opcode field value')
        #if len(opcodes32) > cSeqTableMaxEntries:
            #raise Exception('pulse sequence exceeds max length')
        return opcodes32
    
    # initialize opcode list of dicts and the time mark table
    def _FirstOpcode(self):
        self.opcodes=[{}]
        self.marks=[]
    
    # set a time mark in the sequence's time mark table
    # at start of current opcode. name is nomally a string
    # Mark table times are in clock cycles
    def _Mark(self, name):
        opcode_start_time = 0
        for index in range(len(self.opcodes)-1):
            opcode_start_time += self.opcodes[index]["delay"]
        self.marks.append([opcode_start_time, name])
    
    # get a mark time in seconds
    def GetMarkTime(self, index):
        return self.marks[index][0]/(seqclk_MHz*10**6)
            
    # append a copy of the previous opcode
    # and check that all fields were set
    def _NextOpcode(self):
         if not(self.opcodes[-1].keys() == self.opcode_fields.keys()):
             raise Exception("incorrect or missing field in previous opcode")
         self.opcodes.append(self.opcodes[-1].copy())
    
    # set an opcode field
    def _Field(self, key, value):
        if not isinstance(value, int):
            raise Exception('all fields must be integers')
        if value < 0 or value > self.opcode_fields[key][1]:
            raise Exception('illegal opcode field value')
        self.opcodes[-1][key] = value
    
    # create integer sequence after all opcodes are defined
    def _EndSequence(self):
        self.opcodes32 = self._MakeIntOpcodes()
    
    # return the number of opcodes
    def Len(self):
        return len(self.opcodes)
    
    # return the sequence as a dictionary
    def DictOpcodes(self):
        return self.opcodes
    
    # return the sequence as a nested list of 32-bit-range integers
    def IntOpcodes(self):
        return self.opcodes32
    
    # print the sequence as a binary table
    def PrintBinary(self):
        for index, item in enumerate(self.opcodes32):
            logger.info("{0:032b}".format(item[0]), "{0:032b}".format(item[1]))
    
    # print the sequence as a hex table
    def PrintHex(self):
        for index, item in enumerate(self.opcodes32):
            logger.info("{0:08x}".format(item[0]), "{0:08x}".format(item[1]))
     
    # print the sequence as a decimal table
    def PrintDecimal(self):    
        for index, item in enumerate(self.opcodes32):
            logger.info("{0:010d}".format(item[0]), "{0:010d}".format(item[1]))


# example pulse sequence, one RF pulse and then acquire samples
# parameters may be passed in a dict.  Dict order does not matter but
# parameter names must match
#
#   pdict = {'pulse_us': 20.0, 'acquire_s': 1.0, 'recover_s': 3.0,
#                'rx1_us': 20.0, 'rx2_us': 20.0}
#   mySequence = PulseAcquire(**pdict)
#
class PulseAcquire(PulseSequence):
    def __init__(self, pulse_us, acquire_s, recover_s, rx1_us, rx2_us):
        super().__init__()
        
        # make these methods local to reduce typing
        FirstOpcode = self._FirstOpcode
        NextOpcode = self._NextOpcode
        Field = self._Field
        EndSequence = self._EndSequence
        Mark = self._Mark
        
        # convert time parameters to integer clock cycles as required by the sequencer
        self.pulse = round(pulse_us*us)
        self.acquire = round(acquire_s*s)
        self.recover = round(recover_s*s)
        self.rx1 = round(rx1_us*us)
        self.rx2 = round(rx2_us*us)
        
        # start defining pulse sequence
        # must set all 11 fields of the first opcode
        FirstOpcode()                        # initialize sequence
        Field('delay',    self.short_delay)  # delay times are in clock cycles
        Field('seqFlag',  0)
        Field('seqHalt',  0)
        Field('seqOut',   0b0001)            # Tx mode
        Field('memAcq',   0)
        Field('memZero',  1)                 # assert resets
        Field('CICreset', 1)
        Field('RFreset',  1)
        Field('RFphase',  0)
        Field('RFatten',  0)
        Field('RFfreq',   0)
        
        # after first opcode, only set fields that change
        NextOpcode()                         # copy and append the previous opcode
        Field('delay',    self.short_delay)
        Field('memZero',  0)                 # release resets
        Field('CICreset', 0)
        Field('RFreset',  0)

        # RF pulse
        NextOpcode()
        Field('delay',    self.pulse)
        Field('RFatten',  255)
        
        # receiver recovery delay, still in Tx mode
        NextOpcode()
        Field('delay',    self.rx1)
        Field('RFatten',  0)
        
        # receiver recovery delay, switch to Rx mode
        NextOpcode()
        Field('delay',    self.rx2)
        Field('seqOut',   0b0010)            # Rx mode
        
        # acquire samples
        NextOpcode()
        Field('delay',    self.acquire)
        Field('memAcq',   1)
        
        # T1 recovery time
        NextOpcode()
        Mark('data ready')                  # set a time mark
        Field('delay',    self.recover)
        Field('memAcq',   0)
        Field('seqOut',   0b0001)           # Tx mode
        
        # halt sequencer
        NextOpcode()
        Field('delay',    self.short_delay)
        Field('seqHalt',  1)
        
        # required, converts sequence as dict to seq as nested list of ints
        # also checks for required fields and valid field values
        EndSequence()


class NScanPulseAcquire(PulseSequence):
    def __init__(self, nscans, pulse_us, pulse_amp, acquire_s, recover_s,
                rx1_us, rx2_us, page):
        super().__init__()
        
        # make these methods local to reduce typing
        FirstOpcode = self._FirstOpcode
        NextOpcode = self._NextOpcode
        Field = self._Field
        EndSequence = self._EndSequence
        Mark = self._Mark        
        
        # convert time parameters to integer clock cycles as required by the sequencer
        # convert pulse amplitude in range 0->1 to 8-bit value
        self.nscans = nscans
        self.pulse = round(pulse_us*us)
        self.pulse_amp = round(255*pulse_amp)
        self.acquire = round(acquire_s*s)
        self.recover = round(recover_s*s)
        self.rx1 = round(rx1_us*us)
        self.rx2 = round(rx2_us*us)
        self.page = page
        
        # start defining pulse sequence
        # must set all 11 fields of the first opcode
        FirstOpcode()                        # initialize sequence
        Field('delay',    self.short_delay)  # delay times are in clock cycles
        Field('seqFlag',  0)
        Field('seqHalt',  0)
        Field('seqOut',   0b0001)            # Tx mode
        Field('memAcq',   0)
        Field('memZero',  1)                 # assert resets
        Field('CICreset', 1)
        Field('RFreset',  1)
        Field('RFphase',  0)
        Field('RFatten',  0)
        Field('RFfreq',   0)                 # use frequency register 0

        for ii in range(self.nscans):

            NextOpcode()
            Field('delay',    self.short_delay)
            Field('CICreset', 1)             # assert these resets every scan
            Field('RFreset',  1)
            if not self.page:
                Field('memZero',  1)         # only if not in page mode
            
            NextOpcode()
            Field('delay',    self.short_delay)
            Field('memZero',  0)                 # release resets
            Field('CICreset', 0)
            Field('RFreset',  0)

            # RF pulse
            NextOpcode()
            Field('delay',    self.pulse)
            Field('RFatten',  self.pulse_amp)

            # receiver recovery delay, still in Tx mode
            NextOpcode()
            Field('delay',    self.rx1)
            Field('RFatten',  0)
        
            # receiver recovery delay, switch to Rx mode
            NextOpcode()
            Field('delay',    self.rx2)
            Field('seqOut',   0b0010)            # Rx mode

            # acquire samples
            NextOpcode()
            Field('delay',    self.acquire)
            Field('memAcq',   1)

            # T1 recovery time
            NextOpcode()
            Mark('data ready')            # set a time mark
            if ii < self.nscans-1:
                Field('delay', self.recover)
            else:
                Field('delay', self.short_delay)
            Field('memAcq',   0)          # end acquisition
            Field('seqOut',   0b0001)     # back to Tx mode

        # halt sequencer
        NextOpcode()
        Field('delay',    self.short_delay)
        Field('seqHalt',  1)
        
        # required, converts sequence as dict to seq as nested list of ints
        # also checks for required fields and valid field values
        EndSequence()


# demonstration of RF oscillator modulation
class NScanPulseAcquireMod(PulseSequence):
    def __init__(self, nscans, pulse_us, acquire_s, recover_s, rx1_us, rx2_us):
        super().__init__()
            
        # make these methods local to reduce typing
        FirstOpcode = self._FirstOpcode
        NextOpcode = self._NextOpcode
        Field = self._Field
        EndSequence = self._EndSequence
        Mark = self._Mark        
        
        # convert time parameters to integer clock cycles as required by the sequencer
        # use constants from base class. convert phase angles in degrees using self.deg
        self.nscans = nscans
        self.pulse = round(pulse_us*us)
        self.acquire = round(acquire_s*s)
        self.recover = round(recover_s*s)
        self.rx1 = round(rx1_us*us)
        self.rx2 = round(rx2_us*us)

        # modulation table  mod[m,n], 
        # m = 0->9 is the step index
        # mod[:,0] specifies frequency register 0,1,2,3
        # mod[:,1] specifies phase 0 -> 360 degrees  (quantized by 256)
        mod = [
              [0,0],
              [0,22.5],
              [0,45], 
              [0,67.5],
              [0,90],
              [0,0],
              [1,0],
              [2,0],
              [3,0],
              [0,0]]
    
        # start defining pulse sequence
        # must set all 11 fields of the first opcode
        FirstOpcode()                        # initialize sequence
        Field('delay',    self.short_delay)  # delay times are in clock cycles
        Field('seqFlag',  0)
        Field('seqHalt',  0)
        Field('seqOut',   0b0001)            # Tx mode
        Field('memAcq',   0)
        Field('memZero',  1)                 # assert resets
        Field('CICreset', 1)
        Field('RFreset',  1)
        Field('RFphase',  0)
        Field('RFatten',  0)
        Field('RFfreq',   0 )

        for ii in range(self.nscans):

            NextOpcode()
            Field('delay',    self.short_delay)
            Field('CICreset', 1)             # assert these resets every scan
            Field('RFreset',  1)
            Field('memZero',  0)             # for page mode
            
            NextOpcode()
            Field('delay',    self.short_delay)
            Field('memZero',  0)                 # release resets
            Field('CICreset', 0)
            Field('RFreset',  0)

            # RF pulse
            NextOpcode()
            Field('delay',    self.pulse)
            Field('RFatten',  255)

            # receiver recovery delay, still in Tx mode
            NextOpcode()
            Field('delay',    self.rx1)
            Field('RFatten',  0)
        
            # receiver recovery delay, switch to Rx mode
            NextOpcode()
            Field('delay',    self.rx2)
            Field('seqOut',   0b0010)            # Rx mode
            
            # acquire with phase and frequency modulation
            for jj in range(len(mod)):
                NextOpcode()
                Field('delay',    round(self.acquire/len(mod)))
                Field('memAcq',   1)
                Field('RFfreq',   mod[jj][0])
                Field('RFphase',  round(mod[jj][1]*deg))
                
            # T1 recovery time
            NextOpcode()
            Field('delay',    self.recover)
            Field('memAcq',   0)
            Field('seqOut',   0b0001)           # Tx mode

        # halt sequencer
        NextOpcode()
        Field('delay',    self.short_delay)
        Field('seqHalt',  1)
        
        # required, converts sequence as dict to seq as nested list of ints
        # also checks for required fields and valid field values
        EndSequence()
