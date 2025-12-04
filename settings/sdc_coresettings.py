#include "sdc_coresettings.h"
import logging

class SDC_Value:
    m_dMin : float = 0
    m_dMax : float = 0
    m_dStep : float = 0
    m_dValue : float = 0

    # DONE
    def __init__(self):
        logging.debug("SDC_Value::__init__")
        self.m_dMin = 0
        self.m_dMax = 0
        self.m_dStep = 0
        self.m_dValue = 0

    # DONE
    def vSetLimits(self, dMin, dMax, dStep):
        logging.debug("SDC_Value::vSetLimits")
        self.m_dMin = dMin
        self.m_dMax = dMax
        self.m_dStep = dStep

    def vSetMin(self, dMin):
        logging.debug("SDC_Value::vSetMin")
        self.m_dMin = dMin
    def dGetMin(self) -> float:
        logging.debug("SDC_Value::dGetMin")
        return self.m_dMin

    def vSetMax(self, dMax):
        logging.debug("SDC_Value::vSetMax")
        self.m_dMax = dMax
    def dGetMax(self) -> float:
        logging.debug("SDC_Value::dGetMax")
        return self.m_dMax

    def vSetStep(self, dStep):
        logging.debug("SDC_Value::vSetStep")
        self.m_dStep = dStep
    def dGetStep(self) -> float: 
        logging.debug("SDC_Value::dGetStep")
        return self.m_dStep

    def vSetValue(self, dValue):
        logging.debug("SDC_Value::vSetValue")
        self.m_dValue = dValue
    def dGetValue(self) -> float:
        logging.debug("SDC_Value::dGetValue")
        return self.m_dValue

class SDC_CoreSettings:
    m_bDDS50 : bool = False
    m_bLimitsSet : bool = False
    m_lSetupID : int = -1
    m_lCoreNum : int = -1
    m_lChNum : int = 0
    m_oAmplitude : SDC_Value = None
    m_oFrequency : SDC_Value = None
    m_oPhase : SDC_Value = None


    # DONE
    def __init__(self, lSetupID : int = -1, lCoreNum : int = -1, lChNum : int = -1, bDDS50 : bool = False):
        logging.debug("SDC_CoreSettings::__init__")
        self.m_lSetupID = lSetupID
        self.m_lCoreNum = lCoreNum
        self.m_lChNum = lChNum
        self.m_bDDS50 = bDDS50
        self.m_bLimitsSet = False
        self.m_oAmplitude = SDC_Value()
        self.m_oFrequency = SDC_Value()
        self.m_oPhase = SDC_Value()

    # DONE
    def vSetSetupID(self, lSetupID : int):
        logging.debug("SDC_CoreSettings::vSetSetupID")
        self.m_lSetupID = lSetupID
    # DONE
    def lGetSetupID(self) -> int:
        logging.debug("SDC_CoreSettings::lGetSetupID")
        return self.m_lSetupID

    # DONE
    def vSetCoreNum(self, lCoreNum : int):
        logging.debug("SDC_CoreSettings::vSetCoreNum")
        self.m_lCoreNum = lCoreNum
    # DONE
    def lGetCoreNum(self) -> int:
        logging.debug("SDC_CoreSettings::lGetCoreNum")
        return self.m_lCoreNum

    # DONE
    def vSetChNum(self, lChNum : int):
        logging.debug("SDC_CoreSettings::vSetChNum")
        self.m_lChNum = lChNum
    # DONE
    def lGetChNum(self) -> int:
        logging.debug("SDC_CoreSettings::lGetChNum")
        return self.m_lChNum

    # DONE
    def vSetAmplitude(self, oAmplitude : SDC_Value):
        logging.debug("SDC_CoreSettings::vSetAmplitude")
        if isinstance(oAmplitude, SDC_Value):
            self.m_oAmplitude = oAmplitude
        elif isinstance(oAmplitude, float):
            self.m_oAmplitude.vSetValue(oAmplitude)
    # DONE   
    def oGetAmplitude(self) -> SDC_Value:
        logging.debug("SDC_CoreSettings::oGetAmplitude")
        return self.m_oAmplitude

    # DONE
    def vSetFrequency(self, oFrequency : SDC_Value):
        logging.debug("SDC_CoreSettings::vSetFrequency")
        if isinstance(oFrequency, SDC_Value):
            self.m_oFrequency = oFrequency
        elif isinstance(oFrequency, float):
            self.m_oFrequency.vSetValue(oFrequency)
    # DONE
    def oGetFrequency(self) -> SDC_Value:
        logging.debug("SDC_CoreSettings::oGetFrequency")
        return self.m_oFrequency
    
    # DONE
    def vSetPhase(self, oPhase : SDC_Value):
        logging.debug("SDC_CoreSettings::vSetPhase")
        if isinstance(oPhase, SDC_Value):
            self.m_oPhase = oPhase
        elif isinstance(oPhase, float):
            self.m_oPhase.vSetValue(oPhase)
    # DONE
    def oGetPhase(self):
        logging.debug("SDC_CoreSettings::oGetPhase")
        return self.m_oPhase

    # DONE
    def vSetAmplitude(self, dAmplitude : float):
        logging.debug("SDC_CoreSettings::vSetAmplitude")
        self.m_oAmplitude.vSetValue(dAmplitude)
    
    # void vSetFrequency (double dFrequency) { m_oFrequency.vSetValue (dFrequency); }
    # DONE
    def vSetFrequency(self, dFrequency : float):
        logging.debug("SDC_CoreSettings::vSetFrequency")
        self.m_oFrequency.vSetValue(dFrequency)

    # void vSetPhase     (double dPhase)     { m_oPhase.vSetValue (dPhase);         }
    # DONE
    def vSetPhase(self, dPhase : float):
        logging.debug("SDC_CoreSettings::vSetPhase")
        self.m_oPhase.vSetValue(dPhase)

    # void vSetAmplitudeLimits (double dMin, double dMax, double dStep) { m_oAmplitude.vSetLimits (dMin, dMax, dStep); }
    # DONE
    def vSetAmplitudeLimits(self, dMin : float, dMax : float, dStep : float):
        logging.debug("SDC_CoreSettings::vSetAmplitudeLimits")
        self.m_oAmplitude.vSetLimits(dMin, dMax, dStep)

    # void vSetFrequencyLimits (double dMin, double dMax, double dStep) { m_oFrequency.vSetLimits (dMin, dMax, dStep); }
    # DONE
    def vSetFrequencyLimits(self, dMin : float, dMax : float, dStep : float):
        logging.debug("SDC_CoreSettings::vSetFrequencyLimits")
        self.m_oFrequency.vSetLimits(dMin, dMax, dStep)

    # void vSetPhaseLimits     (double dMin, double dMax, double dStep) { m_oPhase.vSetLimits (dMin, dMax, dStep); }
    # DONE
    def vSetPhaseLimits(self, dMin : float, dMax : float, dStep : float):
        logging.debug("SDC_CoreSettings::vSetPhaseLimits")
        self.m_oPhase.vSetLimits(dMin, dMax, dStep)

    # void vSetLimitsSet (bool bState) { m_bLimitsSet = bState; }
    # DONE
    def vSetLimitsSet(self, bState : bool):
        logging.debug("SDC_CoreSettings::vSetLimitsSet")
        self.m_bLimitsSet = bState

    # bool bLimitsSet () { return m_bLimitsSet; }
    # DONE
    def bLimitsSet(self) -> bool:
        logging.debug("SDC_CoreSettings::bLimitsSet")
        return self.m_bLimitsSet

    # DONE
    def mlsGetAllowedChannels(self, lCoreNum : int) -> dict:
        logging.debug("SDC_CoreSettings::mlsGetAllowedChannels")
        mlsAllowedChannels = {}
        if self.m_bDDS50:
            mlsAllowedChannels[0] = " Channel 0 "

            if lCoreNum == 47: mlsAllowedChannels[1] = " Channel 1 "
            elif lCoreNum == 48: mlsAllowedChannels[2] = " Channel 2 "
            elif lCoreNum == 49: mlsAllowedChannels[3] = " Channel 3 "
        else:
            if lCoreNum == 20: mlsAllowedChannels[1] = " Channel 1 "
            elif lCoreNum == 21: mlsAllowedChannels[2] = " Channel 2 "
            elif lCoreNum == 22: mlsAllowedChannels[3] = " Channel 3 "
            else: mlsAllowedChannels[0] = " Channel 0 "

            if lCoreNum >= 8 and lCoreNum <= 11:
                mlsAllowedChannels[1] = " Channel 1 "
            
            if lCoreNum >= 12 and lCoreNum <= 15:
                mlsAllowedChannels[2] = " Channel 2 "

            if lCoreNum >= 16 and lCoreNum <= 19:
                mlsAllowedChannels[3] = " Channel 3 "

        return mlsAllowedChannels