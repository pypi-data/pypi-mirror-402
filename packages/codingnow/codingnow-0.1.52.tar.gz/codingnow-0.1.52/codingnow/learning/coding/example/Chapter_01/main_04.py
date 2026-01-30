import os
os.system('pip install codingnow --upgrade')
from codingnow.learning.coding.codingTest import *

coding = CodingTest()
coding.start(chapter=1)

while True:
    answer = 0
    cnt = 0
    op = ''
    values = []
    while True:
        value = coding.get()
        
        if value == 'END':
            break
        
        if str(value) in ['+', '-', '*', '/', '//', '%']:
            op = value
            continue
        
        values.append(value)
    
    calculate = str(values[0]) + op + str(values[1])
    answer = eval(calculate)

    result = coding.answer(answer)
    if result:
        continue
    else:
        break
    