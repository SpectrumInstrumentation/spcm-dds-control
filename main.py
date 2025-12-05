import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore

from dialogs.sdc_dlgcontrol import SDC_DlgControl
import resources # import the resources for the ui

DEBUG_MODE = 1 # 0 = off, 1 = file, 2 = console
DEBUG_FILE = 'spcm-dds-control.log'

if DEBUG_MODE:
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    if DEBUG_MODE == 1:
        # create file handler and set level to debug
        logging.basicConfig(filename=DEBUG_FILE, filemode='w', level=logging.DEBUG, format=format_str)
    else:
        # create console handler and set level to debug
        logging.basicConfig(level=logging.DEBUG, format=format_str)

if __name__ == '__main__':
    return_value = 0

    app = QApplication(sys.argv)
    dlg_control = SDC_DlgControl()

    if dlg_control.started:
        dlg_control.show()
        return_value = app.exec_()
    
    del dlg_control

    sys.exit(return_value)