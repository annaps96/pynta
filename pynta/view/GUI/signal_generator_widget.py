import os

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton

from pynta.view.GUI.histogram_widget import HistogramWidget
from pynta.view.GUI.tracks_widget import TracksWidget
from pynta.view.GUI.graph_monitor_widget import GraphMonitorWidget
from pyqtgraph.dockarea import DockArea, Dock

from pynta.model.daqs.signal_generator.base_signal_generator import BaseSignalGenerator, Waveform
#todo: support different waveform, standardize initialization.
#
class SignalGeneratorWidget(QWidget):
    #init takes a parent argument which has to be another QWidget or None, and the model
    def __init__(self, model : BaseSignalGenerator, parent=None):
        # set the base variables
        self.model = model
        # call the base QWidget class initializer
        super().__init__(parent)
        #load the corresponding UI file.
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'designer', 'signal_generator.ui'), self)
        (min_f, max_f) = model.supported_frequencies().get_range()
        self.FrequencySpinbox.setRange(min_f, max_f)
        self.FrequencySpinbox.setValue(0.5*(min_f+max_f))
        (min_a, max_a) = model.supported_amplitudes().get_range()
        self.AmplitudeSpinbox.setRange(min_a, max_a)
        self.AmplitudeSpinbox.setValue(0.5*(min_a+max_a))
        (min_o, max_o) = model.supported_offsets().get_range()
        self.OffsetSpinbox.setRange(min_o, max_o)
        self.OffsetSpinbox.setValue(0.5*(min_o+max_o))
        for waveform in model.supported_waveforms():
            self.WaveformSelector.addItem(waveform.name)
        print("Supports live updates?", model.supports_live_updates())
        self.flush_settings()
        self.connectSignals()

    def connectSignals(self):
        self.FrequencySpinbox.valueChanged.connect(self.set_frequency)
        self.DutyCycleSpinbox.valueChanged.connect(self.set_duty_cycle)
        self.AmplitudeSpinbox.valueChanged.connect(self.set_amplitude)
        self.OffsetSpinbox.valueChanged.connect(self.set_offset)
        self.WaveformSelector.currentTextChanged.connect(self.set_waveform)
    
    def set_frequency(self):
        self.model.set_frequency(self.FrequencySpinbox.value())
    
    def set_duty_cycle(self):
        self.model.set_duty_cycle(self.DutyCycleSpinbox.value())
    
    def set_amplitude(self):
        self.model.set_amplitude(self.AmplitudeSpinbox.value())

    def set_offset(self):
        self.model.set_offset(self.OffsetSpinbox.value())
    
    def set_waveform(self):
        self.model.set_waveform(Waveform[self.WaveformSelector.currentText()])

    def flush_settings(self):
        self.set_waveform()
        self.set_frequency()
        self.set_duty_cycle()
        self.set_amplitude()
        self.set_offset()
        #self.model.flush()
