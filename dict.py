my_dict = {}

key_1 = input("Enter key 1: ")
value_1 = input("Enter value 1: ")

my_dict[key_1] = value_1

key_2 = input("Enter key 2: ")
value_2 = input("Enter value 2: ")

my_dict[key_2] = value_2

key_3 = input("Enter key 3: ")
value_3 = input("Enter value 3: ")

my_dict[key_3] = value_3

print(my_dict)

del my_dict[key_3]

my_dict[key_3] = "100, abc"

print(my_dict)
