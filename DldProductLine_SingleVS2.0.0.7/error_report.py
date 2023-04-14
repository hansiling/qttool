from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os


class ErrorReportDlg(QDialog):
    def __init__(self, error_text):
        super(ErrorReportDlg, self).__init__()
        self.setWindowTitle('Error')
        self.setWindowIcon(QIcon('images/error.png'))
        ok_btn = QPushButton('&OK')
        self.connect(ok_btn, SIGNAL("clicked()"), self.close)
        qpixmap_obj = QPixmap(os.getcwd() + '/images/error.png')
        lbl_img = QLabel()
        lbl_img.setPixmap(qpixmap_obj)
        lbl_msg = QLabel(error_text)
        b_layout = QHBoxLayout()
        b_layout.addStretch()
        b_layout.addWidget(ok_btn)

        layout_h = QHBoxLayout()
        layout_h.addWidget(lbl_img)
        layout_h.addWidget(lbl_msg)

        layoutv = QVBoxLayout()
        layoutv.addLayout(layout_h)
        layoutv.addLayout(b_layout)

        self.setLayout(layoutv)