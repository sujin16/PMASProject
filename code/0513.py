#-*- coding: utf-8 -*-

import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QMessageBox,QApplication,QFileDialog,QMainWindow,QPlainTextEdit,QAbstractItemView, QTableWidgetItem
from PyQt5 import uic, QtGui,QtCore
import mplcursors
import logging

from module.wifiConnectDialog import Ui_wifiDialog
from module.uartConnectDialog import Ui_uartDialog
from module.matrixGraph import Main
from module.randomZ import num as randomZ_num

import random

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
        result_Array=[] # 일단 빈 값을 보내준다.

        self.start_pushButton.clicked.connect(self.startGrah)
        self.mpa_radioButton.clicked.connect(lambda : self.radioButtonClicked(title,theme,result_Array))
        self.max_radioButton.clicked.connect(lambda : self.radioButtonClicked(title,theme,result_Array))

    def startGrah(self):
        #randomZ_num =0 # 초기화 test
        print("num " + str(randomZ_num))

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
            interpol_method='cubic',  # 'nearest', 'linear', 'cubic'
            method='gradation',  # gradation contour rotate wireframe
            matrix_num=3  # 3 5 7 9 ..  2n+1 (n>=1)의 값만 가능
        )

        title = str(self.algorithm_comboBox.currentText())
        theme = str(self.theme_comboBox.currentText())
        result_Array = result_array
        print(result_Array)

        self.radioButtonClicked(title, theme, result_Array)
        self.mpa_radioButton.clicked.connect(lambda: self.radioButtonClicked(title, theme, result_Array))
        self.max_radioButton.clicked.connect(lambda: self.radioButtonClicked(title, theme, result_Array))

    def radioButtonClicked(self,title,theme,result_Array):

        if len(result_Array)>0:

            #mpa_radioButton이 setCheck(True)이므로 그림을 미리 그려줘야 함.

            self.MplWidget.canvas.axes.clear()
            cf =  self.MplWidget.canvas.axes.contourf(result_Array[0], result_Array[1], result_Array[2], cmap=theme)
            self.MplWidget.canvas.axes.set_title("MPA " + title, pad=30)
            self.MplWidget.canvas.draw()

            if self.mpa_radioButton.isChecked():
                self.MplWidget.canvas.axes.clear()
                cf =  self.MplWidget.canvas.axes.contourf(result_Array[0], result_Array[1], result_Array[2], cmap=theme)
                print(type(cf))
                self.MplWidget.canvas.axes.set_title("MPA "+ title, pad=30)
                self.MplWidget.canvas.draw()

                print('mpa ')
                self.resultTable()

                cursor = self.MplWidget.cursor

                @cursor.connect("add")
                def on_add(sel):
                    print('click')
                    sel.annotation.get_bbox_patch().set(fc="white")
                    ann = sel.annotation
                    # `cf.collections.index(sel.artist)` is the index of the selected line
                    # among all those that form the contour plot.
                    # `cf.cvalues[...]` is the corresponding value.

                    ann.set_text("{}\nz={:.5g}".format(
                        ann.get_text(), cf.cvalues[cf.collections.index(sel.artist)]))
                    get_array = ann.get_text().split("\n")

                    #  1. 등고선을 클릭 하면 x_index, y_index 값을 int형으로 반올림을 해준다.
                    x_index = int(float(get_array[0].split("=")[1])) - 1
                    y_index = int(float(get_array[1].split("=")[1])) - 1

                    # 2. 실제 센서 값을 (,100) - > (10, 10) 으로 reshape을 해주고 나서, z_value에 담아준다.
                    z_value = result_Array[3].reshape(10, 10)

                    # 3. matrix_num을 이용하여 편하게 매트릭스를 계산하기 위해 변환을 한다.
                    for_num = int(float((self.matrix_num - 1) / 2))

                    # 4. index가  범위에 벗어나게 되면 인덱스에 벗어났다고 알려준다.
                    if (
                                            x_index < for_num or y_index < for_num or x_index == self.front_num - for_num or y_index == self.end_num - for_num):
                        print("click " + str(for_num) + " < index  < " + str(self.front_num - for_num))
                    else:
                        # 5. 실제 센서값과 가장 가까이 있는 값들을 출력해준다.
                        print("x index : " + str(x_index))  # x_index
                        print("y index : " + str(y_index))  # y_index
                        print("click value" + str(z_value[x_index][y_index]))

                        for i in range(x_index - for_num, x_index + for_num + 1):
                            for j in range(y_index - for_num, y_index + for_num + 1):
                                num = round(z_value[i][j], 0)
                                print("z[" + str(i) + "]" + "[" + str(j) + "]" + "  " + str(num))
                    print("\n")


            elif self.max_radioButton.isChecked():
                self.MplWidget.canvas.axes.clear()
                cf= self.MplWidget.canvas.axes.contourf(result_Array[0], result_Array[1], result_Array[2], cmap=theme)
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