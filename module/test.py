import os

print(os.path.isdir("D:/2019_2_intern/Project/0511Project/code"))

from pathlib import Path

p =Path('D:\2019_2_intern\Project\0511Project\code')

print(p.exists())
print(p.is_dir())
