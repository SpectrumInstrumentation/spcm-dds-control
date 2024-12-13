#include "sdc_coresettings.h"
# from PyQt5.QtCore import QMap

class SDC_Value:
    m_dMin : float = 0
    m_dMax : float = 0
    m_dStep : float = 0
    m_dValue : float = 0

    def __init__(self, dMin : float = 0, dMax : float = 0, dStep : float = 0):
        #print("SDC_Value::__init__")
        self.m_dMin = dMin
        self.m_dMax = dMax
        self.m_dStep = dStep
        self.m_dValue = 0

    def vSetMin(self, dMin):
        #print("SDC_Value::vSetMin")
        self.m_dMin = dMin
    def dGetMin(self) -> float:
        #print("SDC_Value::dGetMin")
        return self.m_dMin

    def vSetMax(self, dMax):
        #print("SDC_Value::vSetMax")
        self.m_dMax = dMax
    def dGetMax(self) -> float:
        #print("SDC_Value::dGetMax")
        return self.m_dMax

    def vSetStep(self, dStep):
        #print("SDC_Value::vSetStep")
        self.m_dStep = dStep
    def dGetStep(self) -> float: 
        #print("SDC_Value::dGetStep")
        return self.m_dStep

    def vSetValue(self, dValue):
        #print("SDC_Value::vSetValue")
        self.m_dValue = dValue
    def dGetValue(self) -> float:
        #print("SDC_Value::dGetValue")
        return self.m_dValue

class SDC_CoreSettings:
    m_oAmplitude : SDC_Value = None
    m_oFrequency : SDC_Value = None
    m_oPhase : SDC_Value = None
    m_lCoreIndex : int = -1
    m_lChannel : int = 0
    m_bDDS50 : bool = False

    # ********************************************************************************************************
    # ***** Public Constructor : Class SDC_CoreSettings
    # ********************************************************************************************************
    def __init__(self, lCoreIndex : int = -1, bDDS50 : bool = False):
        #print("SDC_CoreSettings::__init__")
        self.m_lCoreIndex = lCoreIndex
        self.m_bDDS50 = bDDS50
        self.vSetAmplitude(SDC_Value())
        self.vSetFrequency(SDC_Value())
        self.vSetPhase(SDC_Value())

    def vSetCoreIndex(self, lIndex : int):
        #print("SDC_CoreSettings::vSetCoreIndex")
        self.m_lCoreIndex = lIndex
    def lGetCoreIndex(self) -> int:
        #print("SDC_CoreSettings::lGetCoreIndex")
        return self.m_lCoreIndex

    def vSetChannel(self, lChannel : int):
        #print("SDC_CoreSettings::vSetChannel")
        self.m_lChannel = lChannel
    def lGetChannel(self) -> int:
        #print("SDC_CoreSettings::lGetChannel")
        return self.m_lChannel

    def vSetAmplitude(self, amplitude):
        #print("SDC_CoreSettings::vSetAmplitude")
        if isinstance(amplitude, SDC_Value):
            self.m_oAmplitude = amplitude
        elif isinstance(amplitude, float):
            self.m_oAmplitude.vSetValue(amplitude)
    def oGetAmplitude(self):
        #print("SDC_CoreSettings::oGetAmplitude")
        return self.m_oAmplitude

    def vSetFrequency(self, frequency):
        #print("SDC_CoreSettings::vSetFrequency")
        if isinstance(frequency, SDC_Value):
            self.m_oFrequency = frequency
        elif isinstance(frequency, float):
            self.m_oFrequency.vSetValue(frequency)
    def oGetFrequency(self):
        #print("SDC_CoreSettings::oGetFrequency")
        return self.m_oFrequency
    
    def vSetPhase(self, phase):
        #print("SDC_CoreSettings::vSetPhase")
        if isinstance(phase, SDC_Value):
            self.m_oPhase = phase
        elif isinstance(phase, float):
            self.m_oPhase.vSetValue(phase)
    def oGetPhase(self):
        #print("SDC_CoreSettings::oGetPhase")
        return self.m_oPhase

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def mlsGetAllowedChannels(self, lCoreNum : int):
        #print("SDC_CoreSettings::mlsGetAllowedChannels")
        mlsAllowedChannels = {}
        if self.m_bDDS50:
            mlsAllowedChannels[0] = " Channel 0 "

            if lCoreNum == 47:
                mlsAllowedChannels[1] = " Channel 1 "
            elif lCoreNum == 48:
                mlsAllowedChannels[2] = " Channel 2 "
            elif lCoreNum == 49:
                mlsAllowedChannels[3] = " Channel 3 "
        else:
            if lCoreNum == 20:
                mlsAllowedChannels[1] = " Channel 1 "
            elif lCoreNum == 21: 
                mlsAllowedChannels[2] = " Channel 2 "
            elif lCoreNum == 22: 
                mlsAllowedChannels[3] = " Channel 3 "
            else:
                mlsAllowedChannels[0] = " Channel 0 "

            if lCoreNum >= 8 and lCoreNum <= 11:
                mlsAllowedChannels[1] = " Channel 1 "
            
            if lCoreNum >= 12 and lCoreNum <= 15:
                mlsAllowedChannels[2] = " Channel 2 "

            if lCoreNum >= 16 and lCoreNum <= 19:
                mlsAllowedChannels[3] = " Channel 3 "

        return mlsAllowedChannels