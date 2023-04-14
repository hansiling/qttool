# -*- coding: utf-8 -*-
from PyQt4 import QtGui
from dld_productlinecfg import ProductlineCfg
from dld_xml_operate import *
from error_report import *
from dld_string_res import *

# tws弹窗
class dld_burning(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setStyleSheet("background-color:white")
        lang = get_xmlcfg_language()
        self.setWindowTitle(str_burning_method[lang])
        self.resize(250, 120)
        self.team_on = QRadioButton(self)
        self.team_on.setText(str_burning_team[lang])
        # self.light_on.move(10, 10)
        # self.light_on.toggled.connect(self.onOrOff)

        self.team_off = QRadioButton(self)
        self.team_off.setText(str_burning_not_team[lang])
        self.team_off.move(0, 30)
        if get_tws_on():
            self.team_on.setChecked(True)
        else:
            self.team_off.setChecked(True)

        # button
        self.button_ok = QtGui.QPushButton(str_ok[lang], self)
        self.button_ok.setMinimumSize(30, 23)
        self.button_ok.clicked.connect(self.ok)

        self.buttoncancle = QtGui.QPushButton(str_cancel[lang], self)
        self.buttoncancle.setMinimumSize(30, 23)
        self.buttoncancle.clicked.connect(self.handlecancle)
        #
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.button_ok.setFont(font)
        self.buttoncancle.setFont(font)
        # layout
        gridlayout = QtGui.QGridLayout()
        gridlayout.setSpacing(10)
        buttonlayout = QtGui.QHBoxLayout()
        buttonlayout.addWidget(self.button_ok)
        buttonlayout.addWidget(self.buttoncancle)
        buttonlayout.setSpacing(10)

        dlglayout = QtGui.QVBoxLayout()
        dlglayout.setContentsMargins(25, 25, 20, 20)
        dlglayout.addLayout(gridlayout)
        dlglayout.addStretch(30)
        dlglayout.addLayout(buttonlayout)
        self.setLayout(dlglayout)

    def ok(self):
        if self.team_on.isChecked():
            set_tws_on(True)
        else:
            set_tws_on(False)
        self.accept()

    def handlecancle(self):
        self.reject()
