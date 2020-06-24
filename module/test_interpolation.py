import sys
from pykrige.ok import OrdinaryKriging
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import cm
from mpl_toolkits.mplot3d import axes3d
from scipy.interpolate import griddata as gd

import pybrain.datasets as pd
from pybrain.tools.shortcuts import buildNetwork
from pybrain.supervised.trainers import BackpropTrainer
import datetime as dt
#import code.code_0513 as code

start_time =''
end_time= ''

full_order = 1
machine_number = 0
sen_array = np.array([])

mpa_array = np.array([])
max_array = np.array([])

mpa_grid_array =[]
max_grid_array =[]

class Plot:
    def __init__(self, front_num, end_num, theme, min_bound, max_bound, interval, p_value, extr_interval, model, method,folder_path, file_name):
        super().__init__()

        self.front_num = front_num
        self.end_num = end_num
        self.theme = theme
        self.interval = interval
        self.min_bound = min_bound
        self.max_bound = max_bound
        self.p_value = p_value
        self.extr_interval = extr_interval
        self.method = method
        self.interpol_method = 'cubic'
        self.model = model
        self.folder_path = folder_path +'/'
        self.file_name = file_name

        self.x = []
        self.y = []

        for i in range(front_num):
            for j in range(end_num):
                self.x.append(i + 1)
                self.y.append(j + 1)

        z = np.random.uniform(low=0, high=40, size=(front_num * end_num,))
        self.sample_data = np.c_[self.x, self.y, z]

    def main(self):
        if (self.model == 'Neural'):
            self.plot(method=self.method, title='Neural net')

        if (self.model == 'Kriging'):
            self.plot(method=self.method, title='Kriging')

        if (self.model == 'Nearest'):
            self.plot(method=self.method, title='Nearest')


    def neural_net(self,extrapolation_spots, data):
        net = buildNetwork(2, 10, 1)
        ds = pd.SupervisedDataSet(2, 1)

        for row in self.sample_data:
            ds.addSample((row[0], row[1]), (row[2],))
        trainer = BackpropTrainer(net, ds)
        trainer.trainUntilConvergence()

        new_points = np.zeros((len(extrapolation_spots), 3))
        new_points[:, 0] = extrapolation_spots[:, 0]
        new_points[:, 1] = extrapolation_spots[:, 1]
        for i in range(len(extrapolation_spots)):
            new_points[i, 2] = net.activate(extrapolation_spots[i, :2])
        combined = np.concatenate((data, new_points))
        return combined

    def nearest_neighbor_interpolation(self,data, x, y, p=0.5):
        n = len(data)
        vals = np.zeros((n, 2), dtype=np.int32)
        distance = lambda x1, x2, y1, y2: (x2 - x1) ** 2 + (y2 - y1) ** 2
        for i in range(n):
            dis = distance(data[i, 0], x, data[i, 1], y)
            if(dis !=0):
                vals[i, 0] = data[i, 2] / (dis) ** p
                vals[i, 1] = 1 / (dis) ** p
            else:
                break

        if(np.sum(vals[:, 1]) !=0):
            z = np.sum(vals[:, 0]) / np.sum(vals[:, 1])
            return z
        else:
            return None


    def get_plane(self, xl, xu, yl, yu, i):
        xx = np.arange(xl, xu, i)
        yy = np.arange(yl, yu, i)
        extrapolation_spots = np.zeros((len(xx) * len(yy), 2))
        count = 0
        for i in xx:
            for j in yy:
                extrapolation_spots[count, 0] = i
                extrapolation_spots[count, 1] = j
                count += 1
        return extrapolation_spots

    def kriging(self,data, extrapolation_spots):
        gridx = np.arange(1.0, self.front_num, self.end_num)
        gridy = np.arange(1.0, self.front_num, self.end_num)
        OK = OrdinaryKriging(data[:, 0], data[:, 1], data[:, 2], variogram_model='spherical',verbose=False, nlags=100)

        z, ss = OK.execute('grid', gridx, gridy)
        return gridx, gridy, z, ss

    def extrapolation(self,data, extrapolation_spots, model='Nearest'):
        if model == 'Kriging':
            xx, yy, zz, ss = self.kriging(data, extrapolation_spots)

            new_points = np.zeros((len(yy) * len(zz), 3))
            count = 0
            for i in range(len(xx)):
                for j in range(len(yy)):
                    new_points[count, 0] = xx[i]
                    new_points[count, 1] = yy[j]
                    new_points[count, 2] = zz[i, j]
                    count += 1
            combined = np.concatenate((data, new_points))
            return combined

        if model == 'Nearest':
            new_points = np.zeros((len(extrapolation_spots), 3))
            new_points[:, 0] = extrapolation_spots[:, 0]
            new_points[:, 1] = extrapolation_spots[:, 1]
            for i in range(len(extrapolation_spots)):
                new_points[i, 2] = self.nearest_neighbor_interpolation(data,extrapolation_spots[i, 0],extrapolation_spots[i, 1], self.p_value)
                combined = np.concatenate((data, new_points))
            return combined

    def interpolation(self,data):
        gridx, gridy = np.mgrid[1:self.front_num:50j, 1:self.end_num:50j]
        gridz = gd(data[:, :2], data[:, 2], (gridx, gridy), method=self.interpol_method)
        return gridx, gridy, gridz



    def plot(self,method='gradation', title='Nearest'):

        extrapolation_spots = self.get_plane(1, self.front_num, 1, self.end_num, self.extr_interval)
        #1.먼저 파일 읽기
        f = open(self.folder_path+ self.file_name, 'r')
        def update(i):
            global mpa_grid_array, max_grid_array, sen_array, full_order,mpa_array, max_array


            for i in range(0,self.front_num):

                line = f.readline()
                if not line:
                    fig.suptitle('finish', fontsize=18)
                    ani._stop()

                    if len(mpa_array) == self.front_num * self.end_num:
                        mpa_array = mpa_array.astype('int32')

                        update_data = np.c_[self.x, self.y, mpa_array]

                        if (title == 'Nearest'):
                            update_extra = self.extrapolation(update_data, extrapolation_spots, model='Nearest')
                        if (title == 'Kriging'):
                            update_extra = self.extrapolation(update_data, extrapolation_spots, model='Kriging')
                        if (title == 'Neural net'):
                            update_extra = self.neural_net(extrapolation_spots, update_data)

                        gridx_update, gridy_update, gridz_update = self.interpolation(update_extra)

                        mpa_grid_array.append(gridx_update)  # 0. 보간법이 적용된 x 값
                        mpa_grid_array.append(gridy_update)  # 1. 보간법이 적용된 y 값
                        mpa_grid_array.append(gridz_update)  # 2. 보간법이 적용된 z 값
                        mpa_grid_array.append(mpa_array)  # 3. 실제 센서 값

                    else:
                        mpa_array =[]
                        print('error mpa array')

                    if len(max_array) == self.front_num * self.end_num:
                        max_array = max_array.astype('int32')

                        update_data = np.c_[self.x, self.y, max_array]

                        if (title == 'Nearest'):
                            update_extra = self.extrapolation(update_data, extrapolation_spots, model='Nearest')
                        if (title == 'Kriging'):
                            update_extra = self.extrapolation(update_data, extrapolation_spots, model='Kriging')
                        if (title == 'Neural net'):
                            update_extra = self.neural_net(extrapolation_spots, update_data)

                        gridx_update, gridy_update, gridz_update = self.interpolation(update_extra)

                        max_grid_array.append(gridx_update)  # 0. 보간법이 적용된 x 값
                        max_grid_array.append(gridy_update)  # 1. 보간법이 적용된 y 값
                        max_grid_array.append(gridz_update)  # 2. 보간법이 적용된 z 값
                        max_grid_array.append(max_array)  # 3. 실제 센서 값'
                    else:
                        max_array =[]
                        print('error max array')

                    plt.close('all')
                    return None

                else:
                    line_arrray = line.split(',')

                    if line_arrray[0] == 'MPA':
                        a_array = line_arrray[3:]
                        a_array[0] = a_array[0].split(':')[1]
                        a_array[-1] = a_array[-1].split("\n")[0]
                        mpa_array = np.append(mpa_array, a_array)

                    if line_arrray[0] == 'MAX':
                        a_array = line_arrray[3:]
                        a_array[0] = a_array[0].split(':')[1]
                        a_array[-1] = a_array[-1].split("\n")[0]
                        max_array = np.append(max_array, a_array)

                    if line_arrray[0] == 'SEN':
                        current_full_order = int(line_arrray[1])

                        if current_full_order == full_order + 1:
                            if len(sen_array) == self.front_num * self.end_num:
                                print('full_order success ' + str(full_order))
                                #print(sen_array)
                                full_order = full_order + 1
                                sen_array = np.array([])
                                a_array = line_arrray[3:]
                                a_array[0] = a_array[0].split(':')[1]
                                sen_array = np.append(sen_array, a_array)
                            else:
                                print('full_order error ' + str(full_order))
                                #full_order = full_order + 1
                                sen_array = np.array([])
                                a_array = line_arrray[3:]
                                a_array[0] = a_array[0].split(':')[1]
                                sen_array = np.append(sen_array, a_array)

                        elif current_full_order == full_order:
                            a_array = line_arrray[3:]
                            a_array[0] = a_array[0].split(':')[1]
                            a_array[-1] = a_array[-1].split("\n")[0]
                            sen_array = np.append(sen_array, a_array)

            sen_array = sen_array.astype('int32')
            update_data = np.c_[self.x, self.y, sen_array]

            if (title == 'Nearest'):
                update_extra = self.extrapolation(update_data, extrapolation_spots, model='Nearest')
            if (title == 'Kriging'):
                update_extra = self.extrapolation(update_data, extrapolation_spots, model='Kriging')
            if (title == 'Neural net'):
                update_extra = self.neural_net(extrapolation_spots, update_data)


            gridx_update, gridy_update, gridz_update = self.interpolation(update_extra)

            grid_array =[]

            grid_array.append(gridx_update) #0. 보간법이 적용된 x 값
            grid_array.append(gridy_update) #1. 보간법이 적용된 y 값
            grid_array.append(gridz_update) #2. 보간법이 적용된 z 값
            grid_array.append(sen_array)    #3. 실제 센서 값

            ax.clear()

            if(method =='gradation'):
                ax.plot_surface(gridx_update, gridy_update, gridz_update, alpha=0.5, cmap=self.theme)
                ax.set_zbound(self.min_bound, self.max_bound)
                ax.view_init(azim=45)

            if (method == 'wireframe'):
                ax.plot_wireframe(gridx_update, gridy_update, gridz_update, alpha=0.5)
                ax.scatter(update_data[:, 0], update_data[:, 1], update_data[:, 2], c='red')
                ax.set_zbound(self.min_bound, self.max_bound)
                ax.view_init(azim=45)

            if (method == 'contour'):
                ax.contourf(gridx_update, gridy_update, gridz_update, zdir='z', offset=self.min_bound, cmap=self.theme)
                ax.contourf(gridx_update, gridy_update, gridz_update, zdir='x', offset=1, cmap=self.theme)
                ax.contourf(gridx_update, gridy_update, gridz_update, zdir='y', offset=1, cmap=self.theme)
                ax.set_zbound(self.min_bound, self.max_bound)
                ax.view_init(azim=45)

            return ax,


        fig = plt.figure(figsize=(10, 10))
        fig.suptitle(title, fontsize=18)
        ax = fig.gca(projection='3d')
        ani = animation.FuncAnimation(fig, update, interval=self.interval)
        plt.show()



def Main(front_num,end_num, theme, min_bound, max_bound,interval, p_value, extr_interval, model,method,folder_path, file_name):
    #1. plot 만들기
    plot = Plot(front_num, end_num, theme, min_bound, max_bound,interval, p_value, extr_interval, model, method, folder_path,file_name)
    # 2. plot main 함수 실행
    plot.main()
    return {'MPA' : mpa_grid_array , 'MAX' : max_grid_array}



# result = Main(
#      front_num = 10,
#      end_num = 10,
#      theme="coolwarm",
#      min_bound=20000,
#      max_bound=30000,
#      interval=1000,
#      p_value=0.5,
#      extr_interval=30,
#      model='Nearest',  # 'nearest', 'Kriging', 'neural'
#      method='gradation', # gradation contour rotate wireframe,
#      folder_path = 'D:/2019_2_intern/Project/0511Project/code/',
#      file_name = '2020.06.24.09.06.(Machine1).txt'
# )
#
# print('---------  end result  ------------')
#
# print(result)
#
# #print(result)
# sys.exit()
