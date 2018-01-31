
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QApplication, QSlider, QHBoxLayout, QVBoxLayout, QPushButton, QProgressBar, \
    QComboBox, QAction, QMenuBar, QLabel, QLineEdit, QPushButton, QMessageBox


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

    def set_model(self, model):
        self.model = model


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, settings, parent=None):
        super(SettingsDialog, self).__init__(parent)

        self.settings = settings

        model_box = QHBoxLayout()
        self.lbl1 = QLabel('Model', self)
        self.lbl1.resize(100, 40)

        self.cb = QComboBox()
        self.cb.currentIndexChanged.connect(self.on_combobox_changed)
        self.cb.addItem("Gaussian's Model")
        self.cb.addItem("Lorentz's Model")
        self.current_index = settings.model.value
        self.cb.setCurrentIndex(self.current_index)
        # self.cb.move(20, 10)
        model_box.addWidget(self.lbl1)
        model_box.addWidget(self.cb)

        peak_dist_box = QHBoxLayout()
        self.lbl2 = QLabel('Min Peak distance', self)
        self.lbl2.resize(100, 40)

        self.min_dist_edit = QLineEdit(self)
        self.min_dist_edit.resize(100, 40)
        self.onlyInt = QIntValidator()
        self.min_dist_edit.setValidator(self.onlyInt)
        self.min_dist_edit.setText("{}".format(self.settings.min_peak_dist))
        # self.cb.move(20, 10)
        peak_dist_box.addWidget(self.lbl2)
        peak_dist_box.addWidget(self.min_dist_edit)

        peak_ampl_box = QHBoxLayout()
        self.lbl3 = QLabel('Min Peak amplitude', self)
        self.lbl3.resize(100, 40)

        self.min_ampl_edit = QLineEdit(self)
        self.min_ampl_edit.resize(100, 40)
        self.onlyInt = QIntValidator()
        self.min_ampl_edit.setValidator(self.onlyInt)
        self.min_ampl_edit.setText("{}".format(self.settings.min_amplitude))
        # self.cb.move(20, 10)
        peak_ampl_box.addWidget(self.lbl3)
        peak_ampl_box.addWidget(self.min_ampl_edit)

        peak_threshold_box = QHBoxLayout()
        self.lbl4 = QLabel('Threshold', self)
        self.lbl4.resize(100, 40)

        self.min_threshold_edit = QLineEdit(self)
        self.min_threshold_edit.resize(100, 40)
        self.onlyDouble = QDoubleValidator()
        self.onlyDouble.setNotation(QDoubleValidator.StandardNotation)
        self.min_threshold_edit.setValidator(self.onlyDouble)
        self.min_threshold_edit.setText("{}".format(self.settings.threshold))
        # self.cb.move(20, 10)
        peak_threshold_box.addWidget(self.lbl4)
        peak_threshold_box.addWidget(self.min_threshold_edit)

        peak_function_box = QHBoxLayout()
        self.lbl5 = QLabel('Peak function', self)
        self.lbl5.resize(100, 40)

        self.peak_func_cb = QComboBox()
        self.peak_func_cb.currentIndexChanged.connect(self.on_func_combobox_changed)
        self.peak_func_cb.addItem("Peak detector")
        self.peak_func_cb.addItem("Peak utils")
        self.current_func = settings.peak_function.value
        self.peak_func_cb.setCurrentIndex(self.current_func)

        # self.cb.move(20, 10)
        peak_function_box.addWidget(self.lbl5)
        peak_function_box.addWidget(self.peak_func_cb)

        button_box = QHBoxLayout()
        self.ok_button = QPushButton('Save', self)
        self.cancel_button = QPushButton('Cancel', self)
        self.ok_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.cancel)
        button_box.addWidget(self.ok_button)
        button_box.addWidget(self.cancel_button)

        layout = QVBoxLayout()
        layout.addLayout(model_box)
        layout.addLayout(peak_dist_box)
        layout.addLayout(peak_ampl_box)
        layout.addLayout(peak_threshold_box)
        layout.addLayout(peak_function_box)
        layout.addLayout(button_box)
        self.setLayout(layout)

    def on_combobox_changed(self, new_index):
        self.current_index = new_index

    def on_func_combobox_changed(self, new_index):
        self.current_func = new_index

    def save(self):
        self.settings.model = Model(self.current_index)
        self.settings.min_peak_dist = int(self.min_dist_edit.text())
        self.settings.min_amplitude = int(self.min_ampl_edit.text())
        self.settings.threshold = float(self.min_threshold_edit.text().replace(",", "."))
        self.settings.peak_function = PeakFunction(self.current_func)
        self.accept()

    def cancel(self):
        self.accept()
