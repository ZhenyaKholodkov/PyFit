import sys

pck_path = PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\site-packages"
sys.path.append(pck_path)
octave_path = PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\site-packages\octave_kernel-0.28.3-py3.3.egg"
sys.path.append(octave_path)
exec (open(PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\scripts\WorkSheetWrapper.py").read())
exec (open(PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\scripts\detect_peaks.py").read())
exec (open(PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\scripts\peakdetect.py").read())

import matplotlib

matplotlib.use('Qt5Agg', force=True)
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy import signal

from enum import Enum
import peakutils
import numpy as np
from scipy import signal

def detect_peaks_with_func(data_set, func, mph, mpd, threshold):
    if func is PeakFunction.PEAK_DETECTOR:
        return detect_peaks(data_set, mph=mph, mpd=mpd, threshold=threshold)
    else:
        return peakutils.indexes(data_set, thres=threshold, min_dist=mpd)



class OrgnPlotAnimator():
    def __init__(self, x_line, y_dataset_line, figsize, peak_indexes=None, x_point=None, y_dataset_point=None):
        self.figure, self.ax = plt.subplots(1, 1, figsize=figsize)
        #self.figure.canvas.mpl_connect('button_press_event', self.on_click)
        self.x_line = x_line
        self.y_dataset_line = y_dataset_line
        self.x_point = x_point
        self.y_dataset_point = y_dataset_point
        self.peak_indexes = peak_indexes

        self.cur_y_ind = 0
        self.add_lines()

    def add_lines(self):
        if len(self.x_line) > 0 and len(self.y_dataset_line) > 0:
            self.line, = self.ax.plot(self.x_line, self.y_dataset_line[0], 'k')
        if self.x_point is not None:
            self.line_points, = self.ax.plot(self.x_point, self.y_dataset_point[0], 'bo')
        if self.peak_indexes is not None:
            self.line_ind, = self.ax.plot(self.x_line[self.peak_indexes[0]],
                                          self.y_dataset_line[0][self.peak_indexes[0]],
                                          'r+', ms=5, mew=2)

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


class OrgnPeakFinder:
    def __init__(self, in_wks_wrapper):
        self.wks_wrapper = in_wks_wrapper
        self.max_amplitude = 0
        # self.orgn_peak_animator = None

    def find_peaks(self, peak_func, mph, mpd, threshold):
        """Detect peaks in data based on their amplitude and other features.

           Parameters
           ----------
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
        y_dataset = self.wks_wrapper.get_y_data()
        found_indexes = []
        last_indexes = []
        first_entries = {}
        for i, y_data in enumerate(y_dataset):
            indexes = detect_peaks_with_func(y_data, peak_func, mph, mpd, threshold)
            max_value = max(y_data[indexes]) if len(indexes) > 0 else 0
            self.max_amplitude = max_value if max_value > self.max_amplitude else self.max_amplitude
            found_indexes.append(indexes)

            # find first entry of the peak to buid a model
            for ind in indexes:
                is_new_ind = True
                for last in last_indexes:
                    if last - mpd < ind < last + mpd + 1:
                        is_new_ind = False
                        break
                if is_new_ind:
                    first_entries[i] = ind
            last_indexes = indexes
        return found_indexes, first_entries





'''sheet_wrapper = WorkSheetWrapper(PyOrigin.WorksheetPages(PyOrigin.ActivePage().GetName()).Layers(0))
obj = OrgnPeakFinder(sheet_wrapper)
obj.find_peaks(mph=500, mpd=10, threshold=2, edge='both')
obj.show_animated_peaks()'''
