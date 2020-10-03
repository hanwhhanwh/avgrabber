words = "나는 파이썬을 공부하고 있습니다. 파이썬은 무척 심플하고 명료합니다.".split()

len_list = [len(word) for word in words]

print(len_list)

print(len(len_list))

len_list_if_filtering = [len(word) for word in words if len(word) > 3]

print(len_list_if_filtering)

print(len(len_list_if_filtering))
