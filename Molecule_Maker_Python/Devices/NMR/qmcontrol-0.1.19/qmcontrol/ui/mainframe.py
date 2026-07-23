# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainframe.ui'
##
## Created by: Qt User Interface Compiler version 6.2.4
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QMainWindow, QMenu, QMenuBar,
    QSizePolicy, QStatusBar, QWidget)

from qmcontrol.qmcontrol import MainWindow

class Ui_MainFrame(object):
    def setupUi(self, MainFrame):
        if not MainFrame.objectName():
            MainFrame.setObjectName(u"MainFrame")
        MainFrame.resize(800, 600)
        self.actionQuit = QAction(MainFrame)
        self.actionQuit.setObjectName(u"actionQuit")
        self.actionHardware_Info = QAction(MainFrame)
        self.actionHardware_Info.setObjectName(u"actionHardware_Info")
        self.actionAbout = QAction(MainFrame)
        self.actionAbout.setObjectName(u"actionAbout")
        self.actionSave_Settings = QAction(MainFrame)
        self.actionSave_Settings.setObjectName(u"actionSave_Settings")
        self.qmcontrol = MainWindow(MainFrame)
        self.qmcontrol.setObjectName(u"qmcontrol")
        MainFrame.setCentralWidget(self.qmcontrol)
        self.menubar = QMenuBar(MainFrame)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        MainFrame.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainFrame)
        self.statusbar.setObjectName(u"statusbar")
        MainFrame.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionSave_Settings)
        self.menuFile.addAction(self.actionQuit)
        self.menuHelp.addAction(self.actionHardware_Info)
        self.menuHelp.addAction(self.actionAbout)

        self.retranslateUi(MainFrame)
        self.actionQuit.triggered.connect(MainFrame.close)

        QMetaObject.connectSlotsByName(MainFrame)
    # setupUi

    def retranslateUi(self, MainFrame):
        MainFrame.setWindowTitle(QCoreApplication.translate("MainFrame", u"MainWindow", None))
        self.actionQuit.setText(QCoreApplication.translate("MainFrame", u"Quit", None))
        self.actionHardware_Info.setText(QCoreApplication.translate("MainFrame", u"Hardware Info", None))
        self.actionAbout.setText(QCoreApplication.translate("MainFrame", u"About", None))
        self.actionSave_Settings.setText(QCoreApplication.translate("MainFrame", u"Save Settings", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainFrame", u"File", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainFrame", u"Help", None))
    # retranslateUi

