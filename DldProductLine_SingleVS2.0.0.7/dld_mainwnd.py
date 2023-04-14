# -*- coding: utf-8 -*-
import sys
import os
import struct
import operator
import serial
import thread

import serial
from PyQt4 import QtGui
from PyQt4 import uic
from multiprocessing import Pipe
from threading import Timer
from dld_aboutdlg import dld_aboutdlg
from dld_burning import dld_burning
from dld_setportdlg import dld_setportdlg, get_port
from dld_subprocess import DldProcess
from dld_monitorstep import *
from dld_xml_operate import *
from dld_global import *
from dld_login import dld_login
from dld_productlinecfg import ProductlineCfg
from error_report import *
from win32api import GetSystemMetrics
import md5
import shutil
from dld_string_res import *
from cfg_json_parse import *

lang_set = get_xmlcfg_language()
reload(sys)
sys.setdefaultencoding('utf8')
comFlag = ''

DEFAULT_STYLE = """
QProgressBar{
    border: 2px solid grey;
    border-radius: 5px;
    text-align: center
}
QProgressBar::chunk {
    background-color: lightblue;
    width: 10px;
    margin: 1px;
}
"""

COMPLETED_STYLE1 = """
QProgressBar{
    border: 2px solid grey;
    border-radius: 5px;
    text-align: center
}
QProgressBar::chunk {
    background-color: #FFFF00;
    width: 10px;
    margin: 1px;
}
"""
COMPLETED_STYLE = """
QProgressBar{
    border: 2px solid grey;
    border-radius: 5px;
    text-align: center
}
QProgressBar::chunk {
    background-color: #00FF00;
    width: 10px;
    margin: 1px;
}
"""


def gui_getopt(job):
    index = job['index']
    return opt_array[index]


def gui_getprogressbar(job):
    global bar_array
    index = job['index']
    return bar_array[index]


def gui_getcalibvalue(job):
    global calib_value_array
    index = job['index']
    return calib_value_array[index]


def getSTATE(job):
    global STATE_array
    index = job['index']
    return STATE_array[index]


def gui_get_btaddr_display(job):
    global g_btaddr_display_array
    index = job['index']
    if index != -1:
        return g_btaddr_display_array[index]
    return None


def gui_get_bleaddr_display(job):
    global g_bleaddr_display_array
    index = job['index']
    if index != -1:
        return g_bleaddr_display_array[index]
    return None


def gui_getTIME(job):
    index = job['index']
    return TIME_array[index]


def gui_getmonitorthrd(job):
    global g_monitorthrd_array
    index = job['monitorthrdindex']
    return g_monitorthrd_array[index]


class XProgressBar(QProgressBar):
    def __init__(self, parent=None):
        QProgressBar.__init__(self, parent)
        self.setStyleSheet(DEFAULT_STYLE)
        self.step = 0

    def setValue(self, value):
        QProgressBar.setValue(self, value)
        if value < self.maximum():
            self.setStyleSheet(DEFAULT_STYLE)
        else:
            encrypt_on = xml_encrypt_is_on()
            if encrypt_on is True:
                self.setStyleSheet(COMPLETED_STYLE1)
            else:

                self.setStyleSheet(COMPLETED_STYLE)


class BesDldMainWnd(QMainWindow):
    bar_signal = pyqtSignal(object)
    calibvalue_signal = pyqtSignal(object)
    dldtime_signal = pyqtSignal(object)
    status_signal = pyqtSignal(object)
    btaddr_display_signal = pyqtSignal(object)
    bleaddr_display_signal = pyqtSignal(object)
    dld_succeed_times = 0
    dld_failure_times = 0
    ramrun_path = ''
    flshbin_path = ''
    flshbootbin_path = ''
    Port_list = []
    # Port_list = updateport()
    config_info_display = []
    app_switch = False
    otaboot_switch = False

    def __init__(self, parent=None):
        lang_set = get_xmlcfg_language()
        QMainWindow.__init__(self)
        super(BesDldMainWnd, self).__init__(parent)
        if cfg_as_updatetool() is True:
            self.setWindowTitle(str_updatetool_title[lang_set])
            encrypt_on = False
        else:
            encrypt_on = xml_encrypt_is_on()
            if encrypt_on is True:
                self.setWindowTitle(str_dldtool_encrypt_title[lang_set])
            else:
                self.setWindowTitle(str_dldtool_title[lang_set])
        self.setWindowIcon(QIcon('images/download.png'))

        self.menu = self.menuBar()
        self.operate_menu = self.menu.addMenu('&Operate')
        self.actionStart_all_menu = self.operate_menu.addAction('&Start All')
        self.actionStart_all_menu.setIcon(QIcon('images/start.png'))
        self.connect(self.actionStart_all_menu, SIGNAL("triggered()"), self.StartAll)

        self.actionStop_all_menu = self.operate_menu.addAction('&Stop All')
        self.actionStop_all_menu.setIcon(QIcon('images/stop.png'))
        self.connect(self.actionStop_all_menu, SIGNAL("triggered()"), self.StopAll)

        self.actionQuit = self.operate_menu.addAction('&Exit')
        self.actionQuit.setIcon(QIcon('images/quit.png'))
        self.connect(self.actionQuit, SIGNAL("triggered()"), self.close)

        # This is another menu 'Config'
        self.config_menu = self.menu.addMenu('&Config')
        self.actionPort_Setup_menu = self.config_menu.addAction('&Port Config')
        self.actionPort_Setup_menu.setIcon(QIcon('images/fileset.png'))
        self.connect(self.actionPort_Setup_menu, SIGNAL("triggered()"), self.set_port_dlg)

        # self.action_manager_menu = self.config_menu.addAction('&Bin Path Config')
        # self.action_manager_menu.setIcon(QIcon('images/setup.png'))
        # self.connect(self.action_manager_menu,SIGNAL("triggered()"), self.login)

        # This is another menu 'Help'
        self.help_menu = self.menu.addMenu('&Help')
        self.actionUser_manual = self.help_menu.addAction('&User Manual')
        self.actionUser_manual.setIcon(QIcon('images/help.png'))
        self.connect(self.actionUser_manual, SIGNAL("triggered()"), self.manual)

        self.actionAbout = self.help_menu.addAction('&About')
        self.actionAbout.setIcon(QIcon('images/about.png'))
        self.connect(self.actionAbout, SIGNAL("triggered()"), self.about)

        self.statusBar()
        # Now set the toolbar
        self.toolbar1 = self.addToolBar('Start All')
        self.actionStart_all = self.toolbar1.addAction('&Start All')
        self.actionStart_all.setIcon(QIcon('images/start.png'))
        self.connect(self.actionStart_all, SIGNAL("triggered()"), self.StartAll)

        self.toolbar2 = self.addToolBar('Stop All')
        self.actionStop_all = self.toolbar2.addAction('&Stop All')
        self.actionStop_all.setIcon(QIcon('images/stop.png'))
        self.connect(self.actionStop_all, SIGNAL("triggered()"), self.StopAll)

        self.toolbar3 = self.addToolBar('Exit')
        self.actionQuit = self.toolbar3.addAction('&Exit')
        self.actionQuit.setIcon(QIcon('images/quit.png'))
        self.connect(self.actionQuit, SIGNAL("triggered()"), self.close)

        self.toolbar4 = self.addToolBar('Port Config')
        self.actionPort_Setup = self.toolbar4.addAction('&Port Config')
        self.actionPort_Setup.setIcon(QIcon('images/fileset.png'))
        self.connect(self.actionPort_Setup, SIGNAL("triggered()"), self.set_port_dlg)

        self.toolbar5 = self.addToolBar('Burning Method')
        self.action_burning = self.toolbar5.addAction('&Burning Method')
        self.action_burning.setIcon(QIcon('images/help.png'))
        self.connect(self.action_burning, SIGNAL("triggered()"), self.burning)

        # Set the tablewidget
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(8)
        self.tableWidget.setRowCount(8)
        self.tableWidget.setMinimumSize(100, 70)
        self.tableWidget.setMinimumHeight(10)
        self.tableWidget.setMinimumWidth(200)
        self.tableWidget.setAutoFillBackground(True)
        self.tableWidget.setUpdatesEnabled(True)

        widget0 = QWidget()
        layout0 = QVBoxLayout()
        layout0.addWidget(self.tableWidget)
        widget0.setLayout(layout0)
        widget0.setUpdatesEnabled(True)

        dock1 = QDockWidget('', self)
        dock1.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock1.setWidget(widget0)
        dock1.setFeatures(QDockWidget.NoDockWidgetFeatures)
        dock1.setMinimumHeight(400)
        self.addDockWidget(Qt.RightDockWidgetArea, dock1)

        self.txtbrws_cfg_info = QTextBrowser()
        self.txtbrws_cfg_info.setEnabled(False)
        self.txtbrws_cfg_info.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        dock2 = QDockWidget('', self)
        dock2.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock2.setWidget(self.txtbrws_cfg_info)
        dock2.setFeatures(QDockWidget.NoDockWidgetFeatures)

        self.addDockWidget(Qt.RightDockWidgetArea, dock2)

        self.txtbrws_result_info = QTextBrowser()
        self.txtbrws_result_info.setEnabled(False)
        self.txtbrws_result_info.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        # palette1 = QtGui.QPalette()
        # palette1.setColor(self.backgroundRole(), QColor(255,0,0))
        if encrypt_on is True:
            font = QtGui.QFont()
            font.setBold(True)
            font.setPointSize(40)

            self.encrypt_flag = QTextBrowser()
            self.encrypt_flag.setTextColor(QColor(255, 0, 0))
            self.encrypt_flag.setText(" encrypt mode!")
            self.encrypt_flag.setFont(font)

            self.encrypt_flag.setBackgroundRole(QPalette.ColorRole)
            self.encrypt_flag.setAutoFillBackground(True)
            self.encrypt_flag.setEnabled(False)
            self.encrypt_flag.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        self.push_btn_clear = QPushButton('ClearCount')
        widget = QWidget()

        bottom_layout = QHBoxLayout()
        if encrypt_on is True:
            bottom_layout.addWidget(self.encrypt_flag)
        bottom_layout.addWidget(self.txtbrws_result_info)
        bottom_layout.addWidget(self.push_btn_clear)
        widget.setLayout(bottom_layout)

        dock3 = QDockWidget('', self)
        dock3.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock3.setWidget(widget)
        dock3.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(Qt.RightDockWidgetArea, dock3)

        self.show_productline_cfg_info()
        self.show_dld_result_info()

        self.bar_signal.connect(self.slot_progressbar_update)
        self.calibvalue_signal.connect(self.slot_calibvalue_update)
        self.dldtime_signal.connect(self.slot_dldtime_update)
        self.status_signal.connect(self.slot_status_update)
        self.btaddr_display_signal.connect(self.slot_btaddr_display)
        self.bleaddr_display_signal.connect(self.slot_bleaddr_display)
        self.push_btn_clear.clicked.connect(self.slot_reset_dldresult)
        self.screenwidth = GetSystemMetrics(0)
        self.screenheight = GetSystemMetrics(1)

        self.setTableContents()
        for index in range(0, 8, 1):
            self.dldpipecreate(JOBS[index])
        self.setMinimumWidth(1000)
        self.setMinimumHeight(750)
        get_port()
        self.updateport()
        # tws开关打开
        set_tws_on(True)


    def getFileCRCText(self, _path):
        crc_ret = getFileCRC(_path)
        if crc_ret != 0:
            crc_text = '%08x' % (crc_ret & 0xFFFFFFFF)
            return crc_text
        return 'invalid!'

    def verify_bin_crc(self):
        cfg_app_switch = xml_get_app_switch()
        if cfg_app_switch == '1':
            cfg_verify_crc_switch = xml_get_verifycrc1_switch()
            if cfg_verify_crc_switch == '0':
                return 'success'
            cfg_verify_crc1, cfg_verify_crc2 = xml_get_verify_text()
            if len(cfg_verify_crc1) != 8:
                return 'pls configure verify crc.'
            binfile, otafile = xml_getxmlcfg_burnpath()
            crc_text = self.getFileCRCText(binfile)
            if crc_text.lower() != cfg_verify_crc1.lower():
                return 'crc error'

        cfg_otaboot_switch = xml_get_otaboot_switch()
        if cfg_otaboot_switch == '1':
            cfg_verify_crc_switch = xml_get_verifycrc2_switch()
            if cfg_verify_crc_switch == '0':
                return 'success'
            cfg_verify_crc1, cfg_verify_crc2 = xml_get_verify_text()
            if len(cfg_verify_crc2) != 8:
                return 'pls configure verify crc.'
            binfile, otafile = xml_getxmlcfg_burnpath()
            crc_text = self.getFileCRCText(otafile)
            if crc_text.lower() != cfg_verify_crc2.lower():
                return 'crc error'
        return 'success'

    def verify_bin_md5(self):
        cfg_md5_text = xml_get_verify_text()
        if len(cfg_md5_text) != 32:
            return 'pls configure verify md5.'
        burn_dir = 'burn\\'
        dir_exist_flag = os.path.exists(burn_dir)
        if dir_exist_flag == False:
            return 'pls paste bin(s) under dir burn'
        bin_list = os.listdir(burn_dir)
        for bin_burn in bin_list:
            ext = os.path.splitext(bin_burn)
            if ext[1] == '.bin':
                with open(burn_dir + bin_burn, 'rb') as f:
                    md5_text = md5.new(f.read()).hexdigest()
                    if md5_text == cfg_md5_text:
                        return 'success'
        return 'failure'

    def bes_dldtool_binpath_load(self):
        lang_set = get_xmlcfg_language()
        # verify_ret = self.verify_bin_md5()
        verify_ret = self.verify_bin_crc()
        if verify_ret != 'success':
            return str_crc_verify_failure[lang_set]

        self.flshbin_path, self.flshbootbin_path = xml_getxmlcfg_burnpath()
        if xml_get_app_switch() == '1':
            self.app_switch = True
            flshbin_exist = os.path.exists(self.flshbin_path)
            if flshbin_exist is not True:
                return 'APP file is not exist!'
        else:
            self.app_switch = False

        if xml_get_otaboot_switch() == '1':
            self.otaboot_switch = True
            flshbootbin_exist = os.path.exists(self.flshbootbin_path)
            if flshbootbin_exist is not True:
                return 'OTA BOOT file is not exist!'
        else:
            self.otaboot_switch = False
        chip_version, customer1_enable, custom_bin1_path, customer1_addr, customer2_enable, custom_bin2_path, customer2_addr, customer3_enable, custom_bin3_path, customer3_addr, customer4_enable, custom_bin4_path, customer4_addr = xml_get_customer_info()
        custom_bin1 = ''
        custom_bin2 = ''
        custom_bin3 = ''
        custom_bin4 = ''
        if custom_bin1_path != None:
            custom_bin1 = str(custom_bin1_path)
        if custom_bin2_path != None:
            custom_bin2 = str(custom_bin2_path)
        if custom_bin3_path != None:
            custom_bin3 = str(custom_bin3_path)
        if custom_bin4_path != None:
            custom_bin4 = str(custom_bin4_path)

        erase_en, erase_len, erase_addr = get_erase_info()

        if self.app_switch == False and self.otaboot_switch == False \
                and custom_bin1 == '' and custom_bin2 == '' \
                and custom_bin3 == '' and custom_bin4 == '' and erase_en == False:
            return "Please choose at least a file!"
        if self.app_switch == True:
            app_bin = self.flshbin_path
        '''if self.app_switch == False and self.otaboot_switch == False:
            self.ramrun_path = os.getcwd() + '\\programmer'+str(chip_version)+'.bin'
            get_dlddll().set_chiptype_value(chip_version)
        else:       
            if self.app_switch == True:
               app_bin = self.flshbin_path
            elif self.otaboot_switch == True:
               app_bin = self.flshbootbin_path                       
            self.ramrun_path = get_programmer_bin_path()
        ramrun_exist = os.path.exists(self.ramrun_path)
        if ramrun_exist is not True:
            return 'programmer.bin not exist!'
            '''
        return 'LOADOK'

    def dldpipecreate(self, job):
        if (job['parentconn'] is -1 and job['childconn'] is -1):
            job['parentconn'], job['childconn'] = Pipe()
        if (job['parentconn4dldstop'] is -1 and job['childconn4dldstop'] is -1):
            job['parentconn4dldstop'], job['childconn4dldstop'] = Pipe()
        if (job['pconn4dldstart'] is -1 and job['cconn4dldstart'] is -1):
            job['pconn4dldstart'], job['cconn4dldstart'] = Pipe()

    def cleandldpipe(self, job):
        if (job['parentconn'] is not -1):
            job['parentconn'].close()
            job['parentconn'] = -1
        if (job['childconn'] is not -1):
            job['childconn'].close()
            job['childconn'] = -1
        if (job['parentconn4dldstop'] is not -1):
            job['parentconn4dldstop'].close()
            job['parentconn4dldstop'] = -1
        if (job['childconn4dldstop'] is not -1):
            job['childconn4dldstop'].close()
            job['childconn4dldstop'] = -1
        if (job['pconn4dldstart'] is not -1):
            job['pconn4dldstart'].close()
            job['pconn4dldstart'] = -1
        if (job['cconn4dldstart'] is not -1):
            job['cconn4dldstart'].close()
            job['cconn4dldstart'] = -1

    def dldfailure_gui_update(self, job):
        lang_set = get_xmlcfg_language()
        status = getSTATE(job)
        status.setText(str_failure[lang_set])
        palette = status.palette()
        palette.setColor(status.backgroundRole(), QColor(255, 0, 0))
        status.setPalette(palette)

    def dldsuccess_gui_update(self, job):
        lang_set = get_xmlcfg_language()
        status = getSTATE(job)
        status.setText(str_success[lang_set])
        palette = status.palette()
        palette.setColor(status.backgroundRole(), QColor(0, 255, 0))
        status.setPalette(palette)

    def slot_progressbar_update(self, param):
        job = param[0]
        val = param[1]

        progressbar = gui_getprogressbar(job)
        progressbar.setValue(val)

    def slot_calibvalue_update(self, param):
        job = param[0]
        val = param[1]
        calibdisplay = gui_getcalibvalue(job)
        calibdisplay.setText(str(val))

    def slot_dldtime_update(self, param):
        job = param[0]
        timedisplay = param[1]
        gui_time = gui_getTIME(job)
        gui_time.display(timedisplay)

    def slot_status_update(self, param):
        lang_set = get_xmlcfg_language()
        job = param[0]
        string_display = param[1]
        guistatus = getSTATE(job)

        if string_display == 'Idle':
            guistatus.setText(str_idle[lang_set])
            temp_palette = guistatus.palette()
            temp_palette.setColor(guistatus.backgroundRole(), QColor(222, 222, 222))
            guistatus.setPalette(temp_palette)
        elif string_display == 'Burn Succeed':
            guistatus.setText(str_success[lang_set])
            temp_palette = guistatus.palette()
            temp_palette.setColor(guistatus.backgroundRole(), QColor(0, 255, 0))
            guistatus.setPalette(temp_palette)
        elif string_display == 'Test Succeed':
            guistatus.setText(str_success[lang_set])
            temp_palette = guistatus.palette()
            temp_palette.setColor(guistatus.backgroundRole(), QColor(0, 255, 0))
            guistatus.setPalette(temp_palette)
        elif string_display == 'Valid':
            self.slot_dld_result_display_update('succeed')
            self.bes_dldtool_ajob_stop(None, job)
            stopall_t = Timer(3, self.btn_allstart_enable)
            stopall_t.start()
            set_tws_on(True)
        elif string_display == 'Downloading':
            guistatus.setText(str_burning[lang_set])
            temp_palette = guistatus.palette()
            temp_palette.setColor(guistatus.backgroundRole(), QColor(255, 255, 0))
            guistatus.setPalette(temp_palette)
        elif string_display == 'Testing':
            guistatus.setText(str_testing[lang_set])
            temp_palette = guistatus.palette()
            temp_palette.setColor(guistatus.backgroundRole(), QColor(255, 255, 0))
            guistatus.setPalette(temp_palette)
        elif string_display == 'password_incorrect':
            guistatus.setText(str_key_format_not_supported[lang_set])
            temp_palette = guistatus.palette()
            temp_palette.setColor(guistatus.backgroundRole(), QColor(255, 0, 0))
            guistatus.setPalette(temp_palette)
        elif string_display == 'Failure':
            if param[2] & 0xffff0000 == 0xab0000:
                guistatus.setText(str_failure[lang_set])
                temp_palette = guistatus.palette()
                temp_palette.setColor(guistatus.backgroundRole(), QColor(255, 0, 0))
                guistatus.setPalette(temp_palette)
        elif string_display == 'Invalid':
            if job['stauts'] != 'stop':
                if param[2] & 0xffff0000 == 0xab0000:
                    guistatus.setText(str_failure[lang_set])
                    self.slot_dld_result_display_update('failure')
                    self.dldfailure_gui_update(job)
                    temp_palette = guistatus.palette()
                    temp_palette.setColor(guistatus.backgroundRole(), QColor(255, 0, 0))
                    guistatus.setPalette(temp_palette)
            else:
                guistatus.setText(str_stop[lang_set])
                temp_palette = guistatus.palette()
                temp_palette.setColor(guistatus.backgroundRole(), QColor(222, 222, 222))
                guistatus.setPalette(temp_palette)
        elif string_display == 'Full':
            self.dld_error_report('Burn all completed, please close tools.')
            self.close()
        else:
            pass

    def slot_btaddr_display(self, param):
        job = param[0]
        gui_btaddr = gui_get_btaddr_display(job)
        if param[1] != None:
            gui_btaddr.setText(param[1])

    def slot_bleaddr_display(self, param):
        job = param[0]
        gui_bleaddr = gui_get_bleaddr_display(job)
        if param[1] != None:
            gui_bleaddr.setText(param[1])

    def show_dld_result_info(self):
        lang_set = get_xmlcfg_language()
        count_complete, count_failure = get_dld_result()
        display_text = str_complete_count[lang_set] + str(count_complete) + '\n' + str_failure_count[lang_set] + str(
            count_failure)
        if get_max_burn_num_flag() == True:
            if xml_get_max_burn_num_enable():
                rest_num = get_rest_burn_num()
                total_num = rest_num + count_complete
                display_text = display_text + '\n' + 'Remaining Count:' + str(
                    rest_num) + '\n' + 'Max Burn Count:' + str(total_num)
        self.txtbrws_result_info.setTextColor(QColor(255, 0, 255))
        self.txtbrws_result_info.setText(display_text.decode("utf-8"))

    def slot_dld_result_display_update(self, result_str):
        if result_str == 'succeed':
            dld_complete_count_increase()
        elif result_str == 'failure':
            dld_failure_count_increase()
        self.show_dld_result_info()

    def slot_reset_dldresult(self):
        lang_set = get_xmlcfg_language()
        reset_dld_result()
        restore_dldresult_to_xml()
        count_complete, count_failure = get_dld_result()
        display_text = str_complete_count[lang_set] + str(count_complete) + '\n' + str_failure_count[lang_set] + str(
            count_failure)
        if get_max_burn_num_flag() == True:
            if xml_get_max_burn_num_enable():
                rest_num = get_rest_burn_num()
                total_num = rest_num + count_complete
                display_text = display_text + '\n' + 'Remaining Count:' + str(
                    rest_num) + '\n' + 'Max Burn Count:' + str(total_num)
        self.txtbrws_result_info.setTextColor(QColor(255, 0, 255))
        self.txtbrws_result_info.setText(display_text.decode("utf-8"))

    def setTableContents(self):
        lang_set = get_xmlcfg_language()
        self.tableWidget.setHorizontalHeaderLabels([str_port_num[lang_set], str_com[lang_set], str_progress[lang_set], \
                                                    str_bt_addr[lang_set], str_ble_addr[lang_set], str_status[lang_set],
                                                    str_elapse[lang_set], \
                                                    str_calib_value[lang_set]])
        self.tableWidget.setColumnWidth(0, self.width() / 12)
        self.tableWidget.setColumnWidth(1, self.width() * 1 / 12)
        self.tableWidget.setColumnWidth(2, self.width() * 7.5 / 12)
        self.tableWidget.setColumnWidth(3, self.width() * 2 / 12)
        self.tableWidget.setColumnWidth(4, self.width() * 2 / 12)
        self.tableWidget.setColumnWidth(5, self.width() * 1.5 / 12)
        self.tableWidget.setColumnWidth(6, self.width() * 1.5 / 12)
        self.tableWidget.setColumnWidth(7, self.width() * 1 / 12)
        for i in range(8):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(""))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(""))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(""))
            self.tableWidget.setItem(i, 3, QTableWidgetItem(""))
            self.tableWidget.setItem(i, 4, QTableWidgetItem(""))
            self.tableWidget.setItem(i, 5, QTableWidgetItem(""))
            self.tableWidget.setItem(i, 6, QTableWidgetItem(""))
            self.tableWidget.setItem(i, 7, QTableWidgetItem(""))
            self.tableWidget.setRowHeight(i, self.height() / 12)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.setGeometry(1, 1, self.width() * 8 / 10 - 5, self.height() / 2.5)
        self.txtbrws_cfg_info.setGeometry(1, 2 + self.height() / 2.5, self.width() * 8 / 10, self.height() / 12)
        self.txtbrws_result_info.setGeometry(1, 3 + self.height() / 2.5 + self.height() / 14,
                                             self.width() * 7 / 10 - 10, self.height() / 12)
        self.push_btn_clear.setGeometry(self.width() * 7 / 10 - 11, 3 + self.height() / 2.5 + self.height() / 14,
                                        self.width() / 10 + 11, self.height() / 12)

    def about(self):
        dlg = dld_aboutdlg()
        dlg.exec_()

    def manual(self):
        filename = os.getcwd() + '\\user_manual.pdf'
        os.startfile(filename)

    def show_productline_cfg_info(self):
        lang_set = get_xmlcfg_language()
        update_sector_flag = xml_get_update_sector_enable()
        path_text_1, path_text_2 = xml_getxmlcfg_burnpath()
        burnStep = '\nBurning steps:' \
                   + '\nStep1:Check whether there are only two serial ports on the left and right ears. Otherwise, select the correct serial ports.' \
                   + '\nStep2:Before clicking the "Run" button, close and open the charging case lid for 3 times manually(the final state is open the lid).' \
                   + '\nStep3:Click the "Run" button to start the program.'\
                   + '\nStep4:After Status turn to "Idle", close and open the lid once manually(the final state is open cover).'\
                   + '\nStep5:After Status turn to "success", it is necessary to close and open the lid for reset.'
        if path_text_1 == None:
            path_text_1 = ''
        if path_text_2 == None:
            path_text_2 = ''
        if update_sector_flag == '1':
            # self.config_info_display = str_bin1_path[lang_set] + path_text_1 + '\n' + str_bin2_path[lang_set] + path_text_2 + '\n'+ \
            #                             str_bt_name[lang_set] + xml_get_dev_localbtname()
            self.config_info_display = str_bin1_path[lang_set] + path_text_1 + burnStep
        else:
            # self.config_info_display = str_bin1_path[lang_set] + path_text_1 + '\n' + str_bin2_path[lang_set] + path_text_2 + '\n'
            self.config_info_display = str_bin1_path[lang_set] + path_text_1 + burnStep
        # self.txtbrws_cfg_info.setTextColor(QColor(255, 0, 0))
        self.txtbrws_cfg_info.setText(self.config_info_display.decode("utf-8"))

    def burning(self):
        dlg = dld_burning()
        logret = dlg.exec_()
        if logret == 1:
            self.show_productline_cfg_info()

    def login(self):
        dlg = dld_login()
        logret = dlg.exec_()
        if logret == 1:
            self.show_productline_cfg_info()

    def set_port_dlg(self):
        dlg = dld_setportdlg()
        if dlg.exec_():
            self.updateport()

    def dld_error_report(self, err_text):
        error_dlg = ErrorReportDlg(err_text)
        error_dlg.exec_()

    def updateport(self):
        global bar_array, STATE_array, TIME_array, mainpmonitor_semas, g_btaddr_display_array, g_bleaddr_display_array, calib_value_array
        lang_set = get_xmlcfg_language()
        self.tableWidget.clear()
        self.tableWidget.setHorizontalHeaderLabels([str_port_num[lang_set], str_com[lang_set], str_progress[lang_set], \
                                                    str_bt_addr[lang_set], str_ble_addr[lang_set], str_status[lang_set],
                                                    str_elapse[lang_set], \
                                                    str_calib_value[lang_set]])
        for i in range(8):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(""))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(""))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(""))
            self.tableWidget.setItem(i, 3, QTableWidgetItem(""))
            self.tableWidget.setItem(i, 4, QTableWidgetItem(""))
            self.tableWidget.setItem(i, 5, QTableWidgetItem(""))
            self.tableWidget.setItem(i, 6, QTableWidgetItem(""))
            self.tableWidget.setItem(i, 7, QTableWidgetItem(""))

        self.Port_list = []
        self.LineCom = []

        bar_array = []
        STATE_array = []
        TIME_array = []
        calib_value_array = []

        i = 0
        for i, d in enumerate(JOBS):
            if i >= gettotalportnum():
                break
            index = getportNum(i)
            d["portnum"] = index
            index_str = ' %d' % index
            self.Port_list.append(QCheckBox(index_str.decode("utf-8")))
            self.Port_list[i].setChecked(getportUsed(i))
            self.Port_list[i].setEnabled(False)
            self.tableWidget.setCellWidget(i, 0, self.Port_list[i])

            self.LineCom.append(QLineEdit('COM%d' % (index)))
            self.LineCom[i].setEnabled(False)
            self.LineCom[i].setContextMenuPolicy(Qt.NoContextMenu)
            self.LineCom[i].setFocusPolicy(Qt.StrongFocus)
            self.tableWidget.setCellWidget(i, 1, self.LineCom[i])

            bar = XProgressBar(self)
            bar_array.append(bar)
            self.tableWidget.setCellWidget(i, 2, bar)
            bar.setValue(0)

            Btaddress = QLineEdit('00:00:00:00:00:00')
            Btaddress.setEnabled(False)
            # Btaddress.setAutoFillBackground(True)
            g_btaddr_display_array[i] = Btaddress
            self.tableWidget.setCellWidget(i, 3, Btaddress)

            Bleaddress = QLineEdit('00:00:00:00:00:00')
            Bleaddress.setEnabled(False)
            g_bleaddr_display_array[i] = Bleaddress
            # Bleaddress.setAutoFillBackground(True)
            self.tableWidget.setCellWidget(i, 4, Bleaddress)

            State = QLineEdit(str_closed[lang_set])
            State.setEnabled(False)
            State.setContextMenuPolicy(Qt.NoContextMenu)
            State.setFocusPolicy(Qt.StrongFocus)
            State.setAutoFillBackground(True)
            p = State.palette()
            p.setColor(State.backgroundRole(), QColor(255, 255, 255))
            State.setPalette(p)
            STATE_array.append(State)

            self.tableWidget.setCellWidget(i, 5, State)

            Time = QLCDNumber()
            Time.setSegmentStyle(QLCDNumber.Filled)
            Time.display("00:00")
            TIME_array.append(Time)
            self.tableWidget.setCellWidget(i, 6, Time)

            Calib_lineedit = QLineEdit('')
            Calib_lineedit.setEnabled(False)
            calib_value_array.append(Calib_lineedit)
            self.tableWidget.setCellWidget(i, 7, Calib_lineedit)

    def btn_stopall_enable(self):
        QAction.setEnabled(self.actionStop_all, True)
        QAction.setEnabled(self.actionStop_all_menu, True)

    def StartAll(self):
        global JOBS
        list_len = len(self.Port_list)
        if list_len == 0:
            return
        if get_max_burn_num_flag() == True:
            if xml_get_max_burn_num_enable():
                rest_burn_num = get_rest_burn_num()
                if rest_burn_num <= 0:
                    self.dld_error_report('Burn all completed, please close tools.')
                    self.close()
                    return
        load_text = self.bes_dldtool_binpath_load()  # keep self.ramrun_path and self.flshbin_path and self.flshbootbin_path the same as cfg file.
        if load_text != 'LOADOK':
            self.dld_error_report(load_text)
            return
        for index in range(0, list_len, 1):
            if self.Port_list[index].isChecked():
                # JOBS[index]['stauts'] = 'tws'
                # self.status_signal.emit([JOBS[index], 'TWS'])

                if JOBS[index]['stauts'] is 'run':
                    self.status_signal.emit([JOBS[index], 'Idle'])
                if JOBS[index]['stauts'] is 'runpending' or JOBS[index]['stauts'] is 'done':
                    pass
                elif JOBS[index]['stauts'] is 'fail':
                    JOBS[index]['stauts'] = 'stop'

        # QAction.setEnabled(self.actionStart_all, False)
        # QAction.setEnabled(self.action_manager, False)
        # QAction.setEnabled(self.actionPort_Setup, False)
        # QAction.setEnabled(self.actionStart_all_menu, False)
        # QAction.setEnabled(self.action_manager_menu, False)
        # QAction.setEnabled(self.actionPort_Setup_menu, False)
        #
        # self.bes_dldtool_startall()
        # startall_t = Timer(2, self.btn_stopall_enable)
        # startall_t.start()
        if get_tws_on():
            if list_len == 2:
                serial_ear1 = serial.Serial('COM' + str(JOBS[0]['portnum']), 1200, timeout=0.500)
                serial_ear1.set_buffer_size(rx_size=10240, tx_size=1024)
                serial_ear2 = serial.Serial('COM' + str(JOBS[1]['portnum']), 1200, timeout=0.500)
                serial_ear2.set_buffer_size(rx_size=10240, tx_size=1024)
                QAction.setEnabled(self.actionStart_all, False)
                # QAction.setEnabled(self.action_manager, False)
                QAction.setEnabled(self.actionPort_Setup, False)
                QAction.setEnabled(self.actionStart_all_menu, False)
                # QAction.setEnabled(self.action_manager_menu, False)
                QAction.setEnabled(self.actionPort_Setup_menu, False)
                QAction.setEnabled(self.actionStop_all, False)
                QAction.setEnabled(self.actionStop_all_menu, False)
                tws_thread = threading.Thread(target=self.tws_thread_handler, name="tws_Thread",
                                              args=(serial_ear1, serial_ear2))
                tws_thread.start()
        else:
            QAction.setEnabled(self.actionStart_all, False)
            # QAction.setEnabled(self.action_manager, False)
            QAction.setEnabled(self.actionPort_Setup, False)
            QAction.setEnabled(self.actionStart_all_menu, False)
            # QAction.setEnabled(self.action_manager_menu, False)
            QAction.setEnabled(self.actionPort_Setup_menu, False)
            self.bes_dldtool_startall()
            startall_t = Timer(2, self.btn_stopall_enable)
            startall_t.start()

    def tws_thread_handler(self, serial_ear1, serial_ear2):
        list_len = len(self.Port_list)
        print('pair_address verification')
        flag = self.tws_handler(serial_ear1, serial_ear2)
        if flag:
            print('pair_address verification succeeded. ready for burning')
            serial_ear1.close()
            serial_ear2.close()
            self.bes_dldtool_startall()
            startall_t = Timer(2, self.btn_stopall_enable)
            startall_t.start()
        else:
            print('pair_address verification failed. ready for TWS teaming verification')
            flag1 = self.cmd_handle(serial_ear1, serial_ear2)
            if flag1:
                # print('TWS teaming verification succeeded. ready for burning')
                # serial_ear1.close()
                # serial_ear2.close()
                # self.bes_dldtool_startall()
                # startall_t = Timer(2, self.btn_stopall_enable)
                # startall_t.start()
                print('TWS teaming verification succeeded. pair_address verification again')
                time.sleep(5)
                flag2 = self.tws_handler(serial_ear1, serial_ear2)
                if flag2:
                    print('pair_address verification succeeded. ready for burning')
                    serial_ear1.close()
                    serial_ear2.close()
                    self.bes_dldtool_startall()
                    startall_t = Timer(2, self.btn_stopall_enable)
                    startall_t.start()
                else:
                    print('Second pair_address verification failed. ')
                    QAction.setEnabled(self.actionStart_all, True)
                    QAction.setEnabled(self.actionPort_Setup, True)
                    QAction.setEnabled(self.actionStart_all_menu, True)
                    QAction.setEnabled(self.actionPort_Setup_menu, True)
                    QAction.setEnabled(self.actionStop_all, True)
                    QAction.setEnabled(self.actionStop_all_menu, True)
            else:
                print('TWS teaming verification failed. do not burning')
                QAction.setEnabled(self.actionStart_all, True)
                QAction.setEnabled(self.actionPort_Setup, True)
                QAction.setEnabled(self.actionStart_all_menu, True)
                QAction.setEnabled(self.actionPort_Setup_menu, True)
                QAction.setEnabled(self.actionStop_all, True)
                QAction.setEnabled(self.actionStop_all_menu, True)

    @staticmethod
    def mkdir_encrypt():
        encrypt_dir = 'bin\\encrypt'
        if os.path.exists(encrypt_dir) == False:
            os.mkdir(encrypt_dir)

    def mkdir_customer(self):
        customer_dir = 'bin\\customer'
        if os.path.exists(customer_dir) == True:
            shutil.rmtree(customer_dir)
        os.mkdir(customer_dir)

    def secure_mode_bin_prepare(self, index):
        global JOBS
        encrypt_bin_path = os.getcwd() + '\\bin\\encrypt\\' + ('app%d.bin' % JOBS[index]['ID'])
        burn_path_1, _ = xml_getxmlcfg_burnpath()
        shutil.copyfile(burn_path_1, encrypt_bin_path)
        JOBS[index]['encrypt_path'] = encrypt_bin_path

    def generate_custom_bin(self, chip_version, bin_path, customer_bin_path, bin_addr):
        shutil.copyfile(bin_path, customer_bin_path)
        bin_addr_interger = string.atoi(bin_addr, 16)
        if chip_version == '1000':
            bin_addr_interger = bin_addr_interger + 0x6c000000
        elif chip_version == '2001' or chip_version == '1501' or chip_version == '2003':
            bin_addr_interger = bin_addr_interger + 0x2c000000
        else:
            bin_addr_interger = bin_addr_interger + 0x3c000000
        addr_str = GlobModule.convert_int_bin(bin_addr_interger)
        fp = open(customer_bin_path, 'ab+')
        fp.write(addr_str)
        fp.close()

    def generate_erase_bin(self, chip_version, erase_bin_path, erase_len, erase_addr):
        erase_len_interger = string.atoi(erase_len, 16)
        bin_addr_interger = string.atoi(erase_addr, 16)
        if chip_version == '1000':
            bin_addr_interger = bin_addr_interger + 0x6c000000
        elif chip_version == '2001' or chip_version == '1501' or chip_version == '2003':
            bin_addr_interger = bin_addr_interger + 0x2c000000
        else:
            bin_addr_interger = bin_addr_interger + 0x3c000000
        addr_str = GlobModule.convert_int_bin(bin_addr_interger)
        fp = open(erase_bin_path, 'wb')
        for i in range(0, erase_len_interger):
            bb = struct.pack('B', 255)
            fp.write(bb)
        fp.write(addr_str)
        fp.close()

    def customer_bin_prepare(self):
        self.mkdir_customer()
        customer_bin1_path = ''
        customer_bin2_path = ''
        customer_bin3_path = ''
        customer_bin4_path = ''
        erase_bin_path = ''
        self.custom_bin_list = []

        chip_version, customer1_enable, custom_bin1_path, customer1_addr, customer2_enable, custom_bin2_path, customer2_addr, customer3_enable, custom_bin3_path, customer3_addr, customer4_enable, custom_bin4_path, customer4_addr = xml_get_customer_info()
        if custom_bin1_path != None:
            bin1_path = str(custom_bin1_path)
            if bin1_path != '':
                bin1_addr = str(customer1_addr)
                customer_bin1_path = os.getcwd() + '\\bin\\customer\\customer1.bin'
                self.generate_custom_bin(chip_version, bin1_path, customer_bin1_path, bin1_addr)

        if custom_bin2_path != None:
            bin2_path = str(custom_bin2_path)
            if bin2_path != '' and bin2_path != None:
                bin2_addr = str(customer2_addr)
                customer_bin2_path = os.getcwd() + '\\bin\\customer\\customer2.bin'
                self.generate_custom_bin(chip_version, bin2_path, customer_bin2_path, bin2_addr)

        if custom_bin3_path != None:
            bin3_path = str(custom_bin3_path)
            if bin3_path != '' and bin3_path != None:
                bin3_addr = str(customer3_addr)
                customer_bin3_path = os.getcwd() + '\\bin\\customer\\customer3.bin'
                self.generate_custom_bin(chip_version, bin3_path, customer_bin3_path, bin3_addr)

        if custom_bin4_path != None:
            bin4_path = str(custom_bin4_path)
            if bin4_path != '' and bin4_path != None:
                bin4_addr = str(customer4_addr)
                customer_bin4_path = os.getcwd() + '\\bin\\customer\\customer4.bin'
                self.generate_custom_bin(chip_version, bin4_path, customer_bin4_path, bin4_addr)

        erase_en, erase_len, erase_addr = get_erase_info()
        if erase_en:
            erase_bin_path = os.getcwd() + '\\bin\\customer\\erase.bin'
            self.generate_erase_bin(chip_version, erase_bin_path, erase_len, erase_addr)

        self.custom_bin_list = [erase_bin_path, customer_bin1_path, customer_bin2_path, customer_bin3_path,
                                customer_bin4_path]

    def bes_dldtool_startall(self):
        global JOBS

        self.customer_bin_prepare()
        encrypt_on = xml_encrypt_is_on()
        list_len = len(self.Port_list)
        if list_len == 0:
            return
        for index in range(0, list_len, 1):
            if self.Port_list[index].isChecked():
                if JOBS[index]['stauts'] is 'runpending' or JOBS[index]['stauts'] is 'done':
                    pass
                else:
                    if encrypt_on is True:
                        BesDldMainWnd.mkdir_encrypt()
                        self.secure_mode_bin_prepare(index)
                    self.bes_dldtool_gui_reset(JOBS[index])
                    self.bes_dldtool_mainprocess_thrd_start(JOBS[index], index)
                    if xml_getxmlcfg_is_fctrmdonly() == False:
                        factory_bin_name = JOBS[index]['factorybin']
                        bt_addr_dis, ble_addr_dis, calib_value, sn = dld_sector_gen(factory_bin_name, True)
                        JOBS[index]['btaddr_pack'] = struct.pack('<6B', bt_addr_dis[5], bt_addr_dis[4], bt_addr_dis[3],
                                                                 bt_addr_dis[2], bt_addr_dis[1], bt_addr_dis[0])
                        JOBS[index]['btaddrtext'] = '%02X:%02X:%02X:%02X:%02X:%02X' % (bt_addr_dis[0],
                                                                                       bt_addr_dis[1],
                                                                                       bt_addr_dis[2],
                                                                                       bt_addr_dis[3],
                                                                                       bt_addr_dis[4],
                                                                                       bt_addr_dis[5])
                        JOBS[index]['bleaddrtext'] = '%02X:%02X:%02X:%02X:%02X:%02X' % (ble_addr_dis[0],
                                                                                        ble_addr_dis[1],
                                                                                        ble_addr_dis[2],
                                                                                        ble_addr_dis[3],
                                                                                        ble_addr_dis[4],
                                                                                        ble_addr_dis[5])
                        JOBS[index]['sntext'] = sn
                        write_cfg_log(JOBS[index]['btaddrtext'], JOBS[index]['bleaddrtext'], calib_value,
                                      JOBS[index]['sntext'])
                        calibdisplay = gui_getcalibvalue(JOBS[index])
                        if xml_get_update_calib_enable() == 0 or xml_get_update_sector_enable() == '0':
                            calibdisplay.setText('')
                        else:
                            calibdisplay.setText(str(calib_value))
                    else:
                        write_cfg_log('0', '0', 0, '0')

        for each_i in range(0, list_len, 1):
            if self.Port_list[each_i].isChecked():
                self.jobstart(JOBS[each_i], each_i)

    def tws_handler(self, serial1, serial2):
        return_data1_list = []
        return_data2_list = []
        bt_addr1 = ''
        bt_addr2 = ''
        cmd = b'\x04\xFF\x26\x02\x23\x01\x00'
        for i in range(0, 3):
            serial1.write(cmd)
            serial2.write(cmd)
            time.sleep(1)
        if serial1.in_waiting and serial2.in_waiting:
            data1 = serial1.read(serial1.in_waiting)
            data2 = serial2.read(serial2.in_waiting)
            for i in range(0, len(data1)):
                d1, = struct.unpack('>B', data1[i])
                return_data1_list.append(d1)
            for i in range(0, len(data2)):
                d2, = struct.unpack('>B', data2[i])
                return_data2_list.append(d2)
                while len(return_data1_list) > 0:
                    if return_data1_list[0] == 0xFF:
                        if len(return_data1_list) > 1:
                            if return_data1_list[1] == 0x04:
                                if len(return_data1_list) >= 13:
                                    if return_data1_list[3] == 0x02 and return_data1_list[4] == 0x23 and \
                                            return_data1_list[5] == 0x01 and return_data1_list[6] == 0x06:
                                        if return_data1_list[7] == 0x00 and return_data1_list[8] == 0x00 and \
                                                return_data1_list[9] == 0x00 and return_data1_list[10] == 0x00 and \
                                                return_data1_list[11] == 0x00 and return_data1_list[12] == 0x00:
                                            return False
                                        else:
                                            bt_addr1 = struct.pack('>BBBBBBBBBBBBB', return_data1_list[0],
                                                                   return_data1_list[1], return_data1_list[2],
                                                                   return_data1_list[3], return_data1_list[4],
                                                                   return_data1_list[5], return_data1_list[6],
                                                                   return_data1_list[7], return_data1_list[8],
                                                                   return_data1_list[9], return_data1_list[10],
                                                                   return_data1_list[11], return_data1_list[12])
                                            break
                                    else:
                                        del return_data1_list[0:7]
                                else:
                                    break
                            else:
                                del return_data1_list[0:2]
                        else:
                            break
                    else:
                        del return_data1_list[0:1]
                while len(return_data2_list) > 0:
                    if return_data2_list[0] == 0xFF:
                        if len(return_data2_list) > 1:
                            if return_data2_list[1] == 0x04:
                                if len(return_data2_list) >= 13:
                                    if return_data2_list[3] == 0x02 and return_data2_list[4] == 0x23 and \
                                            return_data2_list[5] == 0x01 and return_data2_list[6] == 0x06:
                                        if return_data2_list[7] == 0x00 and return_data2_list[8] == 0x00 and \
                                                return_data2_list[9] == 0x00 and return_data2_list[10] == 0x00 and \
                                                return_data2_list[11] == 0x00 and return_data2_list[12] == 0x00:
                                            return False
                                        else:
                                            bt_addr2 = struct.pack('>BBBBBBBBBBBBB', return_data2_list[0],
                                                                   return_data2_list[1], return_data2_list[2],
                                                                   return_data2_list[3], return_data2_list[4],
                                                                   return_data2_list[5], return_data2_list[6],
                                                                   return_data2_list[7], return_data2_list[8],
                                                                   return_data2_list[9], return_data2_list[10],
                                                                   return_data2_list[11], return_data2_list[12])
                                            break
                                    else:
                                        del return_data2_list[0:7]
                                else:
                                    break
                            else:
                                del return_data2_list[0:2]
                        else:
                            break
                    else:
                        del return_data2_list[0:1]
        else:
            return False
        if len(bt_addr1) > 0 and len(bt_addr2) > 0 and bt_addr1 == bt_addr2 and bt_addr1:
            return True
        else:
            return False

    def cmd_handle(self, serial1, serial2):
        print('send TWS teaming request...')
        cmd_list = []
        return_list = []
        cmd = b'\x04\xFF\x19\x02\x17\x00\x00'
        for i in range(0, 5):
            serial1.write(cmd)
            serial2.write(cmd)
            time.sleep(3)
        if serial1.in_waiting:
            rec = serial1.read(serial1.in_waiting)
            for i in range(0, len(rec)):
                a, = struct.unpack('>B', rec[i])
                cmd_list.append(a)
            while len(cmd_list) > 0:
                if cmd_list[0] == 0x54:
                    if len(cmd_list) > 1:
                        if cmd_list[1] == 0x5A:
                            if len(cmd_list) >= 13:
                                if cmd_list[3] == 0x00 and cmd_list[4] == 0x02 and cmd_list[5] == 0x00 and cmd_list[
                                    6] == 0x06:
                                    print('Forward TWS teaming request reply')
                                    send_cmd = struct.pack('>BBBBBBBBBBBBB', cmd_list[0], cmd_list[1], cmd_list[2],
                                                           cmd_list[3], cmd_list[4], cmd_list[5], cmd_list[6],
                                                           cmd_list[7], cmd_list[8], cmd_list[9], cmd_list[10],
                                                           cmd_list[11], cmd_list[12])
                                    for i in range(0, 5):
                                        serial2.write(send_cmd)
                                        time.sleep(1)
                                    time.sleep(3)
                                    if serial2.in_waiting:
                                        rec2 = serial2.read(serial2.in_waiting)
                                        for i in range(0, len(rec2)):
                                            b, = struct.unpack('>B', rec2[i])
                                            return_list.append(b)
                                        while len(return_list) > 0:
                                            if return_list[0] == 0xFF:
                                                if len(return_list) > 1:
                                                    if return_list[1] == 0x04:
                                                        if len(return_list) > 2:
                                                            if return_list[2] == 0x1A:
                                                                if len(return_list) > 7:
                                                                    if return_list[3] == 0x01 and return_list[
                                                                        4] == 0x17 and return_list[5] == 0x00 and \
                                                                            return_list[6] == 0x01 and return_list[
                                                                        7] == 0x01:
                                                                        return True
                                                                    else:
                                                                        del return_list[0:8]
                                                                else:
                                                                    return False
                                                            else:
                                                                del return_list[0:3]
                                                        else:
                                                            return False
                                                    else:
                                                        del return_list[0:2]
                                                else:
                                                    return False
                                            else:
                                                del return_list[0:1]
                                    else:
                                        return False
                                else:
                                    del cmd_list[0:7]
                            else:
                                break
                        else:
                            del cmd_list[0:2]
                    else:
                        break
                else:
                    del cmd_list[0:1]
        if len(cmd_list) > 0:
            del cmd_list[0:len(cmd_list)]
        if len(return_list) > 0:
            del return_list[0:len(return_list)]
        if serial2.in_waiting:
            rec = serial2.read(serial2.in_waiting)
            for i in range(0, len(rec)):
                a, = struct.unpack('>B', rec[i])
                cmd_list.append(a)
            while len(cmd_list) > 0:
                if cmd_list[0] == 0x54:
                    if len(cmd_list) > 1:
                        if cmd_list[1] == 0x5A:
                            if len(cmd_list) >= 13:
                                if cmd_list[3] == 0x00 and cmd_list[4] == 0x02 and cmd_list[5] == 0x00 and cmd_list[
                                    6] == 0x06:
                                    print('Forward TWS teaming request reply')
                                    send_cmd = struct.pack('>BBBBBBBBBBBBB', cmd_list[0], cmd_list[1], cmd_list[2],
                                                           cmd_list[3], cmd_list[4], cmd_list[5], cmd_list[6],
                                                           cmd_list[7], cmd_list[8], cmd_list[9], cmd_list[10],
                                                           cmd_list[11], cmd_list[12])
                                    for i in range(0, 5):
                                        serial1.write(send_cmd)
                                        time.sleep(1)
                                    time.sleep(3)
                                    if serial1.in_waiting:
                                        rec2 = serial1.read(serial1.in_waiting)
                                        for i in range(0, len(rec2)):
                                            b, = struct.unpack('>B', rec2[i])
                                            return_list.append(b)
                                        while len(return_list) > 0:
                                            if return_list[0] == 0xFF:
                                                if len(return_list) > 1:
                                                    if return_list[1] == 0x04:
                                                        if len(return_list) > 2:
                                                            if return_list[2] == 0x1A:
                                                                if len(return_list) > 7:
                                                                    if return_list[3] == 0x01 and return_list[
                                                                        4] == 0x17 and return_list[5] == 0x00 and \
                                                                            return_list[6] == 0x01 and return_list[
                                                                        7] == 0x01:
                                                                        return True
                                                                    else:
                                                                        del return_list[0:8]
                                                                else:
                                                                    return False
                                                            else:
                                                                del return_list[0:3]
                                                        else:
                                                            return False
                                                    else:
                                                        del return_list[0:2]
                                                else:
                                                    return False
                                            else:
                                                del return_list[0:1]
                                    else:
                                        return False
                                else:
                                    del cmd_list[0:7]
                            else:
                                return False
                        else:
                            del cmd_list[0:2]
                    else:
                        return False
                else:
                    del cmd_list[0:1]
        else:
            return False

    def btn_allstart_enable(self):
        # bes_trace( 'btn_allstart_enable')
        QAction.setEnabled(self.actionStart_all, True)
        # QAction.setEnabled(self.action_manager, True)
        QAction.setEnabled(self.actionPort_Setup, True)
        QAction.setEnabled(self.actionStart_all_menu, True)
        # QAction.setEnabled(self.action_manager_menu, True)
        QAction.setEnabled(self.actionPort_Setup_menu, True)

    def all_job_is_stop(self):
        global JOBS
        if JOBS[0]['stauts'] == 'stop' and \
                JOBS[1]['stauts'] == 'stop' and \
                JOBS[2]['stauts'] == 'stop' and \
                JOBS[3]['stauts'] == 'stop' and \
                JOBS[4]['stauts'] == 'stop' and \
                JOBS[5]['stauts'] == 'stop' and \
                JOBS[6]['stauts'] == 'stop' and \
                JOBS[7]['stauts'] == 'stop':
            return 'YES'
        return 'NO'

    def StopAll(self):
        if 'YES' == self.all_job_is_stop():
            return
        QAction.setEnabled(self.actionStop_all, False)
        # time.sleep(1) # allstart quickly press allstop btn,comport close ocurr before comport open(subprocess).
        self.bes_dldtool_stop()
        stopall_t = Timer(3, self.btn_allstart_enable)
        stopall_t.start()

    def update_bar_info(self, bar):
        # bes_trace( 'update_bar_info step=%d'%bar.step
        if bar.step <= 100:
            bar.setValue(bar.step)

    def update_time_info(self, Time):
        Time.display(Time.str)

    def bes_dldtool_gui_reset(self, d):
        # self.opt = gui_getopt(d)
        self.jobSTATE = getSTATE(d)
        self.guitime = gui_getTIME(d)

        if d['stauts'] == 'stop':  # or done         fail:
            d['stauts'] = 'runpending'
            self.status_signal.emit([d, 'Idle'])

    # gyt add warning:all gui data be written @ main thread,should not be modified by other thread!
    # gui data including global opt_array[],bar_array[],STATE_array[],TIME_array[]
    def mainp_notify_subp_startburn(self):
        msg_list = []
        msg_list.append('MSG_DLD_START')
        msg_list.append(xml_getxmlcfg_is_fctrmdonly())
        msg_list.append(burn_appota_only())
        msg_list.append(get_baudrate())
        self.job['pconn4dldstart'].send(msg_list)
        self.job['parentconn4dldstop'].send(['MSG_SYNC_ENCRPYT_DATA', self.job['btaddr_pack']])

    def bes_dldtool_mainprocess_thrd_start(self, job, index):
        global g_mainpmonitor_semas, g_monitorthrd_array
        monitorthrd = getmonitorthrd(index)
        if g_monitorthrd_array[index] is not None:
            if g_monitorthrd_array[index].isAlive():
                return
        job['semaindex'] = index
        # start monitor thread:
        monitor_sema = getsema(job['semaindex'])
        if monitor_sema is None:
            monitor_sema = threading.Semaphore(0)
            setsema(index, monitor_sema)
        monitor_thrd = DldProgressMonitor(job,
                                          self.bar_signal,
                                          self.status_signal,
                                          self.dldtime_signal,
                                          monitor_sema,
                                          self.btaddr_display_signal,
                                          self.bleaddr_display_signal,
                                          self.calibvalue_signal)
        monitor_thrd.start()
        setmonitorthrd(index, monitor_thrd)

    def bes_dldtool_mainprocess_monitorthrd_end(self):
        global monitorthrd_array, mainpmonitor_semas
        global JOBS
        if JOBS[0]['stauts'] is not 'stop':
            return
        if len(monitorthrd_array) > 0:
            for i, thrd in enumerate(monitorthrd_array):
                monitorthrdsema = gui_getsema(i)
                if monitorthrdsema is not None:
                    monitorthrdsema.release()
                monitorthrd_array[i] = None

    def doAction(self):
        global JOBS
        return

    def jobstart(self, d, index):
        self.job = d
        self.subproc = None
        cfg_as_update = cfg_as_updatetool()
        encrypt_on = xml_encrypt_is_on()
        erase_whole = xml_get_erasewhole_switch()

        if self.job['stauts'] == 'runpending':
            self.job['stauts'] = 'run'
            gen_btaddr_enable = xml_get_update_sector_enable()
            connector_switch = xml_get_connector_cfg()
            calib_switch = xml_get_calibrate_cfg()

            Customized_enable = xml_get_update_Customized_enable()
            Customized_Addr = xml_get_update_Customized_Addr()
            if xml_get_update_sector_enable() == '0':
                burn_field_enable_value = (1 << 6) + (1 << 5) + (1 << 4) + (1 << 3) + (1 << 2) + (1 << 1) + 1
            else:
                burn_field_enable_value = (xml_get_update_sn_enable() << 6) \
                                          + (xml_get_update_btaddr_enable() << 5) \
                                          + (xml_get_update_btname_enable() << 4) \
                                          + (xml_get_update_bleaddr_enable() << 3) \
                                          + (xml_get_update_blename_enable() << 2) \
                                          + (xml_get_update_conaddr_enable() << 1) \
                                          + xml_get_update_calib_enable()

            if encrypt_on is True:
                ffile = JOBS[index]['encrypt_path']
            else:
                ffile = str(self.flshbin_path)
            self.subproc = DldProcess(self.job,
                                      str(self.ramrun_path),
                                      ffile,
                                      str(self.flshbootbin_path),
                                      self.app_switch,
                                      self.otaboot_switch,
                                      gen_btaddr_enable,
                                      connector_switch,
                                      calib_switch,
                                      cfg_as_update,
                                      burn_field_enable_value,
                                      self.custom_bin_list,
                                      encrypt_on,
                                      erase_whole,
                                      Customized_enable,
                                      Customized_Addr)
            self.subproc.start()
            time.sleep(0.05)
            # release DldProgressMonitor sema.
            monit_thrd_sema = getsema(self.job['semaindex'])
            monit_thrd_sema.release()
            self.mainp_notify_subp_startburn()

    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, "Quit", "Quit bes dldtool?",
                                           QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.gen_unuse_addr()
            # xml_doc_write()
            restore_dldresult_to_xml()
            for i, d in enumerate(JOBS):
                self.clean_alive_threads(d, i)

            event.accept()
        elif reply == QtGui.QMessageBox.No:
            event.ignore()

        # bes_trace( 'closeEvent done.bp here.'

    def clean_alive_threads(self, job, index):
        job['stauts'] = 'leaving'

        if job['parentconn4dldstop'] is not -1:
            job['parentconn4dldstop'].send(['MSG_DLD_STOP'])
        if job['pconn4dldstart'] is not -1:
            job['pconn4dldstart'].send('MSG_DLD_END')
        if job['monitorthrdindex'] is not -1:
            self.monitor_thrd_id = gui_getmonitorthrd(job)
            self.monitor_thrd_sema = getsema(job['semaindex'])
            if self.monitor_thrd_id.isAlive():
                if self.monitor_thrd_sema is not None:
                    self.monitor_thrd_sema.release()

    def bes_dldtool_ajob_stop(self, index, ajob):
        # if ajob['status'] is 'runpending':
        while ajob['stauts'] is 'runpending':
            bes_trace('waiting')
        bes_trace('bes_dldtool_ajob_stop, job status is %s\n' % ajob['stauts'])
        ajob['stauts'] = 'stop'
        if ajob['parentconn4dldstop'] is not -1:
            ajob['parentconn4dldstop'].send(['MSG_DLD_STOP'])
        if ajob['pconn4dldstart'] is not -1:
            ajob['pconn4dldstart'].send('MSG_DLD_END')
        if ajob['monitorthrdindex'] is not -1:
            self.monitor_thrd_id = gui_getmonitorthrd(ajob)
            self.monitor_thrd_sema = getsema(ajob['semaindex'])
            if self.monitor_thrd_id.isAlive():
                if self.monitor_thrd_sema is not None:
                    self.monitor_thrd_sema.release()
        progressbar = gui_getprogressbar(ajob)
        progressbar.setValue(0)

        guistatus = getSTATE(ajob)
        guistatus.setText(str_stop[lang_set])
        temp_palette = guistatus.palette()
        temp_palette.setColor(guistatus.backgroundRole(), QColor(222, 222, 222))
        guistatus.setPalette(temp_palette)

    def bes_dldtool_stop(self):
        # using addr to failed addr
        self.gen_unuse_addr()
        for i, d in enumerate(JOBS):
            if d['stauts'] is not 'stop':
                self.bes_dldtool_ajob_stop(i, d)
        restore_dldresult_to_xml()

    def gen_unuse_addr(self):
        using_bt_addr = get_using_bt_addr()
        failed_bt_addr = xml_get_failed_bt_addr()

        for i in range(0, len(using_bt_addr)):
            failed_bt_addr.append(using_bt_addr[i])
        using_bt_addr = []
        failed_bt_addr = list(set(failed_bt_addr))
        xml_set_failed_bt_addr(failed_bt_addr)

        using_ble_addr = get_using_ble_addr()
        failed_ble_addr = xml_get_failed_ble_addr()

        for i in range(0, len(using_ble_addr)):
            failed_ble_addr.append(using_ble_addr[i])
        using_ble_addr = []
        failed_ble_addr = list(set(failed_ble_addr))
        xml_set_failed_ble_addr(failed_ble_addr)

        xml_doc_write()
