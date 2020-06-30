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


PMASUI = '../ui_Files/PMPS.ui' # ui 파일 읽는 경로


conn = None  # wifi connect 할 때 사용되는 변수
main_window =None  # wifi connect 현재 윈도운의 매개변수 선언


class QTextEditLogger(logging.Handler): #Log 창 만드는 class
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)

class Mode(): # connect mode class
    no_connect = 0
    wifi_connect = 1
    uart_connect = 2
    wifi_success_connect = 3
    uart_success_connect = 4


class MainWindow(QMainWindow): #메인 윈도우 만드는 class

    def __init__(self): # 메인 윈도우 초기화 class __init__
        QMainWindow.__init__(self,None)
        uic.loadUi(PMASUI, self)

        self.mylogger = logging.getLogger("my")
        self.mylogger.setLevel(logging.INFO)

        #wifi mode 일 때 사용되는 변수
        self.ip = ''
        self.ip_port = 9002 # ip port 는 9002로 고정되어 있음.
        self.startClick =False # mode가  wifi_success_connect 가 되면 이 사실을 clientThread에게 알리기 위해 만들어진 변수


        # uart mode 일 때 사용되는 변수
        self.uart_port = ''
        self.uart_baud =''
        self.serial_server = ''
        self.line = []  # 라인 단위로 데이터 가져올 리스트 변수
        self.list = []
        self.meaBool = False # 데이터를 읽을 때, start , end 을 알기 위해 사용되는 BOOL 변수
        self.exitThread = False  # 쓰레드 종료용 BOOL 변수
        self.serial_thread =None  # 만들어진 쓰레드

        self.mode_check =Mode.no_connect # 현재 MODE을 초기화

        self.machine_number ='1'  #하드코딩
        self.folder_name = os.getcwd() # 현재 파일 경로
        self.file_name =None  #데이터가 들어오면 현재 시간이 파일 이름이 됨

        self.theme ='' #setting  창에서 선택한 theme. 등고선에서 같은 theme을 사용하기 위해 변수를 만듬

        self.mpa_grid_array =[] #drawGraph을 가 종료되고 반환되는 mpa array
        self.max_grid_array =[] #drawGraph을 가 종료되고 반환되는 max array
        self.table_array = [] # mpa 혹은 max  버튼을 클릭했을때, 선택된 array을 저장하여 표에 보여주기 위해 만든 변수

        self.location=[0,0,0] # location[0] = x 좌표, location[1] = y 좌표, location[2] = z 좌표,

        self.mplWidgetClick='' #mpl click  event가 몇번 실행됬는지 알기 위해 만든 변수

        self.radionClick = True # drawGraph가 종료되고 나서 radio 버튼에 click event가 생성될 수 있도록 하기 위한 BOOL 변수.
        self.mpa_radioButton.clicked.connect(self.radioButtonClicked)
        self.max_radioButton.clicked.connect(self.radioButtonClicked)


        self.statusbar.showMessage('Ready') # 현재 상태를 statusBar에 Ready 라고 보여줌
        self.initLog() # log 창 셋팅
        self.initConnect() # connect 창 셋팅
        self.initBrowser() # browser 창 셋팅
        self.initSetting() # setting  창 셋팅


    def initConnect(self): # connect 창 설정 함수(1) : mode 콤보 박스와 , connect 버튼 클릭 이벤트 만들기
        self.connect_comboBox.activated[str].connect(self.comboBoxFunction)
        self.connect_pushButton.clicked.connect(self.ConnectFunction)


    def comboBoxFunction(self,text): # connect 창 설정 함수(2) : mode 콤보박스 이벤트 함수
        if 'Wifi' in text :
            self.openWifiDialog()
            self.mode_check = Mode.wifi_connect
        elif 'Uart' in text:
            self.openUartDialog()
            self.mode_check = Mode.uart_connect
        else:
            self.mode_check = Mode.no_connect


    #https://stackoverflow.com/questions/58655570/how-to-access-qlineedit-in-qdialog 참고

    def openWifiDialog(self):  # connect 창 설정 함수(3) : mode 콤보 박스에서 wifi을 선택했을 때 실행되는 함수. 입력된 ip 주소를 반환한다.
        Dialog = QtWidgets.QDialog(self)
        ui = Ui_wifiDialog()
        ui.setupUi(Dialog)
        resp = Dialog.exec_()

        if resp == QtWidgets.QDialog.Accepted:
            self.mylogger.info('IP : ' + ui.ip_lineEdit.text())
            self.ip = ui.ip_lineEdit.text()
            return ui.ip_lineEdit.text()
        else:  #wifi dialog에서 ip 주소를 잘 못 가지고 왔을 경우, reject가 반환됬을 경우
            self.mylogger.warning('Again ip address')
            return None


    def openUartDialog(self): # connect 창 설정 함수(4) : mode 콤보 박스에서 uart을 선택했을 때 실행되는 함수. 선택한 포트를 반환한다.
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

        else:   # uart dialog에서 port 주소를 잘 못 가지고 왔을 경우, reject가 반환됬을 경우
            self.mylogger.warning('Again uart address')
            self.uart_port = None
            self.uart_baud = None
            return None

    def ConnectFunction(self): # connect 창 설정 함수(5) : connnect 버튼을 눌렀을 때 실행되는 함수. 총 5가지 mode에 따라서 연결을 잘 할 수 있도록 도와준다

        if self.mode_check == Mode.no_connect: # mode에서 아무 입력을 하지 않았을 경우에 연결 하라고 메시지 박스를 띄운다.
            print('no connect')
            QMessageBox.about(self, "Warning", "Select Mode")

        if self.mode_check == Mode.wifi_success_connect: # wifi 연결이 잘 되었는데, connect 버튼을 눌렀을 경우이다.
            msg = QMessageBox()
            msg.setWindowTitle('Info')
            msg.setText('Already have a Server Connected. \n Do you want Disconnect ?')
            msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
            result = msg.exec_()

            if result == QMessageBox.Ok: # OK버튼을 눌렀을 경우. mode를 no_connect로 바꾸어 준다.
                global conn
                conn.close() # wifi connect 을 close 해준다
                self.mylogger.info('socket server close')
                self.statusbar.showMessage('Disconnect.. ')
                self.mode_check = Mode.no_connect

        if self.mode_check == Mode.uart_success_connect: # uart 연결이 잘 되었는데, connect 버튼을 눌렀을 경우이다.
            msg = QMessageBox()
            msg.setWindowTitle('Info')
            msg.setText('Already have a Server Connected. \n Do you want Disconnect ?')
            msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
            result = msg.exec_()

            if result == QMessageBox.Ok: # OK버튼을 눌렀을 경우. mode를 no_connect로 바꾸어 준다.
                print('Ok')
                self.serial_server.close() # serial server 을 close 해준다
                self.mylogger.info('serial server close')
                self.statusbar.showMessage('Disconnect.. ')
                self.mode_check = Mode.no_connect

        if self.mode_check == Mode.wifi_connect: # mode가 wifi 였을 때
            if not (self.ip is None): # wifi dialog 등에서 ip 주소가 제대로 입력이 되지 않았을 경우
                QMessageBox.about(self, "Warming", "Again ip address")

            else : #ip 주소가 잘 들어왔으면 serverThread을 start 해준다.
                serverThread = ServerThread(main_window)
                serverThread.start()

        if self.mode_check == Mode.uart_connect: # mode가 uart 였을 때
            if self.uart_port:
                try: # serial_server을 만들어 주고, mode를 uart_success_connect으로 바꾸어준다.
                    signal.signal(signal.SIGINT, self.handler)
                    self.serial_server  = serial.Serial(self.uart_port,self.uart_baud, timeout=0)
                    print(self.serial_server)
                    self.mylogger.info('Connection Successful')
                    self.statusbar.showMessage('Connection Successful')
                    self.mode_check = Mode.uart_success_connect
                except Exception as e: # server을 만들다가 error가 나면 log 창에 error을 입력해준다.
                    print(e)
                    self.mylogger.error(e)
            else: # port 등이 uartDialog에서 선택되지 않았을 경우
                QMessageBox.about(self, "Warming", "Again uart address")



    def handler(self, signum, frame):  # serial server 에서 thread을 만들때 실행되는 함수 (1) :  thread 종료용 signal function
        self.exitThread = True

    def parsing_data(self, data): # uart 연결 데이터 처리 함수
        tmp = ''.join(data)  # list로 들어 온 것을 스트링으로 합친다.
        return tmp

    def sensor_parsing_data(self, data): # serial server 에서 thread을 만들때 실행되는 함수 (2) : 측정된 데이터 센서 값 출력 하고 list에 저장하기
        tmp = ''.join(data)
        self.list.append(tmp)
        return tmp

    def readThread(self, ser): # serial server 에서 thread을 만들때 실행되는 함수 (3) : readThread : 들어온 값을 읽어주는 함수

        # thread가 종료될때까지
        # Serial interfacce :  data를 stream으로 바꿔서 (직렬화,serialization) 한 번에 1 bit 씩 전송한다.
        f  =None

        while not self.exitThread:
           try: # 데이터가 있다면
                 for c in ser.read():
                   self.line.append(chr(c))  # (integer, 0 ~ 255)를 ASCII character로 변환하고 line에 추가한다.

                   if c == 10:  # ASCII의 개행문자 10
                       readystr = self.parsing_data(self.line)

                       if (readystr == 'Transmission done\r\n'): # 데이터가 다 들어왔으면 meaBool을 False로 ,file close, 그리고 drawGraph을 그린다.
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

                       if (self.meaBool): #필요한 데이터 값만 파일에 쓰기 위해 meaBool을 만들었다.True 일때만 file에 쓰여진다.
                           readystr = self.sensor_parsing_data(self.line)
                           if (readystr == '\n'): # 개행문자만 들어왔으면 file에 쓰지 않는다.
                               continue;
                           else:
                               if not (f is None):
                                   readystr = readystr.strip('\n') #개행문자는 파일에 쓰지 않게 하기 위해서.
                                   f.write(readystr)


                       if (readystr == 'Transmission Start\r\n'): # start 하면 meaBool을 True로 해주고, file을 open한다.
                           self.meaBool = True
                           print('===== start =====')
                           self.file_name = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M.%S") + '(Machine' + self.machine_number + ').txt'
                           join_path = os.path.join(self.folder_name, self.file_name)
                           print(join_path)
                           self.mylogger.info(self.file_name + ' Open Write')
                           f = open(join_path, 'w')
                           self.radionClick = False

                       del self.line[:]  # line list 원소를 다 지워버린다.

           except Exception as e: #중간에 연결이 끊어졌을 경우
               print(e)


    def initBrowser(self): # browser 창 설정 함수(1)
        self.browser_lineEdit.setText(self.folder_name)
        self.browser_lineEdit.textChanged.connect(self.sync_browerEdit)
        self.save_pushButton.clicked.connect(self.OnOpenDocument)

    def sync_browerEdit(self,text): # browser 창 설정 함수(2) : browser_lineEdit 값이 바뀔때마다, folder_name을 자동으로 바꿔줌
        #print(text)
        self.folder_name = text

    def OnOpenDocument(self):  # browser 창 설정 함수(3). 디렉토리를 열어서 선택하게 해준다.
        self.folder_name = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if self.folder_name:
            self.browser_lineEdit.setText(self.folder_name)
        else:
            if(self.folder_name ==''):
                QMessageBox.about(self, "Warning", "Select Folder")


    def initLog(self):   # log 창 설정 함수
        logTextBox = QTextEditLogger(self)
        logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(logTextBox)
        self.verticalLayout_3.addWidget(logTextBox.widget)


    def initSetting(self): # setting 창 설정 함수(1) : lineEdit에서 type에 맞는 글자만 들어갈수 있도록 만든다.그리고 startButton click event을 해준다.
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


    def checkSetting(self):  #setting 창 설정 함수(2)
        print('check ')
        return (self.front_senserNum_spinBox.value() >0 and
                self.end_senserNum_spinBox.value() > 0 and
                len(self.z_min_lineEdit.text()) > 0 and
                len(self.z_max_lineEdit.text()) >0  and
                len(self.p_value_lineEdit.text()) and
                len(self.sample_rate_lineEdit.text()) >0)

    # setting 창 설정 함수(3) : start 버튼을 누르면 실행되는 함수. mode에 따라서 데이터를 받아들임.
    def startGrah(self):

        if os.path.isdir(self.folder_name) == False:  #browser path가 실제 존재하는 path 인지
            QMessageBox.about(self, "Warning", "Not Exist Directory")
            return  None

        if self.checkSetting() == False: #setting 창에서 입력을 제대로 했는지
            QMessageBox.about(self, "Warning", "Check Setting")
            return  None


        if self.mode_check == Mode.no_connect: # 연결이 되지 않았는데, start 버튼을 클릭했을 경우
            QMessageBox.about(self, "Warning", "Disconnect Server")
            return None

        elif self.mode_check == Mode.wifi_success_connect : #mode가 wifi_mode 일때 ,startButton을 True로 바꾸고 이것은 clientThread가 알게 된다.
            print('succuess wifi')
            self.startClick =True

        elif self.mode_check == Mode.uart_success_connect:  #mode가 uart 일때

            self.mylogger.info('Read sensor data')
            self.serial_thread = threading.Thread(target=self.readThread, args=(self.serial_server,)) # serial 읽을 thread 생성
            self.serial_thread.start()
            print(self.serial_thread)


    def wifi_drawGraph(self):  # setting 창 설정 함수(4) : wifi 연결이였을때, 그래프 그려주는 함수

        self.mylogger.info('draw 3d wifi chart')

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
        #버튼 클릭이벤트 만
        self.radionClick = True


    def test_drawGraph(self):  # setting 창 설정 함수(4) : interpolation.py 을 실행시키고 종료되면, mpa_grid_array와 max_grid_array을 받아옴.
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

        #result_array의 type이 dict이다. key 값이 MPA, MAX 이다.
        self.mpa_grid_array = result_array['MPA']
        self.max_grid_array = result_array['MAX']

        self.radionClick = True


    # setting 창 설정 함수(5) : mpa, max 을 선택한 것에 따라 등고선 그래프를 그려줌. 그리고 등고선을 클릭하면 좌표값을 보여주고 resultTable() 실행
    def radioButtonClicked(self):


        def onclick(event): #등고선 그래프를 클릭할 경우 실행
            try:
                self.location[0] = math.ceil(event.xdata) # 현재 클릭된 x 좌표
                self.location[1] = math.ceil(event.ydata) # 현재 클릭된 y 좌표

                if self.mpa_radioButton.isChecked():
                    # 10 * 10 이런식으로 grid_array shape을 바꾸어 주기.
                    self.table_array = self.mpa_grid_array[3].reshape(int(self.front_senserNum_spinBox.text()),
                                                                      int(self.end_senserNum_spinBox.text()))
                elif self.max_radioButton.isChecked():
                    self.table_array = self.max_grid_array[3].reshape(int(self.front_senserNum_spinBox.text()),
                                                                      int(self.end_senserNum_spinBox.text()))

                self.location[2] = self.table_array[self.location[0] - 1][self.location[1] - 1] # 현재 클릭된 z 좌표

                locaton_str = 'x :' + str(self.location[0]) + 'y :' + str(self.location[1]) + ' z : ' + str(+self.location[2])
                print(locaton_str)
                self.statusbar.showMessage(locaton_str) # 현재 좌표를 statusBar에 보여준다
                self.resultTable() # 선택된 좌표를 resultTable에 넘긴다. 실행된다.

            except Exception:
                #현재 선택한 좌표가 실수 즉 정수가 아닐 경우 다시 입력하라고 message을 띄운다.
                self.statusbar.showMessage('again click  point')


        if len(self.mpa_grid_array) > 0 : # 데이터를 제대로 다 받아왔다면

            if self.radionClick:  #onclick이 이미 되었는지 안되었는지를 판단하기 위해 self.mplWidgetClick 을 사용
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


    def resultTable(self): # table 창 설정 함수(1) : makeTable()을 실행시키는 함수
        print('==== resultTable  ====')
        #print(self.serial_thread.is_alive())
        self.table_size_comboBox.activated[str].connect(self.makeTable)


    def makeTable(self,text): # table 창 설정 함수(2) : tableWidget을 만드는 창
        print('==== make Table ====')
        size =0    #size 변수 선언

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


        for_num = int(float((size - 1) / 2)) # size에 맞게 데이터를 다 받아오기 위해 변수를 만듬

        # index list와 index list 만들고, 변수 선언. 표에 좌표와 값을 다 보여줘야 되서 두개의 list를 만들고, 미리 array을 만들기 위해 0 값을 넣어주었다.
        value_list = [[0 for i in range(size)] for j in range(size)]
        index_list = [[0 for i in range(size)] for j in range(size)]

        row_index =0
        colum_index = 0

        # value_list, colum_list 에 self.table_array에 있는 값들을 나누어서 넣기. location 주변에 있는 값들을 받아오기위해
        for i in range(self.location[0] - for_num, self.location[0]+ for_num + 1):
            for j in range(self.location[1] - for_num, self.location[1] + for_num + 1):
                #index를 3 x 3 이런 식으로 string으로 만든다.
                index_list[row_index][colum_index] = str(i+1) + " X " + str(j+1)
                try:
                    value_list[row_index][colum_index]  = self.table_array[i][j]
                except IndexError:
                    value_list[row_index][colum_index] = '-' # 영역이 벗어난 부분에는 '-' 을 넣어준다.

                colum_index = colum_index +1

            colum_index =0
            row_index = row_index +1



        for i in range(0,size*2):  #table.item에 좌표(index), 값(value) 배경색 등 등 넣기
            for j in range(0,size): # 배수가 아닌 부분에 index 정보를 넣음
                if i % 2== 0: #
                    self.tableWidget.setItem(i,j,QTableWidgetItem(index_list[i//2][j]))
                    self.tableWidget.item(i,j).setBackground(QtGui.QColor(233, 233, 233))
                    self.tableWidget.item(i, j).setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
                    self.tableWidget.item(i,j).setFont(QtGui.QFont("Arial",8))

                else: # 배수인 부분에 value을 넣음
                    value = value_list[i//2][j] # 선택한 부분 주변의 값 tableItem 설정
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(value)))
                    self.tableWidget.item(i, j).setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
                    self.tableWidget.item(i, j).setFont(QtGui.QFont("Arial", 11))

                    if value ==self.location[2] : # 선택한 부분 값 tableItem 설정
                        self.tableWidget.item(i, j).setBackground(QtGui.QColor(1,1,1))
                        self.tableWidget.item(i, j).setForeground(QtGui.QColor(255, 255, 255))

        #표 안에 글자는 수정 X
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)



#socket 통신 serverThread
class ServerThread(Thread):
    def __init__(self, m_window):
        Thread.__init__(self)
        self.window = m_window


    def run(self): #thread 가 만들어지고 실행되는 함수
        tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # server 생성
        tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcpServer.bind((self.window.ip, self.window.ip_port))
        threads = []

        tcpServer.listen(4)
        while True:
            print("Multithreaded server : Waiting for connections from TCP clients...")
            self.window.mylogger.info('Multithreaded server : Waiting for connections from TCP clients...')

            global conn
            (conn, (ip, port)) = tcpServer.accept() # ip 주소와 port 가 accpet 가 되는지 확인
            print('wifi connect sucesses')
            self.window.mylogger.info('wifi connect sucesses')
            self.window.mode_check = Mode.wifi_success_connect

            newthread = ClientThread(ip, port, self.window) # clientThread 생성
            newthread.start() # thread Start
            threads.append(newthread)

        for t in threads:
            t.join()


class ClientThread(Thread): #socket 통신 clientThread. window는 MainWindow이다. 거기에 있는 변수들을 이용해야 하기 때문이다. 앞에 self.window을 붙이면 된다.
    def __init__(self, ip, port, window):
        Thread.__init__(self)
        self.window = window
        self.ip = ip
        self.port = port
        print(self.window.mode_check)
        print("New server socket thread started for " + ip + ":" + str(port))
        self.window.mylogger.info("New server socket thread started for " + ip + ":" + str(port))

    def run(self):  #clientThread 가 생성되면 실행되는 함수
        print('client thread run')
        f = None

        while True:
            # (conn, (self.ip,self.port)) = serverThread.tcpServer.accept()
            global conn
            data = conn.recv(2048) # server에서 만든 conn을 receive 해준다. 2048은 버퍼사이즈 이다.

            if len(data) > 0 and self.window.startClick: # mode가 wifi_success 이고, start 버튼을 눌렀다면
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