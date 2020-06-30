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
from module.interpolation import Main
from module.test_interpolation import Main as test_Main
from module.test_interpolation_0630 import Main as today_Main

import datetime
from threading import Thread

PMPSUI = '../ui_Files/PMPS.ui'

conn = None
main_window =None

#Log 창 만드는 class
class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)

# connect mode class
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
        self.startClick =False
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
        self.file_name =None

        self.theme =''
        self.finish_line =0
        self.mpa_grid_array =[]
        self.max_grid_array =[]
        self.table_array = []

        self.location=[0,0,0] # location[0] = x 좌표, location[1] = y 좌표, location[2] = z 좌표,

        self.mplWidgetClick=''
        self.radionClick = True
        self.mpa_radioButton.clicked.connect(self.radioButtonClicked)
        self.max_radioButton.clicked.connect(self.radioButtonClicked)


        self.statusbar.showMessage('Ready')
        self.initLog()
        self.initConnect()
        self.initBrowser()
        self.initSetting()


    # connect 창 설정 함수(1)
    def initConnect(self):
        self.connect_comboBox.activated[str].connect(self.comboBoxFunction)
        self.connect_pushButton.clicked.connect(self.ConnectFunction)

    # connect 창 설정 함수(2)
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
    # connect 창 설정 함수(3)
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

    # connect 창 설정 함수(4)
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

    # connect 창 설정 함수(5) : mode에 따라서 연결을 잘 할 수 있도록 도와줌.
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
                global conn
                conn.close()
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
            if not (self.ip is None):
                QMessageBox.about(self, "Warming", "Again ip address")

            else :
                serverThread = ServerThread(main_window)
                serverThread.start()

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

    # uart 연결 데이터 처리 함수
    def parsing_data(self, data):
        tmp = ''.join(data)  # list로 들어 온 것을 스트링으로 합침
        #print(tmp)
        return tmp

    # 측정된 데이터 센서 값 출력 하고 list에 저장하기
    def sensor_parsing_data(self, data):
        tmp = ''.join(data)
        #print(tmp)
        self.list.append(tmp)
        return tmp

    # readThread : 들어온 값을 읽어주는 함수
    def readThread(self, ser):

        # thread가 종료될때까지
        # Serial interfacce :  data를 stream으로 바꿔서 (직렬화,serialization) 한 번에 1 bit 씩 전송

        f  =None

        while not self.exitThread:
           try:
               # 데이터가 있있다면
                 for c in ser.read():
                   self.line.append(chr(c))  # (integer, 0 ~ 255)를 ASCII character로 변환하고 line에 추가한다.

                   if c == 10:  # ASCII의 개행문자 10
                       readystr = self.parsing_data(self.line)


                       if (readystr == 'Transmission done\r\n'):
                           if not (f is None):
                               self.meaBool = False
                               f.close()
                               self.mylogger.info(self.file_name + ' Close')
                               # print(self.serial_thread.is_alive())
                               print('===== done test drawGraph =====')
                               self.test_drawGraph()
                               #self.today_drawGraph()
                               # self.wifi_drawGraph()
                               # self.exitThread = True
                               # return None

                       if (self.meaBool):
                           readystr = self.sensor_parsing_data(self.line)
                           if (readystr == '\n'):
                               continue;
                           else:
                               if not (f is None):
                                   # print('file write')
                                   readystr = readystr.strip('\n')
                                   f.write(readystr)
                                   self.finish_line = self.finish_line + 1

                       if (readystr == 'Transmission Start\r\n'):
                           self.meaBool = True
                           print('===== start =====')
                           self.file_name = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M.%S") + '(Machine' + self.machine_number + ').txt'
                           join_path = os.path.join(self.folder_name, self.file_name)
                           print(join_path)
                           self.mylogger.info(self.file_name + ' Open Write')
                           f = open(join_path, 'w')
                           self.radionClick = False

                       del self.line[:]  # line list 원소를 다 지워버린다.

           except Exception as e:
               #중간에 연결이 끊어졌을 경우
               print(e)

    # browser 창 설정 함수(1)
    def initBrowser(self):
        self.browser_lineEdit.setText(self.folder_name)
        self.browser_lineEdit.textChanged.connect(self.sync_browerEdit)
        self.save_pushButton.clicked.connect(self.OnOpenDocument)

    # browser 창 설정 함수(2) : browser_lineEdit 값이 바뀔때마다, folder_name을 자동으로 바꿔줌
    def sync_browerEdit(self,text):
        #print(text)
        self.folder_name = text

    # browser 창 설정 함수(3)
    def OnOpenDocument(self):
        self.folder_name = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if self.folder_name:
            self.browser_lineEdit.setText(self.folder_name)
        else:
            if(self.folder_name ==''):
                QMessageBox.about(self, "Warning", "Select Folder")

    # log 창 설정 함수
    def initLog(self):
        logTextBox = QTextEditLogger(self)
        logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(logTextBox)
        self.verticalLayout_3.addWidget(logTextBox.widget)

    # setting 창 설정 함수(1)
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

    # setting 창 설정 함수(2)
    def checkSetting(self):
        print('check ')
        return (self.front_senserNum_spinBox.value() >0 and
                self.end_senserNum_spinBox.value() > 0 and
                len(self.z_min_lineEdit.text()) > 0 and
                len(self.z_max_lineEdit.text()) >0  and
                len(self.p_value_lineEdit.text()) and
                len(self.sample_rate_lineEdit.text()) >0)

    # setting 창 설정 함수(3) : 그래프를 그리기 전에 여러 error 가 날 수있는 상황을 체크해주고, mode에 따라서 데이터를 받아들임.
    def startGrah(self):
        #browser path가 실제 존재하는 path 인지
        if os.path.isdir(self.folder_name) == False:
            QMessageBox.about(self, "Warning", "Not Exist Directory")
            return  None

        #setting 창에서 입력을 제대로 했는지
        if self.checkSetting() == False:
            QMessageBox.about(self, "Warning", "Check Setting")
            return  None

        # 연결이 되지 않았을 때
        if self.mode_check == Mode.no_connect:
            QMessageBox.about(self, "Warning", "Disconnect Server")
            return None
        #mode가 wifi 일때,
        elif self.mode_check == Mode.wifi_success_connect :
            print('succuess wifi')
            #원래는 uart connect 처럼 , file을 저장한 후  draw graph
            self.startClick =True

        #mode가 uart 일때,
        elif self.mode_check == Mode.uart_success_connect:
            # serial 읽을 thread 생성
            self.mylogger.info('Read sensor data')
            self.serial_thread = threading.Thread(target=self.readThread, args=(self.serial_server,))

            self.serial_thread.start()
            print(self.serial_thread)


    # setting 창 설정 함수(4) : 임시 graph 그리는 함수
    def wifi_drawGraph(self):

        self.mylogger.info('draw 3d chart')

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

        self.title = str(self.algorithm_comboBox.currentText())
        self.theme = str(self.theme_comboBox.currentText())

        self.mpa_grid_array = result_array
        self.max_grid_array = result_array

        self.radionClick = True

    # setting 창 설정 함수(4) : interpolation.py 을 실행시키고 종료되면, mpa_grid_array와 max_grid_array을 받아옴.
    def test_drawGraph(self):
        self.mylogger.info('draw 3d chart')

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
            folder_name=self.folder_name,
            file_name=self.file_name
        )

        self.title = str(self.algorithm_comboBox.currentText())
        self.theme = str(self.theme_comboBox.currentText())

        #result_array의 type이 dict 임.
        self.mpa_grid_array = result_array['MPA']
        self.max_grid_array = result_array['MAX']


        self.radionClick = True

    def today_drawGraph(self):
        self.mylogger.info('draw 3d chart')

        result_array = today_Main(
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
            folder_name=self.folder_name,
            file_name=self.file_name
        )

        self.title = str(self.algorithm_comboBox.currentText())
        self.theme = str(self.theme_comboBox.currentText())

        # result_array의 type이 dict 임.
        self.mpa_grid_array = result_array['MPA']
        self.max_grid_array = result_array['MAX']

        self.radionClick = True


    # setting 창 설정 함수(5) : mpa, max 을 선택한 것에 따라 등고선 그래프르 그려줌. 그리고 등고선을 클릭하면 좌표값을 보여주고 resultTable() 실행
    def radioButtonClicked(self):

        #e등고선 그래프를 클릭할 경우 실행
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
                #onclick이 이미 되었는지 안되었는지를 판단하기 위해 self.mplWidgetClick 을 사용
                self.mplWidgetClick = self.MplWidget.canvas.mpl_connect('button_press_event', onclick)
                print('mplWidget Click : ' + str(self.mplWidgetClick))
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

    # table 창 설정 함수(1) : makeTable()을 실행시키는 함수
    def resultTable(self):
        print('==== resultTable  ====')
        #print(self.serial_thread.is_alive())

        self.table_size_comboBox.activated[str].connect(self.makeTable)


    # table 창 설정 함수(2) : tableWidget을 만드는 창
    def makeTable(self,text):
        print('==== make Table ====')

        #size 변수 선언
        size =0

        if '3' in text or 3 == text:
            self.tableWidget.clear()
            size = 3
        elif '5' in text or 5 == text:
            self.tableWidget.clear()
            size = 5

        #tableWidget 설정
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.setColumnCount(size)
        self.tableWidget.setRowCount(size*2)

        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setVisible(False)


        for_num = int(float((size - 1) / 2))
        # index list와 index list 만들고, 변수 선언
        value_list = [[0 for i in range(size)] for j in range(size)]
        index_list = [[0 for i in range(size)] for j in range(size)]

        row_index =0
        colum_index = 0

        # value_list, colum_list 에 self.table_array에 있는 값들을 나누어서 넣기
        for i in range(self.location[0] - for_num, self.location[0]+ for_num + 1):
            for j in range(self.location[1] - for_num, self.location[1] + for_num + 1):

                index_list[row_index][colum_index] = str(i+1) + " X " + str(j+1)
                try:
                    value_list[row_index][colum_index]  = self.table_array[i][j]
                except IndexError:
                    value_list[row_index][colum_index] = '-'

                colum_index = colum_index +1

            colum_index =0
            row_index = row_index +1


        #table.item에 좌표(index), 값(value) 배경색 등 등 넣기
        for i in range(0,size*2):
            for j in range(0,size):
                if i % 2== 0:
                    self.tableWidget.setItem(i,j,QTableWidgetItem(index_list[i//2][j]))
                    self.tableWidget.item(i,j).setBackground(QtGui.QColor(233, 233, 233))
                    self.tableWidget.item(i, j).setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
                    self.tableWidget.item(i,j).setFont(QtGui.QFont("Arial",8))

                else:
                    value = value_list[i//2][j]
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(value)))
                    self.tableWidget.item(i, j).setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
                    self.tableWidget.item(i, j).setFont(QtGui.QFont("Arial", 11))

                    if value ==self.location[2] :
                        self.tableWidget.item(i, j).setBackground(QtGui.QColor(1,1,1))
                        self.tableWidget.item(i, j).setForeground(QtGui.QColor(255, 255, 255))

        #표 안에 글자는 수정 X
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)



#socket 통신 serverThread
class ServerThread(Thread):
    def __init__(self, m_window):
        Thread.__init__(self)
        self.window = m_window

    def run(self):
        BUFFER_SIZE = 20
        tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcpServer.bind((self.window.ip, self.window.ip_port))
        threads = []

        tcpServer.listen(4)
        while True:
            print("Multithreaded server : Waiting for connections from TCP clients...")
            self.window.mylogger.info('Multithreaded server : Waiting for connections from TCP clients...')

            global conn
            (conn, (ip, port)) = tcpServer.accept()
            print('wifi connect sucesses')
            self.window.mylogger.info('wifi connect sucesses')
            self.window.mode_check = Mode.wifi_success_connect

            newthread = ClientThread(ip, port, self.window)

            newthread.start()

            threads.append(newthread)

        for t in threads:
            t.join()

#socket 통신 clientThread
class ClientThread(Thread):
    def __init__(self, ip, port, window):
        Thread.__init__(self)
        self.window = window
        self.ip = ip
        self.port = port
        print(self.window.mode_check)
        print("New server socket thread started for " + ip + ":" + str(port))
        self.window.mylogger.info("New server socket thread started for " + ip + ":" + str(port))

    def run(self):
        print('client thread run')

        f = None

        while True:
            # (conn, (self.ip,self.port)) = serverThread.tcpServer.accept()
            global conn
            data = conn.recv(2048)

            if len(data) > 0 and self.window.startClick:
                data_str =data.decode("utf-8")
                if 'Measure file' in data_str :
                    self.window.file_name = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M.%S") + '(Machine' + self.machine_number + ').txt'
                    join_path = os.path.join(self.window.folder_name, self.window.file_name)
                    print(join_path)
                    self.window.mylogger.info(self.window.file_name + ' Open Write')

                    f = open(join_path, 'w')

                elif 'Result'  in data_str:
                    if not (f is None) :
                        print('============ finish ============')
                        f.close()
                        print('============ file close ============')

                        # 그래프 그리기 : 기기가 생기면  self.window.test_drawGraph() 로 실행 해보세요.
                        self.window.wifi_drawGraph()
                else:
                    if not (f is None):
                        # window.chat.append(data.decode("utf-8"))
                        data_str = data_str.strip('\n')
                        print(data_str)
                        f.write(data_str)



'''
QApplicaton : 기본적으로 프로그램을 실행시키는 역할
sys.argv : 현재 소스코드에 대한 절대 경로를 나타낸다. 즉 현재.파일이름.py의 절대경로를 나타낸다.
QApplicaton class의 instance을 생성할 떄,
'''

app = QApplication(sys.argv)
main_window = MainWindow()
main_window.show()
app.exec_() #QApplication().exec_()  : 프로그램을 Event Loop(무한 루프)로 진입시키는 method