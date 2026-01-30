import collections.abc
import enum
import typing
from . import calibration as calibration, control as control, meas as meas, xml as xml
from typing import Callable, ClassVar, overload

class AbstractDataset:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def finished_successfully(self) -> bool:
        """finished_successfully(self: zahner_link._zahner_link.AbstractDataset) -> bool"""
    def get_job_info(self) -> JobInfo:
        """get_job_info(self: zahner_link._zahner_link.AbstractDataset) -> JobInfo


            Get info to the job

            :returns: object with the job info

        """
    def get_row_count(self) -> int:
        """get_row_count(self: zahner_link._zahner_link.AbstractDataset) -> int"""

class AbstractMeasurementJob:
    """
    Abstract base class from which all jobs are derived.
    
    Each job is an instantiation of a C++ template derived from this class.
    """
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_last_job_error_message(self) -> str:
        """get_last_job_error_message(self: zahner_link._zahner_link.AbstractMeasurementJob) -> str


            Get the last job error message when failing.

            The job must have been previously executed using methods such as :meth:`zahner_link.ZahnerLink.do_job` or :meth:`zahner_link.ZahnerLink.do_measurement`.

            :returns: string containing the error message or empty string

        """
    def get_last_job_info(self) -> JobInfo:
        """get_last_job_info(self: zahner_link._zahner_link.AbstractMeasurementJob) -> zahner_link._zahner_link.JobInfo


            Get the info of the last job.

            The job must have been previously executed using methods such as :meth:`zahner_link.ZahnerLink.do_job` or :meth:`zahner_link.ZahnerLink.do_measurement`.

            :returns: object with the job info

        """
    def get_last_job_status(self) -> JobStatusEnum:
        """get_last_job_status(self: zahner_link._zahner_link.AbstractMeasurementJob) -> zahner_link._zahner_link.JobStatusEnum


            Get status of the last job.

            The job must have been previously executed using methods such as :meth:`zahner_link.ZahnerLink.do_job` or :meth:`zahner_link.ZahnerLink.do_measurement`.

            :returns: object with the job status

        """
    def was_successful(self) -> bool:
        """was_successful(self: zahner_link._zahner_link.AbstractMeasurementJob) -> bool


            Get status if the last job was successful.

            The job must have been previously executed using methods such as :meth:`zahner_link.ZahnerLink.do_job` or :meth:`zahner_link.ZahnerLink.do_measurement`.

            :returns: True if job was successful

        """

class BandwidthRange:
    index: int
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class CalibrationDataTypeEnum(enum.Enum):
    """
    Enum which indicates the data type of the calibration data.
    """
    __new__: ClassVar[Callable] = ...
    FLOAT: ClassVar[CalibrationDataTypeEnum] = ...
    FLOAT_VECTOR: ClassVar[CalibrationDataTypeEnum] = ...
    SPECTRA: ClassVar[CalibrationDataTypeEnum] = ...
    STRING: ClassVar[CalibrationDataTypeEnum] = ...
    UNDEFINED: ClassVar[CalibrationDataTypeEnum] = ...
    _generate_next_value_: ClassVar[Callable] = ...
    _hashable_values_: ClassVar[list] = ...
    _member_map_: ClassVar[dict] = ...
    _member_names_: ClassVar[list] = ...
    _member_type_: ClassVar[type[object]] = ...
    _unhashable_values_: ClassVar[list] = ...
    _unhashable_values_map_: ClassVar[dict] = ...
    _use_args_: ClassVar[bool] = ...
    _value2member_map_: ClassVar[dict] = ...
    _value_repr_: ClassVar[None] = ...

class CalibrationTypesEnum(enum.Enum):
    """
    Enum which indicates the type of the calibration.
    """
    __new__: ClassVar[Callable] = ...
    DC: ClassVar[CalibrationTypesEnum] = ...
    DUMP: ClassVar[CalibrationTypesEnum] = ...
    EXTERNAL_POTENTIOSTAT_DC: ClassVar[CalibrationTypesEnum] = ...
    FILTER: ClassVar[CalibrationTypesEnum] = ...
    GAIN: ClassVar[CalibrationTypesEnum] = ...
    LOAD: ClassVar[CalibrationTypesEnum] = ...
    MAIN_SHUNTS_DC: ClassVar[CalibrationTypesEnum] = ...
    MAIN_SHUNT_LOAD: ClassVar[CalibrationTypesEnum] = ...
    MAIN_SHUNT_OPEN: ClassVar[CalibrationTypesEnum] = ...
    MAIN_SHUNT_SHORT: ClassVar[CalibrationTypesEnum] = ...
    MAIN_VOLTAGE_RANGE: ClassVar[CalibrationTypesEnum] = ...
    PAD4_DC_GAIN: ClassVar[CalibrationTypesEnum] = ...
    PAD4_FILTER: ClassVar[CalibrationTypesEnum] = ...
    PAD4_GAIN: ClassVar[CalibrationTypesEnum] = ...
    PAD_FILTER: ClassVar[CalibrationTypesEnum] = ...
    PAD_GAIN: ClassVar[CalibrationTypesEnum] = ...
    REFERENCE_ADC: ClassVar[CalibrationTypesEnum] = ...
    SHUNT_LOAD: ClassVar[CalibrationTypesEnum] = ...
    SHUNT_OPEN: ClassVar[CalibrationTypesEnum] = ...
    SHUNT_REFERENCE: ClassVar[CalibrationTypesEnum] = ...
    SHUNT_SHORT: ClassVar[CalibrationTypesEnum] = ...
    VOLTAGE_RANGE: ClassVar[CalibrationTypesEnum] = ...
    _generate_next_value_: ClassVar[Callable] = ...
    _hashable_values_: ClassVar[list] = ...
    _member_map_: ClassVar[dict] = ...
    _member_names_: ClassVar[list] = ...
    _member_type_: ClassVar[type[object]] = ...
    _unhashable_values_: ClassVar[list] = ...
    _unhashable_values_map_: ClassVar[dict] = ...
    _use_args_: ClassVar[bool] = ...
    _value2member_map_: ClassVar[dict] = ...
    _value_repr_: ClassVar[None] = ...

class CardInfo:
    firmware: str
    hardware: str
    name: str
    serialnumber: str
    symbol: str
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class Channel:
    dimension: str
    polynomial: UserPolynomial
    unit: str
    uri: str
    def __init__(self, *args, **kwargs) -> None:
        """__init__(self: zahner_link._zahner_link.Channel, uri: str, dimension: str, unit: str, polynomial: zahner_link._zahner_link.UserPolynomial) -> None


             Class which contains the settings of a channel.

            :param uri: identifier of the channel as URI
            :param dimension: dimension of the channel
            :param unit: unit of the channel
            :param polynomial:
                * polynomial used to calculate the DC value of this channel
                * it is also included in the impedance calculation

        """

class ColumnHeader:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_dimension(self) -> str:
        """get_dimension(self: zahner_link._zahner_link.ColumnHeader) -> str


            Get the dimension name of the column.

            :returns: dimension name

        """
    def get_unit(self) -> str:
        """get_unit(self: zahner_link._zahner_link.ColumnHeader) -> str


            Get the unit of the column.

            :returns: unit name

        """
    def get_urn(self) -> str:
        """get_urn(self: zahner_link._zahner_link.ColumnHeader) -> str


            Get the urn of the column.

            :returns: urn

        """
    def __eq__(self, arg0: ColumnHeader) -> bool:
        """__eq__(self: zahner_link._zahner_link.ColumnHeader, arg0: zahner_link._zahner_link.ColumnHeader) -> bool"""

class ComplianceRange:
    compliance: float
    index: int
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class CurrentRange:
    current: float
    index: int
    resistance: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class DataSet(AbstractDataset, xml.XmlSerializable):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_job_info(self) -> JobInfo:
        """get_job_info(self: zahner_link._zahner_link.DataSet) -> JobInfo


            Get info to the job

            :returns: object with the job info

        """

class DatasetInfo:
    first_time_value: float
    jobInfo: JobInfo
    job_type: str
    job_type_short: str
    num_rows: int
    type: DatasetType
    def __init__(self) -> None:
        """__init__(self: zahner_link._zahner_link.DatasetInfo) -> None"""

class DatasetType(enum.Enum):
    """
    Enum which indicates the type of the dataset.
    """
    __new__: ClassVar[Callable] = ...
    AC: ClassVar[DatasetType] = ...
    DC: ClassVar[DatasetType] = ...
    _generate_next_value_: ClassVar[Callable] = ...
    _hashable_values_: ClassVar[list] = ...
    _member_map_: ClassVar[dict] = ...
    _member_names_: ClassVar[list] = ...
    _member_type_: ClassVar[type[object]] = ...
    _unhashable_values_: ClassVar[list] = ...
    _unhashable_values_map_: ClassVar[dict] = ...
    _use_args_: ClassVar[bool] = ...
    _value2member_map_: ClassVar[dict] = ...
    _value_repr_: ClassVar[None] = ...

class DcDataset(DataSet):
    EMPTY_TRACK: ClassVar[list[float]] = ...  # read-only
    def __init__(self) -> None:
        """__init__(self: zahner_link._zahner_link.DcDataset) -> None


            Class which contains DC data.

        """
    def append(self, to_append: DcDataset, time_offset: typing.SupportsFloat = ...) -> bool:
        """append(self: zahner_link._zahner_link.DcDataset, to_append: zahner_link._zahner_link.DcDataset, time_offset: typing.SupportsFloat = 0.0) -> bool


            Append a dataset by another.

            :param to_append: dataset to be appended to the data
            :param time_offset: additional offset for the time track
            :returns: true if append was successful

        """
    def get_dc_dimensions(self) -> list[str]:
        """get_dc_dimensions(self: zahner_link._zahner_link.DcDataset) -> list[str]


            Get a list of all track dimension names

            :returns: list with the names

        """
    def get_dc_track(self, dimension: str) -> list[float]:
        """get_dc_track(self: zahner_link._zahner_link.DcDataset, dimension: str) -> list[float]


            Get the data track by a dimension name

            :param dimension: name of the dimension to search in columns
            :returns: list of data points for the track :attr:`DcDataset.EMPTY_TRACK` if the dimension does not exist

        """
    def get_dc_tracks(self) -> dict[str, list[float]]:
        """get_dc_tracks(self: zahner_link._zahner_link.DcDataset) -> dict[str, list[float]]


            Get a dictionary with all tracks

            Keys are a dimension and values are the data as a list of floats.

            :returns: dictionary with the data

        """
    def get_header(self) -> LiveDataHeader:
        """get_header(self: zahner_link._zahner_link.DcDataset) -> zahner_link._zahner_link.LiveDataHeader


            Get the header object

            :returns: header object

        """
    def get_included_datasets(self) -> list[DatasetInfo]:
        """get_included_datasets(self: zahner_link._zahner_link.DcDataset) -> list[zahner_link._zahner_link.DatasetInfo]


            Get included datasets

            :returns: list with pairs. First item type and second item number of rows.

        """
    def get_row_count(self) -> int:
        """get_row_count(self: zahner_link._zahner_link.DcDataset) -> int


            Get number of measured points

            :returns: number of points

        """
    def get_tracks(self) -> list[list[float]]:
        """get_tracks(self: zahner_link._zahner_link.DcDataset) -> list[list[float]]


            Get all data tracks

            :returns: list of lists containing the data points for the tracks

        """
    def index_of(self, column_header: ColumnHeader) -> int:
        """index_of(self: zahner_link._zahner_link.DcDataset, column_header: zahner_link._zahner_link.ColumnHeader) -> int


            Get the index of the column by a header object

            :param column_header: name of the header to search
            :returns: index or -1 if not found

        """
    def index_of_dimension(self, dimension_name: str) -> int:
        """index_of_dimension(self: zahner_link._zahner_link.DcDataset, dimension_name: str) -> int


            Get the index of the column by a dimension name

            :param dimension_name: name of the dimension to search in columns
            :returns: index or -1 if not found

        """
    def index_of_urn(self, urn: str) -> int:
        """index_of_urn(self: zahner_link._zahner_link.DcDataset, urn: str) -> int


            Get the index of the column by a urn

            :param urn: urn to search in columns
            :returns: index or -1 if not found

        """
    def __copy__(self) -> DcDataset:
        """__copy__(self: zahner_link._zahner_link.DcDataset) -> zahner_link._zahner_link.DcDataset"""
    def __deepcopy__(self, arg0: dict) -> DcDataset:
        """__deepcopy__(self: zahner_link._zahner_link.DcDataset, arg0: dict) -> zahner_link._zahner_link.DcDataset"""

class EisDataset(DataSet):
    EMPTY_COMPLEX_TRACK: ClassVar[list[list[float]]] = ...  # read-only
    EMPTY_SPECTRA: ClassVar[list[list[float]]] = ...  # read-only
    EMPTY_TRACK: ClassVar[list[float]] = ...  # read-only
    EMPTY_TRACKWAVE: ClassVar[list[list[float]]] = ...  # read-only
    INVALID_IMPEDANCE_DATA: ClassVar[ImpedanceData] = ...  # read-only
    INVALID_PATH: ClassVar[PathData] = ...  # read-only
    INVALID_POTENTIOSTAT: ClassVar[PotentiostatData] = ...  # read-only
    def __init__(self) -> None:
        """__init__(self: zahner_link._zahner_link.EisDataset) -> None


                Class which contains EIS data.
    
        """
    def append(self, to_append: EisDataset, time_offset: typing.SupportsFloat = ...) -> bool:
        """append(self: zahner_link._zahner_link.EisDataset, to_append: zahner_link._zahner_link.EisDataset, time_offset: typing.SupportsFloat = 0.0) -> bool


            Append a dataset by another

            AFTER THAT OPERATION ALL HELPER OBJECTS ARE INVALID

            :param to_append: dataset to be appended to the data
            :param time_offset: additional offset for the time track
            :returns: true if append was successful

        """
    def get_frequencies(self) -> list[float]:
        """get_frequencies(self: zahner_link._zahner_link.EisDataset) -> list[float]


                Get measured impedance points

                :returns: list with frequencies
    
        """
    @overload
    def get_impedance_data(self, numerator_dimension: str, denominator_dimension: str) -> ImpedanceData:
        """get_impedance_data(*args, **kwargs)
        Overloaded function.

        1. get_impedance_data(self: zahner_link._zahner_link.EisDataset, numerator_dimension: str, denominator_dimension: str) -> zahner_link._zahner_link.ImpedanceData


            Get a :class:`zahner_link.ImpedanceData` object which uses the passed dimension for numerator and denominator

            :param numerator_dimension: dimension of the numerator
            :param denominator_dimension: dimension of the denominator
            :returns: :class:`zahner_link.ImpedanceData` object or :attr:`EisDataset.INVALID_IMPEDANCE_DATA` if it does not exist
    

        2. get_impedance_data(self: zahner_link._zahner_link.EisDataset, dimension: str) -> zahner_link._zahner_link.ImpedanceData


            Get a :class:`zahner_link.ImpedanceData` object which uses the passed dimension    
    
            :param dimension: dimension for which :class:`zahner_link.ImpedanceData` objects are searched for
            :returns: :class:`zahner_link.ImpedanceData` object or :attr:`EisDataset.INVALID_IMPEDANCE_DATA` if it does not exist
    

        3. get_impedance_data(self: zahner_link._zahner_link.EisDataset) -> zahner_link._zahner_link.ImpedanceData


            Get the first :class:`zahner_link.ImpedanceData` object

            :returns: :class:`zahner_link.ImpedanceData` object or :attr:`EisDataset.INVALID_IMPEDANCE_DATA` if it does not exist
    
        """
    @overload
    def get_impedance_data(self, dimension: str) -> ImpedanceData:
        """get_impedance_data(*args, **kwargs)
        Overloaded function.

        1. get_impedance_data(self: zahner_link._zahner_link.EisDataset, numerator_dimension: str, denominator_dimension: str) -> zahner_link._zahner_link.ImpedanceData


            Get a :class:`zahner_link.ImpedanceData` object which uses the passed dimension for numerator and denominator

            :param numerator_dimension: dimension of the numerator
            :param denominator_dimension: dimension of the denominator
            :returns: :class:`zahner_link.ImpedanceData` object or :attr:`EisDataset.INVALID_IMPEDANCE_DATA` if it does not exist
    

        2. get_impedance_data(self: zahner_link._zahner_link.EisDataset, dimension: str) -> zahner_link._zahner_link.ImpedanceData


            Get a :class:`zahner_link.ImpedanceData` object which uses the passed dimension    
    
            :param dimension: dimension for which :class:`zahner_link.ImpedanceData` objects are searched for
            :returns: :class:`zahner_link.ImpedanceData` object or :attr:`EisDataset.INVALID_IMPEDANCE_DATA` if it does not exist
    

        3. get_impedance_data(self: zahner_link._zahner_link.EisDataset) -> zahner_link._zahner_link.ImpedanceData


            Get the first :class:`zahner_link.ImpedanceData` object

            :returns: :class:`zahner_link.ImpedanceData` object or :attr:`EisDataset.INVALID_IMPEDANCE_DATA` if it does not exist
    
        """
    @overload
    def get_impedance_data(self) -> ImpedanceData:
        """get_impedance_data(*args, **kwargs)
        Overloaded function.

        1. get_impedance_data(self: zahner_link._zahner_link.EisDataset, numerator_dimension: str, denominator_dimension: str) -> zahner_link._zahner_link.ImpedanceData


            Get a :class:`zahner_link.ImpedanceData` object which uses the passed dimension for numerator and denominator

            :param numerator_dimension: dimension of the numerator
            :param denominator_dimension: dimension of the denominator
            :returns: :class:`zahner_link.ImpedanceData` object or :attr:`EisDataset.INVALID_IMPEDANCE_DATA` if it does not exist
    

        2. get_impedance_data(self: zahner_link._zahner_link.EisDataset, dimension: str) -> zahner_link._zahner_link.ImpedanceData


            Get a :class:`zahner_link.ImpedanceData` object which uses the passed dimension    
    
            :param dimension: dimension for which :class:`zahner_link.ImpedanceData` objects are searched for
            :returns: :class:`zahner_link.ImpedanceData` object or :attr:`EisDataset.INVALID_IMPEDANCE_DATA` if it does not exist
    

        3. get_impedance_data(self: zahner_link._zahner_link.EisDataset) -> zahner_link._zahner_link.ImpedanceData


            Get the first :class:`zahner_link.ImpedanceData` object

            :returns: :class:`zahner_link.ImpedanceData` object or :attr:`EisDataset.INVALID_IMPEDANCE_DATA` if it does not exist
    
        """
    def get_impedances_data(self) -> dict[tuple[str, str], ImpedanceData]:
        """get_impedances_data(self: zahner_link._zahner_link.EisDataset) -> dict[tuple[str, str], zahner_link._zahner_link.ImpedanceData]


            Get a dictionary with all :class:`zahner_link.ImpedanceData` objects

            Keys are a pair of numerator and denominator dimension and values ar the :class:`zahner_link.ImpedanceData` objects.

            :returns: dictionary with the data
    
        """
    def get_impedances_dimensions(self) -> list[tuple[str, str]]:
        """get_impedances_dimensions(self: zahner_link._zahner_link.EisDataset) -> list[tuple[str, str]]


            Get a list with numerator and denominator dimensions of the impedances

            :returns: list with the dimensions
    
        """
    def get_path_data(self, identifier: str) -> PathData:
        """get_path_data(self: zahner_link._zahner_link.EisDataset, identifier: str) -> zahner_link._zahner_link.PathData


            Get a :class:`PathData` object by identifier

            :param identifier: name of the potentiostat
            :returns: :class:`PathData` object
    
        """
    def get_paths_data(self) -> dict[str, PathData]:
        """get_paths_data(self: zahner_link._zahner_link.EisDataset) -> dict[str, zahner_link._zahner_link.PathData]


            Get a dictionary with all :class:`PathData` objects

            Keys are a dimension names and values the objects.

            :returns: dictionary with the data
    
        """
    def get_paths_dimensions(self) -> list[str]:
        """get_paths_dimensions(self: zahner_link._zahner_link.EisDataset) -> list[str]


            Get a list with all available dimensions

            :returns: list with the dimensions
    
        """
    def get_periods(self) -> list[float]:
        """get_periods(self: zahner_link._zahner_link.EisDataset) -> list[float]


                Get number of measured periods per impedance point

                :returns: list with periods
    
        """
    @overload
    def get_potentiostat_data(self) -> PotentiostatData:
        """get_potentiostat_data(*args, **kwargs)
        Overloaded function.

        1. get_potentiostat_data(self: zahner_link._zahner_link.EisDataset) -> zahner_link._zahner_link.PotentiostatData


            Get the first :class:`PotentiostatData` object

            :returns: :class:`PotentiostatData` object or :attr:`EisDataset.INVALID_POTENTIOSTAT` if the potentiostat does not exist
    

        2. get_potentiostat_data(self: zahner_link._zahner_link.EisDataset, identifier: str) -> zahner_link._zahner_link.PotentiostatData


            Get a :class:`PotentiostatData` by a potentiostat name

            :param identifier: name of the potentiostat
            :returns: :class:`PotentiostatData` object or :attr:`EisDataset.INVALID_POTENTIOSTAT` if the potentiostat does not exist
    
        """
    @overload
    def get_potentiostat_data(self, identifier: str) -> PotentiostatData:
        """get_potentiostat_data(*args, **kwargs)
        Overloaded function.

        1. get_potentiostat_data(self: zahner_link._zahner_link.EisDataset) -> zahner_link._zahner_link.PotentiostatData


            Get the first :class:`PotentiostatData` object

            :returns: :class:`PotentiostatData` object or :attr:`EisDataset.INVALID_POTENTIOSTAT` if the potentiostat does not exist
    

        2. get_potentiostat_data(self: zahner_link._zahner_link.EisDataset, identifier: str) -> zahner_link._zahner_link.PotentiostatData


            Get a :class:`PotentiostatData` by a potentiostat name

            :param identifier: name of the potentiostat
            :returns: :class:`PotentiostatData` object or :attr:`EisDataset.INVALID_POTENTIOSTAT` if the potentiostat does not exist
    
        """
    def get_potentiostats_data(self) -> dict[str, PotentiostatData]:
        """get_potentiostats_data(self: zahner_link._zahner_link.EisDataset) -> dict[str, zahner_link._zahner_link.PotentiostatData]


            Get a dictionary with all :class:`PotentiostatData` objects
    
            Keys are a potentiostats names and values the objects.

            :returns: dictionary with the data
    
        """
    def get_potentiostats_identifiers(self) -> list[str]:
        """get_potentiostats_identifiers(self: zahner_link._zahner_link.EisDataset) -> list[str]


            Get a list with all available potentiostat names

            :returns: list with the names
    
        """
    def get_row_count(self) -> int:
        """get_row_count(self: zahner_link._zahner_link.EisDataset) -> int


                Get number of measured impedance points

                :returns: number points
    
        """
    def get_times(self) -> list[float]:
        """get_times(self: zahner_link._zahner_link.EisDataset) -> list[float]


                Get relative start time per impedance point

                :returns: list with times
    
        """
    def __copy__(self) -> EisDataset:
        """__copy__(self: zahner_link._zahner_link.EisDataset) -> zahner_link._zahner_link.EisDataset"""
    def __deepcopy__(self, arg0: dict) -> EisDataset:
        """__deepcopy__(self: zahner_link._zahner_link.EisDataset, arg0: dict) -> zahner_link._zahner_link.EisDataset"""

class ErrorCodeEnum(enum.Enum):
    """
    Enum which indicates error codes for various operations.
    """
    __new__: ClassVar[Callable] = ...
    CALIBRATION_ERROR: ClassVar[ErrorCodeEnum] = ...
    CALIBRATION_GAIN_CALIB_ERROR: ClassVar[ErrorCodeEnum] = ...
    CALIBRATION_NO_SETTINGS: ClassVar[ErrorCodeEnum] = ...
    CALIBRATION_TYPE_UNKNOWN: ClassVar[ErrorCodeEnum] = ...
    CONNECTION_BROKEN: ClassVar[ErrorCodeEnum] = ...
    CONNECTION_FAILED: ClassVar[ErrorCodeEnum] = ...
    CONNECTION_NOT_ESTABLISHED: ClassVar[ErrorCodeEnum] = ...
    CONNECTION_WAS_CLOSED: ClassVar[ErrorCodeEnum] = ...
    ENDPOINT_NOT_FOUND: ClassVar[ErrorCodeEnum] = ...
    FILE_COULD_NOT_BE_CLOSED: ClassVar[ErrorCodeEnum] = ...
    FILE_COULD_NOT_BE_OPENED: ClassVar[ErrorCodeEnum] = ...
    FILE_COULD_NOT_BE_READ: ClassVar[ErrorCodeEnum] = ...
    FILE_COULD_NOT_BE_WRITTEN: ClassVar[ErrorCodeEnum] = ...
    FILE_IS_EMPTY: ClassVar[ErrorCodeEnum] = ...
    FILE_NOT_FOUND: ClassVar[ErrorCodeEnum] = ...
    HARDWARE_CONFIGURATION_ISSUE: ClassVar[ErrorCodeEnum] = ...
    ID_NOT_FOUND: ClassVar[ErrorCodeEnum] = ...
    INVALID_PARAMETER: ClassVar[ErrorCodeEnum] = ...
    JSON_MALFORMED: ClassVar[ErrorCodeEnum] = ...
    JSON_OBJECT_EXPECTED: ClassVar[ErrorCodeEnum] = ...
    NONE: ClassVar[ErrorCodeEnum] = ...
    OPERATION_TIMED_OUT: ClassVar[ErrorCodeEnum] = ...
    OUT_OF_MEMORY: ClassVar[ErrorCodeEnum] = ...
    PARAMETER_COMBINATION_INVALID: ClassVar[ErrorCodeEnum] = ...
    PARAMETER_CONSTRAINT_VIOLATED: ClassVar[ErrorCodeEnum] = ...
    PARAMETER_FORMAT_INVALID: ClassVar[ErrorCodeEnum] = ...
    PARAMETER_FORMAT_INVALID_HINT: ClassVar[ErrorCodeEnum] = ...
    PARAMETER_IS_NOT_A_NUMBER: ClassVar[ErrorCodeEnum] = ...
    PARAMETER_MISSING: ClassVar[ErrorCodeEnum] = ...
    PARAMETER_RELATIVE_CONSTRAINT_VIOLATED: ClassVar[ErrorCodeEnum] = ...
    PARAMETER_STRING_LENGTH_INVALID: ClassVar[ErrorCodeEnum] = ...
    PARAMETER_SYMBOLIC_PATH_INVALID: ClassVar[ErrorCodeEnum] = ...
    PARAMETER_VALUES_TOO_CLOSE: ClassVar[ErrorCodeEnum] = ...
    PARAMETER_VALUE_TOO_HIGH: ClassVar[ErrorCodeEnum] = ...
    PARAMETER_VALUE_TOO_LOW: ClassVar[ErrorCodeEnum] = ...
    PARAMETER_VECTOR_SIZE_INVALID: ClassVar[ErrorCodeEnum] = ...
    POT_STATUS_MISMATCH: ClassVar[ErrorCodeEnum] = ...
    PREMATURELY_STOPPED: ClassVar[ErrorCodeEnum] = ...
    PROPERTY_OBJECT_MISSING: ClassVar[ErrorCodeEnum] = ...
    PSEUDO_GAL_NEEDS_GAL: ClassVar[ErrorCodeEnum] = ...
    QUEUE_BYPASS_NOT_ALLOWED: ClassVar[ErrorCodeEnum] = ...
    QUEUE_FULL: ClassVar[ErrorCodeEnum] = ...
    RESOURCE_CONTENT_INVALID: ClassVar[ErrorCodeEnum] = ...
    RESOURCE_CREATION_FAILED: ClassVar[ErrorCodeEnum] = ...
    RESOURCE_TYPE_MISMATCH: ClassVar[ErrorCodeEnum] = ...
    SETTINGS_NOT_APPLIED: ClassVar[ErrorCodeEnum] = ...
    SETTING_OK_BUT_NOT_COMMITTED: ClassVar[ErrorCodeEnum] = ...
    STOPPED_MANUALLY: ClassVar[ErrorCodeEnum] = ...
    STOPPED_MANUALLY_BEFORE_RUN: ClassVar[ErrorCodeEnum] = ...
    STOP_CONDITION_MISCONFIGURED: ClassVar[ErrorCodeEnum] = ...
    STOP_CONDITION_TRIGGERED: ClassVar[ErrorCodeEnum] = ...
    TYPE_NAME_UNKNOWN: ClassVar[ErrorCodeEnum] = ...
    UNEXPECTED_EXCEPTION: ClassVar[ErrorCodeEnum] = ...
    UNKNOWN_ERR: ClassVar[ErrorCodeEnum] = ...
    _generate_next_value_: ClassVar[Callable] = ...
    _hashable_values_: ClassVar[list] = ...
    _member_map_: ClassVar[dict] = ...
    _member_names_: ClassVar[list] = ...
    _member_type_: ClassVar[type[object]] = ...
    _unhashable_values_: ClassVar[list] = ...
    _unhashable_values_map_: ClassVar[dict] = ...
    _use_args_: ClassVar[bool] = ...
    _value2member_map_: ClassVar[dict] = ...
    _value_repr_: ClassVar[None] = ...

class ErrorObject:
    """
    Class which contains information about an error.
    """
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_error_code_enum(self) -> ErrorCodeEnum:
        """get_error_code_enum(self: zahner_link._zahner_link.ErrorObject) -> zahner_link._zahner_link.ErrorCodeEnum


            Get the error code enum.

            :returns: error code

        """
    def get_message_format_string(self) -> str:
        """get_message_format_string(self: zahner_link._zahner_link.ErrorObject) -> str


            Get the format string for the error message.

            :returns: format string

        """
    def get_message_formatted(self) -> str:
        """get_message_formatted(self: zahner_link._zahner_link.ErrorObject) -> str


            Get the formatted error message.

            :returns: formatted error message

        """
    def get_message_parameters(self) -> list[bool | float | int | int | str]:
        """get_message_parameters(self: zahner_link._zahner_link.ErrorObject) -> list[bool | float | int | int | str]


            Get the parameters for formatting the error message.

            :returns: list with the parameters

        """
    def __bool__(self) -> bool:
        """__bool__(self: zahner_link._zahner_link.ErrorObject) -> bool


            Convert ErrorObject to boolean.

            :returns: True if the error code is not NONE, False otherwise

        """
    def __eq__(self, arg0: ErrorObject) -> bool:
        """__eq__(self: zahner_link._zahner_link.ErrorObject, arg0: zahner_link._zahner_link.ErrorObject) -> bool


            Compare two ErrorObject instances for equality.

            :returns: True if the objects are equal, False otherwise

        """
    def __ne__(self, arg0: ErrorObject) -> bool:
        """__ne__(self: zahner_link._zahner_link.ErrorObject, arg0: zahner_link._zahner_link.ErrorObject) -> bool


            Compare two ErrorObject instances for inequality.

            :returns: True if the objects are not equal, False otherwise

        """

class ErrorParameter:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class FilterRange:
    enabled: bool
    frequency: float
    index: int
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class GainRange:
    enabled: bool
    index: int
    nominal_gain: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class HardwareInfo:
    cards: list[CardInfo]
    paths: list[PathInfo]
    potentiostats: list[PotentiostatInfo]
    workstation: WorkstationInfo
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def constains_url(self, url: str) -> bool:
        """constains_url(self: zahner_link._zahner_link.HardwareInfo, url: str) -> bool


            Verify that the object contains the url.

            The :class:`zahner_link.DeviceTree` must first be retrieved from the device in order to use this method.

            :param url: urn to check for
            :returns: True if the url exists

        """
    def constains_urn(self, urn: str) -> bool:
        """constains_urn(self: zahner_link._zahner_link.HardwareInfo, urn: str) -> bool


            Verify that the object contains the urn.

            :param urn: urn to check for
            :returns: True if the urn exists

        """
    def convert_url_to_urn(self, url: str) -> str:
        """convert_url_to_urn(self: zahner_link._zahner_link.HardwareInfo, url: str) -> str


            Convert an url to a urn with the device tree.

            :param url: url to convert
            :returns: urn or an empty string

        """
    def convert_urn_to_url(self, urn: str) -> str:
        """convert_urn_to_url(self: zahner_link._zahner_link.HardwareInfo, urn: str) -> str


            Convert an urn to a url with the device tree.

            :param urn: urn to convert
            :returns: url or an empty string

        """

class HardwareSettings:
    """
    Class which contains the settings adopted by the IM7.

    The channels were sorted by the IM7 according to parallel_channels and sequential_channels.
    """
    async_channels: list[Channel]
    impedance_configurations: list[ImpedanceConfiguration]
    output_potentiostats: list[PotentiostatConfiguration]
    sync_channels: list[Channel]
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class HardwareSettingsHelper:
    CHANNELS: ClassVar[str] = ...  # read-only
    IMPEDANCE_CONFIGURATIONS: ClassVar[str] = ...  # read-only
    MAIN_POT: ClassVar[str] = ...  # read-only
    MAIN_POT_I_PAD_I: ClassVar[str] = ...  # read-only
    MAIN_POT_U_PAD_U: ClassVar[str] = ...  # read-only
    OUTPUT_POTENTIOSTATS: ClassVar[str] = ...  # read-only
    PAD_I: ClassVar[str] = ...  # read-only
    PAD_U: ClassVar[str] = ...  # read-only
    SEPARATOR: ClassVar[str] = ...  # read-only
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    @staticmethod
    def get_config_for_main_potentiostat() -> UserHardwareSettings:
        """get_config_for_main_potentiostat() -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration

            U and I channel on the main potentiostat are measured and the impedance is calculated from the two channels.

            :returns: object with the settings

        """
    @staticmethod
    def get_config_for_main_with_sync_channel_impedance(connections: collections.abc.Sequence[Pad4ImpedanceConfiguration]) -> UserHardwareSettings:
        """get_config_for_main_with_sync_channel_impedance(connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4ImpedanceConfiguration]) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for the main potentiostat with impedance between PAD4 channels.
    
            U and I channel on the main potentiostat are measured and the impedance is calculated from the two channels.
            In addition, an impedance is calculated between two PAD4 channels.
    
            :param connections: list with with objects of type Pad4ImpedanceConfiguration which specify the numerator and denominator as Pad4Connection with card index and connector number
            :returns: object with the settings

        """
    @staticmethod
    def get_config_for_main_with_sync_current_channel(connections: collections.abc.Sequence[Pad4Connection]) -> UserHardwareSettings:
        """get_config_for_main_with_sync_current_channel(connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4Connection]) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for the main potentiostat with PAD4 channels.

            U and I channel on the main potentiostat are measured and the impedance is calculated from the two channels.
            In addition, an impedance is calculated between the PAD4 channel as current and the voltage channel of the main potentiostat.

            :param connections: list with PAD4 connections with card index and connector number
            :returns: object with the settings

        """
    @staticmethod
    def get_config_for_main_with_sync_voltage_channel(connections: collections.abc.Sequence[Pad4Connection]) -> UserHardwareSettings:
        """get_config_for_main_with_sync_voltage_channel(connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4Connection]) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for the main potentiostat with PAD4 channels.

            U and I channel on the main potentiostat are measured and the impedance is calculated from the two channels.
            In addition, an impedance is calculated between the PAD4 channel and the current of the main potentiostat.

            :param connections: list with PAD4 connections with card index and connector number
            :returns: object with the settings

        """
    @overload
    @staticmethod
    def get_config_for_potentiostat(pot_serial_number: str) -> UserHardwareSettings:
        """get_config_for_potentiostat(*args, **kwargs)
        Overloaded function.

        1. get_config_for_potentiostat(pot_serial_number: str) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for a potentiostat with a specific serialnumber.

            U and I channel are measured on the potentiostat with the serial number `pot_serial_number` and the impedance is calculated from the two channels.
    
            :param pot_serial_number: serialnumber of the potentiostat as a string
            :returns: object with the settings


        2. get_config_for_potentiostat(pot_connection: zahner_link._zahner_link.PotConnection) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for a potentiostat at a specific EPC slot.

            The U and I channels are measured at the potentiostat with the specified slot on the EPC card, and the impedance is calculated from the two channels.
    
            :param pot_connection: slot of the potentiostat on the EPC card with card index and slot number
            :returns: object with the settings

        """
    @overload
    @staticmethod
    def get_config_for_potentiostat(pot_connection: PotConnection) -> UserHardwareSettings:
        """get_config_for_potentiostat(*args, **kwargs)
        Overloaded function.

        1. get_config_for_potentiostat(pot_serial_number: str) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for a potentiostat with a specific serialnumber.

            U and I channel are measured on the potentiostat with the serial number `pot_serial_number` and the impedance is calculated from the two channels.
    
            :param pot_serial_number: serialnumber of the potentiostat as a string
            :returns: object with the settings


        2. get_config_for_potentiostat(pot_connection: zahner_link._zahner_link.PotConnection) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for a potentiostat at a specific EPC slot.

            The U and I channels are measured at the potentiostat with the specified slot on the EPC card, and the impedance is calculated from the two channels.
    
            :param pot_connection: slot of the potentiostat on the EPC card with card index and slot number
            :returns: object with the settings

        """
    @overload
    @staticmethod
    def get_config_for_potentiostat_with_sync_channel_impedance(pot_serial_number: str, connections: collections.abc.Sequence[Pad4ImpedanceConfiguration]) -> UserHardwareSettings:
        """get_config_for_potentiostat_with_sync_channel_impedance(*args, **kwargs)
        Overloaded function.

        1. get_config_for_potentiostat_with_sync_channel_impedance(pot_serial_number: str, connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4ImpedanceConfiguration]) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for the main potentiostat with impedance between PAD4 channels.
    
            U and I channel are measured on the potentiostat with the serial number `pot_serial_number` and the impedance is
            calculated from the two channels.
            In addition, an impedance is calculated between two PAD4 channels.
    
            :param pot_serial_number: serialnumber of the potentiostat as a string
            :param connections: list with with objects of type Pad4ImpedanceConfiguration which specify the numerator and denominator as Pad4Connection with card index and connector number
            :returns: object with the settings


        2. get_config_for_potentiostat_with_sync_channel_impedance(pot_connection: zahner_link._zahner_link.PotConnection, connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4ImpedanceConfiguration]) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for the main potentiostat with impedance between PAD4 channels.
    
            U and I channel are measured on the potentiostat with the connections `pot_connection` and the impedance is
            calculated from the two channels.
            In addition, an impedance is calculated between two PAD4 channels.
    
            :param pot_connection: slot of the potentiostat on the EPC card with card index and slot number
            :param connections: list with with objects of type Pad4ImpedanceConfiguration which specify the numerator and denominator as Pad4Connection with card index and connector number
            :returns: object with the settings

        """
    @overload
    @staticmethod
    def get_config_for_potentiostat_with_sync_channel_impedance(pot_connection: PotConnection, connections: collections.abc.Sequence[Pad4ImpedanceConfiguration]) -> UserHardwareSettings:
        """get_config_for_potentiostat_with_sync_channel_impedance(*args, **kwargs)
        Overloaded function.

        1. get_config_for_potentiostat_with_sync_channel_impedance(pot_serial_number: str, connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4ImpedanceConfiguration]) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for the main potentiostat with impedance between PAD4 channels.
    
            U and I channel are measured on the potentiostat with the serial number `pot_serial_number` and the impedance is
            calculated from the two channels.
            In addition, an impedance is calculated between two PAD4 channels.
    
            :param pot_serial_number: serialnumber of the potentiostat as a string
            :param connections: list with with objects of type Pad4ImpedanceConfiguration which specify the numerator and denominator as Pad4Connection with card index and connector number
            :returns: object with the settings


        2. get_config_for_potentiostat_with_sync_channel_impedance(pot_connection: zahner_link._zahner_link.PotConnection, connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4ImpedanceConfiguration]) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for the main potentiostat with impedance between PAD4 channels.
    
            U and I channel are measured on the potentiostat with the connections `pot_connection` and the impedance is
            calculated from the two channels.
            In addition, an impedance is calculated between two PAD4 channels.
    
            :param pot_connection: slot of the potentiostat on the EPC card with card index and slot number
            :param connections: list with with objects of type Pad4ImpedanceConfiguration which specify the numerator and denominator as Pad4Connection with card index and connector number
            :returns: object with the settings

        """
    @overload
    @staticmethod
    def get_config_for_potentiostat_with_sync_current_channel(pot_serial_number: str, connections: collections.abc.Sequence[Pad4Connection]) -> UserHardwareSettings:
        """get_config_for_potentiostat_with_sync_current_channel(*args, **kwargs)
        Overloaded function.

        1. get_config_for_potentiostat_with_sync_current_channel(pot_serial_number: str, connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4Connection]) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for a potentiostat with a specific serialnumber and PAD4 channels.

            U and I channel are measured on the potentiostat with the serial number `pot_serial_number` and the impedance is calculated from the two channels.
            In addition, an impedance is calculated between the PAD4 channel as current and the voltage channel of the potentiostat which has the `pot_serial_number`.
    
            :param pot_serial_number: serialnumber of the potentiostat as a string
            :param connections: list with PAD4 connections with card index and connector number
            :returns: object with the settings


        2. get_config_for_potentiostat_with_sync_current_channel(pot_connection: zahner_link._zahner_link.PotConnection, connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4Connection]) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for a potentiostat with a specific serialnumber and PAD4 channels.

            U and I channel are measured on the potentiostat with the connections `pot_connection` and the impedance is calculated from the two channels.
            In addition, an impedance is calculated between the PAD4channel as current and the voltage channel of the potentiostat which has the connections `pot_connection`.

            :param pot_connection: slot of the potentiostat on the EPC card with card index and slot number
            :param connections: list with PAD4 connections with card index and connector number
            :returns: object with the settings

        """
    @overload
    @staticmethod
    def get_config_for_potentiostat_with_sync_current_channel(pot_connection: PotConnection, connections: collections.abc.Sequence[Pad4Connection]) -> UserHardwareSettings:
        """get_config_for_potentiostat_with_sync_current_channel(*args, **kwargs)
        Overloaded function.

        1. get_config_for_potentiostat_with_sync_current_channel(pot_serial_number: str, connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4Connection]) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for a potentiostat with a specific serialnumber and PAD4 channels.

            U and I channel are measured on the potentiostat with the serial number `pot_serial_number` and the impedance is calculated from the two channels.
            In addition, an impedance is calculated between the PAD4 channel as current and the voltage channel of the potentiostat which has the `pot_serial_number`.
    
            :param pot_serial_number: serialnumber of the potentiostat as a string
            :param connections: list with PAD4 connections with card index and connector number
            :returns: object with the settings


        2. get_config_for_potentiostat_with_sync_current_channel(pot_connection: zahner_link._zahner_link.PotConnection, connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4Connection]) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for a potentiostat with a specific serialnumber and PAD4 channels.

            U and I channel are measured on the potentiostat with the connections `pot_connection` and the impedance is calculated from the two channels.
            In addition, an impedance is calculated between the PAD4channel as current and the voltage channel of the potentiostat which has the connections `pot_connection`.

            :param pot_connection: slot of the potentiostat on the EPC card with card index and slot number
            :param connections: list with PAD4 connections with card index and connector number
            :returns: object with the settings

        """
    @overload
    @staticmethod
    def get_config_for_potentiostat_with_sync_voltage_channel(pot_serial_number: str, connections: collections.abc.Sequence[Pad4Connection]) -> UserHardwareSettings:
        """get_config_for_potentiostat_with_sync_voltage_channel(*args, **kwargs)
        Overloaded function.

        1. get_config_for_potentiostat_with_sync_voltage_channel(pot_serial_number: str, connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4Connection]) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for a potentiostat with a specific serialnumber and PAD4 channels.

            U and I channel are measured on the potentiostat with the serial number `pot_serial_number` and the impedance is calculated from the two channels.
            In addition, an impedance is calculated between the PAD4 channel and the current channel of the potentiostat which has the `pot_serial_number`.
    
            :param pot_serial_number: serialnumber of the potentiostat as a string
            :param connections: list with PAD4 connections with card index and connector number
            :returns: object with the settings


        2. get_config_for_potentiostat_with_sync_voltage_channel(pot_connection: zahner_link._zahner_link.PotConnection, connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4Connection]) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for a potentiostat with a specific serialnumber and PAD4 channels.

            U and I channel are measured on the potentiostat with the connections `pot_connection` and the impedance is calculated from the two channels.
            In addition, an impedance is calculated between the PAD4 channel and the current channel of the potentiostat which has the connections `pot_connection`.

            :param pot_connection: slot of the potentiostat on the EPC card with card index and slot number
            :param connections: list with PAD4 connections with card index and connector number
            :returns: object with the settings

        """
    @overload
    @staticmethod
    def get_config_for_potentiostat_with_sync_voltage_channel(pot_connection: PotConnection, connections: collections.abc.Sequence[Pad4Connection]) -> UserHardwareSettings:
        """get_config_for_potentiostat_with_sync_voltage_channel(*args, **kwargs)
        Overloaded function.

        1. get_config_for_potentiostat_with_sync_voltage_channel(pot_serial_number: str, connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4Connection]) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for a potentiostat with a specific serialnumber and PAD4 channels.

            U and I channel are measured on the potentiostat with the serial number `pot_serial_number` and the impedance is calculated from the two channels.
            In addition, an impedance is calculated between the PAD4 channel and the current channel of the potentiostat which has the `pot_serial_number`.
    
            :param pot_serial_number: serialnumber of the potentiostat as a string
            :param connections: list with PAD4 connections with card index and connector number
            :returns: object with the settings


        2. get_config_for_potentiostat_with_sync_voltage_channel(pot_connection: zahner_link._zahner_link.PotConnection, connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4Connection]) -> zahner_link._zahner_link.UserHardwareSettings


            Get the default configuration for a potentiostat with a specific serialnumber and PAD4 channels.

            U and I channel are measured on the potentiostat with the connections `pot_connection` and the impedance is calculated from the two channels.
            In addition, an impedance is calculated between the PAD4 channel and the current channel of the potentiostat which has the connections `pot_connection`.

            :param pot_connection: slot of the potentiostat on the EPC card with card index and slot number
            :param connections: list with PAD4 connections with card index and connector number
            :returns: object with the settings

        """

class ImpedanceConfiguration:
    denominator: str
    numerator: str
    def __init__(self, numerator: str, denominator: str) -> None:
        """__init__(self: zahner_link._zahner_link.ImpedanceConfiguration, numerator: str, denominator: str) -> None


            Class that contains the impedance configuration for a pair of channels.

            Numerator and denominator can be any parallel signal paths in the system. For example, the numerator does not necessarily have to be U.
            For each impedance configuration, the numerator is simply returned divided by the denominator as a complex number,
            which even if impedance is in the name, special cases such as admittance spectra can be measured directly.

            :param numerator: numerator for the impedance calculation
            :param denominator: denominator for the impedance calculation

        """

class ImpedanceData:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_calculated_complex_impedance_track(self) -> list[complex]:
        """get_calculated_complex_impedance_track(self: zahner_link._zahner_link.ImpedanceData) -> list[complex]


            Get the impedance as a list of complex numbers

            Calculates the impedance as complex number from the phase and absolute value.

            :returns: list with the complex numbers
    
        """
    def get_calculated_spectra(self) -> dict[float, complex]:
        """get_calculated_spectra(self: zahner_link._zahner_link.ImpedanceData) -> dict[float, complex]


            Get the spectra as a dictionary with the frequency as key and the complex number as value

            Calculates the impedance as complex number from the phase and absolute value.

            :returns: dictionary with the frequency as key and the complex number as value
    
        """
    def get_denominator_dimension(self) -> str:
        """get_denominator_dimension(self: zahner_link._zahner_link.ImpedanceData) -> str


            Get the name of the denominator dimension of the path

            :returns: dimension name
    
        """
    def get_numerator_dimension(self) -> str:
        """get_numerator_dimension(self: zahner_link._zahner_link.ImpedanceData) -> str


            Get the name of the numerator dimension of the path

            :returns: dimension name
    
        """
    def get_track(self, track_name: str) -> list[float]:
        """get_track(self: zahner_link._zahner_link.ImpedanceData, track_name: str) -> list[float]


            Get a track by a track name
    
            :param track_name: name of the track
            :returns: list with the track data or :attr:`EisDataset.EMPTY_TRACK` if the track name does not exist
    
        """
    def get_track_names(self) -> list[str]:
        """get_track_names(self: zahner_link._zahner_link.ImpedanceData) -> list[str]


            Get a list with all available track names

            :returns: list with the track names
    
        """
    def get_tracks(self) -> dict[str, list[float]]:
        """get_tracks(self: zahner_link._zahner_link.ImpedanceData) -> dict[str, list[float]]


            Get a dictionary with all tracks

            Keys are a dimension and values are the data as a list of floats.

            :returns: dictionary with the data
    
        """
    def __eq__(self, arg0: ImpedanceData) -> bool:
        """__eq__(self: zahner_link._zahner_link.ImpedanceData, arg0: zahner_link._zahner_link.ImpedanceData) -> bool"""
    def __getitem__(self, arg0: str) -> list[float]:
        """__getitem__(self: zahner_link._zahner_link.ImpedanceData, arg0: str) -> list[float]


            Get a track by a track name

            :returns: list with the track data
    
        """

class ImpedanceDataHeader:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_columns(self) -> list[ColumnHeader]:
        """get_columns(self: zahner_link._zahner_link.ImpedanceDataHeader) -> list[zahner_link._zahner_link.ColumnHeader]"""
    def get_denominator_path(self) -> str:
        """get_denominator_path(self: zahner_link._zahner_link.ImpedanceDataHeader) -> str"""
    def get_numerator_path(self) -> str:
        """get_numerator_path(self: zahner_link._zahner_link.ImpedanceDataHeader) -> str"""
    def __eq__(self, arg0: ImpedanceDataHeader) -> bool:
        """__eq__(self: zahner_link._zahner_link.ImpedanceDataHeader, arg0: zahner_link._zahner_link.ImpedanceDataHeader) -> bool"""

class JobInfo:
    """
    Class which contains information about the job.
    """
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_creation_date(self) -> str:
        """get_creation_date(self: zahner_link._zahner_link.JobInfo) -> str


            Get the creation date.
    
            :returns: string with the date

        """
    def get_end_date(self) -> str:
        """get_end_date(self: zahner_link._zahner_link.JobInfo) -> str


            Get the end date.
    
            :returns: string with the date

        """
    def get_error(self) -> ErrorObject:
        """get_error(self: zahner_link._zahner_link.JobInfo) -> zahner_link._zahner_link.ErrorObject


            Get the error object of the job
    
            :returns: object with the error details

        """
    def get_error_message(self) -> str:
        """get_error_message(self: zahner_link._zahner_link.JobInfo) -> str


            Get the error message of the job
    
            :returns: string containing the error message or empty string

        """
    def get_job_id(self) -> str:
        """get_job_id(self: zahner_link._zahner_link.JobInfo) -> str


            Get the ID of the job that was assigned by the IM7.
    
            :returns: string with the id

        """
    def get_start_date(self) -> str:
        """get_start_date(self: zahner_link._zahner_link.JobInfo) -> str


            Get the start date.
    
            :returns: string with the date

        """
    def get_status(self) -> JobStatusEnum:
        """get_status(self: zahner_link._zahner_link.JobInfo) -> zahner_link._zahner_link.JobStatusEnum


            Get the status of the job.
    
            :returns: status object

        """
    def get_status_detail(self) -> JobStatusDetailEnum:
        """get_status_detail(self: zahner_link._zahner_link.JobInfo) -> zahner_link._zahner_link.JobStatusDetailEnum


            Get the detailed status of the job.
    
            :returns: reason object

        """
    def get_status_detail_string(self) -> str:
        """get_status_detail_string(self: zahner_link._zahner_link.JobInfo) -> str


            Get the detailed status of the job as string.
    
            :returns: string with the reason

        """
    def get_status_string(self) -> str:
        """get_status_string(self: zahner_link._zahner_link.JobInfo) -> str


            Get the status of the job as string.
    
            :returns: string with the status

        """
    def get_user_metadata(self) -> dict[str, str]:
        """get_user_metadata(self: zahner_link._zahner_link.JobInfo) -> dict[str, str]


            Get the meta data.
    
            :returns: dict with the data

        """

class JobStatusDetailEnum(enum.Enum):
    """
    An enum that explains the status in more detail.
    """
    __new__: ClassVar[Callable] = ...
    CANCELLED_BEFORE_RUN: ClassVar[JobStatusDetailEnum] = ...
    CONNECTION_LOSS: ClassVar[JobStatusDetailEnum] = ...
    FAILED_TO_CREATE: ClassVar[JobStatusDetailEnum] = ...
    FUNCTIONAL_LIMIT_OCCURRED: ClassVar[JobStatusDetailEnum] = ...
    NOT_CONNECTED: ClassVar[JobStatusDetailEnum] = ...
    NOT_FINISHED: ClassVar[JobStatusDetailEnum] = ...
    RUNTIME_ERROR: ClassVar[JobStatusDetailEnum] = ...
    RUN_TO_COMPLETION: ClassVar[JobStatusDetailEnum] = ...
    SAFETY_LIMIT_OCCURRED: ClassVar[JobStatusDetailEnum] = ...
    STOPPED_BY_USER: ClassVar[JobStatusDetailEnum] = ...
    _generate_next_value_: ClassVar[Callable] = ...
    _hashable_values_: ClassVar[list] = ...
    _member_map_: ClassVar[dict] = ...
    _member_names_: ClassVar[list] = ...
    _member_type_: ClassVar[type[object]] = ...
    _unhashable_values_: ClassVar[list] = ...
    _unhashable_values_map_: ClassVar[dict] = ...
    _use_args_: ClassVar[bool] = ...
    _value2member_map_: ClassVar[dict] = ...
    _value_repr_: ClassVar[None] = ...

class JobStatusEnum(enum.Enum):
    """
    Enum which indicates the status of the job.
    """
    __new__: ClassVar[Callable] = ...
    DELETED: ClassVar[JobStatusEnum] = ...
    FAILED: ClassVar[JobStatusEnum] = ...
    FINISHED: ClassVar[JobStatusEnum] = ...
    PENDING: ClassVar[JobStatusEnum] = ...
    RUNNING: ClassVar[JobStatusEnum] = ...
    UNKNOWN: ClassVar[JobStatusEnum] = ...
    _generate_next_value_: ClassVar[Callable] = ...
    _hashable_values_: ClassVar[list] = ...
    _member_map_: ClassVar[dict] = ...
    _member_names_: ClassVar[list] = ...
    _member_type_: ClassVar[type[object]] = ...
    _unhashable_values_: ClassVar[list] = ...
    _unhashable_values_map_: ClassVar[dict] = ...
    _use_args_: ClassVar[bool] = ...
    _value2member_map_: ClassVar[dict] = ...
    _value_repr_: ClassVar[None] = ...

class LiveDataHeader:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_columns(self) -> list[ColumnHeader]:
        """get_columns(self: zahner_link._zahner_link.LiveDataHeader) -> list[ColumnHeader]


            Get the :class:`zahner_link.ColumnHeader` list of the job.

            The list with :class:`zahner_link.ColumnHeader` objects describe the tracks that were measured in the job.

            :returns: list with the headers of the job

        """
    def get_number_of_columns(self) -> int:
        """get_number_of_columns(self: zahner_link._zahner_link.LiveDataHeader) -> int"""
    def get_short_type(self) -> str:
        """get_short_type(self: zahner_link._zahner_link.LiveDataHeader) -> str"""
    def get_type(self) -> str:
        """get_type(self: zahner_link._zahner_link.LiveDataHeader) -> str"""
    def __eq__(self, arg0: LiveDataHeader) -> bool:
        """__eq__(self: zahner_link._zahner_link.LiveDataHeader, arg0: zahner_link._zahner_link.LiveDataHeader) -> bool"""

class LiveDataHeaderEis(LiveDataHeader):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_async_paths_data_headers(self) -> list[PathDataHeader]:
        """get_async_paths_data_headers(self: zahner_link._zahner_link.LiveDataHeaderEis) -> list[zahner_link._zahner_link.PathDataHeader]


                Get the async headers

                :returns: object with the headers
    
        """
    def get_impedances_headers(self) -> list[ImpedanceDataHeader]:
        """get_impedances_headers(self: zahner_link._zahner_link.LiveDataHeaderEis) -> list[zahner_link._zahner_link.ImpedanceDataHeader]


                Get the impedance headers

                These are the extracted headers from the live data header object.

                :returns: object with the headers
    
        """
    def get_meta_data_header(self) -> list[ColumnHeader]:
        """get_meta_data_header(self: zahner_link._zahner_link.LiveDataHeaderEis) -> list[zahner_link._zahner_link.ColumnHeader]


                Get the meta data headers

                These are the extracted headers from the live data header object.

                :returns: object with the headers
    
        """
    def get_paths_data_headers(self) -> list[PathDataHeader]:
        """get_paths_data_headers(self: zahner_link._zahner_link.LiveDataHeaderEis) -> list[zahner_link._zahner_link.PathDataHeader]


                Get the paths data headers

                These are the extracted headers from the live data header object.

                :returns: object with the headers
    
        """
    def get_potentiostats_data_headers(self) -> list[PotentiostatDataHeader]:
        """get_potentiostats_data_headers(self: zahner_link._zahner_link.LiveDataHeaderEis) -> list[PotentiostatDataHeader]


                Get the potentiostats data headers

                These are the extracted headers from the live data header object.

                :returns: object with the headers
    
        """
    def __eq__(self, arg0: LiveDataHeaderEis) -> bool:
        """__eq__(self: zahner_link._zahner_link.LiveDataHeaderEis, arg0: zahner_link._zahner_link.LiveDataHeaderEis) -> bool"""

class Pad4Connection:
    card_index: int
    connector_index: int
    dimension: str
    polynomial: UserPolynomial
    unit: str
    def __init__(self, card_index: typing.SupportsInt, connector_index: typing.SupportsInt, polynomial: UserPolynomial = ..., dimension: str = ..., unit: str = ...) -> None:
        """__init__(self: zahner_link._zahner_link.Pad4Connection, card_index: typing.SupportsInt, connector_index: typing.SupportsInt, polynomial: zahner_link._zahner_link.UserPolynomial = <zahner_link._zahner_link.UserPolynomial object at 0x7939a1b31930>, dimension: str = '', unit: str = '') -> None


            Class which contains the settings of a PAD4 channel.

            :param card_index: index of the PAD4 card
            :param connector_index: index of the connector on the PAD4 card
            :param polynomial:
                * polynomial used to calculate the DC value of this channel
                * it is also included in the impedance calculation
            :param dimension: dimension of the channel
            :param unit: unit of the channel

        """
    def getPath(self) -> str:
        """getPath(self: zahner_link._zahner_link.Pad4Connection) -> str


            Get the path of the PAD4 as string.
    
            :returns: the path as string

        """
    def __lt__(self, arg0: Pad4Connection) -> bool:
        """__lt__(self: zahner_link._zahner_link.Pad4Connection, arg0: zahner_link._zahner_link.Pad4Connection) -> bool"""

class Pad4ImpedanceConfiguration:
    denominator: Pad4Connection
    numerator: Pad4Connection
    def __init__(self, numerator: Pad4Connection, denominator: Pad4Connection) -> None:
        """__init__(self: zahner_link._zahner_link.Pad4ImpedanceConfiguration, numerator: Pad4Connection, denominator: Pad4Connection) -> None


            Class that contains the impedance configuration for a pair of PAD4 channels.

            :param numerator: numerator for the impedance calculation
            :param denominator: denominator for the impedance calculation

        """

class PathData:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_dc_track(self) -> list[float]:
        """get_dc_track(self: zahner_link._zahner_link.PathData) -> list[float]


            Get a track with the dc data
    
            :returns: list with the track data or :attr:`EisDataset.EMPTY_TRACK` if the track name does not exist
    
        """
    def get_dimension(self) -> str:
        """get_dimension(self: zahner_link._zahner_link.PathData) -> str


            Get the name of the dimension of the path

            :returns: dimension name
    
        """
    @overload
    def get_impedance_data(self, dimension: str) -> ImpedanceData:
        """get_impedance_data(*args, **kwargs)
        Overloaded function.

        1. get_impedance_data(self: zahner_link._zahner_link.PathData, dimension: str) -> zahner_link._zahner_link.ImpedanceData


            Get a :class:`zahner_link.ImpedanceData` object which uses this PathInfo and the passed dimension    

            :param dimension: dimension for which :class:`zahner_link.ImpedanceData` objects are searched for
            :returns: :class:`zahner_link.ImpedanceData` object or :attr:`EisDataset.INVALID_IMPEDANCE_DATA` if it does not exist
    

        2. get_impedance_data(self: zahner_link._zahner_link.PathData) -> zahner_link._zahner_link.ImpedanceData


            Get the first :class:`zahner_link.ImpedanceData` object

            :returns: :class:`zahner_link.ImpedanceData` object or :attr:`EisDataset.INVALID_IMPEDANCE_DATA` if it does not exist
    
        """
    @overload
    def get_impedance_data(self) -> ImpedanceData:
        """get_impedance_data(*args, **kwargs)
        Overloaded function.

        1. get_impedance_data(self: zahner_link._zahner_link.PathData, dimension: str) -> zahner_link._zahner_link.ImpedanceData


            Get a :class:`zahner_link.ImpedanceData` object which uses this PathInfo and the passed dimension    

            :param dimension: dimension for which :class:`zahner_link.ImpedanceData` objects are searched for
            :returns: :class:`zahner_link.ImpedanceData` object or :attr:`EisDataset.INVALID_IMPEDANCE_DATA` if it does not exist
    

        2. get_impedance_data(self: zahner_link._zahner_link.PathData) -> zahner_link._zahner_link.ImpedanceData


            Get the first :class:`zahner_link.ImpedanceData` object

            :returns: :class:`zahner_link.ImpedanceData` object or :attr:`EisDataset.INVALID_IMPEDANCE_DATA` if it does not exist
    
        """
    def get_impedances_data(self) -> dict[tuple[str, str], ImpedanceData]:
        """get_impedances_data(self: zahner_link._zahner_link.PathData) -> dict[tuple[str, str], zahner_link._zahner_link.ImpedanceData]


            Get a dictionary with all :class:`zahner_link.ImpedanceData` objects which use this path

            Keys are a pair of numerator and denominator dimension and values ar the :class:`zahner_link.ImpedanceData` objects.

            :returns: dictionary with the data
    
        """
    def get_track(self, track_name: str) -> list[float]:
        """get_track(self: zahner_link._zahner_link.PathData, track_name: str) -> list[float]


            Get a track by a track name
    
            :param track_name: name of the track
            :returns: list with the track data or :attr:`EisDataset.EMPTY_TRACK` if the track name does not exist
    
        """
    def get_track_names(self) -> list[str]:
        """get_track_names(self: zahner_link._zahner_link.PathData) -> list[str]


            Get a list with all available track names

            :returns: list with the track names
    
        """
    def get_tracks(self) -> dict[str, list[float]]:
        """get_tracks(self: zahner_link._zahner_link.PathData) -> dict[str, list[float]]


            Get a dictionary with all tracks

            Keys are a dimension and values are the data as a list of floats.

            :returns: dictionary with the data
    
        """
    def get_waves(self) -> list[list[float]]:
        """get_waves(self: zahner_link._zahner_link.PathData) -> list[list[float]]


            Get the waves of the path

            The first dimension of the list is the spectra.
            Each list contains a list with the values of the wave.

            :returns: list with the waves
    
        """
    def __eq__(self, arg0: PathData) -> bool:
        """__eq__(self: zahner_link._zahner_link.PathData, arg0: zahner_link._zahner_link.PathData) -> bool"""
    def __getitem__(self, arg0: str) -> list[float]:
        """__getitem__(self: zahner_link._zahner_link.PathData, arg0: str) -> list[float]


            Get a track by a track name

            :returns: list with the track data
    
        """

class PathDataHeader:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_columns(self) -> list[ColumnHeader]:
        """get_columns(self: zahner_link._zahner_link.PathDataHeader) -> list[zahner_link._zahner_link.ColumnHeader]


                Get the paths headers

                These are the extracted headers from the live data header object.

                :returns: object with the headers
    
        """
    def get_polynomial(self) -> UserPolynomial:
        """get_polynomial(self: zahner_link._zahner_link.PathDataHeader) -> UserPolynomial"""
    def get_uri(self) -> str:
        """get_uri(self: zahner_link._zahner_link.PathDataHeader) -> str"""
    def get_wave_size(self) -> int:
        """get_wave_size(self: zahner_link._zahner_link.PathDataHeader) -> int"""
    def __eq__(self, arg0: PathDataHeader) -> bool:
        """__eq__(self: zahner_link._zahner_link.PathDataHeader, arg0: zahner_link._zahner_link.PathDataHeader) -> bool"""

class PathInfo:
    filter_ranges: list[FilterRange]
    gain_ranges: list[GainRange]
    relevance: float
    sampling: str
    source: str
    url: str
    urn: str
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class PotConnection:
    card_index: int
    connector_index: int
    def __init__(self, card_index: typing.SupportsInt, connector_index: typing.SupportsInt) -> None:
        """__init__(self: zahner_link._zahner_link.PotConnection, card_index: typing.SupportsInt, connector_index: typing.SupportsInt) -> None


            Class which describes the connection of a potentiostat to an EPC card.

            :param card_index: index of the card to which the potentiostat is connected
            :param connector_index: index of the connector on the card to which the potentiostat is connected

        """

class PotentiostatConfiguration:
    galvanostatic_polynomial: UserPolynomial
    potentiostatic_polynomial: UserPolynomial
    uri: str
    def __init__(self, uri: str, potentiostatic_polynomial: object = ..., galvanostatic_polynomial: object = ...) -> None:
        """__init__(self: zahner_link._zahner_link.PotentiostatConfiguration, uri: str, potentiostatic_polynomial: object = [0.0, 1.0], galvanostatic_polynomial: object = [0.0, 1.0]) -> None


            Class that contains the impedance configuration for a pair of channels.

            Numerator and denominator can be any parallel signal paths in the system. For example, the numerator does not necessarily have to be U.
            For each impedance configuration, the numerator is simply returned divided by the denominator as a complex number,
            which even if impedance is in the name, special cases such as admittance spectra can be measured directly.

            :param uri: identifier of the potentiostat as URI
            :param potentiostatic_polynomial: polynomial to calculate potentiostatic output for reference electrode and FRA
            :param galvanostatic_polynomial: polynomial to calculate galvanostatic output for FRA

        """
    def __assign__(self, arg0: str) -> PotentiostatConfiguration:
        """__assign__(self: zahner_link._zahner_link.PotentiostatConfiguration, arg0: str) -> zahner_link._zahner_link.PotentiostatConfiguration"""

class PotentiostatCoupling(enum.Enum):
    """
    Enum with which you can select the feedback mode.
    """
    __new__: ClassVar[Callable] = ...
    GALVANOSTATIC: ClassVar[PotentiostatCoupling] = ...
    POTENTIOSTATIC: ClassVar[PotentiostatCoupling] = ...
    _generate_next_value_: ClassVar[Callable] = ...
    _hashable_values_: ClassVar[list] = ...
    _member_map_: ClassVar[dict] = ...
    _member_names_: ClassVar[list] = ...
    _member_type_: ClassVar[type[object]] = ...
    _unhashable_values_: ClassVar[list] = ...
    _unhashable_values_map_: ClassVar[dict] = ...
    _use_args_: ClassVar[bool] = ...
    _value2member_map_: ClassVar[dict] = ...
    _value_repr_: ClassVar[None] = ...

class PotentiostatData:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def get_identifier(self) -> str:
        """get_identifier(self: zahner_link._zahner_link.PotentiostatData) -> str


            Get the name of the potentiostat

            :returns: name of the potentiostat
    
        """
    def get_track(self, track_name: str) -> list[float]:
        """get_track(self: zahner_link._zahner_link.PotentiostatData, track_name: str) -> list[float]


            Get a track by a track name
    
            :param track_name: name of the track
            :returns: list with the track data or :attr:`EisDataset.EMPTY_TRACK` if the track name does not exist
    
        """
    def get_track_names(self) -> list[str]:
        """get_track_names(self: zahner_link._zahner_link.PotentiostatData) -> list[str]


            Get a list with all available track names

            :returns: list with the track names
    
        """
    def get_tracks(self) -> dict[str, list[float]]:
        """get_tracks(self: zahner_link._zahner_link.PotentiostatData) -> dict[str, list[float]]


            Get a dictionary with all tracks

            Keys are a dimension and values are the data as a list of floats.

            :returns: dictionary with the data
    
        """
    def __eq__(self, arg0: PotentiostatData) -> bool:
        """__eq__(self: zahner_link._zahner_link.PotentiostatData, arg0: zahner_link._zahner_link.PotentiostatData) -> bool"""
    def __getitem__(self, arg0: str) -> list[float]:
        """__getitem__(self: zahner_link._zahner_link.PotentiostatData, arg0: str) -> list[float]


            Get a track by a track name

            :returns: list with the track data
    
        """

class PotentiostatInfo:
    bandwidth_ranges: list[BandwidthRange]
    compliance_ranges: list[ComplianceRange]
    current_ranges: list[CurrentRange]
    dac_resolution: int
    has_calibration_data: bool
    identifier: str
    serialnumber: str
    software: str
    url: str
    urn: str
    voltage_ranges: list[VoltageRange]
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class QueueStopModeEnum(enum.Enum):
    """
    Enum with which you can select what should happen when the criteria is met.
    """
    __new__: ClassVar[Callable] = ...
    QUEUE_STOP_MODE_CONTINUE: ClassVar[QueueStopModeEnum] = ...
    QUEUE_STOP_MODE_FLUSH: ClassVar[QueueStopModeEnum] = ...
    _generate_next_value_: ClassVar[Callable] = ...
    _hashable_values_: ClassVar[list] = ...
    _member_map_: ClassVar[dict] = ...
    _member_names_: ClassVar[list] = ...
    _member_type_: ClassVar[type[object]] = ...
    _unhashable_values_: ClassVar[list] = ...
    _unhashable_values_map_: ClassVar[dict] = ...
    _use_args_: ClassVar[bool] = ...
    _value2member_map_: ClassVar[dict] = ...
    _value_repr_: ClassVar[None] = ...

class Resource:
    DATA_CHUNK_SIZE_LIMIT: ClassVar[int] = ...  # read-only
    def __init__(self) -> None:
        """__init__(self: zahner_link._zahner_link.Resource) -> None"""
    @staticmethod
    def from_id(type: ResourceTypeEnum, resource_id: str) -> Resource:
        """from_id(type: ResourceTypeEnum, resource_id: str) -> zahner_link._zahner_link.Resource"""
    def get_creation_date(self) -> str:
        """get_creation_date(self: zahner_link._zahner_link.Resource) -> str"""
    def get_id(self) -> str:
        """get_id(self: zahner_link._zahner_link.Resource) -> str"""
    def get_last_updated_date(self) -> str:
        """get_last_updated_date(self: zahner_link._zahner_link.Resource) -> str"""
    def get_name(self) -> str:
        """get_name(self: zahner_link._zahner_link.Resource) -> str"""
    def get_size(self) -> int:
        """get_size(self: zahner_link._zahner_link.Resource) -> int"""
    def get_type(self) -> ResourceTypeEnum:
        """get_type(self: zahner_link._zahner_link.Resource) -> ResourceTypeEnum"""
    def is_valid(self) -> bool:
        """is_valid(self: zahner_link._zahner_link.Resource) -> bool"""

class ResourceTypeEnum(enum.Enum):
    """
    Enum which indicates the type of the resource.
    """
    __new__: ClassVar[Callable] = ...
    CALIB_MESH: ClassVar[ResourceTypeEnum] = ...
    ISC: ClassVar[ResourceTypeEnum] = ...
    UNDEFINED: ClassVar[ResourceTypeEnum] = ...
    WAVE: ClassVar[ResourceTypeEnum] = ...
    _generate_next_value_: ClassVar[Callable] = ...
    _hashable_values_: ClassVar[list] = ...
    _member_map_: ClassVar[dict] = ...
    _member_names_: ClassVar[list] = ...
    _member_type_: ClassVar[type[object]] = ...
    _unhashable_values_: ClassVar[list] = ...
    _unhashable_values_map_: ClassVar[dict] = ...
    _use_args_: ClassVar[bool] = ...
    _value2member_map_: ClassVar[dict] = ...
    _value_repr_: ClassVar[None] = ...

class Setting:
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.Setting) -> None


            A setting that can hold different types of values


        2. __init__(self: zahner_link._zahner_link.Setting, value: str) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: String value to store


        3. __init__(self: zahner_link._zahner_link.Setting, value: str) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: C string value to store


        4. __init__(self: zahner_link._zahner_link.Setting, value: bool) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Boolean value to store


        5. __init__(self: zahner_link._zahner_link.Setting, value: typing.SupportsInt) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Integer value to store


        6. __init__(self: zahner_link._zahner_link.Setting, value: typing.SupportsFloat) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Double value to store

        """
    @overload
    def __init__(self, value: str) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.Setting) -> None


            A setting that can hold different types of values


        2. __init__(self: zahner_link._zahner_link.Setting, value: str) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: String value to store


        3. __init__(self: zahner_link._zahner_link.Setting, value: str) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: C string value to store


        4. __init__(self: zahner_link._zahner_link.Setting, value: bool) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Boolean value to store


        5. __init__(self: zahner_link._zahner_link.Setting, value: typing.SupportsInt) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Integer value to store


        6. __init__(self: zahner_link._zahner_link.Setting, value: typing.SupportsFloat) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Double value to store

        """
    @overload
    def __init__(self, value: str) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.Setting) -> None


            A setting that can hold different types of values


        2. __init__(self: zahner_link._zahner_link.Setting, value: str) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: String value to store


        3. __init__(self: zahner_link._zahner_link.Setting, value: str) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: C string value to store


        4. __init__(self: zahner_link._zahner_link.Setting, value: bool) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Boolean value to store


        5. __init__(self: zahner_link._zahner_link.Setting, value: typing.SupportsInt) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Integer value to store


        6. __init__(self: zahner_link._zahner_link.Setting, value: typing.SupportsFloat) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Double value to store

        """
    @overload
    def __init__(self, value: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.Setting) -> None


            A setting that can hold different types of values


        2. __init__(self: zahner_link._zahner_link.Setting, value: str) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: String value to store


        3. __init__(self: zahner_link._zahner_link.Setting, value: str) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: C string value to store


        4. __init__(self: zahner_link._zahner_link.Setting, value: bool) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Boolean value to store


        5. __init__(self: zahner_link._zahner_link.Setting, value: typing.SupportsInt) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Integer value to store


        6. __init__(self: zahner_link._zahner_link.Setting, value: typing.SupportsFloat) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Double value to store

        """
    @overload
    def __init__(self, value: typing.SupportsInt) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.Setting) -> None


            A setting that can hold different types of values


        2. __init__(self: zahner_link._zahner_link.Setting, value: str) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: String value to store


        3. __init__(self: zahner_link._zahner_link.Setting, value: str) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: C string value to store


        4. __init__(self: zahner_link._zahner_link.Setting, value: bool) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Boolean value to store


        5. __init__(self: zahner_link._zahner_link.Setting, value: typing.SupportsInt) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Integer value to store


        6. __init__(self: zahner_link._zahner_link.Setting, value: typing.SupportsFloat) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Double value to store

        """
    @overload
    def __init__(self, value: typing.SupportsFloat) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.Setting) -> None


            A setting that can hold different types of values


        2. __init__(self: zahner_link._zahner_link.Setting, value: str) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: String value to store


        3. __init__(self: zahner_link._zahner_link.Setting, value: str) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: C string value to store


        4. __init__(self: zahner_link._zahner_link.Setting, value: bool) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Boolean value to store


        5. __init__(self: zahner_link._zahner_link.Setting, value: typing.SupportsInt) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Integer value to store


        6. __init__(self: zahner_link._zahner_link.Setting, value: typing.SupportsFloat) -> None


            A setting that can hold different types of values
    
            This class represents a single configuration setting that can store boolean, integer, 
            double or string values with automatic type management.
    
            :param value: Double value to store

        """
    def as_string(self) -> str:
        """as_string(self: zahner_link._zahner_link.Setting) -> str


            Convert value to string representation
    
            :returns: String representation of the value

        """
    def assign_bool(self, value: bool) -> Setting:
        """assign_bool(self: zahner_link._zahner_link.Setting, value: bool) -> zahner_link._zahner_link.Setting


            Assign boolean value
    
            :param value: Boolean value to assign
            :returns: Reference to self

        """
    def assign_double(self, value: typing.SupportsFloat) -> Setting:
        """assign_double(self: zahner_link._zahner_link.Setting, value: typing.SupportsFloat) -> zahner_link._zahner_link.Setting


            Assign double value
    
            :param value: Double value to assign
            :returns: Reference to self

        """
    def assign_int(self, value: typing.SupportsInt) -> Setting:
        """assign_int(self: zahner_link._zahner_link.Setting, value: typing.SupportsInt) -> zahner_link._zahner_link.Setting


            Assign integer value
    
            :param value: Integer value to assign
            :returns: Reference to self

        """
    def assign_string(self, value: str) -> Setting:
        """assign_string(self: zahner_link._zahner_link.Setting, value: str) -> zahner_link._zahner_link.Setting


            Assign string value
    
            :param value: String value to assign
            :returns: Reference to self

        """
    def get_bool_value(self) -> bool:
        """get_bool_value(self: zahner_link._zahner_link.Setting) -> bool


            Get boolean value
    
            :returns: Boolean value

        """
    def get_double_value(self) -> float:
        """get_double_value(self: zahner_link._zahner_link.Setting) -> float


            Get double value
    
            :returns: Double value

        """
    def get_int_value(self) -> int:
        """get_int_value(self: zahner_link._zahner_link.Setting) -> int


            Get integer value
    
            :returns: Integer value

        """
    def get_string_value(self) -> str:
        """get_string_value(self: zahner_link._zahner_link.Setting) -> str


            Get string value
    
            :returns: String value

        """
    def get_type(self) -> SettingType:
        """get_type(self: zahner_link._zahner_link.Setting) -> zahner_link._zahner_link.SettingType


            Get the type of the setting
    
            :returns: :class:`zahner_link.SettingType` enum value

        """
    def get_update_failure_reason(self) -> ErrorObject:
        """get_update_failure_reason(self: zahner_link._zahner_link.Setting) -> zahner_link._zahner_link.ErrorObject


            Get reason for update failure
    
            :returns: :class:`zahner_link.ErrorObject` with failure reason

        """
    def successfully_updated(self) -> bool:
        """successfully_updated(self: zahner_link._zahner_link.Setting) -> bool


            Check if setting was successfully updated
    
            :returns: True if setting was successfully updated

        """
    def __copy__(self) -> Setting:
        """__copy__(self: zahner_link._zahner_link.Setting) -> zahner_link._zahner_link.Setting


            Shallow copy of the setting
    
            :returns: Copy of the setting

        """
    def __deepcopy__(self, memo: dict) -> Setting:
        """__deepcopy__(self: zahner_link._zahner_link.Setting, memo: dict) -> zahner_link._zahner_link.Setting


            Deep copy of the setting
    
            :param memo: Memoization dictionary (unused)
            :returns: Deep copy of the setting

        """

class SettingType(enum.Enum):
    """
    Type enumeration for Setting values
    """
    __new__: ClassVar[Callable] = ...
    BOOL: ClassVar[SettingType] = ...
    DOUBLE: ClassVar[SettingType] = ...
    INT: ClassVar[SettingType] = ...
    STRING: ClassVar[SettingType] = ...
    UNINITIALIZED: ClassVar[SettingType] = ...
    _generate_next_value_: ClassVar[Callable] = ...
    _hashable_values_: ClassVar[list] = ...
    _member_map_: ClassVar[dict] = ...
    _member_names_: ClassVar[list] = ...
    _member_type_: ClassVar[type[object]] = ...
    _unhashable_values_: ClassVar[list] = ...
    _unhashable_values_map_: ClassVar[dict] = ...
    _use_args_: ClassVar[bool] = ...
    _value2member_map_: ClassVar[dict] = ...
    _value_repr_: ClassVar[None] = ...

class SettingsSet:
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.SettingsSet) -> None


            Create an empty settings set


        2. __init__(self: zahner_link._zahner_link.SettingsSet, settings: collections.abc.Sequence[tuple[str, zahner_link._zahner_link.Setting]]) -> None


            Create settings set from vector of name and :class:`Setting` pairs
    
            :param settings: Vector of (key, :class:`Setting`) pairs


        3. __init__(self: zahner_link._zahner_link.SettingsSet, settings: collections.abc.Sequence[tuple[str, object]]) -> None


            Create settings set from Python list of (key, value) pairs
    
            Automatically converts Python values to appropriate Setting types.
    
            :param settings: List of (key, value) tuples where values can be bool, int, float, or str

        """
    @overload
    def __init__(self, settings: collections.abc.Sequence[tuple[str, Setting]]) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.SettingsSet) -> None


            Create an empty settings set


        2. __init__(self: zahner_link._zahner_link.SettingsSet, settings: collections.abc.Sequence[tuple[str, zahner_link._zahner_link.Setting]]) -> None


            Create settings set from vector of name and :class:`Setting` pairs
    
            :param settings: Vector of (key, :class:`Setting`) pairs


        3. __init__(self: zahner_link._zahner_link.SettingsSet, settings: collections.abc.Sequence[tuple[str, object]]) -> None


            Create settings set from Python list of (key, value) pairs
    
            Automatically converts Python values to appropriate Setting types.
    
            :param settings: List of (key, value) tuples where values can be bool, int, float, or str

        """
    @overload
    def __init__(self, settings: collections.abc.Sequence[tuple[str, object]]) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.SettingsSet) -> None


            Create an empty settings set


        2. __init__(self: zahner_link._zahner_link.SettingsSet, settings: collections.abc.Sequence[tuple[str, zahner_link._zahner_link.Setting]]) -> None


            Create settings set from vector of name and :class:`Setting` pairs
    
            :param settings: Vector of (key, :class:`Setting`) pairs


        3. __init__(self: zahner_link._zahner_link.SettingsSet, settings: collections.abc.Sequence[tuple[str, object]]) -> None


            Create settings set from Python list of (key, value) pairs
    
            Automatically converts Python values to appropriate Setting types.
    
            :param settings: List of (key, value) tuples where values can be bool, int, float, or str

        """
    def all_successfully_updated(self) -> bool:
        """all_successfully_updated(self: zahner_link._zahner_link.SettingsSet) -> bool


            Check if all settings were successfully updated
    
            :returns: True if all settings were successfully updated

        """
    def keys(self) -> list[str]:
        """keys(self: zahner_link._zahner_link.SettingsSet) -> list[str]


            Get list of all setting keys
    
            :returns: List of setting key names

        """
    def size(self) -> int:
        """size(self: zahner_link._zahner_link.SettingsSet) -> int


            Get number of settings
    
            :returns: Number of settings in the set

        """
    def __copy__(self) -> SettingsSet:
        """__copy__(self: zahner_link._zahner_link.SettingsSet) -> zahner_link._zahner_link.SettingsSet


            Shallow copy of the settings set
    
            :returns: Copy of the settings set

        """
    def __deepcopy__(self, memo: dict) -> SettingsSet:
        """__deepcopy__(self: zahner_link._zahner_link.SettingsSet, memo: dict) -> zahner_link._zahner_link.SettingsSet


            Deep copy of the settings set
    
            :param memo: Memoization dictionary (unused)
            :returns: Deep copy of the settings set

        """
    def __getitem__(self, key: str) -> Setting:
        """__getitem__(self: zahner_link._zahner_link.SettingsSet, key: str) -> zahner_link._zahner_link.Setting


            Get setting by key
    
            :param key: Setting key name
            :returns: :class:`zahner_link.Setting` object

        """
    def __iter__(self) -> collections.abc.Iterator[tuple[str, Setting]]:
        """__iter__(self: zahner_link._zahner_link.SettingsSet) -> collections.abc.Iterator[tuple[str, zahner_link._zahner_link.Setting]]


            Iterator over (key, setting) pairs
    
            :returns: Iterator yielding (key, :class:`zahner_link.Setting`) tuples

        """
    def __len__(self) -> int:
        """__len__(self: zahner_link._zahner_link.SettingsSet) -> int


            Get number of settings
    
            :returns: Number of settings in the set

        """
    @overload
    def __setitem__(self, key: str, value: Setting) -> None:
        """__setitem__(*args, **kwargs)
        Overloaded function.

        1. __setitem__(self: zahner_link._zahner_link.SettingsSet, key: str, value: zahner_link._zahner_link.Setting) -> None


            Set setting by key
    
            :param key: Setting key name
            :param value: :class:`zahner_link.Setting` object


        2. __setitem__(self: zahner_link._zahner_link.SettingsSet, key: str, value: object) -> None


            Set setting by key with automatic type detection
    
            Automatically converts Python values to appropriate Setting types.
    
            :param key: Setting key name
            :param value: Value to set (bool, int, float, str, or other types converted to str)

        """
    @overload
    def __setitem__(self, key: str, value: object) -> None:
        """__setitem__(*args, **kwargs)
        Overloaded function.

        1. __setitem__(self: zahner_link._zahner_link.SettingsSet, key: str, value: zahner_link._zahner_link.Setting) -> None


            Set setting by key
    
            :param key: Setting key name
            :param value: :class:`zahner_link.Setting` object


        2. __setitem__(self: zahner_link._zahner_link.SettingsSet, key: str, value: object) -> None


            Set setting by key with automatic type detection
    
            Automatically converts Python values to appropriate Setting types.
    
            :param key: Setting key name
            :param value: Value to set (bool, int, float, str, or other types converted to str)

        """

class TrackNames:
    """
    Constants for track names used in datasets.
    """
    AMPLITUDE: ClassVar[str] = ...  # read-only
    BANDWITH: ClassVar[str] = ...  # read-only
    CURRENT: ClassVar[str] = ...  # read-only
    DC: ClassVar[str] = ...  # read-only
    DRIFT: ClassVar[str] = ...  # read-only
    FILTER: ClassVar[str] = ...  # read-only
    FREQUENCY: ClassVar[str] = ...  # read-only
    GAIN: ClassVar[str] = ...  # read-only
    IMPEDANCE_ABSOLUTE: ClassVar[str] = ...  # read-only
    IMPEDANCE_DRIFT: ClassVar[str] = ...  # read-only
    IMPEDANCE_ERROR: ClassVar[str] = ...  # read-only
    PERIODS: ClassVar[str] = ...  # read-only
    PHASE: ClassVar[str] = ...  # read-only
    PHASE_DRIFT: ClassVar[str] = ...  # read-only
    PHASE_ERROR: ClassVar[str] = ...  # read-only
    SHUNT: ClassVar[str] = ...  # read-only
    THD: ClassVar[str] = ...  # read-only
    TIME: ClassVar[str] = ...  # read-only
    VOLTAGE: ClassVar[str] = ...  # read-only
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class UnitNames:
    """
    Constants for unit names used in datasets.
    """
    BANDWITH: ClassVar[str] = ...  # read-only
    CURRENT: ClassVar[str] = ...  # read-only
    DRIFT: ClassVar[str] = ...  # read-only
    FILTER: ClassVar[str] = ...  # read-only
    FILTER_HZ: ClassVar[str] = ...  # read-only
    FREQUENCY: ClassVar[str] = ...  # read-only
    GAIN: ClassVar[str] = ...  # read-only
    IMPEDANCE_ABSOLUTE: ClassVar[str] = ...  # read-only
    IMPEDANCE_DRIFT: ClassVar[str] = ...  # read-only
    IMPEDANCE_ERROR: ClassVar[str] = ...  # read-only
    PERIODS: ClassVar[str] = ...  # read-only
    PHASE_DRIFT: ClassVar[str] = ...  # read-only
    PHASE_ERROR: ClassVar[str] = ...  # read-only
    PHASE_RAD: ClassVar[str] = ...  # read-only
    SHUNT: ClassVar[str] = ...  # read-only
    THD: ClassVar[str] = ...  # read-only
    TIME: ClassVar[str] = ...  # read-only
    VOLTAGE: ClassVar[str] = ...  # read-only
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class UserHardwareSettings:
    channels: list[Channel]
    impedance_configurations: list[ImpedanceConfiguration]
    output_potentiostats: list[PotentiostatConfiguration]
    def __init__(self, channels: collections.abc.Sequence[Channel], impedance_configurations: collections.abc.Sequence[ImpedanceConfiguration], output_potentiostats: collections.abc.Sequence[PotentiostatConfiguration]) -> None:
        """__init__(self: zahner_link._zahner_link.UserHardwareSettings, channels: collections.abc.Sequence[zahner_link._zahner_link.Channel], impedance_configurations: collections.abc.Sequence[zahner_link._zahner_link.ImpedanceConfiguration], output_potentiostats: collections.abc.Sequence[zahner_link._zahner_link.PotentiostatConfiguration]) -> None


            Class which contains the information about the sampling configuration to be set

            :param channels:
                * channels to be measured during the measurement
                * asynchron and synchron channels together these are automatically split
            :param impedance_configurations:
                * synchron sampled channels
                * as a list of lists from which impedances are calculated
                * in the sub list, the first element (index 0) divided by the second element (index 1) is used for the impedance calculation
            :param output_potentiostats: potentiostat on which the measurement is to be output

        """
    def add_sync_current_channel(self, connections: collections.abc.Sequence[Pad4Connection]) -> None:
        """add_sync_current_channel(self: zahner_link._zahner_link.UserHardwareSettings, connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4Connection]) -> None


            Adding a synchronous current channel to the configuration.

            With the added channels, an impedance is calculated with the main voltage channel.

            :param connections: synchronous channels

        """
    def add_sync_voltage_channel(self, connections: collections.abc.Sequence[Pad4Connection]) -> None:
        """add_sync_voltage_channel(self: zahner_link._zahner_link.UserHardwareSettings, connections: collections.abc.Sequence[zahner_link._zahner_link.Pad4Connection]) -> None


            Adding a synchronous voltage channel to the configuration.

            With the added channels, an impedance is calculated with the main current channel.

            :param connections: synchronous channels

        """
    def remove_duplicates_from_channels(self) -> None:
        """remove_duplicates_from_channels(self: zahner_link._zahner_link.UserHardwareSettings) -> None


            Removal of duplicates from the channels.

        """

class UserPolynomial:
    coefficients: list[float]
    @overload
    def __init__(self, coefficients: collections.abc.Sequence[typing.SupportsFloat]) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.UserPolynomial, coefficients: collections.abc.Sequence[typing.SupportsFloat]) -> None


                Class which contains the polynomial for the channel configuration.

                :param coefficients: array containing the coefficients of the polynomial
        

        2. __init__(self: zahner_link._zahner_link.UserPolynomial, arg0: collections.abc.Sequence) -> None
        """
    @overload
    def __init__(self, arg0: collections.abc.Sequence) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.UserPolynomial, coefficients: collections.abc.Sequence[typing.SupportsFloat]) -> None


                Class which contains the polynomial for the channel configuration.

                :param coefficients: array containing the coefficients of the polynomial
        

        2. __init__(self: zahner_link._zahner_link.UserPolynomial, arg0: collections.abc.Sequence) -> None
        """
    def __lt__(self, arg0: UserPolynomial) -> bool:
        """__lt__(self: zahner_link._zahner_link.UserPolynomial, arg0: zahner_link._zahner_link.UserPolynomial) -> bool"""

class VoltageRange:
    index: int
    voltage: float
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class WorkstationInfo:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    @property
    def cpu_card_uuid(self) -> str:
        """(self: zahner_link._zahner_link.WorkstationInfo) -> str"""
    @property
    def firmware_version(self) -> str:
        """(self: zahner_link._zahner_link.WorkstationInfo) -> str"""
    @property
    def model_name(self) -> str:
        """(self: zahner_link._zahner_link.WorkstationInfo) -> str"""
    @property
    def protocol_version(self) -> int:
        """(self: zahner_link._zahner_link.WorkstationInfo) -> int"""
    @property
    def serial_number(self) -> str:
        """(self: zahner_link._zahner_link.WorkstationInfo) -> str"""
    @property
    def system_mac(self) -> str:
        """(self: zahner_link._zahner_link.WorkstationInfo) -> str"""
    @property
    def system_name(self) -> str:
        """(self: zahner_link._zahner_link.WorkstationInfo) -> str"""

class WorkstationStatus:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    @property
    def busy(self) -> bool:
        """(self: zahner_link._zahner_link.WorkstationStatus) -> bool"""
    @property
    def last_dc_calibration(self) -> str:
        """(self: zahner_link._zahner_link.WorkstationStatus) -> str"""
    @property
    def uptime(self) -> int:
        """(self: zahner_link._zahner_link.WorkstationStatus) -> int"""

class ZahnerLink:
    def __init__(self, hostname: str, port: str = ..., flags: typing.SupportsInt = ..., http_user: str = ..., http_password: str = ...) -> None:
        """__init__(self: zahner_link._zahner_link.ZahnerLink, hostname: str, port: str = '1994', flags: typing.SupportsInt = 0, http_user: str = '', http_password: str = '') -> None


            Class which manages the connection to the IM7

            This class provides methods for communicating with an IM7 device and executing jobs.

            :param hostname: IP address of the IM7
            :param port: port of the IM7
            :param flags: optional flags of type :class:`zahner_link.ZahnerLinkConnectionFlags` for the connection can be combined with bitwise OR operation
            :param http_user: user name from the settings 
            :param http_password: password from the settings

        """
    def append_to_resource(self, resource: Resource, data: collections.abc.Buffer) -> bool:
        """append_to_resource(self: zahner_link._zahner_link.ZahnerLink, resource: zahner_link._zahner_link.Resource, data: collections.abc.Buffer) -> bool


            Append data to a resource

            :param resource: Resource object
            :param data: Data as bytearray
            :returns: True if successful

        """
    def clear_flag(self, flag: typing.SupportsInt) -> None:
        """clear_flag(self: zahner_link._zahner_link.ZahnerLink, flag: typing.SupportsInt) -> None


            Clear a connection flag.

            :param flag: flag to clear (e.g. from :class:`zahner_link.ZahnerLinkConnectionFlags`)

        """
    def connect(self) -> ZahnerLinkServiceStatusEnum:
        """connect(self: zahner_link._zahner_link.ZahnerLink) -> ZahnerLinkServiceStatusEnum


            Connect to a running IM7

        """
    def create_resource(self, type: ResourceTypeEnum, resource_name: str) -> Resource:
        """create_resource(self: zahner_link._zahner_link.ZahnerLink, type: ResourceTypeEnum, resource_name: str) -> zahner_link._zahner_link.Resource


            Create a resource

            :param type: :class:`zahner_link.ResourceTypeEnum`
            :param resource_name: Name of the resource
            :returns: :class:`zahner_link.Resource` object

        """
    def create_resource_from_file(self, type: ResourceTypeEnum, file_name_and_path: str, resource_name: str = ...) -> Resource:
        """create_resource_from_file(self: zahner_link._zahner_link.ZahnerLink, type: ResourceTypeEnum, file_name_and_path: str, resource_name: str = '') -> zahner_link._zahner_link.Resource


            Create a resource from a file

            :param type: :class:`zahner_link.ResourceTypeEnum`
            :param file_name_and_path: Path to the file
            :param resource_name: Optional resource name
            :returns: :class:`zahner_link.Resource` object

        """
    def delete_resource(self, resource: Resource) -> bool:
        """delete_resource(self: zahner_link._zahner_link.ZahnerLink, resource: zahner_link._zahner_link.Resource) -> bool


            Delete a resource

            :param resource: :class:`zahner_link.Resource` object
            :returns: True if successful

        """
    def disconnect(self) -> None:
        """disconnect(self: zahner_link._zahner_link.ZahnerLink) -> None


            Disconnect from the device

            Jobs can no longer be executed after disconnect has been called.
            However, data that is available in the job objects after the job has been executed remains valid and can still be used.

        """
    def do_job(self, job: AbstractMeasurementJob) -> bool:
        """do_job(self: zahner_link._zahner_link.ZahnerLink, job: AbstractMeasurementJob) -> bool


            Perform a job
    
            :param job: job object
            :returns: True if the job was successful

        """
    def do_measurement(self, job: AbstractMeasurementJob) -> DataSet:
        """do_measurement(self: zahner_link._zahner_link.ZahnerLink, job: AbstractMeasurementJob) -> DataSet


            Execute a measurement job and return the resulting dataset.

            :param job: measurement job object
            :returns: :class:`zahner_link.EisDataset` or :class:`zahner_link.DcDataset` object with the result data as the base class :class:`zahner_link.DataSet`

        """
    def download_resource_to_file(self, resource: Resource, file_name_and_path: str) -> bool:
        """download_resource_to_file(self: zahner_link._zahner_link.ZahnerLink, resource: zahner_link._zahner_link.Resource, file_name_and_path: str) -> bool


            Download resource to file

            :param resource: :class:`zahner_link.Resource` object
            :param file_name_and_path: Path to save file
            :returns: True if successful

        """
    def get_available_resources(self, type: ResourceTypeEnum) -> list[Resource]:
        """get_available_resources(self: zahner_link._zahner_link.ZahnerLink, type: ResourceTypeEnum) -> list[zahner_link._zahner_link.Resource]


            Get available resources of a type

            :param type: :class:`zahner_link.ResourceTypeEnum`
            :returns: List of :class:`zahner_link.Resource` objects

        """
    def get_connection_status(self) -> ZahnerLinkConnectionStatusEnum:
        """get_connection_status(self: zahner_link._zahner_link.ZahnerLink) -> ZahnerLinkConnectionStatusEnum


            Get the connection state

            :returns: enum with the connection state

        """
    def get_job_result_data(self, job: AbstractMeasurementJob) -> DataSet:
        """get_job_result_data(self: zahner_link._zahner_link.ZahnerLink, job: AbstractMeasurementJob) -> DataSet


            Get the result data from a job
    
            This must be used for jobs that return measurement data and online data that have a longer duration.
            For example EIS with :class:`zahner_link.meas.EisGenerateJob` or :class:`zahner_link.meas.CvJob`.
    
            :param job: job object
            :returns: :class:`EisDataset` or :class:`DcDataset` object with the result data as the base class :class:`DataSet`

        """
    def get_settings(self) -> SettingsSet:
        """get_settings(self: zahner_link._zahner_link.ZahnerLink) -> SettingsSet


            Get the current device settings

        """
    def get_updated_resource_info(self, resource: Resource) -> bool:
        """get_updated_resource_info(self: zahner_link._zahner_link.ZahnerLink, resource: zahner_link._zahner_link.Resource) -> bool


            Update resource info

            :param resource: :class:`zahner_link.Resource` object
            :returns: True if successful

        """
    def get_workstation_info(self) -> WorkstationInfo:
        """get_workstation_info(self: zahner_link._zahner_link.ZahnerLink) -> zahner_link._zahner_link.WorkstationInfo


            Get device information

            :returns: :class:`zahner_link.WorkstationInfo` object with device information.

        """
    def get_workstation_status(self) -> WorkstationStatus:
        """get_workstation_status(self: zahner_link._zahner_link.ZahnerLink) -> zahner_link._zahner_link.WorkstationStatus


            Get device status

            :returns: :class:`zahner_link.WorkstationStatus` object with device status.

        """
    def is_connected(self) -> bool:
        """is_connected(self: zahner_link._zahner_link.ZahnerLink) -> bool


            Check if it is connected to IM7

            :returns: True if it is connected

        """
    def retrieve_resource(self, resource: Resource, limit: typing.SupportsInt = ..., offset: typing.SupportsInt = ...) -> bytes:
        """retrieve_resource(self: zahner_link._zahner_link.ZahnerLink, resource: zahner_link._zahner_link.Resource, limit: typing.SupportsInt = 0, offset: typing.SupportsInt = 0) -> bytes


            Retrieve resource data

            :param resource: :class:`zahner_link.Resource` object
            :param limit: Max bytes to retrieve (0 = max)
            :param offset: Offset in resource
            :returns: Data as bytes

        """
    def send_stop(self, queue_stop_mode: QueueStopModeEnum) -> None:
        """send_stop(self: zahner_link._zahner_link.ZahnerLink, queue_stop_mode: QueueStopModeEnum) -> None


            Stop the device

            :param queue_stop_mode: enum how to stop the job

        """
    def set_destination_host(self, hostname: str, port: str) -> None:
        """set_destination_host(self: zahner_link._zahner_link.ZahnerLink, hostname: str, port: str) -> None


            Set the destination host and port.

            :param hostname: IP address or hostname of the IM7
            :param port: port of the IM7

        """
    def set_flag(self, flag: typing.SupportsInt) -> None:
        """set_flag(self: zahner_link._zahner_link.ZahnerLink, flag: typing.SupportsInt) -> None


            Set a connection flag.

            :param flag: flag to set (e.g. from :class:`zahner_link.ZahnerLinkConnectionFlags`)

        """
    def set_http_authentication_info(self, http_user: str, http_password: str) -> None:
        """set_http_authentication_info(self: zahner_link._zahner_link.ZahnerLink, http_user: str, http_password: str) -> None


            Set HTTP authentication information.

            :param http_user: user name
            :param http_password: password

        """
    def set_request_timeout(self, arg0: typing.SupportsFloat) -> None:
        """set_request_timeout(self: zahner_link._zahner_link.ZahnerLink, arg0: typing.SupportsFloat) -> None


            Set the request timeout

            :param timeout: timeout value in seconds

        """
    def test_flag(self, flag: typing.SupportsInt) -> bool:
        """test_flag(self: zahner_link._zahner_link.ZahnerLink, flag: typing.SupportsInt) -> bool


            Test if a connection flag is set.

            :param flag: flag to test (e.g. from :class:`zahner_link.ZahnerLinkConnectionFlags`)
            :returns: True if the flag is set

        """
    def update_settings(self, settings: SettingsSet) -> None:
        """update_settings(self: zahner_link._zahner_link.ZahnerLink, settings: SettingsSet) -> None


            Update device settings

            :param settings: List of settings to update

        """

class ZahnerLinkConnectionFlags:
    """
    Flags for the ZahnerLink connection.
    """
    IGNORE_PROTOCOL_MISMATCH: ClassVar[int] = ...  # read-only
    NONE: ClassVar[int] = ...  # read-only
    SKIP_SSL_CERT_VALIDATION: ClassVar[int] = ...  # read-only
    USE_SSL: ClassVar[int] = ...  # read-only
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class ZahnerLinkConnectionStatusEnum(enum.Enum):
    """
    Indicates the connection status.
    """
    __new__: ClassVar[Callable] = ...
    CONNECTED: ClassVar[ZahnerLinkConnectionStatusEnum] = ...
    DISCONNECTED: ClassVar[ZahnerLinkConnectionStatusEnum] = ...
    _generate_next_value_: ClassVar[Callable] = ...
    _hashable_values_: ClassVar[list] = ...
    _member_map_: ClassVar[dict] = ...
    _member_names_: ClassVar[list] = ...
    _member_type_: ClassVar[type[object]] = ...
    _unhashable_values_: ClassVar[list] = ...
    _unhashable_values_map_: ClassVar[dict] = ...
    _use_args_: ClassVar[bool] = ...
    _value2member_map_: ClassVar[dict] = ...
    _value_repr_: ClassVar[None] = ...

class ZahnerLinkExc(ZahnerLink):
    def __init__(self, hostname: str, port: str = ..., flags: typing.SupportsInt = ..., http_user: str = ..., http_password: str = ...) -> None:
        """__init__(self: zahner_link._zahner_link.ZahnerLinkExc, hostname: str, port: str = '1994', flags: typing.SupportsInt = 0, http_user: str = '', http_password: str = '') -> None


            Class which manages the connection to the IM7

            This class provides methods for communicating with an IM7 device and executing jobs.
            Variant of ZahnerLink which raises :class:`zahner_link.ZahnerLinkException` on errors for selected methods.

            The following methods throw :class:`zahner_link.ZahnerLinkException` when the underlying operation fails:
              * do_job
              * get_job_result_data
              * do_measurement

            :param hostname: IP address of the IM7
            :param port: port of the IM7
            :param flags: optional flags of type :class:`zahner_link.ZahnerLinkConnectionFlags` for the connection can be combined with bitwise OR operation
            :param http_user: user name from the settings 
            :param http_password: password from the settings

        """
    def do_job(self, job: AbstractMeasurementJob) -> bool:
        """do_job(self: zahner_link._zahner_link.ZahnerLinkExc, job: AbstractMeasurementJob) -> bool


            Perform a job.

            :param job: job object
            :returns: True if the job was successful
            :raises ZahnerLinkException: if the job failed

        """
    def do_measurement(self, job: AbstractMeasurementJob) -> DataSet:
        """do_measurement(self: zahner_link._zahner_link.ZahnerLinkExc, job: AbstractMeasurementJob) -> DataSet


            Execute a measurement job and directly return the resulting dataset.

            :param job: measurement job object
            :returns: Dataset object with measurement data
            :raises ZahnerLinkException: if execution failed

        """
    def get_job_result_data(self, job: AbstractMeasurementJob) -> DataSet:
        """get_job_result_data(self: zahner_link._zahner_link.ZahnerLinkExc, job: AbstractMeasurementJob) -> DataSet


            Get the result data from a previously executed job.

            :param job: job object
            :returns: Dataset object (EisDataset, DcDataset, ...) derived from DataSet
            :raises ZahnerLinkException: if retrieval failed or job did not finish successfully

        """

class ZahnerLinkException(Exception):
    """Base class for all ZahnerLink exceptions."""

class ZahnerLinkServiceStatusEnum(enum.IntEnum):
    """
    Enum which indicates the status of the the connection to the IM7.
    """
    __new__: ClassVar[Callable] = ...
    ALREADY_CONNECTED_ERROR: ClassVar[ZahnerLinkServiceStatusEnum] = ...
    COULD_NOT_RESOLVE_HOSTNAME: ClassVar[ZahnerLinkServiceStatusEnum] = ...
    FAILED_TO_CONNECT: ClassVar[ZahnerLinkServiceStatusEnum] = ...
    FAILED_TO_ESTABLISH_WEBSOCKET_CONNECTION: ClassVar[ZahnerLinkServiceStatusEnum] = ...
    FAILED_TO_READ_FROM_SOCKET: ClassVar[ZahnerLinkServiceStatusEnum] = ...
    FAILED_TO_WRITE_TO_SOCKET: ClassVar[ZahnerLinkServiceStatusEnum] = ...
    HTTP_ERROR: ClassVar[ZahnerLinkServiceStatusEnum] = ...
    PROTOCOL_VERSION_MISMATCH: ClassVar[ZahnerLinkServiceStatusEnum] = ...
    SSL_ERROR: ClassVar[ZahnerLinkServiceStatusEnum] = ...
    SSL_HANDSHAKE_ERROR: ClassVar[ZahnerLinkServiceStatusEnum] = ...
    SSL_NOT_SUPPORTED_BY_LIBRARY: ClassVar[ZahnerLinkServiceStatusEnum] = ...
    SUCCESS_NO_ERROR: ClassVar[ZahnerLinkServiceStatusEnum] = ...
    UNABLE_TO_CREATE_CONNECTION_OBJECT: ClassVar[ZahnerLinkServiceStatusEnum] = ...
    UNAUTHORIZED: ClassVar[ZahnerLinkServiceStatusEnum] = ...
    UNKNOWN: ClassVar[ZahnerLinkServiceStatusEnum] = ...
    _generate_next_value_: ClassVar[Callable] = ...
    _hashable_values_: ClassVar[list] = ...
    _member_map_: ClassVar[dict] = ...
    _member_names_: ClassVar[list] = ...
    _member_type_: ClassVar[type[int]] = ...
    _unhashable_values_: ClassVar[list] = ...
    _unhashable_values_map_: ClassVar[dict] = ...
    _use_args_: ClassVar[bool] = ...
    _value2member_map_: ClassVar[dict] = ...
    def __format__(self, *args, **kwargs) -> str:
        """Convert to a string according to format_spec."""

def add(arg0: typing.SupportsInt, arg1: typing.SupportsInt) -> int:
    """add(arg0: typing.SupportsInt, arg1: typing.SupportsInt) -> int


        The add function

        Parameters
        ----------

    """
def factorial(arg0: typing.SupportsFloat) -> float:
    """factorial(arg0: typing.SupportsFloat) -> float


        factorial test

        Parameters
        ----------

    """
