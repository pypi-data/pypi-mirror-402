import random

# Black	30	\033[30m
# Red	31	\033[31m
# Green	32	\033[32m
# Yellow	33	\033[33m
# Blue	34	\033[34m
# White	37	\033[37m
# 초기화	0	\033[0m (반드시 끝에 넣어줘야 다음 줄에 영향이 없음)

class Chapter_01:
    chapter = 1
    step = 1   
    step_min = 1
    step_max = 10
    title = "변수 사용 및 연산"
    problem_lst = []
    problem_idx = 0 
    correct = 0
    guide_line_max = 50
    operation = ['+', '-', '*', '/','//', '%']
    current_operation = '+'
    is_return_operation = False
    
    
    def __init__(self):
        print("\033[32m=" * self.guide_line_max)
        print(f"코딩 테스트 - Chapter {self.chapter}: {self.title}")
        print("설명: 주어진 숫자의 사칙연산 값을 구하세요.")
        print(f"{self.operation}")
        print(f"현재 챕터는 총 {self.step_max} 단계입니다.")
        print()
        print("사용법:")
        print(" 1. result = coding.get()  # 생성된 문제값을 순서대로 반환, 반환값이 없으면 'END' 반환")
        print(" 2. if coding.answer(answer) == False:  # 틀리거나 모든 문제를 통과하면 False 반환")
        print(" 3. coding.print_options()  # 사용가능한 옵션 정보 출력")
        print(" 4. value = coding.get_option(cmd)  # 옵션값 반환 (cmd: operation, length)")
        
        print("=" * self.guide_line_max,end='')
        print("\033[0m",end='')
        print("\n"*1)
        
        print("\033[34m",end='')
        print("=" * self.guide_line_max,end='')
        print("\033[0m")
    
    
    def start(self):
        if self.step < self.step_min or self.step > self.step_max:
            print(f"잘못된 단계를 입력했습니다. {self.step_min} ~ {self.step_max}.")
            return
        
        print("\033[34m",end='')
        print(f"[{self.step} 단계] ",end='')
        print("\033[0m")
        self.problem_idx = 0        
        self.problem_lst = [random.randint(10,100) for _ in range(2) ]
        
        if self.step <= 6:
            self.current_operation = self.operation[self.step - 1]
        else:
            self.current_operation = random.choice(self.operation)
            print("\033[31m",end='')
            print("현재 단계는 랜덤 연산자 단계입니다.",end='')
            print("\033[0m")
        
        self.is_return_operation = True
        print("\033[34m",end='')
        if self.current_operation == '+':
            print("주어진 두 숫자의 더한 값을 구하세요.")
            self.correct = sum(self.problem_lst)
        elif self.current_operation == '-':
            print("주어진 두 숫자의 차감한 값을 구하세요.")
            self.correct = self.problem_lst[0] - self.problem_lst[1]
        elif self.current_operation == '*':
            print("주어진 두 숫자의 곱한 값을 구하세요.")
            self.correct = self.problem_lst[0] * self.problem_lst[1]
        elif self.current_operation == '/':
            print("주어진 두 숫자의 나눈 값을 구하세요.")
            self.correct = self.problem_lst[0] / self.problem_lst[1]
        elif self.current_operation == '//':
            print("주어진 두 숫자의 나눈 몫을 구하세요.")
            self.correct = self.problem_lst[0] // self.problem_lst[1]
        elif self.current_operation == '%':
            print("주어진 두 숫자의 나눈 나머지를 구하세요.")
            self.correct = self.problem_lst[0] % self.problem_lst[1]

        print(f" * 문제값 : {len(self.problem_lst)}개")
        print(f" * 연산자 : 1개")
        print("=" * self.guide_line_max,end='')
        print("\033[0m")
                
    def get(self):
        if self.problem_idx >= len(self.problem_lst):
            if self.is_return_operation:
                print("\033[33m",end='')
                print(f"{self.current_operation}",end='')
                print("\033[0m")
                self.is_return_operation = False
                return self.current_operation
            
            print("\033[33m",end='')
            print(f"END",end='')        
            print("\033[0m")
            return 'END'
        
        value = self.problem_lst[self.problem_idx]
        
        print("\033[33m",end='')
        print(f"{value}",end='')        
        print("\033[0m")
        self.problem_idx += 1
        return value
    
    def get_operation(self):
        return self.current_operation
    
    def answer(self, answer):
        print(f"\n\033[31m[결과 확인]\n 입력 값: {answer}\n 정답 값: {self.correct}\033[0m")
        print()
        if answer == self.correct:
            print("정답!!")
            print()
            
            self.step += 1
            if self.step > self.step_max:
                print("축하합니다! 모든 단계를 완료했습니다.")
                self.step = self.step_max
                print("=" * self.guide_line_max)
                print()
                return False
            else:
                
                print("\033[34m",end='')
                print("=" * self.guide_line_max,end='')
                print("\033[0m")
                # print(f"다음 단계로 이동합니다. Step: {self.step}")
                self.next()
                # print()
                return True
        else:
            print(f"오답!! 정답은 {self.correct} 입니다.")
            print("=" * self.guide_line_max)
            print()
            return False

    def next(self):
        if self.step <= self.step_max:
            self.start()
        else:
            print("이미 마지막 단계입니다.")
            
            
    def print_options(self):
        print("\033[33m",end='')
        print()
        print("[옵션 정보]")
        print(f" * operation (현재 연산자): {self.current_operation}")
        print(f" * length    (문제값 개수): {len(self.problem_lst)}",end='')
        print("\033[0m")
        
    def get_option(self, cmd):
        if cmd == 'operation':
            return self.current_operation
        elif cmd == 'length':
            return len(self.problem_lst)
        else:
            return None