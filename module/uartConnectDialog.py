# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'uartConnect.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
import serial.tools.list_ports
from PyQt5.QtSerialPort import QSerialPort

class Ui_uartDialog(object):

    BAUDRATES = (
        QSerialPort.Baud1200,
        QSerialPort.Baud2400,
        QSerialPort.Baud4800,
        QSerialPort.Baud9600,
        QSerialPort.Baud19200,
        QSerialPort.Baud38400,
        QSerialPort.Baud57600,
        QSerialPort.Baud115200,
    )

    def setupUi(self, uartDialog):
        uartDialog.setObjectName("uartDialog")
        uartDialog.resize(420, 200)
        uartDialog.setMinimumSize(QtCore.QSize(420, 200))
        uartDialog.setMaximumSize(QtCore.QSize(420, 200))
        self.uart_frame = QtWidgets.QFrame(uartDialog)
        self.uart_frame.setGeometry(QtCore.QRect(10, 10, 391, 171))
        self.uart_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.uart_frame.setFrameShadow(QtWidgets.QFrame.Plain)
        self.uart_frame.setObjectName("uart_frame")
        self.wifi_label_6 = QtWidgets.QLabel(self.uart_frame)
        self.wifi_label_6.setGeometry(QtCore.QRect(160, 10, 61, 16))
        self.wifi_label_6.setObjectName("wifi_label_6")
        self.port_label = QtWidgets.QLabel(self.uart_frame)
        self.port_label.setGeometry(QtCore.QRect(40, 50, 31, 16))
        self.port_label.setObjectName("port_label")
        self.save_pushButton = QtWidgets.QPushButton(self.uart_frame)
        self.save_pushButton.setGeometry(QtCore.QRect(130, 140, 121, 23))
        self.save_pushButton.setObjectName("save_pushButton")
        self.rate_label = QtWidgets.QLabel(self.uart_frame)
        self.rate_label.setGeometry(QtCore.QRect(40, 90, 31, 16))
        self.rate_label.setObjectName("rate_label")
        self.port_comboBox = QtWidgets.QComboBox(self.uart_frame)
        self.port_comboBox.setGeometry(QtCore.QRect(100, 50, 231, 22))
        self.port_comboBox.setObjectName("port_comboBox")
        self.rate_comboBox = QtWidgets.QComboBox(self.uart_frame)
        self.rate_comboBox.setGeometry(QtCore.QRect(100, 90, 231, 22))
        self.rate_comboBox.setObjectName("rate_comboBox")

        # 연결 가능한 port comboBox에 추가하기
        comlist = serial.tools.list_ports.comports()
        self.port_comboBox.addItem('')
        for element in comlist:
            self.port_comboBox.addItem(element.device)

        self.rate_comboBox.insertItems(0, [str(x) for x in self.BAUDRATES])

        self.retranslateUi(uartDialog)
        QtCore.QMetaObject.connectSlotsByName(uartDialog)

        self.save_pushButton.clicked.connect(lambda: self.saveAddress(uartDialog))


    def retranslateUi(self, uartDialog):
        _translate = QtCore.QCoreApplication.translate
        uartDialog.setWindowTitle(_translate("Dialog", "Connect Mode"))
        self.wifi_label_6.setText(_translate("Dialog", "Uart mode"))
        self.port_label.setText(_translate("Dialog", "Port"))
        self.save_pushButton.setText(_translate("Dialog", "Save"))
        self.rate_label.setText(_translate("Dialog", "Rate"))


    def saveAddress(self,uartDialog):
        uartDialog.accept()


'''
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

'''

