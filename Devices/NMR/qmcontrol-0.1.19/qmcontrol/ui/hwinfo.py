# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'hwinfo.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QFormLayout, QHBoxLayout, QLabel, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_HardwareInfo(object):
    def setupUi(self, HardwareInfo):
        if not HardwareInfo.objectName():
            HardwareInfo.setObjectName(u"HardwareInfo")
        HardwareInfo.resize(286, 267)
        self.verticalLayout_2 = QVBoxLayout(HardwareInfo)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(HardwareInfo)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.spectrometerLabel = QLabel(HardwareInfo)
        self.spectrometerLabel.setObjectName(u"spectrometerLabel")

        self.horizontalLayout.addWidget(self.spectrometerLabel)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.hwInfoBox = QWidget(HardwareInfo)
        self.hwInfoBox.setObjectName(u"hwInfoBox")
        self.formLayout = QFormLayout(self.hwInfoBox)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(0, 0, -1, 0)
        self.label_3 = QLabel(self.hwInfoBox)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_3)

        self.deviceId = QLabel(self.hwInfoBox)
        self.deviceId.setObjectName(u"deviceId")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.deviceId)

        self.label_4 = QLabel(self.hwInfoBox)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_4)

        self.serialNumber = QLabel(self.hwInfoBox)
        self.serialNumber.setObjectName(u"serialNumber")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.serialNumber)

        self.label_7 = QLabel(self.hwInfoBox)
        self.label_7.setObjectName(u"label_7")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_7)

        self.usbInterface = QLabel(self.hwInfoBox)
        self.usbInterface.setObjectName(u"usbInterface")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.usbInterface)

        self.label_9 = QLabel(self.hwInfoBox)
        self.label_9.setObjectName(u"label_9")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_9)

        self.usbSpeed = QLabel(self.hwInfoBox)
        self.usbSpeed.setObjectName(u"usbSpeed")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.usbSpeed)

        self.verticalSpacer = QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.formLayout.setItem(4, QFormLayout.FieldRole, self.verticalSpacer)

        self.label_11 = QLabel(self.hwInfoBox)
        self.label_11.setObjectName(u"label_11")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.label_11)

        self.okProductVersion = QLabel(self.hwInfoBox)
        self.okProductVersion.setObjectName(u"okProductVersion")

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.okProductVersion)

        self.label_5 = QLabel(self.hwInfoBox)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.label_5)

        self.okAPIVersion = QLabel(self.hwInfoBox)
        self.okAPIVersion.setObjectName(u"okAPIVersion")

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.okAPIVersion)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer_2 = QSpacerItem(20, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.label_12 = QLabel(self.hwInfoBox)
        self.label_12.setObjectName(u"label_12")

        self.verticalLayout.addWidget(self.label_12)


        self.formLayout.setLayout(4, QFormLayout.LabelRole, self.verticalLayout)


        self.verticalLayout_2.addWidget(self.hwInfoBox)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_3)

        self.buttonBox = QDialogButtonBox(HardwareInfo)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)

        self.verticalLayout_2.addWidget(self.buttonBox)


        self.retranslateUi(HardwareInfo)
        self.buttonBox.accepted.connect(HardwareInfo.accept)
        self.buttonBox.rejected.connect(HardwareInfo.reject)

        QMetaObject.connectSlotsByName(HardwareInfo)
    # setupUi

    def retranslateUi(self, HardwareInfo):
        HardwareInfo.setWindowTitle(QCoreApplication.translate("HardwareInfo", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("HardwareInfo", u"Spectrometer:", None))
        self.spectrometerLabel.setText(QCoreApplication.translate("HardwareInfo", u"Not Found", None))
        self.label_3.setText(QCoreApplication.translate("HardwareInfo", u"Device ID", None))
        self.deviceId.setText("")
        self.label_4.setText(QCoreApplication.translate("HardwareInfo", u"Serial Number", None))
        self.serialNumber.setText(QCoreApplication.translate("HardwareInfo", u"TextLabel", None))
        self.label_7.setText(QCoreApplication.translate("HardwareInfo", u"USB interface", None))
        self.usbInterface.setText(QCoreApplication.translate("HardwareInfo", u"TextLabel", None))
        self.label_9.setText(QCoreApplication.translate("HardwareInfo", u"USB speed", None))
        self.usbSpeed.setText(QCoreApplication.translate("HardwareInfo", u"TextLabel", None))
        self.label_11.setText(QCoreApplication.translate("HardwareInfo", u"Product Version", None))
        self.okProductVersion.setText(QCoreApplication.translate("HardwareInfo", u"TextLabel", None))
        self.label_5.setText(QCoreApplication.translate("HardwareInfo", u"API version", None))
        self.okAPIVersion.setText(QCoreApplication.translate("HardwareInfo", u"TextLabel", None))
        self.label_12.setText(QCoreApplication.translate("HardwareInfo", u"Opal Kelly Info", None))
    # retranslateUi

