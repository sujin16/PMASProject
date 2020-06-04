# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wifiConnect.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

FORMAT = [
    {"name": "IP ADDRESS", "format": "000.000.000.000;"}
]


class Ui_wifiDialog(object):

    def setupUi(self, wifiDialog):
        wifiDialog.setObjectName("wifiDialog")
        wifiDialog.resize(420, 275)
        wifiDialog.setMinimumSize(QtCore.QSize(420, 275))
        wifiDialog.setMaximumSize(QtCore.QSize(420, 275))
        self.main_wifi_frame = QtWidgets.QFrame(wifiDialog)
        self.main_wifi_frame.setGeometry(QtCore.QRect(10, 10, 391, 251))
        self.main_wifi_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.main_wifi_frame.setFrameShadow(QtWidgets.QFrame.Plain)
        self.main_wifi_frame.setObjectName("main_wifi_frame")
        self.wifi_label = QtWidgets.QLabel(self.main_wifi_frame)
        self.wifi_label.setGeometry(QtCore.QRect(160, 10, 56, 12))
        self.wifi_label.setObjectName("wifi_label")
        self.wifi_label_2 = QtWidgets.QLabel(self.main_wifi_frame)
        self.wifi_label_2.setGeometry(QtCore.QRect(40, 50, 21, 16))
        self.wifi_label_2.setObjectName("wifi_label_2")
        self.save_pushButton = QtWidgets.QPushButton(self.main_wifi_frame)
        self.save_pushButton.setGeometry(QtCore.QRect(130, 220, 121, 23))
        self.save_pushButton.setObjectName("save_pushButton")
        self.sub_wifi_frame = QtWidgets.QFrame(self.main_wifi_frame)
        self.sub_wifi_frame.setGeometry(QtCore.QRect(10, 80, 361, 121))
        self.sub_wifi_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.sub_wifi_frame.setFrameShadow(QtWidgets.QFrame.Plain)
        self.sub_wifi_frame.setObjectName("sub_wifi_frame")
        self.ssid_lineEdit = QtWidgets.QLineEdit(self.sub_wifi_frame)
        self.ssid_lineEdit.setGeometry(QtCore.QRect(110, 50, 211, 20))
        self.ssid_lineEdit.setObjectName("ssid_lineEdit")
        self.wifi_label_5 = QtWidgets.QLabel(self.sub_wifi_frame)
        self.wifi_label_5.setGeometry(QtCore.QRect(30, 90, 61, 16))
        self.wifi_label_5.setObjectName("wifi_label_5")
        self.password_lineEdit = QtWidgets.QLineEdit(self.sub_wifi_frame)
        self.password_lineEdit.setGeometry(QtCore.QRect(110, 90, 211, 20))
        self.password_lineEdit.setObjectName("password_lineEdit")
        self.wifi_label_3 = QtWidgets.QLabel(self.sub_wifi_frame)
        self.wifi_label_3.setGeometry(QtCore.QRect(120, 10, 121, 16))
        self.wifi_label_3.setObjectName("wifi_label_3")
        self.wifi_label_4 = QtWidgets.QLabel(self.sub_wifi_frame)
        self.wifi_label_4.setGeometry(QtCore.QRect(30, 50, 31, 16))
        self.wifi_label_4.setObjectName("wifi_label_4")
        self.ip_lineEdit = QtWidgets.QLineEdit(self.main_wifi_frame)
        self.ip_lineEdit.setGeometry(QtCore.QRect(100, 50, 231, 20))
        self.ip_lineEdit.setObjectName("ip_lineEdit")

        #ip adrress setting
        self.ip_lineEdit = QtWidgets.QLineEdit(self.main_wifi_frame)
        self.ip_lineEdit.setCursorPosition(0)
        self.ip_lineEdit.setGeometry(QtCore.QRect(100, 50, 231, 20))
        self.ip_lineEdit.setObjectName("ip_lineEdit")
        self.ip_lineEdit.clear()
        self.ip_lineEdit.setFocus()
        self.ip_lineEdit.setInputMask('000.000.000.000;_')

        self.retranslateUi(wifiDialog)
        QtCore.QMetaObject.connectSlotsByName(wifiDialog)
        self.save_pushButton.clicked.connect(lambda  : self.saveAddress(wifiDialog))

    def retranslateUi(self, wifiDialog):
        _translate = QtCore.QCoreApplication.translate
        wifiDialog.setWindowTitle(_translate("wifiDialog", "Coonect Mode"))
        self.wifi_label.setText(_translate("wifiDialog", "Wifi mode"))
        self.wifi_label_2.setText(_translate("wifiDialog", "IP"))
        self.save_pushButton.setText(_translate("wifiDialog", "Save"))
        self.wifi_label_5.setText(_translate("wifiDialog", "Password"))
        self.wifi_label_3.setText(_translate("wifiDialog", "Send wifi information"))
        self.wifi_label_4.setText(_translate("wifiDialog", "SSID"))


    def saveAddress(self,wifiDialog):
        ip = self.ip_lineEdit.text()
        if len(ip) ==3:
            wifiDialog.reject()
        else:
            wifiDialog.accept()


'''

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    wifiDialog = QtWidgets.QDialog()
    ui = Ui_wifiDialog()
    ui.setupUi(wifiDialog)
    wifiDialog.show()
    sys.exit(app.exec_())


'''
