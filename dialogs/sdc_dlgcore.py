from enum import Enum

from PyQt5.QtWidgets import QWidget, QComboBox, QSpinBox, QDial, QPushButton, QGroupBox
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtGui import QIcon
from settings.sdc_coresettings import SDC_CoreSettings

# ********************************************************************************************************
# ***** Public Constructor
# ********************************************************************************************************
class SDC_DlgCore(QWidget):
    SETTING = Enum('SETTING', ['NONE', 'CORENUM', 'AMPLITUDE', 'FREQUENCY', 'PHASE'])

    # signals
    sigRemoveCoreDialog = pyqtSignal(int)
    sigCoreNumChanged = pyqtSignal(int, int)

    def __init__(self, lDlgID : int, lCoreNum : int, lChannelNum : int, bFixCoreNum : bool, poHwControl, poParent):
        #print("SDC_DlgCore::__init__")
        super().__init__(poParent)
        self.m_lDlgID      = lDlgID
        self.m_lCoreNum    = lCoreNum
        self.m_lChannelNum = lChannelNum
        self.m_bFixCoreNum = bFixCoreNum
        self.m_poHwControl = poHwControl
        self.m_eUpdateSetting = None
    
        bDDS50 = self.m_poHwControl.poGetCurrentDevice().bIsDDS50()

        self.m_poCoreSettings = SDC_CoreSettings(self.m_lCoreNum, bDDS50)
        self.m_poHwControl.dwGetCoreInfos(self.m_poCoreSettings)
        
        self.ui = uic.loadUi("formfiles/DlgDDSCore.ui", self)
        
        self.m_poTimerUpdate = QTimer(self)
        self.m_poTimerUpdate.setSingleShot(True)
        self.m_poTimerUpdate.timeout.connect(self.slTimeoutUpdate)

        self.poSpinBoxCoreNum.setValue(lCoreNum)
        self.vSetAllowedChannels(lCoreNum, lChannelNum)

        self.vUpdateGroupTitle()

        if self.m_bFixCoreNum:
            self.poLabelCoreNum.setHidden(True)
            self.poSpinBoxCoreNum.setHidden(True)
            self.poButtonRemove.setHidden(True)
            self.poComboBoxChannels.setHidden(True)
            
        self.poButtonRemove.vSetIcons(QIcon(":/resources/remove.png"), QIcon(":/resources/remove_hover.png"))

        # init amplitude settings
        self.poDialAmplitude.setRange(int(self.m_poCoreSettings.oGetAmplitude().dGetMin() * 100), int(self.m_poCoreSettings.oGetAmplitude().dGetMax() * 100))
        self.poSpinBoxAmplitude.setRange(self.m_poCoreSettings.oGetAmplitude().dGetMin() * 100, self.m_poCoreSettings.oGetAmplitude().dGetMax() * 100)
        self.poSpinBoxAmplitude.setSingleStep(1)

        # init frequency settings
        self.poDialFrequency.setRange(int(self.m_poCoreSettings.oGetFrequency().dGetMin() / 1000000.0), int(self.m_poCoreSettings.oGetFrequency().dGetMax() / 1000000.0))
        self.poSpinBoxFrequency.setRange(self.m_poCoreSettings.oGetFrequency().dGetMin() / 1000000.0, self.m_poCoreSettings.oGetFrequency().dGetMax() / 1000000.0)
        self.poSpinBoxFrequency.setSingleStep(0.01)

        # init phase settings
        self.poDialPhase.setRange(int(self.m_poCoreSettings.oGetPhase().dGetMin()), int(self.m_poCoreSettings.oGetPhase().dGetMax()))
        self.poSpinBoxPhase.setRange(self.m_poCoreSettings.oGetPhase().dGetMin(), self.m_poCoreSettings.oGetPhase().dGetMax())
        self.poSpinBoxPhase.setSingleStep(1)

        self.poButtonRemove.clicked.connect(self.slButtonRemove)
        self.poDialAmplitude.sliderReleased.connect(self.slDialAmplitudeChanged)
        self.poDialFrequency.sliderReleased.connect(self.slDialFrequencyChanged)
        self.poDialPhase.sliderReleased.connect(self.slDialPhaseChanged)
        self.poDialAmplitude.valueChanged.connect(self.slDialAmplitudeChanged)
        self.poDialFrequency.valueChanged.connect(self.slDialFrequencyChanged)
        self.poDialPhase.valueChanged.connect(self.slDialPhaseChanged)
        self.poSpinBoxCoreNum.valueChanged.connect(self.slCoreNumChanged)
        self.poSpinBoxAmplitude.valueChanged.connect(self.slAmplitudeChanged)
        self.poSpinBoxFrequency.valueChanged.connect(self.slFrequencyChanged)
        self.poSpinBoxPhase.valueChanged.connect(self.slPhaseChanged)
        self.poComboBoxChannels.currentIndexChanged.connect(self.slChannelSelectionChanged)

        # default settings
        self.poDialAmplitude.setValue(20)
        self.slDialAmplitudeChanged()

        self.poDialFrequency.setValue(5)
        self.slDialFrequencyChanged()

        self.poDialPhase.setValue(0)
        self.slDialPhaseChanged()

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def poGetCoreSettings(self):
        #print("SDC_DlgCore::poGetCoreSettings")
        self.m_poCoreSettings.vSetCoreIndex(self.poSpinBoxCoreNum.value())
        self.m_poCoreSettings.vSetChannel(self.poComboBoxChannels.currentData())
        self.m_poCoreSettings.vSetAmplitude(self.poSpinBoxAmplitude.value() / 100.0)
        self.m_poCoreSettings.vSetFrequency(self.poSpinBoxFrequency.value() * 1000000.0)
        self.m_poCoreSettings.vSetPhase(self.poSpinBoxPhase.value())

        return self.m_poCoreSettings

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def vSetCoreSettings(self, oCoreSettings):
        #print("SDC_DlgCore::vSetCoreSettings")
        self.poSpinBoxCoreNum.setValue(oCoreSettings.lGetCoreIndex())

        self.vSetAllowedChannels(oCoreSettings.lGetCoreIndex())

        self.vSetChannelNum(oCoreSettings.lGetChannel())

        self.poSpinBoxAmplitude.setValue(oCoreSettings.oGetAmplitude().dGetValue() * 100.0)
        self.poDialAmplitude.setValue(int(self.poSpinBoxAmplitude.value()))

        self.poSpinBoxFrequency.setValue(oCoreSettings.oGetFrequency().dGetValue() / 1000000.0)
        self.poDialFrequency.setValue(int(self.poSpinBoxFrequency.value()))

        self.poSpinBoxPhase.setValue(oCoreSettings.oGetPhase().dGetValue())
        self.poDialPhase.setValue(int(self.poSpinBoxPhase.value()))

    # ********************************************************************************************************
    # ***** Public Slot
    # ********************************************************************************************************
    def slExtCoreNumChanged(self, lCoreNum : int, lChNum : int):
        #print("SDC_DlgCore::slExtCoreNumChanged")
        # ch1 group
        if ((lCoreNum >= 8 and lCoreNum <= 11) and (self.m_lCoreNum >= 8 and self.m_lCoreNum <= 11)):
            if (lChNum != self.m_lChannelNum):
                self.vSetChannelNum(lChNum)
                
        # ch2 group
        if ((lCoreNum >= 12 and lCoreNum <= 15) and (self.m_lCoreNum >= 12 and self.m_lCoreNum <= 15)):
            if (lChNum != self.m_lChannelNum):
                self.vSetChannelNum(lChNum)
            
        if ((lCoreNum >= 16 and lCoreNum <= 19) and (self.m_lCoreNum >= 16 and self.m_lCoreNum <= 19)):
            if (lChNum != self.m_lChannelNum):
                self.vSetChannelNum(lChNum)

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vUpdateGroupTitle(self):
        #print("SDC_DlgCore::vUpdateGroupTitle")
        sTitle = "Ch {} | Core {}".format(self.poComboBoxChannels.currentData(), self.poSpinBoxCoreNum.value())
        self.poGroupCore.setTitle(sTitle)

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vSetAllowedChannels(self, lCoreNum : int, lDefaultChNum : int = -1):
        #print("SDC_DlgCore::vSetAllowedChannels")
        mlsAllowedChannels = self.m_poCoreSettings.mlsGetAllowedChannels(lCoreNum)

        self.poComboBoxChannels.clear()

        # QMapIterator <int, QString> itMap (mlsAllowedChannels);
        for key, allowed_channel in mlsAllowedChannels.items():
            self.poComboBoxChannels.addItem(allowed_channel, key)

        if lDefaultChNum >= 0:
            lIndex = self.poComboBoxChannels.findData(lDefaultChNum)
            if lIndex > -1:
                self.poComboBoxChannels.setCurrentIndex(lIndex)

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slChannelSelectionChanged(self):
        #print("SDC_DlgCore::slChannelSelectionChanged")
        try:
            m_lChannelNum = int(self.poComboBoxChannels.currentData())
        except TypeError:
            m_lChannelNum = 0
        self.vUpdateGroupTitle()

        self.sigCoreNumChanged.emit(self.m_lCoreNum, m_lChannelNum)

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slButtonRemove(self):
        #print("SDC_DlgCore::slButtonRemove")
        self.sigRemoveCoreDialog.emit(self.m_lDlgID)

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slDialAmplitudeChanged(self, lValue : float = None):
        #print("SDC_DlgCore::slDialAmplitudeChanged")
        if lValue is None:
            self.poSpinBoxPhase.setValue(self.poDialPhase.value())
            self.vPhaseChanged()
        else:
            self.poSpinBoxAmplitude.setValue(lValue)
    
    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slDialFrequencyChanged(self, lValue : int = None):
        #print("SDC_DlgCore::slDialFrequencyChanged")
        if lValue is None:
            self.poSpinBoxFrequency.setValue(self.poDialFrequency.value())
            self.vFrequencyChanged()
        else:
            self.poSpinBoxFrequency.setValue(lValue)

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slDialPhaseChanged(self, lValue : int = None):
        if lValue is None:
            self.poSpinBoxFrequency.setValue(self.poDialFrequency.value())
            self.vPhaseChanged()
        else:
            self.poSpinBoxPhase.setValue(lValue)

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slCoreNumChanged(self):
        self.m_eUpdateSetting = self.SETTING.CORENUM
        self.m_poTimerUpdate.start(500)

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slAmplitudeChanged(self):
        self.m_eUpdateSetting = self.SETTING.AMPLITUDE
        self.m_poTimerUpdate.start (200)

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slFrequencyChanged(self):
        self.m_eUpdateSetting = self.SETTING.FREQUENCY
        self.m_poTimerUpdate.start(200)

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slPhaseChanged(self):
        self.m_eUpdateSetting = self.SETTING.PHASE
        self.m_poTimerUpdate.start(200)

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slTimeoutUpdate(self):
        if self.m_eUpdateSetting == self.SETTING.CORENUM:
            self.vCoreNumChanged()
        elif self.m_eUpdateSetting == self.SETTING.AMPLITUDE:
            self.vAmplitudeChanged()
        elif self.m_eUpdateSetting == self.SETTING.FREQUENCY:
            self.vFrequencyChanged()
        elif self.m_eUpdateSetting == self.SETTING.PHASE:
            self.vPhaseChanged() 

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vSetChannelNum(self, lChNum : int):
        self.poComboBoxChannels.currentIndexChanged.disconnect(self.slChannelSelectionChanged)

        lIndex = self.poComboBoxChannels.findData(lChNum)
        if lIndex > -1:
            self.m_lChannelNum = lChNum
            self.poComboBoxChannels.setCurrentIndex(lIndex)

            self.vUpdateGroupTitle()

        self.poComboBoxChannels.currentIndexChanged.connect(self.slChannelSelectionChanged)

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vCoreNumChanged(self):
        self.m_lCoreNum = self.poSpinBoxCoreNum.value()

        if not self.m_bFixCoreNum:
            self.vSetAllowedChannels(self.m_lCoreNum, self.m_lChannelNum)

        self.vUpdateGroupTitle()

        self.sigCoreNumChanged.emit(self.m_lCoreNum, self.m_lChannelNum)

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vAmplitudeChanged(self):
        dValue = self.poSpinBoxAmplitude.value() / 100.0
        self.m_poHwControl.dwSetAmplitude(self.m_lCoreNum, dValue)
        self.poSpinBoxAmplitude.setValue(dValue * 100.0)

        self.poDialAmplitude.setValue(int(self.poSpinBoxAmplitude.value()))

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vFrequencyChanged(self):
        dValue = self.poSpinBoxFrequency.value() * 1000000.0
        self.m_poHwControl.dwSetFrequency(self.m_lCoreNum, dValue)
        self.poSpinBoxFrequency.setValue(dValue / 1000000.0)

        self.poDialFrequency.setValue(int(self.poSpinBoxFrequency.value()))

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vPhaseChanged(self):
        dValue = self.poSpinBoxPhase.value()
        self.m_poHwControl.dwSetPhase(self.m_lCoreNum, dValue)
        self.poSpinBoxPhase.setValue(dValue)

        self.poDialPhase.setValue(int(self.poSpinBoxPhase.value()))

    # ********************************************************************************************************
