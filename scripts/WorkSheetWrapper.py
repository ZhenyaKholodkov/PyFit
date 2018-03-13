'''
Class WorkSheetWrapper
'''

from scipy import signal
from enum import Enum
from numpy import array
import PyOrigin


def find_index_of_nearest(sorted_array, number):
    left = 0
    right = len(sorted_array) - 1
    middle = int(right / 2)
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
            middle = int((right + left) / 2)
        else:
            left = middle + 1
            right = right
            middle = int((right + left) / 2)
    return middle

class FilterType(Enum):
    LFilter = 0
    FILTFILT = 1

class ColumnType(Enum):
    ColumnType_Y = 0
    ColumnType_Disregard = 1
    ColumnType_Y_Error = 2
    ColumnType_X = 3
    ColumnType_Label = 4
    ColumnType_Z = 5
    ColumnType_X_Error = 6

class WorkSheetWrapper:
    @staticmethod
    def create_new_worksheet(new_book, new_page):
        wks = PyOrigin.CreatePage(PyOrigin.PGTYPE_WKS, new_book, new_page, 1)
        return WorkSheetWrapper(wks.Layers(0))

    def __init__(self, wks):
        self._workSheet = wks
        self._sheetName = wks.GetLongName()
        self._colNames = [poCol.GetName() for poCol in wks.Columns()]
        self._colDesc = [poCol.GetLongName() for poCol in wks.Columns()]
        self._colUnits = [poCol.GetUnits() for poCol in wks.Columns()]
        self._colComments = [poCol.GetComments() for poCol in wks.Columns()]
        self._colTypes = [poCol.GetType() for poCol in wks.Columns()]
        self._colData = [poCol.GetData() for poCol in wks.Columns()]

    def get_x_from_comments(self):
        return [float(value.replace(",", ".")) for value in self._colComments[1:len(self._colComments)]]

    def show_data(self):
        for data in self._colData:
            print(data)

    def get_worksheet_name(self):
        return self._sheetName

    def get_column_num(self):
        return len(self._colData)

    def get_x(self, markers=None):
        if markers is not None and markers.is_not_none():
            x_data = array(self._colData[0])
            left_marker__index = find_index_of_nearest(x_data, markers.left_value)
            right_marker__index = find_index_of_nearest(x_data, markers.right_value) + 1
            return x_data[left_marker__index:right_marker__index]
        return array(self._colData[0])

    def get_y_data(self):
        '''b, a = signal.butter(3, 0.5)
        print(b)
        print(a)
        y_dataset = []
        for y in self._colData[1:len(self._colData)]:
            #zi = signal.lfilter_zi(b, a)
            y_dataset.append(signal.lfilter(b, a, y))
        return array(y_dataset)'''
        return array(self._colData[1:len(self._colData)])

    def set_data_column(self, data, column):
        row = 0
        for cell_value in data:
            self._workSheet.SetCell(row, column, cell_value)
            row += 1

    def set_cell_value(self, data, row, col):
        self._workSheet.SetCell(row, col, data)

    def set_size(self, col_num):
        self._workSheet.SetSize(0, col_num)

    #Columns operations
    def delete_col(self, col_num):
        self._workSheet.DeleteCol(col_num)

    def add_col(self, col_num, col_name):
        self._workSheet.InsertCol(col_num, col_name)

    def set_col_name(self, col_num, name):
        self._workSheet.Columns(col_num).SetUserDefLabel(name)

    def set_col_type(self, col_num, type):
        self._workSheet.Columns(col_num).SetType(type)