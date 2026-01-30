import enum
from typing import Callable, ClassVar, overload

class Measurement(XmlSerializable):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.xml.Measurement) -> None

        2. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo) -> None


            Create an XML measurement with a hardware info

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file


        3. __init__(self: zahner_link._zahner_link.xml.Measurement, dataset: EisDataset) -> None


            Create an XML measurement with a dataset

            :param dataset: dataset to be included in the XML file


        4. __init__(self: zahner_link._zahner_link.xml.Measurement, dataset: DcDataset) -> None


            Create an XML measurement with a dataset

            :param dataset: dataset to be included in the XML file


        5. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo, dataset: EisDataset) -> None


            Create an XML measurement with a hardware info and a dataset

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file
            :param dataset: dataset to be included in the XML file


        6. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo, dataset: DcDataset) -> None


            Create an XML measurement with a hardware info and a dataset

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file
            :param dataset: dataset to be included in the XML file

        """
    @overload
    def __init__(self, hardware_info: HardwareInfo) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.xml.Measurement) -> None

        2. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo) -> None


            Create an XML measurement with a hardware info

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file


        3. __init__(self: zahner_link._zahner_link.xml.Measurement, dataset: EisDataset) -> None


            Create an XML measurement with a dataset

            :param dataset: dataset to be included in the XML file


        4. __init__(self: zahner_link._zahner_link.xml.Measurement, dataset: DcDataset) -> None


            Create an XML measurement with a dataset

            :param dataset: dataset to be included in the XML file


        5. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo, dataset: EisDataset) -> None


            Create an XML measurement with a hardware info and a dataset

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file
            :param dataset: dataset to be included in the XML file


        6. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo, dataset: DcDataset) -> None


            Create an XML measurement with a hardware info and a dataset

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file
            :param dataset: dataset to be included in the XML file

        """
    @overload
    def __init__(self, dataset: EisDataset) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.xml.Measurement) -> None

        2. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo) -> None


            Create an XML measurement with a hardware info

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file


        3. __init__(self: zahner_link._zahner_link.xml.Measurement, dataset: EisDataset) -> None


            Create an XML measurement with a dataset

            :param dataset: dataset to be included in the XML file


        4. __init__(self: zahner_link._zahner_link.xml.Measurement, dataset: DcDataset) -> None


            Create an XML measurement with a dataset

            :param dataset: dataset to be included in the XML file


        5. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo, dataset: EisDataset) -> None


            Create an XML measurement with a hardware info and a dataset

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file
            :param dataset: dataset to be included in the XML file


        6. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo, dataset: DcDataset) -> None


            Create an XML measurement with a hardware info and a dataset

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file
            :param dataset: dataset to be included in the XML file

        """
    @overload
    def __init__(self, dataset: DcDataset) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.xml.Measurement) -> None

        2. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo) -> None


            Create an XML measurement with a hardware info

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file


        3. __init__(self: zahner_link._zahner_link.xml.Measurement, dataset: EisDataset) -> None


            Create an XML measurement with a dataset

            :param dataset: dataset to be included in the XML file


        4. __init__(self: zahner_link._zahner_link.xml.Measurement, dataset: DcDataset) -> None


            Create an XML measurement with a dataset

            :param dataset: dataset to be included in the XML file


        5. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo, dataset: EisDataset) -> None


            Create an XML measurement with a hardware info and a dataset

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file
            :param dataset: dataset to be included in the XML file


        6. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo, dataset: DcDataset) -> None


            Create an XML measurement with a hardware info and a dataset

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file
            :param dataset: dataset to be included in the XML file

        """
    @overload
    def __init__(self, hardware_info: HardwareInfo, dataset: EisDataset) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.xml.Measurement) -> None

        2. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo) -> None


            Create an XML measurement with a hardware info

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file


        3. __init__(self: zahner_link._zahner_link.xml.Measurement, dataset: EisDataset) -> None


            Create an XML measurement with a dataset

            :param dataset: dataset to be included in the XML file


        4. __init__(self: zahner_link._zahner_link.xml.Measurement, dataset: DcDataset) -> None


            Create an XML measurement with a dataset

            :param dataset: dataset to be included in the XML file


        5. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo, dataset: EisDataset) -> None


            Create an XML measurement with a hardware info and a dataset

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file
            :param dataset: dataset to be included in the XML file


        6. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo, dataset: DcDataset) -> None


            Create an XML measurement with a hardware info and a dataset

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file
            :param dataset: dataset to be included in the XML file

        """
    @overload
    def __init__(self, hardware_info: HardwareInfo, dataset: DcDataset) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: zahner_link._zahner_link.xml.Measurement) -> None

        2. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo) -> None


            Create an XML measurement with a hardware info

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file


        3. __init__(self: zahner_link._zahner_link.xml.Measurement, dataset: EisDataset) -> None


            Create an XML measurement with a dataset

            :param dataset: dataset to be included in the XML file


        4. __init__(self: zahner_link._zahner_link.xml.Measurement, dataset: DcDataset) -> None


            Create an XML measurement with a dataset

            :param dataset: dataset to be included in the XML file


        5. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo, dataset: EisDataset) -> None


            Create an XML measurement with a hardware info and a dataset

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file
            :param dataset: dataset to be included in the XML file


        6. __init__(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo, dataset: DcDataset) -> None


            Create an XML measurement with a hardware info and a dataset

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file
            :param dataset: dataset to be included in the XML file

        """
    @overload
    def append_dataset(self, dataset: EisDataset) -> None:
        """append_dataset(*args, **kwargs)
        Overloaded function.

        1. append_dataset(self: zahner_link._zahner_link.xml.Measurement, dataset: EisDataset) -> None


            Append the measurement with an EIS dataset

            :param dataset: EIS dataset to append


        2. append_dataset(self: zahner_link._zahner_link.xml.Measurement, dataset: DcDataset) -> None


            Append the measurement with an DC dataset

            :param dataset: DC dataset to append

        """
    @overload
    def append_dataset(self, dataset: DcDataset) -> None:
        """append_dataset(*args, **kwargs)
        Overloaded function.

        1. append_dataset(self: zahner_link._zahner_link.xml.Measurement, dataset: EisDataset) -> None


            Append the measurement with an EIS dataset

            :param dataset: EIS dataset to append


        2. append_dataset(self: zahner_link._zahner_link.xml.Measurement, dataset: DcDataset) -> None


            Append the measurement with an DC dataset

            :param dataset: DC dataset to append

        """
    def get_datasets(self) -> list[DataSet]:
        """get_datasets(self: zahner_link._zahner_link.xml.Measurement) -> list[DataSet]


            Get the datasets included in the measurement
    
            :returns: list of datasets

        """
    def get_hardware_info(self) -> HardwareInfo | None:
        """get_hardware_info(self: zahner_link._zahner_link.xml.Measurement) -> HardwareInfo | None


            Get the used hardware info in the XML file
    
            :returns: :class:`zahner_link.HardwareInfo` object

        """
    def set_hardware_info(self, hardware_info: HardwareInfo) -> None:
        """set_hardware_info(self: zahner_link._zahner_link.xml.Measurement, hardware_info: HardwareInfo) -> None


            Set the hardware info to be included in the XML file

            :param hardware_info: :class:`zahner_link.HardwareInfo` object to be included in the XML file

        """

class XmlError(enum.IntEnum):
    """
    Enum which indicates the status of the xml process.
    """
    __new__: ClassVar[Callable] = ...
    CAN_NOT_CONVERT_TEXT: ClassVar[XmlError] = ...
    ELEMENT_DEPTH_EXCEEDED: ClassVar[XmlError] = ...
    ELEMENT_TYPE_NOT_SUPPORTED: ClassVar[XmlError] = ...
    EMPTY_DOCUMENT: ClassVar[XmlError] = ...
    ERROR_PARSING: ClassVar[XmlError] = ...
    FILE_COULD_NOT_BE_OPENED: ClassVar[XmlError] = ...
    FILE_NOT_FOUND: ClassVar[XmlError] = ...
    FILE_READ_ERROR: ClassVar[XmlError] = ...
    FILE_TYPE_NOT_SUPPORTED: ClassVar[XmlError] = ...
    MISMATCHED_ELEMENT: ClassVar[XmlError] = ...
    NO_ATTRIBUTE: ClassVar[XmlError] = ...
    NO_ERROR: ClassVar[XmlError] = ...
    NO_TEXT_NODE: ClassVar[XmlError] = ...
    PARSING_ATTRIBUTE: ClassVar[XmlError] = ...
    PARSING_CDATA: ClassVar[XmlError] = ...
    PARSING_COMMENT: ClassVar[XmlError] = ...
    PARSING_DECLARATION: ClassVar[XmlError] = ...
    PARSING_ELEMENT: ClassVar[XmlError] = ...
    PARSING_TEXT: ClassVar[XmlError] = ...
    PARSING_UNKNOWN: ClassVar[XmlError] = ...
    SUCCESS: ClassVar[XmlError] = ...
    TINYXML2_ERROR_COUNT: ClassVar[XmlError] = ...
    TYPE_MISMATCH: ClassVar[XmlError] = ...
    WRONG_ATTRIBUTE_TYPE: ClassVar[XmlError] = ...
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

class XmlSerializable:
    """
    Abstract base class for XML serializable objects.
    """
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class ZXmlExporter:
    def __init__(self) -> None:
        """__init__(self: zahner_link._zahner_link.xml.ZXmlExporter) -> None


            Class to export datasets to Zahner XML format

        """
    @staticmethod
    def default_produces_compact_xml() -> bool:
        """default_produces_compact_xml() -> bool


            Get the default compact XML state.

            Compact XML means that unnecessary whitespace is removed.
    
            :returns: True if compact format is enabled

        """
    @staticmethod
    def get_default_file_version() -> int:
        """get_default_file_version() -> int"""
    @staticmethod
    def get_default_generator() -> str:
        """get_default_generator() -> str"""
    @staticmethod
    def get_default_generator_version() -> str:
        """get_default_generator_version() -> str"""
    def get_file_version(self) -> int:
        """get_file_version(self: zahner_link._zahner_link.xml.ZXmlExporter) -> int"""
    def get_generator(self) -> str:
        """get_generator(self: zahner_link._zahner_link.xml.ZXmlExporter) -> str


            Get the used XML generator
    
            :returns: String with the used generator

        """
    def get_generator_version(self) -> str:
        """get_generator_version(self: zahner_link._zahner_link.xml.ZXmlExporter) -> str


            Get the used XML generator version
    
            :returns: String with the used generator version

        """
    def get_xml_element_tree(self, *args, **kwargs):
        """get_xml_element_tree(self: zahner_link._zahner_link.xml.ZXmlExporter, serializable: zahner_link._zahner_link.xml.XmlSerializable, user_comment: str = '') -> object


             Get the XML as Python `xml.etree.ElementTree <https://docs.python.org/3/library/xml.etree.elementtree.html>`_ object

            :param serializable: serializable job
            :param user_comment: optional user comment
            :returns: returns the Python `xml.etree.ElementTree <https://docs.python.org/3/library/xml.etree.elementtree.html>`_ object

        """
    def produces_compact_xml(self) -> bool:
        """produces_compact_xml(self: zahner_link._zahner_link.xml.ZXmlExporter) -> bool


            Get the compact XML state.

            Compact XML means that unnecessary whitespace is removed.
    
            :returns: True if compact format is enabled

        """
    def save_as_file_standalone(self, serializable: XmlSerializable, filename: str, user_comment: str = ...) -> int:
        """save_as_file_standalone(self: zahner_link._zahner_link.xml.ZXmlExporter, serializable: zahner_link._zahner_link.xml.XmlSerializable, filename: str, user_comment: str = '') -> int


            Save the XML file standalone.

            :param serializable: serializable job
            :param filename: filename with path to save
            :param user_comment: optional user comment
            :returns: file content as string

        """
    def serialize(self, serializable: XmlSerializable) -> str:
        """serialize(self: zahner_link._zahner_link.xml.ZXmlExporter, serializable: zahner_link._zahner_link.xml.XmlSerializable) -> str


            Serialize a plain XmlSerializable XML element to string.

            :param serializable: serializable job
            :returns: content as string

        """
    def serialize_as_file_standalone(self, serializable: XmlSerializable, user_comment: str = ...) -> str:
        """serialize_as_file_standalone(self: zahner_link._zahner_link.xml.ZXmlExporter, serializable: zahner_link._zahner_link.xml.XmlSerializable, user_comment: str = '') -> str


            Create the XML file content as string

            :param serializable: serializable job
            :param user_comment: optional user comment
            :returns: file content as string

        """
    def set_compact_xml(self, compact_xml: bool = ...) -> None:
        """set_compact_xml(self: zahner_link._zahner_link.xml.ZXmlExporter, compact_xml: bool = True) -> None


            Set compact XML format.

            Compact XML means that unnecessary whitespace is removed.

            :param compact_xml: True to enable compact format

        """
    @staticmethod
    def set_default_compact_xml(compact_xml: bool = ...) -> None:
        """set_default_compact_xml(compact_xml: bool = True) -> None


            Set default compact XML format.

            Compact XML means that unnecessary whitespace is removed.

            :param compact_xml: True to enable compact format

        """
    @staticmethod
    def set_default_generator(arg0: str) -> None:
        """set_default_generator(arg0: str) -> None"""
    @staticmethod
    def set_default_generator_version(arg0: str) -> None:
        """set_default_generator_version(arg0: str) -> None"""
    def set_generator(self, generator: str) -> None:
        """set_generator(self: zahner_link._zahner_link.xml.ZXmlExporter, generator: str) -> None


            Set the used XML generator

            This is for the customer, who can then enter his application as a generator if necessary.
    
            :param generator: String with the used generator

        """
    def set_generator_version(self, generator_version: str) -> None:
        """set_generator_version(self: zahner_link._zahner_link.xml.ZXmlExporter, generator_version: str) -> None


            Set the used XML generator version

            This is for the customer, who can then enter his application as a generator if necessary.
    
            :param generator_version: String with the used generator version

        """

class ZXmlImporter:
    def __init__(self) -> None:
        """__init__(self: zahner_link._zahner_link.xml.ZXmlImporter) -> None


            Class to import datasets from Zahner XML format

        """
    def deserialize(self, data: bytes) -> XmlSerializable:
        """deserialize(self: zahner_link._zahner_link.xml.ZXmlImporter, data: bytes) -> zahner_link._zahner_link.xml.XmlSerializable


            Deserialize a plain XmlSerializable XML element from bytes.

            :param data: Bytes containing the XML element
            :returns: Shared pointer to the deserialized object or None on failure

        """
    def get_last_error(self) -> XmlError:
        """get_last_error(self: zahner_link._zahner_link.xml.ZXmlImporter) -> zahner_link._zahner_link.xml.XmlError


            Get the status/error code of the last import operation.

            :returns: XmlError enum value indicating the result of the last operation

        """
    def import_from_file(self, filename: str, file_info: ZahnerFileInfo = ...) -> XmlSerializable:
        """import_from_file(self: zahner_link._zahner_link.xml.ZXmlImporter, filename: str, file_info: zahner_link._zahner_link.xml.ZahnerFileInfo = None) -> zahner_link._zahner_link.xml.XmlSerializable


            Create XmlSerializable from a file.

            :param filename: Full path and filename of the file to be imported
            :param file_info: Optional ZahnerFileInfo for informations
            :returns: Imported object or None on failure

        """
    def import_from_file_as_dc_dataset(self, filename: str, file_info: ZahnerFileInfo = ...) -> DcDataset:
        """import_from_file_as_dc_dataset(self: zahner_link._zahner_link.xml.ZXmlImporter, filename: str, file_info: zahner_link._zahner_link.xml.ZahnerFileInfo = None) -> DcDataset


            Create DcDataset from a file.

            :param filename: Full path and filename of the file to be imported
            :param file_info: Optional ZahnerFileInfo for informations
            :returns: Imported DcDataset object or None on failure

        """
    def import_from_file_as_eis_dataset(self, filename: str, file_info: ZahnerFileInfo = ...) -> EisDataset:
        """import_from_file_as_eis_dataset(self: zahner_link._zahner_link.xml.ZXmlImporter, filename: str, file_info: zahner_link._zahner_link.xml.ZahnerFileInfo = None) -> EisDataset


            Create EisDataset from a file.

            :param filename: Full path and filename of the file to be imported
            :param file_info: Optional ZahnerFileInfo for informations
            :returns: Imported EisDataset object or None on failure

        """
    def import_from_file_as_measurement(self, filename: str, file_info: ZahnerFileInfo = ...) -> Measurement:
        """import_from_file_as_measurement(self: zahner_link._zahner_link.xml.ZXmlImporter, filename: str, file_info: zahner_link._zahner_link.xml.ZahnerFileInfo = None) -> zahner_link._zahner_link.xml.Measurement


            Create Measurement from a file.

            :param filename: Full path and filename of the file to be imported
            :param file_info: Optional ZahnerFileInfo for informations
            :returns: Imported Measurement object or None on failure

        """
    def import_from_memory(self, data: bytes, file_info: ZahnerFileInfo = ...) -> XmlSerializable:
        """import_from_memory(self: zahner_link._zahner_link.xml.ZXmlImporter, data: bytes, file_info: zahner_link._zahner_link.xml.ZahnerFileInfo = None) -> zahner_link._zahner_link.xml.XmlSerializable


            Create XmlSerializable from bytes in memory.

            :param data: The complete XML standalone file as bytes
            :param file_info: Optional ZahnerFileInfo for informations
            :returns: Imported object or None on failure

        """
    def import_from_memory_as_dc_dataset(self, data: bytes, file_info: ZahnerFileInfo = ...) -> DcDataset:
        """import_from_memory_as_dc_dataset(self: zahner_link._zahner_link.xml.ZXmlImporter, data: bytes, file_info: zahner_link._zahner_link.xml.ZahnerFileInfo = None) -> DcDataset


            Create DcDataset from bytes in memory.

            :param data: The complete XML standalone file as bytes
            :param file_info: Optional ZahnerFileInfo for informations
            :returns: Imported DcDataset object or None on failure

        """
    def import_from_memory_as_eis_dataset(self, data: bytes, file_info: ZahnerFileInfo = ...) -> EisDataset:
        """import_from_memory_as_eis_dataset(self: zahner_link._zahner_link.xml.ZXmlImporter, data: bytes, file_info: zahner_link._zahner_link.xml.ZahnerFileInfo = None) -> EisDataset


            Create EisDataset from bytes in memory.

            :param data: The complete XML standalone file as bytes
            :param file_info: Optional ZahnerFileInfo for informations
            :returns: Imported EisDataset object or None on failure

        """
    def import_from_memory_as_measurement(self, data: bytes, file_info: ZahnerFileInfo = ...) -> Measurement:
        """import_from_memory_as_measurement(self: zahner_link._zahner_link.xml.ZXmlImporter, data: bytes, file_info: zahner_link._zahner_link.xml.ZahnerFileInfo = None) -> zahner_link._zahner_link.xml.Measurement


            Create Measurement from bytes in memory.

            :param data: The complete XML standalone file as bytes
            :param file_info: Optional ZahnerFileInfo for informations
            :returns: Imported Measurement object or None on failure

        """

class ZahnerFileInfo(XmlSerializable):
    INVALID_FILE_VERSION: ClassVar[int] = ...  # read-only
    XML_ELEMENT_NAME: ClassVar[str] = ...  # read-only
    comment: str
    creation_timestamp: str
    file_version: int
    generator: str
    generator_version: str
    type: str
    def __init__(self) -> None:
        """__init__(self: zahner_link._zahner_link.xml.ZahnerFileInfo) -> None"""
