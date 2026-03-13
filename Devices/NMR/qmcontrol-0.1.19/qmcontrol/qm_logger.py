import json
import logging
import logging.config
from pathlib import Path
import sys

from PySide6.QtCore import QObject, Signal

from .interface_constants import logfile

class LogSignal(QObject):
    log_sig = Signal(str)


class GUIHandler(logging.Handler):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.emitter = LogSignal()
        print(self.__dict__)

    def emit(self, record):
        msg = msg = self.format(record)
        self.emitter.log_sig.emit(msg)

class QMFileHandler(logging.handlers.RotatingFileHandler):
    def __init__(self, filename=None, *args, **kwargs):
        Path(logfile).parent.mkdir(exist_ok=True)
        super().__init__(logfile, *args, **kwargs)
    
    
   
    
def init_logging(log_json):
    with open(log_json) as fin:
        log_dict = json.load(fin)
    print(log_dict)
    logging.config.dictConfig(log_dict)
    
    
    
