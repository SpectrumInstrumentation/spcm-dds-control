import spcm

from PyQt5.QtWidgets import QDialog, QGridLayout, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt, QTimer, QFile, QSettings
from PyQt5.QtGui import QIcon
from PyQt5 import uic

from control.sdc_control import SDC_Control
from settings.sdc_settings import SDC_Settings, DEFAULT_CORE_DDS20_CH0, DEFAULT_CORE_DDS20_CH1, DEFAULT_CORE_DDS20_CH2, DEFAULT_CORE_DDS20_CH3, DEFAULT_CORE_DDS50_CH0, DEFAULT_CORE_DDS50_CH1, DEFAULT_CORE_DDS50_CH2, DEFAULT_CORE_DDS50_CH3
from dialogs.sdc_components import SDC_PushButton
from dialogs.sdc_dlgsettings import SDC_DlgSettings
from dialogs.sdc_dlghwsettings import SDC_DlgHwSettings
from dialogs.sdc_dlgcore import SDC_DlgCore
from settings.sdc_coresettings import SDC_CoreSettings, SDC_Value

MAX_CORES = 16

# ******************************************************************************************************
# ***** Public Constructor
# ********************************************************************************************************
class SDC_DlgControl (QDialog):
    started = False
    m_mlpoCoreDialogs = {}
    
    def __init__(self, start : bool): 
        #print("SDC_DlgControl::__init__")
        super().__init__()

        self.started = start

        self.m_poControl = SDC_Control()
        self.m_poSettings = SDC_Settings()
        
        self.ui = uic.loadUi("formfiles/DlgDDSControl.ui", self)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)

        self.setWindowIcon(QIcon("./SPCDDSControl.ico"))
        self.setWindowTitle(self.m_poSettings.sGetAppTitle())

        self.m_poTimerResize = QTimer(self) 
        self.m_poTimerResize.setSingleShot(True)
        self.m_poTimerResize.timeout.connect(self.slTimeoutResize)

        # create grid layout for core widgets
        self.m_poLayoutCores = QGridLayout(self.ui.poWidgetMain)
        self.m_poLayoutCores.setContentsMargins (0, 0, 0, 0)
        
        self.vInitGUI()

        # set connections
        self.poButtonQuit.clicked.connect(self.close)
        self.poButtonAddCore.clicked.connect(self.slAddCoreDialog)
        self.poButtonOpenSetup.clicked.connect(self.slOpenSetup)
        self.poButtonSaveSetup.clicked.connect(self.slSaveSetup)
        self.poButtonHwSettings.clicked.connect(self.slHwSettings)
        self.poButtonSettings.clicked.connect(self.slSettings)
        self.poButtonStart.clicked.connect(self.slStart)
        self.poComboBoxDevice.currentIndexChanged.connect(self.slDeviceChanged)
        self.m_poControl.sigShowMessage.connect(self.slShowMessageBox)

        self.show()

        self.started = self.bInitControl()

        if self.m_poSettings.bSaveOnExit():
            self.vLoadSetup(self.m_poSettings.sGetInternalSetupFilePath())

    # ******************************************************************************************************
    # ***** Public Destructor
    # ********************************************************************************************************
    def __del__(self):
        #print("SDC_DlgControl::__del__")
        self.m_poSettings.vDestroy()

    # ********************************************************************************************************
    # ***** Protected Event
    # ********************************************************************************************************
    def closeEvent (self, event):
        #print("SDC_DlgControl::closeEvent")
        if self.m_poSettings.bSaveOnExit():
            self.vSaveSetup(self.m_poSettings.sGetInternalSetupFilePath())
        else:
            if QFile.exists(self.m_poSettings.sGetInternalSetupFilePath()):
                QFile.remove(self.m_poSettings.sGetInternalSetupFilePath ())

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slShowMessageBox(self, eMSBoxType, sTitle : str, sMessage : str):
        #print("SDC_DlgControl::slShowMessageBox")
        if eMSBoxType == SDC_Settings.MSBOX_TYPE.MSB_INFO:
            msgbox = QMessageBox.information (self, sTitle, sMessage)
        elif eMSBoxType == SDC_Settings.MSBOX_TYPE.MSB_WARNING:
            msgbox = QMessageBox.warning (self, sTitle, sMessage)
        elif eMSBoxType == SDC_Settings.MSBOX_TYPE.MSB_ERROR:
            msgbox = QMessageBox.critical (self, sTitle, sMessage)

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slDeviceChanged(self, lDevIdx : int):
        #print("SDC_DlgControl::slDeviceChanged")
        self.m_poControl.poGetHwCtrlObj().vSetCurrentDevice(lDevIdx)

        poDevice = self.m_poControl.poGetHwCtrlObj().poGetCurrentDevice()
        if poDevice:
            self.vResetCoreDialogs()

            #print(poDevice.lGetNumMaxChannels())
            for lChIdx in range(poDevice.lGetNumMaxChannels()):
                if poDevice.bIsDDS50():
                    if lChIdx == 0: self.vAddCoreDialog (lChIdx, DEFAULT_CORE_DDS50_CH0, True)
                    if lChIdx == 1: self.vAddCoreDialog (lChIdx, DEFAULT_CORE_DDS50_CH1, True)
                    if lChIdx == 2: self.vAddCoreDialog (lChIdx, DEFAULT_CORE_DDS50_CH2, True)
                    if lChIdx == 3: self.vAddCoreDialog (lChIdx, DEFAULT_CORE_DDS50_CH3, True)
                else:
                    if lChIdx == 0: self.vAddCoreDialog (lChIdx, DEFAULT_CORE_DDS20_CH0, True)
                    if lChIdx == 1: self.vAddCoreDialog (lChIdx, DEFAULT_CORE_DDS20_CH1, True)
                    if lChIdx == 2: self.vAddCoreDialog (lChIdx, DEFAULT_CORE_DDS20_CH2, True)
                    if lChIdx == 3: self.vAddCoreDialog (lChIdx, DEFAULT_CORE_DDS20_CH3, True)

        self.vResizeDialog()

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slAddCoreDialog(self):
        #print("SDC_DlgControl::slAddCoreDialog")
        self.vAddCoreDialog()

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vAddCoreDialog (self, lChNum : int = 0, lCoreNum : int = -1, bFixCoreNum : bool = False):
        #print("SDC_DlgControl::vAddCoreDialog")
        #print(f"lChNum: {lChNum}, lCoreNum: {lCoreNum}, bFixCoreNum: {bFixCoreNum}, {len(self.m_mlpoCoreDialogs) = }")
        if len(self.m_mlpoCoreDialogs) >= MAX_CORES:
            return

        lDlgID = 0
        #print(self.m_mlpoCoreDialogs.keys())
        while lDlgID in self.m_mlpoCoreDialogs.keys():
            lDlgID += 1

        lGridPosX = 0
        if lDlgID == 0 or lDlgID ==  2 or lDlgID ==  6 or lDlgID == 12: lGridPosX = 0
        if lDlgID == 1 or lDlgID ==  3 or lDlgID ==  7 or lDlgID == 13: lGridPosX = 1
        if lDlgID == 4 or lDlgID ==  5 or lDlgID ==  8 or lDlgID == 14: lGridPosX = 2
        if lDlgID == 9 or lDlgID == 10 or lDlgID == 11 or lDlgID == 15: lGridPosX = 3

        lGridPosY = 0
        if lDlgID ==  0 or lDlgID ==  1 or lDlgID ==  4 or lDlgID ==  9: lGridPosY = 0
        if lDlgID ==  2 or lDlgID ==  3 or lDlgID ==  5 or lDlgID == 10: lGridPosY = 1
        if lDlgID ==  6 or lDlgID ==  7 or lDlgID ==  8 or lDlgID == 11: lGridPosY = 2
        if lDlgID == 12 or lDlgID == 13 or lDlgID == 14 or lDlgID == 15: lGridPosY = 3
        
        if lCoreNum == -1:
            lCoreNum = lDlgID

        poDlgCore = SDC_DlgCore(lDlgID, lCoreNum, lChNum, bFixCoreNum, self.m_poControl.poGetHwCtrlObj(), self)
        poDlgCore.sigRemoveCoreDialog.connect(self.slRemoveCoreDialog)

        for core_dialog in self.m_mlpoCoreDialogs.values():
            if core_dialog != poDlgCore:
                core_dialog.sigCoreNumChanged.connect(poDlgCore.slExtCoreNumChanged)
                poDlgCore.sigCoreNumChanged.connect(core_dialog.slExtCoreNumChanged)

        self.m_mlpoCoreDialogs[lDlgID] = poDlgCore

        self.m_poLayoutCores.addWidget(poDlgCore, lGridPosY, lGridPosX)

        poDlgCore.show()

        self.vResizeDialog()

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vResetCoreDialogs(self):
        #print("SDC_DlgControl::vResetCoreDialogs")
        for core_dialog in self.m_mlpoCoreDialogs.values():
            core_dialog.setParent(None)
        self.m_mlpoCoreDialogs = {}

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vLoadSetup (self, sFilePath : str):
        #print("SDC_DlgControl::vLoadSetup({})".format(sFilePath))
        if QFile.exists(sFilePath):
            oSettings = QSettings(sFilePath, QSettings.IniFormat, self)

            lNumCores = oSettings.value("NumCores", 0, int)

            #print(f"{lNumCores = }")
            while len(self.m_mlpoCoreDialogs) < lNumCores and len(self.m_mlpoCoreDialogs) < MAX_CORES:
                self.slAddCoreDialog()

            # read core settings
            for lIdx in range(lNumCores):
                oSettings.beginGroup ("Core{}".format(lIdx))
                lDlgID = oSettings.value ("ID", -1, int)

                if lDlgID in self.m_mlpoCoreDialogs:
                    oCoreSettings = SDC_CoreSettings()
                    oValue = SDC_Value()

                    lCoreNum = oSettings.value ("CoreNum", -1, int)
                    lChNum = oSettings.value ("ChNum", -1, int)

                    if lCoreNum > -1: oCoreSettings.vSetCoreIndex(lCoreNum)
                    if lChNum > -1: oCoreSettings.vSetChannel(lChNum)

                    oValue.vSetValue(oSettings.value("Amp", 0, float))
                    oCoreSettings.vSetAmplitude (oValue)

                    oValue.vSetValue(oSettings.value("Freq", 0, float))
                    oCoreSettings.vSetFrequency (oValue)

                    oValue.vSetValue (oSettings.value("Phase", 0, float))
                    oCoreSettings.vSetPhase (oValue)

                    self.m_mlpoCoreDialogs[lDlgID].vSetCoreSettings(oCoreSettings)

                oSettings.endGroup()
            
            # read hardware settings
            lNumDevices = oSettings.value ("NumDevices", 0, int)
            for lDevIdx in range(lNumDevices):
                oSettings.beginGroup ("Device{}".format(lDevIdx))

                sDeviceName = oSettings.value ("Name", "", str)

                poDevice = self.m_poControl.poGetHwCtrlObj().poGetDeviceByeName(sDeviceName)
                if poDevice:
                    lNumChannels = oSettings.value("NumChannels", 0, int)
                    for lChIdx in range(lNumChannels):
                        oChSetting = poDevice.oGetChSettings(lChIdx)

                        oSettings.beginGroup("Ch{}".format(lChIdx))

                        lValue = oSettings.value("OutputEnabled", 1, int)
                        oChSetting.vSetOutputEnabled(lValue)

                        lValue = oSettings.value ("OutputRange", 1000, int)
                        oChSetting.vSetOutputRange_mV(lValue)

                        lValue = oSettings.value ("Filter", 0, int)
                        oChSetting.vSetFilter(lValue)
                        
                        oSettings.endGroup()

                        poDevice.vSetChSettings (lChIdx, oChSetting)

                oSettings.endGroup ();

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vSaveSetup (self, sFilePath : str):
        #print("SDC_DlgControl::vSaveSetup({})".format(sFilePath))
        if QFile.exists(sFilePath):
            QFile.remove(sFilePath)

        oSettings = QSettings(sFilePath, QSettings.IniFormat, self)

        oSettings.setValue("NumCores", len(self.m_mlpoCoreDialogs))

        lIndex = 0

        # save core settings
        # QMapIterator <int, SDC_DlgCore*> itMap (m_mlpoCoreDialogs);
        for key, core_dialog in self.m_mlpoCoreDialogs.items():
            lIndex += 1
            oSettings.beginGroup ("Core{}".format(lIndex))
            oSettings.setValue ("ID",      key)
            oSettings.setValue ("CoreNum", core_dialog.poGetCoreSettings().lGetCoreIndex())
            oSettings.setValue ("ChNum",   core_dialog.poGetCoreSettings().lGetChannel())
            oSettings.setValue ("Amp",     core_dialog.poGetCoreSettings().oGetAmplitude().dGetValue())
            oSettings.setValue ("Freq",    core_dialog.poGetCoreSettings().oGetFrequency().dGetValue())
            oSettings.setValue ("Phase",   core_dialog.poGetCoreSettings().oGetPhase().dGetValue())
            oSettings.endGroup()

        # save hardware settings
        oSettings.setValue("NumDevices", self.m_poControl.poGetHwCtrlObj().lGetNumOfDevices())
        
        for lDevIdx in range(self.m_poControl.poGetHwCtrlObj().lGetNumOfDevices()):
            poDevice = self.m_poControl.poGetHwCtrlObj().poGetDevice(lDevIdx)
            if poDevice:
                oSettings.beginGroup("Device{}".format(lDevIdx))
                oSettings.setValue("Name", poDevice.sGetDeviceName())
                
                oSettings.setValue("NumChannels", int(poDevice.lGetNumMaxChannels()))

                for lChIdx in range(poDevice.lGetNumMaxChannels()):
                    oChSetting = poDevice.oGetChSettings(lChIdx)
                    
                    oSettings.beginGroup("Ch%1".format(lChIdx))
                    oSettings.setValue("OutputEnabled", int(oChSetting.lOutputEnabled()))
                    oSettings.setValue("OutputRange", int(oChSetting.lGetOutputRange_mV()))
                    oSettings.setValue("Filter", int(oChSetting.lGetFilter()))
                    oSettings.endGroup()
                
                oSettings.endGroup ()

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slOpenSetup(self):
        #print("SDC_DlgControl::slOpenSetup")
        sFilePath, bOk = QFileDialog.getOpenFileName(self, "Load Setup File", self.m_poSettings.sGetSetupFilePath(), "SDC (*.sdc)")
        if sFilePath:
            self.m_poSettings.vSetSetupFilePath(sFilePath)
            self.vLoadSetup (sFilePath)

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slSaveSetup(self):
        #print("SDC_DlgControl::slSaveSetup")
        sFilePath, bOk = QFileDialog.getSaveFileName (self, "Save Setup File", self.m_poSettings.sGetSetupFilePath(), "SDC (*.sdc)")
        if sFilePath:
            self.m_poSettings.vSetSetupFilePath(sFilePath)
            self.vSaveSetup(sFilePath)

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slHwSettings(self):
        #print("SDC_DlgControl::slHwSettings")
        poDevice = self.m_poControl.poGetHwCtrlObj().poGetCurrentDevice()
        if poDevice:
            oDialog = SDC_DlgHwSettings(poDevice)
            oDialog.exec()

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slSettings(self):
        #print("SDC_DlgControl::slSettings")
        oDialog = SDC_DlgSettings()
        oDialog.exec()

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slStart(self):
        #print("SDC_DlgControl::slStart")
        if self.poButtonStart.eGetType() == SDC_PushButton.type.START:
            if self.bStartHw():
                self.poButtonStart.vSetType(SDC_PushButton.type.STOP)
        elif self.poButtonStart.eGetType() == SDC_PushButton.type.STOP:
            self.poButtonStart.vSetType(SDC_PushButton.type.START)
            self.vStopHw()

    # ********************************************************************************************************
    # ***** Private Slot
    # ********************************************************************************************************
    def slTimeoutResize(self):
        #print("SDC_DlgControl::slTimeoutResize")
        if not self.isMaximized():
            oRectDlgCore = self.poWidgetMain.geometry()
            oRectDlgMain = self.geometry()

            oRectDlgMain.setWidth(80 + oRectDlgCore.width())
            oRectDlgMain.setHeight(126 + oRectDlgCore.height())

            self.setGeometry(oRectDlgMain)

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vInitGUI (self):
        #print("SDC_DlgControl::vInitGUI")
        # set tool button icons
        self.poButtonAddCore.vSetIcons(QIcon(":/resources/add.png"), QIcon(":/resources/add_hover.png"));
        self.poButtonOpenSetup.vSetIcons(QIcon(":/resources/open.png"), QIcon(":/resources/open_hover.png"));
        self.poButtonSaveSetup.vSetIcons(QIcon(":/resources/save.png"), QIcon(":/resources/save_hover.png"));
        self.poButtonSettings.vSetIcons(QIcon(":/resources/settings.png"), QIcon(":/resources/settings_hover.png"));
        self.poButtonHwSettings.vSetIcons(QIcon(":/resources/hwsettings.png"), QIcon(":/resources/hwsettings_hover.png"));
        self.poButtonQuit.vSetIcons(QIcon(":/resources/quit.png"), QIcon(":/resources/quit_hover.png"));

        self.poButtonStart.vSetType(SDC_PushButton.type.START);

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def bInitControl(self) -> bool:
        #print("SDC_DlgControl::bInitControl")
        oStrDeviceNames = self.m_poControl.oInit()
        if len(oStrDeviceNames):
            for name in oStrDeviceNames:
                self.ui.poComboBoxDevice.addItem (name)
            self.ui.poComboBoxDevice.setCurrentIndex (0)
        else:
            self.ui.poComboBoxDevice.addItem("No Device");
            self.ui.poComboBoxDevice.setEnabled(False);

            return False

        return True

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vResizeDialog(self):
        #print("SDC_DlgControl::vResizeDialog")
        self.m_poTimerResize.start(100)

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def slRemoveCoreDialog (self, lID : int):
        #print("SDC_DlgControl::slRemoveCoreDialog")
        poDlgCore = self.m_mlpoCoreDialogs.pop(lID)
        poDlgCore.setParent(None)

        self.vResizeDialog()

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def bStartHw(self) -> bool:
        #print("SDC_DlgControl::bStartHw")
        dwError = 0

        try:
            poHwControl = self.m_poControl.poGetHwCtrlObj()
            if poHwControl:
                poHwControl.vClearCoreConnectionsMasks()
                
                poHwControl.dwDoGeneralSetup()

                for core_dialog in self.m_mlpoCoreDialogs.values():
                    poHwControl.dwDoCoreSetup(core_dialog.poGetCoreSettings())

                poHwControl.dwSetCoreConnections()

            poHwControl.dwStart()
        except spcm.SpcmException as e:
            self.slShowMessageBox(SDC_Settings.MSBOX_TYPE.MSB_ERROR, "Driver Error", str(e))
            return False
        except Exception as e:
            self.slShowMessageBox(SDC_Settings.MSBOX_TYPE.MSB_ERROR, "Error", str(e))
            return False
        
        return True

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vStopHw(self):
        #print("SDC_DlgControl::vStopHw")
        self.m_poControl.poGetHwCtrlObj().vStop()

    # ********************************************************************************************************
