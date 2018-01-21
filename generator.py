from random import shuffle

list_whom=["Serezha", "Vitya", "Tasha", "Lesha#1", "Lesha#2", "Zhenya"]
list_who=list(list_whom)

shuffle(list_whom)
shuffle(list_who)

whom_i = 0
for who in list_who:
    if who == list_whom[whom_i]:
        temp = list_whom[whom_i]
        list_whom[whom_i] = list_whom[whom_i+1]
        list_whom[whom_i + 1] = temp
    file = open(who+".txt", "w")
    file.write(list_whom[whom_i])
    file.close()
    whom_i += 1