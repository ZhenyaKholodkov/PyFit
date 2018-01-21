import numpy as np
import os
import matplotlib.pyplot as plt
from lmfit.models import GaussianModel, ExponentialModel, LorentzianModel, VoigtModel
import scipy
from scipy.optimize import leastsq
###############################################################################
###############################################################################

#os.chdir('D:/reference')

def readfio(filename):
    cols = []
# Open file
    f = open(filename +'.fio')
    counter = 0
    for n, line in enumerate(f):
        if line.strip().startswith('Col'):
            linestoskip = n +  1
            cols.append(line.split()[2]) #To have only the column headers in a list
            counter = counter + 1 #gives the number of columns, in principle it is not necessary
    f.close() # close the file
    # Read numerical data without header
    #print (cols)
    data = np.genfromtxt(filename+'.fio',skip_header=linestoskip, skip_footer =1)
    return data, cols
###############################################################################
###############################################################################
def fitting():
    data, cols = readfio(filename)
    x = (2*np.pi/wavelength(energy))*(np.sin(np.radians(data[:,cols.index('om')]))+
    np.sin(np.radians(data[:,cols.index('tt')])-np.radians(data[:,cols.index('om')])))
    y = data[:,cols.index('signalcounter_atten')]/data[:,cols.index('petra_beamcurrent')]
    for ix in np.where(np.isnan(y)):
        y[ix] = (y[ix - 1] + y[ix + 1]) / 2.0
    exp_mod = ExponentialModel(prefix='exp_')
    pars = exp_mod.guess(y, x=x)

    gauss1  = LorentzianModel(prefix='g1_')
    pars.update( gauss1.make_params())
    print("g1")
    print(pars)

    pars['g1_center'].set(3.33, min=3.2, max=3.45)
    pars['g1_sigma'].set(0.02, min=0.01)
    pars['g1_amplitude'].set(2000, min=1)

    gauss2  = LorentzianModel(prefix='g2_')

    pars.update(gauss2.make_params())

    print("g2")
    print(pars)
    pars['g2_center'].set(3.59, min=3.45, max=3.7)
    pars['g2_sigma'].set(0.01, min=0.001)
    pars['g2_amplitude'].set(10000, min=1)

    mod = gauss1 + gauss2 + exp_mod


    init = mod.eval(pars, x=x)
    plt.semilogy(x, y)
    plt.semilogy(x, init, 'k--')

    out = mod.fit(y, pars, x=x)

    print(out.fit_report(min_correl=0.01))

    plt.semilogy(x, out.best_fit, 'r-')
    plt.show()
###############################################################################    ###############################################################################

def wavelength(energy):
    h = 6.626e-34  #joules
    c = 2.998e8    #m/sec
    eV = 1.602e-19 #Joules
    wavelength = h*c/(energy*1000*eV)*1e10
    return wavelength

##############################################################################
''''energy = 10.000 # in KeV
filename = 'alignment_00241'
fitting()'''''
import numpy as np
import matplotlib.pyplot as plt
from lmfit import minimize, Parameters, report_fit

def gauss(x, amp, cen, sigma):
    "basic gaussian"
    return amp*np.exp(-(x-cen)**2/(2.*sigma**2))

def gauss_dataset(params, i, x):
    """calc gaussian from params for data set i
    using simple, hardwired naming convention"""
    amp = params['amp_%i' % (i+1)].value
    cen = params['cen_%i' % (i+1)].value
    sig = params['sig_%i' % (i+1)].value
    return gauss(x, amp, cen, sig)

def objective(params, x, data):
    """ calculate total residual for fits to several data sets held
    in a 2-D array, and modeled by Gaussian functions"""
    ndata, nx = data.shape
    resid = 0.0*data[:]
    # make residual per data set
    for i in range(ndata):
        resid[i, :] = data[i, :] - gauss_dataset(params, i, x)
    # now flatten this to a 1D array, as minimize() needs
    return resid.flatten()

# create 5 datasets
x  = np.linspace( -1, 2, 151)
data = []
for i in np.arange(5):
    params = Parameters()
    amp   =  0.60 + 9.50*np.random.rand()
    cen   = -0.20 + 1.20*np.random.rand()
    sig   =  0.25 + 0.03*np.random.rand()
    dat   = gauss(x, amp, cen, sig) + np.random.normal(size=len(x), scale=0.1)
    data.append(dat)

# data has shape (5, 151)
data = np.array(data)
assert(data.shape) == (5, 151)

# create 5 sets of parameters, one per data set
fit_params = Parameters()
for iy, y in enumerate(data):
    fit_params.add( 'amp_%i' % (iy+1), value=0.5, min=0.0,  max=200)
    fit_params.add( 'cen_%i' % (iy+1), value=0.4, min=-2.0,  max=2.0)
    fit_params.add( 'sig_%i' % (iy+1), value=0.3, min=0.01, max=3.0)

# but now constrain all values of sigma to have the same value
# by assigning sig_2, sig_3, .. sig_5 to be equal to sig_1
for iy in (2, 3, 4, 5):
    fit_params['sig_%i' % iy].expr='sig_1'

# run the global fit to all the data sets
result = minimize(objective, fit_params, args=(x, data))
report_fit(result.params)

# plot the data sets and fits
plt.figure()
for i in range(5):
    y_fit = gauss_dataset(result.params, i, x)
    plt.plot(x, data[i, :], 'o', x, y_fit, '-')

plt.show()