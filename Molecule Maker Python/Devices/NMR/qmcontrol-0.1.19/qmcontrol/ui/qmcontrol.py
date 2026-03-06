# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'qmcontrol.ui'
##
## Created by: Qt User Interface Compiler version 6.2.4
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QComboBox,
    QFrame, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSlider, QSpacerItem,
    QSplitter, QTabWidget, QTextEdit, QVBoxLayout,
    QWidget)

from qmcontrol.qmagspinbox import QMagSpinBox

class Ui_mainWindow(object):
    def setupUi(self, mainWindow):
        if not mainWindow.objectName():
            mainWindow.setObjectName(u"mainWindow")
        mainWindow.resize(866, 751)
        self.verticalLayout = QVBoxLayout(mainWindow)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, 7, -1, -1)
        self.mainHsplitter = QSplitter(mainWindow)
        self.mainHsplitter.setObjectName(u"mainHsplitter")
        self.mainHsplitter.setOrientation(Qt.Vertical)
        self.upperFrame = QFrame(self.mainHsplitter)
        self.upperFrame.setObjectName(u"upperFrame")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(5)
        sizePolicy.setHeightForWidth(self.upperFrame.sizePolicy().hasHeightForWidth())
        self.upperFrame.setSizePolicy(sizePolicy)
        self.upperFrame.setFrameShape(QFrame.NoFrame)
        self.upperFrame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.upperFrame)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.middleSplitter = QSplitter(self.upperFrame)
        self.middleSplitter.setObjectName(u"middleSplitter")
        self.middleSplitter.setOrientation(Qt.Horizontal)
        self.settingsFrame = QFrame(self.middleSplitter)
        self.settingsFrame.setObjectName(u"settingsFrame")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.settingsFrame.sizePolicy().hasHeightForWidth())
        self.settingsFrame.setSizePolicy(sizePolicy1)
        self.settingsFrame.setFrameShape(QFrame.StyledPanel)
        self.settingsFrame.setFrameShadow(QFrame.Raised)
        self.middleSplitter.addWidget(self.settingsFrame)
        self.tabFrame = QFrame(self.middleSplitter)
        self.tabFrame.setObjectName(u"tabFrame")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(5)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.tabFrame.sizePolicy().hasHeightForWidth())
        self.tabFrame.setSizePolicy(sizePolicy2)
        self.tabFrame.setFrameShape(QFrame.NoFrame)
        self.tabFrame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.tabFrame)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.tabWidget = QTabWidget(self.tabFrame)
        self.tabWidget.setObjectName(u"tabWidget")
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy3)
        self.runTab = QWidget()
        self.runTab.setObjectName(u"runTab")
        self.horizontalLayout_4 = QHBoxLayout(self.runTab)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.runTabFrame = QFrame(self.runTab)
        self.runTabFrame.setObjectName(u"runTabFrame")
        self.runTabFrame.setFrameShape(QFrame.StyledPanel)
        self.verticalLayout_5 = QVBoxLayout(self.runTabFrame)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.runTabUpperFrame = QFrame(self.runTabFrame)
        self.runTabUpperFrame.setObjectName(u"runTabUpperFrame")
        sizePolicy4 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(1)
        sizePolicy4.setHeightForWidth(self.runTabUpperFrame.sizePolicy().hasHeightForWidth())
        self.runTabUpperFrame.setSizePolicy(sizePolicy4)
        self.runTabUpperFrame.setMinimumSize(QSize(0, 0))
        self.runTabUpperFrame.setBaseSize(QSize(0, 0))
        self.runTabUpperFrame.setFrameShape(QFrame.NoFrame)
        self.runTabUpperFrame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.runTabUpperFrame)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.runTabStartButtonFrame = QFrame(self.runTabUpperFrame)
        self.runTabStartButtonFrame.setObjectName(u"runTabStartButtonFrame")
        sizePolicy3.setHeightForWidth(self.runTabStartButtonFrame.sizePolicy().hasHeightForWidth())
        self.runTabStartButtonFrame.setSizePolicy(sizePolicy3)
        self.runTabStartButtonFrame.setMinimumSize(QSize(0, 30))
        self.runTabStartButtonFrame.setMaximumSize(QSize(16777215, 30))
        self.runTabStartButtonFrame.setFrameShape(QFrame.NoFrame)
        self.runTabStartButtonFrame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_6 = QHBoxLayout(self.runTabStartButtonFrame)
        self.horizontalLayout_6.setSpacing(4)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(9, 0, -1, 0)
        self.runTabStartButton = QPushButton(self.runTabStartButtonFrame)
        self.runTabStartButton.setObjectName(u"runTabStartButton")

        self.horizontalLayout_6.addWidget(self.runTabStartButton)

        self.horizontalSpacer_4 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_4)

        self.runTabRunsComboBox = QComboBox(self.runTabStartButtonFrame)
        self.runTabRunsComboBox.setObjectName(u"runTabRunsComboBox")
        sizePolicy5 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.runTabRunsComboBox.sizePolicy().hasHeightForWidth())
        self.runTabRunsComboBox.setSizePolicy(sizePolicy5)
        self.runTabRunsComboBox.setMinimumSize(QSize(100, 0))
        self.runTabRunsComboBox.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_6.addWidget(self.runTabRunsComboBox)

        self.horizontalSpacer_5 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_5)

        self.txFreqSpinBox = QMagSpinBox(self.runTabStartButtonFrame)
        self.txFreqSpinBox.setObjectName(u"txFreqSpinBox")
        self.txFreqSpinBox.setDecimals(6)
        self.txFreqSpinBox.setMinimum(1.000000000000000)
        self.txFreqSpinBox.setMaximum(150.000000000000000)
        self.txFreqSpinBox.setSingleStep(0.000010000000000)
        self.txFreqSpinBox.setStepType(QAbstractSpinBox.DefaultStepType)
        self.txFreqSpinBox.setValue(125.000000000000000)

        self.horizontalLayout_6.addWidget(self.txFreqSpinBox)

        self.txFreqLabel = QLabel(self.runTabStartButtonFrame)
        self.txFreqLabel.setObjectName(u"txFreqLabel")

        self.horizontalLayout_6.addWidget(self.txFreqLabel)

        self.horizontalSpacer_6 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_6)

        self.runTabTestCheckBox = QCheckBox(self.runTabStartButtonFrame)
        self.runTabTestCheckBox.setObjectName(u"runTabTestCheckBox")
        self.runTabTestCheckBox.setChecked(True)

        self.horizontalLayout_6.addWidget(self.runTabTestCheckBox)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer)


        self.verticalLayout_2.addWidget(self.runTabStartButtonFrame)

        self.codeWidgetsFrame1 = QFrame(self.runTabUpperFrame)
        self.codeWidgetsFrame1.setObjectName(u"codeWidgetsFrame1")
        self.codeWidgetsFrame1.setMinimumSize(QSize(0, 30))
        self.codeWidgetsFrame1.setMaximumSize(QSize(16777215, 30))
        self.codeWidgetsFrame1.setFrameShape(QFrame.NoFrame)
        self.codeWidgetsFrame1.setFrameShadow(QFrame.Raised)
        self.codeWidgetsLayout1 = QHBoxLayout(self.codeWidgetsFrame1)
        self.codeWidgetsLayout1.setSpacing(4)
        self.codeWidgetsLayout1.setObjectName(u"codeWidgetsLayout1")
        self.codeWidgetsLayout1.setContentsMargins(-1, 0, -1, 0)
        self.codeWidgetsHSpacer1 = QSpacerItem(171, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.codeWidgetsLayout1.addItem(self.codeWidgetsHSpacer1)


        self.verticalLayout_2.addWidget(self.codeWidgetsFrame1)

        self.codeWidgetsFrame2 = QFrame(self.runTabUpperFrame)
        self.codeWidgetsFrame2.setObjectName(u"codeWidgetsFrame2")
        self.codeWidgetsFrame2.setMinimumSize(QSize(0, 30))
        self.codeWidgetsFrame2.setMaximumSize(QSize(16777215, 30))
        self.codeWidgetsFrame2.setFrameShape(QFrame.NoFrame)
        self.codeWidgetsFrame2.setFrameShadow(QFrame.Raised)
        self.codeWidgetsLayout2 = QHBoxLayout(self.codeWidgetsFrame2)
        self.codeWidgetsLayout2.setSpacing(4)
        self.codeWidgetsLayout2.setObjectName(u"codeWidgetsLayout2")
        self.codeWidgetsLayout2.setContentsMargins(-1, 0, -1, 0)
        self.codeWidgetsHSpacer2 = QSpacerItem(758, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.codeWidgetsLayout2.addItem(self.codeWidgetsHSpacer2)


        self.verticalLayout_2.addWidget(self.codeWidgetsFrame2)

        self.runTabPlotFrame = QFrame(self.runTabUpperFrame)
        self.runTabPlotFrame.setObjectName(u"runTabPlotFrame")
        self.runTabPlotFrame.setFrameShape(QFrame.StyledPanel)
        self.runTabPlotFrame.setFrameShadow(QFrame.Raised)

        self.verticalLayout_2.addWidget(self.runTabPlotFrame)


        self.verticalLayout_5.addWidget(self.runTabUpperFrame)

        self.runTabPhaseFrame = QFrame(self.runTabFrame)
        self.runTabPhaseFrame.setObjectName(u"runTabPhaseFrame")
        sizePolicy3.setHeightForWidth(self.runTabPhaseFrame.sizePolicy().hasHeightForWidth())
        self.runTabPhaseFrame.setSizePolicy(sizePolicy3)
        self.runTabPhaseFrame.setMinimumSize(QSize(0, 0))
        self.runTabPhaseFrame.setFrameShape(QFrame.NoFrame)
        self.runTabPhaseFrame.setFrameShadow(QFrame.Raised)
        self.gridLayout = QGridLayout(self.runTabPhaseFrame)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(12)
        self.gridLayout.setContentsMargins(-1, 6, 20, 6)
        self.label_9 = QLabel(self.runTabPhaseFrame)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setMaximumSize(QSize(16777215, 30))
        self.label_9.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.label_9, 7, 1, 1, 1)

        self.runTabPhi0SliderF = QSlider(self.runTabPhaseFrame)
        self.runTabPhi0SliderF.setObjectName(u"runTabPhi0SliderF")
        self.runTabPhi0SliderF.setMinimum(-1000)
        self.runTabPhi0SliderF.setMaximum(1000)
        self.runTabPhi0SliderF.setOrientation(Qt.Horizontal)
        self.runTabPhi0SliderF.setTickPosition(QSlider.TicksAbove)
        self.runTabPhi0SliderF.setTickInterval(500)

        self.gridLayout.addWidget(self.runTabPhi0SliderF, 0, 2, 1, 1)

        self.label_3 = QLabel(self.runTabPhaseFrame)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)

        self.label = QLabel(self.runTabPhaseFrame)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.runTabPhi1SliderC = QSlider(self.runTabPhaseFrame)
        self.runTabPhi1SliderC.setObjectName(u"runTabPhi1SliderC")
        self.runTabPhi1SliderC.setMinimum(-1000)
        self.runTabPhi1SliderC.setMaximum(1000)
        self.runTabPhi1SliderC.setOrientation(Qt.Horizontal)
        self.runTabPhi1SliderC.setTickPosition(QSlider.TicksAbove)
        self.runTabPhi1SliderC.setTickInterval(500)

        self.gridLayout.addWidget(self.runTabPhi1SliderC, 2, 1, 1, 1)

        self.runTab0ppmSliderF = QSlider(self.runTabPhaseFrame)
        self.runTab0ppmSliderF.setObjectName(u"runTab0ppmSliderF")
        self.runTab0ppmSliderF.setMinimum(-1000)
        self.runTab0ppmSliderF.setMaximum(1000)
        self.runTab0ppmSliderF.setOrientation(Qt.Horizontal)
        self.runTab0ppmSliderF.setTickPosition(QSlider.TicksAbove)
        self.runTab0ppmSliderF.setTickInterval(500)

        self.gridLayout.addWidget(self.runTab0ppmSliderF, 5, 2, 1, 1)

        self.runTab0ppmSliderC = QSlider(self.runTabPhaseFrame)
        self.runTab0ppmSliderC.setObjectName(u"runTab0ppmSliderC")
        self.runTab0ppmSliderC.setMinimum(-1000)
        self.runTab0ppmSliderC.setMaximum(1000)
        self.runTab0ppmSliderC.setOrientation(Qt.Horizontal)
        self.runTab0ppmSliderC.setTickPosition(QSlider.TicksAbove)
        self.runTab0ppmSliderC.setTickInterval(500)

        self.gridLayout.addWidget(self.runTab0ppmSliderC, 5, 1, 1, 1)

        self.runTabPhi0SliderC = QSlider(self.runTabPhaseFrame)
        self.runTabPhi0SliderC.setObjectName(u"runTabPhi0SliderC")
        self.runTabPhi0SliderC.setMinimum(-1000)
        self.runTabPhi0SliderC.setMaximum(1000)
        self.runTabPhi0SliderC.setOrientation(Qt.Horizontal)
        self.runTabPhi0SliderC.setTickPosition(QSlider.TicksAbove)
        self.runTabPhi0SliderC.setTickInterval(500)

        self.gridLayout.addWidget(self.runTabPhi0SliderC, 0, 1, 1, 1)

        self.label_4 = QLabel(self.runTabPhaseFrame)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)

        self.label_10 = QLabel(self.runTabPhaseFrame)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setMaximumSize(QSize(16777215, 30))
        self.label_10.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.label_10, 7, 2, 1, 1)

        self.runTabPivotSliderF = QSlider(self.runTabPhaseFrame)
        self.runTabPivotSliderF.setObjectName(u"runTabPivotSliderF")
        self.runTabPivotSliderF.setMinimum(-1000)
        self.runTabPivotSliderF.setMaximum(1000)
        self.runTabPivotSliderF.setOrientation(Qt.Horizontal)
        self.runTabPivotSliderF.setTickPosition(QSlider.TicksAbove)
        self.runTabPivotSliderF.setTickInterval(500)

        self.gridLayout.addWidget(self.runTabPivotSliderF, 3, 2, 1, 1)

        self.runTabPhi1SliderF = QSlider(self.runTabPhaseFrame)
        self.runTabPhi1SliderF.setObjectName(u"runTabPhi1SliderF")
        self.runTabPhi1SliderF.setMinimum(-1000)
        self.runTabPhi1SliderF.setMaximum(1000)
        self.runTabPhi1SliderF.setSingleStep(1)
        self.runTabPhi1SliderF.setOrientation(Qt.Horizontal)
        self.runTabPhi1SliderF.setTickPosition(QSlider.TicksAbove)
        self.runTabPhi1SliderF.setTickInterval(500)

        self.gridLayout.addWidget(self.runTabPhi1SliderF, 2, 2, 1, 1)

        self.runTabPivotSliderC = QSlider(self.runTabPhaseFrame)
        self.runTabPivotSliderC.setObjectName(u"runTabPivotSliderC")
        self.runTabPivotSliderC.setMinimum(-1000)
        self.runTabPivotSliderC.setMaximum(1000)
        self.runTabPivotSliderC.setOrientation(Qt.Horizontal)
        self.runTabPivotSliderC.setTickPosition(QSlider.TicksAbove)
        self.runTabPivotSliderC.setTickInterval(500)

        self.gridLayout.addWidget(self.runTabPivotSliderC, 3, 1, 1, 1)

        self.label_5 = QLabel(self.runTabPhaseFrame)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label_5, 5, 0, 1, 1)


        self.verticalLayout_5.addWidget(self.runTabPhaseFrame)

        self.runTabFidCheckBoxFrame = QFrame(self.runTabFrame)
        self.runTabFidCheckBoxFrame.setObjectName(u"runTabFidCheckBoxFrame")
        self.runTabFidCheckBoxFrame.setMinimumSize(QSize(0, 30))
        self.runTabFidCheckBoxFrame.setMaximumSize(QSize(16777215, 30))
        self.runTabFidCheckBoxFrame.setFrameShape(QFrame.NoFrame)
        self.runTabFidCheckBoxFrame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_8 = QHBoxLayout(self.runTabFidCheckBoxFrame)
        self.horizontalLayout_8.setSpacing(4)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(-1, 0, -1, 0)
        self.phasingCheckBox = QCheckBox(self.runTabFidCheckBoxFrame)
        self.phasingCheckBox.setObjectName(u"phasingCheckBox")

        self.horizontalLayout_8.addWidget(self.phasingCheckBox)

        self.horizontalSpacer_16 = QSpacerItem(8, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_16)

        self.runTabFidCheckBox = QCheckBox(self.runTabFidCheckBoxFrame)
        self.runTabFidCheckBox.setObjectName(u"runTabFidCheckBox")

        self.horizontalLayout_8.addWidget(self.runTabFidCheckBox)

        self.horizontalSpacer_9 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_9)

        self.runTabHzCheckBox = QCheckBox(self.runTabFidCheckBoxFrame)
        self.runTabHzCheckBox.setObjectName(u"runTabHzCheckBox")

        self.horizontalLayout_8.addWidget(self.runTabHzCheckBox)

        self.horizontalSpacer_10 = QSpacerItem(12, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_10)

        self.runTabFullXButton = QPushButton(self.runTabFidCheckBoxFrame)
        self.runTabFullXButton.setObjectName(u"runTabFullXButton")

        self.horizontalLayout_8.addWidget(self.runTabFullXButton)

        self.horizontalSpacer_13 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_13)

        self.runTabFullYButton = QPushButton(self.runTabFidCheckBoxFrame)
        self.runTabFullYButton.setObjectName(u"runTabFullYButton")

        self.horizontalLayout_8.addWidget(self.runTabFullYButton)

        self.horizontalSpacer_3 = QSpacerItem(204, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_3)

        self.runMessageLabel = QLabel(self.runTabFidCheckBoxFrame)
        self.runMessageLabel.setObjectName(u"runMessageLabel")
        self.runMessageLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_8.addWidget(self.runMessageLabel)


        self.verticalLayout_5.addWidget(self.runTabFidCheckBoxFrame)


        self.horizontalLayout_4.addWidget(self.runTabFrame)

        self.tabWidget.addTab(self.runTab, "")
        self.magnetTab = QWidget()
        self.magnetTab.setObjectName(u"magnetTab")
        sizePolicy3.setHeightForWidth(self.magnetTab.sizePolicy().hasHeightForWidth())
        self.magnetTab.setSizePolicy(sizePolicy3)
        self.horizontalLayout_3 = QHBoxLayout(self.magnetTab)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.magnetTabMainFrame = QFrame(self.magnetTab)
        self.magnetTabMainFrame.setObjectName(u"magnetTabMainFrame")
        sizePolicy3.setHeightForWidth(self.magnetTabMainFrame.sizePolicy().hasHeightForWidth())
        self.magnetTabMainFrame.setSizePolicy(sizePolicy3)
        self.magnetTabMainFrame.setFrameShape(QFrame.StyledPanel)
        self.magnetTabMainFrame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.magnetTabMainFrame)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.magTabUpperFrame = QFrame(self.magnetTabMainFrame)
        self.magTabUpperFrame.setObjectName(u"magTabUpperFrame")
        self.magTabUpperFrame.setMaximumSize(QSize(16777215, 30))
        self.magTabUpperFrame.setFrameShape(QFrame.NoFrame)
        self.magTabUpperFrame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_9 = QHBoxLayout(self.magTabUpperFrame)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(-1, 0, -1, 0)
        self.magTabSetTSpinBox = QMagSpinBox(self.magTabUpperFrame)
        self.magTabSetTSpinBox.setObjectName(u"magTabSetTSpinBox")
        self.magTabSetTSpinBox.setDecimals(3)
        self.magTabSetTSpinBox.setMinimum(20.000000000000000)
        self.magTabSetTSpinBox.setMaximum(80.000000000000000)
        self.magTabSetTSpinBox.setSingleStep(0.100000000000000)
        self.magTabSetTSpinBox.setValue(30.000000000000000)

        self.horizontalLayout_9.addWidget(self.magTabSetTSpinBox)

        self.label_2 = QLabel(self.magTabUpperFrame)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_9.addWidget(self.label_2)

        self.horizontalSpacer_14 = QSpacerItem(13, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_14)

        self.magTabSetPushButton = QPushButton(self.magTabUpperFrame)
        self.magTabSetPushButton.setObjectName(u"magTabSetPushButton")

        self.horizontalLayout_9.addWidget(self.magTabSetPushButton)

        self.horizontalSpacer_15 = QSpacerItem(506, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_15)


        self.verticalLayout_4.addWidget(self.magTabUpperFrame)

        self.magTabPlotFrame = QFrame(self.magnetTabMainFrame)
        self.magTabPlotFrame.setObjectName(u"magTabPlotFrame")
        self.magTabPlotFrame.setFrameShape(QFrame.StyledPanel)
        self.magTabPlotFrame.setFrameShadow(QFrame.Raised)

        self.verticalLayout_4.addWidget(self.magTabPlotFrame)

        self.magTabLowerFrame = QFrame(self.magnetTabMainFrame)
        self.magTabLowerFrame.setObjectName(u"magTabLowerFrame")
        self.magTabLowerFrame.setMaximumSize(QSize(16777215, 30))
        self.magTabLowerFrame.setFrameShape(QFrame.NoFrame)
        self.magTabLowerFrame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_10 = QHBoxLayout(self.magTabLowerFrame)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(-1, 0, -1, 0)
        self.magTabPausePlotCheckBox = QCheckBox(self.magTabLowerFrame)
        self.magTabPausePlotCheckBox.setObjectName(u"magTabPausePlotCheckBox")

        self.horizontalLayout_10.addWidget(self.magTabPausePlotCheckBox)

        self.horizontalSpacer_17 = QSpacerItem(571, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_17)


        self.verticalLayout_4.addWidget(self.magTabLowerFrame)


        self.horizontalLayout_3.addWidget(self.magnetTabMainFrame)

        self.tabWidget.addTab(self.magnetTab, "")

        self.verticalLayout_3.addWidget(self.tabWidget)

        self.middleSplitter.addWidget(self.tabFrame)

        self.horizontalLayout_2.addWidget(self.middleSplitter)

        self.mainHsplitter.addWidget(self.upperFrame)
        self.textBrowserFrame = QFrame(self.mainHsplitter)
        self.textBrowserFrame.setObjectName(u"textBrowserFrame")
        self.textBrowserFrame.setEnabled(True)
        sizePolicy4.setHeightForWidth(self.textBrowserFrame.sizePolicy().hasHeightForWidth())
        self.textBrowserFrame.setSizePolicy(sizePolicy4)
        self.textBrowserFrame.setBaseSize(QSize(0, 0))
        self.textBrowserFrame.setFrameShape(QFrame.NoFrame)
        self.textBrowserFrame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.textBrowserFrame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.textEdit = QTextEdit(self.textBrowserFrame)
        self.textEdit.setObjectName(u"textEdit")
        sizePolicy3.setHeightForWidth(self.textEdit.sizePolicy().hasHeightForWidth())
        self.textEdit.setSizePolicy(sizePolicy3)
        font = QFont()
        font.setFamilies([u"Courier New"])
        self.textEdit.setFont(font)

        self.horizontalLayout.addWidget(self.textEdit)

        self.mainHsplitter.addWidget(self.textBrowserFrame)

        self.verticalLayout.addWidget(self.mainHsplitter)


        self.retranslateUi(mainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(mainWindow)
    # setupUi

    def retranslateUi(self, mainWindow):
        mainWindow.setWindowTitle(QCoreApplication.translate("mainWindow", u"Q Magnetics Spectrometer Control", None))
        self.runTabStartButton.setText(QCoreApplication.translate("mainWindow", u"Start", None))
        self.txFreqLabel.setText(QCoreApplication.translate("mainWindow", u"MHz", None))
        self.runTabTestCheckBox.setText(QCoreApplication.translate("mainWindow", u"Test Scan", None))
        self.label_9.setText(QCoreApplication.translate("mainWindow", u"Coarse", None))
        self.label_3.setText(QCoreApplication.translate("mainWindow", u"phi 1", None))
        self.label.setText(QCoreApplication.translate("mainWindow", u"phi 0", None))
        self.label_4.setText(QCoreApplication.translate("mainWindow", u"pivot", None))
        self.label_10.setText(QCoreApplication.translate("mainWindow", u"Fine", None))
        self.label_5.setText(QCoreApplication.translate("mainWindow", u"0 ppm", None))
        self.phasingCheckBox.setText(QCoreApplication.translate("mainWindow", u"Phasing", None))
        self.runTabFidCheckBox.setText(QCoreApplication.translate("mainWindow", u"FID", None))
        self.runTabHzCheckBox.setText(QCoreApplication.translate("mainWindow", u"Hz", None))
        self.runTabFullXButton.setText(QCoreApplication.translate("mainWindow", u"Full X", None))
        self.runTabFullYButton.setText(QCoreApplication.translate("mainWindow", u"Full Y", None))
        self.runMessageLabel.setText(QCoreApplication.translate("mainWindow", u"Run message", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.runTab), QCoreApplication.translate("mainWindow", u"Run", None))
        self.label_2.setText(QCoreApplication.translate("mainWindow", u"Set Point T (C)", None))
        self.magTabSetPushButton.setText(QCoreApplication.translate("mainWindow", u"Set Parameters", None))
        self.magTabPausePlotCheckBox.setText(QCoreApplication.translate("mainWindow", u"Pause Plot", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.magnetTab), QCoreApplication.translate("mainWindow", u"Magnet", None))
    # retranslateUi

