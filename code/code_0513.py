#-*- coding: utf-8 -*-


import sys
import os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox,QApplication,QFileDialog,QMainWindow,QPlainTextEdit,QAbstractItemView, QTableWidgetItem
from PyQt5 import uic, QtGui,QtCore
import logging
import math
import socket
import socketserver

from module.wifiConnectDialog import Ui_wifiDialog
from module.uartConnectDialog import Ui_uartDialog
from module.socketServer import socketServer
from module.interpolation import Main
from module.valueZ import num as randomZ_num

PMPSUI = '../ui_Files/PMPS.ui'


class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class Mode():
    no_connect =0
    wifi_connect = 1
    uart_connect =2
    wifi_succeess_connect =3
    uart_success_connect =4


class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self,None)
        uic.loadUi(PMPSUI, self)

        self.mylogger = logging.getLogger("my")
        self.mylogger.setLevel(logging.INFO)

        self.ip = ''
        self.ip_port = 9002 # ip port 는 9002로 고정되어 있음.
        self.uart_port =''
        self.socket_server = ''
        self.socket_client =''
        self.serial_server = ''
        self.mode_check =Mode.no_connect
        self.folder_name = os.getcwd() # 현재 파일 경로
        self.file_name = ''


        self.theme =''

        self.result_Array =[]
        self.mpa_grid_array =[]
        self.max_grid_array =[]

        self.location=[0,0,0] # location[0] = x 좌표, location[1] = y 좌표, location[2] = z 좌표,
        self.radionClick =False
        self.statusbar.showMessage('Ready')

        self.initLog()
        self.initConnect()
        self.initBrowser()
        self.initSetting()

    def initConnect(self):
        self.connect_comboBox.activated[str].connect(self.comboBoxFunction)
        self.connect_pushButton.clicked.connect(self.ConnectFunction)

    def comboBoxFunction(self,text):

        if 'Wifi' in text :
            self.ip= self.openWifiDialog()
            print(self.ip)
            self.mode_check = Mode.wifi_connect
        elif 'Uart' in text:
            self.uart_port = self.openUartDialog()
            print(self.uart_port)
            self.mode_check = Mode.uart_connect
        else:
            self.mode_check = Mode.no_connect


    #https://stackoverflow.com/questions/58655570/how-to-access-qlineedit-in-qdialog 참고
    def openWifiDialog(self):
        Dialog = QtWidgets.QDialog(self)
        ui = Ui_wifiDialog()
        ui.setupUi(Dialog)
        resp = Dialog.exec_()

        if resp == QtWidgets.QDialog.Accepted:
            self.mylogger.info('IP : ' + ui.ip_lineEdit.text())
            return ui.ip_lineEdit.text()
        else:
            self.mylogger.warning('Again ip address')
            return None


    def openUartDialog(self):
        Dialog = QtWidgets.QDialog(self)
        ui = Ui_uartDialog()
        ui.setupUi(Dialog)
        resp = Dialog.exec_()

        if resp == QtWidgets.QDialog.Accepted:
            self.mylogger.info('PORT : ' +ui.port_comboBox.currentText())
            return ui.port_comboBox.currentText()
        else:
            self.mylogger.warning('Again uart address')
            return None

    def ConnectFunction(self):

        if self.mode_check == Mode.no_connect:
            QMessageBox.about(self, "Warning", "Select Mode")

        if self.mode_check ==Mode.wifi_succeess_connect:
            print('wifi success connect')
            msg = QMessageBox()
            msg.setWindowTitle('Info')
            msg.setText('Already have a Server Connected. \n Do you want Disconnect ?')
            msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
            result = msg.exec_()

            if result == QMessageBox.Cancel:
                print('Cancel')
            elif result == QMessageBox.Ok:
                self.socket_client.close()
                self.mylogger.info('serial client close')
                self.socket_server.close()
                self.mylogger.info('serial server close')
                self.statusbar.showMessage('Disconnect.. ')
                self.mode_check = Mode.no_connect

        if self.mode_check ==Mode.uart_succeess_connect:
            print('uart success connect')
            msg = QMessageBox()
            msg.setWindowTitle('Info')
            msg.setText('Already have a Server Connected. \n Do you want Disconnect ?')
            msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
            result = msg.exec_()

            if result == QMessageBox.Cancel:
                print('Cancel')
            elif result == QMessageBox.Ok:
                self.socket_client.close()
                self.mylogger.info('serial client close')
                self.socket_server.close()
                self.mylogger.info('serial server close')
                self.statusbar.showMessage('Disconnect.. ')
                self.mode_check = Mode.no_connect

        if self.mode_check == Mode.wifi_connect:
            if self.ip != socket.gethostbyname(socket.getfqdn()):
                QMessageBox.about(self, "Warming", "Again ip address")

            elif self.ip == socket.gethostbyname(socket.getfqdn()):

                try:
                    self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.mylogger.info('create server socket')
                    self.statusbar.showMessage('create server socket')
                    self.socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    #self.socket_server.settimeout(1) # timeout for listening
                    #self.socket_server.setdefaulttimeout(60)
                except Exception as e:
                    print(e)
                    self.mylogger.error(e)
                    self.mode_check = Mode.no_connect

                try:
                    self.socket_server.bind((self.ip, self.ip_port))
                    self.mylogger.info('server socket bind. ' + self.ip + ':' + str(self.ip_port))
                    self.statusbar.showMessage('server socket bind. ' + self.ip + ':' + str(self.ip_port))
                except Exception as e:
                    print(e)
                    self.mylogger.error(e)
                    self.mode_check = Mode.no_connect

                try:
                    self.socket_server.listen() # max 1 client : 한개의 클라이언트만 받는다.
                    self.mylogger.info('server socket listen')
                    self.statusbar.showMessage('server socket listen')
                except Exception as e:
                    print(e)
                    self.mylogger.error(e)
                    self.mode_check = Mode.no_connect

                stopped =False
                while not stopped:
                    try:
                        self.socket_client, addr = self.socket_server.accept()
                        print(addr)
                        self.mylogger.info('Connected by'+ addr[0]+ str(addr[1]))
                    except socket.timeout as e:
                        print(e)
                        self.mylogger.error(e)
                        self.mode_check = Mode.no_connect
                        pass
                    except Exception as e:
                        print(e)
                        self.mylogger.error(e)
                        self.mode_check = Mode.no_connect
                    else:
                        stopped =True
                        self.mylogger.info('Connection Successful')
                        self.statusbar.showMessage('Connection Successful')
                        self.mode_check = Mode.wifi_succeess_connect


        elif self.mode_check == Mode.uart_connect:
            if self.uart_port:
                self.mylogger.info('Connection Successful')
                self.statusbar.showMessage('Connection Successful')
                self.mode_check = Mode.succeess_connect
            else:
                QMessageBox.about(self, "Warming", "Again uart address")



    def initBrowser(self):
        self.browser_lineEdit.setText(self.folder_name)
        self.browser_lineEdit.textChanged.connect(self.sync_browerEdit)
        self.save_pushButton.clicked.connect(self.OnOpenDocument)

    def sync_browerEdit(self,text):
        print(text)
        self.folder_name = text

    def OnOpenDocument(self):
        self.folder_name = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if self.folder_name:
            self.browser_lineEdit.setText(self.folder_name)
        else:
            if(self.folder_name ==''):
                QMessageBox.about(self, "Warning", "Select Folder")

    def initLog(self):
        logTextBox = QTextEditLogger(self)
        logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(logTextBox)
        self.verticalLayout_3.addWidget(logTextBox.widget)


    def initSetting(self):
        self.start_pushButton.clicked.connect(self.startGrah)

    def startGrah(self):

        print(self.mode_check)  # no :0 wifi : 1 uart :2 wifi_success :3 uart_success :4
        #print(os.path.isdir(self.folder_name))

        if os.path.isdir(self.folder_name) == False :
            QMessageBox.about(self, "Warning", "Not Exist Directory")

        if self.mode_check == Mode.no_connect:
            QMessageBox.about(self, "Warning", "Disconnect Server")

        elif self.mode_check == Mode.wifi_succeess_connect:
            print('======= start Graph ========== ')
            #randomZ_num =0 # 초기화 test
            print("num " + str(randomZ_num))

            self.result_Array =[] #초기화
            print(self.result_Array)

            result_array = Main(
                front_num=10,
                end_num=10,
                theme=str(self.theme_comboBox.currentText()),
                min_bound=0,
                max_bound=110,
                interval=1000,
                p_value=0.5,
                extr_interval=30,
                model='nearest',  # 'nearest', 'kriging', 'neural'
                method='gradation',  # gradation contour rotate wireframe
                )

            title = str(self.algorithm_comboBox.currentText())
            theme = str(self.theme_comboBox.currentText())
            self.result_Array = result_array # self.result_Array[0] = mpa_grid_array , self.result_Array[1] = max_grid_array

            self.radionClick = True
            self.radioButtonClicked(title, theme, self.result_Array)
            self.mpa_radioButton.clicked.connect(lambda: self.radioButtonClicked(title, theme, self.result_Array))
            self.max_radioButton.clicked.connect(lambda: self.radioButtonClicked(title, theme, self.result_Array))

        elif self.mode_check == Mode.uart_succeess_connect:
            print(self.mode_check)  # no :0 wifi : 1 uart :2 wifi_success :3 uart_success :4

            print('======= start Graph ========== ')
            # randomZ_num =0 # 초기화 test
            print("num " + str(randomZ_num))

            self.result_Array = []  # 초기화
            print(self.result_Array)

            result_array = Main(
                front_num=10,
                end_num=10,
                theme=str(self.theme_comboBox.currentText()),
                min_bound=0,
                max_bound=110,
                interval=1000,
                p_value=0.5,
                extr_interval=30,
                model='nearest',  # 'nearest', 'kriging', 'neural'
                method='gradation',  # gradation contour rotate wireframe
            )

            title = str(self.algorithm_comboBox.currentText())
            theme = str(self.theme_comboBox.currentText())
            self.result_Array = result_array  # self.result_Array[0] = mpa_grid_array , self.result_Array[1] = max_grid_array

            self.radionClick = True
            self.radioButtonClicked(title, theme, self.result_Array)
            self.mpa_radioButton.clicked.connect(lambda: self.radioButtonClicked(title, theme, self.result_Array))
            self.max_radioButton.clicked.connect(lambda: self.radioButtonClicked(title, theme, self.result_Array))




            # if self.mode_check == Mode.no_connect:
        #     QMessageBox.about(self, "Warning", "Disconnect Server")
        # elif self.browser =='':
        #     QMessageBox.about(self, "Warning", "Select Folder")
        # else:
        #     print(self.mode_check)  # no :0 wifi : 1 uart :2 wifi_success :3 uart_success :4
        #
        #     print('======= start Graph ========== ')
        #     #randomZ_num =0 # 초기화 test
        #     print("num " + str(randomZ_num))
        #
        #     self.result_Array =[] #초기화
        #     print(self.result_Array)
        #
        #     result_array = Main(
        #         front_num=10,
        #         end_num=10,
        #         theme=str(self.theme_comboBox.currentText()),
        #         min_bound=0,
        #         max_bound=110,
        #         interval=1000,
        #         p_value=0.5,
        #         extr_interval=30,
        #         model='nearest',  # 'nearest', 'kriging', 'neural'
        #         method='gradation',  # gradation contour rotate wireframe
        #         )
        #
        #     title = str(self.algorithm_comboBox.currentText())
        #     theme = str(self.theme_comboBox.currentText())
        #     self.result_Array = result_array # self.result_Array[0] = mpa_grid_array , self.result_Array[1] = max_grid_array
        #
        #     self.radionClick = True
        #     self.radioButtonClicked(title, theme, self.result_Array)
        #     self.mpa_radioButton.clicked.connect(lambda: self.radioButtonClicked(title, theme, self.result_Array))
        #     self.max_radioButton.clicked.connect(lambda: self.radioButtonClicked(title, theme, self.result_Array))


    def radioButtonClicked(self,title,theme,result_Array):


        def onclick(event):

            '''
            print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
                  ('double' if event.dblclick else 'single', event.button,
                   event.x, event.y, event.xdata, event.ydata))
            '''

            self.location[0] = math.ceil(event.xdata)
            self.location[1] = math.ceil(event.ydata)

            locaton_str = 'x :' + str(self.location[0]) + 'y :' + str(self.location[1])
            print(locaton_str)
            self.statusbar.showMessage(locaton_str)

        if len(result_Array)>0:

            if self.radionClick:
                self.MplWidget.canvas.mpl_connect('button_press_event', onclick)
                self.radionClick = False

            if self.mpa_radioButton.isChecked():
                self.MplWidget.canvas.axes.clear()
                self.MplWidget.canvas.axes.contourf(result_Array[0], result_Array[1], result_Array[2], cmap=theme)
                self.MplWidget.canvas.axes.set_title("MPA "+ title, pad=30)
                self.MplWidget.canvas.draw()
                print('mpa')
                self.resultTable()

            elif self.max_radioButton.isChecked():
                self.MplWidget.canvas.axes.clear()
                self.MplWidget.canvas.axes.contourf(result_Array[0], result_Array[1], result_Array[2], cmap=theme)
                self.MplWidget.canvas.axes.set_title("MAX "+ title, pad=30)
                self.MplWidget.canvas.draw()
                print('max ')
                self.resultTable()

        else:
            print('no array')




    def resultTable(self):
        self.table_size_comboBox.activated[str].connect(self.makeTable)

    def makeTable(self,text):
        size =0

        if '3' in text:
            self.tableWidget.clear()
            size = 3
        elif '5' in text:
            self.tableWidget.clear()
            size = 5

        #self.tableWidget.resizeColumnsToContents()
        #self.tableWidget.resizeRowsToContents()


        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.setColumnCount(size)
        self.tableWidget.setRowCount(size*2)

        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setVisible(False)

        for i in range(0,size*2):
            for j in range(0,size):
                if i % 2== 0:
                    self.tableWidget.setItem(i,j,QTableWidgetItem(str(i) +" X " +str(j)))
                    self.tableWidget.item(i,j).setBackground(QtGui.QColor(233, 233, 233))
                    self.tableWidget.item(i, j).setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
                    self.tableWidget.item(i,j).setFont(QtGui.QFont("Arial",8))

                else:
                    self.tableWidget.setItem(i, j, QTableWidgetItem("a"))
                    self.tableWidget.item(i, j).setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
                    self.tableWidget.item(i, j).setFont(QtGui.QFont("Arial", 11))

        self.tableWidget.item((size//2)*2+1,(size//2)*2-1).setBackground(QtGui.QColor(1,1,1))
        self.tableWidget.item((size//2)*2+1,(size//2)*2-1).setForeground(QtGui.QColor(255, 255, 255))

        #표 안에 글자는 수정할 수 없다.
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)



'''
QApplicaton : 기본적으로 프로그램을 실행시키는 역할
sys.argv : 현재 소스코드에 대한 절대 경로를 나타낸다. 즉 현재.파일이름.py의 절대경로를 나타낸다.
QApplicaton class의 instance을 생성할 떄,
'''
app = QApplication(sys.argv)
main_window = MainWindow()
main_window.show()
app.exec_() #QApplication().exec_()  : 프로그램을 Event Loop(무한 루프)로 진입시키는 method