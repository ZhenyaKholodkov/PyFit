def find_index_of_nearest(sorted_array, number):
    left = 0
    right = len(sorted_array) - 1
    middle = right / 2
    while right is not left:
        d_left = abs(sorted_array[middle - 1] - number)
        d_middle = abs(sorted_array[middle] - number)
        d_right = abs(sorted_array[middle + 1] - number)
        # check if the middle is nearest element to number
        if d_middle < d_left and d_middle < d_right:
            return middle
        # get the next half of array where the nearest element is
        if d_left < d_right:
            left = left
            right = middle - 1
            middle = (right + left) / 2
        else:
            left = middle + 1
            right = right
            middle = (right + left) / 2
    return middle

array = [1,3,4,5,6,7,10,12,13,14,15,16,17,20,21,22,23,24,27,28,29,30]
array_res = [1,1,1,3,4,5,6,7,7,10,10,10,12,13,14,15,16,17,17,20,20,21,22,23,24,24,27,27,28,29,30]

for i in range(0, 31):
    print(i)
    res = find_index_of_nearest(array, i)
    if array_res[i] is not array[res]:
        print("Wrong i - {}, res - {}".format(i, array[res]))


class MarkerSetting:
    def __init__(self):
        self.left_value = None
        self.right_value = None

    def set_left_value(self, value):
        self.left_value = value

    def set_right_value(self, value):
        self.right_value = value


def change(sett):
    sett.set_left_value(5)


sett_t = MarkerSetting()
sett_t.set_left_value(2)
sett_t.set_right_value(8)
change(sett_t)
print(sett_t.left_value)