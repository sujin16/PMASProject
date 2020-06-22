#-*- coding: utf-8 -*-


import sys
import os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox,QApplication,QFileDialog,QMainWindow,QPlainTextEdit,QAbstractItemView, QTableWidgetItem
from PyQt5.QtGui import  QIntValidator ,QDoubleValidator
from PyQt5 import uic, QtGui,QtCore
import logging
import math
import socket
import serial
import signal
import threading

from module.wifiConnectDialog import Ui_wifiDialog
from module.uartConnectDialog import Ui_uartDialog
from module.socketServer import socketServer
from module.interpolation import Main
from module.test_interpolation import Main as test_Main
from datetime import datetime

PMPSUI = '../ui_Files/PMPS.ui'


class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class Mode():
    no_connect = 0
    wifi_connect = 1
    uart_connect = 2
    wifi_success_connect = 3
    uart_success_connect = 4


class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self,None)
        uic.loadUi(PMPSUI, self)

        self.mylogger = logging.getLogger("my")
        self.mylogger.setLevel(logging.INFO)

        #wifi mode
        self.ip = ''
        self.ip_port = 9002 # ip port 는 9002로 고정되어 있음.
        self.socket_server = ''
        self.socket_client =''

        # uart mode
        self.uart_port = ''
        self.uart_baud =''
        self.serial_server = ''
        self.line = []  # 라인 단위로 데이터 가져올 리스트 변수
        self.list = []
        self.meaBool = False
        self.exitThread = False  # 쓰레드 종료용 변수
        self.serial_thread =None

        self.mode_check =Mode.no_connect

        self.machine_number ='1' # 하드코딩
        self.folder_name = os.getcwd() # 현재 파일 경로
        self.file_name = datetime.today().strftime("%Y.%m.%d.%H.%m.") + '(Machine' + self.machine_number + ').txt'

        self.theme =''

        self.result_Array =[]
        self.mpa_grid_array =[]
        self.max_grid_array =[]
        self.table_array = []

        self.location=[0,0,0] # location[0] = x 좌표, location[1] = y 좌표, location[2] = z 좌표,

        self.statusbar.showMessage('Ready')

        self.initLog()
        self.initConnect()
        self.initBrowser()
        self.initSetting()

        self.radionClick = True
        self.mpa_radioButton.clicked.connect(self.radioButtonClicked)
        self.max_radioButton.clicked.connect(self.radioButtonClicked)

    def initConnect(self):
        self.connect_comboBox.activated[str].connect(self.comboBoxFunction)
        self.connect_pushButton.clicked.connect(self.ConnectFunction)

    def comboBoxFunction(self,text):

        if 'Wifi' in text :
            self.openWifiDialog()
            self.mode_check = Mode.wifi_connect
        elif 'Uart' in text:
            self.openUartDialog()
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
            self.ip = ui.ip_lineEdit.text()
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
            self.mylogger.info(
                ' ' +ui.port_comboBox.currentText()
                +' ' + ui.rate_comboBox.currentText())

            self.uart_port = ui.port_comboBox.currentText()
            self.uart_baud = int(ui.rate_comboBox.currentText())
            return ui.port_comboBox.currentText()
        else:
            self.mylogger.warning('Again uart address')
            self.uart_port = None
            self.uart_baud = None
            return None

    def ConnectFunction(self):

        if self.mode_check == Mode.no_connect:
            print('no connect')
            QMessageBox.about(self, "Warning", "Select Mode")

        if self.mode_check == Mode.wifi_success_connect:
            msg = QMessageBox()
            msg.setWindowTitle('Info')
            msg.setText('Already have a Server Connected. \n Do you want Disconnect ?')
            msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
            result = msg.exec_()


            if result == QMessageBox.Ok:
                self.socket_client.close()
                self.mylogger.info('socket client close')
                self.socket_server.close()
                self.mylogger.info('socket server close')
                self.statusbar.showMessage('Disconnect.. ')
                self.mode_check = Mode.no_connect

        if self.mode_check == Mode.uart_success_connect:
            msg = QMessageBox()
            msg.setWindowTitle('Info')
            msg.setText('Already have a Server Connected. \n Do you want Disconnect ?')
            msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
            result = msg.exec_()

            if result == QMessageBox.Ok:
                print('Ok')
                self.serial_server.close()

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
                    # self.socket_server.settimeout(1) # timeout for listening
                    # self.socket_server.setdefaulttimeout(60)
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
                    self.socket_server.listen()  # max 1 client : 한개의 클라이언트만 받는다.
                    self.mylogger.info('server socket listen')
                    self.statusbar.showMessage('server socket listen')
                except Exception as e:
                    print(e)
                    self.mylogger.error(e)
                    self.mode_check = Mode.no_connect

                stopped = False
                while not stopped:
                    try:
                        self.socket_client, addr = self.socket_server.accept()
                        print(addr)
                        self.mylogger.info('Connected by' + addr[0] + str(addr[1]))
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
                        stopped = True
                        self.mylogger.info('Connection Successful')
                        self.statusbar.showMessage('Connection Successful')
                        self.mode_check = Mode.wifi_success_connect


        if self.mode_check == Mode.uart_connect:
            if self.uart_port:
                try:
                    signal.signal(signal.SIGINT, self.handler)
                    self.serial_server  = serial.Serial(self.uart_port,self.uart_baud, timeout=0)
                    print(self.serial_server)
                    self.mylogger.info('Connection Successful')
                    self.statusbar.showMessage('Connection Successful')
                    self.mode_check = Mode.uart_success_connect
                except Exception as e:
                    print(e)
                    self.mylogger.error(e)
            else:
                QMessageBox.about(self, "Warming", "Again uart address")



    # thread 종료용 signal function
    def handler(self, signum, frame):
        self.exitThread = True

    # 데이터 처리 함수
    def parsing_data(self, data):
        tmp = ''.join(data)  # list로 들어 온 것을 스트링으로 합침
        print(tmp)
        return tmp

    # 측정된 데이터 센서 값 출력 하고 list에 저장하기
    def sensor_parsing_data(self, data):
        tmp = ''.join(data)
        print(tmp)
        self.list.append(tmp)
        return tmp

    # 본 thread
    def readThread(self, ser):

        # thread가 종료될때까지
        # Serial interfacce :  data를 stream으로 바꿔서 (직렬화,serialization) 한 번에 1 bit 씩 전송

        join_path = os.path.join(self.folder_name,self.file_name)
        print(join_path)
        f= open(join_path,'w')
        self.mylogger.info(self.file_name+' Open Write')
        while not self.exitThread:
            # 데이터가 있있다면
            for c in ser.read():
                self.line.append(chr(c))  # (integer, 0 ~ 255)를 ASCII character로 변환하고 line에 추가한다.

                if c == 10:  # ASCII의 개행문자 10
                    readystr = self.parsing_data(self.line)

                    if (readystr == 'Transmission done\r\n'):
                        self.meaBool = False
                        f.close()
                        self.mylogger.info(self.file_name + ' Close')
                        #self.serial_thread.join()
                        self.exitThread = True
                        #print(self.serial_thread.is_alive())
                        self.test_drawGraph()
                        return None

                    if (self.meaBool):
                        readystr = self.sensor_parsing_data(self.line)
                        if (readystr == '\n'):
                            continue;
                        else:
                            #print('file write')
                            readystr = readystr.strip('\n')
                            f.write(readystr)

                    if (readystr == 'Transmission Start\r\n'):
                        self.meaBool = True

                    del self.line[:]  # line list 원소를 다 지워버린다.



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
        #create Validator
        self.onlyInt = QIntValidator()
        self.onlyDouble = QDoubleValidator()

        #restrict user input in QLineEdit
        self.z_min_lineEdit.setValidator(self.onlyInt)
        self.z_max_lineEdit.setValidator(self.onlyInt)
        self.interval_lineEdit.setValidator(self.onlyInt)
        self.sample_rate_lineEdit.setValidator(self.onlyDouble)
        self.p_value_lineEdit.setValidator(self.onlyDouble)

        # add button click event
        self.start_pushButton.clicked.connect(self.startGrah)

    def checkSetting(self):
        print('check ')
        return (self.front_senserNum_spinBox.value() >0 and
                self.end_senserNum_spinBox.value() > 0 and
                len(self.z_min_lineEdit.text()) > 0 and
                len(self.z_max_lineEdit.text()) >0  and
                len(self.p_value_lineEdit.text()) and
                len(self.sample_rate_lineEdit.text()) >0)

    def startGrah(self):
        if os.path.isdir(self.folder_name) == False:
            QMessageBox.about(self, "Warning", "Not Exist Directory")
            return  None

        if self.checkSetting() == False:
            QMessageBox.about(self, "Warning", "Check Setting")
            return  None

        if self.mode_check == Mode.no_connect:
            QMessageBox.about(self, "Warning", "Disconnect Server")
            return None

        elif self.mode_check == Mode.wifi_success_connect:
            #원래는 uart connect 처럼 , file을 저장한 후  draw graph
            self.drawGraph()

        elif self.mode_check == Mode.uart_success_connect:
            # serial 읽을 thread 생성
            self.mylogger.info('Read sensor data')
            self.serial_thread = threading.Thread(target=self.readThread, args=(self.serial_server,))

            self.serial_thread.start()
            print(self.serial_thread)


    def drawGraph(self):
        self.mylogger.info('draw 3d chart')

        self.result_Array = []  # 초기화
        print(self.result_Array)

        result_array = Main(
            front_num=int(self.front_senserNum_spinBox.text()),
            end_num=int(self.end_senserNum_spinBox.text()),
            theme=self.theme_comboBox.currentText(),
            min_bound=int(self.z_min_lineEdit.text()),
            max_bound=int(self.z_max_lineEdit.text()),
            interval=int(self.interval_lineEdit.text()),
            p_value=float(self.p_value_lineEdit.text()),
            extr_interval=30,
            model=self.algorithm_comboBox.currentText(),  # 'nearest', 'kriging', 'neural'
            method=self.method_comboBox.currentText()  # gradation contour rotate wireframe
        )

        title = str(self.algorithm_comboBox.currentText())
        theme = str(self.theme_comboBox.currentText())
        self.result_Array = result_array  # self.result_Array[0] = mpa_grid_array , self.result_Array[1] = max_grid_array

        self.radionClick = True
        self.radioButtonClicked(title, theme, self.result_Array)
        self.mpa_radioButton.clicked.connect(
            lambda: self.radioButtonClicked(title, theme, self.result_Array))
        self.max_radioButton.clicked.connect(
            lambda: self.radioButtonClicked(title, theme, self.result_Array))


    def test_drawGraph(self):
        self.mylogger.info('draw 3d chart')

        self.result_Array = []  # 초기화
        print(self.result_Array)

        result_array = test_Main(
            front_num=int(self.front_senserNum_spinBox.text()),
            end_num=int(self.end_senserNum_spinBox.text()),
            theme=self.theme_comboBox.currentText(),
            min_bound=int(self.z_min_lineEdit.text()),
            max_bound=int(self.z_max_lineEdit.text()),
            interval=int(self.interval_lineEdit.text()),
            p_value=float(self.p_value_lineEdit.text()),
            extr_interval=30,
            model=self.algorithm_comboBox.currentText(),  # 'nearest', 'kriging', 'neural'
            method=self.method_comboBox.currentText(),  # gradation contour rotate wireframe
            folder_path=self.folder_name,
            file_name=self.file_name
        )

        self.title = str(self.algorithm_comboBox.currentText())
        self.theme = str(self.theme_comboBox.currentText())

        self.mpa_grid_array = result_array['MPA']
        self.max_grid_array = result_array['MAX']

        print(result_array)
        self.radionClick = True



    def radioButtonClicked(self):

        def onclick(event):

            try:

                self.location[0] = math.ceil(event.xdata)
                self.location[1] = math.ceil(event.ydata)

                if self.mpa_radioButton.isChecked():
                    # 10 * 10 이런식으로 grid_array shape을 바꾸어 주기.
                    self.table_array = self.mpa_grid_array[3].reshape(int(self.front_senserNum_spinBox.text()),
                                                                      int(self.end_senserNum_spinBox.text()))
                elif self.max_radioButton.isChecked():
                    self.table_array = self.max_grid_array[3].reshape(int(self.front_senserNum_spinBox.text()),
                                                                      int(self.end_senserNum_spinBox.text()))

                self.location[2] = self.table_array[self.location[0] - 1][self.location[1] - 1]

                locaton_str = 'x :' + str(self.location[0]) + 'y :' + str(self.location[1]) + ' z : ' + str(+self.location[2])
                print(locaton_str)
                self.statusbar.showMessage(locaton_str)

                self.resultTable()
            except Exception:
                self.statusbar.showMessage('again click  point')

            '''
            print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
                  ('double' if event.dblclick else 'single', event.button,
                   event.x, event.y, event.xdata, event.ydata))
            '''


        if len(self.mpa_grid_array) > 0:

            if self.radionClick:
                self.MplWidget.canvas.mpl_connect('button_press_event', onclick)
                self.radionClick = False

            if self.mpa_radioButton.isChecked():
                self.MplWidget.canvas.axes.clear()
                self.MplWidget.canvas.axes.contourf(self.mpa_grid_array[0], self.mpa_grid_array[1], self.mpa_grid_array[2], cmap=self.theme)
                self.MplWidget.canvas.axes.set_title("MPA "+self.title, pad=30)
                self.MplWidget.canvas.draw()

            elif self.max_radioButton.isChecked():
                self.MplWidget.canvas.axes.clear()
                self.MplWidget.canvas.axes.contourf(self.max_grid_array[0], self.max_grid_array[1], self.max_grid_array[2], cmap=self.theme)
                self.MplWidget.canvas.axes.set_title("MAX "+self.title, pad=30)
                self.MplWidget.canvas.draw()

        else:
            print('no array')



    def resultTable(self):
        print('==== resultTable  ====')
        self.table_size_comboBox.activated[str].connect(self.makeTable)

    # - >  for_num으로 변환을 해준다. - >
    def makeTable(self,text):
        print('make Table')

        size =0

        if '3' in text or 3 == text:
            self.tableWidget.clear()
            size = 3
        elif '5' in text or 5 == text:
            self.tableWidget.clear()
            size = 5

        #self.tableWidget.resizeColumnsToContents()
        #self.tableWidget.resizeRowsToContents()


        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.setColumnCount(size)
        self.tableWidget.setRowCount(size*2)

        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setVisible(False)

        for_num = int(float((size - 1) / 2))

        value_list = [[0 for i in range(size)] for j in range(size)]
        index_list = [[0 for i in range(size)] for j in range(size)]

        row_index =0
        colum_index = 0

        for i in range(self.location[0] - for_num, self.location[0]+ for_num + 1):
            for j in range(self.location[1] - for_num, self.location[1] + for_num + 1):

                index_list[row_index][colum_index] = str(i+1) + "X" + str(j+1)
                try:
                    value_list[row_index][colum_index]  = self.table_array[i][j]
                except IndexError:
                    value_list[row_index][colum_index] = '-'

                colum_index = colum_index +1

            colum_index =0
            row_index = row_index +1


        for i in range(0,size*2):
            for j in range(0,size):
                if i % 2== 0:
                    self.tableWidget.setItem(i,j,QTableWidgetItem(index_list[i//2][j]))
                    self.tableWidget.item(i,j).setBackground(QtGui.QColor(233, 233, 233))
                    self.tableWidget.item(i, j).setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
                    self.tableWidget.item(i,j).setFont(QtGui.QFont("Arial",8))

                else:
                    value = value_list[i//2][j]
                    print(str(i//2)  + " : " + str(j))
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(value)))
                    self.tableWidget.item(i, j).setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
                    self.tableWidget.item(i, j).setFont(QtGui.QFont("Arial", 11))

                    if value ==self.location[2] :
                        self.tableWidget.item(i, j).setBackground(QtGui.QColor(1,1,1))
                        self.tableWidget.item(i, j).setForeground(QtGui.QColor(255, 255, 255))


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