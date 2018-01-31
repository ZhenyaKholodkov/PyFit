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
import matplotlib.pyplot as plt
import pylab

exec (open(PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\scripts\orgn_peak_finder.py").read())
exec (open(PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\scripts\orgn_fitter.py").read())
exec (open(PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\scripts\orgn_settings.py").read())

import pickle
#from pympler.tracker import SummaryTracker

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication, QSlider, QHBoxLayout, QVBoxLayout, QPushButton, QProgressBar, \
    QComboBox, QAction, QMenuBar, QLabel, QLineEdit, QPushButton, QMessageBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from enum import Enum


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

    #method that makes possible to add custom button
    def add_button(self, image_file, text, callback):
        self._actions[callback] = self.addAction(self._icon(image_file), text, callback)


class Window(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        self.settings = Setting()
        self.wks_wrapper = WorkSheetWrapper(PyOrigin.WorksheetPages(PyOrigin.ActivePage().GetName()).Layers(0))
        self.peak_finder = OrgnPeakFinder(self.wks_wrapper)

        self.indexes = []
        self.peaks = []
        self.last_fit_params = {}
        self.last_fit_data = []
        self.progress_dlg = None
        self.fit_thread = None
        self.current_data = 0

        # a figure instance to plot on
        y_dataset = self.wks_wrapper.get_y_data()
        self.animator = OrgnPlotAnimator(self.wks_wrapper.get_x(), y_dataset, figsize=(20, 20))
        # self.peak_finder.show_animation(self.figure)

        self.animator.set_xlabel('Photon energy')
        self.animator.set_y_lim((0, self.peak_finder.max_amplitude + 500))
        self.animator.set_title('Peak finding')
        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.animator.get_figure())
        self.canvas.mpl_connect('button_press_event', self.on_click)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = OrgnToolbar(self.canvas, self)
        images_path = PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject/res/"
        self.toolbar.add_button(images_path + "play_anim.png", "Animate", self.animate_peaks)
        self.toolbar.add_button(images_path + "stop_anim.png", "Stop Animate", self.stop_animate_peaks)
        self.toolbar.add_button(images_path + "fit.png", "Fit", self.fit)
        self.toolbar.add_button(images_path + "Last.png", "Load last fit", self.load_last_fit)
        self.toolbar.add_button(images_path + "Peaks.png", "Show current peaks", self.find_peaks)

        self.myQMenuBar = QtWidgets.QMenuBar(self)
        toolsMenu = self.myQMenuBar.addMenu('Tools')
        settingsAction = QtWidgets.QAction('Model Settings', self)
        settingsAction.triggered.connect(self.show_model_settings)
        toolsMenu.addAction(settingsAction)

        # Just some button connected to `plot` method
        self.sl = QSlider(Qt.Horizontal)
        self.sl.setMinimum(0)
        self.sl.setMaximum(len(self.wks_wrapper.get_y_data()) - 1)
        self.sl.valueChanged.connect(self.on_slider_value_changed)

        self.cb = QComboBox()
        self.cb.setEnabled(False)
        self.cb.currentIndexChanged.connect(self.on_combobox_changed)

        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.sl)
        layout.addWidget(self.cb)
        self.setLayout(layout)
        self.setWindowTitle("Fitting script")

        self.find_peaks()
        self.canvas.draw()

    def on_click(self, event):
        print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
              ('double' if event.dblclick else 'single', event.button,
               event.x, event.y, event.xdata, event.ydata))
        cur_dataset = self.wks_wrapper.get_y_data()[self.current_data]
        ind = (np.abs(cur_dataset - event.ydata)).argmin()
        ind2 = min(range(len(cur_dataset)), key=lambda i: abs(cur_dataset[i] - event.ydata))
        print(ind)
        print(ind2)
        print(cur_dataset[ind])

    def show_model_settings(self):
        settings_dlg = SettingsDialog(self.settings, self)
        settings_dlg.show()

    def find_peaks(self):
        self.indexes, peak_entries = self.peak_finder.find_peaks(self.settings.peak_function, mph=self.settings.min_amplitude,
                                                   mpd=self.settings.min_peak_dist, threshold=self.settings.threshold)

        for data_ind, peak_ind in peak_entries:
            self.peaks.append(Peak(data_ind, peak_ind, self.settings.model))
        # show peaks
        self.animator.clear()
        self.animator.set_title('Peak finding')
        self.animator.set_y_lim((0, self.peak_finder.max_amplitude + 500))
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
        self.show_fit_result(self.fit_thread.fit_params, self.fit_thread.fit_data)

    def fitting_exception_occur(self, inst):
        if inst is not None:
            print(inst.args)
            print(inst)
            print(type(inst))
            QMessageBox.about(self, "Fit error", str(inst))
            raise inst

    def fit(self):
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
            if param[3] is not 'x':
                self.cb.addItem(param)
        self.cb.setEnabled(True)
        self.on_combobox_changed(0)

    def on_combobox_changed(self, i):
        self.animator.clear()
        if i is 0:
            self.animator.set_y_lim((0, self.peak_finder.max_amplitude + 500))
            self.animator.set_line_x_data(self.wks_wrapper.get_x())
            self.animator.set_line_y_dataset(self.last_fit_data)
            self.animator.show_plots_with(0)
        else:
            param = self.cb.currentText()
            # self.animator.set_y_lim((0, max(self.last_fit_params[param])))
            # self.animator.set_x_lim((0, max(self.last_fit_params[param[0:3] + 'x'])))
            self.animator.set_line_x_data(self.last_fit_params[param[0:3] + 'x'])
            self.animator.set_line_y_dataset([self.last_fit_params[param]])
        self.animator.add_lines()
        self.canvas.draw()

    def animate_peaks(self):
        self.animator.show_animation(100)

    def stop_animate_peaks(self):
        self.animator.stop_animation()

    def on_slider_value_changed(self):
        # print(self.sl.value())
        self.current_data = self.sl.value()
        self.animator.show_plots_with(self.current_data)
        self.canvas.draw()
        # self.canvas.update()
        # plt.draw()

    def load_last_fit(self):
        fit_params, fit_data = self.read()
        self.show_fit_result(fit_params, fit_data)

    def read(self):
        fit_params_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_params_orgn.txt', 'rb')
        fit_data_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_data_orgn.txt', 'rb')
        fit_params = pickle.load(fit_params_file)
        fit_data = pickle.load(fit_data_file)
        fit_data_file.close()
        fit_params_file.close()
        return fit_params, fit_data


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
