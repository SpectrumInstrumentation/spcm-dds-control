from PyQt5.QtCore import QObject, pyqtSignal
from pathlib import Path
from numpy import int32
import logging

from settings.sdc_settings import SDC_Settings
from control.sdc_hwcontrol import SDC_HwControl


class SDC_Control(QObject):
    sigShowMessage = pyqtSignal(SDC_Settings.MSBOX_TYPE, str, str)
    m_poSettings : SDC_Settings = None
    m_poHwControl : SDC_HwControl = None
    m_oRegisterNames : list[str] = []
    m_mslRegisterMap : dict[str, int] = {}

    def __init__(self):
        logging.debug("SDC_Control::__init__")
        super().__init__()
        self.m_poSettings = SDC_Settings.poGetInstance()
        self.m_poHwControl = SDC_HwControl()
        self.m_oRegisterNames : list[str] = []
        self.m_mslRegisterMap : dict[str, int] = {}

    def __delete__(self):
        logging.debug("SDC_Control::__delete__")
        # SDC_Settings::vDestroy ();
        del self.m_poSettings

    def poGetHwCtrlObj(self):
        logging.debug("SDC_Control::poGetHwCtrlObj")
        return self.m_poHwControl

    def oInit(self) -> list:
        logging.debug("SDC_Control::oInit")
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
    
    def bLoadRegisterFile(self) -> bool:
        logging.debug("SDC_Control::bLoadRegisterFile")

        voFileData = self.bReadCSVFile(self.m_poSettings.sGetRegisterFilePath())
        if not voFileData:
            return False

        self.m_oRegisterNames.clear()
        self.m_mslRegisterMap.clear()

        for lIdx in range(len(voFileData)):
            if len(voFileData[lIdx]) == 2:
                sRegister = voFileData[lIdx][0]
                lValue = int(voFileData[lIdx][1])

                self.m_oRegisterNames.append(sRegister)
                self.m_mslRegisterMap[sRegister] = lValue

        return True
    
    def lGetRegisterValue(self, sRegisterName: str) -> int:
        logging.debug("SDC_Control::lGetRegisterValue")
        if sRegisterName in self.m_mslRegisterMap:
            return self.m_mslRegisterMap[sRegisterName]

        return -1

    def oGetStrListRegisterNames(self) -> list[str]:
        logging.debug("SDC_Control::oGetStrListRegisterNames")
        return self.m_oRegisterNames

    def bReadCSVFile(self, sFilePath: str) -> list[str]:
        logging.debug(f"SDC_Control::bReadCSVFile({sFilePath})")

        pvoFileData = []
        oPath = Path(sFilePath)
        if not oPath.is_file():
            return False
        
        with oPath.open('r') as oFile:
            for sLine in oFile:
                sLine = sLine.strip()
                if not sLine:
                    continue
                oStrListSplit = sLine.split(',')
                oStrListData = [item.strip() for item in oStrListSplit]
                pvoFileData.append(oStrListData)

        return pvoFileData

    def bWriteCSVFile (self, sFilePath : str, pvoFileData):
        logging.debug(f"SDC_Control::bWriteCSVFile({sFilePath})")
        if not pvoFileData:
            return False

        oPath = Path(sFilePath)
        if not oPath.is_file():
            return False
        
        with oPath.open('w') as oFile:
            for lIdx in range(len(pvoFileData)):
                if len(pvoFileData[lIdx]) == 3:
                    oFile.write(f"{pvoFileData[lIdx][0]},{pvoFileData[lIdx][1]},{pvoFileData[lIdx][2]}\n")

        return True