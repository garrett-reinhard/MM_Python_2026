from PySide6.QtWidgets import QDoubleSpinBox
from PySide6.QtGui import QValidator
import logging

class QMagSpinBox(QDoubleSpinBox):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def validate(self, input, pos ):
        v = super().validate(input,pos)
        if v[0] == QValidator.State.Acceptable:
            return v
        try:
            val = float(input)
            if self.minimum() <= val <= self.maximum():
                num = input.split('.')
                x = "%s.%s"%(num[0],num[1][:self.decimals()])
                return (QValidator.State.Acceptable, x, pos)
        except ValueError:
            pass
        return v        
    
    
    