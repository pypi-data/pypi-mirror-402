# import os
# os.system('pip install codingnow --upgrade')
from codingnow.learning.coding.codingTest import *

coding = CodingTest()
coding.start(chapter=3)

lower = coding.get_option('lower')
print('lower:', lower)

upper = coding.get_option('upper')
print('upper:', upper)

answer = (upper + lower)//2

while True:
    
    if coding.answer(answer) == False:
        break
    
    result = coding.get()
    if result == '정답':
        break
    elif result == 'down':
        upper = answer
        answer = (answer + lower)//2
    elif result == 'up':
        lower = answer
        answer = (upper + answer)//2