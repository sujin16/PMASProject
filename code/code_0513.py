#-*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QMessageBox,QApplication,QFileDialog,QMainWindow,QPlainTextEdit,QAbstractItemView, QTableWidgetItem
from PyQt5 import uic, QtGui,QtCore
import logging
import math

from module.wifiConnectDialog import Ui_wifiDialog
from module.uartConnectDialog import Ui_uartDialog
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


class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self,None)
        uic.loadUi(PMPSUI, self)


        self.folder_name =''
        self.theme =''

        self.result_Array =[]
        self.mpa_grid_array =[]
        self.max_grid_array =[]

        self.location=[0,0,0] # location[0] = x 좌표, location[1] = y 좌표, location[2] = z 좌표,
        self.radionClick =False
        self.statusbar.showMessage('Ready')

        self.initConnect()
        self.initBrowser()
        self.initSetting()
        self.initLog()

    def initConnect(self):
        self.connect_comboBox.activated[str].connect(self.comboBoxFunction)

    def comboBoxFunction(self,text):
        if 'Wifi' in text :
            print('Wifi select')
            self.openWifiDialog()
        elif 'Uart' in text:
            print('Uart select')
            self.openUartDialog()

    def openWifiDialog(self):
        self.window = QMainWindow()
        self.ui = Ui_wifiDialog()
        self.ui.setupUi(self.window)
        self.window.show()

    def openUartDialog(self):
        self.window = QMainWindow()
        self.ui = Ui_uartDialog()
        self.ui.setupUi(self.window)
        self.window.show()


    def initBrowser(self):
        self.save_pushButton.clicked.connect(self.OnOpenDocument)
        #self.save_pushButton.clicked.connect(self.openWindow)

    def OnOpenDocument(self):
        self.folder_name = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if self.folder_name:
            self.browser_lineEdit.setText(self.folder_name)
        else:
            if(self.folder_name ==''):
                QMessageBox.about(self, "Warning", "폴더를 선택해주세요.")

    def initLog(self):
        logTextBox = QTextEditLogger(self)
        # You can format what is printed to text box
        logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(logTextBox)
        # You can control the logging level
        #logging.getLogger().setLevel(logging.DEBUG)

        self.verticalLayout_3.addWidget(logTextBox.widget)
        #self.start_pushButton.clicked.connect(self.test)

    def test(self):
        logging.debug('damn, a bug')
        logging.info('something to remember')
        logging.warning('that\'s not right')
        logging.error('foobar')


    def initSetting(self):
        title =str(self.algorithm_comboBox.currentText())
        theme =str(self.theme_comboBox.currentText())

        self.start_pushButton.clicked.connect(self.startGrah)


    def startGrah(self):
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