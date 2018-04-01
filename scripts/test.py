
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QTableWidget, QShortcut, QVBoxLayout, QTableWidgetItem

class WorkSheetWrapper:
    def __init__(self, data):
        self._colData = data

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

class Widget(QtWidgets.QDialog):
    def __init__(self,parent=None):
        QtWidgets.QDialog.__init__(self,parent)
        # initially construct the visible table
        self.tv=QTableWidget()
        self.tv.setRowCount(1)
        self.tv.setColumnCount(1)
        self.tv.show()

        # set the shortcut ctrl+v for paste
        QShortcut(QKeySequence('Ctrl+v'),self).activated.connect(self._handlePaste)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tv)



    # paste the value
    def _handlePaste(self):
        clipboard_text = QApplication.instance().clipboard().text()
        print(clipboard_text)
        rows = clipboard_text.split('\n')
        lines = [line.split() for line in rows]
        rows = len(lines)
        cols = len(lines[0])
        self.tv.setRowCount(rows)
        self.tv.setColumnCount(cols)
        row_i = 0
        col_i = 0
        for line in lines:
            #print(line)
            #print("\n")
            for number in line:
                try:
                    item = QTableWidgetItem()
                    item.setText(number)
                    self.tv.setItem(col_i, row_i, item)
                except Exception as inst:
                    print(inst)
                row_i += 1
            row_i = 0
            col_i += 1



app = QApplication([])

w = Widget()
w.show()

app.exec_()