import matplotlib

matplotlib.use('Qt5Agg', force=True)

import csv
import sys
import numpy as np
from orgn_result import ResultVisulizer
from orgn_graph_widget import OrgnGrpahWidget
from orgn_settings import Setting
from orgn_settings import SettingsDialog
from orgn_fitting_dialog import WorkSheetWrapper
from orgn_fitting_dialog import Window_fitting
from orgn_fitter import OrgnFitterThread
from orgn_peak_finder import find_peaks
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QKeySequence, QColor, QBrush
from PyQt5.QtWidgets import QHBoxLayout, QMessageBox, QProgressBar, QMainWindow, QApplication,\
    QTableWidget, QShortcut, QVBoxLayout, QTableWidgetItem, QPushButton, QFileDialog, QSizePolicy

from PyQt5.QtGui import QCursor
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from orgn_peak_finder import find_peaks

# progress bar that shows the progress of fitting. Thread-safe Mechanism of signals and slots allow to get
# the completed status of fitting from the thread to that dialog
class ProgressDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(ProgressDialog, self).__init__(parent)
        self.progress = QProgressBar(self)
        self.progress.setGeometry(200, 80, 250, 20)

        button_box = QHBoxLayout()
        self.ok_button = QPushButton('Ok', self)
        self.ok_button.clicked.connect(self.exit_fom_fitting)
        self.ok_button.setEnabled(False)
        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.clicked.connect(self.exit_fom_fitting)
        button_box.addWidget(self.ok_button)
        button_box.addWidget(self.cancel_button)

        layout = QVBoxLayout()
        layout.addWidget(self.progress)
        layout.addLayout(button_box)
        self.setLayout(layout)
        self.setWindowTitle("Fitting...")

    def update_progress(self, value):
        self.progress.setValue(value)
        if value is 100:
            self.ok_button.setEnabled(True)

    def exit_fom_fitting(self):
        self.accept()

# overloading of NavigationToolbar make possible to add custom buttons to the tool bar
class OrgnToolbar(NavigationToolbar):
    def __init__(self, plotCanvas, dialog):
        # create the default toolbar
        NavigationToolbar.__init__(self, plotCanvas, dialog)

    # method that makes possible to add custom button
    def add_button(self, image_file, text, callback):
        self._actions[callback] = self.addAction(self._icon(image_file), text, callback)

def catch_exceptions(t, val, tb):
    QtWidgets.QMessageBox.critical(None,
                                   "An exception was raised",
                                   "Exception type: {}".format(t))
    #old_hook(t, val, tb)


qtCreatorFile = "../res/gui.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class FittingApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.settings = Setting()
        self.indexes = []
        self.peaks = []
        self.last_fit_result = None
        self.progress_dlg = None
        self.fit_thread = None
        self.current_data = 0
        self.max_amplitude = 0
        self.can_set_peak = False
        self.is_fir_result_showed = False
        self.wks_wrapper = None
        self.last_fit_result = None

        self.plotWidget = OrgnGrpahWidget(figsize=(20, 20), settings=self.settings,
                                        animate_call_back=self.show_data_on_graph_with)

        self.result_visualizer = ResultVisulizer(self.result_table, self.result_layout)

        self.canvas = self.plotWidget.get_canvas()
        self.tableWidget.setRowCount(1)
        self.tableWidget.setColumnCount(1)
        self.tableWidget.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.tabWidget.currentChanged.connect(self.on_tab_changed)
        QShortcut(QKeySequence('Ctrl+v'), self).activated.connect(self._handlePaste)

        self.actionOpen_file.triggered.connect(self.openFile)
        self.actionSittings.triggered.connect(self.show_model_settings)
        self.actionSittings.setDisabled(True)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = OrgnToolbar(self.canvas, self)
        #images_path = PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "PyFit/res/"
        images_path = "../res/"

        self.toolbar.addSeparator()
        self.toolbar.add_button(images_path + "markers.png", "Add Markers", self.add_markers)
        self.toolbar.addSeparator()
        self.toolbar.add_button(images_path + "play_anim.png", "Animate", self.animate_peaks)
        self.toolbar.add_button(images_path + "stop_anim.png", "Stop Animate", self.stop_animate_peaks)
        self.toolbar.addSeparator()
        self.toolbar.add_button(images_path + "crosshairs.png", "Add Peak", self.enable_set_peak)
        self.toolbar.addSeparator()
        #self.toolbar.add_button(images_path + "to_wks.png", "Save result to new table", self.save_result_to_wks)
        self.toolbar.addSeparator()
        self.toolbar.add_button(images_path + "fit.png", "Fit", self.fit)
        self.toolbar.add_button(images_path + "Last.png", "Load last fit", self.load_last_fit)
        self.toolbar.add_button(images_path + "Peaks.png", "Show current peaks", self.find_peaks)
        self.addToolBar(self.toolbar)
        self.prevBtn.clicked.connect(self.on_prev_anim)
        self.nextBtn.clicked.connect(self.on_next_anim)
        self.anim_slider.valueChanged.connect(self.on_slider_value_changed)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.tab_matplot.setLayout(layout)
        self.tab_table.setLayout(self.tableLayout)
        self.tab_result.setLayout(self.result_layout)

    def show_model_settings(self):
        settings_dlg = SettingsDialog(self.settings, self)
        settings_dlg.peak_settings_changed.connect(self.find_peaks)
        settings_dlg.initWksSettings()
        settings_dlg.show()

    def add_markers(self):
        if self.is_fir_result_showed:
            return

        if self.plotWidget.is_ver_markers_shown():
            self.plotWidget.hide_ver_markers()
            return

        x = self.wks_wrapper.get_x()
        self.plotWidget.show_ver_markers(x[0], x[len(x) - 1], 0, self.max_amplitude)

    def animate_peaks(self):
        self.plotWidget.show_animation(self.settings.animation_interval)

    def stop_animate_peaks(self):
        self.plotWidget.stop_animation()

    def enable_set_peak(self):
        self.can_set_peak = True
        QApplication.setOverrideCursor(QCursor(Qt.CrossCursor))

    def find_peaks(self):
        try:
            self.indexes, self.max_amplitude = find_peaks(self.wks_wrapper, self.settings.peak_function, mph=self.settings.min_amplitude,
                                  mpd=self.settings.min_peak_dist, threshold=self.settings.threshold)
        except Exception as ex:
            print(ex)
        # self.cb.clear()
        self.is_fir_result_showed = False
        # self.cb.setEnabled(False)
        # show peaks
        self.plotWidget.set_title('Peak finding')
        self.show_data_on_graph_with(0)
        self.plotWidget.autoscale()
        self.plotWidget.autoscale(False)
        self.plotWidget.set_y_lim((0, 1.1 * self.max_amplitude))
        self.canvas.draw()

    def fit(self):
        self.fit_thread = OrgnFitterThread(self,
                                           self.wks_wrapper, self.indexes,
                                           self.settings)
        self.progress_dlg = ProgressDialog(self)

        self.progress_dlg.accepted.connect(self.fit_thread.stop_fit)
        self.progress_dlg.rejected.connect(self.fit_thread.stop_fit)
        self.fit_thread.finished.connect(self.fitting_finished)
        self.fit_thread.complete_changed.connect(self.progress_dlg.update_progress)
        self.fit_thread.exception_occur.connect(self.fitting_exception_occur)

        self.progress_dlg.show()
        self.fit_thread.start()

        self.progress_dlg.exec_()

    def show_data_on_graph_with(self, i):
        if self.wks_wrapper.is_empty():
            return

        self.plotWidget.remove_lines()
        if self.is_fir_result_showed and i < len(self.last_fit_result.fit_data):
            self.anim_slider.setValue(i)
            x_data = self.last_fit_result.x_data
            if len(x_data) != len(self.last_fit_result.fit_data[i]):
                return
            self.plotWidget.add_line(x_data, self.last_fit_result.fit_data[i], 'k')
            if len(self.last_fit_result.component_data) > i:
                for ii, peak_contour in enumerate(self.last_fit_result.component_data[i]):
                        color = self.plotWidget.possible_colors[0]
                        if len(self.plotWidget.possible_colors) > ii:
                            color = self.plotWidget.possible_colors[ii]
                        self.plotWidget.add_line(x_data, peak_contour, color)
        else:
            self.plotWidget.add_line(self.wks_wrapper.get_x(), self.wks_wrapper.get_y_data()[i], 'k')
            self.plotWidget.add_line(self.wks_wrapper.get_x(), self.wks_wrapper.get_y_data()[i], 'bo')
            self.plotWidget.add_line(self.wks_wrapper.get_x()[self.indexes[i]],
                                   self.wks_wrapper.get_y_data()[i][self.indexes[i]], 'r+')
        self.canvas.draw()

    def on_next_anim(self):
        if self.current_data < self.wks_wrapper.get_column_num():
            self.current_data += 1
            self.anima_num_label.display(self.current_data)
            self.anim_slider.setValue(self.current_data)
            self.show_data_on_graph_with(self.current_data)
            self.canvas.draw()

    def on_prev_anim(self):
        if self.current_data > 0:
            self.current_data -= 1
            self.anima_num_label.display(self.current_data)
            self.anim_slider.setValue(self.current_data)
            self.show_data_on_graph_with(self.current_data)
            self.canvas.draw()

    def on_slider_value_changed(self):
        # print(self.anim_slider.value())
        self.current_data = self.anim_slider.value()
        self.show_data_on_graph_with(self.current_data)
        self.anima_num_label.display(self.current_data)

    def on_tab_changed(self, i):
        if i is 0:
            return
        model = self.tableWidget.model()
        x = np.empty(shape=(model.rowCount() - 1))
        z = np.empty(shape=(model.columnCount() - 1))
        y_data = np.zeros(shape=(model.columnCount() - 1, model.rowCount() - 1))
        for column in range(model.columnCount()):
            for row in range(model.rowCount()):
                index = model.index(row, column)
                # We suppose data are strings
                elemnt = model.data(index)
                if elemnt is None:
                    continue
                elemnt = elemnt.replace(',', '.')
                if row is 0 and column > 0:
                    z[column - 1] = float(elemnt)
                elif column is 0 and row > 0:
                    x[row - 1] = float(elemnt)
                else:
                    y_data[column - 1][row - 1] = float(elemnt)
        self.wks_wrapper = WorkSheetWrapper(x, z, y_data)
        self.actionSittings.setDisabled(False)
        self.find_peaks()
        self.canvas.draw()

    def _paste_into_selected(self, data):
        r = self.tableWidget.selectedRanges()[0]
        col = r.leftColumn()
        row = r.topRow()
        if col is 0 and row is 0:
            col += 1
        for line in data:
            for number in line:
                item = QTableWidgetItem()
                item.setText(number)
                self.tableWidget.setItem(row, col, item)
                col += 1
                if col > r.rightColumn():
                    break
            col = 0
            row += 1
            if row > r.bottomRow():
                break

    # paste the value
    def _handlePaste(self):
        clipboard_text = QApplication.instance().clipboard().text()
        #print(clipboard_text)
        rows = clipboard_text.split('\n')
        lines = [line.split() for line in rows]

        if len(self.tableWidget.selectedRanges()) is not 0:
            self._paste_into_selected(lines)
        else:
            rows = len(lines) + 1
            cols = len(lines[0])
            self.tableWidget.setRowCount(rows)
            self.tableWidget.setColumnCount(cols)

            labels = "X"
            for i in range(0, cols):
                labels += ";Y({})".format(i)
            self.tableWidget.setHorizontalHeaderLabels(labels.split(";"))

            labels = "Z"
            for i in range(0, rows):
                labels += ";X({})".format(i)
            self.tableWidget.setVerticalHeaderLabels(labels.split(";"))

            row_i = 0
            col_i = 1
            for line in lines:
                #print(line)
                #print("\n")
                for number in line:
                    try:
                        item = QTableWidgetItem()
                        item.setText(number)
                        self.tableWidget.setItem(col_i, row_i, item)
                    except Exception as inst:
                        print(inst)
                    row_i += 1
                row_i = 0
                col_i += 1

    def fitting_exception_occur(self, inst):
        if inst is not None:
            print(inst.args)
            print(inst)
            print(type(inst))
            QMessageBox.about(self, "Fit error", str(inst))
            #raise inst

    def fitting_finished(self):
        # write(self.fit_thread.fit_result)
        self.show_fit_result(self.fit_thread.fit_result)

    def show_fit_result(self, fit_result):
        self.plotWidget.hide_ver_markers()
        self.last_fit_result = fit_result
        self.result_visualizer.init_tables_with(self.last_fit_result)

    def load_last_fit(self):
        # self.last_fit_result = read()
        self.show_fit_result(self.last_fit_result)

    def openFile(self):
        dialog = QFileDialog()
        dialog.setNameFilters(['CSV (*.csv)'])
        filename = dialog.getOpenFileName(self, 'Open File', '../test_project')
        self.loadCsvFile(filename[0])

    def initTable(self, cols, rows):
        self.tableWidget.setRowCount(rows)
        self.tableWidget.setColumnCount(cols)
        labels = "X"
        for i in range(0, cols):
            labels += ";Y({})".format(i)
        self.tableWidget.setHorizontalHeaderLabels(labels.split(";"))

        labels = "Z"
        for i in range(0, rows):
            labels += ";X({})".format(i)
        self.tableWidget.setVerticalHeaderLabels(labels.split(";"))

    def setTableItem(self, row, col, value, color=QColor(255, 255, 255)):
        item = QTableWidgetItem()
        item.setText(value)
        self.tableWidget.setItem(row, col, item)
        self.tableWidget.item(row, col).setBackground(QBrush(color))

    def loadCsvFile(self, filename):
        with open(filename, newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')

            rows = 0
            cols = 0

            for row in enumerate(spamreader):
                rows += 1
                if cols is 0:
                    cols = len(row[1])

            self.initTable(cols, rows)

            x = []
            z = []
            y_data = []
            csvfile.seek(0)
            for i, row in enumerate(spamreader):
                data_row = []
                for j, value in enumerate(row):
                    if value:
                        float_value = float(value)
                        try:
                            if i is 0:
                                z.append(float_value)
                                self.setTableItem(i, j, value, QColor(138, 250, 90))
                            elif j is 0:
                                x.append(float_value)
                                self.setTableItem(i, j, value, QColor(135, 243, 247))
                            else:
                                data_row.append(float_value)
                                self.setTableItem(i, j, value, QColor(250, 255, 130))
                        except Exception as inst:
                            print(inst)
                if data_row:
                    y_data.append(data_row)
            self.wks_wrapper = WorkSheetWrapper(x, z, y_data)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FittingApp()
    window.show()
    sys.exit(app.exec_())