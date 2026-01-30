# import os
# os.system('pip install codingnow --upgrade')
from codingnow.learning.coding.codingTest import *

coding = CodingTest()
coding.start(chapter=2)

coding.print_options()

oop = coding.get_option('operation')
print('oop:', oop)

length = coding.get_option('length')
print('length:', length)