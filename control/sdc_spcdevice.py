import spcm

# ********************************************************************************************************
# ***** Public Constructor
# ********************************************************************************************************
class SDC_SpcDevChSetting:
    m_lOutputEnabled : int = 0
    m_lOutputRange_mV : int = 0
    m_lFilter : int = 0

    def __init__(self):
        #print("SDC_SpcDevChSetting::__init__")
        self.m_lOutputEnabled = 1
        self.m_lOutputRange_mV = 1000
        self.m_lFilter = 0
        
    def vSetOutputEnabled(self, lValue : int):
        #print("SDC_SpcDevChSetting::vSetOutputEnabled")
        self.m_lOutputEnabled = lValue

    def lOutputEnabled(self) -> int:
        #print("SDC_SpcDevChSetting::lOutputEnabled")
        return self.m_lOutputEnabled

    def vSetOutputRange_mV(self, lValue : int):
        #print("SDC_SpcDevChSetting::vSetOutputRange_mV")
        self.m_lOutputRange_mV = lValue

    def lGetOutputRange_mV(self) -> int:
        #print("SDC_SpcDevChSetting::lGetOutputRange_mV")
        return self.m_lOutputRange_mV

    def vSetFilter(self, lValue : int):
        #print("SDC_SpcDevChSetting::vSetFilter")
        self.m_lFilter = lValue

    def lGetFilter(self) -> int:
        #print("SDC_SpcDevChSetting::lGetFilter")
        return self.m_lFilter

# ********************************************************************************************************
# ***** Public Constructor
# ********************************************************************************************************
class SDC_SpcDevice:
    m_loChannelSettings : list[SDC_SpcDevChSetting] = []
    m_oDevice : spcm.Device = None
    m_oDDS : spcm.DDS = None
    m_oTrigger : spcm.Trigger = None
    m_oChannels : spcm.Channels = None
    m_oClock : spcm.Clock = None
    m_bIsDDS50 : bool = False
    m_lCardType : int = 0
    m_lSN : int = 0
    m_lMaxChannels : int = 0
    m_sDeviceName : str = ""

    def __init__(self, oDevice):
        #print("SDC_SpcDevice::__init__")
        self.m_oDevice = oDevice

        self.m_oDDS = spcm.DDS(self.m_oDevice)
        self.m_oTrigger = spcm.Trigger(self.m_oDevice)
        self.m_oChannels = spcm.Channels(self.m_oDevice)
        self.m_oClock = spcm.Clock(self.m_oDevice)

        self.m_bIsDDS50 = False

        acCardType = self.m_oDevice.product_name()

        self.m_lCardType = self.m_oDevice.card_type()
        self.m_lSN = self.m_oDevice.sn()
        lExtFeatureMask = self.m_oDevice.ext_features()

        if lExtFeatureMask & spcm.SPCM_FEAT_EXTFW_DDS50:
            self.m_bIsDDS50 = True

        self.m_lMaxChannels = self.m_oDevice.num_channels()

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
    def oGetChSettings(self, lChIdx : int): # -> SDC_SpcDevChSetting:
        #print("SDC_SpcDevice::oGetChSettings")
        if lChIdx < len(self.m_loChannelSettings):
            return self.m_loChannelSettings[lChIdx]

        return SDC_SpcDevChSetting()

    # def oDevice(self):
    #     #print("SDC_SpcDevice::hDevice")
    #     return self.m_oDevice

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