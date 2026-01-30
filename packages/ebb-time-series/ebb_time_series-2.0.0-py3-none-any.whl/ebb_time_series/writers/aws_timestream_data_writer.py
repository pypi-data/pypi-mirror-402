import json
import boto3
import logging
from botocore.config import Config
from botocore.exceptions import ClientError
from enum import Enum
from ebb_events.consumers.event_consumer import EventConsumer
from ebb_events.event_schema import DataSchema
from ebb_time_series.constants import (
    CHUNK_NUMBER_FIELD_NAME,
    DATA_VALUE_FIELDNAME,
    MAX_ATTEMPTS,
    MAX_POOL_CONNECTIONS,
    METADATA_DIMENSION_FIELDNAME,
    ORGANIZATION_FIELDNAME,
    READ_TIMEOUT,
    SYSTEM_FIELDNAME,
    SUBSYSTEM_FIELDNAME,
    DEVICE_FIELDNAME,
    SERIAL_NUMBER_FIELDNAME,
    EVENT_ID_FIELDNAME,
)
from ebb_time_series.event_parser_helpers import slugify_name_and_units
from ebb_time_series.exceptions import TimeSeriesWriteException
from ebb_time_series.writers.base_data_writer import BaseDataWriter
from marshmallow import ValidationError


class AwsTimestreamFields(Enum):
    """
    Enum holding specific aws timestream fields
    Case matters!
    """

    MEASURENAME = "MeasureName"
    MEASURVALUES = "MeasureValues"
    MEASUREVALUETYPE = "MeasureValueType"
    TIME = "Time"
    TIMEUNIT = "TimeUnit"
    DIMENSIONS = "Dimensions"
    DIMENSION_TYPE = "DimensionValueType"
    VALUE = "Value"
    NAME = "Name"
    TYPE = "Type"


class AwsTimestreamValueTypes(Enum):
    """
    Enum holding specific aws timestream value type choices
    Case matters!
    """

    MULTI = "MULTI"
    DOUBLE = "DOUBLE"
    VARCHAR = "VARCHAR"
    TIMESTAMP = "TIMESTAMP"


class AwsTimestreamTimeUnitTypes(Enum):
    """
    Enum holding specific aws timestream TimeUnit types
    Case matteres!
    """

    NANOSECONDS = "NANOSECONDS"
    MICROSECONDS = "MICROSECONDS"
    MILLISECONDS = "MILLISECONDS"
    SECONDS = "SECONDS"


AWS_TIMESTREAM_BULK_WRITE_CHUNK_SIZE = 100
AWS_MULTI_VALUE_RECORD_LIMIT = 120
DIMENSION_FIELDS = [
    ORGANIZATION_FIELDNAME,
    SYSTEM_FIELDNAME,
    SUBSYSTEM_FIELDNAME,
    DEVICE_FIELDNAME,
    SERIAL_NUMBER_FIELDNAME,
    METADATA_DIMENSION_FIELDNAME,
    EVENT_ID_FIELDNAME,
]


class AwsTimestreamDataWriter(BaseDataWriter):
    """Class to write event data to AWS timestream database"""

    def __init__(self, db_name: str, table_name: str, aws_region: str) -> None:
        """
        Initialize AwsTimestreamDataWriter class with required parameters

        Args:
            db_name (str): database name to write records to.
            table_name (str): table name to write records to.
            aws_region (str): aws region in which database lives.
        """
        self.aws_region = aws_region
        self.config = Config(
            region_name=self.aws_region,
            read_timeout=READ_TIMEOUT,
            max_pool_connections=MAX_POOL_CONNECTIONS,
            retries={"max_attempts": MAX_ATTEMPTS},
        )
        super().__init__(db_name, table_name)

    def _chunk_list(self, input_list: list, chunk_size: int):
        """Helper returns list of lists from input_list that are maximum length chunk_size"""
        result_lists = []
        for dex in range(0, len(input_list), chunk_size):
            result_lists.append(input_list[dex : dex + chunk_size])  # noqa: E203
        return result_lists

    def _check_bulk_write_event_consumers_dimensions(
        self, event_consumers: list[EventConsumer]
    ) -> dict:
        """
        Helper method returns True if all event consumers have the same dimension data:
        (org, sys, subsys, device, serial_num); False otherwise

        Args:
            event_consumers (list[EventConsumer]): List of EventConsumers to check/validate

        Returns:
            dict: dimensions dictionary to be fed into _build_aws_dimensions() helper
                if all EventConsumers have matching dimensions

        Exceptions:
            Raises TimeSeriesWriteException if any event_consumer dimensions don't match
        """
        if len(event_consumers) <= 1:
            return True

        base_dimensions_check_dict = {
            ORGANIZATION_FIELDNAME: event_consumers[0].get_event_organization(),
            SYSTEM_FIELDNAME: event_consumers[0].get_event_system_id(),
            SUBSYSTEM_FIELDNAME: event_consumers[0].get_event_subsystem_id(),
            DEVICE_FIELDNAME: event_consumers[0].get_event_device_id(),
            SERIAL_NUMBER_FIELDNAME: event_consumers[0].get_device_serial_number(),
        }
        for event_consumer in event_consumers[1:]:
            curr_dimensions_check_dict = {
                ORGANIZATION_FIELDNAME: event_consumer.get_event_organization(),
                SYSTEM_FIELDNAME: event_consumer.get_event_system_id(),
                SUBSYSTEM_FIELDNAME: event_consumer.get_event_subsystem_id(),
                DEVICE_FIELDNAME: event_consumer.get_event_device_id(),
                SERIAL_NUMBER_FIELDNAME: event_consumer.get_device_serial_number(),
            }
            if curr_dimensions_check_dict != base_dimensions_check_dict:
                logging.error(
                    f"Unable to bulk write {len(event_consumers)} to database due to mismatched event dimensions."
                )
                raise TimeSeriesWriteException(
                    "Unable to bulk write the given list of events due to mismatched event dimensions."
                )
        return base_dimensions_check_dict

    def _build_aws_dimensions(self, dimensions_dict: dict) -> list[dict]:
        """
        Helper build dimension dictionary to be included in the timestream write_records call.
        All dimension dicts are of the form {"Name": ___, "Value": ___, "Type": ___}

        Args:
            dimensions_dict (dict): dict of {field_name: field_value} pairs to be
                                    included in dimensions

        Returns:
            list[dict]: containing fields to be included in dimensions field of Common Attributes
                    in the timestream write_records call of the expected dimension format
        """
        dimensions = []
        for field_name, field_value in dimensions_dict.items():
            if field_value is not None:
                dimensions.append(
                    {
                        AwsTimestreamFields.NAME.value: field_name,
                        AwsTimestreamFields.VALUE.value: field_value,
                        AwsTimestreamFields.DIMENSION_TYPE.value: AwsTimestreamValueTypes.VARCHAR.value,
                    }
                )
            else:
                logging.info(
                    f"Skipping field: {field_name} in _build_aws_dimensions because value is None."
                )
        return dimensions

    def _parse_event_data(
        self, event_consumer: EventConsumer, event_id: str
    ) -> list[dict]:
        """
        Helper method that parses event message data from an EventConsumer object
        to build the record dict and records data to be written to time series database.

        Builds a list of records of the form expected by aws's timestream client to be written to aws:
        list_of_records=[{"Name": ___, "Value": ___, "Type": DOUBLE}, ...].
        NOTE: Skips records that have "value": None because timestream does not accept null values.

        This list_of_records is returned wrapped in a measure_record dict:
        {"MeasureName": "measurement", "MeasureValues": list_of_records, "MeasureType": "MULTI"}

        Args:
            event_consumer (EventConsumer): EventConsumer object that contains the event payload
                                            to be parsed and written to the database.
            event_id (str): Used to add an event_id record and for logging information about this event.
        Returns:
            list[dict]: list of single measurement_record dicts to be written to timestream containing list
                    of all of the records from parsed data found in MeasureValues list:
                    {"MeasureName": "measurement", "MeasureValues": [...], "MeasureType": "MULTI"}
        Exceptions:
            Raises ebb_events `PayloadFormatException` or marshmallow `ValidationError` if format does not match expected structure.
        """
        final_list_of_records = []

        # Raises PayloadFormatException or marshmallow.ValidationError if incorrect format
        event_data: dict = event_consumer.get_event_message(metadata_included=False)
        filtered_null_event_data: dict = {
            k: v
            for k, v in event_data.items()
            if (
                not isinstance(v, dict)
                or (isinstance(v, dict) and v.get("value") is not None)
            )
        }
        # Timestamp in milliseconds
        timestamp_ms = round(event_consumer.get_event_time().timestamp() * 1000)
        # Raises ValidationError if any value isn't of format {"value": ___, "units": ___}
        try:
            DataSchema(many=True).load(list(filtered_null_event_data.values()))
        except ValidationError as error:
            logging.error(
                f"Event ID {event_id}: Payload data does not match expected data schema: {str(error)}."
            )
            raise

        # Build and add event_id/timestamp_records
        event_id_record = {
            AwsTimestreamFields.NAME.value: EVENT_ID_FIELDNAME,
            AwsTimestreamFields.VALUE.value: event_id,
            AwsTimestreamFields.DIMENSION_TYPE.value: AwsTimestreamValueTypes.VARCHAR.value,
        }

        # Build event metadata record
        event_metadata: dict = event_consumer.get_event_message_metadata()
        metadata_str = ""
        try:
            event_metadata: dict = event_consumer.get_event_message_metadata()
            metadata_str = json.dumps(event_metadata)
        except TypeError:
            logging.warning(
                f"Metadata {str(event_metadata)} is not JSON serializable. Not including in timestream write."
            )
        metadata_dimension_record = {
            AwsTimestreamFields.NAME.value: METADATA_DIMENSION_FIELDNAME,
            AwsTimestreamFields.VALUE.value: str(metadata_str),
            AwsTimestreamFields.DIMENSION_TYPE.value: AwsTimestreamValueTypes.VARCHAR.value,
        }

        # key structure = "variable_name", value structure = {"value": ___, "units": ___}
        curr_batch_list = []
        curr_batch_size = 0
        tracked_keys = []
        for key, value in filtered_null_event_data.items():
            if key in DIMENSION_FIELDS:
                logging.warning(f"Skipping key {key} because it is a dimension key.")
                continue
            key_unit_slug = slugify_name_and_units(variable_name=key, data_dict=value)
            if key_unit_slug in tracked_keys or key_unit_slug in DIMENSION_FIELDS:
                logging.warning(
                    f"Skipping key {key_unit_slug} because already tracked in this consumer."
                )
                continue
            # Value must be cast as string for boto3 write even though it's a DOUBLE type
            str_val = str(value.get(DATA_VALUE_FIELDNAME))
            if str_val == "-0.0":
                str_val = "0.0"
            record = {
                AwsTimestreamFields.NAME.value: key_unit_slug,
                AwsTimestreamFields.VALUE.value: str_val,
                AwsTimestreamFields.TYPE.value: AwsTimestreamValueTypes.DOUBLE.value,
            }
            curr_batch_list.append(record)
            curr_batch_size += 1
            tracked_keys.append(key_unit_slug)
            # Append current batch and reset for next batch
            if curr_batch_size >= AWS_MULTI_VALUE_RECORD_LIMIT:
                final_list_of_records.append(curr_batch_list)
                curr_batch_size = 0
                curr_batch_list = []
        if curr_batch_list != []:
            final_list_of_records.append(curr_batch_list)
        return [
            {
                AwsTimestreamFields.MEASURENAME.value: "measurement",
                AwsTimestreamFields.MEASURVALUES.value: list_of_records,
                AwsTimestreamFields.MEASUREVALUETYPE.value: AwsTimestreamValueTypes.MULTI.value,
                AwsTimestreamFields.TIME.value: str(timestamp_ms),
                AwsTimestreamFields.TIMEUNIT.value: AwsTimestreamTimeUnitTypes.MILLISECONDS.value,
                AwsTimestreamFields.DIMENSIONS.value: [
                    event_id_record,
                    metadata_dimension_record,
                    {
                        AwsTimestreamFields.NAME.value: CHUNK_NUMBER_FIELD_NAME,
                        AwsTimestreamFields.VALUE.value: str(dex),
                        AwsTimestreamFields.DIMENSION_TYPE.value: AwsTimestreamValueTypes.VARCHAR.value,
                    },
                ],
            }
            for dex, list_of_records in enumerate(final_list_of_records)
        ]

    def write_event_record(self, event_consumer: EventConsumer) -> bool:
        """
        Main writer method that takes in the consumed event payload, parses the data, and writes
        records to the desired database table.

        Args:
            event_consumer (EventConsumer): EventConsumer object that contains the event payload
                                            to be parsed and written to the database.
        Returns:
            bool: True if the event was successfully written to the database
        Exceptions:
            Raises 'TimeSeriesWriteException' if the writer is unable to write these records to the database for any reason.
        """
        try:
            dimensions_data = {
                ORGANIZATION_FIELDNAME: event_consumer.get_event_organization(),
                SYSTEM_FIELDNAME: event_consumer.get_event_system_id(),
                SUBSYSTEM_FIELDNAME: event_consumer.get_event_subsystem_id(),
                DEVICE_FIELDNAME: event_consumer.get_event_device_id(),
                SERIAL_NUMBER_FIELDNAME: event_consumer.get_device_serial_number(),
            }
            dimensions = self._build_aws_dimensions(dimensions_dict=dimensions_data)

            # Build common attributes dict for aws timestream writer
            common_attributes = {
                AwsTimestreamFields.DIMENSIONS.value: dimensions,
            }

            # Parse event message data to build records
            event_id = event_consumer.get_event_id()
            records_dict_list = self._parse_event_data(
                event_consumer=event_consumer, event_id=event_id
            )
            # Initialize the timestream writer and write to database
            timestream_writer = boto3.client("timestream-write", config=self.config)
            timestream_writer.write_records(
                DatabaseName=self.db_name,
                TableName=self.table_name,
                Records=records_dict_list,
                CommonAttributes=common_attributes,
            )
            logging.info(
                f"Successfully wrote event {event_id} data to database {self.db_name}, table {self.table_name}."
            )
            return True
        except ClientError as error:
            logging.error(
                f"Error writting event data {event_id} to database.",
                extra={
                    "error": str(error),
                    "error_response": error.response.get("Error", {}),
                    "event_id": event_id,
                    "db_name": self.db_name,
                    "table_name": self.table_name,
                },
            )
            raise TimeSeriesWriteException(
                f"Unable to write records to database: {str(error.response.get('Error', error))}",
                response=error.response,
            ) from error
        except Exception as error:
            logging.error(
                f"Error writting event data {event_id} to database.",
                extra={
                    "error": str(error),
                    "event_id": event_id,
                    "db_name": self.db_name,
                    "table_name": self.table_name,
                },
            )
            raise TimeSeriesWriteException(
                f"Unable to write records to database: {str(error)}"
            ) from error

    def bulk_write_event_records(self, event_consumers: list[EventConsumer]) -> bool:
        """
        Take in a list of event_consumers, parse all of their payloads finding the common attributes
        bulk write these to aws timestream database.

        In order to bulk_write_event_records, all event_consumers in the event_consumers input parameter
        must have the same organization, system_id, subsystem_id, device_id, and serial_number.
        If any events do not match, a TimeSeriesWriteException will be raised

        Args:
            event_consumers (list[EventConsumer]): List of event consumers and their respective payloads to write
                                                    to aws timestream.
        Returns:
            bool: True on successful write
        Exceptions:
            Raises 'TimeSeriesWriteException' if the writer is unable to write these records to the database for any reason.
        """
        try:
            # Build dimension data dict from event_envelope fields and values
            dimensions_data = self._check_bulk_write_event_consumers_dimensions(
                event_consumers=event_consumers
            )
            dimensions = self._build_aws_dimensions(dimensions_dict=dimensions_data)
            # Build common attributes dict for aws timestream writer
            common_attributes = {
                AwsTimestreamFields.DIMENSIONS.value: dimensions,
            }

            # Build records_list from event_consumers - each with unique event_id, time, metadata
            records_list = []
            for event_consumer in event_consumers:
                event_id = event_consumer.get_event_id()
                list_of_records = self._parse_event_data(
                    event_consumer=event_consumer, event_id=event_id
                )
                for record in list_of_records:
                    records_list.append(record)

            # Initialize the timestream writer and write to database
            timestream_writer = boto3.client("timestream-write", config=self.config)
            chunked_records = self._chunk_list(
                input_list=records_list, chunk_size=AWS_TIMESTREAM_BULK_WRITE_CHUNK_SIZE
            )
            for dex, records in enumerate(chunked_records):
                base_dex = dex * AWS_TIMESTREAM_BULK_WRITE_CHUNK_SIZE
                timestream_writer.write_records(
                    DatabaseName=self.db_name,
                    TableName=self.table_name,
                    Records=records,
                    CommonAttributes=common_attributes,
                )
                logging.info(
                    f"Successfully wrote records' {base_dex} to {len(records) + base_dex - 1} data to database {self.db_name}, table {self.table_name}."
                )
            return True
        except ClientError as error:
            logging.error(
                "Error writting bulk event data to database.",
                extra={
                    "error": str(error),
                    "error_response": error.response.get("Error", {}),
                    "db_name": self.db_name,
                    "table_name": self.table_name,
                },
            )
            raise TimeSeriesWriteException(
                f"Unable to write records to database: {str(error.response.get('Error', error))}",
                response=error.response,
            ) from error
        except Exception as error:
            logging.error(
                "Error writting bulk event data to database.",
                extra={
                    "error": str(error),
                    "db_name": self.db_name,
                    "table_name": self.table_name,
                },
            )
            raise TimeSeriesWriteException(
                f"Unable to write records to database: {str(error)}"
            ) from error
