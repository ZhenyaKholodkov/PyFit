from numpy import sqrt, pi, exp
import PyOrigin
import matplotlib.pyplot as plt

from lmfit import Model


def gaussian_func(x, amp, cen, wid):
    "1-d gaussian: gaussian(x, amp, cen, wid)"
    return (amp / (sqrt(2 * pi) * wid)) * exp(-(x - cen) ** 2 / (2 * wid ** 2))


def gaussian_algorithm(_x, _y):
    g_model = Model(gaussian_func)
    result = g_model.fit(_y, x=_x, amp=5, cen=5, wid=1)
    return result



def gaussian():
    work_sheet = PyOrigin.WorksheetPages(PyOrigin.ActivePage().GetName()).Layers(0)
    sheet_wrapper = WorkSheetWrapper(work_sheet)
    x = sheet_wrapper.get_x()
    y_data = sheet_wrapper.get_y_data()
    if(len(y_data) == 0):
        print("Data is empty.")

    result_sheet = WorkSheetWrapper.create_new_worksheet("FitResult", "Res_page")
    result_sheet.set_col_name(0, "X")
    result_sheet.set_col_type(ColumnType.ColumnType_X.value, 0)
    result_sheet.set_data_column(sheet_wrapper.get_x_from_comments(), 0)
    result_sheet.set_col_name(1, "Amp")
    result_sheet.add_col(2, "Cel")
    result_sheet.add_col(3, "Wid")
    row = 0
    for y in y_data:
        res = gaussian_algorithm(x, y)
        params_dict = res.params.valuesdict()
        if 'amp' in params_dict:
            result_sheet.set_cell_value(res.params.valuesdict()['amp'], row, 1)
        if 'cen' in params_dict:
            result_sheet.set_cell_value(res.params.valuesdict()['cen'], row, 2)
        if 'wid' in params_dict:
            result_sheet.set_cell_value(res.params.valuesdict()['wid'], row, 3)
        row += 1
       # print(res.fit_report())
