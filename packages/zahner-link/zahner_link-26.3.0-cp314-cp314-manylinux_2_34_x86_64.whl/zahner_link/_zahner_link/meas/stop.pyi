import typing

class AbstractStopCondition:
    """
        Abstract base class for stop conditions.
    """
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class IntegratingLimitStopCondition(AbstractStopCondition):
    def __init__(self, for_dimension: str, over_dimension: str, maximum: typing.SupportsFloat) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.stop.IntegratingLimitStopCondition, for_dimension: str, over_dimension: str, maximum: typing.SupportsFloat) -> None


            Integrating limit stop condition

            The job is canceled when the integrated absolute value of one dimension over another dimension exceeds the maximum threshold.

            :param for_dimension: dimension to integrate (e.g., "current", "voltage")
            :param over_dimension: dimension to integrate over (e.g., "time")
            :param maximum: maximum integrated value for the specified dimension
    
            .. collapse:: WebSocket JSON Example

               .. code-block:: json
            
                    {
                        "type": "integrating",
                        "parameters": {
                            "for_dimension": "voltage",
                            "over_dimension": "time",
                            "maximum": 10E0
                        }
                    }

        '''

class MaxLimitStopCondition(AbstractStopCondition):
    def __init__(self, for_dimension: str, maximum: typing.SupportsFloat) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.stop.MaxLimitStopCondition, for_dimension: str, maximum: typing.SupportsFloat) -> None


            Maximum limit stop condition

            :param for_dimension: dimension to apply the limit to (e.g., "time", "voltage", "current")
            :param maximum: maximum value for the specified dimension
    
            .. collapse:: WebSocket JSON Example

               .. code-block:: json
            
                    {
                        "type": "max",
                        "parameters": {
                            "for_dimension": "voltage",
                            "maximum": 3E0
                        }
                    }

        '''

class MinLimitStopCondition(AbstractStopCondition):
    def __init__(self, for_dimension: str, minimum: typing.SupportsFloat) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.stop.MinLimitStopCondition, for_dimension: str, minimum: typing.SupportsFloat) -> None


            Minimum limit stop condition
    
            :param for_dimension: dimension to apply the limit to (e.g., "time", "voltage", "current")
            :param minimum: minimum value for the specified dimension
    
            .. collapse:: WebSocket JSON Example

               .. code-block:: json
            
                    {
                        "type": "min",
                        "parameters": {
                            "for_dimension": "voltage",
                            "minimum": 1E0,
                        }
                    }

        '''

class MinMaxLimitStopCondition(AbstractStopCondition):
    def __init__(self, for_dimension: str, minimum: typing.SupportsFloat, maximum: typing.SupportsFloat) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.stop.MinMaxLimitStopCondition, for_dimension: str, minimum: typing.SupportsFloat, maximum: typing.SupportsFloat) -> None


            Minimum and maximum limit stop condition
    
            :param for_dimension: dimension to apply the limits to (e.g. "voltage", "current")
            :param minimum: minimum value for the specified dimension
            :param maximum: maximum value for the specified dimension
    
            .. collapse:: WebSocket JSON Example

               .. code-block:: json
            
                    {
                        "type": "min_max",
                        "parameters": {
                            "for_dimension": "voltage",
                            "minimum": -2E0,
                            "maximum": 3E0
                        }
                    }

        '''

class StabilityToleranceLimitStopCondition(AbstractStopCondition):
    def __init__(self, for_dimension: str, stability_tolerance: typing.SupportsFloat, minimum_duration: typing.SupportsFloat) -> None:
        '''__init__(self: zahner_link._zahner_link.meas.stop.StabilityToleranceLimitStopCondition, for_dimension: str, stability_tolerance: typing.SupportsFloat, minimum_duration: typing.SupportsFloat) -> None


            Stability tolerance limit stop condition

            This limit can be used to stop when a stability criterion is met and something has settled, for example.

            :param for_dimension: dimension to integrate (e.g., "current", "voltage")
            :param stability_tolerance: absolute tolerance value for a change in dimension per second below which the job stops
            :param minimum_duration: time after that the stability tolerance is checked
    
            .. collapse:: WebSocket JSON Example

               .. code-block:: json
            
                    {
                        "type": "stability_tolerance",
                        "parameters": {
                            "for_dimension": "voltage",
                            "stability_tolerance": 1E-4,
                            "minimum_duration": 3E0
                        }
                    }

        '''
