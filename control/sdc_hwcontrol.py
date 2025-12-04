import ctypes
import time
from numpy import int32
import logging
from spcm_core import *

from PyQt5.QtCore import QSettings, QThread, QMutex, QWaitCondition, qDebug, pyqtSignal

from settings.sdc_settings import SDC_Settings
from settings.sdc_coresettings import SDC_Value, SDC_CoreSettings
from control.sdc_spcdevice import SDC_SpcDevice, SDC_SpcDevM2p65xx, SDC_SpcDevM4i66xx, SDC_SpcDevM4i96xx, SDC_SpcDevM5i63xx

MAX_SPCM_DEVICES = 16


class SDC_DrvCmd:
    m_lRegister : int = -1
    m_lType : int = -1
    m_oValue : object = None

    # SDC_DrvCmd::SDC_DrvCmd ()
    def __init__(self):
        logging.debug("SDC_DrvCmd::__init__")
        self.m_lRegister = -1
        self.m_lType = -1
        self.m_oValue = None

    # DONE
    def __del__(self):
        logging.debug("SDC_DrvCmd::__del__")

    # DONE
    def vSetRegister(self, lRegister : int):
        logging.debug("SDC_DrvCmd::vSetRegister")
        self.m_lRegister = lRegister
    
    # DONE
    def lGetRegister(self) -> int:
        logging.debug("SDC_DrvCmd::lGetRegister")
        return self.m_lRegister
    
    # DONE
    def vSetValue(self, oValue : object):
        logging.debug("SDC_DrvCmd::vSetValue")
        self.m_oValue = oValue
    
    # DONE
    def oGetValue(self) -> object:
        logging.debug("SDC_DrvCmd::oGetValue")
        return self.m_oValue


class SDC_HwControl():
    m_llConnectionMaskCh0 : int = 0
    m_llConnectionMaskCh1 : int = 0
    m_llConnectionMaskCh2 : int = 0
    m_llConnectionMaskCh3 : int = 0
    m_poDevice : SDC_SpcDevice = None
    m_poSettings : SDC_Settings = None
    m_poHwControlThread : 'SDC_HwControlThread' = None
    m_vpoDevices : list[SDC_SpcDevice] = []
    # m_bHwIsRunning : bool = False

    # DONE
    def __init__(self):
        logging.debug("SDC_HwControl::__init__")
        self.m_poSettings = SDC_Settings.poGetInstance()
        self.m_poDevice = None
        self.m_poHwControlThread = SDC_HwControlThread(self)

        # self.m_bHwIsRunning = False
        self.m_vpoDevices = []

    # DONE
    def __del__(self):
        logging.debug("SDC_HwControl::__del__")
        pass

    # DONE
    def dwOpenHardware(self) -> int:
        logging.debug("SDC_HwControl::dwOpenHardware")

        oSettings = QSettings("Spectrum GmbH", "spcm-driver")
        vsVisaStrings : list[str] = []

        # read remote cards information from registery
        bAbort = False
        for lIdx in range(1, MAX_SPCM_DEVICES + 1):
            if bAbort:
                break
            sRemotePath = "Remote Card # {:02d}/".format(lIdx)
            if oSettings.contains(sRemotePath + "IP"):
                sIP = str(oSettings.value(sRemotePath + "IP"))
                sInst = str(oSettings.value(sRemotePath + "Inst"))
                
                if sIP and sInst:
                    vsVisaStrings.append("TCPIP::" + sIP + "::inst" + sInst + "::INSTR")
            else:
                bAbort = True

        self.m_vpoDevices = []

        # open remote devices
        for sVisaString in vsVisaStrings:
            poDevice = self.poOpenDevice(sVisaString)
            if poDevice:
                self.m_vpoDevices.append(poDevice)

        # open local devices
        bAbort = False
        for dwDevIdx in range(MAX_SPCM_DEVICES):
            if bAbort:
                break
            sDevString = "/dev/spcm{}".format(dwDevIdx)
            poDevice = self.poOpenDevice(sDevString)
            if poDevice:
                self.m_vpoDevices.append(poDevice)

        return len(self.m_vpoDevices)
    
    # DONE
    def vCloseHardware(self):
        logging.debug("SDC_HwControl::vCloseHardware")
        for poDevice in self.m_vpoDevices:
            poDevice.hDevice().close()
            del poDevice
        self.m_vpoDevices = []

    # DONE
    def vSetCurrentDevice(self, dwDevIdx : int):
        logging.debug("SDC_HwControl::vSetCurrentDevice")

        if dwDevIdx < len(self.m_vpoDevices):
            self.m_poDevice = self.m_vpoDevices[dwDevIdx]
        
    # DONE
    def poGetCurrentDevice(self):
        logging.debug("SDC_HwControl::poGetCurrentDevice")
        return self.m_poDevice

    # DONE
    def lGetNumOfDevices(self) -> int:
        logging.debug("SDC_HwControl::lGetNumOfDevices")
        return len(self.m_vpoDevices)

    # DONE
    def poGetDevice(self, dwDevIndex : int): # -> SDC_SpcDevice:
        logging.debug("SDC_HwControl::poGetDevice")
        if dwDevIndex < len(self.m_vpoDevices):
            return self.m_vpoDevices[dwDevIndex]
        raise Exception("Device #{} not found !".format(dwDevIndex))

    # DONE
    def poGetDeviceByeName(self, sName : str): #-> SDC_SpcDevice
        logging.debug("SDC_HwControl::poGetDeviceByeName")
        for device in self.m_vpoDevices:
            if device.sGetDeviceName() == sName:
                return device
        raise Exception("Device {} not found !".format(sName))

    # DONE
    def dwGetCoreInfos(self, poCoreSettings : SDC_CoreSettings):
        logging.debug("SDC_HwControl::dwGetCoreInfos")
        
        dMin, dMax, dStep = double(0), double(0), double(0)
        dwError = 0

        if (not self.m_poDevice or self.m_poDevice.bIsDevRunning ()):
            return dwError

        # we need to write dds command first to read current values for active setup
        dwError = spcm_dwSetParam_i32(self.m_poDevice.hDevice (), SPC_CARDMODE, SPC_REP_STD_DDS)
        if self.m_poDevice.oGetGeneralSettings ("SPC_CHENABLE").isValid ():
            lChEnable = int(self.m_poDevice.oGetGeneralSettings ("SPC_CHENABLE"))
            dwError = spcm_dwSetParam_i32 (self.m_poDevice.hDevice (), SPC_CHENABLE, lChEnable)

        if self.m_poDevice.oGetGeneralSettings ("SPC_SAMPLERATE").isValid ():
            llSamplingrate = int(self.m_poDevice.oGetGeneralSettings ("SPC_SAMPLERATE"))
            dwError = spcm_dwSetParam_i64 (self.m_poDevice.hDevice (), SPC_SAMPLERATE, llSamplingrate)

        dwError = spcm_dwGetParam_d64(self.m_poDevice.hDevice(), SPC_DDS_AVAIL_AMP_MIN,  byref(dMin))
        dwError = spcm_dwGetParam_d64(self.m_poDevice.hDevice(), SPC_DDS_AVAIL_AMP_MAX,  byref(dMax))
        dwError = spcm_dwGetParam_d64(self.m_poDevice.hDevice(), SPC_DDS_AVAIL_AMP_STEP, byref(dStep))
        poCoreSettings.vSetAmplitudeLimits(dMin.value, dMax.value, dStep.value)

        dwError = spcm_dwGetParam_d64(self.m_poDevice.hDevice(), SPC_DDS_AVAIL_FREQ_MIN, byref(dMin))
        dwError = spcm_dwGetParam_d64(self.m_poDevice.hDevice(), SPC_DDS_AVAIL_FREQ_MAX, byref(dMax))
        dwError = spcm_dwGetParam_d64(self.m_poDevice.hDevice(), SPC_DDS_AVAIL_FREQ_STEP, byref(dStep))

        # bug: min wird mit -625 MHz gelesen, richtig wäre >= 0
        dMin.value = 0

        poCoreSettings.vSetFrequencyLimits(dMin.value, dMax.value, dStep.value)

        dwError = spcm_dwGetParam_d64(self.m_poDevice.hDevice (), SPC_DDS_AVAIL_PHASE_MIN, byref(dMin))
        dwError = spcm_dwGetParam_d64(self.m_poDevice.hDevice (), SPC_DDS_AVAIL_PHASE_MAX, byref(dMax))
        dwError = spcm_dwGetParam_d64(self.m_poDevice.hDevice (), SPC_DDS_AVAIL_PHASE_STEP, byref(dStep))

        # Correct min, max for M2p
        if (self.m_poDevice.lGetCardFamily () == TYP_M2P65XX_X4):
            dMin = 0
            dMax = 360

        poCoreSettings.vSetPhaseLimits(dMin.value, dMax.value, dStep.value)

        poCoreSettings.vSetLimitsSet(True)
        return dwError

    # DONE
    def vClearCoreConnectionsMasks(self):
        logging.debug("SDC_HwControl::vClearCoreConnectionsMasks")
        self.m_llConnectionMaskCh0 = self.m_llConnectionMaskCh1 = self.m_llConnectionMaskCh2 = self.m_llConnectionMaskCh3 = 0

    # DONE
    def dwSetCoreConnections(self) -> object:
        logging.debug("SDC_HwControl::dwSetCoreConnections")
        dwError = 0

        if not self.m_poDevice.bIsDDS50():
            llMaskCoreGroup1 = SPCM_DDS_CORE8  | SPCM_DDS_CORE9  | SPCM_DDS_CORE10 | SPCM_DDS_CORE11
            llMaskCoreGroup2 = SPCM_DDS_CORE12 | SPCM_DDS_CORE13 | SPCM_DDS_CORE14 | SPCM_DDS_CORE15
            llMaskCoreGroup3 = SPCM_DDS_CORE16 | SPCM_DDS_CORE17 | SPCM_DDS_CORE18 | SPCM_DDS_CORE19

            if self.m_llConnectionMaskCh1 & llMaskCoreGroup1:
                self.m_llConnectionMaskCh1 |= llMaskCoreGroup1
            else:
                self.m_llConnectionMaskCh0 |= llMaskCoreGroup1

            if self.m_llConnectionMaskCh2 & llMaskCoreGroup2:
                self.m_llConnectionMaskCh2 |= llMaskCoreGroup2
            else:
                self.m_llConnectionMaskCh0 |= llMaskCoreGroup2

            if self.m_llConnectionMaskCh3 & llMaskCoreGroup3:
                self.m_llConnectionMaskCh3 |= llMaskCoreGroup3
            else:
                self.m_llConnectionMaskCh0 |= llMaskCoreGroup3

        dwNumCh = int(self.m_poDevice.lGetNumMaxChannels())

        dwError = spcm_dwSetParam_i64(self.m_poDevice.hDevice (), SPC_DDS_CORES_ON_CH0, self.m_llConnectionMaskCh0)
        if dwNumCh > 1:
            dwError = spcm_dwSetParam_i64(self.m_poDevice.hDevice (), SPC_DDS_CORES_ON_CH1, self.m_llConnectionMaskCh1)
        if dwNumCh > 2:
            dwError = spcm_dwSetParam_i64(self.m_poDevice.hDevice (), SPC_DDS_CORES_ON_CH2, self.m_llConnectionMaskCh2)
            dwError = spcm_dwSetParam_i64(self.m_poDevice.hDevice (), SPC_DDS_CORES_ON_CH3, self.m_llConnectionMaskCh3)
        
        return dwError

    # DONE
    def dwDoGeneralSetup(self) -> object:
        logging.debug("SDC_HwControl::dwDoGeneralSetup")
        dwError = 0

        dwNumCh = int(self.m_poDevice.lGetNumMaxChannels())

        llSamplingrate = 0
        lChEnable = (0x1 << dwNumCh) - 1

        if self.m_poDevice.oGetGeneralSettings ("SPC_CHENABLE").isValid():
            lChEnable = int(self.m_poDevice.oGetGeneralSettings("SPC_CHENABLE"))

        dwError = spcm_dwSetParam_i32(self.m_poDevice.hDevice (), SPC_CHENABLE,    lChEnable)
        dwError = spcm_dwSetParam_i32(self.m_poDevice.hDevice (), SPC_CARDMODE,    SPC_REP_STD_DDS)
        dwError = spcm_dwSetParam_i32(self.m_poDevice.hDevice (), SPC_CLOCKMODE,   SPC_CM_INTPLL)
        dwError = spcm_dwSetParam_i32(self.m_poDevice.hDevice (), SPC_TRIG_ORMASK, SPC_TMASK_NONE)

        if self.m_poDevice.oGetGeneralSettings ("SPC_SAMPLERATE").isValid():
            llSamplingrate = int(self.m_poDevice.oGetGeneralSettings("SPC_SAMPLERATE"))
            dwError = spcm_dwSetParam_i64(self.m_poDevice.hDevice (), SPC_SAMPLERATE, llSamplingrate)

        # setup the channels
        for dwChIdx in range(dwNumCh):
            oChSetting = self.m_poDevice.oGetChSettings(dwChIdx)

            dwError = spcm_dwSetParam_i32(self.m_poDevice.hDevice (), SPC_AMP0 + 100 * dwChIdx, oChSetting.lGetOutputRange_mV ())
            dwError = spcm_dwSetParam_i32(self.m_poDevice.hDevice (), SPC_FILTER0 + 100 * dwChIdx, oChSetting.lGetFilter ())
            dwError = spcm_dwSetParam_i32(self.m_poDevice.hDevice (), SPC_ENABLEOUT0 + 100 * dwChIdx, oChSetting.lOutputEnabled ())

        dwError = spcm_dwSetParam_i32(self.m_poDevice.hDevice (), SPC_M2CMD, M2CMD_CARD_WRITESETUP)

        return dwError
    
    # DONE
    def dwDoCoreSetup(self, poCoreSettings) -> object:
        logging.debug("SDC_HwControl::dwDoCoreSetup")
        dwError = 0

        lCoreNum = poCoreSettings.lGetCoreNum()
        llBitMask = 0x1 << lCoreNum

        dwError = spcm_dwSetParam_d64 (self.m_poDevice.hDevice (), SPC_DDS_CORE0_AMP   + lCoreNum, poCoreSettings.oGetAmplitude ().dGetValue ())
        dwError = spcm_dwSetParam_d64 (self.m_poDevice.hDevice (), SPC_DDS_CORE0_FREQ  + lCoreNum, poCoreSettings.oGetFrequency ().dGetValue ())
        dwError = spcm_dwSetParam_d64 (self.m_poDevice.hDevice (), SPC_DDS_CORE0_PHASE + lCoreNum, poCoreSettings.oGetPhase ().dGetValue ())

        # set connection masks (M4i.66xx and M4i.96xx)
        if (self.m_poDevice.lGetCardFamily () == TYP_M4I66XX_X8 or self.m_poDevice.lGetCardFamily () == TYP_M4I96XX_X8):
            lChNum = poCoreSettings.lGetChNum()
            if lChNum == 0: self.m_llConnectionMaskCh0 |= llBitMask
            if lChNum == 1: self.m_llConnectionMaskCh1 |= llBitMask
            if lChNum == 2: self.m_llConnectionMaskCh2 |= llBitMask
            if lChNum == 3: self.m_llConnectionMaskCh3 |= llBitMask
        
        return dwError
    
    # DONE
    def dwWriteToQueue(self, voCmdList : list, lNumLoops : int = 1) -> int:
        logging.debug("SDC_HwControl::dwWriteToQueue")
        dwError = 0
        if lNumLoops == 1:
            if self.m_poDevice.bIsDevRunning():
                dwError = self.dwWriteCmdList(voCmdList)
            else:
                dwError = self.dwExecCmdList(voCmdList)
        else:
            self.m_poHwControlThread.vAddCmdList (voCmdList, lNumLoops)
            self.m_poHwControlThread.vStart()
        return dwError
    
    # DONE
    def dwStart(self) -> int:
        logging.debug("SDC_HwControl::dwStart")
        dwError = 0

        self.m_poDevice.vSetDevIsRunning(True)

        dwError = spcm_dwSetParam_i32(self.m_poDevice.hDevice (), SPC_DDS_CMD, SPCM_DDS_CMD_EXEC_AT_TRG)
        dwError = spcm_dwSetParam_i32(self.m_poDevice.hDevice (), SPC_DDS_CMD, SPCM_DDS_CMD_WRITE_TO_CARD)

        dwError = spcm_dwSetParam_i32(self.m_poDevice.hDevice (), SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER)

        # start the output by initiating a force trigger
        dwError = spcm_dwSetParam_i32(self.m_poDevice.hDevice (), SPC_M2CMD, M2CMD_CARD_FORCETRIGGER)

        return dwError
    
    # DONE
    def dwReset(self) -> int:
        logging.debug("SDC_HwControl::dwReset")
        return spcm_dwSetParam_i32(self.m_poDevice.hDevice (), SPC_DDS_CMD, SPCM_DDS_CMD_RESET)

    # DONE
    def vStop(self):
        logging.debug("SDC_HwControl::vStop")
        self.m_poHwControlThread.vStop()

        spcm_dwSetParam_i32(self.m_poDevice.hDevice(), SPC_M2CMD, M2CMD_CARD_STOP)
        spcm_dwSetParam_i32(self.m_poDevice.hDevice(), SPC_DDS_CMD, SPCM_DDS_CMD_RESET)

        self.m_poDevice.vSetDevIsRunning(False)

    # DONE
    def vStopAll(self):
        logging.debug("SDC_HwControl::vStopAll")
        self.m_poHwControlThread.vStop()

        for lDevIdx in range(len(self.m_vpoDevices)):
            if self.m_vpoDevices[lDevIdx].bIsDevRunning():
                spcm_dwSetParam_i32(self.m_vpoDevices[lDevIdx].hDevice(), SPC_M2CMD, M2CMD_CARD_STOP)
                spcm_dwSetParam_i32(self.m_vpoDevices[lDevIdx].hDevice(), SPC_DDS_CMD, SPCM_DDS_CMD_RESET)

    # DONE
    def dwSetAmplitude(self, dwCoreIndex : int, pdValue : float) -> object:
        logging.debug("SDC_HwControl::dwSetAmplitude")
        dwError = 0
        pdValue = c_float(pdValue)
        dwError = spcm_dwSetParam_d64(self.m_poDevice.hDevice(), SPC_DDS_CORE0_AMP + dwCoreIndex, pdValue)
        dwError = spcm_dwGetParam_d64(self.m_poDevice.hDevice(), SPC_DDS_CORE0_AMP + dwCoreIndex, byref(pdValue))

        if self.m_poDevice.bIsDevRunning():
            dwError = spcm_dwSetParam_i32 (self.m_poDevice.hDevice (), SPC_DDS_CMD, SPCM_DDS_CMD_EXEC_NOW)
            dwError = spcm_dwSetParam_i32 (self.m_poDevice.hDevice (), SPC_DDS_CMD, SPCM_DDS_CMD_WRITE_TO_CARD)

        return dwError

    # DONE
    def dwSetFrequency(self, dwCoreIndex : int, pdValue : float) -> object:
        logging.debug("SDC_HwControl::dwSetFrequency")
        dwError = 0
        pdValue = c_float(pdValue)
        dwError = spcm_dwSetParam_d64(self.m_poDevice.hDevice(), SPC_DDS_CORE0_FREQ + dwCoreIndex, pdValue)
        dwError = spcm_dwGetParam_d64(self.m_poDevice.hDevice(), SPC_DDS_CORE0_FREQ + dwCoreIndex, byref(pdValue))

        if self.m_poDevice.bIsDevRunning():
            dwError = spcm_dwSetParam_i32 (self.m_poDevice.hDevice (), SPC_DDS_CMD, SPCM_DDS_CMD_EXEC_NOW)
            dwError = spcm_dwSetParam_i32 (self.m_poDevice.hDevice (), SPC_DDS_CMD, SPCM_DDS_CMD_WRITE_TO_CARD)

        return dwError

    # DONE
    def dwSetPhase(self, dwCoreIndex : int, pdValue : float) -> object:
        logging.debug("SDC_HwControl::dwSetPhase")
        dwError = 0
        pdValue = c_float(pdValue)
        dwError = spcm_dwSetParam_d64(self.m_poDevice.hDevice(), SPC_DDS_CORE0_PHASE + dwCoreIndex, pdValue)
        dwError = spcm_dwGetParam_d64(self.m_poDevice.hDevice(), SPC_DDS_CORE0_PHASE + dwCoreIndex, byref(pdValue))

        if self.m_poDevice.bIsDevRunning():
            dwError = spcm_dwSetParam_i32 (self.m_poDevice.hDevice (), SPC_DDS_CMD, SPCM_DDS_CMD_EXEC_NOW)
            dwError = spcm_dwSetParam_i32 (self.m_poDevice.hDevice (), SPC_DDS_CMD, SPCM_DDS_CMD_WRITE_TO_CARD)

        return dwError
    
    # DONE
    def sGetLastErrorText(self) -> str:
        logging.debug("SDC_HwControl::sGetLastErrorText")
        # dwRegister = uint32(0)
        # lValue = int32(0)
        szErrorTextBuffer = create_string_buffer(ERRORTEXTLEN)
        # spcm_dwGetErrorInfo_i32(self.m_poDevice.hDevice(), byref(dwRegister), byref(lValue), byref(szErrorTextBuffer))
        spcm_dwGetErrorInfo_i32(self.m_poDevice.hDevice(), None, None, byref(szErrorTextBuffer))
        return szErrorTextBuffer.value.decode('utf-8')
    
    # DONE
    def lReadQueueMax(self) -> int:
        logging.debug("SDC_HwControl::lReadQueueMax")
        lValue = c_int(0)

        if not spcm_dwGetParam_i32(self.m_poDevice.hDevice (), SPC_DDS_QUEUE_CMD_MAX, byref(lValue)):
            return lValue.value

        return -1
    
    # DONE
    def lReadQueueCount(self) -> int:
        logging.debug("SDC_HwControl::lReadQueueCount")
        lValue = c_int(0)

        if not spcm_dwGetParam_i32(self.m_poDevice.hDevice (), SPC_DDS_QUEUE_CMD_COUNT, byref(lValue)):
            return lValue.value

        return -1
    
    # DONE
    def lReadQueueInSW(self) -> int:
        logging.debug("SDC_HwControl::lReadQueueInSW")
        lValue = c_int(0)

        if not spcm_dwGetParam_i32(self.m_poDevice.hDevice (), SPC_DDS_NUM_QUEUED_CMD_IN_SW, byref(lValue)):
            return lValue.value

        return -1

    # DONE
    def bIsDeviceDDS(self, hDevice) -> bool:
        logging.debug("SDC_HwControl::bIsDeviceDDS")
        lFncType = c_int(0)
        spcm_dwGetParam_i32 (hDevice, SPC_FNCTYPE, byref(lFncType))

        if lFncType.value == SPCM_TYPE_AO:
            lFWFeatures = c_int(0)
            spcm_dwGetParam_i32 (hDevice, SPC_PCIEXTFEATURES, byref(lFWFeatures))
            
            if ((lFWFeatures.value & SPCM_FEAT_EXTFW_DDS20) or (lFWFeatures.value & SPCM_FEAT_EXTFW_DDS50)):
                return True

        return False

    # DONE
    def poOpenDevice(self, sDeviceString : str) -> SDC_SpcDevice:
        logging.debug("SDC_HwControl::poOpenDevice")
        poDevice = None

        bAbort = False

        bRemote = False
        if sDeviceString.startswith ("TCPIP::"):
            bRemote = True

        hDevice = spcm_hOpen(create_string_buffer(bytes(sDeviceString, 'utf-8')))

        if hDevice:
            if self.bIsDeviceDDS(hDevice):
                poDevice = self.poCreateDevice(hDevice, bRemote)
            else:
                spcm_vClose(hDevice)
        else:
            bAbort = True

        return poDevice

    # DONE
    def poCreateDevice(self, hDevice, bRemote : bool = False):
        logging.debug("SDC_HwControl::poCreateDevice")
        lCardType = c_int(0)

        spcm_dwGetParam_i32(hDevice, SPC_PCITYP, byref(lCardType))
        
        if (TYP_SERIESMASK | TYP_FAMILYMASK) & lCardType.value == TYP_M2P65XX_X4:  return SDC_SpcDevM2p65xx(hDevice, bRemote)
        if (TYP_SERIESMASK | TYP_FAMILYMASK) & lCardType.value == TYP_M4I66XX_X8:  return SDC_SpcDevM4i66xx(hDevice, bRemote)
        if (TYP_SERIESMASK | TYP_FAMILYMASK) & lCardType.value == TYP_M4I96XX_X8:  return SDC_SpcDevM4i96xx(hDevice, bRemote)
        if (TYP_SERIESMASK | TYP_FAMILYMASK) & lCardType.value == TYP_M5I63XX_X16: return SDC_SpcDevM5i63xx(hDevice, bRemote)
    
    # DONE
    def dwWriteCmdList(self, pvoCmdList : list[SDC_DrvCmd]) -> int:
        logging.debug("SDC_HwControl::dwWriteCmdList")
        
        pstDDSParamListRaw = (ST_LIST_PARAM * len(pvoCmdList))()
        pstDDSParamList = ctypes.cast(pstDDSParamListRaw, ctypes.POINTER(ST_LIST_PARAM))
            
        for lIdx in range(len(pvoCmdList)):
            pstDDSParamList[lIdx].lReg = pvoCmdList[lIdx].lGetRegister()
            pstDDSParamList[lIdx].lType = pvoCmdList[lIdx].lGetType()

            if pvoCmdList[lIdx].lGetType() == TYPE_DOUBLE:
                pstDDSParamList[lIdx].dValue = double(pvoCmdList[lIdx].oGetValue())
            else:
                pstDDSParamList[lIdx].llValue = int(pvoCmdList[lIdx].oGetValue())
            
        return spcm_dwSetParam_ptr (self.m_poDevice.hDevice(), SPC_REGISTER_LIST, pstDDSParamList, len(pvoCmdList) * ctypes.sizeof(ST_LIST_PARAM))
    
    # DONE
    def dwExecCmdList(self, pvoCmdList : list) -> int:
        logging.debug("SDC_HwControl::dwExecCmdList")
        dwError = spcm_dwSetParam_i32(self.m_poDevice.hDevice(), SPC_DDS_CMD, SPCM_DDS_CMD_EXEC_NOW)

        dwError = self.dwWriteCmdList(pvoCmdList)

        if not dwError:
            dwError = spcm_dwSetParam_i32 (self.m_poDevice.hDevice(), SPC_DDS_CMD, SPCM_DDS_CMD_EXEC_AT_TRG)
            dwError = spcm_dwSetParam_i32 (self.m_poDevice.hDevice(), SPC_DDS_CMD, SPCM_DDS_CMD_WRITE_TO_CARD)
            dwError = spcm_dwSetParam_i32 (self.m_poDevice.hDevice(), SPC_M2CMD, M2CMD_CARD_FORCETRIGGER)
        
        return dwError

class SDC_HwControlThread(QThread):
    m_bStop : bool = False
    m_lNumLoops : int = 0
    m_poHwControl : "SDC_HwControl" = None
    m_voCmdList : list = []

    # DONE
    def __init__(self, poHwControl : SDC_HwControl):
        logging.debug("SDC_HwControlThread::__init__")
        self.m_poHwControl = poHwControl
        self.m_bStop = False

        self.m_lNumLoops = 0
        self.m_voCmdList = []
    
    # DONE
    def __del__(self):
        logging.debug("SDC_HwControlThread::__del__")

    # DONE
    def vStart(self):
        logging.debug("SDC_HwControlThread::vStart")
        self.start()
        
    # DONE
    def vStop(self):
        logging.debug("SDC_HwControlThread::vStop")
        self.m_bStop = True
    
    # DONE
    def vAddCmdList(self, voCmdList : list[SDC_DrvCmd], lNumLoops : int):
        logging.debug("SDC_HwControlThread::vAddCmdList")
        self.m_voCmdList = voCmdList
        self.m_lNumLoops = lNumLoops
    
    # DONE
    def run(self):
        logging.debug("SDC_HwControlThread::run")
        lQueueCount = lQueueMax = 0
        self.m_bStop = False
        lCounter = 0
        lQueueMax = self.m_poHwControl.lReadQueueMax()

        while not self.m_lNumLoops or lCounter < self.m_lNumLoops:
            if self.m_bStop:
                break

            lQueueCount = self.m_poHwControl.lReadQueueCount()
            if (lQueueCount + len(self.m_voCmdList)) < lQueueMax:
                self.m_poHwControl.dwWriteToQueue(self.m_voCmdList)
                lCounter += 1

            time.sleep(0.05)


class SDC_HwStatusThread(QThread):
    sigBufferStatus = pyqtSignal(int, int, int)  # lQueueInSW, lQueueCount, lQueueMax
    m_bRunning : bool = False
    m_bEnd : bool = False
    m_poHwControl : "SDC_HwControl" = None
    m_poMutex : QMutex = None
    m_poWaitCondition : QWaitCondition = None

    # DONE
    def __init__(self, poHwControl : "SDC_HwControl"):
        logging.debug("SDC_HwStatusThread::__init__")
        super().__init__()
        self.m_poHwControl = poHwControl
        self.m_bEnd = False
        self.m_bRunning = True

        self.m_poMutex = QMutex()
        self.m_poWaitCondition = QWaitCondition()
    
    # DONE
    def __del__(self):
        logging.debug("SDC_HwStatusThread::__del__")
        del self.m_poMutex
        del self.m_poWaitCondition

    # DONE
    def bIsRunning(self) -> bool:
        logging.debug("SDC_HwStatusThread::bIsRunning")
        return self.m_bRunning
    
    # DONE
    def vStart(self):
        logging.debug("SDC_HwStatusThread::vStart")
        self.m_bRunning = True

        if self.isRunning():
            self.m_poWaitCondition.wakeAll()
        else:
            self.start()
    
    # DONE
    def vStop(self):
        logging.debug("SDC_HwStatusThread::vStop")
        self.m_bRunning = False
    
    # DONE
    def vEnd(self):
        logging.debug("SDC_HwStatusThread::vEnd")
        self.m_bEnd = True
        self.m_bRunning = False
        self.m_poWaitCondition.wakeAll()
    
    # DONE
    def run(self):
        logging.debug("SDC_HwStatusThread::run")
        lQueueCount = lQueueInSW = 0

        lQueueMax = self.m_poHwControl.lReadQueueMax()

        while not self.m_bEnd:
            while self.m_bRunning:
                lQueueCount = self.m_poHwControl.lReadQueueCount()
                lQueueInSW  = self.m_poHwControl.lReadQueueInSW()

                self.sigBufferStatus.emit(lQueueInSW, lQueueCount, lQueueMax)
                
                time.sleep(0.2)

            if not self.m_bEnd:
                self.m_poMutex.lock()
                self.m_poWaitCondition.wait(self.m_poMutex)
                self.m_poMutex.unlock()
                
