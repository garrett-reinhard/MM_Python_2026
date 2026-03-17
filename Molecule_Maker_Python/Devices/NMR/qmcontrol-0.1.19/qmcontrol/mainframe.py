import sys
import json
import time
from pathlib import Path
import logging


from PySide6.QtCore import Qt, QSize, QTimer, QObject, Signal, Slot
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QMainWindow,
    QDialog,
    QLabel,
    QVBoxLayout,
    QHBoxLayout)

from qmcontrol.ui.mainframe import Ui_MainFrame
from qmcontrol.ui.about import Ui_AboutDialog
from qmcontrol.ui.hwinfo import Ui_HardwareInfo

try:
    from qmcontrol.version import Version
except:
    Version="development"

logger = logging.getLogger(__name__)

__author__ = "John Price"
__copyright__ = "Copyright 2021, Q Magnetics, LLC"
__credits__ = ["John Price", "Rainer Malzbender"]
__license__ = "undecided"
__version__ = "0.1"
__maintainer__ = "John Price"
__email__ = "john@qmagnetics.com"
__status__ = "development"


class AboutDialog(QDialog, Ui_AboutDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.versionLabel.setText(Version)
        logger.info("Reading licenses file: %s"%(Path(__file__).parent / "licenses.txt"))
        with open(Path(__file__).parent / "licenses.txt",'rb') as fin:
            text = fin.read().decode()
        self.licensesField.setPlainText(text)
    
class HWDialog(QDialog, Ui_HardwareInfo):
    query_hw_sig = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

    def showEvent(self, event):
        super().showEvent(event)
        self.do_hw_query()
    def do_hw_query(self, ):
        self.spectrometerLabel.setText("checking...")
        self.hwInfoBox.hide()
        self.deviceId.setText("")
        self.serialNumber.setText("")
        self.usbInterface.setText("")
        self.usbSpeed.setText("")
        self.okProductVersion.setText("")
        self.okAPIVersion.setText("")

        self.query_hw_sig.emit()

    Slot(object)
    def on_hw_info(self, hw_data):
        if not hw_data['present']:
            self.spectrometerLabel.setText("Not Present")
            self.hwInfoBox.hide()
            return
        self.spectrometerLabel.setText("Connected")
        
        print(hw_data)
        for item in hw_data:
            if hasattr(self,item):
                getattr(self,item).setText(hw_data[item])
            else:
                print("unknown item: %s"%item)
        self.hwInfoBox.show()
    


class MainFrame(QMainWindow, Ui_MainFrame):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.about_dialog = AboutDialog(self)
        self.hw_dialog = HWDialog(self)
        
        self.actionAbout.triggered.connect(self.about_dialog.open)
        self.actionHardware_Info.triggered.connect(self.hw_dialog.open)
        self.actionSave_Settings.triggered.connect(self.qmcontrol.save_settings)

        self.hw_dialog.query_hw_sig.connect(self.qmcontrol.on_hwQuery)
        self.qmcontrol.hw_info_sig.connect(self.hw_dialog.on_hw_info)
        
    def closeEvent(self, event):
        self.qmcontrol.close()
        
        