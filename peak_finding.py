import sys
import PyOrigin

# exec(open(r'C:\OriginUserFolder\FittingProject\scripts\.py').read())
# append path to packages

pck_path = PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\site-packages"
sys.path.append(pck_path)
exec (open(PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\scripts\WorkSheetWrapper.py").read())
##########################
# from GaussianScript import gaussian
# from SimplexAlgorithm_NelderMead import simplex_func

import numpy as np
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import peakutils
from peakutils.plot import plot as pplot

sheet_wrapper = WorkSheetWrapper(PyOrigin.WorksheetPages(PyOrigin.ActivePage().GetName()).Layers(0))
cur_y_ind = 0
x_data = sheet_wrapper.get_x()
y_data = sheet_wrapper.get_y_data()[cur_y_ind]
fig = plt.figure()
fig.subplots_adjust(top=0.8)
ax = fig.add_subplot(211)
ax.set_xlabel('Photon energy')
ax.set_ylim(0, 20000)
line, = ax.plot(x_data, y_data, 'b-', lw=2)
min_distance = 30
ampl = 0.01
ind = peakutils.indexes(y_data, thres=ampl, min_dist=min_distance)
line_ind, = ax.plot(x_data[ind], y_data[ind], 'r+', ms=5, mew=2)


def animate(i):
    global cur_y_ind
    if cur_y_ind < sheet_wrapper.get_column_num() - 1:
        cur_y_data = sheet_wrapper.get_y_data()[cur_y_ind]
        line.set_ydata(cur_y_data)
        ax.text(1.6, 15000, sheet_wrapper.get_x_from_comments()[cur_y_ind], style='italic',
                bbox={'facecolor': 'red', 'alpha': 0.5, 'pad': 10})
        indexes = peakutils.indexes(cur_y_data, thres=ampl, min_dist=min_distance)
        if len(indexes) >= 3:
            print(cur_y_ind)
        line_ind.set_xdata(x_data[indexes])
        line_ind.set_ydata(cur_y_data[indexes])
        cur_y_ind += 1
    return line,


def init():
    line.set_ydata(np.ma.array(x_data, mask=True))
    return line,


plt.title('Peak finding')
ani = animation.FuncAnimation(fig, animate, init_func=init, interval=100, blit=False)
plt.show()
