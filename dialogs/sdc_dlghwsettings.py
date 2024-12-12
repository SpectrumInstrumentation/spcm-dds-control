#include "sdc_dlghwsettings.h"
from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from PyQt5.QtCore import Qt

MAX_CHANNELS = 4

# ********************************************************************************************************
# ***** Public Constructor
# ********************************************************************************************************
class SDC_DlgHwSettings(QDialog):
    def __init__(self, poDevice, poParent = None):
        #print("SDC_DlgHwSettings::__init__")
        super().__init__(poParent)

        self.m_poDevice = poDevice
        
        self.ui = uic.loadUi("formfiles/DlgHwSettings.ui", self)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)
    
        self.vInitSettings()

        self.poButtonCancel.clicked.connect(self.close)
        self.poButtonOk.clicked.connect(self.slButtonOk)

        self.poButtonOk.setFocus()

        self.show()
        oSize = self.geometry()
        oSize.setHeight(20)

        self.setGeometry(oSize)

# ********************************************************************************************************
# ***** Private Method
# ********************************************************************************************************
    def vInitSettings(self):
        #print("SDC_DlgHwSettings::vInitSettings")
        for lChIdx in range(MAX_CHANNELS):
            if lChIdx < self.m_poDevice.lGetNumMaxChannels():
                self.vHideChannelSettings(False, lChIdx)

                oChSettings = self.m_poDevice.oGetChSettings(lChIdx)

                if lChIdx == 0:
                    self.poSpinBoxOutputRangeCh0.setValue(oChSettings.lGetOutputRange_mV())
                    self.poComboBoxOutputEnableCh0.setCurrentIndex(oChSettings.lOutputEnabled())
                    self.poComboBoxFilterCh0.setCurrentIndex(oChSettings.lGetFilter())
                elif lChIdx ==  1:
                    self.poSpinBoxOutputRangeCh1.setValue(oChSettings.lGetOutputRange_mV())
                    self.poComboBoxOutputEnableCh1.setCurrentIndex(oChSettings.lOutputEnabled())
                    self.poComboBoxFilterCh1.setCurrentIndex(oChSettings.lGetFilter())
                elif lChIdx ==  2:
                    self.poSpinBoxOutputRangeCh2.setValue(oChSettings.lGetOutputRange_mV())
                    self.poComboBoxOutputEnableCh2.setCurrentIndex(oChSettings.lOutputEnabled())
                    self.poComboBoxFilterCh2.setCurrentIndex(oChSettings.lGetFilter())
                elif lChIdx ==  3:
                    self.poSpinBoxOutputRangeCh3.setValue(oChSettings.lGetOutputRange_mV())
                    self.poComboBoxOutputEnableCh3.setCurrentIndex(oChSettings.lOutputEnabled())
                    self.poComboBoxFilterCh3.setCurrentIndex(oChSettings.lGetFilter())
            else:
                self.vHideChannelSettings(True, lChIdx)

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vHideChannelSettings(self, bHide : bool, lNumChannel : int):
        #print("SDC_DlgHwSettings::vHideChannelSettings")
        if lNumChannel == 0:
            self.poLabelCh0.setHidden(bHide)
            self.poComboBoxOutputEnableCh0.setHidden(bHide)
            self.poSpinBoxOutputRangeCh0.setHidden(bHide)
            self.poComboBoxFilterCh0.setHidden(bHide)
        elif lNumChannel == 1:
            self.poLabelCh1.setHidden(bHide)
            self.poComboBoxOutputEnableCh1.setHidden(bHide)
            self.poSpinBoxOutputRangeCh1.setHidden(bHide)
            self.poComboBoxFilterCh1.setHidden(bHide)
        elif lNumChannel == 2:
            self.poLabelCh2.setHidden(bHide)
            self.poComboBoxOutputEnableCh2.setHidden(bHide)
            self.poSpinBoxOutputRangeCh2.setHidden(bHide)
            self.poComboBoxFilterCh2.setHidden(bHide)
        elif lNumChannel == 3:
            self.poLabelCh3.setHidden(bHide)
            self.poComboBoxOutputEnableCh3.setHidden(bHide)
            self.poSpinBoxOutputRangeCh3.setHidden(bHide)
            self.poComboBoxFilterCh3.setHidden(bHide)

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slButtonOk(self):
        #print("SDC_DlgHwSettings::slButtonOk")
        for lChIdx in range(MAX_CHANNELS):
            if lChIdx < self.m_poDevice.lGetNumMaxChannels():
                oChSettings = self.m_poDevice.oGetChSettings(lChIdx)

                if lChIdx == 0:
                    oChSettings.vSetOutputEnabled(self.poComboBoxOutputEnableCh0.currentIndex())
                    oChSettings.vSetOutputRange_mV(self.poSpinBoxOutputRangeCh0.value())
                    oChSettings.vSetFilter(self.poComboBoxFilterCh0.currentIndex())
                elif lChIdx == 1:
                    oChSettings.vSetOutputEnabled(self.poComboBoxOutputEnableCh1.currentIndex())
                    oChSettings.vSetOutputRange_mV(self.poSpinBoxOutputRangeCh1.value())
                    oChSettings.vSetFilter(self.poComboBoxFilterCh1.currentIndex())
                elif lChIdx == 2:
                    oChSettings.vSetOutputEnabled(self.poComboBoxOutputEnableCh2.currentIndex())
                    oChSettings.vSetOutputRange_mV(self.poSpinBoxOutputRangeCh2.value())
                    oChSettings.vSetFilter(self.poComboBoxFilterCh2.currentIndex())
                elif lChIdx == 3:
                    oChSettings.vSetOutputEnabled(self.poComboBoxOutputEnableCh3.currentIndex())
                    oChSettings.vSetOutputRange_mV(self.poSpinBoxOutputRangeCh3.value())
                    oChSettings.vSetFilter(self.poComboBoxFilterCh3.currentIndex())

                self.m_poDevice.vSetChSettings (lChIdx, oChSettings)

        self.close()

# ********************************************************************************************************