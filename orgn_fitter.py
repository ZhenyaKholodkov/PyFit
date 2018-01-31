import sys
import PyOrigin

# exec(open(r'C:\OriginUserFolder\FittingProject\scripts\.py').read())
# append path to packages

pck_path = PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\site-packages"
sys.path.append(pck_path)
##########################
import threading
import numpy as np
import matplotlib.pyplot as plt
import pickle
import matplotlib.animation as animation
from PyQt5.QtCore import QThread, QObject, pyqtSignal

from collections import defaultdict
from lmfit.models import GaussianModel, LorentzianModel, ExponentialModel
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QProgressBar

def create_model(model, prefix):
    if model is Model.GAUSSIAN:
        return GaussianModel(prefix=prefix)
    elif model is Model.LORENTZ:
        return LorentzianModel(prefix=prefix)
    else:
        return GaussianModel(prefix=prefix)


class Peak:
    def __init__(self, data_index, peak_index, model_name):
        self.data_index = data_index
        self.peak_index = peak_index
        self.model = create_model(model_name)


class OrgnFitterThreadException(Exception):
    def __init__(self, value):
        self.value = value
    def __srt__(self):
        return repr(self.value)

class OrgnFitterThread(QThread):
    #define signals
    complete_changed = pyqtSignal(int, name="Completed")
    exception_occur = pyqtSignal(Exception, name="ExceptionOccur")
    def __init__(self, parent=None, *args):
        QThread.__init__(self, parent)
        if len(args) < 3:
            raise OrgnFitterThreadException("OrgnFitterThread did not get some arguments.")
        self.args = args
        self.complete_locker = threading.Lock()
        self.data_locker = threading.Lock()
        self.fit_data = []
        self.fit_params = defaultdict(list)

        self.stop = False
        self.stop_locker = threading.Lock()

    def stop_fit(self):
        self.stop_locker.acquire(0)
        self.stop = True
        self.stop_locker.release()

    def run(self):
        try:
            self.fit_all_th()
        except Exception as inst:
            print(inst)
            self.exception_occur.emit(inst)


    def fit_all_th(self):
        last_indexes = []
        last_prefix = 1
        completed = 0
        try:
            wks = self.args[0]
            dataset_peaks_indexes = self.args[1]
            settings = self.args[2]
        except:
            raise OrgnFitterThreadException("Check fitting arguments. Some arguments were corrupted")
        x_data = wks.get_x()
        if len(x_data) is 0:
            raise OrgnFitterThreadException("x data is empty. Check the worksheet.")
        all_y_data = wks.get_y_data()
        if len(all_y_data) is 0:
            raise OrgnFitterThreadException("y data is empty. Check the worksheet.")
        model = None#ExponentialModel(prefix='exp_')
        parameters = None#model.guess(all_y_data[0], x=x_data)
        first_fit = True
        procent = 100 / len(all_y_data)
        for i_dataset, y_data in enumerate(all_y_data):
            self.stop_locker.acquire(0)
            if self.stop is True:
                self.stop_locker.release()
                #self.finish_callback(self.fit_params, self.fit_data)
                return
            self.stop_locker.release()

            indexes = dataset_peaks_indexes[i_dataset]
            for ind in indexes:
                has_new = False
                for i, x in enumerate(last_indexes):
                    if x - settings.min_peak_dist < ind < x + settings.min_peak_dist + 1:
                        has_new = True
                        last_indexes[i] = ind
                        break
                if not has_new:
                    prefix_str = 'g{}_'.format(last_prefix)
                    last_prefix += 1
                    cur_model = create_model(settings.model, prefix=prefix_str)
                    if model is None:
                        parameters = cur_model.guess(y_data, x=x_data)
                        model = cur_model
                    else:
                        parameters.update(cur_model.guess(y_data, x=x_data))
                        model += cur_model
                    parameters[prefix_str + 'center'].set(x_data[ind])
                    # parameters['g1_sigma'].set(0.003, min=0.002)
                    parameters[prefix_str + 'amplitude'].set(y_data[ind])
                    last_indexes.append(ind)

                ''''if first_fit:# means it is first fit
                    prefix_str = 'g{}_'.format(last_prefix)
                    last_prefix += 1
                    cur_model = create_model(settings.model, prefix=prefix_str)
                    if model is None:
                        parameters = cur_model.guess(y_data, x=x_data)
                        model = cur_model
                    else:
                        parameters.update(cur_model.guess(y_data, x=x_data))
                        model += cur_model
                    parameters[prefix_str + 'center'].set(x_data[ind])
                    # parameters['g1_sigma'].set(0.003, min=0.002)
                    parameters[prefix_str + 'amplitude'].set(y_data[ind])
                    last_indexes = list(indexes)
                else:
                    has_new = False
                    for i, x in enumerate(last_indexes):
                        if x - settings.min_peak_dist < ind < x + settings.min_peak_dist + 1:
                            has_new = True
                            last_indexes[i] = ind
                            break
                    if not has_new:
                        prefix_str = 'g{}_'.format(last_prefix)
                        last_prefix += 1
                        cur_model = create_model(settings.model, prefix=prefix_str)
                        parameters.update(cur_model.guess(y_data, x=x_data))
                        model += cur_model
                        parameters[prefix_str + 'center'].set(x_data[ind])
                        # parameters['g1_sigma'].set(0.003, min=0.002)
                        parameters[prefix_str + 'amplitude'].set(y_data[ind])
                        last_indexes.append(ind)'''''
            result = model.fit(y_data, parameters, x=x_data, fit_kws={'nan_policy': 'omit'})
            self.data_locker.acquire(0)
            self.fit_data.append(result.best_fit)
            for index in range(1, last_prefix):
                prefix_str = 'g{}_'.format(index)
                if first_fit or (prefix_str + 'center') not in self.fit_params:
                    self.fit_params[prefix_str + 'x'] = []
                    self.fit_params[prefix_str + 'center'] = []
                    self.fit_params[prefix_str + 'sigma'] = []
                    self.fit_params[prefix_str + 'amplitude'] = []
                self.fit_params[prefix_str + 'x'].append(wks.get_x_from_comments()[i_dataset])
                self.fit_params[prefix_str + 'center'].append(result.best_values[prefix_str + 'center'])
                self.fit_params[prefix_str + 'sigma'].append(result.best_values[prefix_str + 'sigma'])
                self.fit_params[prefix_str + 'amplitude'].append(result.best_values[prefix_str + 'amplitude'])
                parameters[prefix_str + 'center'].set(result.best_values[prefix_str + 'center'])
                parameters[prefix_str + 'sigma'].set(result.best_values[prefix_str + 'sigma'])
                parameters[prefix_str + 'amplitude'].set(result.best_values[prefix_str + 'amplitude'])
            self.data_locker.release()
            if first_fit:
                first_fit = False
            completed += procent
            self.complete_changed.emit(completed)
        self.write()

    def write(self):
        fit_params_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_params_orgn.txt', 'wb')
        fit_data_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_data_orgn.txt', 'wb')

        self.data_locker.acquire(0)
        pickle.dump(self.fit_params, fit_params_file)
        pickle.dump(self.fit_data, fit_data_file)
        self.data_locker.release()
        #result_file = open('C:\OriginUserFolder\FittingProject\scripts/result_pl.txt', 'wb')
        #pickle.dump(self.results, result_file)
        #result_file.close()
        fit_data_file.close()
        fit_params_file.close()

    def read(self):
        fit_params_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_params_orgn.txt', 'rb')
        fit_data_file = open('C:\OriginUserFolder\FittingProject\scripts/fit_data_orgn.txt', 'rb')
        self.data_locker.acquire(0)
        self.fit_params = pickle.load(fit_params_file)
        self.fit_data = pickle.load(fit_data_file)
        self.data_locker.release()
        fit_data_file.close()
        fit_params_file.close()
