import codingnow

coding = codingnow.CodingTest()
coding.start(2)


while True:
    values = []
    op = ''
    result = 0
    while True:
        value = coding.get()
        if value == 'END':
            break
        if value in ['추가', '합', '평균', '길이', '짝수합', '홀수합']:
            op = value
            continue
        
        values.append(value)
        
    if op == '추가':
        result = values
    elif op == '합':
        result = sum(values)
    elif op == '평균':
        result = sum(values) / len(values) if values else 0
    elif op == '길이':
        result = len(values)
    elif op == '짝수합':
        result = sum(v for v in values if v % 2 == 0)
    elif op == '홀수합':
        result = sum(v for v in values if v % 2 != 0)
        
    if coding.answer(result) == False:
        break

