import sys
import importlib
import PyOrigin
import os
import inspect
import subprocess
import webbrowser
pck_path = PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "PyFit\site-packages"
sys.path.append(pck_path)
sys.path.append(PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "PyFit\scripts\CustomModels")
import shutil
import ntpath
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QApplication, QSlider, QHBoxLayout, QVBoxLayout, QPushButton, QProgressBar, \
    QComboBox, QAction, QMenuBar, QLabel, QLineEdit, QPushButton, QMessageBox, QGroupBox, QGridLayout, \
    QFileDialog, QListWidget, QTableWidget, QTableWidgetItem


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


class PeakFunction(Enum):
    PEAK_DETECTOR = 0
    PEAK_UTILS = 1


class MarkerSetting:
    def __init__(self):
        self.left_value = None
        self.right_value = None

    def set_left_value(self, value):
        self.left_value = value

    def set_right_value(self, value):
        self.right_value = value

    def is_not_none(self):
        return self.left_value is not None and self.right_value is not None


class Setting:
    def __init__(self):
        self.model = "Gaussian's Model"#Model.GAUSSIAN
        self.min_peak_dist = 10
        self.min_amplitude = 500
        self.threshold = 0.06
        self.peak_function = PeakFunction.PEAK_UTILS
        self.animation_interval = 100
        self.algorithms = []
        self.parameters = None
        self.markers = MarkerSetting()

    def set_model(self, model):
        self.model = model


class SettingsDialog(QtWidgets.QDialog):
    peak_settings_changed = pyqtSignal(name="PeakSettingsChanged")

    def __init__(self, settings, parent):
        super(SettingsDialog, self).__init__(parent)

        self.parent = parent
        self.settings = settings

        # fitting model settings
        model_box = QHBoxLayout()
        self.lbl1 = QLabel('Fitting function', self)
        self.lbl1.setFixedHeight(20)
        self.lbl1.setFixedWidth(100)
        self.lbl1.resize(100, 40)

        self.cb = QComboBox()
        self.cb.currentIndexChanged.connect(self.__on_combobox_changed)
        for model_name in list(gl_models_dictionary):
            self.cb.addItem(model_name)
        self.current_index = self.cb.findText(settings.model, Qt.MatchFixedString)
        self.cb.setCurrentIndex(self.current_index)
        self.add_button = QPushButton('Add', self)
        self.add_button.clicked.connect(self.__add)
        self.add_show_folder = QPushButton('Show folder', self)
        self.add_show_folder.clicked.connect(self.__show_folder)
        self.add_show_help = QPushButton('Help models', self)
        self.add_show_help.clicked.connect(self.__open_help)
        
        algorithm_box = QHBoxLayout()
        self.algorithm_lbl1 = QLabel('Algorithms', self)
        self.algorithm_lbl1.setFixedHeight(20)
        self.algorithm_lbl1.setFixedWidth(100)
        self.algorithm_lbl1.resize(100, 40)
        self.cur_algorithm_list = QListWidget(self)
        self.algorithm_list = QListWidget(self)
        self.algorithm_list.addItem("leastsq")
        self.algorithm_list.addItem("least_squares")
        self.algorithm_list.addItem("differential_evolution")
        self.algorithm_list.addItem("brute")
        self.algorithm_list.addItem("nelder")
        self.algorithm_list.addItem("lbfgsb")
        self.algorithm_list.addItem("powell")
        self.algorithm_list.addItem("cg")
        self.algorithm_list.addItem("newton")
        self.algorithm_list.addItem("cobyla")
        self.algorithm_list.addItem("tnc")
        self.algorithm_list.addItem("trust-ncg")
        self.algorithm_list.addItem("dogleg")
        self.algorithm_list.addItem("slsqp")
        
        for alg in self.settings.algorithms:
            self.cur_algorithm_list.addItem(alg)

        self.add_algorithm = QPushButton('Add', self)
        self.add_algorithm.clicked.connect(self.__add_algr)
        self.remove_algorithm = QPushButton('Remove', self)
        self.remove_algorithm.clicked.connect(self.__remove_algr)
        algorithm_box.addWidget(self.algorithm_lbl1)
        algorithm_box.addWidget(self.cur_algorithm_list)
        algorithm_box.addWidget(self.add_algorithm)
        algorithm_box.addWidget(self.remove_algorithm)
        algorithm_box.addWidget(self.algorithm_list)
        
        model_box.addWidget(self.lbl1)
        model_box.addWidget(self.cb)
        model_box.addWidget(self.add_button)
        model_box.addWidget(self.add_show_folder)
        model_box.addWidget(self.add_show_help)
        
        
        x_data = parent.wks_wrapper.get_x()
        all_y_data = parent.wks_wrapper.get_y_data()
        self.settings.parameters = create_params(self.settings.model, x_data, all_y_data, parent.indexes, self.settings.min_peak_dist)
        
        params_box = QHBoxLayout()
        self.tableWidget = QTableWidget(self)
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setRowCount(len(self.settings.parameters))
        self.tableWidget.setHorizontalHeaderItem(0, QTableWidgetItem("name"));
        self.tableWidget.setHorizontalHeaderItem(1, QTableWidgetItem("value"));
        self.tableWidget.setHorizontalHeaderItem(2, QTableWidgetItem("enable(0 or 1"));
        self.tableWidget.setHorizontalHeaderItem(3, QTableWidgetItem("min"));
        self.tableWidget.setHorizontalHeaderItem(4, QTableWidgetItem("max"));
        i = 0
        for key, param in self.settings.parameters.items():
            self.tableWidget.setItem(i,0, QTableWidgetItem(key))
            self.tableWidget.setItem(i,1, QTableWidgetItem("{}".format(self.settings.parameters[key].value)))
            self.tableWidget.setItem(i,2, QTableWidgetItem("{}".format(self.settings.parameters[key].vary)))
            self.tableWidget.setItem(i,3, QTableWidgetItem("{}".format(self.settings.parameters[key].min)))
            self.tableWidget.setItem(i,4, QTableWidgetItem("{}".format(self.settings.parameters[key].max)))
            i = i + 1
        params_box.addWidget(self.tableWidget)

        # peak detection settings
        peak_detection_group = QGroupBox(self)
        peak_detection_group.setTitle('Peak detection settings')
        peak_detection_group_layout = QVBoxLayout()

        peak_dist_box = QHBoxLayout()
        self.lbl2 = QLabel('Min Peak distance', self)
        self.lbl2.setFixedHeight(20)
        self.lbl2.setFixedWidth(100)

        self.min_dist_edit = QLineEdit(self)
        self.min_dist_edit.resize(100, 40)
        self.onlyInt = QIntValidator()
        self.min_dist_edit.setValidator(self.onlyInt)
        self.min_dist_edit.setText("{}".format(self.settings.min_peak_dist))
        # self.cb.move(20, 10)
        peak_dist_box.addWidget(self.lbl2)
        peak_dist_box.addWidget(self.min_dist_edit)

        peak_ampl_box = QHBoxLayout()
        self.lbl_mpd = QLabel('<font size=3>Min Peak amplitude</font><font size=2><br>(Peak detector only)<br/></font>', self)
        self.lbl_mpd.setFixedHeight(30)
        self.lbl_mpd.setFixedWidth(100)

        self.min_ampl_edit = QLineEdit(self)
        self.min_ampl_edit.resize(100, 40)
        self.onlyInt = QIntValidator()
        self.min_ampl_edit.setValidator(self.onlyInt)
        self.min_ampl_edit.setText("{}".format(self.settings.min_amplitude))
        # self.cb.move(20, 10)
        peak_ampl_box.addWidget(self.lbl_mpd)
        peak_ampl_box.addWidget(self.min_ampl_edit)
        if self.settings.peak_function is PeakFunction.PEAK_UTILS:
            self.lbl_mpd.setEnabled(False)
            self.min_ampl_edit.setEnabled(False)

        peak_threshold_box = QHBoxLayout()
        self.lbl4 = QLabel('Threshold', self)
        self.lbl4.setFixedHeight(20)
        self.lbl4.setFixedWidth(100)

        self.min_threshold_edit = QLineEdit(self)
        self.min_threshold_edit.resize(100, 40)
        self.onlyDouble = QDoubleValidator()
        self.onlyDouble.setNotation(QDoubleValidator.StandardNotation)
        self.min_threshold_edit.setValidator(self.onlyDouble)
        self.min_threshold_edit.setText("{}".format(self.settings.threshold))

        peak_threshold_box.addWidget(self.lbl4)
        peak_threshold_box.addWidget(self.min_threshold_edit)

        peak_function_box = QHBoxLayout()
        self.lbl5 = QLabel('Peak function', self)
        self.lbl5.setFixedHeight(20)
        self.lbl5.setFixedWidth(100)

        self.peak_func_cb = QComboBox()
        self.peak_func_cb.currentIndexChanged.connect(self.__on_func_combobox_changed)
        self.peak_func_cb.addItem("Peak detector")
        self.peak_func_cb.addItem("Peak utils")
        self.current_func = settings.peak_function.value
        self.peak_func_cb.setCurrentIndex(self.current_func)

        peak_function_box.addWidget(self.lbl5)
        peak_function_box.addWidget(self.peak_func_cb)

        peak_detection_group_layout.addLayout(peak_dist_box)
        peak_detection_group_layout.addLayout(peak_ampl_box)
        peak_detection_group_layout.addLayout(peak_threshold_box)
        peak_detection_group_layout.addLayout(peak_function_box)

        peak_detection_group.setLayout(peak_detection_group_layout)

        # Animation settings

        animation_group = QGroupBox(self)
        animation_group.setTitle('Animation settings')

        animation_group_layout = QHBoxLayout()
        self.lbl_interval = QLabel('Animation interval(ms)', self)
        self.lbl_interval.setFixedHeight(20)
        self.lbl_interval.setFixedWidth(100)

        self.interval_edit = QLineEdit(self)
        self.interval_edit.resize(100, 40)
        self.interval_edit.setValidator(self.onlyInt)
        self.interval_edit.setText("{}".format(self.settings.animation_interval))

        animation_group_layout.addWidget(self.lbl_interval)
        animation_group_layout.addWidget(self.interval_edit)
        animation_group.setLayout(animation_group_layout)

        # buttons
        button_box = QHBoxLayout()
        self.ok_button = QPushButton('Save', self)
        self.cancel_button = QPushButton('Cancel', self)
        self.ok_button.clicked.connect(self.__save)
        self.cancel_button.clicked.connect(self.__cancel)
        button_box.addWidget(self.ok_button)
        button_box.addWidget(self.cancel_button)

        # main layout
        layout = QVBoxLayout()
        layout.addLayout(model_box)
        layout.addLayout(algorithm_box)
        layout.addLayout(params_box)

        layout.addWidget(peak_detection_group)
        layout.addWidget(animation_group)
        layout.addLayout(button_box)

        self.setWindowTitle("Settings")
        self.setLayout(layout)
        
    def __add_algr(self):
        self.cur_algorithm_list.addItem(self.algorithm_list.currentItem().text())
        
    def __remove_algr(self):
        listItems=self.cur_algorithm_list.selectedItems()
        if not listItems: return        
        for item in listItems:
            self.cur_algorithm_list.takeItem(self.cur_algorithm_list.row(item))
		
    def __open_help(self):
        url = "file://" + PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "PyFit\doc\Built-in Fitting Models in the models module.htm"
        webbrowser.open(url,new=2)

    def __add(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
        #dstdir = os.path.join(custom_path, os.path.dirname(file_name))
        if file_name:
            shutil.copy(file_name, custom_path)
            file_name = ntpath.basename(file_name)
            import_name = os.path.splitext(file_name)[0]
            module = importlib.import_module(import_name)
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj):
                    gl_models_dictionary[obj.__name__] = obj

            self.cb.clear()
            for model_name in list(gl_models_dictionary):
                self.cb.addItem(model_name)

    def __show_folder(self):
        subprocess.Popen(r'explorer /start, ' + PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "PyFit\scripts\CustomModels")

    def __on_combobox_changed(self, new_index):
        self.current_index = new_index
        x_data = self.parent.wks_wrapper.get_x()
        all_y_data = self.parent.wks_wrapper.get_y_data()
        self.settings.parameters = create_params(str(self.cb.currentText()), x_data, all_y_data, self.parent.indexes, self.settings.min_peak_dist)
        i = 0
        for key, param in self.settings.parameters.items():
            try:
                self.tableWidget.setItem(i,0, QTableWidgetItem(key))
                self.tableWidget.setItem(i,1, QTableWidgetItem("{}".format(self.settings.parameters[key].value)))
                self.tableWidget.setItem(i,2, QTableWidgetItem("{}".format(self.settings.parameters[key].vary)))
                self.tableWidget.setItem(i,3, QTableWidgetItem("{}".format(self.settings.parameters[key].min)))
                self.tableWidget.setItem(i,4, QTableWidgetItem("{}".format(self.settings.parameters[key].max)))
            except Exception as e:
                print(type(e))
            i = i + 1

    def __on_func_combobox_changed(self, new_index):
        self.current_func = new_index
        if self.current_func is PeakFunction.PEAK_DETECTOR.value:
            self.lbl_mpd.setEnabled(True)
            self.min_ampl_edit.setEnabled(True)
        else:
            self.lbl_mpd.setEnabled(False)
            self.min_ampl_edit.setEnabled(False)

    def __save(self):
        self.settings.model = str(self.cb.currentText())#Model(self.current_index)

        prev_min_peak_dist = self.settings.min_peak_dist
        prev_min_amplitude = self.settings.min_amplitude
        prev_threshold = self.settings.threshold
        prev_peak_function = self.settings.peak_function

        self.settings.min_peak_dist = int(self.min_dist_edit.text())
        self.settings.min_amplitude = int(self.min_ampl_edit.text())
        self.settings.threshold = float(self.min_threshold_edit.text().replace(",", "."))
        self.settings.peak_function = PeakFunction(self.current_func)

        self.settings.animation_interval = int(self.interval_edit.text())

        if prev_min_peak_dist is not self.settings.min_peak_dist or \
                prev_min_amplitude is not self.settings.min_amplitude or \
                prev_threshold is not self.settings.threshold or \
                prev_peak_function is not self.settings.peak_function:
            self.peak_settings_changed.emit()
            
        items = []
        for index in range(self.cur_algorithm_list.count()):
            items.append(self.cur_algorithm_list.item(index).text())
        self.settings.algorithms = items
          
        i = 0
        for key, param in self.settings.parameters.items():
            try:
                param_name = self.tableWidget.item(i,0).text()
                min = float(self.tableWidget.item(i,3).text())
                max = float(self.tableWidget.item(i,4).text())
                self.settings.parameters[param_name].set(value=float(self.tableWidget.item(i,1).text()),
                                                         vary=str2bool(self.tableWidget.item(i,2).text()), min=min, max=max)
                '''self.settings.parameters[param_name].value = float(self.tableWidget.item(i,1).text())
                self.settings.parameters[param_name].vary = str2bool(self.tableWidget.item(i,2).text())
                if self.tableWidget.item(i,3).text().isdigit():
                    self.settings.parameters[param_name].min = float(self.tableWidget.item(i,3).text())
                if self.tableWidget.item(i,4).text().isdigit():
                    self.settings.parameters[param_name].max = float(self.tableWidget.item(i,4).text())'''
            except Exception as e:
                print(type(e))
            i = i + 1
        self.accept()

    def __cancel(self):
        self.accept()
