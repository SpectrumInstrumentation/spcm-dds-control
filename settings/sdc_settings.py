from PyQt5.QtCore import QSettings
from enum import Enum

# Versioning support using versioneer
import _version
__version__ = _version.get_versions()['version']

COMPANY_NAME = "Spectrum Instrumentation GmbH"
APP_NAME_SHORT = "spc-dds-control"
APP_NAME_LONG = "Spectrum DDS Control"

SETUP_EXT = "sdc"

DEFAULT_CORE_DDS20_CH0 = 0
DEFAULT_CORE_DDS20_CH1 = 20
DEFAULT_CORE_DDS20_CH2 = 21
DEFAULT_CORE_DDS20_CH3 = 22

DEFAULT_CORE_DDS50_CH0 = 0
DEFAULT_CORE_DDS50_CH1 = 47
DEFAULT_CORE_DDS50_CH2 = 48
DEFAULT_CORE_DDS50_CH3 = 49

class SDC_Settings:
    MSBOX_TYPE : Enum = Enum('MSBOX_TYPE', ['MSB_INFO', 'MSB_WARNING', 'MSB_ERROR'])
    _instance : object = None

    m_sSetupFilePath : str = ""
    m_bSaveOnExit : bool = False
    m_sVersion : str = __version__
    m_sInternalSetupFilePath : str = "~spcmddscontrol.{}".format(SETUP_EXT)

    # Singleton function
    def __new__(cls, *args, **kwargs):
        #print("SDC_Settings::__new__")
        if not cls._instance:
            #print("SDC_Settings::__new__ - creating new instance") # works: this only happens once!
            cls._instance = super(SDC_Settings, cls).__new__(cls, *args, **kwargs)
            cls._instance.vLoadSettings()
        return cls._instance
    
    def __init__(self):
        #print("SDC_Settings::__init__")
        pass

    # ********************************************************************************************************
    # ***** Private Destructor
    # ********************************************************************************************************
    def __del__(self):
        #print("SDC_Settings::__del__")
        self.vSaveSettings()

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def vDestroy(self):
        #print("SDC_Settings::vDestroy")
        self._instance = None

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def sGetAppTitle(self) -> str:
        #print("SDC_Settings::sGetAppTitle")
        sAppTitle = f"{APP_NAME_LONG} v{self.m_sVersion}"
        return sAppTitle

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vLoadSettings(self):
        #print("SDC_Settings::vLoadSettings")
        oSettings = QSettings(COMPANY_NAME, APP_NAME_SHORT)

        if oSettings.contains("SetupFile"):
            self.m_sSetupFilePath = oSettings.value("SetupFile", "", str)
        if oSettings.contains("SaveOnExit"):
            self.m_bSaveOnExit = oSettings.value("SaveOnExit", False, bool)

    # ********************************************************************************************************
    # ***** Private Method
    # ********************************************************************************************************
    def vSaveSettings(self):
        #print("SDC_Settings::vSaveSettings")
        oSettings = QSettings(COMPANY_NAME, APP_NAME_SHORT)

        oSettings.setValue("SetupFile", self.m_sSetupFilePath)
        oSettings.setValue("SaveOnExit", self.m_bSaveOnExit)

    
    def vSetSaveOnExit(self, bState : bool):
        #print("SDC_Settings::vSetSaveOnExit({})".format(bState))
        self.m_bSaveOnExit = bState

    def bSaveOnExit(self) -> bool:
        #print("SDC_Settings::bSaveOnExit -> {}".format(self.m_bSaveOnExit))
        return self.m_bSaveOnExit
    
    def vSetSetupFilePath(self, sFilePath : str):
        #print("SDC_Settings::vSetSetupFilePath")
        self.m_sSetupFilePath = sFilePath

    def sGetSetupFilePath(self) -> str:
        #print("SDC_Settings::sGetSetupFilePath")
        return self.m_sSetupFilePath

    def sGetInternalSetupFilePath(self):
        #print("SDC_Settings::sGetInternalSetupFilePath")
        return self.m_sInternalSetupFilePath

    # ********************************************************************************************************
