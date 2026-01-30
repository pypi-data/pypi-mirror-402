# from codingnow import *
import codingnow


def strike_check(idex:int,strike_cnt:int):    
    for i in range(1,9):
        answer_guess[idex] = i        
        answer = ''.join(map(str, answer_guess))
        coding.answer(answer)
        result = coding.get()
        if result['strike'] > strike_cnt:
            return (i,result['strike'])

coding = codingnow.CodingTest()
coding.start(4)

answer_guess = [0,0,0]

strike_cnt = 0
answer_guess[0],strike_cnt = strike_check(0, strike_cnt)
answer_guess[1],strike_cnt = strike_check(1, strike_cnt)
answer_guess[2],strike_cnt = strike_check(2, strike_cnt)

print("Final Answer:", ''.join(map(str, answer_guess)))
