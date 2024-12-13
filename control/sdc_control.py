from PyQt5.QtCore import QObject, pyqtSignal
from settings.sdc_settings import SDC_Settings
from control.sdc_hwcontrol import SDC_HwControl

# ********************************************************************************************************
# ***** Public Constructor
# ********************************************************************************************************
class SDC_Control(QObject):
    sigShowMessage = pyqtSignal(SDC_Settings.MSBOX_TYPE, str, str)
    m_poSettings : SDC_Settings = None
    m_poHwControl : SDC_HwControl = None

    def __init__(self):
        #print("SDC_Control::__init__")
        super().__init__()
        self.m_poSettings = SDC_Settings()
        self.m_poHwControl = SDC_HwControl()

    # ********************************************************************************************************
    # ***** Public Destructor
    # ********************************************************************************************************
    def __delete__(self):
        #print("SDC_Control::__delete__")
        del self.m_poSettings

    # ********************************************************************************************************
    # ***** Public Method
    # ********************************************************************************************************
    def oInit(self) -> list:
        #print("SDC_Control::oInit")
        oDeviceNames = []
        
        dwNumDevices = self.m_poHwControl.dwOpenHardware()
        if not dwNumDevices:
            # raise Exception("No Spectrum DDS device found !")
            self.sigShowMessage.emit(SDC_Settings.MSBOX_TYPE.MSB_WARNING, "No Hardware", "No Spectrum DDS device found !")
        else:
            for dwIdx in range(dwNumDevices):
                poDevice = self.m_poHwControl.poGetDevice(dwIdx)
                if poDevice:
                    oDeviceNames.append(poDevice.sGetDeviceName())

        return oDeviceNames
    
    def poGetHwCtrlObj(self):
        #print("SDC_Control::poGetHwCtrlObj")
        return self.m_poHwControl

# ********************************************************************************************************