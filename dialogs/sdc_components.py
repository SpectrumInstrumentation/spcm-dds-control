from enum import Enum

from PyQt5.QtWidgets import QDial, QToolButton, QPushButton
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import Qt, QEvent

# ********************************************************************************************************
# ***** Public Constructor : Class SDC_Dial
# ********************************************************************************************************
class SDC_Dial(QDial):
    def __init__(self, poParent):
        #print("SDC_Dial::__init__")
        super().__init__(poParent)
        self.setCursor(QCursor(Qt.OpenHandCursor))

    # ********************************************************************************************************
    # ***** Protected Event : Class SDC_Dial
    # ********************************************************************************************************
    def mousePressEvent(self, poEvent):
        #print("SDC_Dial::mousePressEvent")
        self.setCursor(QCursor(Qt.ClosedHandCursor))
        super().mousePressEvent(poEvent)

    # ********************************************************************************************************
    # ***** Protected Event : Class SDC_Dial
    # ********************************************************************************************************
    def mouseReleaseEvent(self, poEvent):
        #print("SDC_Dial::mouseReleaseEvent")
        self.setCursor(QCursor(Qt.OpenHandCursor))
        super().mouseReleaseEvent(poEvent)

# ********************************************************************************************************
# ***** Public Constructor : Class SDC_ToolButton
# ********************************************************************************************************
class SDC_ToolButton(QToolButton):
    m_oIcon : QIcon = None
    m_oIconHover : QIcon = None
    def __init__(self, poParent):
        #print("SDC_ToolButton::__init__")
        super().__init__(poParent)
        self.m_oIcon = QIcon()
        self.m_oIconHover = QIcon()

    # ********************************************************************************************************
    # ***** Public Method : Class SDC_ToolButton
    # ********************************************************************************************************
    def vSetIcons(self, oIcon, oIconHover):
        #print("SDC_ToolButton::vSetIcons")
        self.m_oIcon = oIcon
        self.m_oIconHover = oIconHover

    # ********************************************************************************************************
    # ***** Protected Event : Class SDC_ToolButton
    # ********************************************************************************************************
    def event(self, poEvent) -> bool:
        #print("SDC_ToolButton::event")
        if poEvent.type() == QEvent.HoverEnter:
            self.setIcon(self.m_oIconHover)
            poEvent.accept()
            return True
        elif poEvent.type() == QEvent.Leave:
            self.setIcon(self.m_oIcon)
            poEvent.accept()
            return True

        return super().event(poEvent)
        

# ********************************************************************************************************
# ***** Public Constructor : Class SDC_PushButton
# ********************************************************************************************************
class SDC_PushButton(QPushButton):
    type = Enum('type', ['DEFAULT', 'START', 'STOP'])
    m_eType : type = None
    m_sStyle : str = ""
    m_sStyleOrig : str = ""
    m_sStyleHover : str = ""
    
    def __init__(self, poParent):
        #print("SDC_PushButton::__init__")
        super().__init__(poParent)
        self.m_eType = self.type.DEFAULT
        self.m_sStyle      = "QPushButton { color: #FFFFFF; background-color: #007ACD }"
        self.m_sStyleOrig  = "QPushButton { color: #FFFFFF; background-color: #007ACD }"
        self.m_sStyleHover = "QPushButton { color: white; background-color: #333333 }"

        self.setStyleSheet(self.m_sStyle)

    # ********************************************************************************************************
    # ***** Public Method : Class SDC_PushButton
    # ********************************************************************************************************
    def vSetType(self, eType):
        #print("SDC_PushButton::vSetType")
        if eType == self.type.START:
            self.m_eType = eType
            self.m_sStyle = "QPushButton { color: #FFF; border: 2px solid #555; border - radius: 50px; border - style: outset; background: qradialgradient( cx : 0.3, cy : -0.4, fx : 0.3, fy : -0.4, radius : 1.35, stop : 0 green, stop: 1 #01F001); padding: 5px;}"
            self.setText("  START  ")
        elif eType == self.type.STOP:
            self.m_eType = eType
            self.m_sStyle = "QPushButton { color: #FFF; border: 2px solid #555; border - radius: 50px; border - style: outset; background: qradialgradient( cx : 0.3, cy : -0.4, fx : 0.3, fy : -0.4, radius : 1.35, stop : 0 white, stop: 1 red); padding: 5px;}"
            self.setText("  STOP  ")
        else:
            self.m_eType = self.type.DEFAULT
            self.m_sStyle = self.m_sStyleOrig

        self.setStyleSheet(self.m_sStyle)
    
    def eGetType(self):
        #print("SDC_PushButton::eGetType")
        return self.m_eType

    # ********************************************************************************************************
    # ***** Protected Event : Class SDC_PushButton
    # ********************************************************************************************************
    def event(self, poEvent) -> bool:
        #print("SDC_PushButton::event")
        if poEvent.type() == QEvent.HoverEnter:
            self.vSetHoverEffect(True)
            poEvent.accept()
            return True
        elif poEvent.type() == QEvent.Leave:
            self.vSetHoverEffect(False)
            poEvent.accept()
            return True

        return super().event(poEvent)

    # ********************************************************************************************************
    # ***** Protected Method : Class SDC_PushButton
    # ********************************************************************************************************
    def vSetHoverEffect(self, bState : bool):
        #print("SDC_PushButton::vSetHoverEffect")
        if not self.isEnabled():
            return

        if bState:
            self.setStyleSheet(self.m_sStyleHover)
        else:
            self.setStyleSheet(self.m_sStyle)

# ********************************************************************************************************