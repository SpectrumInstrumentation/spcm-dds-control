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
DEBUG_EXCLUDES = [
    # add any filenames here to exclude them from debug logging
    "sdc_components.py",
]
# empty the debug log file at start
with open(DEBUG_FILE, 'w+') as log_file:
    pass

def excepthook(cls, exception, traceback):
    logging.error("{}".format(exception))
sys.excepthook = excepthook

# def qt_message_handler(mode, context, message):
#     """Custom Qt message handler that still shows Python exceptions."""
#     # Forward to original handler so normal logging still happens
#     if mode == QtCore.QtInfoMsg:
#         mode = 'INFO'
#     elif mode == QtCore.QtWarningMsg:
#         mode = 'WARNING'
#     elif mode == QtCore.QtCriticalMsg:
#         mode = 'CRITICAL'
#     elif mode == QtCore.QtFatalMsg:
#         mode = 'FATAL'
#     else:
#         mode = 'DEBUG'

#     if DEBUG_MODE:
#         filename = os.path.basename(context.file)
#         if filename in DEBUG_EXCLUDES:
#             return
#         message_str = f'{mode} file: {filename}, line: {context.line}, func: {context.function}()\t{message}\n'
#         if DEBUG_MODE == 1: # write to file
#             with open(DEBUG_FILE, 'a') as log_file:
#                 log_file.write(message_str)
#         elif DEBUG_MODE == 2: # print to console
#             print(message_str)

# # install the custom message handler
# QtCore.qInstallMessageHandler(qt_message_handler)

if __name__ == '__main__':
    return_value = 0

    app = QApplication(sys.argv)
    dlg_control = SDC_DlgControl()

    if dlg_control.started:
        dlg_control.show()
        return_value = app.exec_()
    
    del dlg_control

    sys.exit(return_value)