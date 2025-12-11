from PyQt5.QtCore import QSettings, QRect, Qt, QDir
from enum import Enum
import logging

# Versioning support using versioneer
import _version
from settings.sdc_coresettings import SDC_CoreSettings

__version__ = _version.get_versions()['version']

COMPANY_NAME = "Spectrum Instrumentation GmbH"
APP_NAME_SHORT = "spc-dds-control"
APP_NAME_LONG = "Spectrum DDS Control"

SETUP_FILE_EXT = "sdc"
SETUP_FILE_VERSION = 1

DEFAULT_CORE_DDS20_CH0 = 0
DEFAULT_CORE_DDS20_CH1 = 20
DEFAULT_CORE_DDS20_CH2 = 21
DEFAULT_CORE_DDS20_CH3 = 22

DEFAULT_CORE_DDS50_CH0 = 0
DEFAULT_CORE_DDS50_CH1 = 47
DEFAULT_CORE_DDS50_CH2 = 48
DEFAULT_CORE_DDS50_CH3 = 49


class SDC_GuiMode:
    MODE = Enum('MODE', ['CTRL', 'PROG'])

    m_eMode : MODE = MODE.CTRL
    m_lWidgetIndex : int = 0
    m_oGeometry : QRect = None
    m_eWindowState : Qt.WindowStates = None

    def __init__(self, eMode : MODE, lWidgetIndex : int):
        logging.debug("SDC_GuiMode::__init__")
        self.m_eMode = eMode
        self.m_lWidgetIndex = lWidgetIndex
        self.m_eWindowState = Qt.WindowNoState
    
    def eGetMode(self) -> MODE:
        logging.debug("SDC_GuiMode::eGetMode")
        return self.m_eMode
    
    def lGetWidgetIndex(self) -> int:
        logging.debug("SDC_GuiMode::lGetWidgetIndex")
        return self.m_lWidgetIndex
    
    def vSetWindowState(self, eWindowState : Qt.WindowStates):
        logging.debug("SDC_GuiMode::vSetWindowState")
        self.m_eWindowState = eWindowState

    def eGetWindowState(self) -> Qt.WindowStates:
        logging.debug("SDC_GuiMode::eGetWindowState")
        return self.m_eWindowState
    
    def vSetGeometry(self, oGeometry : QRect):
        logging.debug("SDC_GuiMode::vSetGeometry")
        self.m_oGeometry = oGeometry

    def oGetGeometry(self) -> QRect:
        logging.debug("SDC_GuiMode::oGetGeometry")
        return self.m_oGeometry


class SDC_Settings:
    MSBOX_TYPE : Enum = Enum('MSBOX_TYPE', ['MSB_INFO', 'MSB_WARNING', 'MSB_ERROR'])

    m_poSettings : 'SDC_Settings' = None
    m_bSaveOnExit : bool = False
    m_bCompactCoreDialogs : bool = False
    m_bShowOnlyDDS : bool = False
    m_lNumShowCores : int = 0

    m_sVersion : str = __version__
    m_sSetupFilePath : str = ""

    m_sSeqFilePath : str = ""
    m_sInternalSetupFilePath : str = "~spcmddscontrol.{}".format(SETUP_FILE_EXT)
    m_sRegisterFilePath : str = ""
    m_vsExamplesFilePaths : list[str] = []
    m_lvpoCoreSettings : dict[int, list[SDC_CoreSettings]] = {}
    m_mepoGuiModes : dict[SDC_GuiMode.MODE, SDC_GuiMode] = {}

    # Singleton function
    def __new__(cls, *args, **kwargs):
        logging.debug("SDC_Settings::__new__")
        if not cls.m_poSettings:
            logging.debug("SDC_Settings::__new__ - creating new instance") # works: this only happens once!
            cls.m_poSettings = super(SDC_Settings, cls).__new__(cls, *args, **kwargs)
            cls.m_poSettings.vInit()
        return cls.m_poSettings
    
    # NOTE: the constructor is also called when __new__ returns an existing instance, hence init code should be in vInit
    def __init__(self):
        logging.debug("SDC_Settings::__init__")
        pass

    def vInit(self):
        logging.debug("SDC_Settings::vInit")
        self.m_bSaveOnExit = True
        self.m_bCompactCoreDialogs = False
        self.m_bShowOnlyDDS = False
        self.m_lNumShowCores = 4

        # create DDS-Control folder in user directory
        oDir = QDir(QDir.home().path())
        if not oDir.exists(QDir.home().path() + "/DDS-Control"):
            oDir.mkdir("DDS-Control")

        # self.m_sVersion = f"{SDC_VER_MAJOR}.{SDC_VER_MINOR} build {SDC_VER_BUILD}"
        self.m_sVersion = f"{__version__}"
        
        self.m_sSetupFilePath = QDir.home().path() + "/DDS-Control/dds_setup." + SETUP_FILE_EXT
        self.m_sSeqFilePath = QDir.home().path() + "/DDS-Control/dds_sequence.csv"

        # create internal setup file path
        self.m_sInternalSetupFilePath = QDir.home().path() + "/DDS-Control/~spcddscontrol." + SETUP_FILE_EXT
        
        self.m_sRegisterFilePath = QDir.currentPath() + "/resources/spc_registerlist.csv"

        self.m_mepoGuiModes[SDC_GuiMode.MODE.CTRL] = SDC_GuiMode(SDC_GuiMode.MODE.CTRL, 0)
        self.m_mepoGuiModes[SDC_GuiMode.MODE.PROG] = SDC_GuiMode(SDC_GuiMode.MODE.PROG, 1)

        self.m_mepoGuiModes[SDC_GuiMode.MODE.CTRL].vSetGeometry(QRect(400, 300, 500, 500))
        self.m_mepoGuiModes[SDC_GuiMode.MODE.PROG].vSetGeometry(QRect(50, 50, 1400, 1000))

        self.m_mepoGuiModes[SDC_GuiMode.MODE.PROG].vSetWindowState(Qt.WindowMaximized)
        
        self.vInitExamples ()
        self.vLoadSettings()

    def __del__(self):
        logging.debug("SDC_Settings::__del__")
        self.vSaveSettings()

    def vLoadSettings(self):
        logging.debug("SDC_Settings::vLoadSettings")
        oSettings = QSettings(COMPANY_NAME, APP_NAME_SHORT)

        if oSettings.contains("SetupFile"):
            self.m_sSetupFilePath = oSettings.value("SetupFile", "", str)
        if oSettings.contains("SeqFile"):
            self.m_sSeqFilePath = oSettings.value("SeqFile", "", str)
        if oSettings.contains("SaveOnExit"):
            self.m_bSaveOnExit = oSettings.value("SaveOnExit", False, bool)
        if oSettings.contains("CompactCoreDialogs"):
            self.m_bCompactCoreDialogs = oSettings.value("CompactCoreDialogs", False, bool)
        if oSettings.contains("ShowOnlyDDS"):
            self.m_bShowOnlyDDS = oSettings.value("ShowOnlyDDS", False, bool)
        if oSettings.contains("NumShowCores"):
            self.m_lNumShowCores = oSettings.value("NumShowCores", 0, int)

    def vSaveSettings(self):
        logging.debug("SDC_Settings::vSaveSettings")
        oSettings = QSettings(COMPANY_NAME, APP_NAME_SHORT)

        oSettings.setValue("SetupFile", self.m_sSetupFilePath)
        oSettings.setValue("SeqFile", self.m_sSeqFilePath)
        oSettings.setValue("SaveOnExit", self.m_bSaveOnExit)
        oSettings.setValue("CompactCoreDialogs", self.m_bCompactCoreDialogs)
        oSettings.setValue("ShowOnlyDDS", self.m_bShowOnlyDDS)
        oSettings.setValue("NumShowCores", self.m_lNumShowCores)
    
    def vInitExamples(self):
        logging.debug("SDC_Settings::vInitExamples")
        oDir = QDir(QDir.currentPath() + "/examples")

        oFilters = ["*.csv"]

        oDir.setNameFilters(oFilters)

        oFileList = oDir.entryInfoList(QDir.NoDotAndDotDot | QDir.Files)

        for lIdx in range(len(oFileList)):
            self.m_vsExamplesFilePaths.append(oFileList[lIdx].absoluteFilePath())
    

    # static SDC_Settings* poGetInstance ();
    # NOTE the singleton instance is created in __new__
    @staticmethod
    def poGetInstance() -> 'SDC_Settings':
        logging.debug("SDC_Settings::poGetInstance")
        return SDC_Settings()

    # static void vDestroy ();
    @classmethod
    def vDestroy(cls):
        logging.debug("SDC_Settings::vDestroy")
        del cls.m_poSettings

    # QString sGetAppTitle ();
    def sGetAppTitle(self) -> str:
        logging.debug("SDC_Settings::sGetAppTitle")
        sAppTitle = f"{APP_NAME_LONG} v{self.m_sVersion}"
        return sAppTitle

    # void vSetSetupFilePath (const QString& sFilePath) { m_sSetupFilePath = sFilePath; }
    def vSetSetupFilePath(self, sFilePath : str):
        logging.debug("SDC_Settings::vSetSetupFilePath")
        self.m_sSetupFilePath = sFilePath

    # QString sGetSetupFilePath () const { return m_sSetupFilePath; }
    def sGetSetupFilePath(self) -> str:
        logging.debug("SDC_Settings::sGetSetupFilePath")
        return self.m_sSetupFilePath

    # void vSetSeqFilePath (const QString& sFilePath) { m_sSeqFilePath = sFilePath; }
    def vSetSeqFilePath(self, sFilePath : str):
        logging.debug("SDC_Settings::vSetSeqFilePath")
        self.m_sSeqFilePath = sFilePath

    # QString sGetSeqFilePath () const { return m_sSeqFilePath; }
    def sGetSeqFilePath(self) -> str:
        logging.debug("SDC_Settings::sGetSeqFilePath")
        return self.m_sSeqFilePath

    # QString sGetInternalSetupFilePath () const { return m_sInternalSetupFilePath; }
    def sGetInternalSetupFilePath(self):
        logging.debug("SDC_Settings::sGetInternalSetupFilePath")
        return self.m_sInternalSetupFilePath

    # QString sGetRegisterFilePath () const { return m_sRegisterFilePath; }
    def sGetRegisterFilePath(self) -> str:
        logging.debug("SDC_Settings::sGetRegisterFilePath")
        return self.m_sRegisterFilePath

    # void vSetSaveOnExit (bool bState) { m_bSaveOnExit = bState; }
    def vSetSaveOnExit(self, bState : bool):
        logging.debug("SDC_Settings::vSetSaveOnExit({})".format(bState))
        self.m_bSaveOnExit = bState

    # bool bSaveOnExit () const { return m_bSaveOnExit; }
    def bSaveOnExit(self) -> bool:
        logging.debug("SDC_Settings::bSaveOnExit -> {}".format(self.m_bSaveOnExit))
        return self.m_bSaveOnExit

    # void vSetCompactCoreDialogs (bool bState) { m_bCompactCoreDialogs = bState; }
    def vSetCompactCoreDialogs(self, bState : bool):
        logging.debug("SDC_Settings::vSetCompactCoreDialogs({})".format(bState))
        self.m_bCompactCoreDialogs = bState

    # bool bCompactCoreDialogs () { return m_bCompactCoreDialogs; }
    def bCompactCoreDialogs(self) -> bool:
        logging.debug("SDC_Settings::bCompactCoreDialogs")
        return self.m_bCompactCoreDialogs
    
    # void vSetShowOnlyDDS (bool bState) { m_bShowOnlyDDS = bState; }
    def vSetShowOnlyDDS(self, bState : bool):
        logging.debug("SDC_Settings::vSetShowOnlyDDS({})".format(bState))
        self.m_bShowOnlyDDS = bState
    # bool bShowOnlyDDS () { return m_bShowOnlyDDS; }
    def bShowOnlyDDS(self) -> bool:
        logging.debug("SDC_Settings::bShowOnlyDDS")
        return self.m_bShowOnlyDDS

    # void vSetNumShowCores (int lNumShowCores) { m_lNumShowCores = lNumShowCores; }
    def vSetNumShowCores(self, lNumShowCores : int):
        logging.debug("SDC_Settings::vSetNumShowCores({})".format(lNumShowCores))
        self.m_lNumShowCores = lNumShowCores

    # int lGetNumShowCores () { return m_lNumShowCores; }
    def lGetNumShowCores(self) -> int:
        logging.debug("SDC_Settings::lGetNumShowCores")
        return self.m_lNumShowCores

    # void vAddCoreSetting (int lSerialNumber, SDC_CoreSettings* poCoreSetting);
    def vAddCoreSetting(self, lSerialNumber : int, poCoreSetting : SDC_CoreSettings):
        logging.debug("SDC_Settings::vAddCoreSetting")
        if not (lSerialNumber in self.m_lvpoCoreSettings):
            self.m_lvpoCoreSettings[lSerialNumber] = []
        self.m_lvpoCoreSettings[lSerialNumber].append(poCoreSetting)

    # void vRemoveSetting  (int lSerialNumber, int lSetupID);
    def vRemoveSetting(self, lSerialNumber : int, lSetupID : int):
        logging.debug("SDC_Settings::vRemoveSetting")
        if lSerialNumber in self.m_lvpoCoreSettings:
            for lIdx in range(len(self.m_lvpoCoreSettings[lSerialNumber])):
                if self.m_lvpoCoreSettings[lSerialNumber][lIdx].lGetSetupID() == lSetupID:
                    self.m_lvpoCoreSettings[lSerialNumber].pop(lIdx)

    # SDC_CoreSettings* poGetCoreSetting (int lSerialNumber, int lSetupID);
    def poGetCoreSetting(self, lSerialNumber : int, lSetupID : int) -> SDC_CoreSettings:
        logging.debug("SDC_Settings::poGetCoreSetting")
        if lSerialNumber in self.m_lvpoCoreSettings:
            for lIdx in range(len(self.m_lvpoCoreSettings[lSerialNumber])):
                if self.m_lvpoCoreSettings[lSerialNumber][lIdx].lGetSetupID() == lSetupID:
                    return self.m_lvpoCoreSettings[lSerialNumber][lIdx]

        return None

    # int lGetNumCoreSettings (int lSerialNumber);
    def lGetNumCoreSettings(self, lSerialNumber : int) -> int:
        logging.debug("SDC_Settings::lGetNumCoreSettings")
        if lSerialNumber in self.m_lvpoCoreSettings:
            return len(self.m_lvpoCoreSettings[lSerialNumber])

        return 0

    # void vDebugPlotCoreSettings ();
    lCnt = 0 # static variable for counting calls
    def vDebugPlotCoreSettings(self):
        logging.debug("SDC_Settings::vDebugPlotCoreSettings")

        logging.debug("")
        logging.debug(f"***** {self.lCnt} *****")
        logging.debug("")

        for lSerialNumber, vCoreSettings in self.m_lvpoCoreSettings.items():
            for lIdx in range(len(vCoreSettings)):
                logging.debug("[{}][{}]".format(lSerialNumber, lIdx))
                logging.debug("  SetupID: {}".format(vCoreSettings[lIdx].lGetSetupID()))
                logging.debug("  CoreNum: {}".format(vCoreSettings[lIdx].lGetCoreNum()))
                logging.debug("    ChNum: {}".format(vCoreSettings[lIdx].lGetChNum()))
                logging.debug("     Ampl: {}".format(vCoreSettings[lIdx].oGetAmplitude().dGetValue()))
                logging.debug("     Freq: {}".format(vCoreSettings[lIdx].oGetFrequency().dGetValue()))
                logging.debug("    Phase: {}".format(vCoreSettings[lIdx].oGetPhase().dGetValue()))
        self.lCnt += 1

    # SDC_GuiMode* poGetGuiMode (SDC_GuiMode::MODE eMode);
    def poGetGuiMode(self, eMode : SDC_GuiMode.MODE) -> SDC_GuiMode:
        logging.debug("SDC_Settings::poGetGuiMode")
        if eMode in self.m_mepoGuiModes:
            return self.m_mepoGuiModes[eMode]

        return None

    # void vSaveCoreSettings (QSettings *poSettings);
    def vSaveCoreSettings(self, poSettings : QSettings):
        logging.debug("SDC_Settings::vSaveCoreSettings")
        lSetupIdx = 0

        poSettings.setValue("NumSetups", len(self.m_lvpoCoreSettings))

        for lSerialNumber, vCoreSettings in self.m_lvpoCoreSettings.items():
            poSettings.beginGroup(f"Setup{lSetupIdx}")
            poSettings.setValue("SN", lSerialNumber)
            poSettings.setValue("NumCores", len(vCoreSettings))

            for lCoreIdx in range(len(vCoreSettings)):
                poSettings.beginGroup(f"Core{lCoreIdx}")
                poSettings.setValue("SetupID", vCoreSettings[lCoreIdx].lGetSetupID())
                poSettings.setValue("CoreNum", vCoreSettings[lCoreIdx].lGetCoreNum())
                poSettings.setValue("ChNum", vCoreSettings[lCoreIdx].lGetChNum())
                poSettings.setValue("Ampl", vCoreSettings[lCoreIdx].oGetAmplitude().dGetValue())
                poSettings.setValue("Freq", vCoreSettings[lCoreIdx].oGetFrequency().dGetValue())
                poSettings.setValue("Phase", vCoreSettings[lCoreIdx].oGetPhase().dGetValue())
                poSettings.endGroup()

            poSettings.endGroup()
            lSetupIdx += 1

    # void vLoadCoreSettings (QSettings* poSettings);
    def vLoadCoreSettings(self, poSettings : QSettings):
        logging.debug("SDC_Settings::vLoadCoreSettings")
        lNumSetup = poSettings.value("NumSetups", 0, int)

        for lSetupIdx in range(lNumSetup):
            poSettings.beginGroup("Setup{}".format(lSetupIdx))
            lSN = poSettings.value("SN", 0, int)
            if lSN > 0:
                if not (lSN in self.m_lvpoCoreSettings):
                    self.m_lvpoCoreSettings[lSN] = []
                
                lNumCores = poSettings.value("NumCores", 0, int)

                for lCoreIdx in range(lNumCores):
                    while len(self.m_lvpoCoreSettings[lSN]) <= lCoreIdx:
                        self.m_lvpoCoreSettings[lSN].append(SDC_CoreSettings())

                    poSettings.beginGroup("Core{}".format(lCoreIdx))
                    self.m_lvpoCoreSettings[lSN][lCoreIdx].vSetSetupID(poSettings.value("SetupID", -1, int))
                    self.m_lvpoCoreSettings[lSN][lCoreIdx].vSetCoreNum(poSettings.value("CoreNum", -1, int))
                    self.m_lvpoCoreSettings[lSN][lCoreIdx].vSetChNum(poSettings.value("ChNum", -1, int))
                    self.m_lvpoCoreSettings[lSN][lCoreIdx].vSetAmplitude(poSettings.value("Ampl", 0, float))
                    self.m_lvpoCoreSettings[lSN][lCoreIdx].vSetFrequency(poSettings.value("Freq", 0, float))
                    self.m_lvpoCoreSettings[lSN][lCoreIdx].vSetPhase(poSettings.value("Phase", 0, float))
                    poSettings.endGroup()

            poSettings.endGroup()

    # QVector <QString> vsGetExamplesPaths () { return m_vsExamplesFilePaths; }
    def vsGetExamplesPaths(self) -> list[str]:
        logging.debug("SDC_Settings::vsGetExamplesPaths")
        return self.m_vsExamplesFilePaths

