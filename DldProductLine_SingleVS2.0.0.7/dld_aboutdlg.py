# import sys,os
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
# from PyQt4 import uic
# import serial
# import time
from dld_global import *
from dld_xml_operate import *

class dld_aboutdlg(QDialog):
    def __init__(self, parent=None):
        super(dld_aboutdlg, self).__init__(parent)
        if cfg_as_updatetool() is False:
            display_text = '<b>Bes Download Tool </b><br>' +\
                                    ('-'*80)+'<br>' +\
                                    'Bes download tool used for its Bluetooth:<br>' +\
                                    '- BT: Bluetooth Legacy 3.0<br>' +\
                                    '- BLE: Bluetooth Low Energy<br>' +\
                                    '- BTDM: Bluetooth Dual Mode 4.0<br>' +\
                                    ('-'*80)+'<br>' +\
                                    '<b>Platform: Win32/64</b><br>' +\
                                    '<b>Version : '+'2.7'+'</b>'
        else:
            display_text = '<b>Bes Update Tool </b><br>' +\
                            '<b>Version : '+'2.7'+'</b>'
        self.setWindowTitle('About')
        self.setWindowIcon(QIcon('images/about.png'))
        
        #OK button for exit
        ok = QPushButton('&OK')
        self.connect(ok, SIGNAL("clicked()"), self.close)
        
        #image 
        pixmap = QPixmap(os.getcwd() +'/images/about.png')
        lbl_img = QLabel()
        lbl_img.setPixmap(pixmap)
        
        #About message label
        lbl_msg = QLabel(display_text)
        
        #Set button in horizontal layout pushed on right side to the max
        b_layout = QHBoxLayout()
        b_layout.addStretch()
        b_layout.addWidget(ok)
        
        ##image and label in horizontal layout
        layouth = QHBoxLayout()
        layouth.addWidget(lbl_img)
        layouth.addWidget(lbl_msg)
        
        #add label and button layout in dialog layout
        layoutv = QVBoxLayout()
        layoutv.addLayout(layouth)
        layoutv.addLayout(b_layout)
        
        self.setLayout(layoutv)
