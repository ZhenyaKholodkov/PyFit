import sys, os
import PyOrigin

# append path to packages

pck_path = PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\site-packages"
sys.path.append(pck_path)
exec(open(PyOrigin.GetPath(PyOrigin.PATHTYPE_USER)+"FittingProject\scripts\WorkSheetWrapper.py").read())
##########################
# from GaussianScript import gaussian
# from SimplexAlgorithm_NelderMead import simplex_func

import numpy as np
import pandas as pd
from scipy.stats import norm
from lmfit.models import ExponentialModel, GaussianModel, LorentzianModel, VoigtModel, \
    PseudoVoigtModel, MoffatModel, Pearson7Model, StudentsTModel, BreitWignerModel, \
    LognormalModel, DampedOscillatorModel, DampedHarmonicOscillatorModel, \
    ExponentialGaussianModel, SkewedGaussianModel, DonaichModel, ConstantModel, \
    QuadraticModel, PolynomialModel, LinearModel
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import matplotlib.pyplot as plt
import peakutils
from peakutils.plot import plot as pplot
from numpy import loadtxt

# exec(open(r'C:\OriginUserFolder\FittingProject\scripts\.py').read())
items = {'gaussian': GaussianModel, 'loren': LorentzianModel, 'voigt': VoigtModel,
'pseudovoigt': PseudoVoigtModel, 'moffat': MoffatModel, 'pearson': Pearson7Model,
'sudentst': StudentsTModel, 'breitwigner': BreitWignerModel, 'lognormal': LognormalModel,
'dampedoscillator': DampedOscillatorModel, 'dampedharmonicoscillator': DampedHarmonicOscillatorModel,
'exponentialgaussian': ExponentialGaussianModel, 'skewedgaussian': SkewedGaussianModel,
'donaich': DonaichModel, 'constant': ConstantModel, 'quadratic': QuadraticModel,
'polynomial': PolynomialModel, 'linear': LinearModel}

class FittingFunctionException(Exception):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return repr(self._value)


class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)

        layout = QVBoxLayout()
        self.list_box = QComboBox(parent)
        for it in items:
            self.list_box.addItem(it)
        self.list_box.currentIndexChanged.connect(self.selectionchange)
        self.list_box.move(50, 50)
        layout.addWidget(self.list_box)

        self.b_exec = QPushButton("Execute")
        self.b_exec.setCheckable(True)
        self.b_exec.toggle()
        # self.b_exec.clicked.connect(lambda: self.whichbtn(self.b_exec))
        self.b_exec.clicked.connect(self.btnstate)
        layout.addWidget(self.b_exec)

        self.b_exec = QPushButton("Build First Y")
        self.b_exec.setCheckable(True)
        self.b_exec.toggle()
        # self.b_exec.clicked.connect(lambda: self.whichbtn(self.b_exec))
        self.b_exec.clicked.connect(self.btnstate_builf_first)
        layout.addWidget(self.b_exec)


        self.b_exec = QPushButton("Build All")
        self.b_exec.setCheckable(True)
        self.b_exec.toggle()
        # self.b_exec.clicked.connect(lambda: self.whichbtn(self.b_exec))
        self.b_exec.clicked.connect(self.btnstate_build_all)
        layout.addWidget(self.b_exec)

        self.setLayout(layout)
        self.setWindowTitle("Choose script")

    def btnstate(self):
        if self.b_exec.isChecked():
            try:
                fitting_process(items[self.list_box.currentText()]())
            except FittingFunctionException as e:
                print("Fitting error:")
            except IOError as e:
                print("I/O error({0}): {1}".format(e.errno, e.strerror))
            except ValueError:
                print("Could not convert data to an integer.")
            except Exception as inst:
                print(type(inst))
                print(inst)
                print(inst.args)
            except:
                print("an error has occured!")
            self.done(0)
        '''else:
            print("button released")'''

    def btnstate_builf_first(self):
        if self.b_exec.isChecked():
            try:
                find_peaks()
                #build_first_plots_twoPeaks(self.list_box.currentText())
            except FittingFunctionException as e:
                print("Fitting error:" + e)
            except IOError as e:
                print("I/O error({0}): {1}".format(e.errno, e.strerror))
            except ValueError as e:
                print("Could not convert data to an integer.")
                print(e)
            except Exception as e:
                print(type(e))
                print(e)
                print(e.args)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
            except:
                print("an error has occured!")
            #self.done(0)

    def btnstate_build_all(self):
        if self.b_exec.isChecked():
            try:
                build_all_plots(items[self.list_box.currentText()]())
            except FittingFunctionException as e:
                print("Fitting error:" + e)
            except IOError as e:
                print("I/O error({0}): {1}".format(e.errno, e.strerror))
            except ValueError as e :
                print("Could not convert data to an integer.")
                print("I/O error({0}): {1}".format(e.errno, e.strerror))
                print(e)
            except Exception as e:
                print(type(e))
                print(e)
                print(e.args)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
            except:
                print("an error has occured!")
            #self.done(0)

    def selectionchange(self, i):
        print("Items in the list are :")
        for count in range(self.list_box.count()):
            print(self.list_box.itemText(count))
        print("Current index", i, "selection changed ", self.list_box.currentText())

    '''def whichbtn(self, b):
        print("clicked button is " + b.text())'''


def show_plots_jpvelez(x, amp, sigma):
    # Define parameters for normal distribution.
    mu = amp
    sigma = sigma
    rng = x

    # Generate normal distribution with given mean and standard deviation.
    dist = norm(mu, sigma)

    # Plot probability density function and of this distribution.
    # the pdf() method takes takes in a list x values and returns a list of y's.
    plt.subplot(311)  # Creates a 3 row, 1 column grid of plots, and renders the following chart in slot 1.
    plt.plot(rng, dist.pdf(rng), 'r', linewidth=2)
    plt.title('Probability density function of normal distribution')

    # Plot probability density function and of this distribution.
    plt.subplot(312)
    plt.plot(rng, dist.cdf(rng))
    plt.title('Cumulutative distribution function of normal distribution')

    # Draw 1000 samples from the random variable.
    sample = dist.rvs(size=10000)

    print
    "Sample descriptive statistics:"
    print
    pd.DataFrame(sample).describe()

    # Plot a histogram of the samples.
    plt.subplot(313)
    plt.hist(sample, bins=100, normed=True)
    plt.plot(rng, dist.pdf(rng), 'r--', linewidth=2)
    plt.title('10,000 random samples from normal distribution')

    # Show all plots.
    plt.show()


def build_plots(x, y, fit_res):
    params_dict = fit_res.params.valuesdict()
    #dist = norm(params_dict['amplitude'], params_dict['center'])
    plt.plot(x, y, 'b-')
    plt.plot(x, fit_res.best_fit, 'r-')
    # plt.savefig(figname)
    plt.show()

def build_first_plots(model_name):
    model = items[model_name]()
    work_sheet = PyOrigin.WorksheetPages(PyOrigin.ActivePage().GetName()).Layers(0)
    sheet_wrapper = WorkSheetWrapper(work_sheet)
    x_data = sheet_wrapper.get_x()
    y_data = sheet_wrapper.get_y_data()
    # guess parameters for first set of y-es
    parameters = model.guess(y_data[0], x=x_data)
    result = model.fit(y_data[0], parameters, x=x_data)
    params_dict = result.params.valuesdict()
    if 'amplitude' in params_dict and 'center' in params_dict:
        build_plots(x_data, y_data[0], result)

def find_peaks():
    work_sheet = PyOrigin.WorksheetPages(PyOrigin.ActivePage().GetName()).Layers(0)
    sheet_wrapper = WorkSheetWrapper(work_sheet)
    x = sheet_wrapper.get_x()
    y = sheet_wrapper.get_y_data()[0]

    #plt.figure(figsize=(10, 6))
    #plt.plot(x, y)
    #plt.title("Data with noise")
    indexes = peakutils.indexes(y, thres=0.01, min_dist=5)
    print(indexes)
    print(x[indexes], y[indexes])
    plt.figure(figsize=(30, 16))
    pplot(x, y, indexes)
    plt.title('First estimate')
    plt.show()


def build_first_plots_twoPeaks(model_name):
    model_g1 = items[model_name](prefix='g1_')
    model_g2 = items[model_name](prefix='g2_')
    model_g3 = items[model_name](prefix='g3_')

    work_sheet = PyOrigin.WorksheetPages(PyOrigin.ActivePage().GetName()).Layers(0)
    sheet_wrapper = WorkSheetWrapper(work_sheet)
    #data = sheet_wrapper.get_x()
    #indices = np.nonzero(np.logical_and(data >= 1.62, data <= 1.68))

    '''x_data = []
    for index in indices[0]:
        x_data.append(data[index])
    data = sheet_wrapper.get_y_data()[0]
    y_data = []
    for index in indices[0]:
        y_data.append(data[index])

    x_data =  np.array(x_data)
    y_data =  np.array(y_data)'''
    x_data = np.array(sheet_wrapper.get_x())
    y_data = np.array(sheet_wrapper.get_y_data()[0])
    # guess parameters for first set of y-es
    exp_mod = ExponentialModel(prefix='exp_')

    parameters = exp_mod.guess(y_data, x=x_data)
    #parameters = model.guess(y_data, x=x_data)
    parameters.update(model_g1.guess(y_data, x=x_data))
    parameters['g1_center'].set(1.64535499, min=1.640, max=1.648)
    parameters['g1_sigma'].set(0.003, min=0.002)
    parameters['g1_amplitude'].set(7111, min=1)

    parameters.update(model_g2.guess(y_data, x=x_data))
    parameters['g2_center'].set(1.64945494, min=1.648, max=1.653)
    parameters['g2_sigma'].set(0.0022, min=0.001)
    parameters['g2_amplitude'].set(7170, min=1)

    parameters.update(model_g3.guess(y_data, x=x_data))
    parameters['g3_center'].set(1.6538741, min=1.65329, max=1.65448)
    parameters['g3_sigma'].set(0.00256, min=0.001)
    parameters['g3_amplitude'].set(475, min=1)

    #parameters['g1_sigma'].set(0.02, min=0.01)
    #parameters['g2_sigma'].set(0.01, min=0.001)

    mod = model_g1 + model_g2 + model_g3 + exp_mod

    print(parameters)


    plt.figure(figsize=(30, 16))
    init = mod.eval(parameters, x=x_data)
    #plt.semilogy(x_data, y_data, 'b--')
    #plt.semilogy(x_data, init, 'g--')
    print(y_data)
    print(x_data)
    result = mod.fit(y_data, parameters, x=x_data, fit_kws={'nan_policy': 'omit'})
    #plt.semilogy(x_data, result.best_fit, 'r-')
    plt.plot(x_data, y_data, 'b--')
    plt.plot(x_data, result.best_fit)
    plt.show()
    params_dict = result.params.valuesdict()
    '''if 'amplitude' in params_dict and 'center' in params_dict:
        build_plots(x_data, y_data[0], result)'''

def build_all_plots(model):
    work_sheet = PyOrigin.WorksheetPages(PyOrigin.ActivePage().GetName()).Layers(0)
    sheet_wrapper = WorkSheetWrapper(work_sheet)
    x = sheet_wrapper.get_x()
    y_data = sheet_wrapper.get_y_data()
    # guess parameters for first set of y-es
    parameters = model.guess(y_data[0], x=x)
    result = []
    for y in y_data:
        parameters = model.fit(y, parameters, x=x)
        print(parameters.params.valuesdict())
        result.append(parameters)

    '''plt.plot(x, result[0].best_fit, 'r-')
    for i in range(1, len(params_dict)-1):
        plt.plot(x, data.best_fit, 'b--')
    plt.plot(x, result[len(result)].best_fit, 'r-')'''

def fit_worksheet(model):
    work_sheet = PyOrigin.WorksheetPages(PyOrigin.ActivePage().GetName()).Layers(0)
    sheet_wrapper = WorkSheetWrapper(work_sheet)
    x = sheet_wrapper.get_x()
    y_data = sheet_wrapper.get_y_data()
    # guess parameters for first set of y-es
    parameters = model.guess(y_data[0], x=x)
    result = []
    for y in y_data:
        parameters = model.fit(y, parameters, x=x)
        result.append(parameters)
    return result

def fitting_process(model):
    data = fit_worksheet(model)
    create_result_worksheet(data)


def create_result_worksheet(x, fit_data):
    result_sheet = WorkSheetWrapper.create_new_worksheet("FitResult", "Res_page")
    result_sheet.set_col_name(0, "X")
    result_sheet.set_col_type(ColumnType.ColumnType_X.value, 0)
    result_sheet.delete_col(1)
    row = 0
    for data in fit_data:
        params_dict = data.params.valuesdict()
        col = 0
        for key, value in params_dict.iteritems():
            result_sheet.add_col(col, key)
            result_sheet.set_cell_value(value, row, col)
            col += 1
        row += 1


def main():
    argv = []
    app = QApplication(argv)
    ex = Form()
    ex.show()
    app.exec_()


if __name__ == '__main__':
    main()
    '''data = loadtxt("C:/temp/test_peak.dat")
    #work_sheet = PyOrigin.WorksheetPages(PyOrigin.ActivePage().GetName()).Layers(0)
    #sheet_wrapper = WorkSheetWrapper(work_sheet)
    __x = sheet_wrapper.get_x()
    #y = sheet_wrapper.get_y_data()[0]
    x = data[:, 0]
    y = data[:, 1]
    print(type(__x))
 
    gamma_free = False
 
    MODEL = 'gauss'
    # MODEL = 'loren'
    # MODEL = 'voigt'
    # gamma_free = True
 
    if MODEL.lower().startswith('g'):
        mod = GaussianModel()
        gamma_free = False
        figname = '../doc/_images/models_peak1.png'
    elif MODEL.lower().startswith('l'):
        mod = LorentzianModel()
        gamma_free = False
        figname = '../doc/_images/models_peak2.png'
    elif MODEL.lower().startswith('v'):
        mod = VoigtModel()
        figname = '../doc/_images/models_peak3.png'
 
    pars = mod.guess(y, x=x)
 
    if gamma_free:
        pars['gamma'].set(value=0.7, vary=True, expr='')
        figname = '../doc/_images/models_peak4.png'
 
    out = mod.fit(y, pars, x=x)
    print(out.fit_report(min_correl=0.25))
 
    plt.plot(x, y, 'b-')
    plt.plot(x, out.best_fit, 'r-')
    # plt.savefig(figname)
    plt.show()
    # <end examples/doc_builtinmodels_peakmodels.py>'''
