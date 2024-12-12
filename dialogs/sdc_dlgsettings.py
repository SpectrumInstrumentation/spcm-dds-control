#include "sdc_dlgsettings.h"
from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from PyQt5.QtCore import Qt

from settings.sdc_settings import SDC_Settings

# ********************************************************************************************************
# ***** Public Constructor
# ********************************************************************************************************
class SDC_DlgSettings(QDialog):
    
    def __init__(self, poParent = None):
        super().__init__(poParent)
    
        self.m_poSettings = SDC_Settings()
        #print("SDC_DlgSettings::__init__ - bSaveOnExit: {}".format(self.m_poSettings.bSaveOnExit()))
        
        self.ui = uic.loadUi("formfiles/DlgSettings.ui", self)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)
        
        #print("SDC_DlgSettings::__init__ - bSaveOnExit: {}".format(self.m_poSettings.bSaveOnExit()))
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