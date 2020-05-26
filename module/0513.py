#-*- coding: utf-8 -*-

import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QMessageBox,QApplication,QFileDialog,QMainWindow,QPlainTextEdit,QAbstractItemView, QTableWidgetItem
from PyQt5 import uic, QtGui,QtCore
import logging

from wifiConnectDialog import Ui_wifiDialog
from uartConnectDialog import Ui_uartDialog

PMPSUI = '../ui_Files/PMPS.ui'


data = {'col1': ['1', '2', '3', '4'],
        'col2': ['1', '2', '1', '3'],
        'col3': ['1', '1', '2', '1']}



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

        #전역 변수들
        self.folder_name =''
        self.theme =''

        self.statusbar.showMessage('Ready')

        self.initConnect()
        self.initBrowser()
        self.initLog()
        self.resultGraph()
        self.resultTable()

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
            QMessageBox.about(self, "Warning", "폴더를 선택해주세요.")

    def initLog(self):
        logTextBox = QTextEditLogger(self)
        # You can format what is printed to text box
        logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(logTextBox)
        # You can control the logging level
        #logging.getLogger().setLevel(logging.DEBUG)

        self.verticalLayout_3.addWidget(logTextBox.widget)
        self.start_pushButton.clicked.connect(self.test)

    def test(self):
        logging.debug('damn, a bug')
        logging.info('something to remember')
        logging.warning('that\'s not right')
        logging.error('foobar')


    def initSetting(self):
        front_senserNum = self.front_senserNum_spinBox
        end_senserNum = self.end_senserNum_spinBox
        graph_method = self.method_comboBox
        graph_theme = self.theme_comboBox
        z_min =self.min_lineEdit
        z_max = self.z_max_lineEdit
        sample_rate = self.sample_rate_lineEdit
        algorithm = self.algorithm_comboBox
        threshold =self.threshold_lineEdit
        p_value = self.p_value_lineEdit

        dot_check= self.dotcheckBox
        startButton = self.start_pushButton


    def resultGraph(self):
        # self.max_radioButton  / self.mpa_radionButton 에 따라 다른 그래프 보여주기
        #cursor를 갔다대면, tableView 보여주기

        N = 5
        value = (20, 35, 30, 35, 27)
        ind = np.arange(N)
        width = 0.35

        fig = plt.Figure()  # fig은 그래프 창, ax 는 그래프 그 자체
        ax = fig.add_subplot(111)
        ax.bar(ind, value, width)
        ax.set_xticks(ind + width / 20)
        ax.set_xticklabels(['G1', 'G2', 'G3', 'G4', 'G5'])
        ax.set_xticks(ind + width / 20)

        canvas = FigureCanvas(fig)
        canvas.draw()
        self.verticalLayout_2.addWidget(canvas)

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

