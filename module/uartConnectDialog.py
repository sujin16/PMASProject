# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'uartConnect.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_uartDialog(object):

    def setupUi(self, uartDialog):
        uartDialog.setObjectName("Dialog")
        uartDialog.resize(420, 200)
        uartDialog.setMinimumSize(QtCore.QSize(420, 200))
        uartDialog.setMaximumSize(QtCore.QSize(420, 200))
        self.uart_frame = QtWidgets.QFrame(Dialog)
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
        self.port_lineEdit = QtWidgets.QLineEdit(self.uart_frame)
        self.port_lineEdit.setGeometry(QtCore.QRect(100, 50, 231, 20))
        self.port_lineEdit.setObjectName("port_lineEdit")
        self.rate_lineEdit = QtWidgets.QLineEdit(self.uart_frame)
        self.rate_lineEdit.setGeometry(QtCore.QRect(100, 90, 231, 20))
        self.rate_lineEdit.setObjectName("rate_lineEdit")
        self.rate_label = QtWidgets.QLabel(self.uart_frame)
        self.rate_label.setGeometry(QtCore.QRect(40, 90, 31, 16))
        self.rate_label.setObjectName("rate_label")

        self.retranslateUi(uartDialog)
        QtCore.QMetaObject.connectSlotsByName(uartDialog)

        self.save_pushButton.clicked.connect(lambda: self.saveAddress(uartDialog))

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Connect Mode"))
        self.wifi_label_6.setText(_translate("Dialog", "Uart mode"))
        self.port_label.setText(_translate("Dialog", "Port"))
        self.save_pushButton.setText(_translate("Dialog", "Save"))
        self.rate_label.setText(_translate("Dialog", "Rate"))



    def saveAddress(self,uartDialog):
        port = self.port_lineEdit
        if len(port) ==3:
            uartDialog.reject()
        else:
            uartDialog.accept()


'''
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_uartDialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

'''


