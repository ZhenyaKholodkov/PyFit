import sys
import PyOrigin
import importlib
import inspect
import os
from os import listdir
from collections import OrderedDict
import numpy as np
# exec(open(r'C:\OriginUserFolder\PyFit\scripts\.py').read())
# append path to packages
pck_path = PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "PyFit\site-packages"
sys.path.append(pck_path)
##########################
import threading
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from collections import defaultdict
from lmfit.models import GaussianModel, LorentzianModel, VoigtModel, MoffatModel, Pearson7Model, \
                         StudentsTModel, BreitWignerModel, LognormalModel, DampedOscillatorModel, \
                         DampedHarmonicOscillatorModel, ExponentialGaussianModel, SkewedGaussianModel, \
                         DonaichModel, ExponentialModel, PowerLawModel

gl_models_dictionary = OrderedDict([("Gaussian's Model", GaussianModel),
                        ("Lorentz's Model", LorentzianModel),
                        ("Voigt's Model", VoigtModel),
                        ("Moffat's Model", MoffatModel),
                        ("Pearson7Model", Pearson7Model),
                        ("StudentsTModel", StudentsTModel),
                        ("BreitWignerModel", BreitWignerModel),
                        ("LognormalModel", LognormalModel),
                        ("DampedOcsillatorModel", DampedOscillatorModel),
                        ("DampedHarmonicOcsillatorModel", DampedHarmonicOscillatorModel),
                        ("ExponentialGaussianModel", ExponentialGaussianModel),
                        ("SkewedGaussianModel", SkewedGaussianModel),
                        ("DonaichModel", DonaichModel),
                        ("ExponentialModel", ExponentialModel),
                        ("PowerLawModel", PowerLawModel)
                        ])

custom_path = PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "PyFit/scripts/CustomModels/"
sys.path.append(custom_path)
custom_models_list = listdir(custom_path)
for c_file in custom_models_list:
    #exec(open(custom_path + c_file).read())
    module = importlib.import_module(os.path.splitext(c_file)[0])
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj):
            gl_models_dictionary[obj.__name__] = obj


def create_model(model, prefix):
    return gl_models_dictionary[model](prefix=prefix)

def create_params(model_name, x_data, all_y_data, peak_indexes, mpd):
    model = None#ExponentialModel(prefix='exp_')
    parameters = None#model.guess(all_y_data[0], x=x_data)
    last_prefix = 1
    completed = 0
    for i_data_set, y_data in enumerate(all_y_data):
        # find first entry of the peak to build a model
        for ind in peak_indexes[i_data_set]:
            is_new_ind = True
            if i_data_set is not 0:
                for last in peak_indexes[i_data_set - 1]:
                    if last - mpd < ind < last + mpd + 1:
                        is_new_ind = False
                        break
            # if new peak was found
            if is_new_ind:
                # create model for new peaks
                prefix_str = 'g{}_'.format(last_prefix)
                last_prefix += 1
                cur_model = create_model(model_name, prefix=prefix_str)
                if model is None:
                    parameters = cur_model.guess(y_data, x=x_data)
                    model = cur_model
                else:
                    parameters.update(cur_model.guess(y_data, x=x_data))
                    model += cur_model
                params_dict = parameters.valuesdict()
                if prefix_str + 'center' in params_dict:
                    parameters[prefix_str + 'center'].set(x_data[ind])
                if prefix_str + 'amplitude' in params_dict:
                    parameters[prefix_str + 'amplitude'].set(y_data[ind])
    return parameters

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
    # define signals
    complete_changed = pyqtSignal(int, name="Completed")
    exception_occur = pyqtSignal(Exception, name="ExceptionOccur")

    def __init__(self, parent, wks, peak_indexes, settings):
        QThread.__init__(self, parent)
        self.wks = wks
        self.peak_indexes = peak_indexes
        self.model_name = settings.model
        self.mpd = settings.min_peak_dist
        self.algorithms = settings.algorithms
        self.parameters = settings.parameters

        self.complete_locker = threading.Lock()
        self.data_locker = threading.Lock()
        self.fit_data = []
        self.component_data = []
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
        x_data = self.wks.get_x()
        if len(x_data) is 0:
            raise OrgnFitterThreadException("x data is empty. Check the worksheet.")

        all_y_data = self.wks.get_y_data()
        if len(all_y_data) is 0:
            raise OrgnFitterThreadException("y data is empty. Check the worksheet.")

        model = None#ExponentialModel(prefix='exp_')
        parameters = self.parameters#model.guess(all_y_data[0], x=x_data)
        percent = 100 / len(all_y_data)
        last_prefix = 1
        completed = 0
        print("begin")
        for i_data_set, y_data in enumerate(all_y_data):
            self.stop_locker.acquire(0)
            if self.stop is True:
                self.stop_locker.release()
                return
            self.stop_locker.release()

            # find first entry of the peak to build a model
            for ind in self.peak_indexes[i_data_set]:
                is_new_ind = True
                if i_data_set is not 0:
                    for last in self.peak_indexes[i_data_set - 1]:
                        if last - self.mpd < ind < last + self.mpd + 1:
                            is_new_ind = False
                            break
                # if new peak was found
                if is_new_ind:
                    # create model for new peaks
                    prefix_str = 'g{}_'.format(last_prefix)
                    last_prefix += 1
                    cur_model = create_model(self.model_name, prefix=prefix_str)
                    if model is None:
                        if self.parameters is None:
                            parameters = cur_model.guess(y_data, x=x_data)
                            params_dict = parameters.valuesdict()
                            if prefix_str + 'center' in params_dict:
                                parameters[prefix_str + 'center'].set(x_data[ind])
                            if prefix_str + 'amplitude' in params_dict:
                                parameters[prefix_str + 'amplitude'].set(y_data[ind])
                        else:
                            for key, param in self.parameters.items():
                                if key[1] is '{}'.format(last_prefix):
                                    parameters[key] = self.parameters[key]
                        model = cur_model
                    else:
                        if self.parameters is None:
                            parameters.update(cur_model.guess(y_data, x=x_data))
                            params_dict = parameters.valuesdict()
                            if prefix_str + 'center' in params_dict:
                                parameters[prefix_str + 'center'].set(x_data[ind])
                            if prefix_str + 'amplitude' in params_dict:
                                parameters[prefix_str + 'amplitude'].set(y_data[ind])
                        else:
                            for key, param in self.parameters.items():
                                if key[1] is '{}'.format(last_prefix):
                                    parameters[key] = self.parameters[key]
                        model += cur_model

            print(parameters)
            # fit and append result
            if model is not None:
                if not self.algorithms: 
                    result = model.fit(y_data, parameters, x=x_data, fit_kws={'nan_policy': 'omit'})
                else:
                    params = parameters
                    for alg in self.algorithms:
                        result = model.fit(y_data, parameters, method=alg, x=x_data, fit_kws={'nan_policy': 'omit'})
                        params = result.best_values
  
                self.data_locker.acquire(0)
                self.fit_data.append(result.best_fit)
                comps = result.eval_components(x=x_data)
                self.component_data.append([])
                for index in range(1, last_prefix):
                    prefix_str = 'g{}_'.format(index)
                    self.component_data[i_data_set].append(comps[prefix_str].astype(np.int64))
                for param_name, params in result.best_values.items():
                    if param_name not in self.fit_params:
                        self.fit_params[param_name] = []
                    self.fit_params[param_name].append(result.best_values[param_name])
                    parameters[param_name].set(result.best_values[param_name])
                self.data_locker.release()
                completed += percent
                self.complete_changed.emit(completed)
