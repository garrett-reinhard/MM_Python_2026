"""qmcontrol by John Price"""

import sys
import os
import logging
import traceback
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from qmcontrol.mainframe import MainFrame
from qmcontrol.qm_logger import init_logging

from win32event import CreateMutex
from win32api import GetLastError
from winerror import ERROR_ALREADY_EXISTS



# os.environ[] changes env variables that were captured at
# python start-up. Changes do not persist.

#handle logging uncaught exceptions
def exception_handler(etype, value, tb):
    try:
        logger = logging.getLogger(__file__)
        fmt = "".join(traceback.format_exception(etype,value,tb))
        logger.error("Uncaught exception: {0}".format(fmt))
    except Exception as e:
        print("Error with exception_handler: %s"%e)
    except:
        print("Unknown Error with exception_handler")
        
def main():
    
    
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    sys.excepthook = exception_handler
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    init_logging(Path(__file__).parent / "logging.json")
    mutex = CreateMutex(None, False, "QMAGNETICS_QMCONTROL")
    lasterror = GetLastError()
    if lasterror == ERROR_ALREADY_EXISTS:
        logger = logging.getLogger(__name__)
        logger.error("Detected another version of QMControl already running.  exiting")
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setWindowTitle("QMControl is already running.")
        msgBox.setText("Another version of QMControl is already running.")
        msgBox.setInformativeText("Only one instance of QMControl may be running at a time.")
        msgBox.setStandardButtons(QMessageBox.Close)
        msgBox.finished.connect(app.closeAllWindows)
        msgBox.show()

    else:    
        mainwindow = MainFrame()
        mainwindow.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
