# import os
# os.system('pip install codingnow --upgrade')
from codingnow.learning.coding.codingTest import *

coding = CodingTest()
coding.start(chapter=3)

lower = coding.get_option('lower')
print('lower:', lower)

upper = coding.get_option('upper')
print('upper:', upper)