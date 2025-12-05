#include "sdc_dlgsettings.h"
from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from PyQt5.QtCore import Qt

import logging

from settings.sdc_settings import SDC_Settings


class SDC_DlgSettings(QDialog):
    m_poSettings : SDC_Settings = None
    ui : QDialog = None
    
    
    def __init__(self, poParent = None):
        logging.debug("SDC_DlgSettings::__init__")
        super().__init__(poParent)
    
        self.m_poSettings = SDC_Settings.poGetInstance()
        
        self.ui = uic.loadUi("formfiles/DlgSettings.ui", self)
        self.ui.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)
        
        self.ui.poCheckBoxSaveExit.setChecked(self.m_poSettings.bSaveOnExit())
        self.ui.poCheckBoxCompactCoreDialogs.setChecked(self.m_poSettings.bCompactCoreDialogs())

        self.ui.poButtonCancel.clicked.connect(self.close)
        self.ui.poButtonOk.clicked.connect(self.slButtonOk)

    def slButtonOk(self):
        logging.debug("SDC_DlgSettings::slButtonOk")
        self.m_poSettings.vSetSaveOnExit(self.ui.poCheckBoxSaveExit.isChecked())
        self.m_poSettings.vSetCompactCoreDialogs(self.ui.poCheckBoxCompactCoreDialogs.isChecked())
        
        self.accept()

# ********************************************************************************************************