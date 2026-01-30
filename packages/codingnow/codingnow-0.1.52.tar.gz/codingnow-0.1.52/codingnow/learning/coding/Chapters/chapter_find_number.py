import random

# Black	30	\033[30m
# Red	31	\033[31m
# Green	32	\033[32m
# Yellow	33	\033[33m
# Blue	34	\033[34m
# White	37	\033[37m
# 초기화	0	\033[0m (반드시 끝에 넣어줘야 다음 줄에 영향이 없음)

class Chapter_find_number:
    chapter = '숫자 맞추기'
    step = 1   
    step_min = 1
    step_max = 1
    title = "간단한 게임"
    number_lower = 1
    number_upper = 100
    correct = 0
    guide_line_max = 50
    operation = ['up', 'down','정답']
    current_operation = '없음'
    is_return_operation = False
    
    answer_limit_count = 10
    answer_count = 0
    
    
    def __init__(self):
        print("\033[32m=" * self.guide_line_max)
        print(f"코딩 테스트 - {self.title} : {self.chapter}")
        print("설명: 입력한 숫자보다 크면 'up', 작으면 'down', 같으면 '정답'이 출력됩니다.")
        print(f"출력되는 값 : {self.operation}")
        print(f"현재 챕터는 총 {self.step_max} 단계입니다.")
        print()
        print("사용법:")
        print(" 1. lower = coding.get_option('lower')  # 하위값")
        print(" 2. upper = coding.get_option('upper')  # 상위값")
        print(" 3. if coding.answer(answer) == False:  # 정답을 맞추거나 제한횟수를 넘으면 False 반환")
        print(" 4. result =coding.get()  # 현재 결과 값 반환 ('up', 'down', '정답')")
        
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
        
        self.number_upper = (self.step) * 100
        self.correct = random.randint(self.number_lower, self.number_upper)

        self.answer_limit_count = 10
        self.answer_count = 0
        self.is_return_operation = True
        print("\033[34m",end='')
        print(f"[문제 설명] 주어진 숫자를 맞추세요. 숫자는 {self.number_lower} 부터 {self.number_upper} 사이입니다.")
        print("=" * self.guide_line_max,end='')
        print("\033[0m")
                
    def get(self):
        return self.current_operation
    
    def get_operation(self):
        return self.current_operation
    
    def answer(self, answer):
        self.answer_count += 1
        print(f"\n\033[31m[결과 확인] 입력 값: {answer} 시도횟수 : {self.answer_count}\033[0m")
        # print(f"정답 값: {self.correct}")
        # print()
        if answer == self.correct:
            print("\033[31m정답!!\033[0m")
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
                return False
        elif self.answer_count >= self.answer_limit_count:
            print(f"\n\033[31m답안 시도 횟수 초과!! 정답은 {self.correct} 입니다.\033[0m")
            print("=" * self.guide_line_max)
            print()
            return False
        elif answer < self.correct:
            self.current_operation = 'up'
            print("\033[33mup\033[0m")
            print("=" * self.guide_line_max)
            print()
            return True
        else:
            self.current_operation = 'down'
            print("\033[33mdown\033[0m")
            print("=" * self.guide_line_max)
            print()
            return True

    def next(self):
        if self.step <= self.step_max:
            self.start()
        else:
            print("이미 마지막 단계입니다.")
            
            
    def print_options(self):
        print("\033[33m",end='')
        print()
        print("[옵션 정보]")
        print(f" * operation (현재결과) : {self.current_operation}")
        print(f" * lower     (하위값): {self.number_lower}")
        print(f" * upper     (상위값): {self.number_upper}",end='')
        print("\033[0m")
        
    def get_option(self, cmd):
        if cmd == 'operation':
            return self.current_operation
        elif cmd == 'lower':
            return self.number_lower
        elif cmd == 'upper':
            return self.number_upper
        else:
            return None