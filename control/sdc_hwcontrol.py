import spcm

from settings.sdc_settings import SDC_Settings
from settings.sdc_coresettings import SDC_Value
from control.sdc_spcdevice import SDC_SpcDevice

MAX_SPCM_DEVICES = 16

# ********************************************************************************************************
# ***** Public Constructor
# ********************************************************************************************************
class SDC_HwControl():
    m_vpoDevices = []
    m_llConnectionMaskCh0 = 0
    m_llConnectionMaskCh1 = 0
    m_llConnectionMaskCh2 = 0
    m_llConnectionMaskCh3 = 0

    def __init__(self):
        #print("SDC_HwControl::__init__")
        self.m_poSettings = SDC_Settings()
        self.m_poDevice = None
        self.m_bHwIsRunning = False

    # ********************************************************************************************************
    # ***** Public Destructor
    # ********************************************************************************************************
    def __del__(self):
        #print("SDC_HwControl::__del__")
        pass

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def dwOpenHardware(self) -> int:
        #print("SDC_HwControl::dwOpenHardware")
        self.m_vpoDevices = []

        for dwDevIdx in range(MAX_SPCM_DEVICES):
            oDeviceName = "/dev/spcm{}".format(dwDevIdx)
            device = spcm.Card(oDeviceName, throw_error=False)
            device.__enter__()
            if device:
                if self.bIsDeviceDDS(device):
                    poDevice = SDC_SpcDevice(device)
                    self.m_vpoDevices.append(poDevice)

        return len(self.m_vpoDevices)

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def vSetCurrentDevice (self, dwDevIdx : int):
        #print("SDC_HwControl::vSetCurrentDevice")

        if dwDevIdx < len(self.m_vpoDevices):
            self.m_poDevice = self.m_vpoDevices[dwDevIdx]

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def poGetDevice (self, dwDevIndex : int): # -> SDC_SpcDevice:
        #print("SDC_HwControl::poGetDevice")
        if dwDevIndex < len(self.m_vpoDevices):
            return self.m_vpoDevices[dwDevIndex]
        raise Exception("Device #{} not found !".format(dwDevIndex))

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def poGetDeviceByeName (self, sName : str): #-> SDC_SpcDevice
        #print("SDC_HwControl::poGetDeviceByeName")
        for device in self.m_vpoDevices:
            if device.sGetDeviceName() == sName:
                return device
        raise Exception("Device {} not found !".format(sName))

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def dwGetCoreInfos (self, poCoreSettings) -> int:
        #print("SDC_HwControl::dwGetCoreInfos")
        dwError = 0

        if not self.m_poDevice:
            return dwError

        dMin = 0 #self.m_poDevice.dds.avail_amp_min() # TODO this is a bug in the driver
        dMax = self.m_poDevice.dds.avail_amp_max()
        dStep = self.m_poDevice.dds.avail_amp_step()
        poCoreSettings.vSetAmplitude(SDC_Value(dMin, dMax, dStep))
        
        dMin = 0 #self.m_poDevice.dds.avail_freq_min() # TODO this is a bug in the driver
        dMax = self.m_poDevice.dds.avail_freq_max()
        dStep = self.m_poDevice.dds.avail_freq_step()
        poCoreSettings.vSetFrequency(SDC_Value(dMin, dMax, dStep))

        dMin = self.m_poDevice.dds.avail_phase_min()
        dMax = self.m_poDevice.dds.avail_phase_max()
        dStep = self.m_poDevice.dds.avail_phase_step()
        poCoreSettings.vSetPhase(SDC_Value(dMin, dMax, dStep))

        return dwError

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def dwSetAmplitude (self, dwCoreIndex : int, pdValue : float) -> int:
        #print("SDC_HwControl::dwSetAmplitude")
        dwError = 0
        self.m_poDevice.dds.amp(dwCoreIndex, pdValue)
        if self.m_bHwIsRunning:
            self.m_poDevice.dds.exec_now()
            self.m_poDevice.dds.write_to_card()

        return dwError

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def dwSetFrequency(self, dwCoreIndex : int, pdValue : float) -> int:
        #print("SDC_HwControl::dwSetFrequency")
        dwError = 0
        self.m_poDevice.dds.freq(dwCoreIndex, pdValue)
        if self.m_bHwIsRunning:
            self.m_poDevice.dds.exec_now()
            self.m_poDevice.dds.write_to_card()

        return dwError

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def dwSetPhase(self, dwCoreIndex : int, pdValue : float) -> int:
        #print("SDC_HwControl::dwSetPhase")
        dwError = 0
        self.m_poDevice.dds.phase(dwCoreIndex, pdValue)
        if self.m_bHwIsRunning:
            self.m_poDevice.dds.exec_now()
            self.m_poDevice.dds.write_to_card()

        return dwError

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def vClearCoreConnectionsMasks(self):
        #print("SDC_HwControl::vClearCoreConnectionsMasks")
        self.m_llConnectionMaskCh0 = self.m_llConnectionMaskCh1 = self.m_llConnectionMaskCh2 = self.m_llConnectionMaskCh3 = 0

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def dwSetCoreConnections(self) -> int:
        #print("SDC_HwControl::dwSetCoreConnections")
        dwError = 0

        if not self.m_poDevice.bIsDDS50():
            llMaskCoreGroup1 = spcm.SPCM_DDS_CORE8  | spcm.SPCM_DDS_CORE9  | spcm.SPCM_DDS_CORE10 | spcm.SPCM_DDS_CORE11;
            llMaskCoreGroup2 = spcm.SPCM_DDS_CORE12 | spcm.SPCM_DDS_CORE13 | spcm.SPCM_DDS_CORE14 | spcm.SPCM_DDS_CORE15;
            llMaskCoreGroup3 = spcm.SPCM_DDS_CORE16 | spcm.SPCM_DDS_CORE17 | spcm.SPCM_DDS_CORE18 | spcm.SPCM_DDS_CORE19;

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

        self.m_poDevice.dds.cores_on_channel(0, self.m_llConnectionMaskCh0)
        if dwNumCh > 1:
            self.m_poDevice.dds.cores_on_channel(1, self.m_llConnectionMaskCh1)
        if dwNumCh > 2:
            self.m_poDevice.dds.cores_on_channel(2, self.m_llConnectionMaskCh2)
            self.m_poDevice.dds.cores_on_channel(3, self.m_llConnectionMaskCh3)
        
        return dwError

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def dwDoGeneralSetup (self) -> int:
        #print("SDC_HwControl::dwDoGeneralSetup")
        dwError = 0

        dwNumCh = int(self.m_poDevice.lGetNumMaxChannels())

        #print(f"{dwNumCh = }")
        #print(f"{len(self.m_poDevice.channels) = }")
        
        self.m_poDevice.channels.channels_enable(enable_all=True)
        self.m_poDevice.hDevice().card_mode(spcm.SPC_REP_STD_DDS)
        self.m_poDevice.clock.mode(spcm.SPC_CM_INTPLL)
        self.m_poDevice.trigger.or_mask(spcm.SPC_TMASK_NONE)

        #print(f"{len(self.m_poDevice.channels) = }")

        # setup the channels
        for dwChIdx in range(dwNumCh):
            oChSetting = self.m_poDevice.oGetChSettings(dwChIdx)
            
            self.m_poDevice.channels[dwChIdx].amp(oChSetting.lGetOutputRange_mV())
            self.m_poDevice.channels[dwChIdx].filter(oChSetting.lGetFilter())
            self.m_poDevice.channels[dwChIdx].enable(oChSetting.lOutputEnabled())

        self.m_poDevice.hDevice().write_setup()
        self.m_poDevice.dds.reset()

        return dwError

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def dwDoCoreSetup (self, poCoreSettings) -> int:
        #print("SDC_HwControl::dwDoCoreSetup")
        dwError = 0

        lCoreIndex = poCoreSettings.lGetCoreIndex()
        llBitMask = 0x1 << lCoreIndex

        self.m_poDevice.dds.amp(lCoreIndex, poCoreSettings.oGetAmplitude().dGetValue())
        self.m_poDevice.dds.freq(lCoreIndex, poCoreSettings.oGetFrequency().dGetValue())
        self.m_poDevice.dds.phase(lCoreIndex, poCoreSettings.oGetPhase().dGetValue())

        # set connection masks
        if poCoreSettings.lGetChannel() == 0:
            self.m_llConnectionMaskCh0 |= llBitMask
        elif poCoreSettings.lGetChannel() == 1:
            self.m_llConnectionMaskCh1 |= llBitMask
        elif poCoreSettings.lGetChannel() == 2:
            self.m_llConnectionMaskCh2 |= llBitMask
        elif poCoreSettings.lGetChannel() == 3:
            self.m_llConnectionMaskCh3 |= llBitMask
        
        return dwError

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def dwStart (self):
        #print("SDC_HwControl::dwStart")
        dwError = 0

        self.m_bHwIsRunning = True

        self.m_poDevice.dds.exec_at_trg()
        self.m_poDevice.dds.write_to_card()

        self.m_poDevice.hDevice().start(spcm.M2CMD_CARD_ENABLETRIGGER)

        self.m_poDevice.trigger.force()

        return dwError

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def vStop(self):
        #print("SDC_HwControl::vStop")
        self.m_poDevice.hDevice().stop()
        self.m_bHwIsRunning = False

    # ********************************************************************************************************
    # ***** Protected Method
    # ********************************************************************************************************
    def bIsDeviceDDS(self, device : spcm.Card) -> bool:
        #print("SDC_HwControl::bIsDeviceDDS")
        if device.function_type() == spcm.SPCM_TYPE_AO:
            features = device.ext_features()
            if (features & spcm.SPCM_FEAT_EXTFW_DDS20) or (features & spcm.SPCM_FEAT_EXTFW_DDS50):
                return True

        return False

    
    def poGetCurrentDevice(self):
        #print("SDC_HwControl::poGetCurrentDevice")
        return self.m_poDevice

    def lGetNumOfDevices(self) -> int:
        #print("SDC_HwControl::lGetNumOfDevices")
        return len(self.m_vpoDevices)

    # ********************************************************************************************************
