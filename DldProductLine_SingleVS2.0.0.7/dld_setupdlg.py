# -*- coding: utf-8 -*-
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
from PyQt4 import uic
import serial
import time
from dld_global import *

qtCreatorFile = "setupdlg.ui" # Enter file here.   
Ui_SetupDlg, QtBaseClass = uic.loadUiType(qtCreatorFile)
class dld_setupdlg(QDialog, Ui_SetupDlg):
    def __init__(self):
        QDialog.__init__(self)
        Ui_SetupDlg.__init__(self)
        self.setupUi(self)
        # self.rfilename = ""
        self.ffilename = ""
        # self.cfilename = ""
        self.cfgfile = None
        # self.connect(self.Rfile_browse, SIGNAL('clicked()'), self.openrfile)
        self.connect(self.Ffile_browse, SIGNAL('clicked()'), self.openffile)
        # self.connect(self.Cfile_browse, SIGNAL('clicked()'), self.opencfile)
        self.connect(self.pushButton, SIGNAL('clicked()'), self.Ok)
        self.connect(self.pushButton_2, SIGNAL('clicked()'), self.Cancle)
        self.initfile()
        
    def initfile(self):
        try:
            self.cfgfile = open('filecfg.dat', 'rb')
        except:
            return
        if self.cfgfile != None:
            # self.rfilename = (self.cfgfile.readline().split('\r\n')[0]).decode("utf-8")
            # self.lineEdit.setText(self.rfilename)
            self.ffilename = (self.cfgfile.readline().split('\r\n')[0]).decode("utf-8")
            self.lineEdit_2.setText(self.ffilename)
            # self.cfilename = (self.cfgfile.readline().split('\r\n')[0]).decode("utf-8")
            # self.lineEdit_3.setText(self.cfilename)
            setffilename(self.ffilename)
            self.cfgfile.close()
            
    def openrfile(self):
        pass
        # self.rfilename = QFileDialog.getOpenFileName(self, 'Select Ramrun File', '', '*.*')
        # self.lineEdit.setText(self.rfilename)

    def openffile(self):
        self.ffilename = QFileDialog.getOpenFileName(self, 'Select Flash File', '', '*.*')
        self.lineEdit_2.setText(self.ffilename)

#    def opencfile(self):
#        self.cfilename = QFileDialog.getOpenFileName(self, 'Select Config File', '', '*.*')
#        self.lineEdit_3.setText(self.cfilename)
        
    def savefilecfg(self):
        self.cfgfile = open('filecfg.dat', 'wb')
        # self.cfgfile.writelines(self.rfilename)
        # self.cfgfile.write('\r\n')
        self.cfgfile.writelines(self.ffilename)
        self.cfgfile.write('\r\n')
        # self.cfgfile.writelines(self.cfilename)
        # self.cfgfile.write('\r\n')
        self.cfgfile.close()
        
    def Ok(self):
        # self.rfilename = str(self.lineEdit.text())
        self.ffilename = str(self.lineEdit_2.text())
        # self.cfilename = str(self.lineEdit_3.text())
        setffilename(self.ffilename)    # g_ffilename == '' @ StartAll.
        self.savefilecfg()
        self.accept()

    def Cancle(self):
        self.reject()   


