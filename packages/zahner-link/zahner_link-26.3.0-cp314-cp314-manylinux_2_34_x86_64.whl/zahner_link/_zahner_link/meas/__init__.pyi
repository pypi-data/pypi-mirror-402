import collections.abc
import typing
import zahner_link._zahner_link
from . import stop as stop
from typing import overload

class CvJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: CvParametersPy
    def __init__(self, start_value: typing.SupportsFloat, first_vertex: typing.SupportsFloat, second_vertex: typing.SupportsFloat, end_value: typing.SupportsFloat, scan_rate: typing.SupportsFloat, output_data_rate: typing.SupportsFloat, num_cycles: typing.SupportsFloat, autorange: bool, current_range: typing.SupportsFloat, turn_limit_check: bool, upper_turn_boundary: typing.SupportsFloat, lower_turn_boundary: typing.SupportsFloat, step_height: typing.SupportsFloat, ir_drop: typing.SupportsFloat, meta_data: dict = ..., stop_conditions: collections.abc.Sequence[AbstractStopCondition] = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.CvJob, start_value: typing.SupportsFloat, first_vertex: typing.SupportsFloat, second_vertex: typing.SupportsFloat, end_value: typing.SupportsFloat, scan_rate: typing.SupportsFloat, output_data_rate: typing.SupportsFloat, num_cycles: typing.SupportsFloat, autorange: bool, current_range: typing.SupportsFloat, turn_limit_check: bool, upper_turn_boundary: typing.SupportsFloat, lower_turn_boundary: typing.SupportsFloat, step_height: typing.SupportsFloat, ir_drop: typing.SupportsFloat, meta_data: dict = {}, stop_conditions: collections.abc.Sequence[AbstractStopCondition] = []) -> None


            Cyclic Voltammetry job

            This cyclic voltammetry job can be carried out potentiostatically or galvanostatically.
            The description of the parameters is for the potentiostatic standard case.
            If the potentiostat was previously switched on galvanostatically,
            then the CV is also executed galvanostatically and the potential parameters become currents and the current parameters become voltages.
            For example, `start_value` becomes a current and `upper_turn_boundary` is a voltage.

            :param start_value: starting potential
            :param first_vertex: first reversing potential
            :param second_vertex: second reversing potential
            :param end_value: ending potential
            :param scan_rate: magnitude of the CV scaning slew rate :math:`\\frac{∆E}{∆t}`
            :param output_data_rate: rate at which data is output
            :param num_cycles:
                * number of full CV cycles (scan from 1st potential to 2nd potential and back to the 1st potential)
                * half cycles can be performed with .5
            :param autorange:
                * whether automatic switching should be used
                * for maximum measurement accuracy, autoranging should be switched off and current_range should be selected to match the object current
            :param current_range: optional selection of the current range that matches the object as the maximum absolute current if autoranging is disabled
            :param turn_limit_check: whether to perform turn limit checks
            :param upper_turn_boundary: upper reversal current limit at which the scan is reversed
            :param lower_turn_boundary: lower reversal current limit at which the scan is reversed
            :param step_height:
                * height of the steps
                * 0 uses the smallest step size
            :param ir_drop:
                * ohmic value for iRdrop compensation
                * at 0 disabled
            :param meta_data: dict[str, str] with user-defined key-value pairs
            :param stop_conditions: list of stop condition objects from :ref:`python_stopconditions`

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "cv",
                      "parameters": {
                        "start_value": 0.0,
                        "first_vertex": 1.0,
                        "second_vertex": -1.0,
                        "end_value": 0.0,
                        "scan_rate": 0.1,
                        "output_data_rate": 25.0,
                        "num_cycles": 2.5,
                        "autorange": true,
                        "current_range": 0.01,
                        "turn_limit_check": false,
                        "upper_turn_boundary": 0.01,
                        "lower_turn_boundary": -0.01,
                        "step_height": 0.0,
                        "ir_drop": 0.0
                      }
                    },
                    "request_id": "cv-job-uuid-example"
                  }

        '''

class CvParametersPy:
    autorange: bool
    current_range: float
    end_value: float
    first_vertex: float
    ir_drop: float
    lower_turn_boundary: float
    num_cycles: float
    output_data_rate: float
    scan_rate: float
    second_vertex: float
    start_value: float
    step_height: float
    turn_limit_check: bool
    upper_turn_boundary: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class DpvJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: DpvParametersPy
    def __init__(self, start_value: typing.SupportsFloat, step_value: typing.SupportsFloat, pulse_value: typing.SupportsFloat, end_value: typing.SupportsFloat, step_time: typing.SupportsFloat, pulse_time: typing.SupportsFloat, invert_pulse: bool, output_data_rate: typing.SupportsFloat, current_range: typing.SupportsFloat, meta_data: dict = ..., stop_conditions: collections.abc.Sequence[AbstractStopCondition] = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.DpvJob, start_value: typing.SupportsFloat, step_value: typing.SupportsFloat, pulse_value: typing.SupportsFloat, end_value: typing.SupportsFloat, step_time: typing.SupportsFloat, pulse_time: typing.SupportsFloat, invert_pulse: bool, output_data_rate: typing.SupportsFloat, current_range: typing.SupportsFloat, meta_data: dict = {}, stop_conditions: collections.abc.Sequence[AbstractStopCondition] = []) -> None


            Differential Pulse Voltammetry job

            :param start_value: starting DC value
            :param step_value: value of each step for the staircase function
            :param pulse_value: absolute value of each pulse added to the staircase potential
            :param end_value: maximum DC value of the last step and pulse
            :param step_time:
                * duration of each step of the staircase
                * should be at least twice as long as pulse duration
            :param pulse_time: duration of each pulse
            :param invert_pulse: invert pulse direction
            :param output_data_rate: rate at which data is output
            :param current_range: selection of the current range that matches the object as the maximum absolute current
            :param meta_data: dict[str, str] with user-defined key-value pairs
            :param stop_conditions: list of stop condition objects from :ref:`python_stopconditions`

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "dpv",
                      "parameters": {
                        "start_value": 0.0,
                        "step_value": 0.01,
                        "pulse_value": 0.05,
                        "end_value": 1.5,
                        "step_time": 0.5,
                        "pulse_time": 0.1,
                        "invert_pulse": false,
                        "output_data_rate": 200.0,
                        "current_range": 0.1
                      }
                    },
                    "request_id": "dpv-job-uuid-example"
                  }

        '''

class DpvParametersPy:
    current_range: float
    end_value: float
    invert_pulse: bool
    output_data_rate: float
    pulse_time: float
    pulse_value: float
    start_value: float
    step_time: float
    step_value: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class EisFrequencyTableJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: EisParametersFrequencyTablePy
    @overload
    def __init__(self, bias: typing.SupportsFloat, spectrum: collections.abc.Sequence[EisParametersFrequencyTableEntry], meta_data: dict = ...) -> None:
        '''__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.meas.EisFrequencyTableJob, bias: typing.SupportsFloat, spectrum: collections.abc.Sequence[zahner_link._zahner_link.meas.EisParametersFrequencyTableEntry], meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param bias: DC bias for defining the operating point of the object
            :param spectrum: spectrum measurement settings

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "eis_table",
                      "parameters": {
                        "bias": 0.0,
                        "frequency_range": {
                          "type": "table",
                          "spectrum": [
                            {
                              "frequency": 100.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            },
                            {
                              "frequency": 200.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            },
                            {
                              "frequency": 500.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            }
                          ]
                        }
                      }
                    },
                    "request_id": "00936e81-a128-4526-8a9e-5d5bdbf82fb9"
                  }


        2. __init__(self: zahner_link._zahner_link.meas.EisFrequencyTableJob, table: zahner_link._zahner_link.meas.EisParametersFrequencyTable, meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param table: spectrum measurement settings


        3. __init__(self: zahner_link._zahner_link.meas.EisFrequencyTableJob, table: dict, meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param table: a dictionary with values like the following example

            .. code-block:: python

                job = EisFrequencyTableJob(
                    {
                        "bias": 0.0,
                        "spectrum": [
                            {
                                "frequency": 10,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                            {
                                "frequency": 100,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                            {
                                "frequency": 1000,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                        ],
                    }
                )

            Or a simplified, shorter notation if, for example, only the frequency in the list needs to be adjusted.

            .. code-block:: python

                freqs_to_measure = [10, 100, 1000]
                job = EisFrequencyTableJob(
                    {
                        "bias": 0.0,
                        "spectrum": [
                            {
                                "frequency": freq,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            }
                            for freq in freqs_to_measure
                        ],
                    }
                )

        '''
    @overload
    def __init__(self, table: EisParametersFrequencyTable, meta_data: dict = ...) -> None:
        '''__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.meas.EisFrequencyTableJob, bias: typing.SupportsFloat, spectrum: collections.abc.Sequence[zahner_link._zahner_link.meas.EisParametersFrequencyTableEntry], meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param bias: DC bias for defining the operating point of the object
            :param spectrum: spectrum measurement settings

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "eis_table",
                      "parameters": {
                        "bias": 0.0,
                        "frequency_range": {
                          "type": "table",
                          "spectrum": [
                            {
                              "frequency": 100.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            },
                            {
                              "frequency": 200.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            },
                            {
                              "frequency": 500.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            }
                          ]
                        }
                      }
                    },
                    "request_id": "00936e81-a128-4526-8a9e-5d5bdbf82fb9"
                  }


        2. __init__(self: zahner_link._zahner_link.meas.EisFrequencyTableJob, table: zahner_link._zahner_link.meas.EisParametersFrequencyTable, meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param table: spectrum measurement settings


        3. __init__(self: zahner_link._zahner_link.meas.EisFrequencyTableJob, table: dict, meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param table: a dictionary with values like the following example

            .. code-block:: python

                job = EisFrequencyTableJob(
                    {
                        "bias": 0.0,
                        "spectrum": [
                            {
                                "frequency": 10,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                            {
                                "frequency": 100,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                            {
                                "frequency": 1000,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                        ],
                    }
                )

            Or a simplified, shorter notation if, for example, only the frequency in the list needs to be adjusted.

            .. code-block:: python

                freqs_to_measure = [10, 100, 1000]
                job = EisFrequencyTableJob(
                    {
                        "bias": 0.0,
                        "spectrum": [
                            {
                                "frequency": freq,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            }
                            for freq in freqs_to_measure
                        ],
                    }
                )

        '''
    @overload
    def __init__(self, table: dict, meta_data: dict = ...) -> None:
        '''__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.meas.EisFrequencyTableJob, bias: typing.SupportsFloat, spectrum: collections.abc.Sequence[zahner_link._zahner_link.meas.EisParametersFrequencyTableEntry], meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param bias: DC bias for defining the operating point of the object
            :param spectrum: spectrum measurement settings

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "eis_table",
                      "parameters": {
                        "bias": 0.0,
                        "frequency_range": {
                          "type": "table",
                          "spectrum": [
                            {
                              "frequency": 100.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            },
                            {
                              "frequency": 200.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            },
                            {
                              "frequency": 500.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            }
                          ]
                        }
                      }
                    },
                    "request_id": "00936e81-a128-4526-8a9e-5d5bdbf82fb9"
                  }


        2. __init__(self: zahner_link._zahner_link.meas.EisFrequencyTableJob, table: zahner_link._zahner_link.meas.EisParametersFrequencyTable, meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param table: spectrum measurement settings


        3. __init__(self: zahner_link._zahner_link.meas.EisFrequencyTableJob, table: dict, meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param table: a dictionary with values like the following example

            .. code-block:: python

                job = EisFrequencyTableJob(
                    {
                        "bias": 0.0,
                        "spectrum": [
                            {
                                "frequency": 10,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                            {
                                "frequency": 100,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                            {
                                "frequency": 1000,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                        ],
                    }
                )

            Or a simplified, shorter notation if, for example, only the frequency in the list needs to be adjusted.

            .. code-block:: python

                freqs_to_measure = [10, 100, 1000]
                job = EisFrequencyTableJob(
                    {
                        "bias": 0.0,
                        "spectrum": [
                            {
                                "frequency": freq,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            }
                            for freq in freqs_to_measure
                        ],
                    }
                )

        '''

class EisGenerateJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: EisParametersGeneratePy
    def __init__(self, bias: typing.SupportsFloat, min_frequency: typing.SupportsFloat, max_frequency: typing.SupportsFloat, start_frequency: typing.SupportsFloat, points_per_decade_upper: typing.SupportsInt, points_per_decade_lower: typing.SupportsInt, pre_duration: typing.SupportsFloat, pre_waves: typing.SupportsInt, meas_duration: typing.SupportsFloat, meas_waves: typing.SupportsInt, amplitude: typing.SupportsFloat, meta_data: dict = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.EisGenerateJob, bias: typing.SupportsFloat, min_frequency: typing.SupportsFloat, max_frequency: typing.SupportsFloat, start_frequency: typing.SupportsFloat, points_per_decade_upper: typing.SupportsInt, points_per_decade_lower: typing.SupportsInt, pre_duration: typing.SupportsFloat, pre_waves: typing.SupportsInt, meas_duration: typing.SupportsFloat, meas_waves: typing.SupportsInt, amplitude: typing.SupportsFloat, meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job

            The sequence is from `start_frequency` to `max_frequency` back down to `min_frequency`.
            The following applies: `min_frequency` < `start_frequency` < `max_frequency`.

            At 66 Hz, the density of the spectrum can be changed. Above 66 Hz,
            measurements are made with `points_per_decade_upper` steps per decade.
            Below 66 Hz, the support point density is changed linearly from
            `points_per_decade_upper` to `points_per_decade_lower` at `max_frequency` down to `min_frequency`.

            In order to make optimum use of the measuring time per frequency point,
            you can specify the minimum number of periods to be measured with `meas_waves` and a time `meas_duration`.
            At least `meas_waves` are always measured, but if `meas_duration` has not been reached after `meas_waves` periods,
            measurements are continued until this time is reached. Especially in the low frequency range, `meas_waves` will always exceed `meas_duration`.

            :param bias: DC bias for defining the operating point of the object
            :param min_frequency: lower frequency limit of the impedance spectrum
            :param max_frequency: upper frequency limit of the impedance spectrum
            :param start_frequency: starting frequency of the impedance spectrum
            :param points_per_decade_upper:
                * number of frequency steps per decade between 66 Hz and max_frequency
                * frequency steps are logarithmic equidistant
            :param points_per_decade_lower:
                * number of frequency steps per decade at min_frequency
                * logarithmic linear density from min_frequency to 66 Hz
            :param pre_duration:
                * minimum pre-conditioning time for each frequency step
                * allow longer pre-conditioning at higher frequencies
            :param pre_waves:
                * number of pre-conditioning sine waves before each frequency step
                * more waves for better pre-conditioning
            :param meas_duration:
                * minimum recording time for each frequency step
                * allow more averages at higher frequencies
            :param meas_waves:
                * minimum number of sine waves for each frequency step
                * more averages for higher SNR
            :param amplitude: corresponding AC peak amplitude
            :param meta_data: dict[str, str] with user-defined key-value pairs

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "eis",
                      "parameters": {
                        "bias": 0.0,
                        "frequency_range": {
                          "type": "generate",
                          "min_frequency": 100.0,
                          "max_frequency": 1000000.0,
                          "start_frequency": 10000.0,
                          "points_per_decade_upper": 20,
                          "points_per_decade_lower": 5,
                          "pre_duration": 0.1,
                          "pre_waves": 1,
                          "meas_duration": 1.0,
                          "meas_waves": 5,
                          "amplitude": 0.01
                        }
                      }
                    },
                    "request_id": "e813643e-4dde-4b5c-bb0e-7e1cfdf0646c"
                  }

        '''

class EisParametersFrequencyTable:
    bias: float
    spectrum: list[EisParametersFrequencyTableEntry]
    def __init__(self, bias: typing.SupportsFloat, spectrum: collections.abc.Sequence[EisParametersFrequencyTableEntry]) -> None:
        """__init__(self: zahner_link._zahner_link.meas.EisParametersFrequencyTable, bias: typing.SupportsFloat, spectrum: collections.abc.Sequence[zahner_link._zahner_link.meas.EisParametersFrequencyTableEntry]) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param bias: DC bias for defining the operating point of the object
            :param spectrum: spectrum measurement settings

        """

class EisParametersFrequencyTableEntry:
    amplitude: float
    frequency: float
    meas_duration: float
    meas_waves: int
    pre_duration: float
    pre_waves: int
    def __init__(self, frequency: typing.SupportsFloat, amplitude: typing.SupportsFloat, pre_duration: typing.SupportsFloat, pre_waves: typing.SupportsInt, meas_duration: typing.SupportsFloat, meas_waves: typing.SupportsInt) -> None:
        """__init__(self: zahner_link._zahner_link.meas.EisParametersFrequencyTableEntry, frequency: typing.SupportsFloat, amplitude: typing.SupportsFloat, pre_duration: typing.SupportsFloat, pre_waves: typing.SupportsInt, meas_duration: typing.SupportsFloat, meas_waves: typing.SupportsInt) -> None


            Settings for a frequency point

            Each frequency point can be measured with an individual duration and amplitude in order to measure the object as accurately as possible.
    
            In order to make optimum use of the measuring time per frequency point,
            you can specify the minimum number of periods to be measured with `meas_waves` and a time `meas_duration`.
            At least `meas_waves` are always measured, but if `meas_duration` has not been reached after `meas_waves` periods,
            measurements are continued until this time is reached. Especially in the low frequency range, `meas_waves` will always exceed `meas_duration`.

            :param frequency: corresponding AC frequency
            :param amplitude: corresponding AC peak amplitude
            :param pre_duration:
                * minimum pre-conditioning time for each frequency step
                * allow longer pre-conditioning at higher frequencies
            :param pre_waves:
                * number of pre-conditioning sine waves before each frequency step
                * more waves for better pre-conditioning
            :param meas_duration:
                * minimum recording time for each frequency step
                * allow more averages at higher frequencies
            :param meas_waves:
                * minimum number of sine waves for each frequency step
                * more averages for higher SNR

        """

class EisParametersFrequencyTablePy:
    bias: float
    spectrum: list[EisParametersFrequencyTableEntry]
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class EisParametersGeneratePy:
    amplitude: float
    bias: float
    max_frequency: float
    meas_duration: float
    meas_waves: int
    min_frequency: float
    points_per_decade_lower: int
    points_per_decade_upper: int
    pre_duration: float
    pre_waves: int
    start_frequency: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class GeisVaFrequencyTableJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: GeisVaParametersFrequencyTablePy
    @overload
    def __init__(self, bias: typing.SupportsFloat, minimum_current_amplitude: typing.SupportsFloat, maximum_current_amplitude: typing.SupportsFloat, spectrum: collections.abc.Sequence[EisParametersFrequencyTableEntry], meta_data: dict = ...) -> None:
        '''__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.meas.GeisVaFrequencyTableJob, bias: typing.SupportsFloat, minimum_current_amplitude: typing.SupportsFloat, maximum_current_amplitude: typing.SupportsFloat, spectrum: collections.abc.Sequence[zahner_link._zahner_link.meas.EisParametersFrequencyTableEntry], meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param bias: DC current bias for defining the operating point of the object
            :param minimum_current_amplitude: minimum current amplitude that will be used for the measurement
            :param maximum_current_amplitude: maximum current amplitude that will be used for the measurement
            :param spectrum: spectrum measurement settings
            :param meta_data: dict[str, str] with user-defined key-value pairs

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "geis_va_table",
                      "parameters": {
                        "bias": 0.0,
                        "minimum_current_amplitude": 0.001,
                        "maximum_current_amplitude": 1.0,
                        "frequency_range": {
                          "type": "table",
                          "spectrum": [
                            {
                              "frequency": 100.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            },
                            {
                              "frequency": 200.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            },
                            {
                              "frequency": 500.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            }
                          ]
                        }
                      }
                    },
                    "request_id": "00936e81-a128-4526-8a9e-5d5bdbf82fb9"
                  }


        2. __init__(self: zahner_link._zahner_link.meas.GeisVaFrequencyTableJob, table: GeisVaParametersFrequencyTable, meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param table: spectrum measurement settings
            :param meta_data: dict[str, str] with user-defined key-value pairs


        3. __init__(self: zahner_link._zahner_link.meas.GeisVaFrequencyTableJob, table: dict, meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param table: a dictionary with values like the following example
            :param meta_data: dict[str, str] with user-defined key-value pairs

            .. code-block:: python

                job = GeisVaFrequencyTableJob(
                    {
                        "bias": 0.0,
                        "minimum_current_amplitude": 0.001,
                        "maximum_current_amplitude": 1,
                        "spectrum": [
                            {
                                "frequency": 10,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                            {
                                "frequency": 100,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                            {
                                "frequency": 1000,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                        ],
                    }
                )

            Or a simplified, shorter notation if, for example, only the frequency in the list needs to be adjusted.

            .. code-block:: python

                freqs_to_measure = [10, 100, 1000]
                job = GeisVaFrequencyTableJob(
                    {
                        "bias": 0.0,
                        "minimum_current_amplitude": 0.001,
                        "maximum_current_amplitude": 1,
                        "spectrum": [
                            {
                                "frequency": freq,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            }
                            for freq in freqs_to_measure
                        ],
                    }
                )

        '''
    @overload
    def __init__(self, table: GeisVaParametersFrequencyTable, meta_data: dict = ...) -> None:
        '''__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.meas.GeisVaFrequencyTableJob, bias: typing.SupportsFloat, minimum_current_amplitude: typing.SupportsFloat, maximum_current_amplitude: typing.SupportsFloat, spectrum: collections.abc.Sequence[zahner_link._zahner_link.meas.EisParametersFrequencyTableEntry], meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param bias: DC current bias for defining the operating point of the object
            :param minimum_current_amplitude: minimum current amplitude that will be used for the measurement
            :param maximum_current_amplitude: maximum current amplitude that will be used for the measurement
            :param spectrum: spectrum measurement settings
            :param meta_data: dict[str, str] with user-defined key-value pairs

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "geis_va_table",
                      "parameters": {
                        "bias": 0.0,
                        "minimum_current_amplitude": 0.001,
                        "maximum_current_amplitude": 1.0,
                        "frequency_range": {
                          "type": "table",
                          "spectrum": [
                            {
                              "frequency": 100.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            },
                            {
                              "frequency": 200.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            },
                            {
                              "frequency": 500.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            }
                          ]
                        }
                      }
                    },
                    "request_id": "00936e81-a128-4526-8a9e-5d5bdbf82fb9"
                  }


        2. __init__(self: zahner_link._zahner_link.meas.GeisVaFrequencyTableJob, table: GeisVaParametersFrequencyTable, meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param table: spectrum measurement settings
            :param meta_data: dict[str, str] with user-defined key-value pairs


        3. __init__(self: zahner_link._zahner_link.meas.GeisVaFrequencyTableJob, table: dict, meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param table: a dictionary with values like the following example
            :param meta_data: dict[str, str] with user-defined key-value pairs

            .. code-block:: python

                job = GeisVaFrequencyTableJob(
                    {
                        "bias": 0.0,
                        "minimum_current_amplitude": 0.001,
                        "maximum_current_amplitude": 1,
                        "spectrum": [
                            {
                                "frequency": 10,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                            {
                                "frequency": 100,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                            {
                                "frequency": 1000,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                        ],
                    }
                )

            Or a simplified, shorter notation if, for example, only the frequency in the list needs to be adjusted.

            .. code-block:: python

                freqs_to_measure = [10, 100, 1000]
                job = GeisVaFrequencyTableJob(
                    {
                        "bias": 0.0,
                        "minimum_current_amplitude": 0.001,
                        "maximum_current_amplitude": 1,
                        "spectrum": [
                            {
                                "frequency": freq,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            }
                            for freq in freqs_to_measure
                        ],
                    }
                )

        '''
    @overload
    def __init__(self, table: dict, meta_data: dict = ...) -> None:
        '''__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.meas.GeisVaFrequencyTableJob, bias: typing.SupportsFloat, minimum_current_amplitude: typing.SupportsFloat, maximum_current_amplitude: typing.SupportsFloat, spectrum: collections.abc.Sequence[zahner_link._zahner_link.meas.EisParametersFrequencyTableEntry], meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param bias: DC current bias for defining the operating point of the object
            :param minimum_current_amplitude: minimum current amplitude that will be used for the measurement
            :param maximum_current_amplitude: maximum current amplitude that will be used for the measurement
            :param spectrum: spectrum measurement settings
            :param meta_data: dict[str, str] with user-defined key-value pairs

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "geis_va_table",
                      "parameters": {
                        "bias": 0.0,
                        "minimum_current_amplitude": 0.001,
                        "maximum_current_amplitude": 1.0,
                        "frequency_range": {
                          "type": "table",
                          "spectrum": [
                            {
                              "frequency": 100.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            },
                            {
                              "frequency": 200.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            },
                            {
                              "frequency": 500.0,
                              "amplitude": 0.01,
                              "pre_duration": 0.1,
                              "pre_waves": 1,
                              "meas_duration": 1.0,
                              "meas_waves": 5
                            }
                          ]
                        }
                      }
                    },
                    "request_id": "00936e81-a128-4526-8a9e-5d5bdbf82fb9"
                  }


        2. __init__(self: zahner_link._zahner_link.meas.GeisVaFrequencyTableJob, table: GeisVaParametersFrequencyTable, meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param table: spectrum measurement settings
            :param meta_data: dict[str, str] with user-defined key-value pairs


        3. __init__(self: zahner_link._zahner_link.meas.GeisVaFrequencyTableJob, table: dict, meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job with self-specified frequency points.

            With this EIS, you can determine the frequencies, amplitude and duration of the measurement.
            This allows the object to be better characterized at relevant points than with an automatically generated spectrum,
            where the support points cannot be precisely defined.

            :param table: a dictionary with values like the following example
            :param meta_data: dict[str, str] with user-defined key-value pairs

            .. code-block:: python

                job = GeisVaFrequencyTableJob(
                    {
                        "bias": 0.0,
                        "minimum_current_amplitude": 0.001,
                        "maximum_current_amplitude": 1,
                        "spectrum": [
                            {
                                "frequency": 10,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                            {
                                "frequency": 100,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                            {
                                "frequency": 1000,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            },
                        ],
                    }
                )

            Or a simplified, shorter notation if, for example, only the frequency in the list needs to be adjusted.

            .. code-block:: python

                freqs_to_measure = [10, 100, 1000]
                job = GeisVaFrequencyTableJob(
                    {
                        "bias": 0.0,
                        "minimum_current_amplitude": 0.001,
                        "maximum_current_amplitude": 1,
                        "spectrum": [
                            {
                                "frequency": freq,
                                "amplitude": 0.01,
                                "pre_duration": 0.1,
                                "pre_waves": 1,
                                "meas_duration": 1,
                                "meas_waves": 3,
                            }
                            for freq in freqs_to_measure
                        ],
                    }
                )

        '''

class GeisVaGenerateJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: GeisVaParametersGeneratePy
    def __init__(self, bias: typing.SupportsFloat, min_frequency: typing.SupportsFloat, max_frequency: typing.SupportsFloat, start_frequency: typing.SupportsFloat, points_per_decade_upper: typing.SupportsInt, points_per_decade_lower: typing.SupportsInt, pre_duration: typing.SupportsFloat, pre_waves: typing.SupportsInt, meas_duration: typing.SupportsFloat, meas_waves: typing.SupportsInt, amplitude: typing.SupportsFloat, minimum_current_amplitude: typing.SupportsFloat, maximum_current_amplitude: typing.SupportsFloat, meta_data: dict = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.GeisVaGenerateJob, bias: typing.SupportsFloat, min_frequency: typing.SupportsFloat, max_frequency: typing.SupportsFloat, start_frequency: typing.SupportsFloat, points_per_decade_upper: typing.SupportsInt, points_per_decade_lower: typing.SupportsInt, pre_duration: typing.SupportsFloat, pre_waves: typing.SupportsInt, meas_duration: typing.SupportsFloat, meas_waves: typing.SupportsInt, amplitude: typing.SupportsFloat, minimum_current_amplitude: typing.SupportsFloat, maximum_current_amplitude: typing.SupportsFloat, meta_data: dict = {}) -> None


            Electrochemical Impedance Spectroscopy job

            The sequence is from start_frequency to max_frequency back down to min_frequency.
            The following applies: min_frequency < start_frequency < max_frequency.

            At 66 Hz, the density of the spectrum can be changed. Above 66 Hz,
            measurements are made with `points_per_decade_upper` steps per decade.
            Below 66 Hz, the support point density is changed linearly from
            `points_per_decade_upper` to `points_per_decade_lower` at `max_frequency` down to `min_frequency`.
    
            In order to make optimum use of the measuring time per frequency point,
            you can specify the minimum number of periods to be measured with `meas_waves` and a time `meas_duration`.
            At least `meas_waves` are always measured, but if `meas_duration` has not been reached after `meas_waves` periods,
            measurements are continued until this time is reached. Especially in the low frequency range, `meas_waves` will always exceed `meas_duration`.
    
            :param bias: DC current bias for defining the operating point of the object
            :param min_frequency: lower frequency limit of the impedance spectrum
            :param max_frequency: upper frequency limit of the impedance spectrum
            :param start_frequency: starting frequency of the impedance spectrum
            :param points_per_decade_upper:
                * number of frequency steps per decade between 66 Hz and max_frequency
                * frequency steps are logarithmic equidistant
            :param points_per_decade_lower:
                * number of frequency steps per decade at min_frequency
                * logarithmic linear density from min_frequency to 66 Hz
            :param pre_duration:
                * minimum pre-conditioning time for each frequency step
                * allow longer pre-conditioning at higher frequencies
            :param pre_waves:
                * number of pre-conditioning sine waves before each frequency step
                * more waves for better pre-conditioning
            :param meas_duration:
                * minimum recording time for each frequency step
                * allow more averages at higher frequencies
            :param meas_waves:
                * minimum number of sine waves for each frequency step
                * more averages for higher SNR
            :param amplitude: corresponding AC voltage peak amplitude
            :param minimum_current_amplitude: minimum current amplitude that will be used for the measurement
            :param maximum_current_amplitude: maximum current amplitude that will be used for the measurement
            :param meta_data: dict[str, str] with user-defined key-value pairs

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "eis",
                      "parameters": {
                        "bias": 0.0,
                        "minimum_current_amplitude": 0.001,
                        "maximum_current_amplitude": 1.0,
                        "frequency_range": {
                          "type": "generate",
                          "min_frequency": 100.0,
                          "max_frequency": 1000000.0,
                          "start_frequency": 10000.0,
                          "points_per_decade_upper": 20,
                          "points_per_decade_lower": 5,
                          "pre_duration": 0.1,
                          "pre_waves": 1,
                          "meas_duration": 1.0,
                          "meas_waves": 5,
                          "amplitude": 0.01
                        }
                      }
                    },
                    "request_id": "e813643e-4dde-4b5c-bb0e-7e1cfdf0646c"
                  }

        '''

class GeisVaParametersFrequencyTablePy:
    bias: float
    maximum_current_amplitude: float
    minimum_current_amplitude: float
    spectrum: list[EisParametersFrequencyTableEntry]
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class GeisVaParametersGeneratePy:
    amplitude: float
    bias: float
    max_frequency: float
    maximum_current_amplitude: float
    meas_duration: float
    meas_waves: int
    min_frequency: float
    minimum_current_amplitude: float
    points_per_decade_lower: int
    points_per_decade_upper: int
    pre_duration: float
    pre_waves: int
    start_frequency: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class NpvJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: NpvParametersPy
    def __init__(self, start_value: typing.SupportsFloat, step_value: typing.SupportsFloat, end_value: typing.SupportsFloat, step_time: typing.SupportsFloat, pulse_time: typing.SupportsFloat, output_data_rate: typing.SupportsFloat, current_range: typing.SupportsFloat, meta_data: dict = ..., stop_conditions: collections.abc.Sequence[AbstractStopCondition] = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.NpvJob, start_value: typing.SupportsFloat, step_value: typing.SupportsFloat, end_value: typing.SupportsFloat, step_time: typing.SupportsFloat, pulse_time: typing.SupportsFloat, output_data_rate: typing.SupportsFloat, current_range: typing.SupportsFloat, meta_data: dict = {}, stop_conditions: collections.abc.Sequence[AbstractStopCondition] = []) -> None


            Normal Pulse Voltammetry job

            :param start_value: starting DC value
            :param step_value: value of each step for the rising pulse function
            :param end_value: maximum DC value of the last step and pulse
            :param step_time:
                * duration of each step of the staircase
                * should be at least twice as long as pulse duration
            :param pulse_time: duration of each pulse
            :param output_data_rate: rate at which data is output
            :param current_range: selection of the current range that matches the object as the maximum absolute current
            :param meta_data: dict[str, str] with user-defined key-value pairs
            :param stop_conditions: list of stop condition objects from :ref:`python_stopconditions`

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "npv",
                      "parameters": {
                        "start_value": 0.0,
                        "step_value": 0.1,
                        "end_value": 1.5,
                        "step_time": 1.0,
                        "pulse_time": 0.1,
                        "output_data_rate": 200.0,
                        "current_range": 0.1
                      }
                    },
                    "request_id": "npv-job-uuid-example"
                  }

        '''

class NpvParametersPy:
    current_range: float
    end_value: float
    output_data_rate: float
    pulse_time: float
    start_value: float
    step_time: float
    step_value: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class OcvJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: OcvParametersPy
    def __init__(self, duration: typing.SupportsFloat, output_data_rate: typing.SupportsFloat, meta_data: dict = ..., stop_conditions: collections.abc.Sequence[AbstractStopCondition] = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.OcvJob, duration: typing.SupportsFloat, output_data_rate: typing.SupportsFloat, meta_data: dict = {}, stop_conditions: collections.abc.Sequence[AbstractStopCondition] = []) -> None


            Open Circuit Voltage job

            Also referred to as Open Circuit Potential.

            :param duration: maximum runtime
            :param output_data_rate: rate at which data is output
            :param meta_data: dict[str, str] with user-defined key-value pairs
            :param stop_conditions: list of stop condition objects from :ref:`python_stopconditions`

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "ocv",
                      "parameters": {
                        "duration": 10.0,
                        "output_data_rate": 10.0
                      }
                    },
                    "request_id": "ocv-job-uuid-example"
                  }

        '''

class OcvParametersPy:
    duration: float
    output_data_rate: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class PogaJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: PogaParametersPy
    def __init__(self, bias: typing.SupportsFloat, duration: typing.SupportsFloat, output_data_rate: typing.SupportsFloat, autorange: bool, current_range: typing.SupportsFloat, ir_drop: typing.SupportsFloat, meta_data: dict = ..., stop_conditions: collections.abc.Sequence[AbstractStopCondition] = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.PogaJob, bias: typing.SupportsFloat, duration: typing.SupportsFloat, output_data_rate: typing.SupportsFloat, autorange: bool, current_range: typing.SupportsFloat, ir_drop: typing.SupportsFloat, meta_data: dict = {}, stop_conditions: collections.abc.Sequence[AbstractStopCondition] = []) -> None


            Poga Potentiostatic Galvanostatic Polarization job
        
            Can be potentiostatic or galvanostatic.
            Also referred to as Chronopotentiometry, Chronoamperometry, Chronocoulometry.

            :param bias: start value
            :param duration: maximum runtime
            :param output_data_rate: rate at which data is output
            :param autorange:
                * whether automatic switching should be used
                * for maximum measurement accuracy, autoranging should be switched off and current_range should be selected to match the object
            :param current_range: optional selection of the current range that matches the object as the maximum absolute current if autoranging is disabled
            :param ir_drop:
                * ohmic value for iRdrop compensation
                * at 0 disabled
            :param meta_data: dict[str, str] with user-defined key-value pairs
            :param stop_conditions: list of stop condition objects from :ref:`python_stopconditions`

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "poga",
                      "parameters": {
                        "bias": 1.0,
                        "duration": 5.0,
                        "output_data_rate": 25.0,
                        "autorange": true,
                        "current_range": 0.1,
                        "ir_drop": 0.0
                      }
                    },
                    "request_id": "poga-job-uuid-example"
                  }

        '''

class PogaParametersPy:
    autorange: bool
    bias: float
    current_range: float
    duration: float
    ir_drop: float
    output_data_rate: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class RampJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: RampParametersPy
    def __init__(self, start_value: typing.SupportsFloat, end_value: typing.SupportsFloat, scan_rate: typing.SupportsFloat, step_height: typing.SupportsFloat, output_data_rate: typing.SupportsFloat, autorange: bool, current_range: typing.SupportsFloat, ir_drop: typing.SupportsFloat, meta_data: dict = ..., stop_conditions: collections.abc.Sequence[AbstractStopCondition] = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.RampJob, start_value: typing.SupportsFloat, end_value: typing.SupportsFloat, scan_rate: typing.SupportsFloat, step_height: typing.SupportsFloat, output_data_rate: typing.SupportsFloat, autorange: bool, current_range: typing.SupportsFloat, ir_drop: typing.SupportsFloat, meta_data: dict = {}, stop_conditions: collections.abc.Sequence[AbstractStopCondition] = []) -> None


            Ramp job

            Can be potentiostatic or galvanostatic.
            Also referred to as:
    
            * Linear Sweep Voltammetry (LSV)
            * Linear Sweep Galvanostatic
            * Staircase Voltammetry/Galvanostatic
            * Current Voltage Characteristic/Curves

            :param start_value: start value of the ramp
            :param end_value: end value of the ramp
            :param scan_rate: scan rate from start_value to end_value
            :param step_height:
                * height of the steps
                * 0 uses the smallest step size
            :param output_data_rate: rate at which data is output
            :param autorange:
                * whether automatic switching should be used
                * for maximum measurement accuracy, autoranging should be switched off and current_range should be selected to match the object
            :param current_range: optional selection of the current range that matches the object as the maximum absolute current if autoranging is disabled
            :param ir_drop:
                * ohmic value for iRdrop compensation
                * at 0 disabled
            :param meta_data: dict[str, str] with user-defined key-value pairs
            :param stop_conditions: list of stop condition objects from :ref:`python_stopconditions`

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "ramp",
                      "parameters": {
                        "start_value": 0.0,
                        "end_value": 1.0,
                        "scan_rate": 0.1,
                        "step_height": 0.0,
                        "output_data_rate": 10.0,
                        "autorange": true,
                        "current_range": 0.1,
                        "ir_drop": 0.0
                      }
                    },
                    "request_id": "ramp-job-uuid-example"
                  }

        '''

class RampParametersPy:
    autorange: bool
    current_range: float
    end_value: float
    ir_drop: float
    output_data_rate: float
    scan_rate: float
    start_value: float
    step_height: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class SteadyStairsJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: SteadyStairsParametersPy
    def __init__(self, start_value: typing.SupportsFloat, end_value: typing.SupportsFloat, step_time: typing.SupportsFloat, step_height: typing.SupportsFloat, hold_time: typing.SupportsFloat, stability_tolerance: typing.SupportsFloat, output_data_rate: typing.SupportsFloat, autorange: bool, current_range: typing.SupportsFloat, ir_drop: typing.SupportsFloat, meta_data: dict = ..., stop_conditions: collections.abc.Sequence[AbstractStopCondition] = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.SteadyStairsJob, start_value: typing.SupportsFloat, end_value: typing.SupportsFloat, step_time: typing.SupportsFloat, step_height: typing.SupportsFloat, hold_time: typing.SupportsFloat, stability_tolerance: typing.SupportsFloat, output_data_rate: typing.SupportsFloat, autorange: bool, current_range: typing.SupportsFloat, ir_drop: typing.SupportsFloat, meta_data: dict = {}, stop_conditions: collections.abc.Sequence[AbstractStopCondition] = []) -> None


            Steady Stairs Current Voltage Characteristic/Curves job

            Can be potentiostatic or galvanostatic.

            This primitive can be used to output slower steps, whereby each step has a termination criterion based on a change tolerance.
            For example, voltage steps can be terminated if the current change falls below a certain value.

            Also referred to as:

            * Current Voltage Characteristic/Curves
            * Steady State Staircase Voltammetry/Galvanostatic
            * IE

            :param start_value: start value of the ramp
            :param end_value: end value of the ramp
            :param step_time: maximum duration of a step
            :param step_height: height of the steps
            :param hold_time: time after that the stability tolerance is checked
            :param stability_tolerance: absolute tolerance value for a change in dimension per second below which the job stops
            :param output_data_rate: rate at which data is output
            :param autorange:
                * whether automatic switching should be used
                * for maximum measurement accuracy, autoranging should be switched off and current_range should be selected to match the object
            :param current_range: optional selection of the current range that matches the object as the maximum absolute current if autoranging is disabled
            :param ir_drop:
                * ohmic value for iRdrop compensation
                * at 0 disabled
            :param meta_data: dict[str, str] with user-defined key-value pairs
            :param stop_conditions: list of stop condition objects from :ref:`python_stopconditions`

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "steady_stairs",
                      "parameters": {
                        "start_value": 0.0,
                        "end_value": 1.0,
                        "step_time": 2.0,
                        "step_height": 0.01,
                        "hold_time": 1.0,
                        "stability_tolerance": 0.01,
                        "output_data_rate": 10.0,
                        "autorange": true,
                        "current_range": 0.1,
                        "ir_drop": 0.0
                      }
                    },
                    "request_id": "steady-stairs-job-uuid-example"
                  }

        '''

class SteadyStairsParametersPy:
    autorange: bool
    current_range: float
    end_value: float
    hold_time: float
    ir_drop: float
    output_data_rate: float
    stability_tolerance: float
    start_value: float
    step_height: float
    step_time: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class SwvJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: SwvParametersPy
    def __init__(self, start_value: typing.SupportsFloat, step_value: typing.SupportsFloat, amplitude: typing.SupportsFloat, end_value: typing.SupportsFloat, period: typing.SupportsFloat, output_data_rate: typing.SupportsFloat, current_range: typing.SupportsFloat, meta_data: dict = ..., stop_conditions: collections.abc.Sequence[AbstractStopCondition] = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.SwvJob, start_value: typing.SupportsFloat, step_value: typing.SupportsFloat, amplitude: typing.SupportsFloat, end_value: typing.SupportsFloat, period: typing.SupportsFloat, output_data_rate: typing.SupportsFloat, current_range: typing.SupportsFloat, meta_data: dict = {}, stop_conditions: collections.abc.Sequence[AbstractStopCondition] = []) -> None


            Square Wave Voltammetry job

            :param start_value: starting DC value
            :param step_value: value of each step for the staircase function
            :param amplitude: rectangle amplitude of the differential pulse added to the staircase potential
            :param end_value: maximum DC potential of the last step and pulse
            :param period:
                * duration of each differential pulse period
                * each pulse is half of the period time
            :param output_data_rate: rate at which data is output
            :param current_range: selection of the current range that matches the object as the maximum absolute current
            :param meta_data: dict[str, str] with user-defined key-value pairs
            :param stop_conditions: list of stop condition objects from :ref:`python_stopconditions`

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "swv",
                      "parameters": {
                        "start_value": 0.0,
                        "step_value": 0.01,
                        "amplitude": 0.05,
                        "end_value": 1.5,
                        "period": 0.4,
                        "output_data_rate": 200.0,
                        "current_range": 0.1
                      }
                    },
                    "request_id": "swv-job-uuid-example"
                  }

        '''

class SwvParametersPy:
    amplitude: float
    current_range: float
    end_value: float
    output_data_rate: float
    period: float
    start_value: float
    step_value: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class WaveFileJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: WaveFileParametersPy
    def __init__(self, output_data_rate: typing.SupportsFloat, value_rate: typing.SupportsFloat, current_range: typing.SupportsFloat, resource_id: str, meta_data: dict = ..., stop_conditions: collections.abc.Sequence[AbstractStopCondition] = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.WaveFileJob, output_data_rate: typing.SupportsFloat, value_rate: typing.SupportsFloat, current_range: typing.SupportsFloat, resource_id: str, meta_data: dict = {}, stop_conditions: collections.abc.Sequence[AbstractStopCondition] = []) -> None


            WaveFile job

            Can be potentiostatic or galvanostatic.
            The wave job can be used to output arbitrary values of current or voltage which are faster.
            Current and voltage cannot be mixed. For slow processes, ramp and poga should be used instead of wave.

            This job variant uses a previously uploaded file with current or voltage values, which can be used for large waveforms.
    
            :param output_data_rate: rate at which data is output which was measured (internal oversampled)
            :param value_rate: rate at which current or voltage values are output
            :param current_range: selection of the current range that matches the object as the maximum absolute current
            :param resource_id: resource id of (previously uploaded) file with current or voltage values which are output with value_rate frequency
            :param meta_data: dict[str, str] with user-defined key-value pairs
            :param stop_conditions: list of stop condition objects from :ref:`python_stopconditions`

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "wave_file",
                      "parameters": {
                        "output_data_rate": 1000.0,
                        "value_rate": 1000.0,
                        "current_range": 0.001,
                        "resource_id": "triangular-wave-resource-uuid"
                      }
                    },
                    "request_id": "wave-file-job-uuid-example"
                  }

        '''

class WaveFileParametersPy:
    current_range: float
    output_data_rate: float
    resource_id: str
    value_rate: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class WaveJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: WaveParametersPy
    def __init__(self, output_data_rate: typing.SupportsFloat, value_rate: typing.SupportsFloat, current_range: typing.SupportsFloat, values: collections.abc.Sequence[typing.SupportsFloat], meta_data: dict = ..., stop_conditions: collections.abc.Sequence[AbstractStopCondition] = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.WaveJob, output_data_rate: typing.SupportsFloat, value_rate: typing.SupportsFloat, current_range: typing.SupportsFloat, values: collections.abc.Sequence[typing.SupportsFloat], meta_data: dict = {}, stop_conditions: collections.abc.Sequence[AbstractStopCondition] = []) -> None


            Wave job

            Can be potentiostatic or galvanostatic.
            The wave job can be used to output arbitrary values of current or voltage which are faster.
            Current and voltage cannot be mixed. For slow processes, ramp and poga should be used instead of wave.
    
            :param output_data_rate: rate at which data is output which was measured (internal oversampled)
            :param value_rate: rate at which current or voltage values are output
            :param current_range: selection of the current range that matches the object as the maximum absolute current
            :param values: current or voltage values list which are output with value_rate frequency
            :param meta_data: dict[str, str] with user-defined key-value pairs
            :param stop_conditions: list of stop condition objects from :ref:`python_stopconditions`

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "wave",
                      "parameters": {
                        "output_data_rate": 1000.0,
                        "value_rate": 100.0,
                        "current_range": 0.01,
                        "values": [0.0, 0.5, 1.0, 0.5, 0.0, -0.5, -1.0, -0.5, 0.0]
                      }
                    },
                    "request_id": "wave-job-uuid-example"
                  }

        '''

class WaveParametersPy:
    current_range: float
    output_data_rate: float
    value_rate: float
    values: list[float]
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
