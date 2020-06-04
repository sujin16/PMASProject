#!/usr/bin/env python
import sys
from threading import Thread
import serial
import time
import collections
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import struct
import copy
import pandas as pd
import sensor
import signal
import threading

class serialServer:
    def __init__(self, serialPort='COM5', serialBaud=115200, plotLength=100, dataNumBytes=2, numPlots=1):

        self.list = []
        self.line = []
        self.start_time = None
        self.end_time = None
        self.sensorBool = False
        self.file_path = ""
        self.file_name = "test.txt"
        self.line_number =0  #TXS_(??) : line 줄 수
        self.machine_number = 0  #machine numer : machine 이름

        self.port = serialPort
        self.baud = serialBaud
        self.plotMaxLength = plotLength
        self.dataNumBytes = dataNumBytes
        self.numPlots = numPlots

        self.data = []
        for i in range(numPlots):  # give an array for each type of data and store them in a list
            self.data.append(collections.deque([0] * plotLength, maxlen=plotLength))
        self.isRun = True
        self.isReceiving = False
        self.thread = None
        self.plotTimer = 0
        self.previousTimer = 0
        # self.csvData = []

        print('Trying to connect to: ' + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
        try:
            self.serialConnection = serial.Serial(serialPort, serialBaud, timeout=1)
            print('Connected to ' + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
        except:
            print("Failed to connect with " + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
            sys.exit()

    def readSerialStart(self):
        print('read Serial Start')
        if self.thread == None:
            self.thread = Thread(target=self.backgroundThread)
            self.thread.start()
            # Block till we start receiving values
            while self.isReceiving != True:
                #print('------ Receiving False ------')
                time.sleep(0.1) #= 0.1 초 동안 프로세스 정지

    # 측정된 데이터 센서 값 출력 하고 list에 저장하기
    def sensor_parsing_data(self, data):
        tmp = ''.join(data)
        print(tmp)
        self.list.append(tmp)
        return tmp

    def parsing_data(self, data):
        tmp = ''.join(data)  # list로 들어 온 것을 스트링으로 합침
        print(tmp)
        return tmp

    def getSerialData(self, frame, lines, lineValueText, lineLabel, timeText):
        if(len(self.list)>0):
            self.readSensorDataForm()
            print(self.list)

            currentTimer = time.perf_counter()
            self.plotTimer = int((currentTimer - self.previousTimer) * 1000)  # the first reading will be erroneous
            self.previousTimer = currentTimer
            timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')
            # privateData = copy.deepcopy(self.rawData[:])  # so that the 3 values in our plots will be synchronized to the same sample time
            datalist = sensor.read_temp()

            if (datalist is None):
                return lines,
            else:
                for i in range(self.numPlots):
                    value = datalist[i]
                    self.data[i].append(value)  # we get the latest data point and append it to our array
                    lines[i].set_data(range(self.plotMaxLength), self.data[i])  # data = [[],[],[],[],[],[],[]]
                    lineValueText[i].set_text('[' + lineLabel[i] + '] = ' + str(value))
                    # self.csvData.append([self.data[0][-1], self.data[1][-1], self.data[2][-1]])

    def readSensorDataForm(self):
        '''
        total_array = []
        sensor_dict = {}

        #sensor dict init
        for i in range(0, self.numPlots):
            sensor_dict['S' + str(i+1)] = []

        array_line = None
        while array_line != '':
            array_line = list[-1] #계속 들어오는 데이터를 받기 위해 맨 마지막 list value을 가지고 온다.
            if (array_line.find('TXS_') >= 0):
                self.line_number = int(array_line[4:].replace(",", ""))
                continue
            if (array_line.find('Ready') >= 0):
                continue
            if (array_line.find('Measure') >= 0):
                continue
            if (array_line.find('Result') >= 0):
                continue
            if (array_line == ''):
                continue

            array_line = array_line.strip("\n")
            total_array.append(array_line)
            # print(total_array)

        num = 1

        for items in total_array:
            if (num <= self.line_number - 3):
                item = items.split(",")[2:]  # time이랑 machine number는 제외하고 출력
                for i in range(0, self.numPlots):
                    sensor_dict['S' + str(i + 1)].append(item[i].split(":")[1])
            else:
                item = items.split(",")
            print(item, "else line number", num)
            num = num + 1

        print(sensor_dict)
        '''

        data = self.list[-1]
        if (data.find('TXS_') >= 0): #TXS_
            self.line_number = data.split(',')[0][4:]
        return 1

    def backgroundThread(self):# retrieve data
        time.sleep(1.0)  # give some buffer time for retrieving data

        #f = open(self.file_name, 'w')

        while (self.isRun):
            for c in  self.serialConnection.read():
                self.line.append(chr(c))  # (integer, 0 ~ 255)를 ASCII character로 변환하고 line에 추가한다.
                if c == 10:  # ASCII의 개행문자 10
                    readystr = self.parsing_data(self.line)

                    if (readystr == 'xbee is ready?\r\n'):
                        self.serialConnection.write(b'x')

                    if (readystr.find('TXS_') >= 0):
                        self.start_time = time.time()
                        self.serialConnection.write(b'R')
                        self.sensorBool = True

                    if (readystr.find('Send confirm message(A, F)') >= 0):
                        #1. SUM, MPA, COUNT 값 보여주기
                        print(self.list[-3]) #SUM
                        print(self.list[-2]) #MPA
                        print(self.list[-1]) #COUNT

                        #2. line error check해주기 : list 길이랑 line_number 값 비교해주기
                        print("line check "+str(self.lineCheck()))

                        #3. list 비워주기
                        del self.list[:]
                        # 바로 종료하고 싶을 때,
                        if(True):
                            self.serialConnection.write(b'F')
                            print(self.sensorBool)
                            self.sensorBool = False

                    if (not self.sensorBool and readystr.find('Ready') >= 0):
                        #f.close()
                        self.end_time = time.time()
                        #print("working time: {} sec".format(self.end_time - self.start_time))
                        print('text close')
                        self.sensorBool = False

                    if (self.sensorBool):
                        readystr = self.sensor_parsing_data(self.line)
                        if (readystr == '\n'):
                            continue
                        else:
                            readystr = readystr.strip('\n')
                            #f.write(readystr)

                    del self.line[:]  # line list 원소를 다 지워버린다.

            self.isReceiving = True


    def lineCheck(self):
        # TXS__ , \r\w ,  --Ready --, --Measure  file--, --Result value --  총 5개
        print('line length : ' + str(self.line_number) + "list length" + str(len(self.list)))
        return (len(self.list)  -5 == int(self.line_number))

    def close(self):
        self.isRun = False
        self.thread.join()
        self.serialConnection.close()
        print('Disconnected...')

def main():
    #1. serial init
    portName = 'COM51'
    baudRate = 115200
    maxPlotLength = 20  # number of points in x-axis of real time plot
    dataNumBytes = 4  # number of bytes of 1 data point
    numPlots = 7  # number of plots in 1 graph

    # 2. make serialPlot()
    s = serialServer(portName, baudRate, maxPlotLength, dataNumBytes, numPlots)  # initializes all required variables

    # 3. serial start
    s.readSerialStart()

    # 4. plot init
    pltInterval = 1000 # Period at which the plot animation updates [ms]
    xmin = 0
    xmax = maxPlotLength
    ymin = -(1)
    ymax = 100
    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(xlim=(xmin, xmax), ylim=(float(ymin - (ymax - ymin) / 10), float(ymax + (ymax - ymin) / 10)))
    ax.set_title('Arduino Accelerometer')
    ax.set_xlabel("Time")
    ax.set_ylabel("Accelerometer Output")
    lineLabel = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7']
    timeText = ax.text(0.70, 0.95, '', transform=ax.transAxes)
    lines = []
    lineValueText = []
    for i in range(numPlots):
        lines.append(ax.plot([], [], label=lineLabel[i])[0])
        lineValueText.append(ax.text(0.70, 0.90 - i * 0.05, '', transform=ax.transAxes))

    # 5. plot animation
    anim = animation.FuncAnimation(fig, s.getSerialData, fargs=(lines, lineValueText, lineLabel, timeText),
                                   interval=pltInterval)  # fargs has to be a tuple

    plt.legend(loc="upper left")
    plt.show()
    s.close()

if __name__ == '__main__':
    main()