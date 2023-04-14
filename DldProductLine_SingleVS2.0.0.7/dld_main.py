from multiprocessing import freeze_support
from dld_mainwnd import *
from win32api import GetLastError
from winerror import ERROR_ALREADY_EXISTS
from dld_global import *

class wtdldtool_app_instance(object):
    def __init__(self):
        global G_COMPANY_NAME, G_APP_NAME
        from win32event import CreateMutex
        self.mutexName = '%s.%s' % (G_COMPANY_NAME, G_APP_NAME)
        self.myMutex = CreateMutex(None, False, self.mutexName)
        self.lastErr = GetLastError()

    def app_is_alive(self):
        if self.lastErr == ERROR_ALREADY_EXISTS:
            return True
        else:
            return False



if __name__ == '__main__':
    freeze_support()
    bes_dldtool_app = QApplication(sys.argv)
    initglobal()
    if xml_get_encrypt_on():
        xml_mod_for_encrypt_mode()
    parseval = xml_doc_parse()
    if parseval == 'xmlcfgok':
        if(config_json_parse() == False):
            error_dlg = ErrorReportDlg('json parse fail')
            error_dlg.exec_()
        else:                
            burnpath_text_1, burnpath_text_2 = xml_getxmlcfg_burnpath()
            if burnpath_text_1 != None:
                get_dlddll().handle_buildinfo_to_extend((burnpath_text_1).encode("utf-8"))
                buf = (c_char * 249)()
                buildinfo_bt_name_len = get_dlddll().get_build_info_bt_name(buf)
                if buildinfo_bt_name_len is not 0:                
                    namestr = ''
                    for i in range(buildinfo_bt_name_len):
                        namestr = namestr + str(buf[i])
                    xml_dev_local_name_write_back(namestr)
            bes_dldtool_window = BesDldMainWnd()
            bes_dldtool_window.show()
            sys.exit(bes_dldtool_app.exec_())
    else:
        error_dlg = ErrorReportDlg(parseval)
        error_dlg.exec_()



