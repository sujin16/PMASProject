import numpy as np
import time
num =0
z_min = 50
z_max =  100
num_frame =20

folder_name = 'D:/2019_2_intern/Project/0511Project/data/'
file_name = 'machine1.txt'
machine_number = '0'

def read_temp(sensor):
    global num

    if(num<num_frame):
        num =num+1
        temp = np.random.uniform(low=z_min, high=z_max, size=(100,))

    if (num >= num_frame):
        temp = np.array([])
        num  = 0

    print('num '+ str(num))
    return temp



#randomvalue file에 저장하기

def writeSensor():

    f = open(folder_name+ file_name, 'a')

    for i in range(1, 11): # data 순서. 1부터 시작
        for y in range(0,10):  # matrix size. 센서 행
            value =''
            for x in range(1, 11):  # senser random value 만들어 주기
                if (x == 10):
                    value += str(np.random.randint(21238, 30000))
                else:
                    value += str(np.random.randint(21238, 30000)) + ","


            sensor_str = 'SEN,' + str(i)+ ','+ machine_number+ ','+str(y)+':'+value+"\n"
            f.write(sensor_str)

    f.write('\n')

    for y in range(0, 10):
        value = ''
        for x in range(1, 11):  # senser random value 만들어 주기
            if (x == 10):
                value += str(np.random.randint(21238, 30000))
            else:
                value += str(np.random.randint(21238, 30000)) + ","


        mpa_result = 'MPA,' + '0' + ',' + machine_number + ',' + str(y) + ':' + value + "\n"
        f.write(mpa_result)

    for y in range(0, 10):
        value = ''
        for x in range(1, 11):  # senser random value 만들어 주기
            if (x == 10):
                value += str(np.random.randint(21238, 30000))
            else:
                value += str(np.random.randint(21238, 30000)) + ","


        max_result = 'MAX,' + '0' + ',' + machine_number + ',' + str(y) + ':' + value + "\n"
        f.write(max_result)


    f.close()


def readFile():
    total=[]
    order = 1
    f = open(folder_name+ file_name, 'r')
    lines = f.readlines()
    for line in lines:
        data_order = int(line.split(',')[1])
        print('data_order : ' + str(data_order))
        if(data_order == order):
            senser_line = line.split(',')[3:]
            senser_row = (senser_line[0].split(':'))[0]
            senser_data = line.split(',')[4:]
            senser_data.insert(0, (senser_line[0].split(':'))[1])
            total.append(senser_data)
        else:
            order +=1
            senser_line = line.split(',')[3:]
            senser_row = (senser_line[0].split(':'))[0]
            senser_data = line.split(',')[4:]
            senser_data.insert(0, (senser_line[0].split(':'))[1])
            total.append(senser_data)

        print('order: '+ str(order))


    f.close()


writeSensor()