words = "나는 파이썬을 공부하고 있습니다. 파이썬은 무척 심플하고 명료합니다.".split()

len_list = [len(word) for word in words]

print(len_list)

print(len(len_list))

len_list_if_filtering = [len(word) for word in words if len(word) > 3]

print(len_list_if_filtering)

print(len(len_list_if_filtering))

my_list = [1, '2', 3, '4', 5, [6, 7], 8, 9]

my_list.append('10')
print(my_list)
print(len(my_list))

my_list.append(1)
print(my_list)
print(len(my_list))

my_list.remove(1)
my_list.remove(1)

print(my_list)
print(len(my_list))
print(my_list.index(8))

my_list.reverse() #my_list.sort()
print(my_list)
