from codingnow.learning.coding.Chapters.chapter_01 import *
from codingnow.learning.coding.Chapters.chapter_02 import *
from codingnow.learning.coding.Chapters.chapter_03 import *
from codingnow.learning.coding.Chapters.chapter_find_number import *
from codingnow.learning.coding.Chapters.chapter_baseball_game import *
        
class CodingTest:
    chapter = 1
        
    def __init__(self):
        print()
        print("\033[31m",end='')
        print("코딩 테스트 시작 1~5",end='')
        print("\033[0m")
        
    def start(self,chapter):
        self.chapter = chapter
        if self.chapter == 1:
            self.instance = Chapter_01()
            self.instance.start()
        elif self.chapter == 2:
            self.instance = Chapter_02()
            self.instance.start()
        elif self.chapter == 3:
            self.instance = Chapter_03()
            self.instance.start()
        elif self.chapter == 4:
            self.instance = Chapter_find_number()
            self.instance.start()
        elif self.chapter == 5:
            self.instance = Chapter_baseball_game()
            self.instance.start()
        else:
            print("해당 챕터는 준비중입니다.")
    
    def get(self):
        print(" \033[34m",end='')
        print("get -> ",end='')
        print("\033[0m",end='')
        return self.instance.get()
    
    def answer(self, answer):
        return self.instance.answer(answer)
        
    def get_option(self,cmd):
        return self.instance.get_option(cmd)
    
    def print_options(self):
        self.instance.print_options()