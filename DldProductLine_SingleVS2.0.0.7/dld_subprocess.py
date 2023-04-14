# -*- coding: utf-8 -*-
import multiprocessing
from dld_global import *
from ctypes import *
import copy
import struct

class dld_thread(threading.Thread):
    def __init__(self, job, com, sector_update_flag, connector_switch, calib_switch, \
                cfg_as_update,burn_field_enable_value, custom_bin_list, load_dll, encrypt_on, eraser_switch, Customized_enable,Customized_Addr):
        threading.Thread.__init__(self)
        self.job = job
        self.com = str(com)
        self.stopped = False
        self.rfile = ""
        self.ffile = ""
        self.fbfile = ""
        self.appswitch = False
        self.bootswitch = False
        self.argc = 0
        self.argv = []
        self.sector_update_flag = sector_update_flag
        self.calib_switch = calib_switch
        self.connector_switch = connector_switch
        self.cfg_as_update = cfg_as_update
        self.burn_field_enable_value = burn_field_enable_value
        self.custom_bin_list = custom_bin_list
        self.dldtool = load_dll
        self.encrypt_on = encrypt_on
        self.eraser_switch = eraser_switch
        self.Customized_enable = Customized_enable
        self.Customized_Addr = Customized_Addr

        
    def dispatch_pip_msg_terminated(self):
        '''dispatch_pip_msg_terminated'''
        self.job['childconn'].send(['ev_wm_terminated'])

    def thread_communicate_with_chip_evt_dispatch(self, evt):
        '''dispatch evt from dld thread'''
        str_leave = 'leaving'
        str_loop = 'looping'
        if evt == ev_wm_burn_progress:
            progress = self.dldtool.get_burn_progress()
            self.job['childconn'].send(['ev_wm_burn_progress', int(progress)])
        elif evt == ev_wm_sync_succeed:
            self.job['childconn'].send(['ev_wm_sync_succeed'])
        elif evt == ev_wm_run_programmer_succeed:
            bes_trace( 'evt ev_wm_run_programmer_succeed')
        elif evt == ev_wm_bin_encrypt_begin:
           
            # bes_trace('ev_wm_bin_encrypt_begin')
            efuse_value1 = self.dldtool.get_encrypt_efuse_value1()
            efuse_value2 = self.dldtool.get_encrypt_efuse_value2()
            
            #print '7777777777777&&&&&&&&&&&'
            #print hex(88), hex(efuse_value1),hex(efuse_value2)
            
            efuse_value = efuse_value1|(efuse_value2<<16)
            pack_efuse_data = struct.pack('i',efuse_value)
            # print 'efuse_value =======================>%08X' % efuse_value
            ret_data = get_tool_rsa_key()
            ret_descrip = ret_data[0]
            if ret_descrip == 'password_incorrect':
                self.job['childconn'].send(['ev_wm_bin_encrypt_begin',ret_descrip])
            elif ret_descrip == 'succeed':
                pri_key = ret_data[1][0]
                pub_key = ret_data[1][1]
                signer = Signature_pkcs1_v1_5.new(pri_key)
                digest = SHA256.new()
                #print '111111111111111111111'
                #print dld_courier.encrypt_data
                digest.update(pack_efuse_data+dld_courier.encrypt_data)
                #print  hex(digest)
                sign = signer.sign(digest)
                #print sign
                #print "pub_key"
                #print pub_key
                dump_pubkey = GlobModule.dump_public_key(pub_key)
                key_addr_int = self.dldtool.get_key_addr_from_buildinfo(self.job['encrypt_path'])
                if key_addr_int != 0:                
                    #print type(key_addr_int)
                    GlobModule.add_pubkey_signature_to_bin(self.job['encrypt_path'],key_addr_int,dump_pubkey,sign)
                self.dldtool.end_encrypt_block()
        elif evt == ev_wm_bin_encrypt_end:
            bes_trace('ev_wm_bin_encrypt_end')
        elif evt == ev_wm_burn_magic:
            self.job['childconn'].send(['ev_wm_burn_magic'])
        elif evt == ev_wm_burn_failure:
            errorcode = self.dldtool.get_exit_code()
            self.job['childconn'].send(['ev_wm_burn_failure', errorcode])
        elif evt == ev_wm_burn_complt:
            self.job['childconn'].send(['ev_wm_burn_complt'])        
        elif evt == ev_wm_chip_poweroff:
            self.job['childconn'].send(['ev_wm_chip_poweroff'])
        elif evt == ev_wm_burn_efuse_start:
            self.job['childconn'].send(['ev_wm_burn_efuse_start'])
        elif evt == ev_wm_burn_efuse_end:
            self.job['childconn'].send(['ev_wm_burn_efuse_end'])
        elif evt == ev_wm_exit_valid:
            self.job['childconn'].send(['ev_wm_exit_valid'])
            return str_leave
        elif evt == ev_wm_exit_invalid:
            errorcode = self.dldtool.get_exit_code()
            self.job['childconn'].send(['ev_wm_exit_invalid', errorcode])
            return str_leave
        elif evt == ev_wm_exit_user_stop:
            return str_leave
        elif evt == ev_wm_sync_wait:
            bes_trace( 'waiting for chip sync...')
        elif evt == ev_wm_port_open_succeed:
            bes_trace( 'port open succeed' )
        elif evt == ev_wm_factory_mode:
            self.job['childconn'].send(['ev_wm_factory_mode'])
        elif evt == ev_wm_factory_mode_progress:
            progress = self.dldtool.pyext_get_mcu_test_progress()
            self.job['childconn'].send(['ev_wm_factory_mode_progress', int(progress)])
        elif evt == ev_wm_factory_calib_value:
            calib_value = self.dldtool.pyext_get_calib_value()
            self.job['childconn'].send(['ev_wm_factory_calib_value', calib_value])
        elif evt == ev_wm_factory_mode_success:
            self.job['childconn'].send(['ev_wm_factory_mode_success'])
        elif evt == ev_wm_factory_mode_fail:
            errorcode = self.dldtool.get_exit_code()
            self.job['childconn'].send(['ev_wm_factory_mode_fail', errorcode])
        else:
            bes_trace( 'unknown evt %d' % evt)
        return str_loop

    def dispatch_pip_msg_get_evt_start(self):
        '''dispatch_pip_msg_get_evt_start'''
        while True:
            time.sleep(0.05)
            if self.stopped:
                break
            evt = self.dldtool.get_notify_from_cext()
            if evt >= ev_wm_port_open_failed and evt < ev_wm_max:
                ret = self.thread_communicate_with_chip_evt_dispatch(evt)
                if ret == 'leaving':
                    break
        bes_trace( "thread_communicate_with_chip_evt_dispatch over")


    def run(self): 
        rfile = self.rfile
        dldcom = self.com.decode('utf-8').encode('gbk')
        self.dldtool.handle_buildinfo_to_extend(self.ffile)

        while True:
            time.sleep(0.05)
            rcv = self.job['cconn4dldstart'].recv()
            bes_trace('subprocess dld_thread~~~~~~~~~~~~~~~~~%s~~~~~~~~~~~~~~' % rcv)
            if len(rcv) == 4:
                if rcv[0] == 'MSG_DLD_START':
                    self.argv = [] 
                    self.argv.append('dldtool.exe')
                    self.argv.append('-C' + dldcom)
                    #self.argv.append('-r' + rfile)
                    self.argv.append('-V' + rcv[3] )
                    if self.custom_bin_list[0] !='':
                        self.argv.append('-B' + self.custom_bin_list[0])
                    if rcv[1] == False:
                        if self.appswitch:
                            ffile = self.ffile.decode('utf-8').encode('gbk')
                            self.argv.append('-b' + ffile)
                        if self.bootswitch:
                            fbfile = self.fbfile.decode('utf-8').encode('gbk')
                            self.argv.append('-b' + fbfile)
                        if rcv[2] == False and self.appswitch:
                            binpath = os.getcwd() + '\\bin\\' + self.job['factorybin']
                            self.argv.append('-f' + binpath)
                        self.argv.append('-w' + str(self.burn_field_enable_value))

                    for i in range(1, len(self.custom_bin_list)):
                        if self.custom_bin_list[i] != '':
                            print '%s' % self.custom_bin_list[i]
                            self.argv.append('-B' + self.custom_bin_list[i])
                        
                    if self.cfg_as_update is False:
                        self.argv.append('-F' + self.connector_switch)
                        self.argv.append('-c' + self.calib_switch)
                        self.argv.append('-P' + '0')
                    else:
                        self.argv.append('-P' + '1')
                    if self.Customized_enable == 1:
                        self.argv.append('-K' + self.Customized_Addr)

                    self.argv.append('-e' + self.eraser_switch)
                    bes_trace(self.argv)
                    arg_var = (c_char_p * (len(self.argv)+1))()
                    index = 0
                    for argument in self.argv:
                        arg_var[index] = argument
                        index += 1
                    arg_ptr = cast(arg_var, POINTER(c_char_p))
                    if self.encrypt_on is True:
                        self.dldtool.dldtool_cfg_set(1)
                        efuseid1 = get_g_efuseID1()
                        efuseid2 = get_g_efuseID2()
                        self.dldtool.set_pin_array(efuseid1,efuseid2)
                    dldret = self.dldtool.dldstart(len(self.argv), arg_ptr)
                    if dldret is 0:
                        bes_trace('dld failure~')
                        break
                    self.dispatch_pip_msg_get_evt_start()
            elif rcv == 'MSG_DLD_END':
                bes_trace('dld_thread recv MSG_DLD_END')
                self.dispatch_pip_msg_terminated()
                self.stopped = True
                break
            else:
                bes_trace('dld_thread rcv ERRORMSG.')
        bes_trace('\ndld_thread over...\n')

    def setfile(self, rfile, ffile, fbfile, app_switch, otaboot_switch):
        self.rfile = rfile
        self.ffile = ffile
        self.fbfile = fbfile
        self.appswitch = app_switch
        self.bootswitch = otaboot_switch
        

class dld_courier(threading.Thread):
    encrypt_data = None
    def __init__(self, d, load_dll):
        threading.Thread.__init__(self)
        self.job = d
        self.bstop = False
        self.dldtool = load_dll

    def dispatch_pip_msg_dld_stop(self):
        'dispatch msg MSG_DLD_STOP from main process'
        self.dldtool.dldstop()
        bes_trace( 'dldtool.dldstop()')
        
    def run(self):
        while True:
            time.sleep(0.05)
            bes_trace( "dld_courier start..........\n")
            msgdescrip = self.job['childconn4dldstop'].recv()
            if msgdescrip[0] == 'MSG_DLD_STOP':              
                self.dispatch_pip_msg_dld_stop()
                break
            elif msgdescrip[0] == 'MSG_SYNC_ENCRPYT_DATA':
                dld_courier.encrypt_data = copy.deepcopy(msgdescrip[1])
        bes_trace('\ndld_courier over...\n')


class DldProcess(multiprocessing.Process):
    proc = None
    def __init__(self, job, rfile, ffile, fbfile, app_switch, otaboot_switch, \
                enable_flag, connector_switch, calib_switch, cfg_as_update,\
                burn_field_enable_value, custom_bin_list, encrypt_on, eraser_switch,Customized_enable, Customized_Addr):
        multiprocessing.Process.__init__(self)
        self.job = job
        self.rfile = rfile
        self.ffile = ffile
        self.fbfile = fbfile
        self.appswitch = app_switch
        self.bootswitch = otaboot_switch
        self.sector_update_flag = enable_flag
        self.connector_switch = connector_switch
        self.calib_switch = calib_switch
        self.cfg_as_update = cfg_as_update
        self.burn_field_enable_value = burn_field_enable_value
        self.custom_bin_list = custom_bin_list
        self.encrypt_on = encrypt_on
        self.eraser_switch = eraser_switch
        self.dldtool = None
        self.Customized_enable = Customized_enable
        self.Customized_Addr = Customized_Addr

    def run(self):
        self.dldtool = cdll.LoadLibrary(r'transferdll.dll')
        portnum = self.job['portnum']
        dld_courier_thread = dld_courier(self.job,self.dldtool)
        dld_courier_thread.start()

        dldthread = dld_thread(self.job,
                               portnum,
                               self.sector_update_flag,
                               self.connector_switch,
                               self.calib_switch,
                               self.cfg_as_update,
                               self.burn_field_enable_value,
                               self.custom_bin_list,
                               self.dldtool,
                               self.encrypt_on,
                               self.eraser_switch,
                               self.Customized_enable,
                               self.Customized_Addr)
        dldthread.setfile(self.rfile, self.ffile, self.fbfile, self.appswitch, self.bootswitch)
        dldthread.start()
        dld_courier_thread.join()
        dldthread.join()
        bes_trace('\nsubprocess run over...\n')
