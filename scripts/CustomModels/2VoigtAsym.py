import lmfit
import numpy as np
# Instrukcja dla nowej modeli
# Zmie? nazw? klasy
class DoubleVoigtAsym(lmfit.Model):
    def __init__(self, *args, **kwargs):
        # zmie? funkcj?. Je?li funkcja potrzebuje parametr?w amplitude i center,
        # to oni musz? zostac bez zmian w nazwach
        def function(x, amplitude, center, sigma, mu, q):
            return amplitude*(mu*((sigma+q*(x-center))/2)**2/((x-center)**2+((sigma+q*(x-center))/2)**2)+(1-mu)*np.exp(-(x-center)**2/(2*(1/(2*np.sqrt(np.log(4)))*(sigma+q*(x-center)))**2)))
        # zmie? tu nazw? klasy
        super(DoubleVoigtAsym, self).__init__(function, *args, **kwargs)

    # funkcja ustawia parametry inicjalizacyjne
    # data - y  
    def guess(self, data, x, **kwargs):
        params = self.make_params()
        def pset(param, value, vary=None, min=None, max=None):
            params["%s%s" % (self.prefix, param)].set(value=value,vary=vary, min=min, max=max)
        # zmie? na swoje parametry. (Je?li funkcja ma parametry amplitude i center, to oni b?d?
        # zmienione zgodnie ze znalezionych pik?w)
		
        #wks_wrapper = WorkSheetWrapper(PyOrigin.WorksheetPages(PyOrigin.ActivePage().GetName()).Layers(0))
        pset("amplitude", 2000, vary=True, min=0)
        pset("center", 1.644, vary=True, min=x[0], max=x[len(data) - 1])
        pset("sigma", value= 0.004,  vary=True,  min=0.001,max=0.01)
        pset("mu",   value= 0 ,   vary=True,   min=0,      max=1) #False
        pset("q",     value= 0,   vary=False,   min=-0.14,   max=0.1) 

        return lmfit.models.update_param_vals(params, self.prefix, **kwargs)