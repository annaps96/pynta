import os

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton
import numpy as np

from pyqtgraph.dockarea import DockArea, Dock
#todo: abstract into generic model
from pynta.controller.devices.NIDAQ.ni_usb_6216 import NiUsb6216 as Adc

class AdcCaptureWidget(QWidget):
    #init takes a parent argument which has to be another QWidget or None, and the model
    def __init__(self, model : Adc, parent=None):
        # set the base variables
        self.model = model
        # call the base QWidget class initializer
        super().__init__(parent)
        #load the corresponding UI file.
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'designer', 'adc.ui'), self)
        #(min_f, max_f) = model.supported_frequencies().get_range()
        self.FrequencySpinbox.setRange(1e2, 5e3)
        self.FrequencySpinbox.setValue(1e3)
        #(min_a, max_a) = model.supported_amplitudes().get_range()
        self.PointsSpinbox.setRange(100, 10000)
        self.PointsSpinbox.setValue(2000)
        self.curve = self.PlotView.plot(np.zeros(1000))
        self.connectSignals()

    def connectSignals(self):
        self.UpdateButton.clicked.connect(self.flush_settings)
    
    def flush_settings(self):
        def fnc(data):
            print("updating curve")
            self.curve.setData(data)
            #self.plot_widget.render()
            return 0
        self.model.capture_stream(self.FrequencySpinbox.value(), self.PointsSpinbox.value(), fnc)
