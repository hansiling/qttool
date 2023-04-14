# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtGui
import xml.etree.ElementTree as ET
#from dld_setupdlg import dld_setupdlg
from dld_productlinecfg import ProductlineCfg
from dld_xml_operate import *
from error_report import *
from dld_string_res import *



class dld_login(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.login_status = False
        self.setWindowIcon(QIcon('images/download.png'))
        lang = get_xmlcfg_language()
        self.setWindowTitle(str_login[lang])
        self.resize(250, 120)
        # text
        self.textName = QtGui.QLineEdit(self)
        self.textName.setMaximumWidth(190)
        self.textName.setMinimumHeight(20)
        self.textPass = QtGui.QLineEdit(self)
        self.textPass.setEchoMode(QtGui.QLineEdit.Password)
        self.textPass.setMaximumWidth(190)
        self.textPass.setMinimumHeight(20)
        self.labelName = QtGui.QLabel(str_username[lang])
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.labelName.setFont(font)

        self.labelPass = QtGui.QLabel(str_pwd[lang])
        self.labelPass.setFont(font)

        # button
        self.buttonlogin = QtGui.QPushButton(str_ok[lang], self)
        self.buttonlogin.setMinimumSize(30, 23)
        self.buttonlogin.clicked.connect(self.handlelogin)

        self.buttoncancle = QtGui.QPushButton(str_cancel[lang], self)
        self.buttoncancle.setMinimumSize(30, 23)
        self.buttoncancle.clicked.connect(self.handlecancle)

        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(True)
        self.buttonlogin.setFont(font)
        self.buttoncancle.setFont(font)
        # layout
        gridlayout = QtGui.QGridLayout()
        gridlayout.addWidget(self.labelName, 0, 0, 1, 1)
        gridlayout.addWidget(self.labelPass, 1, 0, 1, 1)
        gridlayout.addWidget(self.textName, 0, 1, 1, 3)
        gridlayout.addWidget(self.textPass, 1, 1, 1, 3)
        gridlayout.setSpacing(10)
        buttonlayout = QtGui.QHBoxLayout()
        buttonlayout.addWidget(self.buttonlogin)
        buttonlayout.addWidget(self.buttoncancle)
        buttonlayout.setSpacing(10)

        dlglayout = QtGui.QVBoxLayout()
        dlglayout.setContentsMargins(15, 15, 20, 20)
        dlglayout.addLayout(gridlayout)
        dlglayout.addStretch(20)
        dlglayout.addLayout(buttonlayout)
        self.setLayout(dlglayout)

    def handlelogin(self):
        doc = ET.parse('productline_cfg.xml')
        root = doc.getroot()
        usrinfo_list = []
        for i in root.findall('admin'):
             name = i.find('username').text
             password = i.find('password').text
             temp_node = [name, password]
             usrinfo_list.extend(temp_node)

        for i in range(0, len(usrinfo_list)/2, 1):
             if(self.textName.text() == usrinfo_list[2*i] and self.textPass.text() == usrinfo_list[2*i+1]):
                 self.login_status = True
                 break
             else:
                 self.login_status = False


        if(self.login_status == True):
            self.accept()
            self.handlesetfile()

        else:
            QtGui.QMessageBox.warning(self, 'Error', 'Bad username or password')

    def handlecancle(self):
         self.reject()

    def handlesetfile(self):
        # dlg = dld_setupdlg()
        parsetxt = xml_doc_parse()
        if parsetxt != 'xmlcfgok':
            error_dlg = ErrorReportDlg(parsetxt)
            error_dlg.exec_()
        else:
            prodctlinecfg_dlg = ProductlineCfg()
            prodctlinecfg_dlg.exec_()

