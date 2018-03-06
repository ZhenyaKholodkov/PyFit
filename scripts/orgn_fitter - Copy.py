import sys
import PyOrigin
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
                         DonaichModel, ExponentialModel


def create_model(model, prefix):
    if model is Model.GAUSSIAN:
        return GaussianModel(prefix=prefix)
    elif model is Model.LORENTZ:
        return LorentzianModel(prefix=prefix)
    elif model is Model.VOIGT:
        return VoigtModel(prefix=prefix)
    elif model is Model.MOFFAT:
        return MoffatModel(prefix=prefix)
    elif model is Model.PEARSON7:
        return Pearson7Model(prefix=prefix)
    elif model is Model.STUDENTST:
        return StudentsTModel(prefix=prefix)
    elif model is Model.BREITWIGNER:
        return BreitWignerModel(prefix=prefix)
    elif model is Model.LOGNORMAL:
        return LognormalModel(prefix=prefix)
    elif model is Model.DAMPEDOCSILLATOR:
        return DampedOscillatorModel(prefix=prefix)
    elif model is Model.DAMPEDHARMONICOCSILLATOR:
        return DampedHarmonicOscillatorModel(prefix=prefix)
    elif model is Model.EXPONENTIALGAUSSIAN:
        return ExponentialGaussianModel(prefix=prefix)
    elif model is Model.SKEWEDGAUSSIAN:
        return SkewedGaussianModel(prefix=prefix)
    elif model is Model.DONAICH:
        return DonaichModel(prefix=prefix)
    elif model is Model.EXPONENTIAL:
        return ExponentialModel(prefix=prefix)
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
    # define signals
    complete_changed = pyqtSignal(int, name="Completed")
    exception_occur = pyqtSignal(Exception, name="ExceptionOccur")

    def __init__(self, parent, wks, peak_indexes, settings):
        QThread.__init__(self, parent)
        self.wks = wks
        self.peak_indexes = peak_indexes
        self.model_name = settings.model
        self.mpd = settings.min_peak_dist

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
        x_data = self.wks.get_x()
        if len(x_data) is 0:
            raise OrgnFitterThreadException("x data is empty. Check the worksheet.")

        all_y_data = self.wks.get_y_data()
        if len(all_y_data) is 0:
            raise OrgnFitterThreadException("y data is empty. Check the worksheet.")

        model = None#ExponentialModel(prefix='exp_')
        parameters = None#model.guess(all_y_data[0], x=x_data)
        percent = 100 / len(all_y_data)
        last_prefix = 1
        completed = 0

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
                        parameters = cur_model.guess(y_data, x=x_data)
                        model = cur_model
                    else:
                        parameters.update(cur_model.guess(y_data, x=x_data))
                        model += cur_model
                    parameters[prefix_str + 'center'].set(x_data[ind])
                    parameters[prefix_str + 'amplitude'].set(y_data[ind])

            # fit and append result
            if model is not None:
                result = model.fit(y_data, parameters, x=x_data, fit_kws={'nan_policy': 'omit'})
                self.data_locker.acquire(0)
                self.fit_data.append(result.best_fit)
                for index in range(1, last_prefix):
                    prefix_str = 'g{}_'.format(index)
                    if (prefix_str + 'center') not in self.fit_params:
                        #self.fit_params[prefix_str + 'x'] = []
                        self.fit_params[prefix_str + 'center'] = []
                        self.fit_params[prefix_str + 'sigma'] = []
                        self.fit_params[prefix_str + 'amplitude'] = []
                    #self.fit_params[prefix_str + 'x'].append(self.wks.get_x_from_comments()[i_data_set])
                    self.fit_params[prefix_str + 'center'].append(result.best_values[prefix_str + 'center'])
                    self.fit_params[prefix_str + 'sigma'].append(result.best_values[prefix_str + 'sigma'])
                    self.fit_params[prefix_str + 'amplitude'].append(result.best_values[prefix_str + 'amplitude'])
                    parameters[prefix_str + 'center'].set(result.best_values[prefix_str + 'center'])
                    parameters[prefix_str + 'sigma'].set(result.best_values[prefix_str + 'sigma'])
                    parameters[prefix_str + 'amplitude'].set(result.best_values[prefix_str + 'amplitude'])
                self.data_locker.release()
                completed += percent
                self.complete_changed.emit(completed)
