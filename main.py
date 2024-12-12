import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from dialogs.sdc_dlgcontrol import SDC_DlgControl
import resources # import the resources for the ui

if __name__ == '__main__':
    return_value = 0
    start = True

    app = QApplication(sys.argv)
    dlg_control = SDC_DlgControl(start)

    if dlg_control.started:
        dlg_control.show()
        return_value = app.exec_()

    sys.exit(return_value)