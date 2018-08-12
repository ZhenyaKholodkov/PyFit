
from orgn_peak_finder import find_peaks
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QKeySequence, QColor, QBrush
from PyQt5.QtWidgets import QHBoxLayout, QMessageBox, QProgressBar, QMainWindow, QApplication,\
    QTableWidget, QShortcut, QVBoxLayout, QTableWidgetItem, QPushButton, QFileDialog


from orgn_graph_widget import OrgnGrpahWidget


class ResultVisulizer:
    def __init__(self, result_table, layout):
        self.table_widget = result_table
        self.plot_widget = OrgnGrpahWidget(figsize=(20, 20), settings=None,
                                        animate_call_back=self.show_data_on_graph_with)
        self.canvas = self.plot_widget.get_canvas()
        layout.addWidget(self.canvas)
        layout.setStretchFactor(self.canvas, 75)
        self.fit_result = None
        self.table_widget.cellClicked.connect(self.on_cell_clicked)

    def on_cell_clicked(self, row, col):
        self.show_data_on_graph_with(col)
        self.canvas.draw()

    def init_tables_with(self, fit_result):
        self.fit_result = fit_result
        self.table_widget.setColumnCount(len(fit_result.fit_params.items()))
        labels = ""
        col = 0
        for param_name, params in fit_result.fit_params.items():
            labels += param_name
            labels += ';'
            if self.table_widget.rowCount() is 0:
                self.table_widget.setRowCount(len(params))

            row = 0
            for param in params:
                value_item = QTableWidgetItem()
                value_item.setText(str(param))
                self.table_widget.setItem(row, col, value_item)
                row += 1
            col += 1

        self.table_widget.setHorizontalHeaderLabels(labels.split(";"))

    def show_data_on_graph_with(self, i):
        self.plot_widget.remove_lines()
        x_data = self.fit_result.x_data
        if len(x_data) != len(self.fit_result.fit_data[i]):
            return
        self.plot_widget.add_line(x_data, self.fit_result.fit_data[i], 'k')
        if len(self.fit_result.component_data) > i:
            for ii, peak_contour in enumerate(self.fit_result.component_data[i]):
                    color = self.plot_widget.possible_colors[0]
                    if len(self.plot_widget.possible_colors) > ii:
                        color = self.plot_widget.possible_colors[ii]
                    self.plot_widget.add_line(x_data, peak_contour, color)