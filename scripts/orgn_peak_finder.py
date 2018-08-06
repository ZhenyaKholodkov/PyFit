import sys
''''pck_path = PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "PyFit\site-packages"
sys.path.append(pck_path)
octave_path = PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "PyFit\site-packages\octave_kernel-0.28.3-py3.3.egg"
sys.path.append(octave_path)
exec (open(PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "PyFit\scripts\WorkSheetWrapper.py").read())
exec (open(PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "PyFit\scripts\detect_peaks.py").read())
exec (open(PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "PyFit\scripts\peakdetect.py").read())'''''

import matplotlib

matplotlib.use('Qt5Agg', force=True)
from orgn_settings import PeakFunction

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import detect_peaks
import peakutils
import numpy as np

from PyQt5.QtCore import pyqtSignal


def detect_peaks_with_func(data_set, func, mph, mpd, threshold):
    return peakutils.indexes(data_set, thres=threshold, min_dist=mpd)
    ''''if func is PeakFunction.PEAK_UTILS:
        return peakutils.indexes(data_set, thres=threshold, min_dist=mpd)
    else:
        return detect_peaks(data_set, mph=mph, mpd=mpd, threshold=threshold)'''''



class OrgnPlotAnimator():
    def __init__(self, x_line, y_dataset_line, figsize, peak_indexes=None, x_point=None,
                 y_dataset_point=None, changed_data_callback=None):
        self.figure, self.ax = plt.subplots(1, 1, figsize=figsize)
        #self.figure.canvas.mpl_connect('button_press_event', self.on_click)
        self.x_line = x_line
        self.y_dataset_line = y_dataset_line
        self.x_point = x_point
        self.y_dataset_point = y_dataset_point
        self.peak_indexes = peak_indexes
        self.changed_data_callback = changed_data_callback
        self.line, = self.ax.plot(self.x_line, self.y_dataset_line[0], 'k')
        self.line_points = None
        self.line_ind = None
        self.lines = []
        self.possible_colors = ['b--', 'g--', 'r--', 'c--', 'm--', 'y--', 'w--']

        self.cur_y_ind = 0
        self.add_lines()

    def add_lines(self):
        if 0 < len(self.x_line) and len(self.y_dataset_line) > 0 and len(self.x_line) == len(self.y_dataset_line[0]):
            self.line, = self.ax.plot(self.x_line, self.y_dataset_line[0], 'k')
        if self.x_point is not None:
            self.line_points, = self.ax.plot(self.x_point, self.y_dataset_point[0], 'bo')
        if self.peak_indexes is not None:
            self.line_ind, = self.ax.plot(self.x_line[self.peak_indexes[0]],
                                          self.y_dataset_line[0][self.peak_indexes[0]],
                                          'r+', ms=5, mew=2)

    def add_line(self, x, y, color_options):
        line, = self.ax.plot(x, y, color_options, ms=5, mew=2)
        self.lines.append(line)

    def remove_lines(self):
        for line in self.lines:
            if line in self.ax.lines:
                self.ax.lines.remove(line)
                del line
        self.lines.clear()
        self.ax.relim()

    def clear(self):
        self.ax.clear()
        self.x_line = None
        self.y_dataset_line = None
        self.x_point = None
        self.y_dataset_point = None
        self.peak_indexes = None

    def set_title(self, title):
        plt.title(title)

    def set_x_lim(self, lim=(0, 1)):
        self.ax.set_xlim(lim)

    def set_y_lim(self, lim=(0, 1)):
        self.ax.set_ylim(lim)

    def set_xlabel(self, label):
        self.ax.set_xlabel(label)

    def set_ylabel(self, label):
        self.ax.set_ylabel(label)

    def set_line_y_dataset(self, y_dataset):
        self.y_dataset_line = y_dataset
        plt.draw()

    def set_line_x_data(self, x):
        self.x_line = x
        plt.draw()

    def set_point_data(self, x, y_dataset):
        self.x_point = x
        self.y_dataset_point = y_dataset
        plt.draw()

    def set_peak_indexes(self, peak_indexes):
        self.peak_indexes = peak_indexes
        plt.draw()

    def set_show_peaks(self, value):
        self.show_peaks = value

    def show_plots_with(self, y_data_index):
        if y_data_index >= len(self.y_dataset_line):
            return
        cur_y_data = self.y_dataset_line[y_data_index]
        #base = peakutils.baseline(cur_y_data, 2)
        #cur_y_data -= base
        self.line.set_xdata(self.x_line)
        self.line.set_ydata(cur_y_data)
        if self.x_point is not None:
            self.line_points.set_xdata(self.x_point)
            self.line_points.set_ydata(self.y_dataset_point[y_data_index])
        if self.peak_indexes is not None:
            self.line_ind.set_xdata(self.x_line[self.peak_indexes[y_data_index]])
            self.line_ind.set_ydata(cur_y_data[self.peak_indexes[y_data_index]])
        return self.line,

    def animate(self, i):
        if self.cur_y_ind < len(self.y_dataset_line) - 1:
            self.show_plots_with(self.cur_y_ind)
            self.cur_y_ind += 1
            if self.changed_data_callback is not None:
                self.changed_data_callback(self.cur_y_ind)
        return self.line,

    def init_animation(self):
        return self.line,

    def show_animation(self, interval):
        self.cur_y_ind = 0
        self.anim = animation.FuncAnimation(self.figure, self.animate, init_func=self.init_animation, interval=interval)
        plt.draw()

    def stop_animation(self):
        self.anim.event_source.stop()

    def get_figure(self):
        return self.figure


def find_peaks(wks_wrapper, peak_func, mph, mpd, threshold):
    """Detect peaks in data based on their amplitude and other features.

       Parameters
       ----------
       wks_wrapper : worksheet wrapper
       peak_func : function used for peak detection
            Can be Peak utils or Detect peak
       mph : {None, number}, optional (default = None)
           detect peaks that are greater than minimum peak height.
       mpd : positive integer, optional (default = 1)
           detect peaks that are at least separated by minimum peak distance (in
           number of data).
       threshold : positive number, optional (default = 0)
           detect peaks (valleys) that are greater (smaller) than `threshold`
           in relation to their immediate neighbors.
       edge : {None, 'rising', 'falling', 'both'}, optional (default = 'rising')
           for a flat peak, keep only the rising edge ('rising'), only the
           falling edge ('falling'), both edges ('both'), or don't detect a
           flat peak (None).
       kpsh : bool, optional (default = False)
           keep peaks with same height even if they are closer than `mpd`.
       valley : bool, optional (default = False)
           if True (1), detect valleys (local minima) instead of peaks."""
    y_data_set = wks_wrapper.get_y_data()
    found_indexes = []
    max_amplitude = 0
    max_value = 0
    for i, y_data in enumerate(y_data_set):
        try:
            indexes = peakutils.indexes(y_data, thres=threshold, min_dist=mpd)
            #indexes = detect_peaks_with_func(y_data, peak_func, mph, mpd, threshold)
            if len(indexes) > 0:
                max_value = max([y_data[i] for i in indexes])
            else:
                max_value = 0
            max_amplitude = max_value if max_value > max_amplitude else max_amplitude
            found_indexes.append(indexes)
        except Exception as ex:
            print(ex)
    return found_indexes, max_amplitude





'''sheet_wrapper = WorkSheetWrapper(PyOrigin.WorksheetPages(PyOrigin.ActivePage().GetName()).Layers(0))
obj = OrgnPeakFinder(sheet_wrapper)
obj.find_peaks(mph=500, mpd=10, threshold=2, edge='both')
obj.show_animated_peaks()'''
