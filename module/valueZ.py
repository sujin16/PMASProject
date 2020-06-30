import numpy as np
import time
num =0
z_min = 50
z_max =  100
num_frame =20


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


