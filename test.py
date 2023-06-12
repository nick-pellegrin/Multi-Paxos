import sys
import math


# id = str(sys.argv[1])
# idNum = int([*id][1])

# print(id)
# print(idNum)

# dictionary = {}
# keys_to_delete = []
# dictionary[1] = "conn1"
# dictionary[2] = "conn2"
# dictionary[3] = "conn3"
# n =  math.ceil((len(dictionary) + 1)/2)
# print(n)

# print(dictionary)
# for key,value in dictionary.items():
#     if value == "conn2":
#         keys_to_delete.append(key)
# for key in keys_to_delete:
#     del dictionary[key]

# if 4 not in dictionary:
#     dictionary[4] = "conn4"

# print(dictionary)

# for i in range(1,4):
#     print(i)

# n = 4/2
# print(n)
# print(math.ceil(n))

lines = open("N2_blockchain_log.txt", 'r').readlines()
for line in lines:
    line = line[:-1]
    print(line)

