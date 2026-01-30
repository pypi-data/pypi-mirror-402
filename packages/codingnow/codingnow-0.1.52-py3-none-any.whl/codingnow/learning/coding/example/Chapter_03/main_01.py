# import os
# os.system('pip install codingnow --upgrade')
from codingnow.learning.coding.codingTest import *

coding = CodingTest()
coding.start(chapter=2)

#최대 값
a = coding.get()
b = coding.get()

if a > b:
    c = a
else:
    c = b

coding.answer(c)

#최소 값
a = coding.get()
b = coding.get()
if a < b:
    c = a
else:
    c = b

coding.answer(c)


#짝수개수
a = coding.get()
b = coding.get()

cnt = 0
if a % 2 == 0:
    cnt += 1
if b % 2 == 0:
    cnt += 1
coding.answer(cnt)
        
    
#짝수개수
a = coding.get()
b = coding.get()

cnt = 0
if a % 2 == 1:
    cnt += 1
if b % 2 == 1:
    cnt += 1
coding.answer(cnt)

#합계
a = coding.get()
b = coding.get()
c = a + b
coding.answer(c)

#평균
a = coding.get()
b = coding.get()
c = a + b
c = c / 2
coding.answer(c)