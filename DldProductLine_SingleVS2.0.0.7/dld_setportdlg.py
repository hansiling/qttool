# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic
import serial.tools.list_ports
from dld_global import *
from dld_xml_operate import *
from dld_string_res import *

lang_set = get_xmlcfg_language()
if lang_set == 'cn':
    qtCreatorFile = "setportdlg.ui" # Enter file here.   
else:
    qtCreatorFile = "setportdlg_en.ui"
Ui_SetportDlg, QtBaseClass = uic.loadUiType(qtCreatorFile)
class dld_setportdlg(QDialog, Ui_SetportDlg):
    def __init__(self):
        QDialog.__init__(self)
        Ui_SetportDlg.__init__(self)
        self.setupUi(self)
        lang_set = get_xmlcfg_language()
        # self.tableWidget.setHorizontalHeaderLabels(['Port number', 'Serial port', 'Baud rate(bps)'])
        self.tableWidget.setHorizontalHeaderLabels([str_port_num[lang_set], str_com[lang_set]])
        self.Port_list = []
        self.Portnum = []
        self.LineCom = []
        self.Linebaud = []
        self.length = 0
        self.bt_addr_dis = None
        self.ble_addr_dis = None
        for i in range(0, 10):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(""))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(""))
            # self.tableWidget.setItem(i, 2, QTableWidgetItem(""))
            
        self.connect(self.autocheckButton, SIGNAL('clicked()'), self.autocheck)
        self.connect(self.OkButton, SIGNAL('clicked()'), self.Ok)
        self.connect(self.Canclebutton, SIGNAL('clicked()'), self.Cancle)

    def Ok(self):
        if len(self.Port_list) == 0:
            self.accept()
            return
        checked_port_num = 0
        loop_index = 0
        for loop_index in range(self.length):
            if self.Port_list[loop_index].isChecked() == True:
                checked_port_num += 1
        loop_index = 0
        while True:
            port_set = self.Port_list[loop_index]
            port_num = self.Portnum[loop_index]
            if port_set.isChecked() == False:
                self.Port_list.remove(port_set)
                self.Portnum.remove(port_num)
                if len(self.Port_list) == checked_port_num:
                    break
                loop_index = 0
            else:
                loop_index += 1
                if loop_index >= self.length:
                    break
        row_count = len(self.Port_list)
        if row_count == 0:
            self.accept()
            return
        settotalportnum(row_count)
        # app_path, ota_path = xml_getxmlcfg_burnpath()
        for i in range(row_count):
            setportNum(i, self.Portnum[i])
            setportUsed(i, self.Port_list[i].isChecked())
        self.accept()

    def Cancle(self):
        self.reject()  

    def autocheck(self):
        serial_list = []
        lang_set = get_xmlcfg_language()
        port_list = list(serial.tools.list_ports.comports())
        com_count = len(port_list)
        for i in range(0, com_count):
            port_n = port_list[i]
            try: #com i available ?
                s = serial.Serial(port_n[0])
                if int(port_n[0].split('COM')[1]) != 1:
                    serial_list.append(int(port_n[0].split('COM')[1]))
                s.close()
            except serial.SerialException:
                pass
            
        serial_list.sort()

        self.length = len(serial_list)

        #clear 
        self.Port_list = []
        self.LineCom = []
        self.Linebaud = []
        
        self.tableWidget.clear()
        self.tableWidget.setHorizontalHeaderLabels ([str_port_num[lang_set], str_com[lang_set]]) #, 'Baud rate(bps)'])
        for i in range(0, 10):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(""))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(""))
            # self.tableWidget.setItem(i, 2, QTableWidgetItem(""))
            
        for i in range(self.length):
            index = serial_list[i]
            self.Portnum.append(index)
            self.Port_list.append(QCheckBox('COM'))
            self.Port_list[i].setChecked(True)
            self.tableWidget.setCellWidget(i, 0, self.Port_list[i])

            self.LineCom.append(QLineEdit('%d'%(index)))
            self.LineCom[i].setEnabled(False)
            self.LineCom[i].setContextMenuPolicy(Qt.NoContextMenu)
            self.LineCom[i].setFocusPolicy(Qt.StrongFocus)
            self.tableWidget.setCellWidget(i, 1, self.LineCom[i])

            # self.Linebaud.append(QLineEdit('921600'))
            # self.Linebaud[i].setEnabled(True)
            # self.Linebaud[i].setContextMenuPolicy(Qt.NoContextMenu)
            # self.Linebaud[i].setFocusPolicy(Qt.StrongFocus)
            # self.tableWidget.setCellWidget(i, 2, self.Linebaud[i])


def get_port():
    serial_list = []
    port_list = list(serial.tools.list_ports.comports())
    com_count = len(port_list)
    for i in range(0, com_count):
        port_n = port_list[i]
        try:  # com i available ?
            s = serial.Serial(port_n[0])
            if int(port_n[0].split('COM')[1]) != 1:
                serial_list.append(int(port_n[0].split('COM')[1]))
            s.close()
        except serial.SerialException:
            pass

    serial_list.sort()
    length = len(serial_list)
    settotalportnum(length)
    for i in range(length):
        setportNum(i, serial_list[i])
        setportUsed(i, True)


