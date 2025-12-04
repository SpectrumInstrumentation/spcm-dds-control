import logging
from spcm_core import *
from enum import Enum, auto

from PyQt5.QtCore import QVariant, qDebug


class SDC_SpcDevChSetting:
    m_lMaxOutputRange_mV : int = 0
    m_lOutputEnabled : int = 0
    m_lOutputRange_mV : int = 0
    m_lFilter : int = 0

    # DONE
    def __init__(self, lMaxOutputRange_mV : int = 1000):
        logging.debug("SDC_SpcDevChSetting::__init__")
        self.m_lMaxOutputRange_mV = lMaxOutputRange_mV
        self.m_lOutputEnabled = 1
        self.m_lOutputRange_mV = 1000
        self.m_lFilter = 0

        if self.m_lOutputRange_mV > lMaxOutputRange_mV:
            self.m_lOutputRange_mV = lMaxOutputRange_mV
        
    def vSetOutputEnabled(self, lValue : int):
        logging.debug("SDC_SpcDevChSetting::vSetOutputEnabled")
        self.m_lOutputEnabled = lValue

    def lOutputEnabled(self) -> int:
        logging.debug("SDC_SpcDevChSetting::lOutputEnabled")
        return self.m_lOutputEnabled

    def vSetOutputRange_mV(self, lValue : int):
        logging.debug("SDC_SpcDevChSetting::vSetOutputRange_mV")
        self.m_lOutputRange_mV = lValue

    def lGetOutputRange_mV(self) -> int:
        logging.debug("SDC_SpcDevChSetting::lGetOutputRange_mV")
        return self.m_lOutputRange_mV

    def vSetFilter(self, lValue : int):
        logging.debug("SDC_SpcDevChSetting::vSetFilter")
        self.m_lFilter = lValue

    def lGetFilter(self) -> int:
        logging.debug("SDC_SpcDevChSetting::lGetFilter")
        return self.m_lFilter
    
    # DONE
    def vSetMaxOutputRange_mV(self, lValue : int):
        logging.debug("SDC_SpcDevChSetting::vSetMaxOutputRange_mV")
        self.m_lMaxOutputRange_mV = lValue
    
    # DONE
    def lGetMaxOutputRange_mV(self) -> int:
        logging.debug("SDC_SpcDevChSetting::lGetMaxOutputRange_mV")
        return self.m_lMaxOutputRange_mV



class SDC_SpcDevice:
    class SETTING_TYPE(Enum):
        AMPLITUDE = auto()
        FREQUENCY = auto()
        PHASE = auto()

    m_hDevice : object = None

    m_bRemote : bool = False
    m_bIsDDS50 : bool = False
    m_bDevIsRunning : bool = False

    m_lCardType : int = 0
    m_lSN : int = 0
    m_lMaxChannels : int = 0
    m_lMaxCores : int = 0
    m_dDefaultAmplitude : float = 1.0
    m_dDefaultFrequency : float = 1e6
    m_dDefaultPhase : float = 0.0

    m_sDeviceName : str = ""
    m_msoGeneralSettings : dict[str, QVariant] = {}
    m_loChannelSettings : list[SDC_SpcDevChSetting] = []
    m_memInitCoreValues : dict[SETTING_TYPE, dict[int, float]] = {}

    # DONE
    def __init__(self, hDevice, bRemote : bool = False):
        logging.debug("SDC_SpcDevice::__init__")
        self.m_hDevice = hDevice
        self.m_bRemote = bRemote
        self.m_bIsDDS50 = False
        self.m_bDevIsRunning = False
        self.m_dDefaultAmplitude = 0.2
        self.m_dDefaultFrequency = 5000000
        self.m_dDefaultPhase = 0

        self.m_lSN = c_int(0)
        self.m_lMaxChannels = c_int(0)
        self.m_lMaxCores = c_int(0)
        
        acCardType = create_string_buffer(20)
        spcm_dwGetParam_ptr (self.m_hDevice, SPC_PCITYP, acCardType, sizeof(acCardType));

        lCardType = c_int(0)
        lSN = c_int(0)
        lMaxChannels = c_int(0)
        lModulesCount = c_int(0)
        lExtFeatureMask = c_int(0)
        lGainMax = c_int(0)

        spcm_dwGetParam_i32(self.m_hDevice, SPC_PCITYP, byref(lCardType))
        self.m_lCardType = lCardType.value
        spcm_dwGetParam_i32(self.m_hDevice, SPC_PCISERIALNO, byref(lSN))
        self.m_lSN = lSN.value
        spcm_dwGetParam_i32(self.m_hDevice, SPC_MIINST_MODULES, byref(lModulesCount))
        spcm_dwGetParam_i32(self.m_hDevice, SPC_MIINST_CHPERMODULE, byref(lMaxChannels))
        self.m_lMaxChannels = lMaxChannels.value * lModulesCount.value
        spcm_dwGetParam_i32(self.m_hDevice, SPC_READAOGAINMAX, byref(lGainMax))
        spcm_dwGetParam_i32(self.m_hDevice, SPC_PCIEXTFEATURES, byref(lExtFeatureMask))

        if lExtFeatureMask.value & SPCM_FEAT_EXTFW_DDS50:
            self.m_bIsDDS50 = True

        self.m_sDeviceName = str(acCardType.value.decode('utf-8')) + " SN: {}".format(self.m_lSN)
        if self.m_bRemote:
            self.m_sDeviceName += " (Remote)"

        for _ in range(self.m_lMaxChannels):
            self.m_loChannelSettings.append(SDC_SpcDevChSetting(lGainMax.value))

    def hDevice(self):
        logging.debug("SDC_SpcDevice::hDevice")
        return self.m_hDevice

    def bIsDDS50(self) -> bool:
        logging.debug("SDC_SpcDevice::bIsDDS50")
        return self.m_bIsDDS50

    def sGetDeviceName(self) -> str:
        logging.debug("SDC_SpcDevice::sGetDeviceName")
        return self.m_sDeviceName

    # DONE
    def lGetCardFamily(self) -> int:
        logging.debug("SDC_SpcDevice::lGetCardFamily")
        return ((TYP_SERIESMASK | TYP_FAMILYMASK) & self.m_lCardType)

    # DONE
    def lGetCardType(self) -> int:
        logging.debug("SDC_SpcDevice::lGetCardType")
        return self.m_lCardType
    
    # DONE
    def lGetSerialNumber(self) -> int:
        logging.debug("SDC_SpcDevice::lGetSerialNumber")
        return self.m_lSN

    def lGetNumMaxChannels(self) -> int:
        logging.debug("SDC_SpcDevice::lGetNumMaxChannels")
        return self.m_lMaxChannels
    
    # DONE
    def lGetMaxCores(self) -> int:
        logging.debug("SDC_SpcDevice::lGetMaxCores")
        return self.m_lMaxCores
    
    # DONE
    def dGetInitCoreValue(self, eType : SETTING_TYPE, lCoreNum : int) -> float:
        logging.debug("SDC_SpcDevice::dGetInitCoreValue")
        if eType in self.m_memInitCoreValues and lCoreNum in self.m_memInitCoreValues[eType]:
            return self.m_memInitCoreValues[eType][lCoreNum]

        if eType == self.SETTING_TYPE.AMPLITUDE:
            return self.m_dDefaultAmplitude
        elif eType == self.SETTING_TYPE.FREQUENCY:
            return self.m_dDefaultFrequency
        elif eType == self.SETTING_TYPE.PHASE:
            return self.m_dDefaultPhase
        else:
            return 0
    
    # DONE
    def vSetGeneralSettings(self, sKey : str, oValue):
        logging.debug("SDC_SpcDevice::vSetGeneralSettings")
        self.m_msoGeneralSettings[sKey] = oValue

    # DONE
    def oGetGeneralSettings(self, sKey : str):
        logging.debug("SDC_SpcDevice::oGetGeneralSettings")
        if sKey in self.m_msoGeneralSettings:
            return self.m_msoGeneralSettings[sKey]

        return QVariant()
    
    def vSetChSettings(self, lChIdx : int, oSetting):
        logging.debug("SDC_SpcDevice::vSetChSettings")
        if lChIdx < len(self.m_loChannelSettings):
            self.m_loChannelSettings[lChIdx] = oSetting

    def oGetChSettings(self, lChIdx : int): # -> SDC_SpcDevChSetting:
        logging.debug("SDC_SpcDevice::oGetChSettings")
        if lChIdx < len(self.m_loChannelSettings):
            return self.m_loChannelSettings[lChIdx]

        return SDC_SpcDevChSetting(0)
    
    # DONE
    # Needs to be overridden in derived classes
    def lGetCoresPerChannel(self, lNumActiveChannels : int, lSRate_MS : int = 0) -> int:
        logging.debug("SDC_SpcDevice::lGetCoresPerChannel")
        return 0
    
    # DONE
    def vSetDevIsRunning(self, bState : bool):
        logging.debug("SDC_SpcDevice::vSetDevIsRunning")
        self.m_bDevIsRunning = bState

    #DONE
    def bIsDevRunning(self) -> bool:
        logging.debug("SDC_SpcDevice::bIsDevRunning")
        return self.m_bDevIsRunning
    

class SDC_SpcDevM2p65xx(SDC_SpcDevice):
    # DONE
    def __init__(self, oDevice, bRemote : bool = False):
        logging.debug("SDC_SpcDevM2p65xx::__init__")
        super().__init__(oDevice, bRemote)
        self.m_lMaxCores = 16
        self.m_dDefaultAmplitude = 0

        self.m_memInitCoreValues[self.SETTING_TYPE.AMPLITUDE][0] = 0.1
        self.m_memInitCoreValues[self.SETTING_TYPE.FREQUENCY][0] = 5000000
    

class SDC_SpcDevM4i66xx(SDC_SpcDevice):
    # DONE
    def __init__(self, oDevice, bRemote : bool = False):
        logging.debug("SDC_SpcDevM4i66xx::__init__")
        super().__init__(oDevice, bRemote)
        self.m_lMaxCores = 20


class SDC_SpcDevM4i96xx(SDC_SpcDevice):
    # DONE
    def __init__(self, oDevice, bRemote : bool = False):
        logging.debug("SDC_SpcDevM4i96xx::__init__")
        super().__init__(oDevice, bRemote)
        self.m_lMaxCores = 50
    

class SDC_SpcDevM5i63xx(SDC_SpcDevice):
    # DONE
    def __init__(self, oDevice, bRemote : bool = False):
        logging.debug("SDC_SpcDevM5i63xx::__init__")
        super().__init__(oDevice, bRemote)
        self.m_lMaxCores = 64
        self.m_dDefaultAmplitude = 0

        self.m_memInitCoreValues[self.SETTING_TYPE.AMPLITUDE][0] = 0.1
        self.m_memInitCoreValues[self.SETTING_TYPE.AMPLITUDE][1] = 0.1

        self.m_memInitCoreValues[self.SETTING_TYPE.FREQUENCY][0] = 5000000
        self.m_memInitCoreValues[self.SETTING_TYPE.FREQUENCY][1] = 10000000
    
    # DONE
    def lGetCoresPerChannel(self, lNumActiveChannels, lSRate_MS = 0):
        logging.debug("SDC_SpcDevM5i63xx::lGetCoresPerChannel")
        lCoresPerCh : int = 0

        if lSRate_MS == 2500:
            lCoresPerCh = 32 if lNumActiveChannels > 1 else 64
        elif lSRate_MS == 5000:
            lCoresPerCh = 16 if lNumActiveChannels > 1 else 32
        elif lSRate_MS == 10000:
            lCoresPerCh = 0 if lNumActiveChannels > 1 else 16

        return lCoresPerCh