from enum import IntEnum, Enum
import logging

from PyQt5.QtWidgets import QWidget, QGridLayout, QMenu, QTableWidgetItem
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QTimer, QSignalMapper, Qt
from PyQt5.QtGui import QIcon
from control.sdc_control import SDC_Control
from control.sdc_hwcontrol import SDC_HwControl, SDC_HwStatusThread, SDC_DrvCmd
from control.sdc_spcdevice import SDC_SpcDevice
from settings.sdc_coresettings import SDC_CoreSettings
from settings.sdc_settings import SDC_Settings, SDC_GuiMode


class SDC_DlgCore(QWidget):
    SETTING = Enum('SETTING', ['NONE', 'CORENUM', 'AMPLITUDE', 'FREQUENCY', 'PHASE'])
    class FLAGS(IntEnum):
        NOFIXCORENUM = 0x00000001
        COMPACT = 0x00000002
    m_lDlgID : int = 0
    m_lCoreNum : int = 0
    m_lChannelNum : int = 0
    m_lChCoreIndex : int = 0
    m_dwFlags : int = 0
    m_eUpdateSetting : SETTING = None
    m_poTimerUpdate : QTimer = None
    m_poHwControl : SDC_HwControl = None
    m_poSettings : SDC_Settings = None
    m_poCoreSettings : SDC_CoreSettings = None
    ui : QWidget = None
    m_poParent : QWidget = None

    def __init__(self, lDlgID : int, lCoreNum : int, lChannelNum : int, lChCoreIndex : int, poHwControl : SDC_HwControl, dwFlags : int , poParent : QWidget = None):
        logging.debug("SDC_DlgCore::__init__")
        super().__init__(poParent, flags=Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.m_lDlgID = lDlgID
        self.m_lCoreNum = lCoreNum
        self.m_lChannelNum = lChannelNum
        self.m_lChCoreIndex = lChCoreIndex
        self.m_poHwControl = poHwControl
        self.m_eUpdateSetting = None
        
        self.m_poSettings = SDC_Settings.poGetInstance()

        bDDS50 = self.m_poHwControl.poGetCurrentDevice().bIsDDS50()

        lSN = self.m_poHwControl.poGetCurrentDevice().lGetSerialNumber()

        bUseDefaultValue = False
        self.m_poCoreSettings = self.m_poSettings.poGetCoreSetting(lSN, lDlgID)
        if not self.m_poCoreSettings:
            self.m_poCoreSettings = SDC_CoreSettings(self.m_lDlgID, self.m_lCoreNum, self.m_lChannelNum, bDDS50)
            self.m_poSettings.vAddCoreSetting(lSN, self.m_poCoreSettings)
            bUseDefaultValue = True

        if not self.m_poCoreSettings.bLimitsSet():
            self.m_poHwControl.dwGetCoreInfos(self.m_poCoreSettings)

        self.ui = uic.loadUi("formfiles/DlgDDSCore.ui", self)
        
        self.vSetFlags(dwFlags)

        self.m_poTimerUpdate = QTimer(self)
        self.m_poTimerUpdate.setSingleShot(True)
        self.m_poTimerUpdate.timeout.connect(self.slTimeoutUpdate)

        self.ui.poSpinBoxCoreNum.setValue(lCoreNum)
        self.vSetAllowedChannels(lCoreNum, lChannelNum)

        self.vUpdateGroupTitle()

        self.ui.poButtonRemove.vSetIcons(QIcon(":/resources/remove.png"), QIcon(":/resources/remove_hover.png"))
        # init amplitude settings
        self.ui.poDialAmplitude.setRange(int(self.m_poCoreSettings.oGetAmplitude().dGetMin() * 100), int(self.m_poCoreSettings.oGetAmplitude().dGetMax() * 100))
        self.ui.poSpinBoxAmplitude.setRange(int(self.m_poCoreSettings.oGetAmplitude().dGetMin() * 100), int(self.m_poCoreSettings.oGetAmplitude().dGetMax() * 100))
        self.ui.poSpinBoxAmplitude.setSingleStep(1)

        # init frequency settings
        self.ui.poDialFrequency.setRange(int(self.m_poCoreSettings.oGetFrequency().dGetMin() / 1000000.0), int(self.m_poCoreSettings.oGetFrequency().dGetMax() / 1000000.0))
        self.ui.poSpinBoxFrequency.setRange(int(self.m_poCoreSettings.oGetFrequency().dGetMin() / 1000000.0), int(self.m_poCoreSettings.oGetFrequency().dGetMax() / 1000000.0))
        self.ui.poSpinBoxFrequency.setSingleStep(0.01)

        # init phase settings
        self.ui.poDialPhase.setRange(int(self.m_poCoreSettings.oGetPhase().dGetMin()), int(self.m_poCoreSettings.oGetPhase().dGetMax()))
        self.ui.poSpinBoxPhase.setRange(int(self.m_poCoreSettings.oGetPhase().dGetMin()), int(self.m_poCoreSettings.oGetPhase().dGetMax()))
        self.ui.poSpinBoxPhase.setSingleStep(1)

        self.ui.poButtonRemove.clicked.connect(self.slButtonRemove)
        self.ui.poDialAmplitude.sliderReleased.connect(self.slDialAmplitudeChanged)
        self.ui.poDialFrequency.sliderReleased.connect(self.slDialFrequencyChanged)
        self.ui.poDialPhase.sliderReleased.connect(self.slDialPhaseChanged)
        self.ui.poDialAmplitude.valueChanged.connect(self.slDialAmplitudeChanged)
        self.ui.poDialFrequency.valueChanged.connect(self.slDialFrequencyChanged)
        self.ui.poDialPhase.valueChanged.connect(self.slDialPhaseChanged)
        self.ui.poSpinBoxCoreNum.valueChanged.connect(self.slCoreNumChanged)
        self.ui.poSpinBoxAmplitude.valueChanged.connect(self.slAmplitudeChanged)
        self.ui.poSpinBoxFrequency.valueChanged.connect(self.slFrequencyChanged)
        self.ui.poSpinBoxPhase.valueChanged.connect(self.slPhaseChanged)
        self.ui.poComboBoxChannels.currentIndexChanged.connect(self.slChannelSelectionChanged)

        self.vUpdateCoreGUI(bUseDefaultValue)

    # void vSetFlags (unsigned int dwFlags);
    def vSetFlags(self, dwFlags : int):
        logging.debug("SDC_DlgCore::vSetFlags")
        self.m_dwFlags = dwFlags

        if self.m_dwFlags & self.FLAGS.NOFIXCORENUM:
            self.ui.poGroupCoreSelection.setHidden(False)
        else:
            self.ui.poGroupCoreSelection.setHidden(True)

        if dwFlags & self.FLAGS.COMPACT:
            self.ui.poLineAmplitude.setHidden(True)
            self.ui.poLineFrequency.setHidden(True)
            self.ui.poLinePhase.setHidden(True)

            self.ui.poDialAmplitude.setHidden(True)
            self.ui.poDialFrequency.setHidden(True)
            self.ui.poDialPhase.setHidden(True)

            self.ui.poLabelAmplitude.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
            self.ui.poLabelFrequency.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
            self.ui.poLabelPhase.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        else:
            self.ui.poLineAmplitude.setHidden(False)
            self.ui.poLineFrequency.setHidden(False)
            self.ui.poLinePhase.setHidden(False)

            self.ui.poDialAmplitude.setHidden(False)
            self.ui.poDialFrequency.setHidden(False)
            self.ui.poDialPhase.setHidden(False)

            self.ui.poLabelAmplitude.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.poLabelFrequency.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.poLabelPhase.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
    
	# unsigned int dwGetFlags () { return m_dwFlags; }
    def dwGetFlags(self) -> int:
        logging.debug("SDC_DlgCore::dwGetFlags")
        return self.m_dwFlags

	# SDC_CoreSettings *poGetCoreSettings ();
    def poGetCoreSettings(self):
        logging.debug("SDC_DlgCore::poGetCoreSettings")
        self.m_poCoreSettings.vSetCoreNum(self.poSpinBoxCoreNum.value())
        self.m_poCoreSettings.vSetChNum(self.poComboBoxChannels.currentData())
        self.m_poCoreSettings.vSetAmplitude(self.poSpinBoxAmplitude.value() / 100.0)
        self.m_poCoreSettings.vSetFrequency(self.poSpinBoxFrequency.value() * 1000000.0)
        self.m_poCoreSettings.vSetPhase(self.poSpinBoxPhase.value())

        return self.m_poCoreSettings

	# void vSetCoreSettings (SDC_CoreSettings oCoreSettings);
    def vSetCoreSettings(self, oCoreSettings):
        logging.debug("SDC_DlgCore::vSetCoreSettings")
        self.ui.poSpinBoxCoreNum.setValue(oCoreSettings.lGetCoreIndex())

        self.vSetAllowedChannels(oCoreSettings.lGetCoreIndex())

        self.vSetChannelNum(oCoreSettings.lGetChannel())

        self.ui.poSpinBoxAmplitude.setValue(oCoreSettings.oGetAmplitude().dGetValue() * 100.0)
        self.ui.poDialAmplitude.setValue(int(self.ui.poSpinBoxAmplitude.value()))

        self.ui.poSpinBoxFrequency.setValue(oCoreSettings.oGetFrequency().dGetValue() / 1000000.0)
        self.ui.poDialFrequency.setValue(int(self.ui.poSpinBoxFrequency.value()))

        self.ui.poSpinBoxPhase.setValue(oCoreSettings.oGetPhase().dGetValue())
        self.ui.poDialPhase.setValue(int(self.ui.poSpinBoxPhase.value()))
	
	# int lGetChNum () { return m_lChannelNum; }
    def lGetChNum(self) -> int:
        logging.debug("SDC_DlgCore::lGetChNum")
        return self.m_lChannelNum

	# void vUpdateCoreGUI (bool bUseDefaultValues = false);
    def vUpdateCoreGUI(self, bUseDefaultValues : bool = False):
        logging.debug("SDC_DlgCore::vUpdateCoreGUI")
        if bUseDefaultValues:
            dValue = self.m_poHwControl.poGetCurrentDevice().dGetInitCoreValue(SDC_SpcDevice.SETTING_TYPE.AMPLITUDE, self.m_lChCoreIndex)
        else:
            dValue = self.m_poCoreSettings.oGetAmplitude().dGetValue()

        self.ui.poDialAmplitude.setValue(int(dValue * 100))
        self.slDialAmplitudeChanged()

        if (bUseDefaultValues):
            dValue = self.m_poHwControl.poGetCurrentDevice().dGetInitCoreValue(SDC_SpcDevice.SETTING_TYPE.FREQUENCY, self.m_lChCoreIndex)
        else:
            dValue = self.m_poCoreSettings.oGetFrequency().dGetValue()

        self.ui.poDialFrequency.setValue(int(dValue / 1000000.0))
        self.slDialFrequencyChanged()

        if (bUseDefaultValues):
            dValue = self.m_poHwControl.poGetCurrentDevice().dGetInitCoreValue(SDC_SpcDevice.SETTING_TYPE.PHASE, self.m_lChCoreIndex)
        else:
            dValue = self.m_poCoreSettings.oGetPhase().dGetValue()

        self.ui.poDialPhase.setValue(int(dValue))
        self.slDialPhaseChanged()

	# void slExtCoreNumChanged (int lCoreNum, int lChNum);
    def slExtCoreNumChanged(self, lCoreNum : int, lChNum : int):
        logging.debug("SDC_DlgCore::slExtCoreNumChanged")
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

	# void sigRemoveCoreDialog (int);
	# void sigCoreNumChanged (int, int);
    sigRemoveCoreDialog = pyqtSignal(int)
    sigCoreNumChanged = pyqtSignal(int, int)

	# void slChannelSelectionChanged ();
    def slChannelSelectionChanged(self):
        logging.debug("SDC_DlgCore::slChannelSelectionChanged")
        try:
            m_lChannelNum = int(self.poComboBoxChannels.currentData())
        except TypeError:
            m_lChannelNum = 0
        self.vUpdateGroupTitle()

        self.sigCoreNumChanged.emit(self.m_lCoreNum, m_lChannelNum)
    
	# void slButtonRemove            ();
    def slButtonRemove(self):
        logging.debug("SDC_DlgCore::slButtonRemove")
        self.sigRemoveCoreDialog.emit(self.m_lDlgID)

	# void slDialAmplitudeChanged    ();
    def slDialAmplitudeChanged(self, lValue : float = None):
        logging.debug("SDC_DlgCore::slDialAmplitudeChanged")
        if lValue is None:
            self.poSpinBoxAmplitude.setValue(self.poDialAmplitude.value())
            self.vAmplitudeChanged()
        else:
            self.poSpinBoxAmplitude.setValue(lValue)

	# void slDialFrequencyChanged    ();
    def slDialFrequencyChanged(self, lValue : int = None):
        logging.debug("SDC_DlgCore::slDialFrequencyChanged")
        if lValue is None:
            self.poSpinBoxFrequency.setValue(self.poDialFrequency.value())
            self.vFrequencyChanged()
        else:
            self.poSpinBoxFrequency.setValue(lValue)

	# void slDialPhaseChanged        ();
    def slDialPhaseChanged(self, lValue : int = None):
        logging.debug("SDC_DlgCore::slDialPhaseChanged")
        if lValue is None:
            self.poSpinBoxPhase.setValue(self.poDialPhase.value())
            self.vPhaseChanged()
        else:
            self.poSpinBoxPhase.setValue(lValue)

	# void slCoreNumChanged          ();
    def slCoreNumChanged(self):
        logging.debug("SDC_DlgCore::slCoreNumChanged")
        self.m_eUpdateSetting = self.SETTING.CORENUM
        self.m_poTimerUpdate.start(500)

	# void slAmplitudeChanged		   ();
    def slAmplitudeChanged(self):
        logging.debug("SDC_DlgCore::slAmplitudeChanged")
        self.m_eUpdateSetting = self.SETTING.AMPLITUDE
        self.m_poTimerUpdate.start(200)

	# void slFrequencyChanged		   ();
    def slFrequencyChanged(self):
        logging.debug("SDC_DlgCore::slFrequencyChanged")
        self.m_eUpdateSetting = self.SETTING.FREQUENCY
        self.m_poTimerUpdate.start(200)

	# void slPhaseChanged		       ();
    def slPhaseChanged(self):
        logging.debug("SDC_DlgCore::slPhaseChanged")
        self.m_eUpdateSetting = self.SETTING.PHASE
        self.m_poTimerUpdate.start(200)

	# void slTimeoutUpdate		   ();
    def slTimeoutUpdate(self):
        logging.debug("SDC_DlgCore::slTimeoutUpdate")
        if self.m_eUpdateSetting == self.SETTING.CORENUM:
            self.vCoreNumChanged()
        elif self.m_eUpdateSetting == self.SETTING.AMPLITUDE:
            self.vAmplitudeChanged()
        elif self.m_eUpdateSetting == self.SETTING.FREQUENCY:
            self.vFrequencyChanged()
        elif self.m_eUpdateSetting == self.SETTING.PHASE:
            self.vPhaseChanged()

	# void vUpdateGroupTitle ();
    def vUpdateGroupTitle(self):
        logging.debug("SDC_DlgCore::vUpdateGroupTitle")
        sChNum = ""
        sCoreNum = ""
        
        if self.m_dwFlags and self.FLAGS.NOFIXCORENUM:
            sChNum = int(self.ui.poComboBoxChannels.currentData())
            sCoreNum = int(self.ui.poSpinBoxCoreNum.value())
        else:
            sChNum = str(self.m_lChannelNum)
            sCoreNum = str(self.m_lCoreNum)
        
        if int(sChNum) == 1: self.ui.poGroupCore.setStyleSheet("QGroupBox {color: magenta;}")
        if int(sChNum) == 2: self.ui.poGroupCore.setStyleSheet("QGroupBox {color: yellow;}")
        if int(sChNum) == 3: self.ui.poGroupCore.setStyleSheet("QGroupBox {color: lightGreen;}")
        if int(sChNum) == 4: self.ui.poGroupCore.setStyleSheet("QGroupBox {color: #7092BE;}")
        if int(sChNum) == 5: self.ui.poGroupCore.setStyleSheet("QGroupBox {color: white;}")
        if int(sChNum) == 6: self.ui.poGroupCore.setStyleSheet("QGroupBox {color: cyan;}")
        if int(sChNum) == 7: self.ui.poGroupCore.setStyleSheet("QGroupBox {color: black;}")
        
        sTitle = f"Ch {sChNum} | Core {sCoreNum}" # "Ch " + sChNum + " | Core " + sCoreNum
        self.ui.poGroupCore.setTitle(sTitle)

	# void vSetAllowedChannels (int lCoreNum, int lDefaultChNum = -1);
    def vSetAllowedChannels(self, lCoreNum : int, lDefaultChNum : int = -1):
        logging.debug("SDC_DlgCore::vSetAllowedChannels")
        mlsAllowedChannels = self.m_poCoreSettings.mlsGetAllowedChannels(lCoreNum)

        self.poComboBoxChannels.clear()

        for key, allowed_channel in mlsAllowedChannels.items():
            self.poComboBoxChannels.addItem(allowed_channel, key)

        if lDefaultChNum >= 0:
            lIndex = self.poComboBoxChannels.findData(lDefaultChNum)
            if lIndex > -1:
                self.poComboBoxChannels.setCurrentIndex(lIndex)

	# void vSetChannelNum    (int lChNum);
    def vSetChannelNum(self, lChNum : int):
        logging.debug("SDC_DlgCore::vSetChannelNum")
        self.poComboBoxChannels.currentIndexChanged.disconnect(self.slChannelSelectionChanged)

        lIndex = self.poComboBoxChannels.findData(lChNum)
        if lIndex > -1:
            self.m_lChannelNum = lChNum
            self.poComboBoxChannels.setCurrentIndex(lIndex)

            self.vUpdateGroupTitle()

        self.poComboBoxChannels.currentIndexChanged.connect(self.slChannelSelectionChanged)

	# void vCoreNumChanged   ();
    def vCoreNumChanged(self):
        logging.debug("SDC_DlgCore::vCoreNumChanged")
        m_lCoreNum = self.ui.poSpinBoxCoreNum.value()

        if self.ui.poGroupCoreSelection.isVisible():
            self.vSetAllowedChannels(m_lCoreNum, self.m_lChannelNum)
        
        self.vUpdateGroupTitle()

        self.sigCoreNumChanged.emit(m_lCoreNum, self.m_lChannelNum)

	# void vAmplitudeChanged ();
    def vAmplitudeChanged(self):
        logging.debug("SDC_DlgCore::vAmplitudeChanged")
        dValue = self.ui.poSpinBoxAmplitude.value() / 100.0
        self.m_poCoreSettings.vSetAmplitude(dValue)
        self.m_poHwControl.dwSetAmplitude(self.m_lCoreNum, dValue)
        self.ui.poSpinBoxAmplitude.setValue(int(dValue * 100.0))

        self.ui.poDialAmplitude.setValue(int(self.ui.poSpinBoxAmplitude.value()))

	# void vFrequencyChanged ();
    def vFrequencyChanged(self):
        logging.debug("SDC_DlgCore::vFrequencyChanged")
        dValue = self.ui.poSpinBoxFrequency.value() * 1000000.0
        self.m_poCoreSettings.vSetFrequency(dValue)
        self.m_poHwControl.dwSetFrequency(self.m_lCoreNum, dValue)
        self.ui.poSpinBoxFrequency.setValue(int(dValue / 1000000.0))

        self.ui.poDialFrequency.setValue(int(self.ui.poSpinBoxFrequency.value()))

	# void vPhaseChanged     ();
    def vPhaseChanged(self):
        logging.debug("SDC_DlgCore::vPhaseChanged")
        dValue = self.ui.poSpinBoxPhase.value()
        self.m_poCoreSettings.vSetPhase(dValue)
        self.m_poHwControl.dwSetPhase(self.m_lCoreNum, dValue)
        self.ui.poSpinBoxPhase.setValue(int(dValue))

        self.ui.poDialPhase.setValue(int(self.ui.poSpinBoxPhase.value()))
