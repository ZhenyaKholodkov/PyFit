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
from collections import defaultdict
import matplotlib.pyplot as plt
import pickle
import matplotlib.animation as animation
import peakutils
from peakutils.plot import plot as pplot
from lmfit.models import GaussianModel, LorentzianModel, ExponentialModel

sheet_wrapper = WorkSheetWrapper(PyOrigin.WorksheetPages(PyOrigin.ActivePage().GetName()).Layers(0))
x_data = sheet_wrapper.get_x()
cur_y_ind = 0

fit_data = []
fit_params = defaultdict(list)


#fit data animation

fig = plt.figure()
fig.subplots_adjust(top=0.8)
ax = fig.add_subplot(211)
ax.set_xlabel('Photon energy')
ax.set_ylim(0, 20000)
line = None

def fit_all():
    all_y_data = sheet_wrapper.get_y_data()
    model = ExponentialModel(prefix='exp_')
    parameters = model.guess(all_y_data[0], x=x_data)
    first_fit = True
    y_index = 0
    for y_data in all_y_data:
        indexes = peakutils.indexes(y_data, thres=0.01, min_dist=5)
        i = 1
        for ind in indexes:
            prefix_str = 'g{}_'.format(i)
            if first_fit or (prefix_str + 'center') not in model.param_names:
                cur_model = LorentzianModel(prefix=prefix_str)
                parameters.update(cur_model.guess(y_data, x=x_data))
                model += cur_model
            parameters[prefix_str + 'center'].set(x_data[ind])
            #parameters['g1_sigma'].set(0.003, min=0.002)
            parameters[prefix_str + 'amplitude'].set(y_data[ind])
            i += 1
        result = model.fit(y_data, parameters, x=x_data, fit_kws={'nan_policy': 'omit'})
        fit_data.append(result.best_fit)
        for index in range(1, i):
            prefix_str = 'g{}_'.format(index)
            if first_fit or (prefix_str + 'center') not in fit_params:
                fit_params[prefix_str + 'x'] = []
                fit_params[prefix_str + 'center'] = []
                fit_params[prefix_str + 'sigma'] = []
                fit_params[prefix_str + 'amplitude'] = []
            fit_params[prefix_str + 'x'].append(sheet_wrapper.get_x_from_comments()[y_index])
            fit_params[prefix_str + 'center'].append(result.best_values[prefix_str + 'center'])
            fit_params[prefix_str + 'sigma'].append(result.best_values[prefix_str + 'sigma'])
            fit_params[prefix_str + 'amplitude'].append(result.best_values[prefix_str + 'amplitude'])
        first_fit = False
        y_index += 1


def fit_index(index):
    all_y_data = sheet_wrapper.get_y_data()
    model = ExponentialModel(prefix='exp_')
    parameters = model.guess(all_y_data[index], x=x_data)
    y_data = all_y_data[index]
    indexes = peakutils.indexes(y_data, thres=0.01, min_dist=5)
    i = 1
    for ind in indexes:
        prefix_str = 'g{}_'.format(i)
        cur_model = LorentzianModel(prefix=prefix_str)
        parameters.update(cur_model.guess(y_data, x=x_data))
        model += cur_model
        parameters[prefix_str + 'center'].set(x_data[ind])
        # parameters['g1_sigma'].set(0.003, min=0.002)
        parameters[prefix_str + 'amplitude'].set(y_data[ind])
        i += 1
    result = model.fit(y_data, parameters, x=x_data, fit_kws={'nan_policy': 'omit'})
    fit_data.append(result.best_fit)
    for index in range(1, i):
        prefix_str = 'g{}_'.format(index)
        fit_params[prefix_str + 'center'] = []
        fit_params[prefix_str + 'sigma'] = []
        fit_params[prefix_str + 'amplitude'] = []
        fit_params[prefix_str + 'center'].append(result.best_values[prefix_str + 'center'])
        fit_params[prefix_str + 'sigma'].append(result.best_values[prefix_str + 'sigma'])
        fit_params[prefix_str + 'amplitude'].append(result.best_values[prefix_str + 'amplitude'])

def plot_fit_params():
    fig = plt.figure()
    fig.subplots_adjust(top=0.8)
    i = 1
    for key, params in fit_params.items():
        ax = fig.add_subplot(210)
        ax.plot(x_data, params, 'g-', lw=2)
    plt.show()

def plot_fit_params_2():
    all_y_data = sheet_wrapper.get_y_data()
    #fig = plt.figure()
    #fig.subplots_adjust(top=0.8)
    #ax = fig.add_subplot(211)
    plt.figure(1)
    for i in range(1, 3):
        plt.subplot(210 + i)
        plt.plot(x_data, all_y_data[0], 'g-', lw=2)
    plt.show()

def plot_fit_params_3():
    plt.figure()
    plt.subplot(211)
    plt.plot(fit_params['g3_x'], fit_params['g3_center'], 'g-', lw=2)
    plt.show()


def animate(i):
    global cur_y_ind
    if cur_y_ind < len(fit_data):
        cur_y_data = fit_data[cur_y_ind]
        line.set_ydata(cur_y_data)
        ax.text(1.6, 15000, sheet_wrapper.get_x_from_comments()[cur_y_ind], style='italic', bbox={'facecolor': 'red', 'alpha': 0.5, 'pad': 10})
        #indexes = peakutils.indexes(cur_y_data, thres=0.01, min_dist=5)
        #line_ind.set_xdata(x_data[indexes])
        #line_ind.set_ydata(cur_y_data[indexes])
        cur_y_ind += 1
    return line,


def init():
    line.set_ydata(np.ma.array(x_data, mask=True))
    return line,


def animate_fit_data():
    global line
    plt.title('Peak finding')
    line, = ax.plot(x_data, fit_data[0], 'b-', lw=2)
    ani = animation.FuncAnimation(fig, animate, init_func=init, interval=100, blit=False)
    plt.show()

def write():
    fit_params_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_params.txt', 'wb')
    pickle.dump(fit_params, fit_params_file)
    fit_data_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_data.txt', 'wb')
    pickle.dump(fit_data, fit_data_file)
    fit_params_file.close()
    fit_data_file.close()

def read():
    global fit_params
    global fit_data
    fit_params_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_params_pl.txt', 'rb')
    fit_data_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_data_pl.txt', 'rb')
    fit_params = pickle.load(fit_params_file)
    fit_data = pickle.load(fit_data_file)
def plot_somedata():
    line, = ax.plot(x_data, fit_data[0], 'b-', lw=2)
    all_y_data = sheet_wrapper.get_y_data()

    indexes = peakutils.indexes(all_y_data[84], thres=0.01, min_dist=5)
    line_ind, = ax.plot(x_data[indexes], fit_data[0][indexes], 'r+', ms=5, mew=2)
    plt.show()

#plot_fit_params_2()
#fit_all()
#write()
read()
#print(fit_params)
animate_fit_data()
#fit_index(84)
#print(fit_data[0])
#print(fit_params)
plot_fit_params_3()
#print(len(fit_params['g2_x']))
#print(len(fit_params['g2_center']))