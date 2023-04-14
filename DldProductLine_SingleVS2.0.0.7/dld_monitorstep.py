from dld_global import *
from dld_xml_operate import *
from threading import Timer

class DldProgressMonitor(threading.Thread):
    bar_signal = None
    calibvalue_signal = None
    dldtime_signal = None
    monitorsema = None
    def __init__(self,job, barsignal, statussignal, dldtimesignal, param_sema, btaddr_display_signal, bleaddr_display_signal, calibvalue_signal):
        threading.Thread.__init__(self)
        self.job = job
        self.bar_signal = barsignal
        self.statussignal = statussignal
        self.dldtime_signal = dldtimesignal
        self.monitorsema = param_sema
        self.dldbegin = 0
        self.btaddr_disp_signal = btaddr_display_signal
        self.bleaddr_disp_siganl = bleaddr_display_signal
        self.calibvalue_signal = calibvalue_signal
        self.burn_and_fctrmd_flag = False
        self.update_elapse_timer = None
        self.timecancel = True
        self.btaddr_pack = None
        self.incraddr = False
    def run(self):

        while self.job['stauts'] is not 'leaving' and self.job['stauts'] is not 'stop':
            time.sleep(0.05)
            bes_trace( 'main proc monitor thrd blocking...')
            self.monitorsema.acquire()
            bes_trace( 'main proc monitor thrd block over...')
            if self.job['stauts'] == 'leaving':
                break
            self.app_pipe_msg_monitor()

        bes_trace('\nmainproc DldProgressMonitor run over...\n')

    def start_next_burn(self, addr_inc_flag):
        if self.job['stauts'] == 'stop':
            bes_trace( "user stop!!!!!!!!!!!!!!!!!\n")
            return
        if xml_getxmlcfg_is_fctrmdonly() == False:
            if addr_inc_flag == True:
                encrypt_on = xml_encrypt_is_on()
                factory_bin_name = self.job['factorybin']
                bt_addr_dis, ble_addr_dis,calib_value,sn = dld_sector_gen(factory_bin_name, True)
                self.job['btaddr_pack'] = struct.pack('<6B', bt_addr_dis[5], bt_addr_dis[4], bt_addr_dis[3], bt_addr_dis[2], bt_addr_dis[1], bt_addr_dis[0])
                self.job['parentconn4dldstop'].send(['MSG_SYNC_ENCRPYT_DATA',self.job['btaddr_pack']])
                self.job['btaddrtext'] = '%02X:%02X:%02X:%02X:%02X:%02X' % (bt_addr_dis[0],
                                                                bt_addr_dis[1],
                                                                bt_addr_dis[2],
                                                                bt_addr_dis[3],
                                                                bt_addr_dis[4],
                                                                bt_addr_dis[5])
                self.job['bleaddrtext'] = '%02X:%02X:%02X:%02X:%02X:%02X' % (ble_addr_dis[0],
                                                                ble_addr_dis[1],
                                                                ble_addr_dis[2],
                                                                ble_addr_dis[3],
                                                                ble_addr_dis[4],
                                                                ble_addr_dis[5])
                self.job['sntext'] = sn
            write_cfg_log(self.job['btaddrtext'] , self.job['bleaddrtext'], xml_getxmlcfg_default_calib_value(), self.job['sntext'])                     
        else:
            write_cfg_log('0', '0', 0,'0')   
        msg_list = []
        msg_list.append('MSG_DLD_START')
        msg_list.append(xml_getxmlcfg_is_fctrmdonly())
        msg_list.append(burn_appota_only())
        msg_list.append(get_baudrate())
        self.job['pconn4dldstart'].send(msg_list)

    def update_elapse_func(self):
        '''update_test_elapse_func'''
        timeinfo = []
        testelapse = (time.time()-self.begin)
        elapse_sec = int(testelapse)
        elapse_min = (elapse_sec/60)
        elapse_sec = (elapse_sec % 60)
        elapse_str = '%02d:%02d' % (elapse_min, elapse_sec)
        timeinfo.append(self.job)
        timeinfo.append(elapse_str)
        self.dldtime_signal.emit(timeinfo)
        if self.timecancel == False:
            self.update_elapse_timer = Timer(1, self.update_elapse_func)
            self.update_elapse_timer.start()

    def dispatch_chip_poweroff_evt(self):
        'dispatch msg ev_wm_chip_poweroff'
        bes_trace( "dispatch_chip_poweroff_evt")
        self.statussignal.emit([self.job, 'Idle'])
        self.dldtime_signal.emit([self.job, "00:00"])
        self.bar_signal.emit([self.job, 0])

    def dispatch_burn_progress(self, msg):
        'dispatch msg burn progress'  
        if msg[1] >= 100:
            msg[1] = 99
            
        emit_string = 'Downloading'

        self.statussignal.emit([self.job, emit_string])
        self.bar_signal.emit([self.job, msg[1]])

    def dispatch_exit_invalid(self,ret):
        'dispatch msg exit invalid.'
        bes_trace( 'ev_wm_exit_invalid')
        if ret!=EXIT_CODE_WAIT_SYNC_ERROR:
            self.statussignal.emit([self.job, 'Invalid', ret])
        if self.update_elapse_timer is not None:
            self.update_elapse_timer.cancel()
        self.timecancel = True
        self.incraddr = False
        self.start_next_burn(self.incraddr)
        
    def dispatch_exit_valid(self):
        'dispatch msg exit valid.'
        bes_trace( 'ev_wm_exit_valid')
        if self.update_elapse_timer is not None:
            self.update_elapse_timer.cancel()
        self.timecancel = True
        self.incraddr = True
        threads_mutex = get_mainproc_monitor_mutex()
        threads_mutex.acquire()  
        if get_max_burn_num_flag()==True:
            if xml_get_max_burn_num_enable():
                rest_burn_num = get_rest_burn_num()
                if rest_burn_num > 1:
                    set_rest_burn_num(rest_burn_num-1)
                elif rest_burn_num == 1:
                    self.statussignal.emit([self.job, 'Full'])
                    set_rest_burn_num(0)
                else:
                    self.statussignal.emit([self.job, 'Full'])
        threads_mutex.release()
        self.statussignal.emit([self.job, 'Valid'])
        self.start_next_burn(self.incraddr)

    def dispatch_sync_succeed(self):
        'dispatch msg sync succeess'
        self.statussignal.emit([self.job, 'Downloading'])
        self.begin = time.time()
        self.dldtime_signal.emit([self.job, "00:00"])
        update_sector_enable = xml_get_update_sector_enable()
        if update_sector_enable == '1':    
            self.btaddr_disp_signal.emit([self.job, self.job['btaddrtext']])
            self.bleaddr_disp_siganl.emit([self.job, self.job['bleaddrtext']])
        else:
            self.btaddr_disp_signal.emit([self.job, "00:00:00:00:00:00"])
            self.bleaddr_disp_siganl.emit([self.job, "00:00:00:00:00:00"])
        self.update_elapse_timer = Timer(1, self.update_elapse_func)
        self.update_elapse_timer.start()
        self.timecancel =False
        save_log_to_file("SYNC SUCCESS. btaddr:%s  bleaddr%s sn:%s\n\n" % (self.job['btaddrtext'],self.job['bleaddrtext'],self.job['sntext']))

    def dispatch_burn_complt_evt(self):
        'dispatch burn complete event'
        self.job['stauts'] = 'done'
        self.statussignal.emit([self.job, 'Burn Succeed'])
        self.bar_signal.emit([self.job, 100])
        if self.update_elapse_timer is not None:
            self.update_elapse_timer.cancel()
        self.timecancel = True
        save_log_to_file("BURN SUCCESS. btaddr:%s  bleaddr%s sn:%s\n\n" % (self.job['btaddrtext'],self.job['bleaddrtext'],self.job['sntext']))        
        #delete using addr
        threads_mutex = get_mainproc_monitor_mutex()
        threads_mutex.acquire()
        if xml_get_update_sector_enable() == '1' and xml_get_update_btaddr_enable() == 1:
            using_btaddr = get_using_bt_addr() 
            try:
                using_btaddr.remove(self.job['btaddrtext'])
            except:
                bes_trace( "%s is not in using list\n" % self.job['btaddrtext'])
            set_using_bt_addr(using_btaddr)

        if xml_get_update_sector_enable() == '1' and xml_get_update_bleaddr_enable() == 1:
            using_bleaddr = get_using_ble_addr()                        
            try:
                using_bleaddr.remove(self.job['bleaddrtext'])
            except:
                bes_trace( "%s is not in using list\n" % self.job['bleaddrtext'])
            set_using_ble_addr(using_bleaddr)
        threads_mutex.release()

        
    def dispatch_ev_burn_efuse_start(self):
        '''dispatch_ev_burn_efuse_start'''
        #self.statussignal.emit([self.job, 'burn_eFuse_start'])
        pass

    def dispatch_ev_burn_efuse_end(self):
        '''dispatch_ev_burn_efuse_end'''
        #self.statussignal.emit([self.job, 'burn_eFuse_end'])
        pass

    def dispatch_burn_fail_evt(self,ret):
        'dispatch burn complete event'        
        if ret!=EXIT_CODE_WAIT_SYNC_ERROR:
            self.statussignal.emit([self.job, 'Failure', ret])
        if self.update_elapse_timer is not None:
            self.update_elapse_timer.cancel()
        self.timecancel = True
        if xml_getxmlcfg_is_fctrmdonly():
            save_log_to_file("FACTORY MODE FAIL 0x%x. \n\n" % (ret))
        else:
            save_log_to_file("BURN FAIL 0x%x. btaddr:%s  bleaddr%s\n\n" % (ret, self.job['btaddrtext'],self.job['bleaddrtext']))

    def dispatch_factory_mode(self):
        'dispatch msg factory mode'
        self.statussignal.emit([self.job, 'Testing'])
        self.bar_signal.emit([self.job, 0])
        self.begin = time.time()
        self.dldtime_signal.emit([self.job, "00:00"])        
        self.update_elapse_timer = Timer(1, self.update_elapse_func)
        self.update_elapse_timer.start()
        self.timecancel =False
        if xml_getxmlcfg_is_fctrmdonly():
            save_log_to_file("FACTORY MODE BEGIN. \n\n")
        else:
            save_log_to_file("FACTORY MODE BEGIN. btaddr:%s  bleaddr%s  sn:%s\n\n" % (self.job['btaddrtext'],self.job['bleaddrtext'],self.job['sntext']))        
        
    def dispatch_factory_mode_progress(self, msg):
        'dispatch msg burn progress'           
        if msg[1] >= 0 and msg[1] < 100:
            emit_string = 'Testing'
        elif msg[1] == 100:
            emit_string = 'Succeed'
        self.statussignal.emit([self.job, emit_string])
        self.bar_signal.emit([self.job, msg[1]])

    def dispatch_factory_mode_complt_evt(self):
        'dispatch burn complete event'
        self.job['stauts'] = 'done'
        self.statussignal.emit([self.job, 'Test Succeed'])
        self.bar_signal.emit([self.job, 100])
        if self.update_elapse_timer is not None:
            self.update_elapse_timer.cancel()
        self.timecancel = True
        if xml_getxmlcfg_is_fctrmdonly():
            save_log_to_file("FACTORY MODE SUCCESS. \n\n")
        else:
            save_log_to_file("FACTORY MODE SUCCESS. btaddr:%s  bleaddr%s  sn:%s\n\n" % (self.job['btaddrtext'],self.job['bleaddrtext'],self.job['sntext']))        

    def dispatch_factory_mode_fail_evt(self,ret):
        'dispatch burn complete event'
        self.statussignal.emit([self.job, 'Failure', ret])
        if self.update_elapse_timer is not None:
            self.update_elapse_timer.cancel()
        self.timecancel = True
        if xml_getxmlcfg_is_fctrmdonly():
            save_log_to_file("FACTORY MODE FAIL 0x%x. \n\n" % (ret))
        else:
            save_log_to_file("FACTORY MODE FAIL 0x%x. btaddr:%s  bleaddr%s  sn:%s\n\n" % (ret, self.job['btaddrtext'],self.job['bleaddrtext'],self.job['sntext']))        
        
    def dispatch_factory_calib_value(self, calib_value):
        'dispatch msg burn progress'           
        self.calibvalue_signal.emit([self.job, calib_value])
        if xml_getxmlcfg_is_fctrmdonly():
            save_log_to_file("CALIB VALUE is %d.\n\n" % (calib_value))
        else:
            save_log_to_file("CALIB VALUE is %d. btaddr:%s  bleaddr%s\n\n" % (calib_value, self.job['btaddrtext'],self.job['bleaddrtext']))
            
    def dispatch_wm_terminated(self):
        if self.update_elapse_timer is not None:
            self.update_elapse_timer.cancel()
        self.timecancel = True
        save_log_to_file("USER STOP BURN AND TEST. \n\n")
        
    def dispatch_encrypt_evt(self, param):
        if param == 'password_incorrect':
            self.statussignal.emit([self.job, 'password_incorrect'])
            self.dispatch_wm_terminated()

    def app_pipe_msg_monitor(self):
        'dispatch event from subprocess'
        #if (self.job['cfgmode'] & 0x4) == 0:
            #return
        dld_time_begin = 0
        while True:
            time.sleep(0.05)
            msg = self.job['parentconn'].recv()
            if msg[0] == 'ev_wm_burn_progress':
                self.dispatch_burn_progress(msg)
            elif msg[0] == 'ev_wm_sync_succeed':
                bes_trace( 'ev_wm_sync_succeed')
                self.dispatch_sync_succeed()
            elif msg[0] == 'ev_wm_bin_encrypt_begin':
                self.dispatch_encrypt_evt(msg[1])
            elif msg[0] == 'ev_wm_burn_magic':
                bes_trace( 'ev_wm_burn_magic')
            elif msg[0] == 'ev_wm_burn_complt':
                bes_trace( 'ev_wm_burn_complt')
                self.dispatch_burn_complt_evt()
            elif msg[0] == 'ev_wm_burn_failure':
                bes_trace( 'ev_wm_burn_failure')
                self.dispatch_burn_fail_evt(msg[1])
            elif msg[0] == 'ev_wm_chip_poweroff':
                bes_trace( 'ev_wm_chip_poweroff')
                self.dispatch_chip_poweroff_evt()
            elif msg[0] == 'ev_wm_burn_efuse_start':
                self.dispatch_ev_burn_efuse_start()
                bes_trace( 'ev_wm_burn_efuse_start')
            elif msg[0] == 'ev_wm_burn_efuse_end':
                self.dispatch_ev_burn_efuse_end()
            elif msg[0] == 'ev_wm_factory_mode':
                bes_trace( 'ev_wm_factory_mode')
                self.dispatch_factory_mode()
            elif msg[0] == 'ev_wm_factory_mode_progress':
                self.dispatch_factory_mode_progress(msg)
            elif msg[0] == 'ev_wm_factory_calib_value':
                self.dispatch_factory_calib_value(msg[1])
            elif msg[0] == 'ev_wm_factory_mode_success':
                bes_trace( 'ev_wm_factory_mode_success')
                self.dispatch_factory_mode_complt_evt()
            elif msg[0] == 'ev_wm_factory_mode_fail':
                bes_trace( 'ev_wm_factory_mode_fail')
                self.dispatch_factory_mode_fail_evt(msg[1])
            elif msg[0] == 'ev_wm_exit_valid':
                bes_trace( 'ev_wm_exit_valid')
                self.dispatch_exit_valid()
            elif msg[0] == 'ev_wm_exit_invalid':
                self.dispatch_exit_invalid(msg[1])
            elif msg[0] == 'ev_wm_terminated':
                self.dispatch_wm_terminated()
                break
            else:
                bes_trace( 'main process rcv unrecognized msg.')
                break
        bes_trace( 'app_pipe_msg_monitor over...')

