#include "sdc_dlgsettings.h"
from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from PyQt5.QtCore import Qt

from settings.sdc_settings import SDC_Settings

# ********************************************************************************************************
# ***** Public Constructor
# ********************************************************************************************************
class SDC_DlgSettings(QDialog):
    m_poSettings : SDC_Settings = None
    ui : QDialog = None
    
    def __init__(self, poParent = None):
        #print("SDC_DlgSettings::__init__")
        super().__init__(poParent)
    
        self.m_poSettings = SDC_Settings()
        
        self.ui = uic.loadUi("formfiles/DlgSettings.ui", self)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)
        
        self.poCheckBoxSaveExit.setChecked(self.m_poSettings.bSaveOnExit())

        self.poButtonCancel.clicked.connect(self.close)
        self.poButtonOk.clicked.connect(self.slButtonOk)

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slButtonOk(self):
        #print("SDC_DlgSettings::slButtonOk")
        self.m_poSettings.vSetSaveOnExit(self.poCheckBoxSaveExit.isChecked())
        
        self.close()

# ********************************************************************************************************