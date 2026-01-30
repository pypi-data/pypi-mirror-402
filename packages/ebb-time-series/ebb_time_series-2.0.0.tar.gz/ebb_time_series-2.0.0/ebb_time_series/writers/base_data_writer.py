from abc import ABC, abstractmethod
from ebb_events.consumers.event_consumer import EventConsumer


class BaseDataWriter(ABC):
    """Abstract base writer class defines required methods to be implemented by concrete classes"""

    def __init__(self, db_name: str, table_name: str) -> None:
        """
        Abstract data writer __init__ takes in database name and table name to write to.

        Args:
            db_name (str): database name to write records to.
            table_name (str): table name to write records to.
        """
        self.db_name = db_name
        self.table_name = table_name
        super().__init__()

    @abstractmethod
    def _parse_event_data(self, event_consumer: EventConsumer, event_id: str):
        """
        Abstract helper method that parses data from an EventConsumer object
        to build the record to be written to time series database. Built records will
        differ depending on concrete implementations.

        Args:
            event_consumer (EventConsumer): EventConsumer object that contains the event payload
                                            to be parsed and written to the database.
            event_id (str): Useful for logging information about this event.
        Exceptions:
            Raises ebb_events `PayloadFormatException` if payload in EventConsumer does not match expected structure.
        """
        pass

    @abstractmethod
    def write_event_record(self, event_consumer: EventConsumer, context: dict) -> bool:
        """
        Main writer method that takes in the consumed event payload, parses the data, and writes
        records to the desired database table.

        Args:
            event_consumer (EventConsumer): EventConsumer object that contains the event payload
                                            to be parsed and written to the database.
            context (dict): any additional context.
        Returns:
            bool: True if the event was successfully written to the database; False otherwise.
        Exceptions:
            Raises 'TimeSeriesWriteException' if the writer is unable to write these records to the database for any reason.
        """
        pass

    @abstractmethod
    def bulk_write_event_records(
        self, event_consumers: list[EventConsumer], context: dict
    ) -> bool:
        """
        Building off of the write_event_record method - this method does a bulk write to the databse.

        In order for this to succeed, all EventConsumer objects in the list must contain the same
        common/shared/dimension data fields (e.g. organization, system, subsystem, device_id, serial_number, etc.)

        attributes that can differ include:
        - value readings
        - time stamps
        - event_ids

        Args:
            event_consumers (list[EventConsumer]): List of EventConsumer objects that contain the event payloads
                                            to be parsed and written to the database.
            context (dict): any additional context.
        Returns:
            bool: True if the events were successfully written to the database; False otherwise.
        Exceptions:
            Raises 'TimeSeriesWriteException' if the writer is unable to write these records to the database for any reason.
        """
