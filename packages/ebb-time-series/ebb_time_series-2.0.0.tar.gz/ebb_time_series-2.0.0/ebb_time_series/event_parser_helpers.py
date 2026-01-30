import logging

from marshmallow import ValidationError
from ebb_events.event_schema import DataSchema
from ebb_time_series.constants import DATA_UNITS_FIELDNAME


def slugify_name_and_units(variable_name: str, data_dict: dict) -> str:
    """
    Helper returns string name of variable__units combined with double underscore separator.
    If no units are provided, variable name ends with double underscore (my_var__)

    Args:
        variable_name (str): variable name (key of event data)
        data_dict (dict): dictionary of form {"value":___, "units":___}, value of event data

    Returns:
        str: slugified name with variable_name__units

    Raises:
        marshmallow ValidationError if data_dict doesn't match expected schema
    """
    try:
        unit_val = data_dict.get(DATA_UNITS_FIELDNAME)
        DataSchema().load(data_dict)
        if (
            unit_val is not None
            and isinstance(unit_val, str)
            and unit_val.strip() != ""
        ):
            return f"{variable_name}__{unit_val}"
        return variable_name
    except ValidationError as error:
        logging.error(
            f"Unable to slugify name and units: {str(error)}.",
            extra={
                "variable_name": variable_name,
                "data_dict": str(data_dict),
                "error": str(error),
            },
        )
        raise
