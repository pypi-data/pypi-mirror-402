import codingnow

coding = codingnow.CodingTest()
coding.start(2)

values = []

while True:
    value = coding.get()
    if value == 'END':
        break
    values.append(value)
    
print(values)
