# -*- coding: utf-8 -*-
"""
Pulse Acquire run
"""
import time
import math
import numpy as np
import json
import os
import glob
from pathlib import Path
import logging

from PySide6.QtCore import Qt, QSize, QTimer, QObject, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QLabel,
    QSpinBox,
    QAbstractSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QLineEdit,
    QSlider,
    QVBoxLayout,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QMessageBox)

from qmcontrol.utilities import simulated_pulse_acquire_run, initialize_hardware, InterfaceError
import qmcontrol.pulse_sequences as ps
import qmcontrol.shim_system as ss
import qmcontrol.ext485 as ex4
import qmcontrol.jcamp_write as jw
import qmcontrol.noindent_json as nj
from qmcontrol.align import align 
from qmcontrol.interface_constants import seqclk_MHz, s, settings_file, shims_dir, programdata_root, cSeqTableMaxEntries

logger = logging.getLogger(__name__)

__author__ = "John Price"
__copyright__ = "Copyright 2021, Q Magnetics, LLC"
__credits__ = ["John Price"]
__license__ = "undecided"
__version__ = "0.0.1"
__maintainer__ = "John Price"
__email__ = "john@qmagnetics.com"
__status__ = "development"

class PulseAcquire():

    def __init__(self, MainWindow):
    
        #print('PulseAcquire class __init__')
        self.mw = MainWindow
    
    
    def setup_UI(self):

        # remove all widgets from both code-widget frames
        self.clear_layout(self.mw.codeWidgetsLayout1)
        self.clear_layout(self.mw.codeWidgetsLayout2)
        self.mw.codeWidgetsFrame1.setVisible(True)  # only using Frame1
        self.mw.codeWidgetsFrame2.setVisible(False)
        
        # add widgets and spacers
        self.mw.dataFileLineEdit = QLineEdit(self.mw.codeWidgetsFrame1)
        self.mw.dataFileLineEdit.setMinimumSize(QSize(100, 0))
        self.mw.dataFileLineEdit.setMaximumSize(QSize(70, 16777215))
        self.mw.codeWidgetsLayout1.addWidget(self.mw.dataFileLineEdit)
        
        self.mw.dataFileLabel = QLabel(self.mw.codeWidgetsFrame1)
        self.mw.dataFileLabel.setText(u"Data File")
        self.mw.codeWidgetsLayout1.addWidget(self.mw.dataFileLabel)
        
        self.mw.hSpacer1 = QSpacerItem(8, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.mw.codeWidgetsLayout1.addItem(self.mw.hSpacer1)
 
        self.mw.scansSpinBox = QSpinBox(self.mw.codeWidgetsFrame1)
        self.mw.scansSpinBox.setMinimum(1)
        self.mw.scansSpinBox.setMaximum(9999)
        self.mw.scansSpinBox.setSingleStep(1)
        self.mw.scansSpinBox.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)
        self.mw.scansSpinBox.setValue(1)
        self.mw.scansSpinBox.setDisplayIntegerBase(10)
        self.mw.codeWidgetsLayout1.addWidget(self.mw.scansSpinBox)
        
        self.mw.scansLabel = QLabel(self.mw.codeWidgetsFrame1)
        self.mw.scansLabel.setText(u"Scans")
        self.mw.codeWidgetsLayout1.addWidget(self.mw.scansLabel)
        
        self.mw.hSpacer2 = QSpacerItem(8, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.mw.codeWidgetsLayout1.addItem(self.mw.hSpacer2)
        
        self.mw.acquireTimeSpinBox = QDoubleSpinBox(self.mw.codeWidgetsFrame1)
        self.mw.acquireTimeSpinBox.setValue(1.000000)
        self.mw.codeWidgetsLayout1.addWidget(self.mw.acquireTimeSpinBox)

        self.mw.acquireTimeLabel = QLabel(self.mw.codeWidgetsFrame1)
        self.mw.acquireTimeLabel.setText(u"Acquire (s)")
        self.mw.codeWidgetsLayout1.addWidget(self.mw.acquireTimeLabel)
        
        self.mw.hSpacer3 = QSpacerItem(8, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.mw.codeWidgetsLayout1.addItem(self.mw.hSpacer3)
        
        self.mw.recoveryTimeSpinBox = QDoubleSpinBox(self.mw.codeWidgetsFrame1)
        self.mw.recoveryTimeSpinBox.setValue(1.000000)
        self.mw.codeWidgetsLayout1.addWidget(self.mw.recoveryTimeSpinBox)

        self.mw.recoveryTimeLabel = QLabel(self.mw.codeWidgetsFrame1)
        self.mw.recoveryTimeLabel.setText(u"Recovery (s)")
        self.mw.codeWidgetsLayout1.addWidget(self.mw.recoveryTimeLabel)
        
        self.mw.hSpacerExpand = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.mw.codeWidgetsLayout1.addItem(self.mw.hSpacerExpand)
        
        # connect signals
        self.mw.p.child('Pulse Acquire Run','Files','data filename'
                        ).sigValueChanged.connect(self.data_filename_param_changed)
        self.mw.p.child('Pulse Acquire Run','Sequencer','scans'
                        ).sigValueChanged.connect(self.scans_param_changed)
        self.mw.p.child('Pulse Acquire Run','Sequencer','acquire time'
                        ).sigValueChanged.connect(self.acquiretime_param_changed)
        self.mw.p.child('Pulse Acquire Run','Sequencer','recovery time'
                        ).sigValueChanged.connect(self.recoverytime_param_changed)        
        self.mw.dataFileLineEdit.textChanged.connect(self.dataFileLineEdit_changed)
        self.mw.scansSpinBox.valueChanged.connect(self.scansSpinBox_changed)
        self.mw.acquireTimeSpinBox.valueChanged.connect(self.acquireTimeSpinBox_changed)
        self.mw.recoveryTimeSpinBox.valueChanged.connect(self.recoveryTimeSpinBox_changed)
        
        # initialize UI from settings
        logger.info('Pulse Acquire run selected')
        self.mw.runMessageLabel.setText("Pulse Acquire run selected")
        self.mw.dataFileLineEdit.setText(
            self.mw.p.child('Pulse Acquire Run','Files','data filename').value())
        self.mw.scansSpinBox.setValue(
            self.mw.p.child('Pulse Acquire Run','Sequencer','scans').value())
        self.mw.acquireTimeSpinBox.setValue(
            self.mw.p.child('Pulse Acquire Run','Sequencer','acquire time').value())
        self.mw.recoveryTimeSpinBox.setValue(
            self.mw.p.child('Pulse Acquire Run','Sequencer','recovery time').value())
        
        
    def start_run(self, file_name, save_directory, shim_file):
        """Modified Input: save_name, save_directory"""
        # update start button and messages
        self.mw.runTabStartButton.setText('Stop')
        self.mw.runTabStartButton.repaint()
        logger.info("-> Start run...")
        self.mw.runMessageLabel.setText('Start run')
        
        # capture all run settings at start of run
        self.gpars = self.mw.param_dict(['Global'])
        self.mpars = self.mw.param_dict(['Global','Magnet'])
        self.vpars = self.mw.param_dict(['Global','Service'])
        self.fpars = self.mw.param_dict(['Pulse Acquire Run','Files'])
        self.spars = self.mw.param_dict(['Pulse Acquire Run','Sequencer'])
        self.ppars = self.mw.param_dict(['Pulse Acquire Run','Processing'])

        #Manually adjust parameters here
        self.fpars['data directory'] = save_directory
        
        self.fpars['data filename'] = file_name
        
        try:
            if not Path(self.fpars['data directory']).exists():
                Path(self.fpars['data directory']).mkdir(mode=777, parents=True, exist_ok=True)
        except Exception as e:
            logger.exception("Problem configuring data directory")
            #TODO: just threw a self. here so that the box doesn't disapper immediatly, need to refactor
            self.msgBox = QMessageBox()
            self.msgBox.setIcon(QMessageBox.Critical)
            self.msgBox.setWindowTitle("Data Directory issue")
            self.msgBox.setText("There was a problem configuring the data directory")
            self.msgBox.setInformativeText(str(e))
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            
        #### if will save data, check if file already exists, glob.glob() expands wildcard 
        self.file_suffix_str = '_'+str(self.fpars['file suffix']).zfill(4)        
        if (self.fpars['save indiv. fids'] or self.fpars['save average fid']) and not(self.gpars['test scan']):
            file_suffix_str = '_'+str(self.fpars['file suffix']).zfill(4)
            if self.fpars['append suffix']:
                if glob.glob(self.fpars['data directory']+'/'+self.fpars['data filename']+self.file_suffix_str+'*'):
                    message = "The directory [%s] already contains files with the name [%s]"%(self.fpars['data directory'],self.fpars['data filename']+self.file_suffix_str+'*')
                    QMessageBox.warning(None, "Files already present", message)
                    logger.warning(message)
                    self.cleanup()
                    return
            else: 
                if glob.glob(self.fpars['data directory']+'/'+self.fpars['data filename']+'*'):
                    message = "The directory [%s] already contains files with the name [%s]"%(self.fpars['data directory'],self.fpars['data filename']+'*')
                    QMessageBox.warning(None, "Files already present", message)
                    logger.warning(message)
                    self.cleanup()
                    return
                
        #### must align and average if want to save average fid
        if (self.fpars['save average fid'] == True) and (self.ppars['align and average'] == False):
            message = "Must average and align to save average spectrum"
            QMessageBox.warning(None, "", message)
            logger.warning(message)
            self.cleanup()
            return
            
        # handle simulated run and no hardware
        if self.vpars['simulate']:
            simulated_pulse_acquire_run(self.mw)  # needs revisions
            self.cleanup()
            return
        if not self.mw.si.configured:
            QMessageBox.warning(None,"Spectrometer Error","No spectrometer present on USB" )
            logger.info(f"No spectrometer present on USB")
            self.mw.runMessageLabel.setText('No spectrometer present on USB')
            self.cleanup()
            return
        
        # load shims to hardware
        logger.info('Load shims...')
        
        with open(shim_file,'r') as jfile:
            shims = json.load(jfile)
        success,_ , satflags,_ ,_ = ss.set_shims(self.mw.si, shims)
        if np.sum(np.abs(satflags)) > 0:
            logger.info(f'saturated shim DACs: {satflags}')
        if not success:
            logger.warning('Invalid shims, may exceed total current limit')       
        
        time.sleep(0.10)           # make sure shim currents have time to settle  
          
        #### initialize hardware and update settings to be consistent with hardware constraints
        filter_atten, decimation, self.exact_spec_width_kHz = \
            initialize_hardware(self.mw.si, self.spars, self.gpars, verbose=self.vpars['verbose'])
        self.mw.p.child('Pulse Acquire Run','Sequencer','filter atten').setValue(filter_atten)
        self.mw.p.child('Pulse Acquire Run','Sequencer','decimation').setValue(decimation)

        #### generate, load, and verify pulse sequence
        # loading sequence also asserts sequencer reset and clears sequencer flags
        self.nscans = self.spars['scans'] + self.spars['equilib. scans']  # total number of scans
        if self.gpars['test scan']: self.nscans = 1
        self.seq = ps.NScanPulseAcquire(self.nscans, self.spars['pulse time'], self.spars['pulse amplitude'],
              self.spars['acquire time'], self.spars['recovery time'], self.spars['Rx delay 1'], 
              self.spars['Rx delay 2'], self.spars['page mode'])
        
        nops = self.seq.Len()
        logger.info(f'Compiled pulse sequence contains {nops} opcodes')
        if nops <= cSeqTableMaxEntries:
            logger.info(f'Load pulse sequence...')
            self.mw.si.LoadPulseSequenceFast(self.seq.IntOpcodes())   # load to hardware
        else: 
            logger.warning(f'Pulse sequence contains more than {cSeqTableMaxEntries} opcodes')
            QMessageBox.warning(None, f"Pulse Sequence Error", 
                        "Reduce number of scans")
            self.cleanup()
            return
        
        #int_opcodes = self.mw.si.ReadPulseSequence(self.seq.Len())
        #agree = (int_opcodes == self.seq.IntOpcodes())            # verify
        #if not(agree): raise InterfaceError('sequence read or write failed')

        #### generate processing control table
        # a list of dicts, one dict for each time mark
        self.ctab = [{} for i in range(len(self.seq.marks))]
        for ii in range(len(self.seq.marks)):
            dscan = ii - self.spars['equilib. scans']          # dscan = data scans index
            
            if self.fpars["save indiv. fids"] and dscan>=0:    # save current fid
                self.ctab[ii]["save_current"] = True
            else:
                self.ctab[ii]["save_current"] = False
                
            if self.ppars["track Tx freq"] or self.ppars["align and average"]: # align to previous fid or average fid
                self.ctab[ii]["align"] = True                        # if available
            else:
                self.ctab[ii]["align"] = False
                
            if self.ppars["align and average"] and dscan>=0:         # current fid is part of an average fid
                self.ctab[ii]["average"] = True
            else:
                self.ctab[ii]["average"] = False 
            
            if self.ppars["track Tx freq"]:               # use current fid for Tx tracking
                self.ctab[ii]["track"] = True
            else:
                self.ctab[ii]["track"] = False
            
            if self.gpars['test scan']:
                self.ctab[ii]["message"] = "Test scan"
            elif dscan<0:
                self.ctab[ii]["message"] = f"Equilibration scan {ii+1}"
            else:
                self.ctab[ii]["message"] = f"Acquisition scan {dscan+1}"

        #### Initialize storage for processing
        self.fids = []                    # list of individual fids
        self.fid_previous = np.array([])  # previous fid
        self.fid_ave = np.array([])       # running average fid
        self.tracking_tx_freq = self.gpars['Tx freq']  # starting tx frequency for tracking
        self.scan = 0                     # scan counter, counts calls to process_scans()

        #### Start sequencer, start QTimer to schedule calls to process_scans()
        self.scan_timer = QTimer()
        self.scan_timer.setTimerType(Qt.PreciseTimer)
        self.scan_timer.setSingleShot(True)
        self.scan_timer.timeout.connect(self.process_scans) # callback for timeout event
        logger.info("Start sequencer...")
        marktime = self.seq.GetMarkTime(self.scan)     # first time mark
        self.mw.si.ReleaseSeqReset()                   # start sequencer
        self.scan_timer.start(1000*marktime+10)        # first timer interval
    
    
    def process_scans(self):
       
        marktime = self.seq.GetMarkTime(self.scan)     # get time mark for this scan
        seq_time = self.mw.si.GetSeqTime()             # read current sequencer time
        lag_time = seq_time - marktime                 # want this to be positive
        if lag_time < 0:
            time.sleep(-lag_time)                  # wait a bit longer if necessary
        self.scan_timer.stop()                     # stop the timer

        # find most recent samples written to memory and transfer FID
        start_address = self.mw.si.GetMemAddrAcqStart()
        end_address = self.mw.si.GetMemAddrAcqEnd()
        nsamples = math.floor((end_address-start_address)/4)
        tic = time.perf_counter() 
        fid, blocks_transfer, bytes_transfer, bytes_received = \
               self.mw.si.GetSamples(nsamples, start_address)
        fid_current = fid[0,:] + 1j*fid[1,:]
        toc = time.perf_counter()
        transfer_time = toc - tic
        
        logger.info("-> " + self.ctab[self.scan]["message"])
        self.mw.runMessageLabel.setText(self.ctab[self.scan]["message"])
        
        if self.vpars['verbose']:
            logger.info(f'Processing lag time = {lag_time:0.3f}s')
            logger.info(f'Acquistion start address = {start_address}, end = {end_address-1}')
            logger.info(f'Acquired {end_address-start_address} bytes, {nsamples} full samples' )
            logger.info(f'Transfered {blocks_transfer} blocks, {bytes_transfer} bytes')
            logger.info(f'Received {bytes_received} bytes')
            logger.info(f"Transfer time = {transfer_time:0.4f} s")
            
        # saved fids are not apodized but will be affected by Tx tracking  
        if self.ctab[self.scan]["save_current"]:
            self.fids.append(fid_current)
        
        # make time_series and optionally apodize current fid
        time_series = np.arange(len(fid_current))/(self.exact_spec_width_kHz*1000)
        if self.ppars['apodize']:
            exp_tau = 1/(np.pi*self.ppars['broadening'])
            fid_current = fid_current*np.exp(-time_series/exp_tau)
        
        # align fid
        if self.ctab[self.scan]["align"]:
            if len(self.fid_ave>0):
                df, fid_aligned = align(self.fid_ave, fid_current, 
                                                    self.exact_spec_width_kHz)
            elif len(self.fid_previous>0):
                df, fid_aligned = align(self.fid_previous, fid_current, 
                                                    self.exact_spec_width_kHz)
            else:
                df = 0
                fid_aligned = fid_current
            logger.info(f'Lag {lag_time:0.3f}s, df = {-df:0.3f} Hz')  # frequency drift of fid
            
        # average fid
        if self.ctab[self.scan]["average"]:
            if len(self.fid_ave>0):
                dscan = self.scan - self.spars['equilib. scans']   # data scans index
                self.fid_ave = (self.fid_ave*dscan + fid_aligned)/(dscan+1)
            else:
                self.fid_ave = fid_aligned
       
        # track Tx frequency
        if self.ctab[self.scan]["track"]:
            self.tracking_tx_freq = self.tracking_tx_freq - df*1E-6
            self.mw.si.SetRefNCOFreq0(self.tracking_tx_freq)
            logger.info(f'Updated Tx frequency = {self.tracking_tx_freq:0.9f} Hz')
        
        self.fid_previous = fid_current    # save fid for next scan

        # plot to run tab UI
        self.mw.times = time_series
        self.mw.fid = fid_current if len(self.fid_ave) == 0 else self.fid_ave
        self.mw.plot_fid()
        
        self.mw.spect = np.fft.fft(self.mw.fid, self.ppars['zero pad'])/nsamples
        self.mw.spect = np.fft.fftshift(self.mw.spect)
        self.mw.freqs = np.fft.fftfreq(self.ppars['zero pad'], 1/(self.exact_spec_width_kHz*1000))
        self.mw.freqs = np.fft.fftshift(self.mw.freqs)  
        xa=False; ya=False
        if self.mw.plots_blank:
            xa=True; ya=True
            self.mw.plots_blank = False
        self.mw.plot_spectrum(xauto=xa, yauto=ya)
        self.mw.runTabCanvas.draw()

        # SNR calculations
        # noise window must not include any signals
        # rms is computed around a linear fit to the phased real part of the spectrum within the noise window
        # peak is the highest point of the phased real part of the full spectrum
        # see notes v.9 p.42 for rms formula
        # SNR is peak divided by twice the rms
        if self.ppars['SNR']:
            run_name = self.mw.current_run_name()     
            fL, phi0, phi1, pivot, offset, plot_Hz, plot_mag = self.mw.get_plotting_params(run_name)
            spect = np.real(self.mw.spect*np.exp(-1j*2*np.pi*phi0/360)\
                *np.exp(-1j*2*np.pi*(self.mw.freqs - pivot)*phi1/360)) 
            peak = np.max(spect)
            maxf = self.ppars['noise window max']
            minf = self.ppars['noise window min']
            valid_window =  -self.exact_spec_width_kHz*1000/2 < maxf < self.exact_spec_width_kHz*1000/2 \
                     and -self.exact_spec_width_kHz*1000/2 < minf < self.exact_spec_width_kHz*1000/2 \
                     and maxf > minf
            if valid_window:
                df = self.exact_spec_width_kHz*1000/self.ppars['zero pad']
                window_index_max = round(self.ppars['zero pad']/2 + maxf/df)
                window_index_min = round(self.ppars['zero pad']/2 + minf/df)
                spect_win = spect[window_index_min:window_index_max]
                freqs_win = self.mw.freqs[window_index_min:window_index_max]
                N = len(spect_win)
                Sx = np.sum(freqs_win)
                Sy = np.sum(spect_win)
                Sxy = np.sum(freqs_win*spect_win)
                Sx2 = np.sum(freqs_win**2)
                a = (Sxy - Sx*Sy/N)/(Sx2-Sx**2/N)
                b = Sy/N - a*Sx/N
                rms = (np.sum((spect_win-a*freqs_win-b)**2)/N)**0.5
                SNR = peak/(2*rms)
                #fit_max = a*maxf+b
                #fit_min = a*minf+b
                #logger.info(f'window index max: {window_index_max}, window index min: {window_index_min}')
                #logger.info(f'N: {N}, min freq: {freqs_win[0]}, max freq: {freqs_win[N-1]}')
                #logger.info(f'a: {a}, b: {b}, fit(maxf): {fit_max}, fit(minf): {fit_min}')
                logger.info(f'peak: {peak:0.2f}, rms: {rms:0.4f}, SNR: {SNR:0.2f}')
            else:
                logger.info(f'peak: {peak:0.2f}, noise window not valid')
            
            
        # schedule processing for next scan
        # after last scan, call finish_run()
        self.scan += 1
        if self.scan < self.nscans and not self.gpars['test scan']:
            marktime = self.seq.GetMarkTime(self.scan)
            seqtime = self.mw.si.GetSeqTime()
            self.scan_timer.start(1000*(marktime-seqtime)+10)
        else:
            self.finish_run()


    # called after last call to process_scans()
    # also called when stop button pressed while showing text 'Stop', to interrupt a run 
    def finish_run(self):

        self.mw.runTabStartButton.blockSignals(True)
        self.mw.runTabStartButton.setText('Stopping...')
        self.mw.runTabStartButton.repaint()

        self.scan_timer.stop()         # stop timer to stop calls to process_scans()
        self.mw.si.AssertSeqReset()    # stop and reset the sequencer
        
        anything_saved = False
        
        if self.fpars['append suffix']:
            file_suffix_str = self.file_suffix_str
        else:
            file_suffix_str = ""
        
        # write average fid to .jdx file
        # ##.OBSERVE FREQUENCY = starting value of Tx freq even if tracking
        if self.fpars['save average fid'] and len(self.fid_ave)>0 and not(self.gpars['test scan']):
            anything_saved = True
            fn = self.fpars['data directory']+chr(92)+self.fpars['data filename']+ '_ave'
            logger.info(f'Saving average FID to file {fn}...')
            fid_ave_parts = np.array([self.fid_ave.real,self.fid_ave.imag])
            jw.jcamp_npa_write(fid_ave_parts, self.fpars, self.spars, self.ppars, 
                               self.gpars, self.mpars, self.vpars, file_suffix_str+'_ave')
             
        # write individual fids to .jdx files
        # ##.OBSERVE FREQUENCY = starting value of tx_freq_MHz even if tracking
        if self.fpars['save indiv. fids'] and len(self.fids) > 0 and not(self.gpars['test scan']):
            anything_saved = True
            fn = self.fpars['data directory']+chr(92)+self.fpars['data filename']+ '_nnn'
            logger.info(f'Saving individual FIDs to files {fn}...')
            for ii in range(len(self.fids)):
                fid_parts = np.array([self.fids[ii].real,self.fids[ii].imag])
                jw.jcamp_npa_write(fid_parts, self.fpars, self.spars, self.ppars,
                                   self.gpars, self.mpars, self.vpars, file_suffix_str+'_'+str(ii+1).zfill(3))
        
        # increment suffix
        if anything_saved and self.fpars['append suffix']:
            old_suffix = self.mw.p.child('Pulse Acquire Run','Files', 'file suffix').value()
            self.mw.p.child('Pulse Acquire Run','Files', 'file suffix').setValue(str(old_suffix+1).zfill(4))
            logger.info(f'Increment file suffix')
        
        # update global Tx frequency
        self.mw.p.child('Global','Tx freq').setValue(self.tracking_tx_freq)
        
        # report
        previous_msg = self.mw.runMessageLabel.text()
        if self.scan == self.nscans or self.gpars['test scan']:
            self.mw.runMessageLabel.setText(previous_msg + ', Run complete')
            logger.info(f'Run complete')
        else:
            self.mw.runMessageLabel.setText(previous_msg + ', Run interrupted') 
            logger.warning(f'Run interrupted')
       
        self.cleanup()
        
        self.mw.runTabStartButton.blockSignals(False)

    
    ##############
    # slots for UI
    def dataFileLineEdit_changed(self,value):
        self.mw.p.child('Pulse Acquire Run','Files','data filename').setValue(value)
    
    def data_filename_param_changed(self):
        self.mw.dataFileLineEdit.setText(self.mw.p.child('Pulse Acquire Run','Files','data filename').value())

    def scansSpinBox_changed(self,value):
        self.mw.p.child('Pulse Acquire Run','Sequencer','scans').setValue(value)
    
    def scans_param_changed(self):
        self.mw.scansSpinBox.setValue(self.mw.p.child('Pulse Acquire Run','Sequencer','scans').value())
    
    def acquireTimeSpinBox_changed(self,value):
        self.mw.p.child('Pulse Acquire Run','Sequencer','acquire time').setValue(value)
        
    def acquiretime_param_changed(self):
        self.mw.acquireTimeSpinBox.setValue(self.mw.p.child('Pulse Acquire Run','Sequencer','acquire time').value())
    
    def recoveryTimeSpinBox_changed(self,value):
        self.mw.p.child('Pulse Acquire Run','Sequencer','recovery time').setValue(value)
        
    def recoverytime_param_changed(self):
        self.mw.recoveryTimeSpinBox.setValue(self.mw.p.child('Pulse Acquire Run','Sequencer','recovery time').value())
    
    
    #################################
    # utility functions and constants
    
    # things to do when the run ends regularly or when interrupted
    def cleanup(self):
        TRIGGER_PATH = r"..\..\scan_trigger.txt"
        self.mw.runTabStartButton.setText('Start')
        self.mw.runTabStartButton.repaint()
        trig_enable_checked = self.mw.p.child('Global','trigger enable').value()
        if trig_enable_checked:
            #ex4.clear_latches(self.mw.si,'01')                          # clear latched triggers
            os.remove(TRIGGER_PATH)
            self.mw.trigger_timer.start(self.mw.trigger_timer_period)   # restart timer
        self.mw.run_isrunning = False
    
    
    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            childWidget = child.widget()
            if childWidget:
                childWidget.setParent(None)
                childWidget.deleteLater()

    
    # all runs must define default_settings with at least these settings:
    # outermost dict with 'Run Name' name under key 'name'
    # ['Run Name','Sequencer','spectral width']
    # ['Run Name','Processing','phase phi 0']
    # ['Run Name','Processing','phase phi 1']
    # ['Run Name','Processing','phase pivot']
    # ['Run Name','Processing','ppm offset']
    # ['Run Name','Processing','plot mag']
    default_settings =  \
        {'name': 'Pulse Acquire Run', 'type': 'group', 'expanded': True, 'children': 
            [
            {'name': 'Files', 'type': 'group', 'expanded': False, 'children':
                [
                {'name': 'save average fid', 'type': 'bool', 'value': True},
                {'name': 'save indiv. fids', 'type': 'bool', 'value': False},
                {'name': 'data filename', 'type': 'str', 'value': 'tests'},
                {'name': 'file suffix', 'type': 'int', 'value': 0, 'limits': [0,9999]},
                {'name': 'append suffix', 'type': 'bool', 'value': False},
                {'name': 'data directory', 'type': 'directory', 'value': str((programdata_root / 'nmr_data').absolute())},
                {'name': 'sample', 'type': 'str', 'value': 'CHCl3'},
                {'name': 'solvent', 'type': 'str', 'value': 'neat'},
                {'name': 'notes', 'type': 'str', 'value': 'testing'},
                {'name': 'user name', 'type': 'str', 'value': 'John Price'},
                {'name': 'institution', 'type': 'str', 'value': 'Q Magnetics'},
                {'name': 'pulse sequence', 'type': 'str', 'value': 'NScanPulseAcquire','readonly': True},
                {'name': 'run type', 'type': 'str', 'value': 'pulse acquire','readonly': True}
                ]
            },
            {'name': 'Sequencer', 'type': 'group', 'expanded': False, 'children':
                [
                {'name': 'scans', 'type': 'int', 'value': 10, 'limits': [1,2000]},
                {'name': 'equilib. scans', 'type': 'int', 'value': 0, 'limits': [0,100]},
                {'name': 'acquire time', 'type': 'float', 'value': 4.0, 'decimals': 2, 'step': 0.1, 'limits': [0.01,100], 'siSuffix': True, 'suffix': 's'},
                {'name': 'recovery time', 'type': 'float', 'value': 4.0, 'decimals': 2, 'step': 0.1, 'limits': [0.01,1000], 'siSuffix': True, 'suffix': 's'},
                {'name': 'start delay', 'type': 'float', 'value': 5.0, 'decimals': 2, 'step': 0.1, 'limits': [0,1000], 'siSuffix': True, 'suffix': 's'},
                {'name': 'pulse amplitude', 'type': 'float', 'value': 0.42, 'decimals': 4, 'step': 0.01, 'limits': [0,1]},
                {'name': 'pulse time', 'type': 'float', 'value': 12.0, 'step': 1, 'limits': [0,10000], 'siSuffix': True, 'suffix': '\u03bcs'},
                {'name': 'spectral width', 'type': 'float', 'value': 10.0, 'step': 1.0, 'limits': [5,10000], 'siSuffix': True, 'suffix': 'kHz', 'decimals': 5},
                {'name': 'Rx delay 1', 'type': 'float', 'value': 50.0, 'step': 1, 'limits': [0,10000], 'siSuffix': True, 'suffix': '\u03bcs'},
                {'name': 'Rx delay 2', 'type': 'float', 'value': 250.0, 'step': 1, 'limits': [0,10000], 'siSuffix': True, 'suffix': '\u03bcs'},
                {'name': 'page mode', 'type': 'bool', 'value': True},
                {'name': 'auto atten', 'type': 'bool', 'value': True},
                {'name': 'filter atten', 'type': 'int', 'value': 27, 'limits': [4,31],'step': 1},
                {'name': 'auto decim', 'type': 'bool', 'value': True},
                {'name': 'decimation', 'type': 'int', 'value': 16000, 'limits': [2,32000],'step': 1}
                ]
            },
            {'name': 'Processing', 'type': 'group', 'expanded': False, 'children':
                [
                {'name': 'align and average', 'type': 'bool', 'value': True},
                {'name': 'track Tx freq', 'type': 'bool', 'value': False},
                {'name': 'phase phi 0', 'type': 'float', 'value': 0.0, 'step': 1.0, 'limits': [-180,180],'siSuffix': True, 'suffix': 'deg'},
                {'name': 'phase phi 1', 'type': 'float', 'value': 0.0, 'step': 0.1, 'siSuffix': True, 'suffix': 'deg/Hz'},
                {'name': 'phase pivot', 'type': 'float', 'value': 0.0, 'step': 1.0, 'siSuffix': True, 'suffix': 'Hz'},
                {'name': 'ppm offset', 'type': 'float', 'value': 0.0, 'step': 10, 'siSuffix': True, 'suffix': 'Hz', 'decimals': 5}, 
                {'name': 'plot mag', 'type': 'bool', 'value': False},
                {'name': 'apodize', 'type': 'bool', 'value': False},
                {'name': 'broadening', 'type': 'float', 'value': 1.0, 'step': 0.1,'siSuffix': True, 'suffix': 'Hz'},
                {'name': 'SNR', 'type': 'bool', 'value': False},
                {'name': 'noise window max', 'type': 'float', 'value': 1000.0, 'step': 0.1,'siSuffix': True, 'suffix': 'Hz', 'decimals': 5},
                {'name': 'noise window min', 'type': 'float', 'value': 500.0, 'step': 0.1,'siSuffix': True, 'suffix': 'Hz', 'decimals': 5},
                {'name': 'zero pad', 'type': 'int', 'value': 200000, 'step': 10000, 'limits': [0,1000000]},
                {'name': 'software filter', 'type': 'str', 'value': 'None'}
                ]
            }
            ]
        }
