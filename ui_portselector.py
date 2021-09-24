# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'port_selector.ui'
##
## Created by: Qt User Interface Compiler version 6.1.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore


class Ui_PortSelector(object):
    def setupUi(self, PortSelector):
        if not PortSelector.objectName():
            PortSelector.setObjectName(u"PortSelector")
        PortSelector.resize(400, 100)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PortSelector.sizePolicy().hasHeightForWidth())
        PortSelector.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(PortSelector)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.portSelectorComboBox = QComboBox(PortSelector)
        self.portSelectorComboBox.setObjectName(u"portSelectorComboBox")

        self.verticalLayout.addWidget(self.portSelectorComboBox)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.refreshButton = QPushButton(PortSelector)
        self.refreshButton.setObjectName(u"refreshButton")
        self.refreshButton.setAutoDefault(False)
        self.refreshButton.setFlat(False)

        self.horizontalLayout_2.addWidget(self.refreshButton)

        self.connectButton = QPushButton(PortSelector)
        self.connectButton.setObjectName(u"connectButton")

        self.horizontalLayout_2.addWidget(self.connectButton)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.connectedLabel = QLabel(PortSelector)
        self.connectedLabel.setObjectName(u"connectedLabel")
        self.connectedLabel.setTextInteractionFlags(Qt.NoTextInteraction)

        self.horizontalLayout.addWidget(self.connectedLabel)


        self.retranslateUi(PortSelector)

        self.refreshButton.setDefault(False)


        QMetaObject.connectSlotsByName(PortSelector)
    # setupUi

    def retranslateUi(self, PortSelector):
        PortSelector.setWindowTitle(QCoreApplication.translate("PortSelector", u"PortSelector", None))
        self.portSelectorComboBox.setPlaceholderText(QCoreApplication.translate("PortSelector", u"Port w\u00e4hlen", None))
        self.refreshButton.setText(QCoreApplication.translate("PortSelector", u"Erneuern", None))
        self.connectButton.setText(QCoreApplication.translate("PortSelector", u"Verbinden", None))
        self.connectedLabel.setText(QCoreApplication.translate("PortSelector", u"Nicht verbunden", None))
    # retranslateUi
