# import os
# os.system('pip install codingnow --upgrade')
from codingnow.learning.coding.codingTest import *

coding = CodingTest()
coding.start(chapter=2)

while True:
    values = []
    op = ''

    while True:
        value = coding.get()
        if value == 'END':
            break
        
        if value in ['최대', '최소', '짝수개수', '홀수개수', '합계', '평균']:
            op = value
            continue
        
        values.append(value)   

    if op == '최대':
        answer = max(values)
    elif op == '최소':
        answer = min(values)
    elif op == '짝수개수':
        answer = sum(1 for v in values if v % 2 == 0)
    elif op == '홀수개수':
        answer = sum(1 for v in values if v % 2 == 1)
    elif op == '합계':
        answer = sum(values)
    elif op == '평균':
        answer = sum(values) / len(values)

    result = coding.answer(answer)
    if result:
        continue
    else:
        break