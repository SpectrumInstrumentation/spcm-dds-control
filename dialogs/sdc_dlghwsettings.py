#include "sdc_dlghwsettings.h"
from PyQt5.QtWidgets import QDialog, QWidget
from PyQt5 import uic
from PyQt5.QtCore import Qt

import logging

from control.sdc_spcdevice import SDC_SpcDevice

MAX_CHANNELS = 8


class SDC_DlgHwSettings(QDialog):
    m_poDevice : SDC_SpcDevice = None
    ui : QWidget = None

    # DONE
    def __init__(self, poDevice, poParent = None):
        logging.debug("SDC_DlgHwSettings::__init__")
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


	# void slButtonOk ();
    # DONE
    def slButtonOk(self):
        logging.debug("SDC_DlgHwSettings::slButtonOk")
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
                elif lChIdx ==  4:
                    oChSettings.vSetOutputEnabled(self.poComboBoxOutputEnableCh4.currentIndex())
                    oChSettings.vSetOutputRange_mV(self.poSpinBoxOutputRangeCh4.value())
                    oChSettings.vSetFilter(self.poComboBoxFilterCh4.currentIndex())
                elif lChIdx ==  5:
                    oChSettings.vSetOutputEnabled(self.poComboBoxOutputEnableCh5.currentIndex())
                    oChSettings.vSetOutputRange_mV(self.poSpinBoxOutputRangeCh5.value())
                    oChSettings.vSetFilter(self.poComboBoxFilterCh5.currentIndex())
                elif lChIdx ==  6:
                    oChSettings.vSetOutputEnabled(self.poComboBoxOutputEnableCh6.currentIndex())
                    oChSettings.vSetOutputRange_mV(self.poSpinBoxOutputRangeCh6.value())
                    oChSettings.vSetFilter(self.poComboBoxFilterCh6.currentIndex())
                elif lChIdx ==  7:
                    oChSettings.vSetOutputEnabled(self.poComboBoxOutputEnableCh7.currentIndex())
                    oChSettings.vSetOutputRange_mV(self.poSpinBoxOutputRangeCh7.value())
                    oChSettings.vSetFilter(self.poComboBoxFilterCh7.currentIndex())

                self.m_poDevice.vSetChSettings(lChIdx, oChSettings)

        self.close()

	
	# void vInitSettings ();
    # DONE
    def vInitSettings(self):
        logging.debug("SDC_DlgHwSettings::vInitSettings")
        for lChIdx in range(MAX_CHANNELS):
            if lChIdx < self.m_poDevice.lGetNumMaxChannels():
                self.vHideChannelSettings(False, lChIdx)

                oChSettings = self.m_poDevice.oGetChSettings(lChIdx)

                if lChIdx == 0:
                    self.poSpinBoxOutputRangeCh0.setValue(oChSettings.lGetOutputRange_mV())
                    self.poComboBoxOutputEnableCh0.setCurrentIndex(oChSettings.lOutputEnabled())
                    self.poComboBoxFilterCh0.setCurrentIndex(oChSettings.lGetFilter())
                elif lChIdx == 1:
                    self.poSpinBoxOutputRangeCh1.setValue(oChSettings.lGetOutputRange_mV())
                    self.poComboBoxOutputEnableCh1.setCurrentIndex(oChSettings.lOutputEnabled())
                    self.poComboBoxFilterCh1.setCurrentIndex(oChSettings.lGetFilter())
                elif lChIdx == 2:
                    self.poSpinBoxOutputRangeCh2.setValue(oChSettings.lGetOutputRange_mV())
                    self.poComboBoxOutputEnableCh2.setCurrentIndex(oChSettings.lOutputEnabled())
                    self.poComboBoxFilterCh2.setCurrentIndex(oChSettings.lGetFilter())
                elif lChIdx == 3:
                    self.poSpinBoxOutputRangeCh3.setValue(oChSettings.lGetOutputRange_mV())
                    self.poComboBoxOutputEnableCh3.setCurrentIndex(oChSettings.lOutputEnabled())
                    self.poComboBoxFilterCh3.setCurrentIndex(oChSettings.lGetFilter())
                elif lChIdx == 4:
                    self.poSpinBoxOutputRangeCh4.setValue(oChSettings.lGetOutputRange_mV())
                    self.poSpinBoxOutputRangeCh4.setMaximum(oChSettings.lGetMaxOutputRange_mV())
                    self.poComboBoxOutputEnableCh4.setCurrentIndex(oChSettings.lOutputEnabled())
                    self.poComboBoxFilterCh4.setCurrentIndex(oChSettings.lGetFilter())
                elif lChIdx == 5:
                    self.poSpinBoxOutputRangeCh5.setValue(oChSettings.lGetOutputRange_mV())
                    self.poSpinBoxOutputRangeCh5.setMaximum(oChSettings.lGetMaxOutputRange_mV())
                    self.poComboBoxOutputEnableCh5.setCurrentIndex(oChSettings.lOutputEnabled())
                    self.poComboBoxFilterCh5.setCurrentIndex(oChSettings.lGetFilter())
                elif lChIdx == 6:
                    self.poSpinBoxOutputRangeCh6.setValue(oChSettings.lGetOutputRange_mV())
                    self.poSpinBoxOutputRangeCh6.setMaximum(oChSettings.lGetMaxOutputRange_mV())
                    self.poComboBoxOutputEnableCh6.setCurrentIndex(oChSettings.lOutputEnabled())
                    self.poComboBoxFilterCh6.setCurrentIndex(oChSettings.lGetFilter())
                elif lChIdx == 7:
                    self.poSpinBoxOutputRangeCh7.setValue(oChSettings.lGetOutputRange_mV())
                    self.poSpinBoxOutputRangeCh7.setMaximum(oChSettings.lGetMaxOutputRange_mV())
                    self.poComboBoxOutputEnableCh7.setCurrentIndex(oChSettings.lOutputEnabled())
                    self.poComboBoxFilterCh7.setCurrentIndex(oChSettings.lGetFilter())
            else:
                self.vHideChannelSettings(True, lChIdx)

	# void vHideChannelSettings (bool bHide, int lNumChannel);
    # DONE
    def vHideChannelSettings(self, bHide : bool, lNumChannel : int):
        logging.debug("SDC_DlgHwSettings::vHideChannelSettings")
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
        elif lNumChannel == 4:
            self.poLabelCh4.setHidden(bHide)
            self.poComboBoxOutputEnableCh4.setHidden(bHide)
            self.poSpinBoxOutputRangeCh4.setHidden(bHide)
            self.poComboBoxFilterCh4.setHidden(bHide)
        elif lNumChannel == 5:
            self.poLabelCh5.setHidden(bHide)
            self.poComboBoxOutputEnableCh5.setHidden(bHide)
            self.poSpinBoxOutputRangeCh5.setHidden(bHide)
            self.poComboBoxFilterCh5.setHidden(bHide)
        elif lNumChannel == 6:
            self.poLabelCh6.setHidden(bHide)
            self.poComboBoxOutputEnableCh6.setHidden(bHide)
            self.poSpinBoxOutputRangeCh6.setHidden(bHide)
            self.poComboBoxFilterCh6.setHidden(bHide)
        elif lNumChannel == 7:
            self.poLabelCh7.setHidden(bHide)
            self.poComboBoxOutputEnableCh7.setHidden(bHide)
            self.poSpinBoxOutputRangeCh7.setHidden(bHide)
            self.poComboBoxFilterCh7.setHidden(bHide)