import PyOrigin
import matplotlib.pyplot as plt
from numpy import sqrt, pi, exp

# method with fit function
def gaussian_func(x, amp, cen, wid):
    "1-d gaussian: gaussian(x, amp, cen, wid)"
    return (amp / (sqrt(2 * pi) * wid)) * exp(-(x - cen) ** 2 / (2 * wid ** 2))

class BaseFitAlgorithm:
    def __init__(self, wks_wrapper):
        self._wks_wrapper = wks_wrapper

    def build_plots(self, x, y, fit_data):
        plt.plot(x, y, 'bo')
        plt.plot(x, fit_data.init_fit, 'k--')
        plt.plot(x, fit_data.best_fit, 'r-')
        plt.show()


    # methos that should be reimplimented
    def algorithm_function(self, x, y, args=None):
        g_model = Model(gaussian_func)
        amp = 5
        if 'amp' in args:
            amp = args['amp']
        cen = 5
        if 'cen' in args:
            cen = args['cen']
        wid = 1
        if 'wid' in args:
            wid = args['wid']
        result = g_model.fit(y, x=x, amp=amp, cen=cen, wid=wid)
        return result

    def create_result_worksheet(self, ):

    def process_algorithm(self):
        x = self._wks_wrapper.get_x()
        y_data = self._wks_wrapper.get_y_data()