import lmfit
import numpy as np
# Instrukcja dla nowej modeli
# Zmie? nazw? klasy
class CustomModel(lmfit.Model):
    def __init__(self, *args, **kwargs):
        # zmie? funkcj?. Je?li funkcja potrzebuje parametr?w amplitude i center,
        # to oni musz? zostac bez zmian w nazwach
        def function(x, amplitude, center, offset, freq, tau):
            return amplitude * np.sin((x - center)*freq) * np.exp(-x/tau) + offset
        # zmie? tu nazw? klasy
        super(CustomModel, self).__init__(function, *args, **kwargs)

    # funkcja ustawia parametry inicjalizacyjne
    # data - y  
    def guess(self, data, x, **kwargs):
        params = self.make_params()
        def pset(param, value):
            params["%s%s" % (self.prefix, param)].set(value=value)

        # zmie? na swoje parametry. (Je?li funkcja ma parametry amplitude i center, to oni b?d?
        # zmienione zgodnie ze znalezionych pik?w)
        pset("amplitude", np.max(data) - np.min(data))
        pset("center", 0)
        pset("offset", np.mean(data))
        pset("freq", 1)
        pset("tau", 1)

        return lmfit.models.update_param_vals(params, self.prefix, **kwargs)