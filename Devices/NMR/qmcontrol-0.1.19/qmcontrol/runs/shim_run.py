# -*- coding: utf-8 -*-
"""
Shim run
"""
import time
import math
import os
import numpy as np
import json
import logging

from PySide6.QtCore import Qt, QSize, QTimer, QObject, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QLabel,
    QSpinBox,
    QAbstractSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QComboBox,
    QLineEdit,
    QSlider,
    QVBoxLayout,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QMessageBox)

# import from modified version of scipy optimize.py 
# generator version of Nelder-Mead minimization
from qmcontrol.gen_optimize import _minimize_neldermead as gen_neldermead

import qmcontrol.noindent_json as nj
from qmcontrol.utilities import simulated_shim_run, initialize_hardware, InterfaceError
import qmcontrol.shim_system as ss
import qmcontrol.ext485 as ex4
import qmcontrol.pulse_sequences as ps
from qmcontrol.interface_constants import seqclk_MHz, s, settings_file, programdata_root, shims_dir, cSeqTableMaxEntries

logger = logging.getLogger(__name__)

__author__ = "John Price"
__copyright__ = "Copyright 2021, Q Magnetics, LLC"
__credits__ = ["John Price"]
__license__ = "undecided"
__version__ = "0.0.1"
__maintainer__ = "John Price"
__email__ = "john@qmagnetics.com"
__status__ = "development"

class Shim():
    def __init__(self,MainWindow):
        #print('Shim class __init__')
        self.mw = MainWindow
    
    def setup_UI(self):
        
        # remove all widgets from both code-widget frames
        self.clear_layout(self.mw.codeWidgetsLayout1)
        self.clear_layout(self.mw.codeWidgetsLayout2)
        self.mw.codeWidgetsFrame1.setVisible(True)  # only using Frame1
        self.mw.codeWidgetsFrame2.setVisible(False)
        
        # add widgets and spacers
        self.mw.newShimFileLineEdit = QLineEdit(self.mw.codeWidgetsFrame1)
        self.mw.newShimFileLineEdit.setMinimumSize(QSize(100, 0))
        self.mw.newShimFileLineEdit.setMaximumSize(QSize(70, 16777215))
        self.mw.codeWidgetsLayout1.addWidget(self.mw.newShimFileLineEdit)
        
        self.mw.newShimFileLabel = QLabel(self.mw.codeWidgetsFrame1)
        self.mw.newShimFileLabel.setText(u"New Shim File")
        self.mw.codeWidgetsLayout1.addWidget(self.mw.newShimFileLabel)
        
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
        
        self.mw.incsComboBox = QComboBox(self.mw.codeWidgetsFrame1)
        self.mw.codeWidgetsLayout1.addWidget(self.mw.incsComboBox)      
        for inc_name in self.inc_names:
            self.mw.incsComboBox.addItem(inc_name)        
        
        self.mw.incsLabel = QLabel(self.mw.codeWidgetsFrame1)
        self.mw.incsLabel.setText(u"Increments")
        self.mw.codeWidgetsLayout1.addWidget(self.mw.incsLabel)
        
        self.mw.hSpacer3 = QSpacerItem(8, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.mw.codeWidgetsLayout1.addItem(self.mw.hSpacer3)
        
        self.mw.acquireTimeSpinBox = QDoubleSpinBox(self.mw.codeWidgetsFrame1)
        self.mw.acquireTimeSpinBox.setValue(1.000000)
        self.mw.codeWidgetsLayout1.addWidget(self.mw.acquireTimeSpinBox)

        self.mw.acquireTimeLabel = QLabel(self.mw.codeWidgetsFrame1)
        self.mw.acquireTimeLabel.setText(u"Acquire (s)")
        self.mw.codeWidgetsLayout1.addWidget(self.mw.acquireTimeLabel)
        
        self.mw.hSpacer4 = QSpacerItem(8, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.mw.codeWidgetsLayout1.addItem(self.mw.hSpacer4)
        
        self.mw.recoveryTimeSpinBox = QDoubleSpinBox(self.mw.codeWidgetsFrame1)
        self.mw.recoveryTimeSpinBox.setValue(1.000000)
        self.mw.codeWidgetsLayout1.addWidget(self.mw.recoveryTimeSpinBox)

        self.mw.recoveryTimeLabel = QLabel(self.mw.codeWidgetsFrame1)
        self.mw.recoveryTimeLabel.setText(u"Recovery (s)")
        self.mw.codeWidgetsLayout1.addWidget(self.mw.recoveryTimeLabel)
        
        self.mw.hSpacerExpand = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.mw.codeWidgetsLayout1.addItem(self.mw.hSpacerExpand)
        
        # connect signals
        self.mw.p.child('Shim Run','Files','new shim file'
                        ).sigValueChanged.connect(self.shim_filename_param_changed)
        self.mw.p.child('Shim Run','Sequencer','scans'
                        ).sigValueChanged.connect(self.scans_param_changed)
        self.mw.p.child('Shim Run','Sequencer','acquire time'
                        ).sigValueChanged.connect(self.acquiretime_param_changed)
        self.mw.p.child('Shim Run','Sequencer','recovery time'
                        ).sigValueChanged.connect(self.recoverytime_param_changed)        
        self.mw.p.child('Shim Run','Sequencer','increments'
                        ).sigValueChanged.connect(self.shim_increments_param_changed)
        self.mw.newShimFileLineEdit.textChanged.connect(self.newShimFileLineEdit_changed)
        self.mw.scansSpinBox.valueChanged.connect(self.scansSpinBox_changed)
        self.mw.acquireTimeSpinBox.valueChanged.connect(self.acquireTimeSpinBox_changed)
        self.mw.recoveryTimeSpinBox.valueChanged.connect(self.recoveryTimeSpinBox_changed)
        self.mw.incsComboBox.activated.connect(self.incsComboBox_activated) 
        
        # initialize UI
        logger.info('Shim run selected')
        self.mw.runMessageLabel.setText("Shim run selected")
        self.mw.newShimFileLineEdit.setText(
            self.mw.p.child('Shim Run','Files','new shim file').value())
        self.mw.scansSpinBox.setValue(
            self.mw.p.child('Shim Run','Sequencer','scans').value())
        self.mw.acquireTimeSpinBox.setValue(
            self.mw.p.child('Shim Run','Sequencer','acquire time').value())
        self.mw.recoveryTimeSpinBox.setValue(
            self.mw.p.child('Shim Run','Sequencer','recovery time').value())
        item_text = self.mw.p.child('Shim Run','Sequencer','increments').value()
        index = self.inc_names.index(item_text)
        self.mw.incsComboBox.setCurrentIndex(index)
     
     
    def start_run(self,file_name, save_directory, shim_file):
    
        # update start button and messages
        self.mw.runTabStartButton.setText('Stop')
        self.mw.runTabStartButton.repaint()
        logger.info("-> Start run...")
        self.mw.runMessageLabel.setText('Start run')
        
        # capture all run settings at start of run
        self.gpars = self.mw.param_dict(['Global'])
        self.mpars = self.mw.param_dict(['Global','Magnet'])
        self.vpars = self.mw.param_dict(['Global','Service'])
        self.fpars = self.mw.param_dict(['Shim Run','Files'])
        self.spars = self.mw.param_dict(['Shim Run','Sequencer'])
        self.ppars = self.mw.param_dict(['Shim Run','Processing'])
       
        #Manually Adjusted Params
        self.fpars['data directory'] = save_directory
        
        self.fpars['data filename'] = file_name

        # handle simulated run and no hardware
        if self.vpars['simulate']:
            simulated_shim_run(self.mw)  # needs revisions
            self.cleanup()
            return
            
        if not self.mw.si.configured:
            logger.warning(f"No spectrometer present on USB")
            QMessageBox.warning(None,"Spectrometer Error","No spectrometer present on USB" )
            self.mw.runMessageLabel.setText('No spectrometer present on USB')
            self.cleanup()
            return

        # check for shim file overwrite
        # shim_file = 'shims/' + self.gpars['shim file'] + '.json'
        self.new_shim_file = save_directory +'/'+ file_name
        if self.fpars['save'] and not(self.gpars['test scan']):
            if os.path.exists(self.new_shim_file):
                message = "Shim file already exists: %s"%self.new_shim_file
                QMessageBox.warning(None, "File already present", message)
                logger.warning(message)
                self.cleanup()
                return
       
        # read starting shims from shim file
        # add self.spars['shim offset'] and load to hardware
        with open(shim_file,'r') as jfile:
            shims = json.load(jfile)
        shim_offset_str = self.spars['shim offsets']
        shim_offset_vec = ss.shim_str2vec(shim_offset_str)
        shims[1] = [shims[1][i] + shim_offset_vec[i] for i in range(len(shims[1]))]
        logger.info('Load starting shims...')
        success,_,satflags,shim_current,shim_power = ss.set_shims(self.mw.si, shims)     # takes 0.4-0.5s to return
        if self.vpars['verbose']:
            logger.info(f"Total shim coil current = {shim_current:0.4f} A")
            logger.info(f"Total shim coil power = {shim_power:0.4f} W")
        if np.sum(np.abs(satflags)) > 0:
            logger.info(f'saturated shim DACs: {satflags}')
        if not success:
            logger.warning('Invalid shims, may exceed total current limit')

        time.sleep(0.10)  # make sure shim currents have time to settle
        self.start_shims = shims
       
        #### initialize hardware and update settings to be consistent with hardware constraints
        filter_atten, decimation, self.exact_spec_width_kHz, = \
            initialize_hardware(self.mw.si, self.spars, self.gpars, verbose=self.vpars['verbose'])
        self.mw.p.child('Shim Run','Sequencer','filter atten').setValue(filter_atten)
        self.mw.p.child('Shim Run','Sequencer','decimation').setValue(decimation)

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
      
        #### construct increments vector, starting active shims, initial simplex
        inc_select_str = self.spars['increments']
        #TODO setup shim value for coarseness
        inc_select_str = 4 # 4 is coarse,1 is fine?
        shim_inc_multiplier = self.spars['inc multiplier']
        if shim_inc_multiplier == 0:            
             shim_inc_multiplier = 0.000001
        inc_def_str = self.mw.p.child('Shim Run','Sequencer','Increment Defs',inc_select_str).value()
        self.incs = ss.shim_str2vec(inc_def_str)
        self.incs = [shim_inc_multiplier*self.incs[i] for i in range(len(self.incs))]
        self.active_start_vec, init_simp = ss.make_simplex(self.start_shims, self.incs)

        #### create generator version of Nelder Mead
        # outside_f() returns cost function evals back to nelder mead through f_of_x
        # generator returns next x (next active shim vector)
        # options set so the generator will never terminate
        def outside_f(x):
            return self.f_of_x

        self.gen_NM = gen_neldermead(outside_f, self.active_start_vec, initial_simplex=init_simp,
                                xatol=1e-20, fatol=1e-20)
        self.active_shims_vec = next(self.gen_NM)  # first call returns active_start_vec, shims already loaded
        
        #### Initialize storage for processing
        self.collector = []         # collect results of each scan here
        self.f_of_x = 0             # return -peak to gen_neldermead()
        self.scan = 0               # scan counter, counts calls to process_scans()
        
        ##### Start sequencer, start QTimer to schedule calls to process_scans()
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

        # make time_series and optionally apodize current fid
        time_series = np.arange(len(fid_current))/(self.exact_spec_width_kHz*1000)
        if self.ppars['apodize']:
            exp_tau = 1/(np.pi*self.ppars['broadening'])
            fid_current = fid_current*np.exp(-time_series/exp_tau)
        
        # plot to UI
        self.mw.times = time_series
        self.mw.fid = fid_current
        self.mw.plot_fid()
        
        self.mw.spect = np.fft.fft(self.mw.fid, self.ppars['zero pad'])/nsamples
        self.mw.spect = np.fft.fftshift(self.mw.spect)
        self.mw.freqs = np.fft.fftfreq(self.ppars['zero pad'], 1/(self.exact_spec_width_kHz*1000))
        self.mw.freqs = np.fft.fftshift(self.mw.freqs)  
        if self.mw.plots_blank:
            xa=True; ya=True
        else: 
            xa=False; ya=False
        self.mw.plots_blank = False  
        self.mw.plot_spectrum(xauto=xa, yauto=ya)
        self.mw.runTabCanvas.draw()
        
        # get peak of magnitude of spectrum
        peak = np.max(np.abs(self.mw.spect))
        self.f_of_x = -peak

        # report
        if self.gpars['test scan']:
            logger.info("-> Test scan")
            logger.info("# lag: peak shims")
            self.mw.runMessageLabel.setText('Test scan')
        elif self.scan == 0 and self.spars['equilib. scans'] > 0:
            logger.info("-> Start equilibration scans")
            logger.info("# lag: peak shims")
            self.mw.runMessageLabel.setText(f'Equilibration scan 1')
        elif 0 < self.scan < self.spars['equilib. scans']:
            self.mw.runMessageLabel.setText(f'Equilibration scan {self.scan+1}')
        elif self.scan == self.spars['equilib. scans'] and self.spars['scans'] > 0:
            logger.info("-> Start optimization scans")
            logger.info("# lag: peak shims")
            self.mw.runMessageLabel.setText(f'Optimization scan 1')
        else:
            self.mw.runMessageLabel.setText(f'Optimization scan {self.scan-self.spars["equilib. scans"]+1}')
            
        if self.vpars['verbose']:
            logger.info(f'Acquistion start address = {start_address}, end = {end_address-1}')
            logger.info(f'Acquired {end_address-start_address} bytes, {nsamples} full samples' )
            logger.info(f'Transfered {blocks_transfer} blocks, {bytes_transfer} bytes')
            logger.info(f'Received {bytes_received} bytes')
            logger.info(f"Transfer time = {transfer_time:0.4f} s")

        np_ashims_vec = np.array(self.active_shims_vec)   
        with np.printoptions(precision=5, sign='+',
                             suppress=True, floatmode='fixed'):
            if self.scan < self.spars['equilib. scans']: 
                ind = self.scan+1 
            else:
                ind = self.scan-self.spars['equilib. scans']+1
            logger.info(f'{ind} {lag_time:0.3f}s: {peak:0.2f} {np_ashims_vec}')
        
        # collect results
        if self.scan >= self.spars['equilib. scans'] and self.spars['scans'] > 0:
            self.collector.append([self.scan-self.spars['equilib. scans']+1, peak, self.active_shims_vec])
        
        # call gen_NM and set shims if next scan is optimization
        if not self.gpars['test scan'] and self.spars['scans'] > 0:
            if self.scan >= self.spars['equilib. scans']:
                self.active_shims_vec = next(self.gen_NM)
                new_shims = ss.update_shims_record(self.start_shims, self.active_shims_vec, self.incs)
                success,_ , satflags,Itotal ,_ = ss.set_shims(self.mw.si, new_shims)
                if np.sum(np.abs(satflags)) > 0:
                    logger.info(f'saturated shim DACs: {satflags}')
                if not success:
                    logger.warning('Invalid shims, may exceed total current limit')
                    logger.info(f'total DAC current: {Itotal}')                    
                
        # schedule processing for next scan
        # after last scan, call finish_run()
        self.scan += 1
        if self.scan < self.nscans and not self.gpars['test scan']:
            marktime = self.seq.GetMarkTime(self.scan)
            seqtime = self.mw.si.GetSeqTime()
            self.scan_timer.start(1000*(marktime-seqtime)+10)
        else:
            self.finish_run()

    def finish_run(self):
        
        self.mw.runTabStartButton.blockSignals(True)
        self.mw.runTabStartButton.setText('Stopping...')
        self.mw.runTabStartButton.repaint()

        self.scan_timer.stop()         # stop timer to stop calls to process_scans()
        self.mw.si.AssertSeqReset()    # stop and reset the sequencer
        
        #### find best scan, report, and save best shims
        if len(self.collector) > 0 and not self.gpars['test scan']:   # might be new shims
            peaks = [row[1] for row in self.collector]
            best_scan = self.collector[np.argmax(peaks)]
            logger.info(f'Max peak height {best_scan[1]:8.4f} at scan {best_scan[0]}')
            with np.printoptions(precision = 5):
                logger.info(f'Best shims {best_scan[2]}')
            if best_scan[0] == 1:
                logger.info('Best shims are starting shims')
                logger.info('Load starting shims')
                success,_ , satflags,_ ,_ = ss.set_shims(self.mw.si, self.start_shims)
                if np.sum(np.abs(satflags)) > 0:
                    logger.info(f'saturated shim DACs: {satflags}')
                if not success:
                    logger.warning('Invalid shims, may exceed total current limit')         
            elif not self.fpars['save']:   
                logger.info('Best shims will not be saved')
                logger.info('Load starting shims')
                success,_ , satflags,_ ,_ = ss.set_shims(self.mw.si, self.start_shims)
                if np.sum(np.abs(satflags)) > 0:
                    logger.info(f'saturated shim DACs: {satflags}')
                if not success:
                    logger.warning('Invalid shims, may exceed total current limit')          
            else:
                # make full shim record and load
                best_shims_vec = best_scan[2]
                new_shims = ss.update_shims_record(self.start_shims, best_shims_vec, self.incs)
                logger.info('Load best shims')
                success,_ , satflags,_ ,_ = ss.set_shims(self.mw.si, new_shims)
                if success:
                    success_save,_,_ = ss.SAV(self.mw.si)
                    if not success_save:
                        logger.warning('Saving shims to flash failed')
                if np.sum(np.abs(satflags)) > 0:
                    logger.info(f'saturated shim DACs: {satflags}')
                if not success:
                    logger.warning('Invalid shims, may exceed total current limit')
 
                # save new shims and update global shimfile name
                print("Saving shim file")
                wrapped_new_shims = nj.noindent_wrap(new_shims)
                logger.info(f'Saving best shims to {self.new_shim_file}')
                os.makedirs(os.path.dirname(self.new_shim_file), exist_ok=True)
                with open(self.new_shim_file,'w') as jfile:  
                    json.dump(wrapped_new_shims, jfile, cls=nj.NoIndentEncoder, indent=4)
                self.mw.p.child('Global','shim file').setValue(self.fpars['new shim file'])
            
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
    def newShimFileLineEdit_changed(self,value):
        self.mw.p.child('Shim Run','Files','new shim file').setValue(value)
    
    def shim_filename_param_changed(self):
        self.mw.newShimFileLineEdit.setText(self.mw.p.child('Shim Run','Files','new shim file').value())

    def scansSpinBox_changed(self,value):
        self.mw.p.child('Shim Run','Sequencer','scans').setValue(value)
    
    def scans_param_changed(self):
        self.mw.scansSpinBox.setValue(self.mw.p.child('Shim Run','Sequencer','scans').value())
    
    def acquireTimeSpinBox_changed(self,value):
        self.mw.p.child('Shim Run','Sequencer','acquire time').setValue(value)
        
    def acquiretime_param_changed(self):
        self.mw.acquireTimeSpinBox.setValue(self.mw.p.child('Shim Run','Sequencer','acquire time').value())
    
    def recoveryTimeSpinBox_changed(self,value):
        self.mw.p.child('Shim Run','Sequencer','recovery time').setValue(value)
        
    def recoverytime_param_changed(self):
        self.mw.recoveryTimeSpinBox.setValue(self.mw.p.child('Shim Run','Sequencer','recovery time').value())
        
    def incsComboBox_activated(self,value):
        text_item = self.inc_names[value]
        self.mw.p.child('Shim Run','Sequencer','increments').setValue(text_item)
        
    def shim_increments_param_changed(self):
        item_text = self.mw.p.child('Shim Run','Sequencer','increments').value()
        inc_index = self.inc_names.index(item_text)
        self.mw.incsComboBox.setCurrentIndex(inc_index)
 
            
    #################################
    # utility functions and constants
    # things to do when the run ends regularly or when interrupted
    def cleanup(self):
        TRIGGER_PATH = r'..\scan_trigger.txt'
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
                childWidget.deleteLater               

    inc_names = ["fine","medium","coarse 1","coarse 2","custom 1","custom 2"]
    
    # all runs must define default_settings with at least these settings:
    # outermost dict with 'Run Name' name under key 'name'
    # ['Run Name','Sequencer','spectral width']
    # ['Run Name','Processing','phase phi 0']
    # ['Run Name','Processing','phase phi 1']
    # ['Run Name','Processing','phase pivot']
    # ['Run Name','Processing','ppm offset']
    # ['Run Name','Processing','plot mag']
    default_settings =  \
        {'name': 'Shim Run', 'type': 'group', 'expanded': True, 'children': 
            [
            {'name': 'Files', 'type': 'group', 'expanded': False, 'children':
                [
                {'name': 'new shim file', 'type': 'str', 'value': 'new_shim_file'},
                {'name': 'notes', 'type': 'str', 'value': 'tests'},
                {'name': 'save', 'type': 'bool', 'value': True}
                ]
            },
            {'name': 'Sequencer', 'type': 'group', 'expanded': False, 'children':
                [
                {'name': 'scans', 'type': 'int', 'value': 200, 'limits': [0,2000]},
                {'name': 'increments', 'type': 'list', 'values': ['fine','medium','coarse 1','coarse 2','custom 1','custom 2'], 'value': 4},
                {'name': 'equilib. scans', 'type': 'int', 'value': 4, 'limits': [0,100]},
                {'name': 'acquire time', 'type': 'float', 'value': 0.5, 'decimals': 2, 'step': 0.1, 'limits': [0,1000], 'siSuffix': True, 'suffix': 's'},
                {'name': 'recovery time', 'type': 'float', 'value': 5.0, 'decimals': 2, 'step': 0.1, 'limits': [0,1000], 'siSuffix': True, 'suffix': 's'},
                {'name': 'pulse amplitude', 'type': 'float', 'value': 0.42, 'decimals': 4, 'step': 0.01, 'limits': [0,1]},
                {'name': 'pulse time', 'type': 'float', 'value': 12.0, 'step': 1, 'limits': [0,10000], 'siSuffix': True, 'suffix': '\u03bcs'},
                {'name': 'spectral width', 'type': 'float', 'value': 10.0, 'step': 1.0, 'limits': [5,1000], 'siSuffix': True, 'suffix': 'kHz', 'decimals': 5},
                {'name': 'Rx delay 1', 'type': 'float', 'value': 50.0, 'step': 1, 'limits': [0,10000], 'siSuffix': True, 'suffix': '\u03bcs'},
                {'name': 'Rx delay 2', 'type': 'float', 'value': 250.0, 'step': 1, 'limits': [0,10000], 'siSuffix': True, 'suffix': '\u03bcs'},
                {'name': 'page mode', 'type': 'bool', 'value': True},
                {'name': 'auto atten', 'type': 'bool', 'value': True},
                {'name': 'filter atten', 'type': 'int', 'value': 27, 'limits': [4,31],'step': 1},
                {'name': 'auto decim', 'type': 'bool', 'value': True},
                {'name': 'decimation', 'type': 'int', 'value': 16000, 'limits': [2,32000],'step': 1},
                {'name': 'shim offsets', 'type': 'str', 'value': '[0; 0,0,0; 0,0,0,0,0; 0,0,0,0,0,0,0; 0]'},
                {'name': 'inc multiplier', 'type': 'float', 'value': 1.0, 'decimals': 2, 'step': 0.1, 'limits': [-20,20]},
                {'name': 'Increment Defs', 'type': 'group', 'expanded': False, 'children':
                    [
                    {'name': 'fine', 'type': 'str', 'value': '[0;0.0003,0.001,0.001;0,0,0,0,0;0,0,0,0,0,0,0;0]'},
                    {'name': 'medium', 'type': 'str', 'value': '[0;0.0003,0.001,0.001;0.001,0.002,0.002,0.002,0.001;0,0,0,0,0,0,0;0]'},
                    {'name': 'coarse 1', 'type': 'str', 'value': '[0;0.0003,0.001,0.001;0.001,0.002,0.002,0.002,0.001;0.005,0,0,0,0,0,0;-0.015]'},
                    {'name': 'coarse 2', 'type': 'str', 'value': '[0;0.0003,0.001,0.001;0,0,0,0,0;0.005,0.004,0.002,0.01,0.01,0.015,0.015;-0.015]'},
                    {'name': 'custom 1', 'type': 'str', 'value': '[0;0,0,0;0,0,0,0,0;0,0,0,0,0,0,0;0]'},
                    {'name': 'custom 2', 'type': 'str', 'value': '[0;0,0,0;0,0,0,0,0;0,0,0,0,0,0,0;0]'}
                    ]}
                ]
            },
            {'name': 'Processing', 'type': 'group', 'expanded': False, 'children':
                [
                {'name': 'track Tx freq', 'type': 'bool', 'value': False},
                {'name': 'phase phi 0', 'type': 'float', 'value': 0.0, 'step': 1.0, 'limits': [-180,180],'siSuffix': True, 'suffix': 'deg'},
                {'name': 'phase phi 1', 'type': 'float', 'value': 0.0, 'step': 1.0, 'siSuffix': True, 'suffix': 'deg/Hz'},
                {'name': 'phase pivot', 'type': 'float', 'value': 0.0, 'step': 1.0,'siSuffix': True, 'suffix': 'Hz'},
                {'name': 'ppm offset', 'type': 'float', 'value': 0.0, 'step': 0.1}, 
                {'name': 'plot mag', 'type': 'bool', 'value': False},
                {'name': 'apodize', 'type': 'bool', 'value': False},
                {'name': 'broadening', 'type': 'float', 'value': 1.0, 'step': 0.1,'siSuffix': True, 'suffix': 'Hz'},
                {'name': 'zero pad', 'type': 'int', 'value': 200000, 'step': 10000},
                {'name': 'software filter', 'type': 'str', 'value': 'None'}
                ]
            }
            ]
        }
            