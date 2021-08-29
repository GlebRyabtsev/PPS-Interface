# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'standard_mode.ui'
##
## Created by: Qt User Interface Compiler version 6.1.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore


class Ui_StandardMode(object):
    def setupUi(self, StandardMode):
        if not StandardMode.objectName():
            StandardMode.setObjectName(u"StandardMode")
        StandardMode.resize(317, 444)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(StandardMode.sizePolicy().hasHeightForWidth())
        StandardMode.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(StandardMode)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.channel_label = QLabel(StandardMode)
        self.channel_label.setObjectName(u"channel_label")
        self.channel_label.setLayoutDirection(Qt.LeftToRight)
        self.channel_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.channel_label)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_3)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.set_voltage_lcd = QLCDNumber(StandardMode)
        self.set_voltage_lcd.setObjectName(u"set_voltage_lcd")
        sizePolicy.setHeightForWidth(self.set_voltage_lcd.sizePolicy().hasHeightForWidth())
        self.set_voltage_lcd.setSizePolicy(sizePolicy)
        self.set_voltage_lcd.setMinimumSize(QSize(150, 48))
        palette = QPalette()
        brush = QBrush(QColor(0, 0, 255, 216))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        brush1 = QBrush(QColor(0, 0, 0, 63))
        brush1.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Disabled, QPalette.WindowText, brush1)
        self.set_voltage_lcd.setPalette(palette)
        self.set_voltage_lcd.setAutoFillBackground(False)
        self.set_voltage_lcd.setFrameShape(QFrame.NoFrame)
        self.set_voltage_lcd.setSmallDecimalPoint(False)
        self.set_voltage_lcd.setDigitCount(6)
        self.set_voltage_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.set_voltage_lcd.setProperty("value", 12.000000000000000)
        self.set_voltage_lcd.setProperty("intValue", 12)

        self.horizontalLayout_5.addWidget(self.set_voltage_lcd)

        self.label_2 = QLabel(StandardMode)
        self.label_2.setObjectName(u"label_2")
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(48)
        font.setBold(False)
        self.label_2.setFont(font)
        self.label_2.setTextInteractionFlags(Qt.NoTextInteraction)

        self.horizontalLayout_5.addWidget(self.label_2)


        self.verticalLayout_3.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_7)

        self.change_voltage_check_box = QCheckBox(StandardMode)
        self.change_voltage_check_box.setObjectName(u"change_voltage_check_box")
        self.change_voltage_check_box.setCheckable(False)

        self.horizontalLayout_8.addWidget(self.change_voltage_check_box)


        self.verticalLayout_3.addLayout(self.horizontalLayout_8)


        self.horizontalLayout_6.addLayout(self.verticalLayout_3)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_4)


        self.verticalLayout.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_5)

        self.real_voltage_lcd = QLCDNumber(StandardMode)
        self.real_voltage_lcd.setObjectName(u"real_voltage_lcd")
        sizePolicy.setHeightForWidth(self.real_voltage_lcd.sizePolicy().hasHeightForWidth())
        self.real_voltage_lcd.setSizePolicy(sizePolicy)
        self.real_voltage_lcd.setMinimumSize(QSize(150, 48))
        palette1 = QPalette()
        brush2 = QBrush(QColor(255, 0, 0, 216))
        brush2.setStyle(Qt.SolidPattern)
        palette1.setBrush(QPalette.Active, QPalette.WindowText, brush2)
        palette1.setBrush(QPalette.Inactive, QPalette.WindowText, brush2)
        palette1.setBrush(QPalette.Disabled, QPalette.WindowText, brush1)
        self.real_voltage_lcd.setPalette(palette1)
        self.real_voltage_lcd.setAutoFillBackground(False)
        self.real_voltage_lcd.setFrameShape(QFrame.NoFrame)
        self.real_voltage_lcd.setSmallDecimalPoint(False)
        self.real_voltage_lcd.setDigitCount(6)
        self.real_voltage_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.real_voltage_lcd.setProperty("value", 12.000000000000000)
        self.real_voltage_lcd.setProperty("intValue", 12)

        self.horizontalLayout_4.addWidget(self.real_voltage_lcd)

        self.label_3 = QLabel(StandardMode)
        self.label_3.setObjectName(u"label_3")
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setFont(font)
        self.label_3.setTextInteractionFlags(Qt.NoTextInteraction)

        self.horizontalLayout_4.addWidget(self.label_3)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_6)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.current_lcd = QLCDNumber(StandardMode)
        self.current_lcd.setObjectName(u"current_lcd")
        sizePolicy.setHeightForWidth(self.current_lcd.sizePolicy().hasHeightForWidth())
        self.current_lcd.setSizePolicy(sizePolicy)
        self.current_lcd.setMinimumSize(QSize(150, 48))
        palette2 = QPalette()
        palette2.setBrush(QPalette.Active, QPalette.WindowText, brush2)
        palette2.setBrush(QPalette.Inactive, QPalette.WindowText, brush2)
        palette2.setBrush(QPalette.Disabled, QPalette.WindowText, brush1)
        self.current_lcd.setPalette(palette2)
        self.current_lcd.setAutoFillBackground(False)
        self.current_lcd.setFrameShape(QFrame.NoFrame)
        self.current_lcd.setFrameShadow(QFrame.Raised)
        self.current_lcd.setDigitCount(6)
        self.current_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.current_lcd.setProperty("value", 1.000000000000000)
        self.current_lcd.setProperty("intValue", 1)

        self.horizontalLayout.addWidget(self.current_lcd)

        self.label = QLabel(StandardMode)
        self.label.setObjectName(u"label")
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setFont(font)
        self.label.setTextInteractionFlags(Qt.NoTextInteraction)

        self.horizontalLayout.addWidget(self.label)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setSizeConstraint(QLayout.SetMinimumSize)
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.coarse_radio_button = QRadioButton(StandardMode)
        self.coarse_radio_button.setObjectName(u"coarse_radio_button")
        sizePolicy.setHeightForWidth(self.coarse_radio_button.sizePolicy().hasHeightForWidth())
        self.coarse_radio_button.setSizePolicy(sizePolicy)
        self.coarse_radio_button.setChecked(True)

        self.verticalLayout_2.addWidget(self.coarse_radio_button)

        self.fine_radio_button = QRadioButton(StandardMode)
        self.fine_radio_button.setObjectName(u"fine_radio_button")
        sizePolicy.setHeightForWidth(self.fine_radio_button.sizePolicy().hasHeightForWidth())
        self.fine_radio_button.setSizePolicy(sizePolicy)

        self.verticalLayout_2.addWidget(self.fine_radio_button)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)


        self.horizontalLayout_3.addLayout(self.verticalLayout_2)

        self.dial = QDial(StandardMode)
        self.dial.setObjectName(u"dial")
        sizePolicy.setHeightForWidth(self.dial.sizePolicy().hasHeightForWidth())
        self.dial.setSizePolicy(sizePolicy)
        self.dial.setMinimumSize(QSize(150, 150))
        self.dial.setMaximum(10)
        self.dial.setSingleStep(1)
        self.dial.setPageStep(1)
        self.dial.setInvertedAppearance(False)
        self.dial.setInvertedControls(False)
        self.dial.setWrapping(True)
        self.dial.setNotchesVisible(False)

        self.horizontalLayout_3.addWidget(self.dial)


        self.verticalLayout.addLayout(self.horizontalLayout_3)


        self.retranslateUi(StandardMode)

        QMetaObject.connectSlotsByName(StandardMode)
    # setupUi

    def retranslateUi(self, StandardMode):
        StandardMode.setWindowTitle(QCoreApplication.translate("StandardMode", u"StandardMode", None))
        self.channel_label.setText(QCoreApplication.translate("StandardMode", u"Kanal 1", None))
        self.label_2.setText(QCoreApplication.translate("StandardMode", u"V", None))
        self.change_voltage_check_box.setText(QCoreApplication.translate("StandardMode", u"Connected", None))
        self.label_3.setText(QCoreApplication.translate("StandardMode", u"V", None))
        self.label.setText(QCoreApplication.translate("StandardMode", u"A", None))
        self.coarse_radio_button.setText(QCoreApplication.translate("StandardMode", u"Coarse", None))
        self.fine_radio_button.setText(QCoreApplication.translate("StandardMode", u"Fine", None))
    # retranslateUi

