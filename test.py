s = [[1,2,3,], [4,0,1], [5,12,6]]
print(s)
s.sort(key=lambda tup: tup[1], reverse=True)
print(s)