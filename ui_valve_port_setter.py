# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'valve_port_setterwCIKMl.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(173, 106)
        self.widget = QWidget(Form)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(20, 10, 111, 41))
        self.widget.setMaximumSize(QSize(111, 41))
        self.label_2 = QLabel(self.widget)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(60, 0, 47, 13))
        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 0, 47, 13))
        self.Valve_2 = QSpinBox(self.widget)
        self.Valve_2.setObjectName(u"Valve_2")
        self.Valve_2.setGeometry(QRect(60, 10, 42, 22))
        self.Valve_2.setMinimum(1)
        self.Valve_2.setMaximum(8)
        self.Valve = QSpinBox(self.widget)
        self.Valve.setObjectName(u"Valve")
        self.Valve.setGeometry(QRect(10, 10, 42, 22))
        self.Valve.setMinimum(1)
        self.Valve.setMaximum(24)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Port", None))
        self.label.setText(QCoreApplication.translate("Form", u"Valve", None))
    # retranslateUi

