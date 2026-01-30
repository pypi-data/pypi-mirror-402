import os
os.system('pip install codingnow --upgrade')
from codingnow.learning.coding.codingTest import *

coding = CodingTest()
coding.start(chapter=1)

a = coding.get()
b = coding.get()
# op = coding.get()
op = coding.get_option('operation')

if op == '+':
    c = a + b
elif op == '-':
    c = a - b
elif op == '*':
    c = a * b
elif op == '/':
    c = a / b
elif op == '//':
    c = a // b
elif op == '%':
    c = a % b

coding.answer(c)