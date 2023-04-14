import sys
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
from dld_global import *

class dld_file:
    def __init__(self,filename):
        self.filename = filename
        self.fp = 0
        
    def openfile(self):
        self.fp = open(filename,'rb')

    def readfile(self):
        try:
            self.openfile()
            data = self.fp.read()
        finally:
            self.fp.close()        