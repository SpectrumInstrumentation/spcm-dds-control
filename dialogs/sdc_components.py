from enum import Enum
import logging

from PyQt5.QtWidgets import QDial, QToolButton, QPushButton
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import Qt, QEvent, qDebug


class SDC_Dial(QDial):
    def __init__(self, poParent):
        logging.debug("SDC_Dial::__init__")
        super().__init__(poParent)
        self.setCursor(QCursor(Qt.OpenHandCursor))

    def mousePressEvent(self, poEvent):
        #logging.debug("SDC_Dial::mousePressEvent")
        self.setCursor(QCursor(Qt.ClosedHandCursor))
        super().mousePressEvent(poEvent)

    def mouseReleaseEvent(self, poEvent):
        #logging.debug("SDC_Dial::mouseReleaseEvent")
        self.setCursor(QCursor(Qt.OpenHandCursor))
        super().mouseReleaseEvent(poEvent)


class SDC_ToolButton(QToolButton):
    m_oIcon : QIcon = None
    m_oIconHover : QIcon = None
    def __init__(self, poParent):
        logging.debug("SDC_ToolButton::__init__")
        super().__init__(poParent)
        self.m_oIcon = QIcon()
        self.m_oIconHover = QIcon()

    def vSetIcons(self, oIcon, oIconHover):
        logging.debug("SDC_ToolButton::vSetIcons")
        self.m_oIcon = oIcon
        self.m_oIconHover = oIconHover

    def event(self, poEvent) -> bool:
        #logging.debug("SDC_ToolButton::event")
        if poEvent.type() == QEvent.HoverEnter:
            self.setIcon(self.m_oIconHover)
            poEvent.accept()
            return True
        elif poEvent.type() == QEvent.Leave:
            self.setIcon(self.m_oIcon)
            poEvent.accept()
            return True

        return super().event(poEvent)
        

class SDC_PushButton(QPushButton):
    type = Enum('type', ['DEFAULT', 'START', 'STOP', 'WRITE'])
    m_eType : type = None
    m_sStyle : str = ""
    m_sStyleOrig : str = ""
    m_sStyleHover : str = ""
    
    def __init__(self, parent):
        logging.debug("SDC_PushButton::__init__")
        super().__init__(parent)
        self.m_eType = self.type.DEFAULT
        self.m_sStyle      = "QPushButton { color: #FFFFFF; background-color: #007ACD }"
        self.m_sStyleOrig  = "QPushButton { color: #FFFFFF; background-color: #007ACD }"
        self.m_sStyleHover = "QPushButton { color: white; background-color: #333333 }"

        self.setStyleSheet(self.m_sStyle)

    def vSetType(self, eType):
        logging.debug("SDC_PushButton::vSetType")
        if eType == self.type.START:
            self.m_eType = eType
            self.m_sStyle = "QPushButton { color: #FFFFFF; border: 2px solid #555; border - radius: 50px; border - style: outset; background: qradialgradient( cx : 0.3, cy : -0.4, fx : 0.3, fy : -0.4, radius : 1.35, stop : 0 green, stop: 1 #01F001); padding: 5px;}"
            self.setText("  START  ")
        elif eType == self.type.STOP:
            self.m_eType = eType
            self.m_sStyle = "QPushButton { color: #FFFFFF; border: 2px solid #555; border - radius: 50px; border - style: outset; background: qradialgradient( cx : 0.3, cy : -0.4, fx : 0.3, fy : -0.4, radius : 1.35, stop : 0 white, stop: 1 red); padding: 5px;}"
            self.setText("  STOP  ")
        elif eType == self.type.WRITE:
            self.m_eType = eType
            self.m_sStyle = "QPushButton { color: #FFFFFF; border: 2px solid #555; border - radius: 50px; border - style: outset; background: qradialgradient( cx : 0.3, cy : -0.4, fx : 0.3, fy : -0.4, radius : 1.35, stop : 0 black, stop: 1 #FA792C); padding: 5px;}"
            self.m_sStyleHover = "QPushButton { color: #FFFFFF; border: 2px solid #555; border - radius: 50px; border - style: outset; background-color: #333333; padding: 5px;}"
            self.setText("Write To Queue")
        else:
            self.m_eType = self.type.DEFAULT
            self.m_sStyle = self.m_sStyleOrig

        self.setStyleSheet(self.m_sStyle)
    
    def eGetType(self):
        logging.debug("SDC_PushButton::eGetType")
        return self.m_eType

    def event(self, poEvent) -> bool:
        #logging.debug("SDC_PushButton::event")
        if poEvent.type() == QEvent.HoverEnter:
            self.vSetHoverEffect(True)
            poEvent.accept()
            return True
        elif poEvent.type() == QEvent.Leave:
            self.vSetHoverEffect(False)
            poEvent.accept()
            return True

        return super().event(poEvent)

    def vSetHoverEffect(self, bState : bool):
        logging.debug("SDC_PushButton::vSetHoverEffect")
        if not self.isEnabled():
            return

        if bState:
            self.setStyleSheet(self.m_sStyleHover)
        else:
            self.setStyleSheet(self.m_sStyle)