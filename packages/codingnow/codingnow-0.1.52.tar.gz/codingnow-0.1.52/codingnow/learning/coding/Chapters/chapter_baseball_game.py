import random

# Black	30	\033[30m
# Red	31	\033[31m
# Green	32	\033[32m
# Yellow	33	\033[33m
# Blue	34	\033[34m
# White	37	\033[37m
# 초기화	0	\033[0m (반드시 끝에 넣어줘야 다음 줄에 영향이 없음)

class Chapter_baseball_game:
    chapter = '야구게임'
    step = 1   
    step_min = 1
    step_max = 1
    title = "간단한 게임"
    correct = 0
    guide_line_max = 50
    
    answer_limit_count = 10
    answer_count = 0
    strike = 0
    ball = 0
    
    
    def __init__(self):
        print("\033[32m=" * self.guide_line_max)
        print(f"코딩 테스트 - {self.title} : {self.chapter}")
        print("설명: 같은 자리의 수는 스트라이크, 다른 자리의 수는 볼이 출력됩니다.")
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

        self.strike = 0
        self.ball = 0
        self.correct = ''.join(random.sample(['1','2','3','4','5','6','7','8','9'],3))

        self.answer_limit_count = 100
        self.answer_count = 0
        self.is_return_operation = True
        print("\033[34m",end='')
        print(f"[문제 설명] 3자리 숫자를 맞춰보세요! (중복 숫자 없음) ",end='')
        print(f"정답 값: {self.correct}")
        print("=" * self.guide_line_max,end='')
        print("\033[0m")
                
    def get(self):
        return {"strike": self.strike, "ball": self.ball}
    
    def get_operation(self):
        return {"strike": self.strike, "ball": self.ball}

    def answer(self, answer):
        self.answer_count += 1
        print(f"\n\033[31m[결과 확인] 입력 값: {answer} 시도횟수 : {self.answer_count}\033[0m")
        # print()
        answer = str(answer)
        self.strike = 0
        self.ball = 0
        for i in range(3):
            if answer[i] == self.correct[i]:
                self.strike += 1
            elif answer[i] in self.correct:
                self.ball += 1
        print(f"\033[33m스트라이크: {self.strike}, 볼: {self.ball}\033[0m")
        
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
        else:
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
        print(f" * operation (현재결과) : {(self.strike, self.ball)}")
        print("\033[0m")
        
    def get_option(self, cmd):
        if cmd == 'operation':
            return (self.strike, self.ball)
        else:
            return None