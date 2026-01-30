import collections.abc
import typing
import zahner_link._zahner_link
from typing import overload

class AdcStateInfo:
    active_gain_indexes: list[int]
    def __init__(self) -> None:
        """__init__(self: zahner_link._zahner_link.control.AdcStateInfo) -> None


            Object which contains the state of the adc

        """

class BcMuxJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: BcMuxParametersPy
    def __init__(self, ip: str, port: typing.SupportsInt, channel: typing.SupportsInt, pulse_duration: typing.SupportsFloat = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.control.BcMuxJob, ip: str, port: typing.SupportsInt, channel: typing.SupportsInt, pulse_duration: typing.SupportsFloat = 0.25) -> None


            BC-MUX job
        
            Auxiliary job to control the BC-MUX directly with the measuring device.
            May be removed in the future, as the client should control the BC-MUX directly.
            JavaScript clients like the old Blockly cant talk with TCP/IP sockets to the BC-MUX.

            :param ip: IP address of the device
            :param port: port of the device
            :param channel:
                * channel to switch to the IM7
                * 0 to disconnect all
            :param pulse_duration: pulse duration for the relay. The default is 0.25 seconds, and 0 seconds for a monostable relay

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "bc_mux",
                      "parameters": {
                        "ip": "192.168.1.100",
                        "port": 4223,
                        "pulse_duration": 0.25,
                        "channel": 1
                      }
                    },
                    "request_id": "bc-mux-job-uuid-example"
                  }

        '''

class BcMuxParametersPy:
    channel: int
    ip: str
    port: int
    pulse_duration: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class BeepJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: BeepParametersPy
    def __init__(self, frequency: typing.SupportsFloat, duration: typing.SupportsFloat) -> None:
        '''__init__(self: zahner_link._zahner_link.control.BeepJob, frequency: typing.SupportsFloat, duration: typing.SupportsFloat) -> None


            Beep job

            :param frequency: frequency of the beep
            :param duration: duration of the beep

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "beep",
                      "parameters": {
                        "frequency": 1000.0,
                        "duration": 0.5
                      }
                    },
                    "request_id": "beep-job-uuid-example"
                  }

        '''

class BeepParametersPy:
    duration: float
    frequency: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class GetAdcStateJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: GetAdcStateParametersPy
    def __init__(self, adc: str) -> None:
        '''__init__(self: zahner_link._zahner_link.control.GetAdcStateJob, adc: str) -> None


            Get the state of the analog-to-digital converter job.

            :param adc: locator of the ADC like "PAD:1:PAD_U"

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "get_adc_state",
                      "parameters": {
                        "adc": "PAD:1:PAD_U"
                      }
                    },
                    "request_id": "get-adc-state-job-uuid-example"
                  }

        '''
    def get_job_result(self) -> AdcStateInfo:
        """get_job_result(self: zahner_link._zahner_link.control.GetAdcStateJob) -> zahner_link._zahner_link.control.AdcStateInfo


            Get the state of the analog-to-digital converter.

            :returns: object with the state

        """

class GetAdcStateParametersPy:
    adc: str
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class GetHardwareInfoJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: GetHardwareInfoParametersPy
    def __init__(self) -> None:
        '''__init__(self: zahner_link._zahner_link.control.GetHardwareInfoJob) -> None


            GetHardwareInfoJob job

            This job queries the device tree of the IM7, which contains all signal paths and potentiostats that are available.

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "get_hardware_info",
                      "parameters": {}
                    },
                    "request_id": "get-hardware-info-job-uuid-example"
                  }

        '''
    def get_job_result(self) -> zahner_link._zahner_link.HardwareInfo:
        """get_job_result(self: zahner_link._zahner_link.control.GetHardwareInfoJob) -> zahner_link._zahner_link.HardwareInfo


            Get the queried device tree.

            :returns: object with the device tree

        """

class GetHardwareInfoParametersPy:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class GetHardwareSettingsJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: GetHardwareSettingsParametersPy
    def __init__(self) -> None:
        '''__init__(self: zahner_link._zahner_link.control.GetHardwareSettingsJob) -> None


            GetHardwareSettingsJob job

            This job queries the current signal path measurement settings.

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "get_hardware_settings",
                      "parameters": {}
                    },
                    "request_id": "get-hardware-settings-job-uuid-example"
                  }

        '''
    def get_job_result(self) -> zahner_link._zahner_link.HardwareSettings:
        """get_job_result(self: zahner_link._zahner_link.control.GetHardwareSettingsJob) -> zahner_link._zahner_link.HardwareSettings


            Get the queried hardware settings.

            :returns: object with the settings

        """

class GetHardwareSettingsParametersPy:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class GetPotentiostatStateJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: GetPotentiostatStateParametersPy
    def __init__(self, potentiostat: str) -> None:
        '''__init__(self: zahner_link._zahner_link.control.GetPotentiostatStateJob, potentiostat: str) -> None


            GetPotentiostatStateJob job

            This job queries the status and information for a potentiostat.

            Url examples:
    
            * EPC:1:EXT2:POT
            * MAIN:1:POT

            Urn example:

            * 354531:POT

            :param potentiostat: url or urn of the desired potentiostat.

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "get_potentiostat_state",
                      "parameters": {
                        "potentiostat": "MAIN:1:POT"
                      }
                    },
                    "request_id": "get-potentiostat-state-job-uuid-example"
                  }

        '''
    def get_job_result(self) -> PotentiostatState:
        """get_job_result(self: zahner_link._zahner_link.control.GetPotentiostatStateJob) -> zahner_link._zahner_link.control.PotentiostatState


            Get the queried potentiostat state.

            :returns: object with the potentiostat state

        """

class GetPotentiostatStateParametersPy:
    potentiostat: str
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class MeasureIntegralJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: MeasureIntegralParametersPy
    def __init__(self, channel: str, duration: typing.SupportsFloat = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.control.MeasureIntegralJob, channel: str, duration: typing.SupportsFloat = 0.3) -> None


            Measurement of a single value

            This job can be used to measure a single value from a path or source.

            :param channel: locator like "MAIN:1:POT:U", "MAIN:1:POT:I", or a dimension like "voltage" or "current"
            :param duration: duration of the measurement

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "measure_integral",
                      "parameters": {
                        "channel": "MAIN:1:POT:U",
                        "duration": 0.3
                      }
                    },
                    "request_id": "measure-integral-job-uuid-example"
                  }

        '''
    def get_job_result(self) -> float:
        """get_job_result(self: zahner_link._zahner_link.control.MeasureIntegralJob) -> float


            Get the queried value.

            :returns: the measured value

        """

class MeasureIntegralParametersPy:
    channel: str
    duration: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class PotentiostatState:
    active_bandwidth_indexes: list[int]
    active_current_range_indexes: list[int]
    autocompensation_on: bool
    bandwidth_index: int
    bias: float
    compliance_range_index: int
    coupling: zahner_link._zahner_link.PotentiostatCoupling
    current_range_index: int
    current_range_integration_time: float
    current_range_relaxation_time: float
    switched_on: bool
    voltage_range_index: int
    def __init__(self) -> None:
        """__init__(self: zahner_link._zahner_link.control.PotentiostatState) -> None"""

class SetActiveCurrentRangesJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: SetActiveCurrentRangesParametersPy
    def __init__(self, potentiostat: str, indexes: collections.abc.Sequence[typing.SupportsInt] = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.control.SetActiveCurrentRangesJob, potentiostat: str, indexes: collections.abc.Sequence[typing.SupportsInt] = []) -> None


            Set active current ranges job

            :param potentiostat: url or urn of the desired potentiostat
            :param indexes: shunt indexes that may be used for the measurement. An empty list for all current ranges available in the hardware.

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "set_active_current_ranges",
                      "parameters": {
                        "potentiostat": "MAIN:1:POT",
                        "indexes": []
                      }
                    },
                    "request_id": "set-active-current-ranges-job-uuid-example"
                  }

        '''

class SetActiveCurrentRangesParametersPy:
    indexes: list[int]
    potentiostat: str
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class SetActiveGainsJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: SetActiveGainsParametersPy
    def __init__(self, adc: str, indexes: collections.abc.Sequence[typing.SupportsInt] = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.control.SetActiveGainsJob, adc: str, indexes: collections.abc.Sequence[typing.SupportsInt] = []) -> None


            Set active gains job

            :param adc: url or urn of the desired adc
            :param indexes: gain indexes that may be used for the measurement. An empty list for all gain indexes available in the hardware.

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "set_active_gains",
                      "parameters": {
                        "adc": "MAIN:1:ADC",
                        "indexes": []
                      }
                    },
                    "request_id": "set-active-gains-job-uuid-example"
                  }

        '''

class SetActiveGainsParametersPy:
    adc: str
    indexes: list[int]
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class SetBiasJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: SetBiasParametersPy
    def __init__(self, potentiostat: str, bias: typing.SupportsFloat) -> None:
        '''__init__(self: zahner_link._zahner_link.control.SetBiasJob, potentiostat: str, bias: typing.SupportsFloat) -> None


            Set bias job

            Only the bias is set and possibly ranged.
            Current or voltage are only measured internally for the ranging.

            :param potentiostat: url or urn of the desired potentiostat
            :param bias: value in V or A depending on mode

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "set_bias",
                      "parameters": {
                        "potentiostat": "MAIN:1:POT",
                        "bias": 1.5
                      }
                    },
                    "request_id": "set-bias-job-uuid-example"
                  }

        '''

class SetBiasParametersPy:
    bias: float
    potentiostat: str
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class SetCableOptionsJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: SetCableOptionsParametersPy
    def __init__(self, potentiostat: str, additional_ce_capacitance: typing.SupportsFloat) -> None:
        '''__init__(self: zahner_link._zahner_link.control.SetCableOptionsJob, potentiostat: str, additional_ce_capacitance: typing.SupportsFloat) -> None


            Set cable options job

            Sets additional cable options, like the additional CE capacitance (shunt capacitance).

            :param potentiostat: url or urn of the desired potentiostat
            :param additional_ce_capacitance: additional capacitance of the CE cable in Farad. For example 95e-12 for 95pF of Shielded Cable Set.

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "set_cable_options",
                      "parameters": {
                        "potentiostat": "MAIN:1:POT",
                        "additional_ce_capacitance": 95e-12
                      }
                    },
                    "request_id": "set-cable-options-job-uuid-example"
                  }

        '''

class SetCableOptionsParametersPy:
    additional_ce_capacitance: float
    potentiostat: str
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class SetHardwareSettingsJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: SetHardwareSettingsParametersPy
    @overload
    def __init__(self, settings: SetHardwareSettingsParameters) -> None:
        '''__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.control.SetHardwareSettingsJob, settings: SetHardwareSettingsParameters) -> None


            Set hardware settings for sampling job.

            Only the necessary channels should be measured, not simply all of them.
            As the sampling rate decreases slightly with each channel, less averaging can be performed.

            This class should be used in combination with the :class:`zahner_link.HardwareSettingsHelper` class.

            :param settings: object with the settings

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "set_hardware_settings",
                      "parameters": {
                        "output_potentiostats": [
                            {
                                "uri": "MAIN:1:POT",
                                "potentiostatic_polynomial": [
                                    0E0,
                                    1E0
                                ],
                                "galvanostatic_polynomial": [
                                    0E0,
                                    1E0
                                ]
                            }
                        ],
                        "channels": [
                            {
                                "uri": "MAIN:1:POT:U~PAD:1:PAD_U",
                                "dimension": "voltage",
                                "unit": "V",
                                "polynomial": [
                                    0E0,
                                    1E0
                                ]
                            },
                            {
                                "uri": "MAIN:1:POT:I~PAD:1:PAD_I",
                                "dimension": "current",
                                "unit": "A",
                                "polynomial": [
                                    0E0,
                                    1E0
                                ]
                            }
                        ],
                        "impedance_configurations": [
                            {
                            "numerator": "MAIN:1:POT:U~PAD:1:PAD_U",
                            "denominator": "MAIN:1:POT:I~PAD:1:PAD_I"
                            }
                        ]
                      }
                    },
                    "request_id": "set-hardware-settings-job-uuid-example"
                  }


        2. __init__(self: zahner_link._zahner_link.control.SetHardwareSettingsJob, channels: collections.abc.Sequence[zahner_link._zahner_link.Channel], impedance_configurations: collections.abc.Sequence[zahner_link._zahner_link.ImpedanceConfiguration], output_potentiostats: collections.abc.Sequence[zahner_link._zahner_link.PotentiostatConfiguration]) -> None


            Set hardware settings for sampling job.

            Only the necessary channels should be measured, not simply all of them.
            As the sampling rate decreases slightly with each channel, less averaging can be performed.

            This class should be used in combination with the :class:`zahner_link.HardwareSettingsHelper` class.

            :param channels:
                * channels to be measured during the measurement
                * sequential and parallel channels together these are automatically split
            :param impedance_configurations:
                * parallel sampled channels
                * as a list of lists from which impedances are calculated
                * in the sub list, the first element (index 0) divided by the second element (index 1) is used for the impedance calculation
            :param output_potentiostats: potentiostat on which the measurement is to be output


        3. __init__(self: zahner_link._zahner_link.control.SetHardwareSettingsJob, channels: collections.abc.Sequence[zahner_link._zahner_link.Channel], impedance_configurations: collections.abc.Sequence[zahner_link._zahner_link.ImpedanceConfiguration], output_potentiostats: collections.abc.Sequence[str]) -> None


            Set hardware settings for sampling job.

            Only the necessary channels should be measured, not simply all of them.
            As the sampling rate decreases slightly with each channel, less averaging can be performed.

            This class should be used in combination with the :class:`zahner_link.HardwareSettingsHelper` class.

            :param channels:
                * channels to be measured during the measurement
                * sequential and parallel channels together these are automatically split
            :param impedance_configurations:
                * parallel sampled channels
                * as a list of lists from which impedances are calculated
                * in the sub list, the first element (index 0) divided by the second element (index 1) is used for the impedance calculation
            :param output_potentiostats: potentiostat on which the measurement is to be output


        4. __init__(self: zahner_link._zahner_link.control.SetHardwareSettingsJob, config: zahner_link._zahner_link.UserHardwareSettings) -> None


            Set hardware settings for sampling job.

            The :class:`zahner_link.HardwareSettingsHelper` class returns a :class:`zahner_link.UserHardwareSettings` object, which can be passed to this class.

            :param config: object with the settings

        '''
    @overload
    def __init__(self, channels: collections.abc.Sequence[zahner_link._zahner_link.Channel], impedance_configurations: collections.abc.Sequence[zahner_link._zahner_link.ImpedanceConfiguration], output_potentiostats: collections.abc.Sequence[zahner_link._zahner_link.PotentiostatConfiguration]) -> None:
        '''__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.control.SetHardwareSettingsJob, settings: SetHardwareSettingsParameters) -> None


            Set hardware settings for sampling job.

            Only the necessary channels should be measured, not simply all of them.
            As the sampling rate decreases slightly with each channel, less averaging can be performed.

            This class should be used in combination with the :class:`zahner_link.HardwareSettingsHelper` class.

            :param settings: object with the settings

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "set_hardware_settings",
                      "parameters": {
                        "output_potentiostats": [
                            {
                                "uri": "MAIN:1:POT",
                                "potentiostatic_polynomial": [
                                    0E0,
                                    1E0
                                ],
                                "galvanostatic_polynomial": [
                                    0E0,
                                    1E0
                                ]
                            }
                        ],
                        "channels": [
                            {
                                "uri": "MAIN:1:POT:U~PAD:1:PAD_U",
                                "dimension": "voltage",
                                "unit": "V",
                                "polynomial": [
                                    0E0,
                                    1E0
                                ]
                            },
                            {
                                "uri": "MAIN:1:POT:I~PAD:1:PAD_I",
                                "dimension": "current",
                                "unit": "A",
                                "polynomial": [
                                    0E0,
                                    1E0
                                ]
                            }
                        ],
                        "impedance_configurations": [
                            {
                            "numerator": "MAIN:1:POT:U~PAD:1:PAD_U",
                            "denominator": "MAIN:1:POT:I~PAD:1:PAD_I"
                            }
                        ]
                      }
                    },
                    "request_id": "set-hardware-settings-job-uuid-example"
                  }


        2. __init__(self: zahner_link._zahner_link.control.SetHardwareSettingsJob, channels: collections.abc.Sequence[zahner_link._zahner_link.Channel], impedance_configurations: collections.abc.Sequence[zahner_link._zahner_link.ImpedanceConfiguration], output_potentiostats: collections.abc.Sequence[zahner_link._zahner_link.PotentiostatConfiguration]) -> None


            Set hardware settings for sampling job.

            Only the necessary channels should be measured, not simply all of them.
            As the sampling rate decreases slightly with each channel, less averaging can be performed.

            This class should be used in combination with the :class:`zahner_link.HardwareSettingsHelper` class.

            :param channels:
                * channels to be measured during the measurement
                * sequential and parallel channels together these are automatically split
            :param impedance_configurations:
                * parallel sampled channels
                * as a list of lists from which impedances are calculated
                * in the sub list, the first element (index 0) divided by the second element (index 1) is used for the impedance calculation
            :param output_potentiostats: potentiostat on which the measurement is to be output


        3. __init__(self: zahner_link._zahner_link.control.SetHardwareSettingsJob, channels: collections.abc.Sequence[zahner_link._zahner_link.Channel], impedance_configurations: collections.abc.Sequence[zahner_link._zahner_link.ImpedanceConfiguration], output_potentiostats: collections.abc.Sequence[str]) -> None


            Set hardware settings for sampling job.

            Only the necessary channels should be measured, not simply all of them.
            As the sampling rate decreases slightly with each channel, less averaging can be performed.

            This class should be used in combination with the :class:`zahner_link.HardwareSettingsHelper` class.

            :param channels:
                * channels to be measured during the measurement
                * sequential and parallel channels together these are automatically split
            :param impedance_configurations:
                * parallel sampled channels
                * as a list of lists from which impedances are calculated
                * in the sub list, the first element (index 0) divided by the second element (index 1) is used for the impedance calculation
            :param output_potentiostats: potentiostat on which the measurement is to be output


        4. __init__(self: zahner_link._zahner_link.control.SetHardwareSettingsJob, config: zahner_link._zahner_link.UserHardwareSettings) -> None


            Set hardware settings for sampling job.

            The :class:`zahner_link.HardwareSettingsHelper` class returns a :class:`zahner_link.UserHardwareSettings` object, which can be passed to this class.

            :param config: object with the settings

        '''
    @overload
    def __init__(self, channels: collections.abc.Sequence[zahner_link._zahner_link.Channel], impedance_configurations: collections.abc.Sequence[zahner_link._zahner_link.ImpedanceConfiguration], output_potentiostats: collections.abc.Sequence[str]) -> None:
        '''__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.control.SetHardwareSettingsJob, settings: SetHardwareSettingsParameters) -> None


            Set hardware settings for sampling job.

            Only the necessary channels should be measured, not simply all of them.
            As the sampling rate decreases slightly with each channel, less averaging can be performed.

            This class should be used in combination with the :class:`zahner_link.HardwareSettingsHelper` class.

            :param settings: object with the settings

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "set_hardware_settings",
                      "parameters": {
                        "output_potentiostats": [
                            {
                                "uri": "MAIN:1:POT",
                                "potentiostatic_polynomial": [
                                    0E0,
                                    1E0
                                ],
                                "galvanostatic_polynomial": [
                                    0E0,
                                    1E0
                                ]
                            }
                        ],
                        "channels": [
                            {
                                "uri": "MAIN:1:POT:U~PAD:1:PAD_U",
                                "dimension": "voltage",
                                "unit": "V",
                                "polynomial": [
                                    0E0,
                                    1E0
                                ]
                            },
                            {
                                "uri": "MAIN:1:POT:I~PAD:1:PAD_I",
                                "dimension": "current",
                                "unit": "A",
                                "polynomial": [
                                    0E0,
                                    1E0
                                ]
                            }
                        ],
                        "impedance_configurations": [
                            {
                            "numerator": "MAIN:1:POT:U~PAD:1:PAD_U",
                            "denominator": "MAIN:1:POT:I~PAD:1:PAD_I"
                            }
                        ]
                      }
                    },
                    "request_id": "set-hardware-settings-job-uuid-example"
                  }


        2. __init__(self: zahner_link._zahner_link.control.SetHardwareSettingsJob, channels: collections.abc.Sequence[zahner_link._zahner_link.Channel], impedance_configurations: collections.abc.Sequence[zahner_link._zahner_link.ImpedanceConfiguration], output_potentiostats: collections.abc.Sequence[zahner_link._zahner_link.PotentiostatConfiguration]) -> None


            Set hardware settings for sampling job.

            Only the necessary channels should be measured, not simply all of them.
            As the sampling rate decreases slightly with each channel, less averaging can be performed.

            This class should be used in combination with the :class:`zahner_link.HardwareSettingsHelper` class.

            :param channels:
                * channels to be measured during the measurement
                * sequential and parallel channels together these are automatically split
            :param impedance_configurations:
                * parallel sampled channels
                * as a list of lists from which impedances are calculated
                * in the sub list, the first element (index 0) divided by the second element (index 1) is used for the impedance calculation
            :param output_potentiostats: potentiostat on which the measurement is to be output


        3. __init__(self: zahner_link._zahner_link.control.SetHardwareSettingsJob, channels: collections.abc.Sequence[zahner_link._zahner_link.Channel], impedance_configurations: collections.abc.Sequence[zahner_link._zahner_link.ImpedanceConfiguration], output_potentiostats: collections.abc.Sequence[str]) -> None


            Set hardware settings for sampling job.

            Only the necessary channels should be measured, not simply all of them.
            As the sampling rate decreases slightly with each channel, less averaging can be performed.

            This class should be used in combination with the :class:`zahner_link.HardwareSettingsHelper` class.

            :param channels:
                * channels to be measured during the measurement
                * sequential and parallel channels together these are automatically split
            :param impedance_configurations:
                * parallel sampled channels
                * as a list of lists from which impedances are calculated
                * in the sub list, the first element (index 0) divided by the second element (index 1) is used for the impedance calculation
            :param output_potentiostats: potentiostat on which the measurement is to be output


        4. __init__(self: zahner_link._zahner_link.control.SetHardwareSettingsJob, config: zahner_link._zahner_link.UserHardwareSettings) -> None


            Set hardware settings for sampling job.

            The :class:`zahner_link.HardwareSettingsHelper` class returns a :class:`zahner_link.UserHardwareSettings` object, which can be passed to this class.

            :param config: object with the settings

        '''
    @overload
    def __init__(self, config: zahner_link._zahner_link.UserHardwareSettings) -> None:
        '''__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.control.SetHardwareSettingsJob, settings: SetHardwareSettingsParameters) -> None


            Set hardware settings for sampling job.

            Only the necessary channels should be measured, not simply all of them.
            As the sampling rate decreases slightly with each channel, less averaging can be performed.

            This class should be used in combination with the :class:`zahner_link.HardwareSettingsHelper` class.

            :param settings: object with the settings

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "set_hardware_settings",
                      "parameters": {
                        "output_potentiostats": [
                            {
                                "uri": "MAIN:1:POT",
                                "potentiostatic_polynomial": [
                                    0E0,
                                    1E0
                                ],
                                "galvanostatic_polynomial": [
                                    0E0,
                                    1E0
                                ]
                            }
                        ],
                        "channels": [
                            {
                                "uri": "MAIN:1:POT:U~PAD:1:PAD_U",
                                "dimension": "voltage",
                                "unit": "V",
                                "polynomial": [
                                    0E0,
                                    1E0
                                ]
                            },
                            {
                                "uri": "MAIN:1:POT:I~PAD:1:PAD_I",
                                "dimension": "current",
                                "unit": "A",
                                "polynomial": [
                                    0E0,
                                    1E0
                                ]
                            }
                        ],
                        "impedance_configurations": [
                            {
                            "numerator": "MAIN:1:POT:U~PAD:1:PAD_U",
                            "denominator": "MAIN:1:POT:I~PAD:1:PAD_I"
                            }
                        ]
                      }
                    },
                    "request_id": "set-hardware-settings-job-uuid-example"
                  }


        2. __init__(self: zahner_link._zahner_link.control.SetHardwareSettingsJob, channels: collections.abc.Sequence[zahner_link._zahner_link.Channel], impedance_configurations: collections.abc.Sequence[zahner_link._zahner_link.ImpedanceConfiguration], output_potentiostats: collections.abc.Sequence[zahner_link._zahner_link.PotentiostatConfiguration]) -> None


            Set hardware settings for sampling job.

            Only the necessary channels should be measured, not simply all of them.
            As the sampling rate decreases slightly with each channel, less averaging can be performed.

            This class should be used in combination with the :class:`zahner_link.HardwareSettingsHelper` class.

            :param channels:
                * channels to be measured during the measurement
                * sequential and parallel channels together these are automatically split
            :param impedance_configurations:
                * parallel sampled channels
                * as a list of lists from which impedances are calculated
                * in the sub list, the first element (index 0) divided by the second element (index 1) is used for the impedance calculation
            :param output_potentiostats: potentiostat on which the measurement is to be output


        3. __init__(self: zahner_link._zahner_link.control.SetHardwareSettingsJob, channels: collections.abc.Sequence[zahner_link._zahner_link.Channel], impedance_configurations: collections.abc.Sequence[zahner_link._zahner_link.ImpedanceConfiguration], output_potentiostats: collections.abc.Sequence[str]) -> None


            Set hardware settings for sampling job.

            Only the necessary channels should be measured, not simply all of them.
            As the sampling rate decreases slightly with each channel, less averaging can be performed.

            This class should be used in combination with the :class:`zahner_link.HardwareSettingsHelper` class.

            :param channels:
                * channels to be measured during the measurement
                * sequential and parallel channels together these are automatically split
            :param impedance_configurations:
                * parallel sampled channels
                * as a list of lists from which impedances are calculated
                * in the sub list, the first element (index 0) divided by the second element (index 1) is used for the impedance calculation
            :param output_potentiostats: potentiostat on which the measurement is to be output


        4. __init__(self: zahner_link._zahner_link.control.SetHardwareSettingsJob, config: zahner_link._zahner_link.UserHardwareSettings) -> None


            Set hardware settings for sampling job.

            The :class:`zahner_link.HardwareSettingsHelper` class returns a :class:`zahner_link.UserHardwareSettings` object, which can be passed to this class.

            :param config: object with the settings

        '''

class SetHardwareSettingsParametersPy:
    channels: list[zahner_link._zahner_link.Channel]
    impedance_configurations: list[zahner_link._zahner_link.ImpedanceConfiguration]
    output_potentiostats: list[zahner_link._zahner_link.PotentiostatConfiguration]
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class SetLedColorJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: SetLedColorParametersPy
    @overload
    def __init__(self, red: typing.SupportsInt, green: typing.SupportsInt, blue: typing.SupportsInt) -> None:
        '''__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.control.SetLedColorJob, red: typing.SupportsInt, green: typing.SupportsInt, blue: typing.SupportsInt) -> None


            Set LED Colors using red green and blue values

            Only the color of the lower RGB LED can be set.

            :param red: red value from 0 to 255
            :param green: green value from 0 to 255
            :param blue: blue value from 0 to 255

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "set_led_color",
                      "parameters": {
                        "red": 255,
                        "green": 128,
                        "blue": 0
                      }
                    },
                    "request_id": "set-led-color-job-uuid-example"
                  }


        2. __init__(self: zahner_link._zahner_link.control.SetLedColorJob, led: typing.SupportsInt) -> None


            Set LED Color using integer color values

            Color examples:
            - 0xFF0000 for red
            - 0x00FF00 for green    
            - 0x0000FF for blue
    
            :param led: integer color value for lower LED

        '''
    @overload
    def __init__(self, led: typing.SupportsInt) -> None:
        '''__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.control.SetLedColorJob, red: typing.SupportsInt, green: typing.SupportsInt, blue: typing.SupportsInt) -> None


            Set LED Colors using red green and blue values

            Only the color of the lower RGB LED can be set.

            :param red: red value from 0 to 255
            :param green: green value from 0 to 255
            :param blue: blue value from 0 to 255

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "set_led_color",
                      "parameters": {
                        "red": 255,
                        "green": 128,
                        "blue": 0
                      }
                    },
                    "request_id": "set-led-color-job-uuid-example"
                  }


        2. __init__(self: zahner_link._zahner_link.control.SetLedColorJob, led: typing.SupportsInt) -> None


            Set LED Color using integer color values

            Color examples:
            - 0xFF0000 for red
            - 0x00FF00 for green    
            - 0x0000FF for blue
    
            :param led: integer color value for lower LED

        '''

class SetLedColorParametersPy:
    blue: int
    green: int
    red: int
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class SleepJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: SleepParametersPy
    def __init__(self, duration: typing.SupportsFloat) -> None:
        '''__init__(self: zahner_link._zahner_link.control.SleepJob, duration: typing.SupportsFloat) -> None


            Sleep job

            :param duration: duration of the sleep in seconds

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "sleep",
                      "parameters": {
                        "duration": 2.0
                      }
                    },
                    "request_id": "sleep-job-uuid-example"
                  }

        '''

class SleepParametersPy:
    duration: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class SwitchAllOffJob(zahner_link._zahner_link.AbstractMeasurementJob):
    def __init__(self) -> None:
        '''__init__(self: zahner_link._zahner_link.control.SwitchAllOffJob) -> None


            Switch all potentiostats off job

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "switch_all_off",
                      "parameters": {}
                    },
                    "request_id": "switch-all-off-job-uuid-example"
                  }

        '''

class SwitchOffJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: SwitchOffParametersPy
    def __init__(self, potentiostat: str) -> None:
        '''__init__(self: zahner_link._zahner_link.control.SwitchOffJob, potentiostat: str) -> None


            Switch off job

            :param potentiostat: url or urn of the desired potentiostat

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "switch_off",
                      "parameters": {
                        "potentiostat": "MAIN:1:POT"
                      }
                    },
                    "request_id": "switch-off-job-uuid-example"
                  }

        '''

class SwitchOffParametersPy:
    potentiostat: str
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class SwitchOnJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: SwitchOnParametersPy
    def __init__(self, potentiostat: str, coupling: zahner_link._zahner_link.PotentiostatCoupling, bias: typing.SupportsFloat, voltage_range_index: typing.SupportsInt = ..., compliance_range_index: typing.SupportsInt = ...) -> None:
        '''__init__(self: zahner_link._zahner_link.control.SwitchOnJob, potentiostat: str, coupling: zahner_link._zahner_link.PotentiostatCoupling, bias: typing.SupportsFloat, voltage_range_index: typing.SupportsInt = 0, compliance_range_index: typing.SupportsInt = 0) -> None


            Switch on job

            If the potentiostat was switched on in potentiostatic mode, all primitives are executed in potentiostatic mode.
            If it was switched on in galvanostatic mode, all primitives are executed in galvanostatic mode. In cyclic voltammetry,
            for example, all passed values, such as the reverse vertex values, are currents in galvanostatic mode.

            There are only a few methods that require an explicit operating mode and cannot be performed galvanostatically or potentiostatically.

            Url examples:
    
            * EPC:1:EXT2:POT
            * MAIN:1:POT

            Urn example:

            * 354531:POT

            :param potentiostat: url or urn of the desired potentiostat
            :param coupling: coupling how the potentiostat is operated potentiostatically or galvanostatically
            :param bias: DC value
            :param voltage_range_index: voltage range as index with which to switch on
            :param compliance_range_index: compliance range as index with which to switch on

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "switch_on",
                      "parameters": {
                        "potentiostat": "MAIN:1:POT",
                        "coupling": "POTENTIOSTATIC",
                        "bias": 1.5,
                        "voltage_range_index": 2,
                        "compliance_range_index": 1
                      }
                    },
                    "request_id": "switch-on-job-uuid-example"
                  }

        '''

class SwitchOnParametersPy:
    bias: float
    compliance_range_index: int
    coupling: zahner_link._zahner_link.PotentiostatCoupling
    potentiostat: str
    voltage_range_index: int
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
