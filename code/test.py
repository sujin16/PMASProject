from module.matrixGraph import Main, grid_array
from module.valueZ import  num
print('hello')

result = Main(
     front_num = 10,
     end_num = 10,
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

print('nice to meet you')
print(result)

print("num"+ str(num))

result2 = Main(
     front_num = 10,
     end_num = 10,
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

print('nice to meet you')
print(result2)