from pathlib import Path
import logging
from pyqtgraph.parametertree import Parameter, ParameterTree, parameterTypes
from PySide6.QtGui import QFontMetricsF

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QPushButton)

logger = logging.getLogger(__name__)

class DirectoryParameterItem(parameterTypes.str.StrParameterItem):
    def __init__(self, param, depth):
        self._value = None
        super().__init__(param, depth)

        button = QPushButton('...')
        button.setFixedWidth(25)
        button.setContentsMargins(0, 0, 0, 0)
        button.clicked.connect(self.setDirectory)
        self.widget.editingFinished.connect(self.textUpdate)
        self.layoutWidget.layout().insertWidget(2, button)
        self.displayLabel.resizeEvent = self._newResizeEvent
        # self.layoutWidget.layout().insertWidget(3, self.defaultBtn)

    def makeWidget(self):
        w = super().makeWidget()
        w.setValue = self.setValue
        w.value = self.value
        # Doesn't make much sense to have a 'changing' signal since filepaths should be complete before value
        # is emitted
        delattr(w, 'sigChanging')
        return w

    def _newResizeEvent(self, ev):
        ret = type(self.displayLabel).resizeEvent(self.displayLabel, ev)
        self.updateDisplayLabel()
        return ret

    def textUpdate(self):
        v = str(Path(self.widget.text()).absolute())
        logger.info("TextUpdate: %s"%v)
        self.param.setValue(v)
    
    def setValue(self, value):
        self._value = value
        self.widget.setText(str(value))

    def value(self):
        return self._value

    def setDirectory(self):
        curVal = self.param.value()
        fname = QFileDialog.getExistingDirectory(None,"",str(Path(curVal).parent.absolute()))
        if not fname:
            return
        self.param.setValue(fname)

    def updateDefaultBtn(self):
        # Override since a readonly label should still allow reverting to default
        ## enable/disable default btn
        self.defaultBtn.setEnabled(
            not self.param.valueIsDefault() and self.param.opts['enabled'])

        # hide / show
        self.defaultBtn.setVisible(self.param.hasDefault())

    def updateDisplayLabel(self, value=None):
        lbl = self.displayLabel
        if value is None:
            value = self.param.value()
        value = str(value)
        font = lbl.font()
        metrics = QFontMetricsF(font)
        value = metrics.elidedText(value, Qt.TextElideMode.ElideLeft, lbl.width()-5)
        return super().updateDisplayLabel(value)



class DirectoryParameter(Parameter):
    """
    Interfaces with the myriad of file options available from a QFileDialog.

    Note that the output can either be a single file string or list of files, depending on whether
    `fileMode='ExistingFiles'` is specified.

    Note that in all cases, absolute file paths are returned unless `relativeTo` is specified as
    elaborated below.

    ============== ========================================================
    **Options:**
    parent         Dialog parent
    winTitle       Title of dialog window
    nameFilter     File filter as required by the Qt dialog
    directory      Where in the file system to open this dialog
    selectFile     File to preselect
    relativeTo     Parent directory that, if provided, will be removed from the prefix of all returned paths. So,
                   if '/my/text/file.txt' was selected, and `relativeTo='my/text/'`, the return value would be
                   'file.txt'. This uses os.path.relpath under the hood, so expect that behavior.
    kwargs         Any enum value accepted by a QFileDialog and its value. Values can be a string or list of strings,
                   i.e. fileMode='AnyFile', options=['ShowDirsOnly', 'DontResolveSymlinks']
    ============== ========================================================
    """
    itemClass = DirectoryParameterItem

    def __init__(self, **opts):
        #opts.setdefault('readonly', True)
        super().__init__(**opts)
