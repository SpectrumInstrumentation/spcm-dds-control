import logging
from spcm_core import *

from PyQt5.QtWidgets import QDialog, QGridLayout, QMessageBox, QFileDialog, QMenu, QTableWidgetItem, QWidget, QAbstractItemView, QAction, QProgressDialog, QComboBox
from PyQt5.QtCore import Qt, QTimer, QFile, QSettings, QSignalMapper, QEvent, QPoint, QFileInfo
from PyQt5.QtGui import QIcon, QDropEvent, QMouseEvent, QKeyEvent, QColor
from PyQt5 import uic

from settings.sdc_settings import SDC_GuiMode, SDC_Settings, SETUP_FILE_VERSION,\
     DEFAULT_CORE_DDS20_CH0, DEFAULT_CORE_DDS20_CH1, DEFAULT_CORE_DDS20_CH2, DEFAULT_CORE_DDS20_CH3,\
     DEFAULT_CORE_DDS50_CH0, DEFAULT_CORE_DDS50_CH1, DEFAULT_CORE_DDS50_CH2, DEFAULT_CORE_DDS50_CH3
from control.sdc_control import SDC_Control
from control.sdc_hwcontrol import SDC_HwControl, SDC_HwStatusThread, SDC_DrvCmd
from dialogs.sdc_components import SDC_PushButton
from dialogs.sdc_dlgsettings import SDC_DlgSettings
from dialogs.sdc_dlghwsettings import SDC_DlgHwSettings
from dialogs.sdc_dlgcore import SDC_DlgCore
from control.sdc_spcdevice import SDC_SpcDevice

MAX_CORES = 16


class SDC_DlgControl(QDialog):
    m_bTableDropEvent : bool = False
    m_bTableDropNewRow : bool = False
    m_poSettings : SDC_Settings = None
    m_poControl : SDC_Control = None
    m_poHwControl : SDC_HwControl = None
    m_poDlgCore : SDC_DlgCore = None
    m_poDevice : SDC_SpcDevice = None
    m_poCurrentGuiMode : SDC_GuiMode = None
    m_poLayoutCores : QGridLayout = None
    m_poTimerResize : QTimer = None
    m_poExampleMenu : QMenu = None
    m_poStatusThread : SDC_HwStatusThread = None
    m_poSelectedPrgTableItem : QTableWidgetItem = None
    m_poExamplesMapper : QSignalMapper = None
    m_vlSelectedRows : list[int] = []
    m_voCmdList : list[SDC_DrvCmd] = []
    m_mlpoCoreDialogs : dict[int, SDC_DlgCore] = {}
    ui : object = None

    started : bool = False
    
    def __init__(self, poParent : QWidget = None): 
        logging.debug("SDC_DlgControl::__init__")
        super().__init__(parent=poParent, flags=Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)

        self.started = False

        self.m_poControl = SDC_Control()
        self.m_poHwControl = self.m_poControl.poGetHwCtrlObj()
        self.m_poSettings = SDC_Settings.poGetInstance()
        self.m_poDevice = None
        self.m_poSelectedPrgTableItem = None
        self.m_poCurrentGuiMode = None
        self.m_bTableDropEvent = False
        self.m_bTableDropNewRow = False
        
        self.ui = uic.loadUi("formfiles/DlgDDSControl.ui", self)

        self.setWindowIcon(QIcon("./SPCDDSControl.ico"))
        self.setWindowTitle(self.m_poSettings.sGetAppTitle())

        self.m_poTimerResize = QTimer(self) 
        self.m_poTimerResize.setSingleShot(True)
        self.m_poTimerResize.timeout.connect(self.slTimeoutResize)

        # create grid layout for core widgets
        self.m_poLayoutCores = QGridLayout(self.poWidgetMain)
        self.m_poLayoutCores.setContentsMargins(0, 0, 0, 0)
        
        self.vInitGUI()

        # create status thread
        self.m_poStatusThread = SDC_HwStatusThread(self.m_poHwControl)
        self.m_poStatusThread.sigBufferStatus.connect(self.slSetStatus)

        self.show()

        self.started = self.bInitControl()

        if self.m_poSettings.bSaveOnExit():
            self.vLoadSetupFile(self.m_poSettings.sGetInternalSetupFilePath(), False)
        
        self.vSetGuiMode(SDC_GuiMode.MODE.CTRL)

    def __del__(self):
        logging.debug("SDC_DlgControl::__del__")
        SDC_Settings.vDestroy()
        del self.m_poControl

    def closeEvent(self, event):
        logging.debug("SDC_DlgControl::closeEvent")
        self.m_poHwControl.vStopAll()

        if self.m_poSettings.bSaveOnExit():
            self.vSaveSetupFile(self.m_poSettings.sGetInternalSetupFilePath(), False)
        else:
            if QFile.exists(self.m_poSettings.sGetInternalSetupFilePath()):
                QFile.remove(self.m_poSettings.sGetInternalSetupFilePath())
    
    def eventFilter(self, poObject, poEvent) -> bool:
        logging.debug("SDC_DlgControl::eventFilter")
        if poObject == self.poTableWidget.viewport() or poObject == self.ui.poTableWidget:
            if poEvent.type() == QEvent.Drop:
                logging.debug("SDC_DlgControl::eventFilter - Drop event")
                poDropEvent = QDropEvent(poEvent)
                if poDropEvent:
                    poItem = self.poTableWidget.itemAt(poDropEvent.pos())
                    if poItem:
                        self.m_bTableDropNewRow = True

                    self.m_bTableDropEvent = True

                    if poDropEvent.source() == self.ui.poTableWidget:
                        if poItem:
                            self.vMoveSelectedRows(poItem.row(), True)

                        return True
                
            if poEvent.type() == QEvent.MouseButtonPress:
                logging.debug("SDC_DlgControl::eventFilter - MouseButtonPress event")
                poMouseEvent = QMouseEvent(poEvent)
                if poMouseEvent:
                    if poMouseEvent.modifiers () == Qt.ControlModifier:
                        return True

            if poEvent.type() == QEvent.KeyPress:
                logging.debug("SDC_DlgControl::eventFilter - KeyPress event")
                poKeyEvent = QKeyEvent(poEvent)
                if poKeyEvent and poKeyEvent.key() == Qt.Key_Delete:
                    self.vClearSelectedRows()
                    return True

        return super().eventFilter(poObject, poEvent)
    
    def slRemoveCoreDialog(self, lID : int):
        logging.debug("SDC_DlgControl::slRemoveCoreDialog")
        if self.m_poDevice:
            self.m_poSettings.vRemoveSetting(self.m_poDevice.lGetSerialNumber(), lID)

        poDlgCore = self.m_mlpoCoreDialogs.pop(lID)
        poDlgCore.setParent(None)

        self.vResizeDialog()

    def slShowMessageBox(self, eMSBoxType, sTitle : str, sMessage : str):
        logging.debug("SDC_DlgControl::slShowMessageBox")
        if eMSBoxType == SDC_Settings.MSBOX_TYPE.MSB_INFO:
            msgbox = QMessageBox.information(self, sTitle, sMessage)
        elif eMSBoxType == SDC_Settings.MSBOX_TYPE.MSB_WARNING:
            msgbox = QMessageBox.warning(self, sTitle, sMessage)
        elif eMSBoxType == SDC_Settings.MSBOX_TYPE.MSB_ERROR:
            msgbox = QMessageBox.critical(self, sTitle, sMessage)

    def slDeviceChanged(self, lDevIdx : int):
        logging.debug("SDC_DlgControl::slDeviceChanged")
        self.hide()

        self.m_poHwControl.vSetCurrentDevice(lDevIdx)

        self.m_poDevice = self.m_poHwControl.poGetCurrentDevice()
        if self.m_poDevice:
            self.vResetCoreDialogs()

            if self.m_poDevice.bIsDevRunning():
                self.poButtonStart.vSetType(SDC_PushButton.type.STOP)
            else:
                self.poButtonStart.vSetType(SDC_PushButton.type.START)

            if self.m_poDevice.lGetCardFamily() == TYP_M2P65XX_X4:
                self.vInitM2p65xx()
            elif self.m_poDevice.lGetCardFamily() == TYP_M4I66XX_X8:
                self.vInitM4i66xx()
            elif self.m_poDevice.lGetCardFamily() == TYP_M4I96XX_X8:
                self.vInitM4i96xx()
            elif self.m_poDevice.lGetCardFamily() == TYP_M5I63XX_X16:
                self.vInitM5i63xx()
        self.vResizeDialog()

        self.show()
    
    def slNumChannelsChanged(self, lItemIdx : int):
        logging.debug("SDC_DlgControl::slNumChannelsChanged")
        lNumChannels = int(self.poComboBoxNumChannels.itemData(lItemIdx))
        if not lNumChannels:
            return

        if not self.m_poDevice:
            return

        if self.m_poDevice.lGetCardFamily() == TYP_M2P65XX_X4:
            self.vSelectNumChM2p65xx(lNumChannels)
        elif self.m_poDevice.lGetCardFamily() == TYP_M5I63XX_X16:
            self.vSelectNumChM5i63xx(lNumChannels)

    def slSamplingrateChanged(self, lItemIdx : int):
        logging.debug("SDC_DlgControl::slSamplingrateChanged")
        if not self.m_poDevice:
            return

        if self.m_poDevice.lGetCardFamily() == TYP_M5I63XX_X16:
            self.vSetCoresChM5i63xx()

    #void slShowNumCores (int lNumCores);
    def slShowNumCores(self, lNumCores : int):
        logging.debug("SDC_DlgControl::slShowNumCores")
        self.vUpdateShowCoresFilter()
    
    #void slShowChannels (int lItemIdx);
    def slShowChannels(self, lItemIdx : int):
        logging.debug("SDC_DlgControl::slShowChannels")
        self.vUpdateShowCoresFilter()

    #void slRegTextChanged (const QString& sText);
    def slRegTextChanged(self, sText : str):
        logging.debug("SDC_DlgControl::slRegTextChanged")
        oListItems = self.poListWidgetRegs.findItems(sText, Qt.MatchContains)

        for lIdx in range(self.poListWidgetRegs.count()):
            if oListItems.contains(self.poListWidgetRegs.item(lIdx)):
                self.poListWidgetRegs.item(lIdx).setHidden(False)
            else:
                self.poListWidgetRegs.item(lIdx).setHidden(True)
        
    #void slRegItemDoubleClicked (QListWidgetItem* poItem);
    def slRegItemDoubleClicked(self, poItem):
        logging.debug("SDC_DlgControl::slRegItemDoubleClicked")
        if self.m_poSelectedPrgTableItem:
            self.m_poSelectedPrgTableItem.setText(poItem.text())

    #void slPrgTableItemClicked (QTableWidgetItem* poItem);
    def slPrgTableItemClicked(self, poItem):
        logging.debug("SDC_DlgControl::slPrgTableItemClicked")
        self.m_poSelectedPrgTableItem = poItem
    
    #void slPrgTableItemChanged (QTableWidgetItem* poItem);
    def slPrgTableItemChanged(self, poItem : QTableWidgetItem):
        logging.debug("SDC_DlgControl::slPrgTableItemChanged")
        lRow = poItem.row()

        if self.m_bTableDropEvent:
            self.vInitPrgTableItem(poItem, lRow)

            if self.m_bTableDropNewRow:
                self.vCreatePrgTableItem(lRow, 1)
                self.vCreatePrgTableItem(lRow, 2)
            
            self.m_bTableDropNewRow = False
            self.m_bTableDropEvent = False

    #void slPrgTableItemSelectionChanged ();
    def slPrgTableItemSelectionChanged(self):
        logging.debug("SDC_DlgControl::slPrgTableItemSelectionChanged")
        self.m_vlSelectedRows.clear()

        for lRow in range(self.poTableWidget.rowCount()):
            bSelected = self.poTableWidget.item(lRow, 0).isSelected() or self.poTableWidget.item(lRow, 2).isSelected()

            self.vPrgTableSelectRow(lRow, bSelected)

            if bSelected:
                self.m_vlSelectedRows.append(lRow)

    #void slSetStatus (qint32 lQueueInSW, qint32 lQueueCount, qint32 lQueueMax);
    def slSetStatus(self, lQueueInSW : int, lQueueCount : int, lQueueMax : int):
        logging.debug("SDC_DlgControl::slSetStatus")
        sText = "{} / {} / {}".format(lQueueInSW, lQueueCount, lQueueMax)
        self.poLabelQueueStatus.setText(sText)

    
    def slAddCoreDialog(self):
        logging.debug("SDC_DlgControl::slAddCoreDialog")
        if not self.m_poDevice.bIsDevRunning():
            self.vAddCoreDialog(0, -1, -1, False, SDC_DlgCore.FLAGS.NOFIXCORENUM)
    
    #void vAddCoreDialog  ();
    def vAddCoreDialog(self, lChNum : int = 0, lCoreNum : int = -1, lChCoreIndex : int = -1, bLinear : bool = False, dwFlags : int = 0):
        logging.debug("SDC_DlgControl::vAddCoreDialog")
        if len(self.m_mlpoCoreDialogs) >= self.m_poDevice.lGetMaxCores():
            return

        lDlgID = 0
        while lDlgID in self.m_mlpoCoreDialogs:
            lDlgID += 1

        lGridPosX = 0
        lGridPosY = 0

        if bLinear:
            lGridPosX = lCoreNum % 4
            lGridPosY = lCoreNum / 4
        else:
            # default x position
            if lDlgID == 0 or lDlgID ==  2 or lDlgID ==  6 or lDlgID == 12: lGridPosX = 0
            if lDlgID == 1 or lDlgID ==  3 or lDlgID ==  7 or lDlgID == 13: lGridPosX = 1
            if lDlgID == 4 or lDlgID ==  5 or lDlgID ==  8 or lDlgID == 14: lGridPosX = 2
            if lDlgID == 9 or lDlgID == 10 or lDlgID == 11 or lDlgID == 15: lGridPosX = 3

            # default y position
            if lDlgID ==  0 or lDlgID ==  1 or lDlgID ==  4 or lDlgID ==  9: lGridPosY = 0
            if lDlgID ==  2 or lDlgID ==  3 or lDlgID ==  5 or lDlgID == 10: lGridPosY = 1
            if lDlgID ==  6 or lDlgID ==  7 or lDlgID ==  8 or lDlgID == 11: lGridPosY = 2
            if lDlgID == 12 or lDlgID == 13 or lDlgID == 14 or lDlgID == 15: lGridPosY = 3

        if lCoreNum == -1:
            lCoreNum = lDlgID

        if self.m_poSettings.bCompactCoreDialogs():
            dwFlags |= SDC_DlgCore.FLAGS.COMPACT

        poDlgCore = SDC_DlgCore(lDlgID, lCoreNum, lChNum, lChCoreIndex, self.m_poHwControl, dwFlags, self)
        poDlgCore.sigRemoveCoreDialog.connect(self.slRemoveCoreDialog)

        for lpoCoreDialog in self.m_mlpoCoreDialogs.values():
            if lpoCoreDialog != poDlgCore:
                lpoCoreDialog.sigCoreNumChanged.connect(poDlgCore.slExtCoreNumChanged)
                poDlgCore.sigCoreNumChanged.connect(lpoCoreDialog.slExtCoreNumChanged)

        self.m_mlpoCoreDialogs[lDlgID] = poDlgCore

        self.m_poLayoutCores.addWidget(poDlgCore, lGridPosY, lGridPosX)

        poDlgCore.show()

        self.vResizeDialog()

    #void slSwitchMode     ();
    def slSwitchMode(self):
        logging.debug("SDC_DlgControl::slSwitchMode")
        if self.m_poCurrentGuiMode and self.m_poCurrentGuiMode.eGetMode() == SDC_GuiMode.MODE.CTRL:
            self.vSetGuiMode(SDC_GuiMode.MODE.PROG)
        else:
            self.vSetGuiMode(SDC_GuiMode.MODE.CTRL)
    
    def slOpenSetup(self):
        logging.debug("SDC_DlgControl::slOpenSetup")

        if self.m_poCurrentGuiMode and self.m_poCurrentGuiMode.eGetMode() == SDC_GuiMode.MODE.PROG:
            sFilePath = self.m_poSettings.sGetSeqFilePath()
            sExtension = "CSV (*.csv);;SDC (*.sdc)"
        else:
            sFilePath = self.m_poSettings.sGetSetupFilePath()
            sExtension = "SDC (*.sdc);;CSV (*.csv)"

        sNewFilePath, bOk = QFileDialog.getOpenFileName(self, "Load File", sFilePath, sExtension)
        if bOk:
            if sNewFilePath.endswith(".sdc"):
                self.vLoadSetupFile(sNewFilePath, True)
                
            if sNewFilePath.endswith(".csv"):
                self.vLoadSeqFile(sNewFilePath, True)

    def slSaveSetup(self):
        logging.debug("SDC_DlgControl::slSaveSetup")

        if self.m_poCurrentGuiMode and self.m_poCurrentGuiMode.eGetMode() == SDC_GuiMode.MODE.PROG:
            sFilePath = self.m_poSettings.sGetSeqFilePath()
            sExtension = "CSV (*.csv);;SDC (*.sdc)"
        else:
            sFilePath = self.m_poSettings.sGetSetupFilePath()
            sExtension = "SDC (*.sdc);;CSV (*.csv)"

        sNewFilePath, bOk = QFileDialog.getSaveFileName(self, "Save File", sFilePath, sExtension)
        if bOk:
            if sNewFilePath.endswith(".sdc"):
                self.vSaveSetupFile(sNewFilePath, True)
                
            if sNewFilePath.endswith(".csv"):
                self.vSaveSeqFile(sNewFilePath, True)

    def slHwSettings(self):
        logging.debug("SDC_DlgControl::slHwSettings")
        poDevice = self.m_poControl.poGetHwCtrlObj().poGetCurrentDevice()
        if poDevice:
            oDialog = SDC_DlgHwSettings(poDevice)
            oDialog.exec()

    def slSettings(self):
        logging.debug("SDC_DlgControl::slSettings")
        oDialog = SDC_DlgSettings()
        if oDialog.exec () == QDialog.Accepted:
            for poCoreDialog in self.m_mlpoCoreDialogs.values():
                dwFlags = poCoreDialog.dwGetFlags()

                if self.m_poSettings.bCompactCoreDialogs():
                    dwFlags |= SDC_DlgCore.FLAGS.COMPACT
                else:
                    dwFlags &= ~SDC_DlgCore.FLAGS.COMPACT

                poCoreDialog.vSetFlags(dwFlags)
            self.vResizeDialog()

    def slStart(self):
        logging.debug("SDC_DlgControl::slStart")
        if self.poButtonStart.eGetType() == SDC_PushButton.type.START:
            if self.bStartHw():
                self.m_poStatusThread.vStart()
                self.poButtonStart.vSetType(SDC_PushButton.type.STOP)
        elif self.poButtonStart.eGetType() == SDC_PushButton.type.STOP:
            self.poButtonStart.vSetType(SDC_PushButton.type.START)
            self.vStopHw()
            self.m_poStatusThread.vStop()
    
    #void slAddTableRows   ();
    def slAddTableRows(self):
        logging.debug("SDC_DlgControl::slAddTableRows")
        self.vPrgTableAddRows(self.poSpinBoxAddTableRows.value())

    #void slClearTable     ();
    def slClearTable(self):
        logging.debug("SDC_DlgControl::slClearTable")
        self.vClearPrgTable()

    #void slWriteToQueue   ();
    def slWriteToQueue(self):
        logging.debug("SDC_DlgControl::slWriteToQueue")
        self.vUpdateCmdListFromTable()

        self.m_poHwControl.dwWriteToQueue(self.m_voCmdList)

        self.vUpdateQueueStatus()

    #void slButtonExamples ();
    def slButtonExamples(self):
        logging.debug("SDC_DlgControl::slButtonExamples")
        oPos = self.ui.poButtonExamples.mapToGlobal(QPoint(0, 0))
        oPos.setY(oPos.y() + 24)
        self.m_poExampleMenu.exec(oPos)

    #void slLoadExample    (const QString&);
    def slLoadExample(self, sFilePath : str):
        logging.debug("SDC_DlgControl::slLoadExample")
        self.vLoadSeqFile(sFilePath, False)

    def slTimeoutResize(self):
        logging.debug("SDC_DlgControl::slTimeoutResize")
        if not self.isMaximized():
            oRectDlgCore = self.poWidgetMain.geometry()
            oRectDlgMain = self.geometry()

            lOffsetX = 130

            lOffsetY = 160
            if self.poGroupCoreFilter.isVisible():
                lOffsetY += 62

            lHeight = oRectDlgCore.height()

            oRectDlgMain.setWidth(lOffsetX + oRectDlgCore.width())
            oRectDlgMain.setHeight(lOffsetY + lHeight)

            self.setGeometry(oRectDlgMain)

    def vInitGUI(self):
        logging.debug("SDC_DlgControl::vInitGUI")
        # set tool button icons
        self.poButtonAddCore.vSetIcons(QIcon(":/resources/add.png"), QIcon(":/resources/add_hover.png"))
        self.poButtonSwitchMode.vSetIcons(QIcon(":/resources/prg.png"), QIcon(":/resources/prg_hover.png"))
        self.poButtonOpenSetup.vSetIcons(QIcon(":/resources/open.png"), QIcon(":/resources/open_hover.png"))
        self.poButtonSaveSetup.vSetIcons(QIcon(":/resources/save.png"), QIcon(":/resources/save_hover.png"))
        self.poButtonSettings.vSetIcons(QIcon(":/resources/settings.png"), QIcon(":/resources/settings_hover.png"))
        self.poButtonHwSettings.vSetIcons(QIcon(":/resources/hwsettings.png"), QIcon(":/resources/hwsettings_hover.png"))
        self.poButtonQuit.vSetIcons(QIcon(":/resources/quit.png"), QIcon(":/resources/quit_hover.png"))

        self.poButtonStart.vSetType(SDC_PushButton.type.START)
        self.poButtonWriteToQueue.vSetType(SDC_PushButton.type.WRITE)
    
        self.poListWidgetRegs.setSelectionMode(QAbstractItemView.SingleSelection)
        self.poListWidgetRegs.setDragEnabled(True)
        self.poListWidgetRegs.setDragDropMode(QAbstractItemView.DragOnly)
        self.poListWidgetRegs.setStyleSheet("QListWidget::item:selected { color: white; background: #007ACD; }")

        self.ui.poTableWidget.viewport().installEventFilter(self)
        self.ui.poTableWidget.installEventFilter(self)

        # set connections
        self.ui.poButtonQuit.clicked.connect(self.close)
        self.ui.poButtonAddCore.clicked.connect(self.slAddCoreDialog)
        self.ui.poButtonSwitchMode.clicked.connect(self.slSwitchMode)
        self.ui.poButtonOpenSetup.clicked.connect(self.slOpenSetup)
        self.ui.poButtonSaveSetup.clicked.connect(self.slSaveSetup)
        self.ui.poButtonHwSettings.clicked.connect(self.slHwSettings)
        self.ui.poButtonSettings.clicked.connect(self.slSettings)
        self.ui.poButtonStart.clicked.connect(self.slStart)
        self.ui.poButtonAddTableRows.clicked.connect(self.slAddTableRows)
        self.ui.poButtonClearTable.clicked.connect(self.slClearTable)
        self.ui.poButtonWriteToQueue.clicked.connect(self.slWriteToQueue)
        self.ui.poButtonExamples.clicked.connect(self.slButtonExamples)
        self.ui.poComboBoxDevice.currentIndexChanged.connect(self.slDeviceChanged)
        self.ui.poComboBoxNumChannels.currentIndexChanged.connect(self.slNumChannelsChanged)
        self.ui.poComboBoxSamplingrate.currentIndexChanged.connect(self.slSamplingrateChanged)
        self.ui.poSpinBoxShowNumCores.valueChanged.connect(self.slShowNumCores)
        self.ui.poComboBoxShowChannels.currentIndexChanged.connect(self.slShowChannels)
        self.ui.poLineEditReg.textChanged.connect(self.slRegTextChanged)
        self.ui.poTableWidget.itemClicked.connect(self.slPrgTableItemClicked)
        self.ui.poTableWidget.itemChanged.connect(self.slPrgTableItemChanged)
        self.ui.poTableWidget.itemSelectionChanged.connect(self.slPrgTableItemSelectionChanged)
        self.ui.poListWidgetRegs.itemDoubleClicked.connect(self.slRegItemDoubleClicked)
        self.m_poControl.sigShowMessage.connect(self.slShowMessageBox)
        
        self.vCreateExampleMenu()
        self.vCreatePrgTable()

        self.poSplitter.setStretchFactor(0, 2)
        self.poSplitter.setStretchFactor(1, 4)

        if self.m_poControl.bLoadRegisterFile():    
            self.poListWidgetRegs.addItems(self.m_poControl.oGetStrListRegisterNames())
        else:
            self.poListWidgetRegs.addItem("Register list could not be loaded.")
            self.poListWidgetRegs.setSelectionMode(QAbstractItemView.NoSelection)
            self.poListWidgetRegs.setEnabled(False)

    def bInitControl(self) -> bool:
        logging.debug("SDC_DlgControl::bInitControl")
        oStrDeviceNames = self.m_poControl.oInit()
        if len(oStrDeviceNames):
            for name in oStrDeviceNames:
                self.ui.poComboBoxDevice.addItem(name)
            self.ui.poComboBoxDevice.setCurrentIndex(0)
        else:
            self.ui.poComboBoxDevice.addItem("No Device");
            self.ui.poComboBoxDevice.setEnabled(False);

            return False

        return True
    
    # void vInitM4i66xx ();
    def vInitM4i66xx(self):
        logging.debug("SDC_DlgControl::vInitM4i66xx")
        self.poLabelNumChannels.setHidden(True)
        self.poComboBoxNumChannels.setHidden(True)
        self.poLabelSamplingrate.setHidden(True)
        self.poComboBoxSamplingrate.setHidden(True)
        self.poButtonAddCore.setHidden(False)
        self.poGroupCoreFilter.setHidden(True)

        self.poTextEditInfo.clear()

        for lChIdx in range(self.m_poDevice.lGetNumMaxChannels()):
            if self.m_poDevice.bIsDDS50():
                if (lChIdx == 0): self.vAddCoreDialog(lChIdx, DEFAULT_CORE_DDS50_CH0)
                if (lChIdx == 1): self.vAddCoreDialog(lChIdx, DEFAULT_CORE_DDS50_CH1)
                if (lChIdx == 2): self.vAddCoreDialog(lChIdx, DEFAULT_CORE_DDS50_CH2)
                if (lChIdx == 3): self.vAddCoreDialog(lChIdx, DEFAULT_CORE_DDS50_CH3)
            else:
                if (lChIdx == 0): self.vAddCoreDialog(lChIdx, DEFAULT_CORE_DDS20_CH0)
                if (lChIdx == 1): self.vAddCoreDialog(lChIdx, DEFAULT_CORE_DDS20_CH1)
                if (lChIdx == 2): self.vAddCoreDialog(lChIdx, DEFAULT_CORE_DDS20_CH2)
                if (lChIdx == 3): self.vAddCoreDialog(lChIdx, DEFAULT_CORE_DDS20_CH3)

        lNumSetCores = self.m_poSettings.lGetNumCoreSettings(self.m_poDevice.lGetSerialNumber())
        for lChIdx in range(lNumSetCores):
            self.vAddCoreDialog()

        self.vResizeDialog()

    # void vInitM4i96xx ();
    def vInitM4i96xx(self):
        logging.debug("SDC_DlgControl::vInitM4i96xx")
        self.vInitM4i66xx()

    # void vInitM2p65xx ();
    def vInitM2p65xx(self):
        logging.debug("SDC_DlgControl::vInitM2p65xx")
        self.ui.poLabelNumChannels.setHidden(False)
        self.ui.poComboBoxNumChannels.setHidden(False)
        self.ui.poLabelSamplingrate.setHidden(True)
        self.ui.poComboBoxSamplingrate.setHidden(True)
        self.ui.poButtonAddCore.setHidden(True)
        self.ui.poGroupCoreFilter.setHidden(False)

        self.vInitComboBoxChannels(self.m_poDevice.lGetNumMaxChannels())

        if self.ui.poComboBoxNumChannels.count():
            try:
                lChNum = int(self.ui.poComboBoxNumChannels.currentData())
            except:
                lChNum = 1
            self.vSelectNumChM2p65xx(lChNum)
        

    # void vInitM5i63xx ();
    def vInitM5i63xx(self):
        logging.debug("SDC_DlgControl::vInitM5i63xx")
        self.ui.poLabelNumChannels.setHidden(False)
        self.ui.poComboBoxNumChannels.setHidden(False)
        self.ui.poLabelSamplingrate.setHidden(False)
        self.ui.poComboBoxSamplingrate.setHidden(False)
        self.ui.poButtonAddCore.setHidden(True)
        self.ui.poGroupCoreFilter.setHidden(False)

        self.ui.poTextEditInfo.clear()

        self.vInitComboBoxChannels(self.m_poDevice.lGetNumMaxChannels())

        if self.ui.poComboBoxNumChannels.count():
            try:
                lChNum = int(self.ui.poComboBoxNumChannels.currentData())
            except:
                lChNum = 1
            self.vSelectNumChM5i63xx(lChNum)

    # void vInitComboBoxChannels (int lNumChannels);
    def vInitComboBoxChannels(self, lNumChannels : int):
        logging.debug("SDC_DlgControl::vInitComboBoxChannels")
        self.ui.poComboBoxNumChannels.currentIndexChanged.disconnect(self.slNumChannelsChanged)

        self.ui.poComboBoxNumChannels.clear()

        for lChIdx in range(lNumChannels):
            if lChIdx == 0: self.ui.poComboBoxNumChannels.addItem ("1 Channel",  1)
            if lChIdx == 1: self.ui.poComboBoxNumChannels.addItem ("2 Channels", 2)
            if lChIdx == 3: self.ui.poComboBoxNumChannels.addItem ("4 Channels", 4)
            if lChIdx == 7: self.ui.poComboBoxNumChannels.addItem ("8 Channels", 8)

        # set to last combobox element
        if self.ui.poComboBoxNumChannels.count():
            self.ui.poComboBoxNumChannels.setCurrentIndex(self.ui.poComboBoxNumChannels.count() - 1)

        self.ui.poComboBoxNumChannels.currentIndexChanged.connect(self.slNumChannelsChanged)

    # void vInitComboBoxShowChannels (int lNumChannels);
    def vInitComboBoxShowChannels(self, lNumChannels : int):
        logging.debug("SDC_DlgControl::vInitComboBoxShowChannels")
        self.ui.poComboBoxShowChannels.clear()
        self.ui.poComboBoxShowChannels.addItem ("All", 0xFF)

        if lNumChannels > 1:
            self.ui.poLabelShowChannels.setHidden(False)
            self.ui.poComboBoxShowChannels.setHidden(False)
            for lChIdx in range(lNumChannels):
                self.ui.poComboBoxShowChannels.addItem("Ch{}".format(lChIdx), 0x1 << lChIdx)
            self.ui.poComboBoxShowChannels.setCurrentIndex(0)
        else:
            self.ui.poLabelShowChannels.setHidden(True)
            self.ui.poComboBoxShowChannels.setHidden(True)

    # void vSetShowNumCoresSpinBox (int lMin, int lMax, int lValue);
    def vSetShowNumCoresSpinBox(self, lMin : int, lMax : int, lValue : int):
        logging.debug("SDC_DlgControl::vSetShowNumCoresSpinBox")
        self.ui.poSpinBoxShowNumCores.setMinimum(lMin)
        self.ui.poSpinBoxShowNumCores.setMaximum(lMax)

        if lValue < lMax:
            self.ui.poSpinBoxShowNumCores.setValue(lValue)
        else:
            self.ui.poSpinBoxShowNumCores.setValue(lMax)

    # void vSelectNumChM2p65xx (int lNumCh);
    def vSelectNumChM2p65xx(self, lNumCh : int):
        logging.debug("SDC_DlgControl::vSelectNumChM2p65xx")
        self.vResetCoreDialogs()

        lCoresPerCh = self.m_poDevice.lGetCoresPerChannel(lNumCh)

        self.ui.poTextEditInfo.clear()
        self.ui.poTextEditInfo.setText(" " + str(lCoresPerCh) + " Cores per channel:")
        if lNumCh == 1:
            self.ui.poTextEditInfo.append(" Ch0-Cores: 00-15")

        if lNumCh == 2:
            self.ui.poTextEditInfo.append(" Ch0-Cores: 00-07 | Ch1-Cores: 08-15")

        if lNumCh == 4:
            self.ui.poTextEditInfo.append(" Ch0-Cores: 00-03 | Ch1-Cores: 04-07 | Ch2-Cores: 08-11, Ch3-Cores: 12-15")

        if lNumCh == 8:
            self.ui.poTextEditInfo.append(" Ch0-Cores: 00-01 | Ch1-Cores: 02-03 | Ch2-Cores: 04-05, Ch3-Cores: 06-07")
            self.ui.poTextEditInfo.append(" Ch4-Cores: 08-09 | Ch5-Cores: 10-11 | Ch6-Cores: 12-13, Ch7-Cores: 14-15")
        lChIdx = -1
        for lCoreIdx in range(self.m_poDevice.lGetMaxCores()):
            if not (lCoreIdx % lCoresPerCh):
                lChIdx += 1

            self.vAddCoreDialog(lChIdx, lCoreIdx, lCoreIdx % lCoresPerCh, True)

        self.vSetShowNumCoresSpinBox (1, lCoresPerCh, self.m_poSettings.lGetNumShowCores())

        self.vInitComboBoxShowChannels(lNumCh)

    # void vSelectNumChM5i63xx (int lNumCh);
    def vSelectNumChM5i63xx(self, lNumCh : int):
        logging.debug("SDC_DlgControl::vSelectNumChM5i63xx")
        self.ui.poComboBoxSamplingrate.currentIndexChanged.disconnect(self.slSamplingrateChanged)

        self.ui.poComboBoxSamplingrate.clear()

        self.ui.poComboBoxSamplingrate.addItem ("2.5 GS/s", 2500)
        self.ui.poComboBoxSamplingrate.addItem ("5 GS/s", 5000)

        if lNumCh == 1:
            self.ui.poComboBoxSamplingrate.addItem ("10 GS/s", 10000)

        self.ui.poComboBoxSamplingrate.setCurrentIndex(self.ui.poComboBoxSamplingrate.count() - 1)

        self.ui.poComboBoxSamplingrate.currentIndexChanged.connect(self.slSamplingrateChanged)

        self.vSetCoresChM5i63xx()

    # void vSetCoresChM5i63xx ();
    def vSetCoresChM5i63xx(self):
        logging.debug("SDC_DlgControl::vSetCoresChM5i63xx")
        self.vResetCoreDialogs()

        lSRate_MS = self.ui.poComboBoxSamplingrate.currentData()
        lNumCh = self.ui.poComboBoxNumChannels.currentData()
        lCoresPerCh = self.m_poDevice.lGetCoresPerChannel(lNumCh, lSRate_MS)

        lMaxCores = lCoresPerCh * lNumCh
        
        self.m_poDevice.vSetGeneralSettings("SPC_SAMPLERATE", lSRate_MS * 1000000)
        self.m_poDevice.vSetGeneralSettings("SPC_CHENABLE", (0x1 << lNumCh) - 1)

        lChIdx = -1
        for lCoreIdx in range(lMaxCores):
            if not (lCoreIdx % lCoresPerCh):
                lChIdx += 1

            self.vAddCoreDialog(lChIdx, lCoreIdx, lCoreIdx % lCoresPerCh, True)
        
        self.ui.poTextEditInfo.clear()
        self.ui.poTextEditInfo.setText(str(lCoresPerCh) + " Cores per channel:")

        if lSRate_MS == 2500:
            if lNumCh == 1:
                self.ui.poTextEditInfo.append("Ch0-Cores: 00-63")
            else:
                self.ui.poTextEditInfo.append("Ch0-Cores: 00-31")
                self.ui.poTextEditInfo.append("Ch1-Cores: 32-63")

        if lSRate_MS == 5000:  
            if lNumCh == 1:
                self.ui.poTextEditInfo.append("Ch0-Cores: 00-31")
            else:
                self.ui.poTextEditInfo.append("Ch0-Cores: 00-15")
                self.ui.poTextEditInfo.append("Ch1-Cores: 16-31")

        if lSRate_MS == 10000:
            if lNumCh == 1:
                self.ui.poTextEditInfo.append("Ch0-Cores: 00-15")

        self.vSetShowNumCoresSpinBox(1, lCoresPerCh, self.m_poSettings.lGetNumShowCores())

        self.vInitComboBoxShowChannels(lNumCh)

    # void vSetGuiMode (SDC_GuiMode::MODE eMode);
    def vSetGuiMode(self, eMode):
        logging.debug("SDC_DlgControl::vSetGuiMode")
        poNewGuiMode = self.m_poSettings.poGetGuiMode(eMode)
        if not poNewGuiMode:
            return

        if self.m_poCurrentGuiMode:
            self.m_poCurrentGuiMode.vSetWindowState(self.windowState())
            self.m_poCurrentGuiMode.vSetGeometry(self.geometry())
        
        if eMode == SDC_GuiMode.MODE.CTRL:
            self.ui.poButtonSwitchMode.vSetIcons (QIcon (":/resources/prg.png"), QIcon (":/resources/prg_hover.png"))
            self.ui.poButtonSwitchMode.setToolTip ("Switch to programming mode")

        if eMode == SDC_GuiMode.MODE.PROG:
            self.ui.poButtonSwitchMode.vSetIcons (QIcon (":/resources/control.png"), QIcon (":/resources/control_hover.png"))
            self.ui.poButtonSwitchMode.setToolTip ("Switch to control mode")
            self.m_poHwControl.dwReset()
            self.vUpdateQueueStatus()

        self.ui.poStackedWidget.setCurrentIndex(poNewGuiMode.lGetWidgetIndex())

        # self.ui.setGeometry(poNewGuiMode.oGetGeometry()) # TODO this moves the window to a specific screen
        self.ui.setWindowState(poNewGuiMode.eGetWindowState())

        self.m_poCurrentGuiMode = poNewGuiMode

    def vResizeDialog(self):
        logging.debug("SDC_DlgControl::vResizeDialog")
        self.m_poTimerResize.start(100)
    
    # void vUpdateShowCoresFilter ();
    def vUpdateShowCoresFilter(self):
        logging.debug("SDC_DlgControl::vUpdateShowCoresFilter")
        lNumActiveChannels = self.ui.poComboBoxNumChannels.currentData()
        lShowNumCores = self.ui.poSpinBoxShowNumCores.value()
        lShowChMask = self.ui.poComboBoxShowChannels.currentData()

        lSRate_MS = 0
        if self.ui.poComboBoxSamplingrate.isVisible():
            lSRate_MS = self.ui.poComboBoxSamplingrate.currentData()

        lCoresPerCh = 0
        if self.m_poDevice:
            lCoresPerCh = self.m_poDevice.lGetCoresPerChannel(lNumActiveChannels, lSRate_MS)

        if  not lCoresPerCh:
            return

        for poCoreDialog in self.m_mlpoCoreDialogs.values():
            lCurrentMask = 0x1 << poCoreDialog.lGetChNum()

            if lCurrentMask & lShowChMask:
                if (poCoreDialog.lGetCoreNum() % lCoresPerCh) < lShowNumCores:
                    poCoreDialog.setHidden(False)
                else:
                    poCoreDialog.setHidden(True)
            else:
                poCoreDialog.setHidden(True)

        self.m_poSettings.vSetNumShowCores(lShowNumCores)

    # void vUpdateCmdListFromTable ();
    def vUpdateCmdListFromTable(self):
        logging.debug("SDC_DlgControl::vUpdateCmdListFromTable")

        self.m_voCmdList.clear()

        for lRow in range(self.ui.poTableWidget.rowCount()):
            lReg = -1

            # get register entry
            poItem = self.ui.poTableWidget.item(lRow, 0)
            if poItem:
                sText = poItem.text()

                try:
                    lReg = int(sText)
                except ValueError:
                    lReg = 0
                if not lReg:
                    lReg = self.m_poControl.lGetRegisterValue(sText)

            if lReg == -1:
                continue

            lType = TYPE_INT64
            poComboBox = self.ui.poTableWidget.cellWidget(lRow, 1)
            if poComboBox and poComboBox.currentText() == "DOUBLE":
                lType = TYPE_DOUBLE

            # get value entry
            poItem = self.ui.poTableWidget.item(lRow, 2)
            if poItem:
                sText = poItem.text()
                if sText.startswith("SP"):
                    oValue = self.m_poControl.lGetRegisterValue(sText)
                else:
                    oValue = sText

            oDrvCmd = SDC_DrvCmd()
            oDrvCmd.vSetRegister(lReg)
            oDrvCmd.vSetType(lType)
            oDrvCmd.vSetValue(oValue)

            self.m_voCmdList.append(oDrvCmd)
       
    # void vUpdateQueueStatus ();
    def vUpdateQueueStatus(self):
        logging.debug("SDC_DlgControl::vUpdateQueueStatus")
        self.m_voCmdList.clear()

        for lRow in range(self.ui.poTableWidget.rowCount()):
            lReg = -1

            # get register entry
            poItem = self.ui.poTableWidget.item(lRow, 0)
            if poItem:
                sText = poItem.text()

                try:
                    lReg = int(sText)
                except ValueError:
                    lReg = 0
                if not lReg:
                    lReg = self.m_poControl.lGetRegisterValue(sText)

            if lReg == -1:
                continue

            lType = TYPE_INT64
            poComboBox = self.ui.poTableWidget.cellWidget(lRow, 1)
            if poComboBox and poComboBox.currentText() == "DOUBLE":
                lType = TYPE_DOUBLE

            # get value entry
            poItem = self.ui.poTableWidget.item(lRow, 2)
            if poItem:
                sText = poItem.text()
                if sText.startswith("SP"):
                    oValue = self.m_poControl.lGetRegisterValue(sText)
                else:
                    oValue = sText

            oDrvCmd = SDC_DrvCmd()
            oDrvCmd.vSetRegister(lReg)
            oDrvCmd.vSetType(lType)
            oDrvCmd.vSetValue(oValue)

            self.m_voCmdList.append(oDrvCmd)

    def bStartHw(self) -> bool:
        logging.debug("SDC_DlgControl::bStartHw")

        if self.m_poCurrentGuiMode and self.m_poCurrentGuiMode.eGetMode() == SDC_GuiMode.MODE.PROG:
            self.vUpdateCmdListFromTable()

            dwError = self.m_poHwControl.dwDoGeneralSetup()

            lNumLoop = 1
            if self.ui.poCheckBoxLoop.isChecked():
                lNumLoop = self.ui.poSpinBoxLoop.value()

            if  not dwError:
                dwError = self.m_poHwControl.dwWriteToQueue(self.m_voCmdList, lNumLoop)
        else:
            self.m_poHwControl.vClearCoreConnectionsMasks()
                
            dwError = self.m_poHwControl.dwDoGeneralSetup()

            if not dwError:
                for poCoreDialog in self.m_mlpoCoreDialogs.values():
                    dwError = self.m_poHwControl.dwDoCoreSetup(poCoreDialog.poGetCoreSettings())
                    if dwError:
                        break

            # set core connections (M4i.66xx, M4i.96xx)
            if not dwError and (self.m_poDevice.lGetCardFamily() == TYP_M4I66XX_X8 or self.m_poDevice.lGetCardFamily() == TYP_M4I96XX_X8):
                dwError = self.m_poHwControl.dwSetCoreConnections()
            
        if not dwError:
            dwError = self.m_poHwControl.dwStart()
            
        if dwError:
            self.slShowMessageBox(SDC_Settings.MSBOX_TYPE.MSB_ERROR, "Driver Error", self.m_poHwControl.sGetLastErrorText())
            return False
        
        return True
    
    def vStopHw(self):
        logging.debug("SDC_DlgControl::vStopHw")
        self.m_poHwControl.vStop()

    def vResetCoreDialogs(self):
        logging.debug("SDC_DlgControl::vResetCoreDialogs")
        for core_dialog in self.m_mlpoCoreDialogs.values():
            core_dialog.setParent(None)
        self.m_mlpoCoreDialogs = {}
    
    # void vLoadSetupFile (const QString& sFilePath, bool bSavePath);
    def vLoadSetupFile(self, sFilePath : str, bSavePath : bool):
        logging.debug("SDC_DlgControl::vLoadSetupFile")
        if QFile.exists (sFilePath):
            if bSavePath:
                self.m_poSettings.vSetSetupFilePath(sFilePath)

            oSettings = QSettings(sFilePath, QSettings.IniFormat, self)

            try:
                lFileVersion = int(oSettings.value("FileVersion", 0))
            except:
                lFileVersion = 0
            if lFileVersion < SETUP_FILE_VERSION:
                QMessageBox.critical(self, "Load Setup Failed", "The setup file was created with an older DDS Control version and cannot be loaded.")
                return

            lDevIndex = oSettings.value ("DevIndex", 0, int)
            self.m_poSettings.vLoadCoreSettings(oSettings)

            for poCoreDialog in self.m_mlpoCoreDialogs.values():
                poCoreDialog.vUpdateCoreGUI()

            # read hardware settings
            lNumDevices = oSettings.value("NumDevices", 0, int)
            for lDevIdx in range(lNumDevices):
                oSettings.beginGroup("Device{}".format(lDevIdx))

                sDeviceName = oSettings.value("Name", "")
                poDevice = self.m_poHwControl.poGetDeviceByeName(sDeviceName)
                if poDevice:
                    lNumChannels = oSettings.value("NumChannels", 0, int)
                    for lChIdx in range(lNumChannels):
                        oChSetting = poDevice.oGetChSettings(lChIdx)

                        oSettings.beginGroup("Ch{}".format(lChIdx))

                        lValue = oSettings.value ("OutputEnabled", 1, int)
                        oChSetting.vSetOutputEnabled(lValue)

                        lValue = oSettings.value ("OutputRange", 1000, int)
                        oChSetting.vSetOutputRange_mV(lValue)

                        lValue = oSettings.value ("Filter", 0, int)
                        oChSetting.vSetFilter(lValue)
                        
                        oSettings.endGroup()

                        poDevice.vSetChSettings(lChIdx, oChSetting)

                oSettings.endGroup()

            self.ui.poComboBoxDevice.currentIndexChanged.disconnect(self.slDeviceChanged)
            self.ui.poComboBoxDevice.setCurrentIndex(lDevIndex)
            self.slDeviceChanged(lDevIndex)
            self.ui.poComboBoxDevice.currentIndexChanged.connect(self.slDeviceChanged)
    
    # void vSaveSetupFile (const QString& sFilePath, bool bSavePath);
    def vSaveSetupFile(self, sFilePath : str, bSavePath : bool):
        logging.debug("SDC_DlgControl::vSaveSetupFile")
        if QFile.exists(sFilePath):
            QFile.remove(sFilePath)

        if bSavePath:
            self.m_poSettings.vSetSetupFilePath(sFilePath)

        oSettings = QSettings(sFilePath, QSettings.IniFormat, self)

        oSettings.setValue("FileVersion", SETUP_FILE_VERSION)
        oSettings.setValue("DevIndex", self.ui.poComboBoxDevice.currentIndex())

        self.m_poSettings.vSaveCoreSettings(oSettings)
        
        # save hardware settings
        oSettings.setValue("NumDevices", self.m_poHwControl.lGetNumOfDevices())
        
        for lDevIdx in range(self.m_poHwControl.lGetNumOfDevices()):
            poDevice = self.m_poHwControl.poGetDevice(lDevIdx)
            if poDevice:
                oSettings.beginGroup("Device{}".format(lDevIdx))
                oSettings.setValue("Name", poDevice.sGetDeviceName())
                
                oSettings.setValue("NumChannels", int(poDevice.lGetNumMaxChannels()))

                for lChIdx in range(poDevice.lGetNumMaxChannels()):
                    oChSetting = poDevice.oGetChSettings(lChIdx)
                    
                    oSettings.beginGroup("Ch{}".format(lChIdx))
                    oSettings.setValue("OutputEnabled", int(oChSetting.lOutputEnabled()))
                    oSettings.setValue("OutputRange", int(oChSetting.lGetOutputRange_mV()))
                    oSettings.setValue("Filter", int(oChSetting.lGetFilter()))
                    oSettings.endGroup()
                
                oSettings.endGroup()

    # void vLoadSeqFile   (const QString& sFilePath, bool bSavePath);
    def vLoadSeqFile(self, sFilePath : str, bSavePath : bool):
        logging.debug("SDC_DlgControl::vLoadSeqFile")
        if bSavePath:
            self.m_poSettings.vSetSeqFilePath(sFilePath)

        voFileData = self.m_poControl.bReadCSVFile(sFilePath)
        if voFileData:
            self.vSetPrgTableContent(voFileData)

    # void vSaveSeqFile   (const QString& sFilePath, bool bSavePath);
    def vSaveSeqFile(self, sFilePath : str, bSavePath : bool):
        logging.debug("SDC_DlgControl::vSaveSeqFile")
        if bSavePath:
            self.m_poSettings.vSetSeqFilePath(sFilePath)

        voFileData = self.bGetPrgTableContent()
        if voFileData:
            self.m_poControl.bWriteCSVFile(sFilePath, voFileData)

    # void vCreateExampleMenu  ();
    def vCreateExampleMenu(self):
        logging.debug("SDC_DlgControl::vCreateExampleMenu")
        self.m_poExamplesMapper = QSignalMapper(self)
        # connect (m_poExamplesMapper, SIGNAL (mapped (const QString&)), this, SLOT (slLoadExample (const QString&)));
        self.m_poExamplesMapper.mapped[str].connect(self.slLoadExample)

        self.m_poExampleMenu = QMenu(self)
        self.m_poExampleMenu.setStyleSheet("QMenu { background: #007ACD; } QMenu::item:selected { background: #484A56; }")

        oFont = self.m_poExampleMenu.font()
        oFont.setPixelSize(14)
        oFont.setFamily("Arial")
        oFont.setBold(True)
        self.m_poExampleMenu.setFont(oFont)

        vsExamplePaths = self.m_poSettings.vsGetExamplesPaths()

        if vsExamplePaths:
            for sExamplePath in vsExamplePaths:
                oFileInfo = QFileInfo(sExamplePath)
                poAction = QAction(oFileInfo.baseName(), self)
                self.m_poExampleMenu.addAction(poAction)

                self.m_poExamplesMapper.setMapping(poAction, sExamplePath)
                # connect (poAction, SIGNAL (triggered ()), m_poExamplesMapper, SLOT (map ()));
                poAction.triggered.connect(self.m_poExamplesMapper.map)

    # void vCreatePrgTable     ();
    def vCreatePrgTable(self):
        logging.debug("SDC_DlgControl::vCreatePrgTable")
        self.ui.poTableWidget.setAcceptDrops(True)
        self.ui.poTableWidget.setDragEnabled(True)
        self.ui.poTableWidget.setDragDropMode(QAbstractItemView.DragDrop)
        self.ui.poTableWidget.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.ui.poTableWidget.horizontalHeader().setSectionsClickable(False)
        self.ui.poTableWidget.horizontalHeader().setStretchLastSection(True)
        self.ui.poTableWidget.verticalHeader().setHidden(True)
        oStrList = ["Register", "Type", "Value"]

        for lColumn in range(len(oStrList)):
            self.ui.poTableWidget.insertColumn(lColumn)

        self.ui.poTableWidget.setHorizontalHeaderLabels(oStrList)

        for lColumn in range(len(oStrList)):
            self.vInitPrgTableItem(self.ui.poTableWidget.horizontalHeaderItem(lColumn))

        for lRow in range(10):
            self.vPrgTableInsertRow(lRow)

        self.ui.poTableWidget.horizontalHeader().resizeSection(0, 400)
        self.ui.poTableWidget.horizontalHeader().resizeSection(1, 150)
        self.ui.poTableWidget.horizontalHeader().resizeSection(2, 200)

    # void vClearPrgTable      ();
    def vClearPrgTable(self):
        logging.debug("SDC_DlgControl::vClearPrgTable")
        lRows = self.ui.poTableWidget.rowCount()

        for lIdx in range(lRows):
            self.ui.poTableWidget.removeRow(0)

        self.m_poSelectedPrgTableItem = None

    # void vPrgTableInsertRow  (int lRow = -1);
    def vPrgTableInsertRow(self, lRow : int = -1):
        logging.debug("SDC_DlgControl::vPrgTableInsertRow")
        lNewRow = 0
        if lRow > -1:
            lNewRow = lRow
        else:
            lNewRow = self.ui.poTableWidget.rowCount()

        self.ui.poTableWidget.insertRow(lNewRow)

        for lColumn in range(self.ui.poTableWidget.columnCount()):
            self.vCreatePrgTableItem(lNewRow, lColumn)

        self.ui.poTableWidget.verticalHeader().resizeSection(lNewRow, 25)

    # void vPrgTableSelectRow  (int lRow, bool bSelect);
    def vPrgTableSelectRow(self, lRow : int, bSelect : bool):
        logging.debug("SDC_DlgControl::vPrgTableSelectRow")
        oItemColor = None
        sWidgetStyle = ""

        if bSelect:
            oItemColor = QColor("#3399FE")
            sWidgetStyle = "QComboBox { background: #3399FE; }"
        else:
            if lRow % 2:
                oItemColor = Qt.darkGray
                sWidgetStyle = "QWidget { color:#333333; background: darkGray; }"
            else:
                oItemColor = Qt.lightGray
                sWidgetStyle = "QWidget { color:#333333; background: lightGray; }"

        for lColumn in range(self.ui.poTableWidget.columnCount()):
            if (self.ui.poTableWidget.item(lRow, lColumn)):
                self.ui.poTableWidget.item(lRow, lColumn).setBackground(oItemColor)

            if (self.ui.poTableWidget.cellWidget(lRow, lColumn)):
                self.ui.poTableWidget.cellWidget(lRow, lColumn).setStyleSheet(sWidgetStyle)

    # void vPrgTableAddRows    (int lNumRows = 1, bool bShowProgress = false);
    def vPrgTableAddRows(self, lNumRows : int = 1, bShowProgress : bool = False):
        logging.debug("SDC_DlgControl::vPrgTableAddRows")
        poDlgProgress = QProgressDialog()

        self.ui.poTableWidget.viewport().hide()
        self.ui.poTableWidget.verticalScrollBar().hide()

        if bShowProgress:
            poDlgProgress = QProgressDialog ("Processing...", "Abort", 0, lNumRows, self)
            poDlgProgress.setWindowModality(Qt.WindowModal)

        bAbort = False
        for lRow in range(lNumRows):
            if poDlgProgress:
                poDlgProgress.setValue(lRow)

                if poDlgProgress.wasCanceled():
                    bAbort = True
                    break

            self.vPrgTableInsertRow()

        if poDlgProgress:
            poDlgProgress.setValue(lNumRows)

        if bAbort:
            self.vClearPrgTable()

        self.ui.poTableWidget.viewport().show()
        self.ui.poTableWidget.verticalScrollBar().show()

    # void vCreatePrgTableItem (int lRow, int lColumn);
    def vCreatePrgTableItem(self, lRow : int, lColumn : int):
        logging.debug("SDC_DlgControl::vCreatePrgTableItem")
        self.ui.poTableWidget.itemChanged.disconnect(self.slPrgTableItemChanged)

        if lColumn == 1:
            poComboBox = QComboBox()
            self.vInitPrgTableComboBox(poComboBox, lRow)
            self.ui.poTableWidget.setCellWidget(lRow, lColumn, poComboBox)
        else:
            poItem = QTableWidgetItem()
            self.vInitPrgTableItem(poItem, lRow)
            self.ui.poTableWidget.setItem(lRow, lColumn, poItem)

        self.ui.poTableWidget.itemChanged.connect(self.slPrgTableItemChanged)

    # void vInitPrgTableItem   (QTableWidgetItem* poItem, int lIdx = -1);
    def vInitPrgTableItem(self, poItem, lIdx : int = -1):
        logging.debug("SDC_DlgControl::vInitPrgTableItem")
        if poItem:
            oFont = poItem.font()

            oFont.setFamily("Arial")
            oFont.setBold(True)

            if lIdx >= 0:
                oFont.setPixelSize(14)

                poItem.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if lIdx % 2:
                    poItem.setBackground(Qt.darkGray)
                else:
                    poItem.setBackground(Qt.lightGray)
                
                poItem.setForeground(QColor("#333333"))
            else:
                oFont.setPixelSize(16)
                poItem.setForeground(QColor ("#333333"))

            poItem.setFont(oFont)

    # void vInitPrgTableWidget (QWidget* poWidget, int lIdx);
    def vInitPrgTableComboBox(self, poComboBox, lIdx : int):
        logging.debug("SDC_DlgControl::vInitPrgTableComboBox")
        # poComboBox = QComboBox(poWidget)

        oFont = poComboBox.font()

        oFont.setFamily("Arial")
        oFont.setBold(True)
        oFont.setPixelSize(14)

        if lIdx % 2:
            poComboBox.setStyleSheet("QWidget { color:#333333; background: darkGray; }")
        else:
            poComboBox.setStyleSheet("QWidget { color:#333333; background: lightGray; }")
        
        poComboBox.addItem("INT64")
        poComboBox.addItem("DOUBLE")

        poComboBox.setFont(oFont)

    # void vSetPrgTableContent (QVector <QStringList> voTableData);
    def vSetPrgTableContent(self, voTableData : list[list[str]]):
        logging.debug("SDC_DlgControl::vSetPrgTableContent")
        # QTableWidgetItem* poItem;

        self.vClearPrgTable()

        self.vPrgTableAddRows(len(voTableData), True)

        for lRowIdx in range(len(voTableData)):
            if len(voTableData[lRowIdx]) == 3:
                # set register cell
                poItem = self.ui.poTableWidget.item(lRowIdx, 0)
                if poItem:
                    poItem.setText(voTableData[lRowIdx][0])

                # set type cell
                poComboBox = self.ui.poTableWidget.cellWidget(lRowIdx, 1)
                if poComboBox:
                    if voTableData[lRowIdx][1].upper() == "DOUBLE":
                        poComboBox.setCurrentIndex(1)
                    else:
                        poComboBox.setCurrentIndex(0)

                # set value cell
                poItem = self.ui.poTableWidget.item(lRowIdx, 2)
                if poItem:
                    poItem.setText(voTableData[lRowIdx][2])

    # bool bGetPrgTableContent (QVector <QStringList> *pvoTableData);
    def bGetPrgTableContent(self) -> list[list[str]]:
        logging.debug("SDC_DlgControl::bGetPrgTableContent")
        if not self.ui.poTableWidget.rowCount():
            return False

        pvoTableData = []

        for lRow in range(self.ui.poTableWidget.rowCount()):
            if not self.ui.poTableWidget.item(lRow, 0).text():
                break

            oStrList = []
            oStrList.append(self.ui.poTableWidget.item(lRow, 0).text())
            
            poComboBox = self.ui.poTableWidget.cellWidget(lRow, 1)
            if poComboBox:
                oStrList.append(poComboBox.currentText())
            
            oStrList.append(self.ui.poTableWidget.item(lRow, 2).text())

            pvoTableData.append(oStrList)

        return pvoTableData
    
    # bool bCopyPrgTableRow  (int lRowSource, int lRowDest);
    def bCopyPrgTableRow(self, lRowSource : int, lRowDest : int) -> bool:
        logging.debug("SDC_DlgControl::bCopyPrgTableRow")
        poItemSourceReg = self.ui.poTableWidget.item(lRowSource, 0)
        poItemSourceVal = self.ui.poTableWidget.item(lRowSource, 2)
        poComboBoxSource = self.ui.poTableWidget.cellWidget(lRowSource, 1)

        if not poItemSourceReg or not poItemSourceVal or not poComboBoxSource:
            return False

        poItemDestReg = self.ui.poTableWidget.item(lRowDest, 0)
        poItemDestVal = self.ui.poTableWidget.item(lRowDest, 2)
        poComboBoxDest = self.ui.poTableWidget.cellWidget(lRowDest, 1)

        if not poItemDestReg or not poItemDestVal or not poComboBoxDest:
            return False

        poItemDestReg.setText(poItemSourceReg.text())
        poItemDestVal.setText(poItemSourceVal.text())
        poComboBoxDest.setCurrentIndex(poComboBoxSource.currentIndex())

        return True
    
    # void vClearPrgTableRow (int lRow);
    def vClearPrgTableRow(self, lRow : int):
        logging.debug("SDC_DlgControl::vClearPrgTableRow")
        poItemReg = self.ui.poTableWidget.item(lRow, 0)
        if poItemReg:
            poItemReg.setText("")

        poComboBox = self.ui.poTableWidget.cellWidget(lRow, 1)
        if poComboBox:
            poComboBox.setCurrentIndex(0)

        poItemVal = self.ui.poTableWidget.item(lRow, 2)
        if poItemVal:
            poItemVal.setText("")

    # void vMoveSelectedRows (int lDestRow, bool bCopy);
    def vMoveSelectedRows(self, lDestRow : int, bCopy : bool):
        logging.debug("SDC_DlgControl::vMoveSelectedRows")
        
        vsRegs = []
        vsValues = []
        vlComboBoxIndexes = []

        for lIdx in range(len(self.m_vlSelectedRows)):
            poItemReg   = self.ui.poTableWidget.item(self.m_vlSelectedRows[lIdx], 0)
            poItemValue = self.ui.poTableWidget.item(self.m_vlSelectedRows[lIdx], 2)
            poComboBox = self.ui.poTableWidget.cellWidget(self.m_vlSelectedRows[lIdx], 1)

            if poItemReg and poItemValue and poComboBox:
                vsRegs.append(poItemReg.text())
                vsValues.append(poItemValue.text())
                vlComboBoxIndexes.append(poComboBox.currentIndex())

        for lIdx in range(len(vsRegs)):
            self.ui.poTableWidget.item(lDestRow + lIdx, 0).setText(vsRegs[lIdx])
            self.ui.poTableWidget.item(lDestRow + lIdx, 2).setText(vsValues[lIdx])

            poComboBox = self.ui.poTableWidget.cellWidget(lDestRow + lIdx, 1)
            if poComboBox:
                poComboBox.setCurrentIndex(vlComboBoxIndexes[lIdx])

        if not bCopy:
            self.vClearSelectedRows()

    # void vClearSelectedRows ();
    def vClearSelectedRows(self):
        logging.debug("SDC_DlgControl::vClearSelectedRows")
        for lIdx in range(len(self.m_vlSelectedRows)):
            self.vClearPrgTableRow(self.m_vlSelectedRows[lIdx])

        self.ui.poTableWidget.clearSelection()


