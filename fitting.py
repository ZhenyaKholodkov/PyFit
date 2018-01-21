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

from collections import defaultdict
import matplotlib.pyplot as plt
import pickle
import matplotlib.animation as animation
import peakutils
from peakutils.plot import plot as pplot
from lmfit.models import GaussianModel, LorentzianModel, ExponentialModel
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import operator

import threading
import time

def plot_somedata():
    line, = ax.plot(x_data, fit_data[0], 'b-', lw=2)
    all_y_data = sheet_wrapper.get_y_data()

    indexes = peakutils.indexes(all_y_data[84], thres=0.01, min_dist=5)
    line_ind, = ax.plot(x_data[indexes], fit_data[0][indexes], 'r+', ms=5, mew=2)
    plt.show()

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

'''class ProgressDlg(QDialog):
    def __init__(self, parent=None):
        super(ProgressDlg, self).__init__(parent)

        self.progress = QtGui.QProgressBar(self)
        self.progress.setGeometry(200, 80, 250, 20)
    def update(self):
        self.completed = 0
        for i in range(0,99):
            self.completed += 1
            self.progress.setValue(self.completed)
            time.sleep(0.5)'''


class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)

        self.progress = QProgressBar(self)
        self.progress.setGeometry(200, 80, 250, 20)
        self.sheet_wrapper = WorkSheetWrapper(PyOrigin.WorksheetPages(PyOrigin.ActivePage().GetName()).Layers(0))
        self.x_data = self.sheet_wrapper.get_x()
        self.cur_y_ind = 0

        self.fit_data = []
        self.fit_params = defaultdict(list)

        #fit data animation
        self.fig = plt.figure()
        self.fig.subplots_adjust(top=0.8)
        self.ax = self.fig.add_subplot(211)
        self.ax.set_xlabel('Photon energy')
        self.ax.set_ylim(0, 10000)
        self.line = None
        self.completed = 0
        self.locker = threading.Lock()

    def thread_func(self, lock, obj):
        for i in range(1, 100):
            lock.acquire(0)
            obj.progress.setValue(i)
            lock.release()
            time.sleep(0.1)
    def fit_all_onthread(self):
        lock_progres = threading.Lock()
        #t = threading.Thread(target=self.thread_func, args=(lock_progres, self,))
        t = threading.Thread(target=self.fit_all_th, args=())
        t.start()
        t.join()


    def fit_all_th(self):
        sheet = WorkSheetWrapper(PyOrigin.WorksheetPages(PyOrigin.ActivePage().GetName()).Layers(0))
        all_y_data = sheet.get_y_data()
        model = None#ExponentialModel(prefix='exp_')
        x_data = sheet.get_x()
        parameters = None#model.guess(all_y_data[0], x=x_data)
        first_fit = True
        y_index = 0
        procent = 100 / len(all_y_data)
        for y_data in all_y_data:
            indexes = peakutils.indexes(y_data, thres=0.01, min_dist=5)
            i = 1
            '''old_values = sorted(cur_indexes.keys())
            if len(indexes) >= len(old_values):
                for ind in old_values:
                        new_value = min(indexes, key=lambda x:abs(x - ind))
                        #print("ind {} to {}".format(ind, new_value))
                        #print("prefix {}".format(cur_indexes[ind]))
                        #print(cur_indexes)
                        cur_indexes[new_value] = cur_indexes.pop(ind)
                        #print(cur_indexes)
                        index = np.argwhere(indexes == new_value)
                        indexes = np.delete(indexes, index)
            elif len(old_values) > 0:
                for ind in indexes:
                        old_value = min(old_values, key=lambda x:abs(x - ind))
                        #print("ind {} to {}".format(old_value, ind))
                        #print("prefix {}".format(cur_indexes[old_value]))
                        #print(cur_indexes)
                        cur_indexes[ind] = cur_indexes.pop(old_value)
                        #print(cur_indexes)
                        index = np.argwhere(indexes == ind)
                        indexes = np.delete(indexes, index)

            print(cur_indexes)
            if len(indexes) > 0:
                for ind in indexes:
                    prefix = "g{}_".format(len(cur_indexes) + 1)
                    print(prefix)
                    cur_indexes[ind] = prefix
                    new_model = LorentzianModel(prefix=prefix)
                    if model is None:
                        model = new_model
                        parameters = new_model.guess(y_data, x=x_data)
                    else:
                        model += new_model
                        parameters.update(new_model.guess(y_data, x=x_data))
                    parameters[prefix + 'center'].set(x_data[ind])
                    #parameters['g1_sigma'].set(0.003, min=0.002)
                    parameters[prefix + 'amplitude'].set(y_data[ind])
            print(cur_indexes)'''

            for ind in indexes:
                prefix_str = 'g{}_'.format(i)
                if first_fit:
                    model = LorentzianModel(prefix=prefix_str)
                    parameters = model.guess(y_data, x=x_data)
                    parameters[prefix_str + 'center'].set(x_data[ind])
                    #parameters['g1_sigma'].set(0.003, min=0.002)
                    parameters[prefix_str + 'amplitude'].set(y_data[ind])
                if (prefix_str + 'center') not in model.param_names:
                    cur_model = LorentzianModel(prefix=prefix_str)
                    parameters.update(cur_model.guess(y_data, x=x_data))
                    model += cur_model
                    parameters[prefix_str + 'center'].set(x_data[ind])
                    #parameters['g1_sigma'].set(0.003, min=0.002)
                    parameters[prefix_str + 'amplitude'].set(y_data[ind])
                i += 1
            result = model.fit(y_data, parameters, x=x_data, fit_kws={'nan_policy': 'omit'})
            self.locker.acquire(0)
            self.fit_data.append(result.best_fit)
            for index in range(1, i):
                prefix_str = 'g{}_'.format(index)
                if first_fit or (prefix_str + 'center') not in self.fit_params:
                    self.fit_params[prefix_str + 'x'] = []
                    self.fit_params[prefix_str + 'center'] = []
                    self.fit_params[prefix_str + 'sigma'] = []
                    self.fit_params[prefix_str + 'amplitude'] = []
                self.fit_params[prefix_str + 'x'].append(self.sheet_wrapper.get_x_from_comments()[y_index])
                self.fit_params[prefix_str + 'center'].append(result.best_values[prefix_str + 'center'])
                self.fit_params[prefix_str + 'sigma'].append(result.best_values[prefix_str + 'sigma'])
                self.fit_params[prefix_str + 'amplitude'].append(result.best_values[prefix_str + 'amplitude'])
                parameters[prefix_str + 'center'].set(result.best_values[prefix_str + 'center'])
                parameters[prefix_str + 'sigma'].set(result.best_values[prefix_str + 'sigma'])
                parameters[prefix_str + 'amplitude'].set(result.best_values[prefix_str + 'amplitude'])
            first_fit = False
            y_index += 1
            self.completed += procent
            self.progress.setValue(self.completed)
            self.locker.release()
        self.locker.acquire(0)
        self.completed = 100
        self.progress.setValue(self.completed)
        self.write()
        self.locker.release()

    def fit_all(self):
        all_y_data = self.sheet_wrapper.get_y_data()
        model = ExponentialModel(prefix='exp_')
        parameters = model.guess(all_y_data[0], x=self.x_data)
        first_fit = True
        y_index = 0
        self.completed = 0
        procent = 100 / len(all_y_data)
        for y_data in all_y_data:
            indexes = peakutils.indexes(y_data, thres=0.01, min_dist=5)
            i = 1
            for ind in indexes:
                prefix_str = 'g{}_'.format(i)
                if first_fit or (prefix_str + 'center') not in model.param_names:
                    cur_model = LorentzianModel(prefix=prefix_str)
                    parameters.update(cur_model.guess(y_data, x=self.x_data))
                    model += cur_model
                    parameters[prefix_str + 'center'].set(self.x_data[ind])
                    #parameters['g1_sigma'].set(0.003, min=0.002)
                    parameters[prefix_str + 'amplitude'].set(y_data[ind])
                i += 1
            result = model.fit(y_data, parameters, x=self.x_data, fit_kws={'nan_policy': 'omit'})
            self.fit_data.append(result.best_fit)
            for index in range(1, i):
                prefix_str = 'g{}_'.format(index)
                if first_fit or (prefix_str + 'center') not in self.fit_params:
                    self.fit_params[prefix_str + 'x'] = []
                    self.fit_params[prefix_str + 'center'] = []
                    self.fit_params[prefix_str + 'sigma'] = []
                    self.fit_params[prefix_str + 'amplitude'] = []
                self.fit_params[prefix_str + 'x'].append(self.sheet_wrapper.get_x_from_comments()[y_index])
                self.fit_params[prefix_str + 'center'].append(result.best_values[prefix_str + 'center'])
                self.fit_params[prefix_str + 'sigma'].append(result.best_values[prefix_str + 'sigma'])
                self.fit_params[prefix_str + 'amplitude'].append(result.best_values[prefix_str + 'amplitude'])
            first_fit = False
            y_index += 1
            self.completed += procent
            self.progress.setValue(self.completed)
        self.completed = 100
        self.progress.setValue(self.completed)
        self.write()

    def plot_fit_params(self):
        fig = plt.figure()
        fig.subplots_adjust(top=0.8)
        i = 1
        for key, params in self.fit_params.items():
            ax = fig.add_subplot(210)
            ax.plot(self.x_data, params, 'g-', lw=2)
        plt.show()

    '''def plot_fit_params_2():
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
        plt.plot(sheet_wrapper.get_x_from_comments(), fit_params['g1_center'], 'g-', lw=2)
        plt.show()'''


    def animate(self, i):
        if self.cur_y_ind < len(self.fit_data):
            cur_y_data = self.fit_data[self.cur_y_ind]
            self.line.set_ydata(cur_y_data)
            #indexes = peakutils.indexes(cur_y_data, thres=0.01, min_dist=5)
            #line_ind.set_xdata(x_data[indexes])
            #line_ind.set_ydata(cur_y_data[indexes])
            self.cur_y_ind += 1
        return self.line,


    def init_anim(self):
        self.line.set_ydata(np.ma.array(self.x_data, mask=True))
        return self.line,


    def animate_fit_data(self):
        plt.title('Peak finding')
        self.line, = self.ax.plot(self.x_data, self.fit_data[0], 'b-', lw=2)
        ani = animation.FuncAnimation(self.fig, self.animate, init_func=self.init_anim, interval=20, blit=False)
        plt.show()

    def write(self):
        fit_params_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_params_pl.txt', 'wb')
        pickle.dump(self.fit_params, fit_params_file)
        fit_data_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_data_pl.txt', 'wb')
        pickle.dump(self.fit_data, fit_data_file)
        fit_params_file.close()
        fit_data_file.close()

    def read():
        fit_params_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_params.txt', 'rb')
        fit_data_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_data.txt', 'rb')
        self.fit_params = pickle.load(fit_params_file)
        self.fit_data = pickle.load(fit_data_file)

def main():
    argv = []
    app = QApplication(argv)
    ex = Form()
    #ex.animate_fit_data()
    ex.show()
    ex.fit_all_onthread()
    app.exec_()

if __name__ == '__main__':
    main()
#plot_fit_params_2()
#fit_all()
#write()
#read()
#animate_fit_data()
#fit_index(84)
#print(fit_data[0])
#print(fit_params)
#plot_somedata()