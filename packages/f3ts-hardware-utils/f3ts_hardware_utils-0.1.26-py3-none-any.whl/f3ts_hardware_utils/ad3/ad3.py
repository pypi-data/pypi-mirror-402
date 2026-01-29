"""

Reference: https://github.com/Digilent/WaveForms-SDK-Getting-Started-PY
"""

import os

import matplotlib.pyplot as plt  # needed for plotting

from .WF_SDK import (  # import instruments
    device,
    dmm,
    logic,
    scope,
    static,
    supplies,
    wavegen,
)


class AD3:
    GPIO_INPUT = 0
    GPIO_OUTPUT = 1

    def __init__(self, default_supply_voltage=0, log_dir="data_plots", save_plots=True):
        self.device_data = device.open()
        self.log_dir = log_dir
        self.save_plots = save_plots
        self.default_supply_voltage = default_supply_voltage

        if not os.path.isdir(log_dir):
            os.mkdir(log_dir)

        # GPIO Configuration:
        # set all pins as input
        for index in range(16):
            static.set_mode(self.device_data, index, self.GPIO_INPUT)

        # DMM Configuration
        dmm.open(self.device_data)

    def set_supply(self, state, voltage=None):
        supplies_data = supplies.data()

        # start the positive supply
        supplies_data.master_state = state
        supplies_data.positive_state = state
        if voltage:
            self.default_supply_voltage = voltage
            supplies_data.positive_voltage = self.default_supply_voltage

        supplies.switch(self.device_data, supplies_data)

    def set_gpio_mode(self, pin, mode):
        static.set_mode(self.device_data, pin, mode)

    def set_gpio_state(self, pin, state):
        static.set_state(self.device_data, pin, state)

    def read_gpio_state(self, pin):
        return static.get_state(self.device_data, pin)

    def setup_scope(self, sampling_frequency=20e06, offset=0, amplitude_range=5):
        """
        initialize the oscilloscope

        parameters:
                    - sampling frequency in Hz, default is 20MHz
                    - offset voltage in Volts, default is 0V
                    - amplitude range in Volts, default is ±5V
        """
        # initialize the scope
        scope.open(
            self.device_data,
            sampling_frequency=sampling_frequency,
            offset=offset,
            amplitude_range=amplitude_range,
        )

    def scope_measure(self, channel, num_samples: int = 1):
        """
        measure a voltage
        parameters: - the selected oscilloscope channel (1-2, or 1-4)

        returns:    - the measured voltage in Volts
        """
        vals = []
        for x in range(num_samples):
            vals += [scope.measure(self.device_data, channel)]

        return scope.measure(self.device_data, channel)

    def setup_scope_trigger(
        self,
        enable=True,
        source=scope.trigger_source.analog,
        channel=1,
        timeout=0,
        edge_rising=True,
        level=0,
    ):
        """
        parameters:
                    - enable / disable triggering with True/False
                    - trigger source - possible: none, analog, digital, external[1-4]
                    - trigger channel - possible options: 1-4 for analog, or 0-15 for digital
                    - auto trigger timeout in seconds, default is 0
                    - trigger edge rising - True means rising, False means falling, default is rising
                    - trigger level in Volts, default is 0V
        """
        # set up triggering on scope channel
        scope.trigger(
            self.device_data,
            enable=enable,
            source=source,
            channel=channel,
            timeout=timeout,
            edge_rising=edge_rising,
            level=level,
        )

    def read_scope(self, channel, filename=None):
        # record data with the scopeon channel
        buffer = scope.record(self.device_data, channel=channel)

        # limit displayed data size
        length = len(buffer)
        if length > 10000:
            length = 10000
        buffer = buffer[0:length]

        # generate buffer for time moments
        times = []
        for index in range(len(buffer)):
            times.append(index / scope.data.sampling_frequency)

        # plot
        if self.save_plots and filename:
            plt.plot(times, buffer)
            plt.xlabel("time [S]")
            plt.ylabel("voltage [V]")
            plt.savefig(os.path.join(self.log_dir, filename))
            plt.clf()

        return times, buffer

    def close_scope(self):
        scope.close(self.device_data)

    def generate_custom_wave(
        self,
        channel,
        offset,
        frequency=1e03,
        amplitude=1,
        symmetry=50,
        wait=0,
        run_time=0,
        repeat=0,
        data=[],
    ):
        """
        parameters:
                    - the selected wavegen channel (1-2)
                    - offset voltage in Volts
                    - frequency in Hz, default is 1KHz
                    - amplitude in Volts, default is 1V
                    - signal symmetry in percentage, default is 50%
                    - wait time in seconds, default is 0s
                    - run time in seconds, default is infinite (0)
                    - repeat count, default is infinite (0)
                    - data - list of voltages, used only if function=custom, default is empty
        """
        wavegen.generate(
            self.device_data,
            channel=channel,
            function=wavegen.function.custom,
            offset=offset,
            frequency=frequency,
            amplitude=amplitude,
            symmetry=symmetry,
            wait=wait,
            run_time=run_time,
            repeat=repeat,
            data=data,
        )

    def stop_wavegen(self, channel):
        wavegen.disable(self.device_data, channel=channel)

    def setup_logic(self, sampling_frequency=100e06, buffer_size=0):
        """
        initialize the logic analyzer

        parameters:
                    - sampling frequency in Hz, default is 100MHz
                    - buffer size, default is 0 (maximum)
        """
        # initialize the logic analyzer
        logic.open(
            self.device_data,
            sampling_frequency=sampling_frequency,
            buffer_size=buffer_size,
        )

    def setup_logic_trigger(
        self,
        enable,
        channel,
        position=0,
        timeout=0,
        rising_edge=True,
        length_min=0,
        length_max=20,
        count=0,
    ):
        """
        set up triggering

        parameters:
                    - enable - True or False to enable, or disable triggering
                    - channel - the selected DIO line number to use as trigger source
                    - buffer size, the default is 4096
                    - position - prefill size, the default is 0
                    - timeout - auto trigger time, the default is 0
                    - rising_edge - set True for rising edge, False for falling edge, the default is rising edge
                    - length_min - trigger sequence minimum time in seconds, the default is 0
                    - length_max - trigger sequence maximum time in seconds, the default is 20
                    - count - instance count, the default is 0 (immediate)
        """
        # initialize the logic analyzer
        logic.trigger(
            self.device_data,
            enable,
            channel,
            position=position,
            timeout=timeout,
            rising_edge=rising_edge,
            length_min=length_min,
            length_max=length_max,
            count=count,
        )

    def read_all_logic(self, channels, filename=None):
        # record data with the scopeon channel
        results = logic.record_multiple(self.device_data, channels=channels)

        for channel in results:
            buffer = results[channel]
            length = len(buffer)

            # generate buffer for time moments
            times = []
            for index in range(length):
                times.append(
                    index * 1e03 / logic.data.sampling_frequency
                )  # convert time to ms

            # plot
            if self.save_plots and filename:
                plt.plot(times, buffer)
                plt.xlabel("time [ms]")
                plt.ylabel("logic value")
                plt.yticks([0, 1])
                plt.savefig(os.path.join(self.log_dir, f"{channel}_{filename}"))
                plt.clf()

        return times, results

    def close_logic(self):
        logic.close(self.device_data)

    def read_dmm(self, mode, meas_range=0, high_impedance=False):
        """
        measure a voltage/current/resistance/continuity/temperature

        parameters: - mode: dmm.mode.ac_voltage/dc_voltage/ac_high_current/dc_high_current/ac_low_current/dc_low_current/resistance/continuity/diode/temperature
                    - meas_range: voltage/current/resistance/temperature range, 0 means auto, default is auto
                    - high_impedance: input impedance for DC voltage measurement, False means 10MΩ, True means 10GΩ, default is 10MΩ

        returns:    - the measured value in V/A/Ω/°C, or None on error
        """
        return dmm.measure(self.device_data, mode, meas_range, high_impedance)

    def close(self):
        # stop the static I/O
        for gpio in range(16):
            self.set_gpio_mode(gpio, self.GPIO_INPUT)

        static.close(self.device_data)

        # reset the scopes
        self.close_logic()
        self.close_scope()

        # reset the wavegen
        self.stop_wavegen(1)
        self.stop_wavegen(2)
        wavegen.close(self.device_data)

        # stop and reset the power supplies
        self.set_supply(False)
        supplies.close(self.device_data)

        """-----------------------------------"""

        # close the connection
        device.close(self.device_data)
