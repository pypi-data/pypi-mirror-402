import collections.abc
import typing
import zahner_link._zahner_link
from typing import overload

class CalibrateJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: CalibrateParametersStringPy
    @overload
    def __init__(self, calibration_type: str = ..., calibration_path: str = ..., indexes: collections.abc.Sequence[typing.SupportsInt] = ..., paths: collections.abc.Sequence[str] = ...) -> None:
        '''__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.calibration.CalibrateJob, calibration_type: str = \'dc\', calibration_path: str = \'\', indexes: collections.abc.Sequence[typing.SupportsInt] = [], paths: collections.abc.Sequence[str] = []) -> None


            Calibrate job
        
            This job starts a calibration of the passed type.

            :param calibration_type: calibration type, only "dc" available


        2. __init__(self: zahner_link._zahner_link.calibration.CalibrateJob, calibration_type: zahner_link._zahner_link.CalibrationTypesEnum = <CalibrationTypesEnum.DC: 2>, calibration_path: str = \'\', indexes: collections.abc.Sequence[typing.SupportsInt] = [], paths: collections.abc.Sequence[str] = []) -> None


            Calibrate job
        
            This job starts a calibration of the passed type.

            :param calibration_type: calibration type, only CalibrationTypesEnum.DC available

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "calibrate",
                      "parameters": {
                        "calibration_type": "dc"
                      }
                    },
                    "request_id": "calibrate-job-uuid-example"
                  }

        '''
    @overload
    def __init__(self, calibration_type: zahner_link._zahner_link.CalibrationTypesEnum = ..., calibration_path: str = ..., indexes: collections.abc.Sequence[typing.SupportsInt] = ..., paths: collections.abc.Sequence[str] = ...) -> None:
        '''__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.calibration.CalibrateJob, calibration_type: str = \'dc\', calibration_path: str = \'\', indexes: collections.abc.Sequence[typing.SupportsInt] = [], paths: collections.abc.Sequence[str] = []) -> None


            Calibrate job
        
            This job starts a calibration of the passed type.

            :param calibration_type: calibration type, only "dc" available


        2. __init__(self: zahner_link._zahner_link.calibration.CalibrateJob, calibration_type: zahner_link._zahner_link.CalibrationTypesEnum = <CalibrationTypesEnum.DC: 2>, calibration_path: str = \'\', indexes: collections.abc.Sequence[typing.SupportsInt] = [], paths: collections.abc.Sequence[str] = []) -> None


            Calibrate job
        
            This job starts a calibration of the passed type.

            :param calibration_type: calibration type, only CalibrationTypesEnum.DC available

            .. collapse:: WebSocket JSON Example

               .. code-block:: json

                  {
                    "do": "/job/start",
                    "job": {
                      "type": "calibrate",
                      "parameters": {
                        "calibration_type": "dc"
                      }
                    },
                    "request_id": "calibrate-job-uuid-example"
                  }

        '''

class CalibrateParametersPy:
    calibration_path: str
    calibration_type: zahner_link._zahner_link.CalibrationTypesEnum
    indexes: list[int]
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class CalibrateParametersStringPy:
    calibration_path: str
    calibration_type: str
    indexes: list[int]
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class FilterUsageMatrix:
    matrix: list[tuple[int, int]]
    def __init__(self) -> None:
        """__init__(self: zahner_link._zahner_link.calibration.FilterUsageMatrix) -> None"""

class GetCalibrationDataJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: GetCalibrationDataParametersPy
    @overload
    def __init__(self, calibration_type: str, calibration_path: str = ..., indexes: collections.abc.Sequence[typing.SupportsInt] = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.calibration.GetCalibrationDataJob, calibration_type: str, calibration_path: str = '', indexes: collections.abc.Sequence[typing.SupportsInt] = []) -> None


            Set Calibration Data job - No customer should call this job


        2. __init__(self: zahner_link._zahner_link.calibration.GetCalibrationDataJob, calibration_type: zahner_link._zahner_link.CalibrationTypesEnum, calibration_path: str = '', indexes: collections.abc.Sequence[typing.SupportsInt] = []) -> None


            Set Calibration Data job - No customer should call this job

        """
    @overload
    def __init__(self, calibration_type: zahner_link._zahner_link.CalibrationTypesEnum, calibration_path: str = ..., indexes: collections.abc.Sequence[typing.SupportsInt] = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.calibration.GetCalibrationDataJob, calibration_type: str, calibration_path: str = '', indexes: collections.abc.Sequence[typing.SupportsInt] = []) -> None


            Set Calibration Data job - No customer should call this job


        2. __init__(self: zahner_link._zahner_link.calibration.GetCalibrationDataJob, calibration_type: zahner_link._zahner_link.CalibrationTypesEnum, calibration_path: str = '', indexes: collections.abc.Sequence[typing.SupportsInt] = []) -> None


            Set Calibration Data job - No customer should call this job

        """
    def get_calibration_data_type(self) -> zahner_link._zahner_link.CalibrationDataTypeEnum:
        """get_calibration_data_type(self: zahner_link._zahner_link.calibration.GetCalibrationDataJob) -> zahner_link._zahner_link.CalibrationDataTypeEnum



        """
    def get_data(self) -> object:
        """get_data(self: zahner_link._zahner_link.calibration.GetCalibrationDataJob) -> object


    
        """
    def get_float_data(self) -> float:
        """get_float_data(self: zahner_link._zahner_link.calibration.GetCalibrationDataJob) -> float



        """
    def get_float_vector_data(self) -> list[float]:
        """get_float_vector_data(self: zahner_link._zahner_link.calibration.GetCalibrationDataJob) -> list[float]



        """
    def get_spectra_data(self) -> dict[float, complex]:
        """get_spectra_data(self: zahner_link._zahner_link.calibration.GetCalibrationDataJob) -> dict[float, complex]



        """
    def get_string_data(self) -> str:
        """get_string_data(self: zahner_link._zahner_link.calibration.GetCalibrationDataJob) -> str



        """

class GetCalibrationDataParametersPy:
    calibration_path: str
    calibration_type: str
    indexes: list[int]
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class GetFilterUsageMatrixJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: GetFilterUsageMatrixParametersPy
    def __init__(self, pad4_path: str) -> None:
        """__init__(self: zahner_link._zahner_link.calibration.GetFilterUsageMatrixJob, pad4_path: str) -> None


             GetFilterUsageMatrixJob job - No customer should call this job

        """
    def get_job_result(self) -> FilterUsageMatrix:
        """get_job_result(self: zahner_link._zahner_link.calibration.GetFilterUsageMatrixJob) -> zahner_link._zahner_link.calibration.FilterUsageMatrix



        """

class GetFilterUsageMatrixParametersPy:
    pad4_path: str
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class GetMeshJsonFileJob(zahner_link._zahner_link.AbstractMeasurementJob):
    def __init__(self) -> None:
        """__init__(self: zahner_link._zahner_link.calibration.GetMeshJsonFileJob) -> None


            GetMeshJsonFileJob job - No customer should call this job

        """
    def get_job_result(self) -> bytes:
        """get_job_result(self: zahner_link._zahner_link.calibration.GetMeshJsonFileJob) -> bytes


            Get the queried mesh file contents.

            :returns: bytes object with the file contents

        """

class SetCalibrationDataJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: SetCalibrationDataParametersPy
    @overload
    def __init__(self, calibration_type: str, calibration_path: str = ..., indexes: collections.abc.Sequence[typing.SupportsInt] = ..., data_type: str = ..., float_data: typing.SupportsFloat = ..., float_vector_data: collections.abc.Sequence[typing.SupportsFloat] = ..., spectra_data: collections.abc.Mapping[typing.SupportsFloat, complex] = ..., string_data: str = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.calibration.SetCalibrationDataJob, calibration_type: str, calibration_path: str = '', indexes: collections.abc.Sequence[typing.SupportsInt] = [], data_type: str = '', float_data: typing.SupportsFloat = 0, float_vector_data: collections.abc.Sequence[typing.SupportsFloat] = [], spectra_data: collections.abc.Mapping[typing.SupportsFloat, complex] = {}, string_data: str = '') -> None


            SetCalibrationDataJob - No customer should call this job


        2. __init__(self: zahner_link._zahner_link.calibration.SetCalibrationDataJob, calibration_type: zahner_link._zahner_link.CalibrationTypesEnum, calibration_path: str = '', indexes: collections.abc.Sequence[typing.SupportsInt] = [], data_type: str = '', float_data: typing.SupportsFloat = 0, float_vector_data: collections.abc.Sequence[typing.SupportsFloat] = [], spectra_data: collections.abc.Mapping[typing.SupportsFloat, complex] = {}, string_data: str = '') -> None


            SetCalibrationDataJob - No customer should call this job

        """
    @overload
    def __init__(self, calibration_type: zahner_link._zahner_link.CalibrationTypesEnum, calibration_path: str = ..., indexes: collections.abc.Sequence[typing.SupportsInt] = ..., data_type: str = ..., float_data: typing.SupportsFloat = ..., float_vector_data: collections.abc.Sequence[typing.SupportsFloat] = ..., spectra_data: collections.abc.Mapping[typing.SupportsFloat, complex] = ..., string_data: str = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.calibration.SetCalibrationDataJob, calibration_type: str, calibration_path: str = '', indexes: collections.abc.Sequence[typing.SupportsInt] = [], data_type: str = '', float_data: typing.SupportsFloat = 0, float_vector_data: collections.abc.Sequence[typing.SupportsFloat] = [], spectra_data: collections.abc.Mapping[typing.SupportsFloat, complex] = {}, string_data: str = '') -> None


            SetCalibrationDataJob - No customer should call this job


        2. __init__(self: zahner_link._zahner_link.calibration.SetCalibrationDataJob, calibration_type: zahner_link._zahner_link.CalibrationTypesEnum, calibration_path: str = '', indexes: collections.abc.Sequence[typing.SupportsInt] = [], data_type: str = '', float_data: typing.SupportsFloat = 0, float_vector_data: collections.abc.Sequence[typing.SupportsFloat] = [], spectra_data: collections.abc.Mapping[typing.SupportsFloat, complex] = {}, string_data: str = '') -> None


            SetCalibrationDataJob - No customer should call this job

        """

class SetCalibrationDataParametersPy:
    calibration_path: str
    calibration_type: str
    data_type: str
    float_data: float
    float_vector_data: list[float]
    indexes: list[int]
    spectra_data: dict[float, complex]
    string_data: str
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class SetMeshJsonFileJob(zahner_link._zahner_link.AbstractMeasurementJob):
    parameters: SetMeshJsonFileParametersPy
    def __init__(self, resource_id: str) -> None:
        """__init__(self: zahner_link._zahner_link.calibration.SetMeshJsonFileJob, resource_id: str) -> None


            SetMeshJsonFileJob - No customer should call this job

        """

class SetMeshJsonFileParametersPy:
    resource_id: str
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
