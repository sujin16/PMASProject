import sys
from pykrige.ok import OrdinaryKriging
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt2
import matplotlib.animation as animation
from matplotlib import cm
from mpl_toolkits.mplot3d import axes3d
from scipy.interpolate import griddata as gd

import pybrain.datasets as pd
from pybrain.tools.shortcuts import buildNetwork
from pybrain.supervised.trainers import BackpropTrainer
import randomZ
import datetime as dt
import mplcursors

total ={}
grid_array =[]

start_time =''
end_time= ''

class Plot:
    def __init__(self, num, theme, min_bound, max_bound, interval, p_value, extr_interval, model,
                 interpol_method, method,matrix_num):
        super().__init__()

        self.num = num  # num * num
        self.theme = theme
        self.interval = interval
        self.min_bound = min_bound
        self.max_bound = max_bound
        self.p_value = p_value
        self.extr_interval = extr_interval
        self.method = method
        self.interpol_method = interpol_method
        self.model = model
        self.matrix_num = matrix_num

        self.x = []
        self.y = []

        for i in range(num):
            for j in range(num):
                self.x.append(i + 1)
                self.y.append(j + 1)

        z = np.random.uniform(low=0, high=40, size=(num * num,))
        self.sensor_data = np.c_[self.x, self.y, z]

    def main(self):
        extrapolation_spots = self.get_plane(1, self.num, 1, self.num, self.extr_interval)

        if (self.model == 'neural'):
            self.neural_analysis(extrapolation_spots)

        if (self.model == 'kriging'):
            self.kriging_analysis(extrapolation_spots)

        if (self.model == 'nearest'):
            self.nearest_analysis(extrapolation_spots)

    def neural_analysis(self,extrapolation_spots):
        data_extra = self.neural_net(extrapolation_spots, self.sensor_data)
        gridx_data, gridy_data, gridz_data = self.interpolation(data_extra)
        self.plot(self.sensor_data, gridx_data, gridy_data, gridz_data, method=self.method, title='neural net')

    def neural_net(self,extrapolation_spots, data):
        net = buildNetwork(2, 10, 1)
        ds = pd.SupervisedDataSet(2, 1)

        for row in self.sensor_data:
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

    def nearest_analysis(self,extrapolation_spots):
        data_extra = self.extrapolation(self.sensor_data, extrapolation_spots, model='nearest')
        gridx_data, gridy_data, gridz_data = self.interpolation(data_extra)
        self.plot(self.sensor_data, gridx_data, gridy_data, gridz_data, method=self.method, title='nearest')

    def kriging_analysis(self,extrapolation_spots):
        data_extra = self.extrapolation(self.sensor_data, extrapolation_spots, model='kriging')
        gridx_data, gridy_data, gridz_data = self.interpolation(data_extra)
        self.plot(self.sensor_data, gridx_data, gridy_data, gridz_data, method=self.method, title='kriging')

    def nearest_neighbor_interpolation(self,data, x, y, p=0.5):
        n = len(data)
        vals = np.zeros((n, 2), dtype=np.float64)
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
        gridx = np.arange(1.0, self.num, self.num)
        gridy = np.arange(1.0, self.num, self.num)
        OK = OrdinaryKriging(data[:, 0], data[:, 1], data[:, 2], variogram_model='spherical',verbose=False, nlags=100)

        z, ss = OK.execute('grid', gridx, gridy)
        return gridx, gridy, z, ss

    def extrapolation(self,data, extrapolation_spots, model='nearest'):
        if model == 'kriging':
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

        if model == 'nearest':
            new_points = np.zeros((len(extrapolation_spots), 3))
            new_points[:, 0] = extrapolation_spots[:, 0]
            new_points[:, 1] = extrapolation_spots[:, 1]
            for i in range(len(extrapolation_spots)):
                new_points[i, 2] = self.nearest_neighbor_interpolation(data,extrapolation_spots[i, 0],extrapolation_spots[i, 1], self.p_value)
                combined = np.concatenate((data, new_points))
            return combined

    def interpolation(self,data):
        gridx, gridy = np.mgrid[1:self.num:50j, 1:self.num:50j]
        gridz = gd(data[:, :2], data[:, 2], (gridx, gridy), method=self.interpol_method)
        return gridx, gridy, gridz

    def plot(self,data, gridx, gridy, gridz, method='rotate', title='nearest'):

        extrapolation_spots = self.get_plane(1, self.num, 1, self.num, self.extr_interval)

        def update(i):
            ax.view_init(azim=i)
            return ax,

        def update_(i):
            now = dt.datetime.now().strftime('%H:%M:%S')
            update_z = randomZ.read_temp(self.num)
            global start_time, end_time, grid_array,total

            # 3. 값이 더이상 들어오지 않음
            if (update_z.size == 0):
                fig.suptitle('finish', fontsize=18)
                end_time = now
                ani._stop()

                print(start_time)
                print(end_time)

                fig2 = plt2.figure(figsize=(10, 10))
                fig2.suptitle(title, fontsize=18)
                cf = plt2.contourf(grid_array[0], grid_array[1], grid_array[2],cmap=self.theme)
                plt2.gca().invert_yaxis()
                cursor = mplcursors.cursor()

                @cursor.connect("add")
                def on_add(sel):
                    sel.annotation.get_bbox_patch().set(fc="white")
                    ann = sel.annotation
                    # `cf.collections.index(sel.artist)` is the index of the selected line
                    # among all those that form the contour plot.
                    # `cf.cvalues[...]` is the corresponding value.

                    ann.set_text("{}\nz={:.5g}".format(
                        ann.get_text(), cf.cvalues[cf.collections.index(sel.artist)]))
                    get_array = ann.get_text().split("\n")

                    #  1. 등고선을 클릭 하면 x_index, y_index 값을 int형으로 반올림을 해준다.
                    x_index = int(float(get_array[0].split("=")[1])) -1
                    y_index = int(float(get_array[1].split("=")[1])) -1

                    # 2. 실제 센서 값을 (,100) - > (10, 10) 으로 reshape을 해주고 나서, z_value에 담아준다.
                    z_value =grid_array[3].reshape(10,10)

                    # 3. matrix_num을 이용하여 편하게 매트릭스를 계산하기 위해 변환을 한다.
                    for_num = int(float((self.matrix_num -1)/2))

                    # 4. index가  범위에 벗어나게 되면 인덱스에 벗어났다고 알려준다.
                    if(x_index <for_num or y_index <for_num or x_index == self.num -for_num or y_index == self.num -for_num ):
                        print("click "+str(for_num) +" < index  < "+ str(self.num -for_num))
                    else:
                        # 5. 실제 센서값과 가장 가까이 있는 값들을 출력해준다.
                        print("x index : " + str(x_index))  # x_index
                        print("y index : " + str(y_index))  # y_index
                        print("click value" + str(z_value[x_index][y_index]))

                        for i in range (x_index -for_num ,x_index +for_num+1):
                            for j in range(y_index - for_num, y_index + for_num+1):
                                num  = round(z_value[i][j],0)
                                print("z["+str(i)+"]"+"["+str(j)+"]" +"  "+str(num))

                    print("\n")
                    '''



                    x_index = int(float(x_index))
                    y_index = int(float(y_index))

                    2. matrix_num 은 3 , 5 ,7  홀수만 가능하다. 2n + 1 ( n>= 1)

                    for_num = int(float((matrix_num -1)/2))

                    for i in range (a_index -for_num ,a_index +for_num+1):
                        for j in range(b_index - 1, b_index + 2):
                            num  = round(z[i][j],0)
                            print("z["+str(i)+"]"+"["+str(j)+"]" +"  "+str(num))

                    for i in range (x_index -for_num ,x_index +for_num+1):
                        for j in range(y_index - 1, y_index + 2):
                            num  = round(z_reshape[i][j],0)
                            print("z["+str(i)+"]"+"["+str(j)+"]" +"  "+str(num))
                    '''


                plt2.show()

                return now

            if (update_z.all()):

                if (len(total) == 0):
                    start_time = now

                total[now] = update_z
                update_data = np.c_[self.x, self.y, update_z]

                if (title == 'nearest'):
                    update_extra = self.extrapolation(update_data, extrapolation_spots, model='nearest')
                if (title == 'kriging'):
                    update_extra = self.extrapolation(update_data, extrapolation_spots, model='kriging')
                if (title == 'neural net'):
                    update_extra = self.neural_net(extrapolation_spots, update_data)

                gridx_update, gridy_update, gridz_update = self.interpolation(update_extra)

                grid_array =[]

                grid_array.append(gridx_update) #0. 보간법이 적용된 x 값
                grid_array.append(gridy_update) #1. 보간법이 적용된 y 값
                grid_array.append(gridz_update) #2. 보간법이 적용된 z 값
                grid_array.append(update_z)     #3. 실제 센서 값

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
                    ax.contourf(gridx_update, gridy_update, gridz_update, zdir='z', offset=np.min(data[:, 2]), cmap=self.theme)
                    ax.contourf(gridx_update, gridy_update, gridz_update, zdir='x', offset=0, cmap=self.theme)
                    ax.contourf(gridx_update, gridy_update, gridz_update, zdir='y', offset=0, cmap=self.theme)
                    ax.set_zbound(self.min_bound, self.max_bound)
                    ax.view_init(azim=45)

                return ax,

        if method == 'gradation':
            fig = plt.figure(figsize=(10, 10))
            fig.suptitle(title, fontsize=18)
            ax = fig.gca(projection='3d')
            ax.plot_surface(gridx, gridy, gridz, alpha=0.5, cmap=self.theme)
            ax.set_zbound(self.min_bound, self.max_bound)
            ani = animation.FuncAnimation(fig, update_,interval=self.interval)
            plt.show()

        if method == 'rotate':
            fig = plt.figure(figsize=(10, 10))
            fig.suptitle(title, fontsize=18)
            ax = fig.gca(projection='3d')
            #ax.plot_wireframe(gridx, gridy, gridz, alpha=0.5)
            #ax.scatter(data[:, 0], data[:, 1], data[:, 2], c='red')
            ax.plot_surface(gridx, gridy, gridz, alpha=0.5, cmap=self.theme)
            ax.set_zbound(self.min_bound, self.max_bound)
            ani = animation.FuncAnimation(fig, update, np.arange(360 * 5), interval=1)
            plt.show()

        if method == 'wireframe':
            fig = plt.figure(figsize=(10, 10))
            fig.suptitle(title, fontsize=18)
            ax = fig.gca(projection='3d')
            ax.plot_wireframe(gridx, gridy, gridz, alpha=0.5)
            ax.scatter(data[:, 0], data[:, 1], data[:, 2], c='red')
            ax.set_zbound(self.min_bound, self.max_bound)
            ax.view_init(azim=45)
            ani = animation.FuncAnimation(fig, update_, interval=self.interval)
            plt.show()

        if method == 'contour':
            fig = plt.figure(figsize=(10, 10))
            fig.suptitle(title, fontsize=18)
            ax = fig.gca(projection='3d')
            ax.contourf(gridx, gridy, gridz, zdir='z', offset=np.min(data[:, 2]), cmap=self.theme)
            ax.contourf(gridx, gridy, gridz, zdir='x', offset=0, cmap=self.theme)
            ax.contourf(gridx, gridy, gridz, zdir='y', offset=0, cmap=self.theme)
            ax.set_zbound(self.min_bound, self.max_bound)
            ani = animation.FuncAnimation(fig, update_, interval=self.interval)
            ax.view_init(azim=45)
            plt.show()

'''
if __name__ == '__main__':
    plot= Plot(num =10,
     theme="Blues",
     min_bound=0,
     max_bound=110,
     height=1000,
     width=800,
     interval=1000,
     p_value=2,
     extr_interval=30,
     model ='nearest',  # 'nearest', 'kriging', 'neural'
     interpol_method='cubic', # 'nearest', 'linear', 'cubic'
     method ='gradation')  # wireframe  gradation contour rotate

    plot.main()
    sys.exit()


'''
def Main(num, theme, min_bound, max_bound,interval, p_value, extr_interval, model, interpol_method, method,matrix_num):
    #1. plot 만들기
    plot = Plot(num, theme, min_bound, max_bound,interval, p_value, extr_interval, model, interpol_method, method,matrix_num)
    # 2. plot main 함수 실행
    plot.main()
    sys.exit()
    return result


result = Main(num=10,
     theme="coolwarm",
     min_bound=0,
     max_bound=110,
     interval=1000,
     p_value=0.5,
     extr_interval=30,
     model='nearest',  # 'nearest', 'kriging', 'neural'
     interpol_method='cubic',  # 'nearest', 'linear', 'cubic'
     method='gradation', # gradation contour rotate wireframe
     matrix_num = 3 # 3 5 7 9 ..  2n+1 (n>=1)의 값만 가능
     )

print("-- result --")
print(result)