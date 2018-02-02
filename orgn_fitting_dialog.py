import sys
import PyOrigin
# exec(open(r'C:\OriginUserFolder\FittingProject\scripts\orgn_fitting_dialog.py').read())
# append path to packages
pck_path = PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\site-packages"
sys.path.append(pck_path)

import os
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = PyOrigin.GetPath(
    PyOrigin.PATHTYPE_USER) + "FittingProject\site-packages\PyQt5\plugins\platforms"
import matplotlib
import numpy as np
matplotlib.use('Qt5Agg', force=True)
import pickle
from PyQt5.QtGui import QCursor
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication, QSlider, QHBoxLayout, QVBoxLayout, QPushButton, QProgressBar, \
    QComboBox, QAction, QMenuBar, QLabel, QLineEdit, QPushButton, QMessageBox, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
#from pympler.tracker import SummaryTracker

exec (open(PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\scripts\orgn_peak_finder.py").read())
exec (open(PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\scripts\orgn_fitter.py").read())
exec (open(PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\scripts\orgn_settings.py").read())


def write(fit_params, fit_data):
    fit_params_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_params_orgn.txt', 'wb')
    fit_data_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_data_orgn.txt', 'wb')
    pickle.dump(fit_params, fit_params_file)
    pickle.dump(fit_data, fit_data_file)
    fit_data_file.close()
    fit_params_file.close()


def read():
    fit_params_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_params_orgn.txt', 'rb')
    fit_data_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_data_orgn.txt', 'rb')
    fit_params = pickle.load(fit_params_file)
    fit_data = pickle.load(fit_data_file)
    fit_data_file.close()
    fit_params_file.close()
    return fit_params, fit_data


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


class Window(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        self.settings = Setting()
        self.wks_wrapper = WorkSheetWrapper(PyOrigin.WorksheetPages(PyOrigin.ActivePage().GetName()).Layers(0))

        self.indexes = []
        self.peaks = []
        self.last_fit_params = {}
        self.last_fit_data = []
        self.progress_dlg = None
        self.fit_thread = None
        self.current_data = 0
        self.max_amplitude = 0
        self.can_set_peak = False

        # a figure instance to plot on
        y_dataset = self.wks_wrapper.get_y_data()
        self.animator = OrgnPlotAnimator(self.wks_wrapper.get_x(), y_dataset, figsize=(20, 20), changed_data_callback=self.on_animtion_changed_data)

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.animator.get_figure())
        self.canvas.mpl_connect('button_press_event', self.on_click)

        # create menu with settings
        self.myQMenuBar = QtWidgets.QMenuBar(self)
        toolsMenu = self.myQMenuBar.addMenu('Tools')
        settingsAction = QtWidgets.QAction('Model Settings', self)
        settingsAction.triggered.connect(self.show_model_settings)
        toolsMenu.addAction(settingsAction)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = OrgnToolbar(self.canvas, self)
        images_path = PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject/res/"
        self.toolbar.addSeparator()
        self.toolbar.add_button(images_path + "play_anim.png", "Animate", self.animate_peaks)
        self.toolbar.add_button(images_path + "stop_anim.png", "Stop Animate", self.stop_animate_peaks)
        self.toolbar.addSeparator()
        self.toolbar.add_button(images_path + "crosshairs.png", "Add Peak", self.enable_set_peak)
        self.toolbar.addSeparator()
        self.toolbar.add_button(images_path + "to_wks.png", "Save result to new table", self.save_result_to_wks)
        self.toolbar.addSeparator()
        self.toolbar.add_button(images_path + "fit.png", "Fit", self.fit)
        self.toolbar.add_button(images_path + "Last.png", "Load last fit", self.load_last_fit)
        self.toolbar.add_button(images_path + "Peaks.png", "Show current peaks", self.find_peaks)

        self.animation_box_container = QWidget()
        animation_box = QHBoxLayout(self.animation_box_container)
        self.anima_label = QLabel('Data set:', self)
        self.anima_label.setFixedHeight(20)
        self.anima_label.setFixedWidth(40)
        self.anima_num_label = QLabel('0', self)
        self.anima_num_label.setFixedHeight(20)
        self.anima_num_label.setFixedWidth(20)
        self.left_button = QPushButton('<<', self)
        self.left_button.setFixedHeight(25)
        self.left_button.setFixedWidth(30)
        self.left_button.clicked.connect(self.on_prev_anim)
        self.right_button = QPushButton('>>', self)
        self.right_button.setFixedHeight(25)
        self.right_button.setFixedWidth(30)
        self.right_button.clicked.connect(self.on_next_anim)
        self.anim_slider = QSlider(Qt.Horizontal)
        self.anim_slider.setMinimum(0)
        self.anim_slider.setMaximum(len(self.wks_wrapper.get_y_data()) - 1)
        self.anim_slider.valueChanged.connect(self.on_slider_value_changed)
        animation_box.addWidget(self.anima_label)
        animation_box.addWidget(self.anima_num_label)
        animation_box.addWidget(self.left_button)
        animation_box.addWidget(self.right_button)
        animation_box.addWidget(self.anim_slider)

        self.cb = QComboBox()
        self.cb.setEnabled(False)
        self.cb.currentIndexChanged.connect(self.on_combobox_changed)

        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.animation_box_container)
        layout.addWidget(self.cb)
        self.setLayout(layout)
        self.setWindowTitle("Fitting script")

        self.find_peaks()
        self.canvas.draw()

    def save_result_to_wks(self):
        result_book = PyOrigin.CreatePage(2, 'Fit data', 'Result', 1)
        fit_data_sheet = WorkSheetWrapper(result_book[0])
        fit_params_sheet = WorkSheetWrapper(result_book.AddLayer("Fit params"))

        fit_data_sheet.set_data_column(self.wks_wrapper.get_x(), 0)
        fit_data_sheet.delete_col(1)
        for i, data in enumerate(self.last_fit_data):
            num = i + 1
            name = str(num)
            fit_data_sheet.add_col(num, name)
            fit_data_sheet.set_data_column(data, num)

        fit_params_sheet.set_data_column(self.wks_wrapper.get_x_from_comments(), 0)
        fit_params_sheet.delete_col(1)
        num = 1
        for param_name, params in self.last_fit_params.items():
            fit_params_sheet.add_col(num, param_name)
            fit_params_sheet.set_data_column(params, num)
            num += 1

    def enable_set_peak(self):
        self.can_set_peak = True
        QApplication.setOverrideCursor(QCursor(Qt.CrossCursor))

    def on_click(self, event):
        if self.can_set_peak is False:
            return

        x_data = self.wks_wrapper.get_x()
        ind = (np.abs(x_data - event.xdata)).argmin()
        if self.current_data < len(self.indexes):
            if ind in self.indexes[self.current_data]:
                self.indexes[self.current_data] = np.delete(self.indexes[self.current_data],
                                                            np.where(self.indexes[self.current_data] == ind))
            else:
                self.indexes[self.current_data] = np.append(self.indexes[self.current_data], ind)
                self.indexes[self.current_data].sort()
        self.animator.set_peak_indexes(self.indexes)
        self.animator.show_plots_with(self.current_data)
        self.canvas.draw()
        self.can_set_peak = False
        #QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
        QApplication.restoreOverrideCursor()
        QApplication.restoreOverrideCursor()

    def show_model_settings(self):
        settings_dlg = SettingsDialog(self.settings, self)
        settings_dlg.peak_settings_changed.connect(self.find_peaks)
        settings_dlg.show()

    def find_peaks(self):
        self.indexes, self.max_amplitude = find_peaks(self.wks_wrapper, self.settings.peak_function, mph=self.settings.min_amplitude,
                                  mpd=self.settings.min_peak_dist, threshold=self.settings.threshold)

        self.cb.clear()
        self.cb.setEnabled(False)
        self.animation_box_container.setEnabled(True)
        # show peaks
        self.animator.clear()
        self.animator.set_title('Peak finding')
        self.animator.set_y_lim((0, 1.1 * self.max_amplitude))
        self.animator.set_line_x_data(self.wks_wrapper.get_x())
        self.animator.set_line_y_dataset(self.wks_wrapper.get_y_data())
        self.animator.set_point_data(self.wks_wrapper.get_x(), self.wks_wrapper.get_y_data())
        self.animator.set_peak_indexes(self.indexes)
        self.animator.add_lines()
        self.animator.show_plots_with(0)
        self.canvas.draw()

    def stop_fit(self):
        if self.fit_thread is not None and self.fit_thread.isAlive():
            self.fit_thread.stop_fit()

    def fitting_finished(self):
        write(self.fit_thread.fit_params, self.fit_thread.fit_data)
        self.show_fit_result(self.fit_thread.fit_params, self.fit_thread.fit_data)

    def fitting_exception_occur(self, inst):
        if inst is not None:
            print(inst.args)
            print(inst)
            print(type(inst))
            QMessageBox.about(self, "Fit error", str(inst))
            raise inst

    def fit(self):
        print(self.indexes[0])
        self.fit_thread = OrgnFitterThread(self,
                                      self.wks_wrapper,
                                      self.indexes, self.settings)
        self.progress_dlg = ProgressDialog(self)

        self.progress_dlg.accepted.connect(self.fit_thread.stop_fit)
        self.progress_dlg.rejected.connect(self.fit_thread.stop_fit)
        self.fit_thread.finished.connect(self.fitting_finished)
        self.fit_thread.complete_changed.connect(self.progress_dlg.update_progress)
        self.fit_thread.exception_occur.connect(self.fitting_exception_occur)

        self.progress_dlg.show()
        self.fit_thread.start()

        self.progress_dlg.exec_()

    def show_fit_result(self, fit_params, fit_data):
        self.last_fit_params = fit_params
        self.last_fit_data = fit_data
        self.cb.addItem("Fitting data set")
        for param in fit_params.keys():
            self.cb.addItem(param)
        self.cb.setEnabled(True)
        self.on_combobox_changed(0)

    def on_combobox_changed(self, i):
        self.animator.clear()
        if i is 0:
            self.animator.set_y_lim((0, 1.1 * self.max_amplitude))
            self.animator.set_line_x_data(self.wks_wrapper.get_x())
            self.animator.set_line_y_dataset(self.last_fit_data)
            self.animator.show_plots_with(0)
            self.animation_box_container.setEnabled(True)
        else:
            param = self.cb.currentText()
            self.animator.set_line_x_data(self.wks_wrapper.get_x_from_comments())#self.last_fit_params[param[0:3] + 'x'])
            self.animator.set_line_y_dataset([self.last_fit_params[param]])
            self.animation_box_container.setEnabled(False)
        self.animator.add_lines()
        self.canvas.draw()

    def animate_peaks(self):
        self.animator.show_animation(self.settings.animation_interval)

    def stop_animate_peaks(self):
        self.animator.stop_animation()

    def on_animtion_changed_data(self, new_data):
        self.current_data = new_data
        self.anima_num_label.setText(str(self.current_data))
        self.anim_slider.setValue(self.current_data)

    def on_next_anim(self):
        if self.current_data < self.wks_wrapper.get_column_num():
            self.current_data += 1
            self.anima_num_label.setText(str(self.current_data))
            self.anim_slider.setValue(self.current_data)
            self.animator.show_plots_with(self.current_data)
            self.canvas.draw()

    def on_prev_anim(self):
        if self.current_data > 0:
            self.current_data -= 1
            self.anima_num_label.setText(str(self.current_data))
            self.anim_slider.setValue(self.current_data)
            self.animator.show_plots_with(self.current_data)
            self.canvas.draw()

    def on_slider_value_changed(self):
        # print(self.anim_slider.value())
        self.current_data = self.anim_slider.value()
        self.animator.show_plots_with(self.current_data)
        self.anima_num_label.setText(str(self.current_data))
        self.canvas.draw()
        # self.canvas.update()
        # plt.draw()

    def load_last_fit(self):
        self.last_fit_params, self.last_fit_data = read()
        self.show_fit_result(self.last_fit_params, self.last_fit_data)

def start_app():
    # try:
    app = QApplication(sys.argv)

    main = Window()
    main.show()

    app.exec_()
    #main.stop_fit()
    #del main
    # except Exception as inst:
    #    print(type(inst))
    #    print(inst.args)


if __name__ == '__main__':
    # tracker = SummaryTracker()
    start_app()
    # tracker.print_diff()
