from .base_signal_generator import BaseSignalGenerator, Waveform, SupportedValues


class DummySignalGenerator(BaseSignalGenerator):
    def __init__(self) -> None:
        super().__init__()

    def supported_waveforms(self) -> 'set[Waveform]':
        return {Waveform.Square}

    def supported_frequencies(self) -> SupportedValues:
        return SupportedValues.from_range(1, 50)

    def supported_amplitudes(self) -> SupportedValues:
        return SupportedValues.from_range(0, 5)

    def supported_offsets(self) -> SupportedValues:
        return SupportedValues.from_range(0, 0)

    def set_waveform(self, waveform: Waveform):
        print("setting waveform to ", waveform)

    def set_frequency(self, frequency):
        print("setting frequency to {}".format(frequency))

    def set_amplitude(self, amplitude: float):
        print("setting amplitude to ", amplitude)

    def set_offset(self, offset: float):
        print("setting offset to ", offset)

    def set_duty_cycle(self, duty_cycle: float):
        print("setting duty_cycle to ", duty_cycle)

    def supports_live_updates(self) -> bool:
        return True
