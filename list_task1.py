# 1st Task - 5 elements list

orig_list = [
    123, "AMD", True, None, 65.5
]

# 2nd Task

orig_list.pop(2)

print(orig_list)  # [123, 'AMD', None, 65.5]

# 3rd Task

print(len(orig_list))  # 4

# 4th Task

orig_list.reverse()
print(orig_list)  # [65.5, None, 'AMD', 123]

# 5Th Task

new_list = [
    "BMW", 67
]

# 6th Task

orig_list = orig_list + new_list

# 7th Task
print(orig_list)  # [65.5, None, 'AMD', 123, 'BMW', 67]
