import spcm

# ********************************************************************************************************
# ***** Public Constructor
# ********************************************************************************************************
class SDC_SpcDevChSetting:
    def __init__(self):
        #print("SDC_SpcDevChSetting::__init__")
        self.m_lOutputEnabled = 1
        self.m_lOutputRange_mV = 1000
        self.m_lFilter = 0
        
    def vSetOutputEnabled (self, lValue : int):
        #print("SDC_SpcDevChSetting::vSetOutputEnabled")
        self.m_lOutputEnabled = lValue

    def lOutputEnabled(self) -> int:
        #print("SDC_SpcDevChSetting::lOutputEnabled")
        return self.m_lOutputEnabled

    def vSetOutputRange_mV (self, lValue : int):
        #print("SDC_SpcDevChSetting::vSetOutputRange_mV")
        self.m_lOutputRange_mV = lValue

    def lGetOutputRange_mV(self) -> int:
        #print("SDC_SpcDevChSetting::lGetOutputRange_mV")
        return self.m_lOutputRange_mV

    def vSetFilter (self, lValue : int):
        #print("SDC_SpcDevChSetting::vSetFilter")
        self.m_lFilter = lValue

    def lGetFilter(self) -> int:
        #print("SDC_SpcDevChSetting::lGetFilter")
        return self.m_lFilter

# ********************************************************************************************************
# ***** Public Constructor
# ********************************************************************************************************
class SDC_SpcDevice:
    m_loChannelSettings : list = []

    def __init__(self, hDevice):
        #print("SDC_SpcDevice::__init__")
        self.m_hDevice = hDevice

        self.dds = spcm.DDS(self.m_hDevice)
        self.trigger = spcm.Trigger(self.m_hDevice)
        self.channels = spcm.Channels(self.m_hDevice)
        self.clock = spcm.Clock(self.m_hDevice)

        self.m_bIsDDS50 = False

        acCardType = self.m_hDevice.product_name()

        self.m_lCardType = self.m_hDevice.card_type()
        self.m_lSN = self.m_hDevice.sn()
        lExtFeatureMask = self.m_hDevice.ext_features()

        if lExtFeatureMask & spcm.SPCM_FEAT_EXTFW_DDS50:
            self.m_bIsDDS50 = True

        self.m_lMaxChannels = self.m_hDevice.num_channels()

        self.m_sDeviceName = "{} SN: {}".format(acCardType, self.m_lSN)

        for _ in range(self.m_lMaxChannels):
            self.m_loChannelSettings.append(SDC_SpcDevChSetting())

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def vSetChSettings(self, lChIdx : int, oSetting):
        #print("SDC_SpcDevice::vSetChSettings")
        if lChIdx < len(self.m_loChannelSettings):
            self.m_loChannelSettings[lChIdx] = oSetting

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def oGetChSettings (self, lChIdx : int): # -> SDC_SpcDevChSetting:
        #print("SDC_SpcDevice::oGetChSettings")
        if lChIdx < len(self.m_loChannelSettings):
            return self.m_loChannelSettings[lChIdx]

        return SDC_SpcDevChSetting ()

    def hDevice(self):
        #print("SDC_SpcDevice::hDevice")
        return self.m_hDevice

    def bIsDDS50(self) -> bool:
        #print("SDC_SpcDevice::bIsDDS50")
        return self.m_bIsDDS50

    def sGetDeviceName(self) -> str:
        #print("SDC_SpcDevice::sGetDeviceName")
        return self.m_sDeviceName

    def lGetNumMaxChannels(self) -> int:
        #print("SDC_SpcDevice::lGetNumMaxChannels")
        return self.m_lMaxChannels


# ********************************************************************************************************