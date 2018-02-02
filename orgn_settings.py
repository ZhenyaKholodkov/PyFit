import sys
import PyOrigin
pck_path = PyOrigin.GetPath(PyOrigin.PATHTYPE_USER) + "FittingProject\site-packages"
sys.path.append(pck_path)
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QApplication, QSlider, QHBoxLayout, QVBoxLayout, QPushButton, QProgressBar, \
    QComboBox, QAction, QMenuBar, QLabel, QLineEdit, QPushButton, QMessageBox, QGroupBox, QGridLayout


class PeakFunction(Enum):
    PEAK_DETECTOR = 0
    PEAK_UTILS = 1


class Model(Enum):
    GAUSSIAN = 0
    LORENTZ = 1


class Setting:
    def __init__(self):
        self.model = Model.GAUSSIAN
        self.min_peak_dist = 10
        self.min_amplitude = 500
        self.threshold = 0.05
        self.peak_function = PeakFunction.PEAK_UTILS
        self.animation_interval = 100

    def set_model(self, model):
        self.model = model


class SettingsDialog(QtWidgets.QDialog):
    peak_settings_changed = pyqtSignal(name="PeakSettingsChanged")

    def __init__(self, settings, parent=None):
        super(SettingsDialog, self).__init__(parent)

        self.settings = settings

        # fitting model settings
        model_box = QHBoxLayout()
        self.lbl1 = QLabel('Fitting function', self)
        self.lbl1.setFixedHeight(20)
        self.lbl1.setFixedWidth(100)
        self.lbl1.resize(100, 40)

        self.cb = QComboBox()
        self.cb.currentIndexChanged.connect(self.__on_combobox_changed)
        self.cb.addItem("Gaussian's Model")
        self.cb.addItem("Lorentz's Model")
        self.current_index = settings.model.value
        self.cb.setCurrentIndex(self.current_index)
        model_box.addWidget(self.lbl1)
        model_box.addWidget(self.cb)

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

        layout.addWidget(peak_detection_group)
        layout.addWidget(animation_group)
        layout.addLayout(button_box)

        self.setWindowTitle("Settings")
        self.setLayout(layout)

    def __on_combobox_changed(self, new_index):
        self.current_index = new_index

    def __on_func_combobox_changed(self, new_index):
        self.current_func = new_index
        if self.current_func is PeakFunction.PEAK_DETECTOR.value:
            self.lbl_mpd.setEnabled(True)
            self.min_ampl_edit.setEnabled(True)
        else:
            self.lbl_mpd.setEnabled(False)
            self.min_ampl_edit.setEnabled(False)

    def __save(self):
        self.settings.model = Model(self.current_index)

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
        self.accept()

    def __cancel(self):
        self.accept()
