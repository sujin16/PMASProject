import numpy as np
num =0
z_min = 0
z_max =  40
num_frame =10

def read_temp(sensor):
    global num
    if(num<num_frame):
        num =num+1
        temp = np.random.uniform(low=z_min, high=z_max, size=(100,))
        print(num)
    if (num >= num_frame):
        temp = np.array([])
    return temp
