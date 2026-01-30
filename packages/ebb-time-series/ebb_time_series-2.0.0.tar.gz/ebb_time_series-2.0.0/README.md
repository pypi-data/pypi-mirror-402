# Ebb Time Series
EbbCarbon package for working with time series data and databases. Time series data is a type of data that is collected over certain time intervals and is used to analyze trends, patterns, and behavior over time. This `ebb-time-series` package is built to be used in tandem with the [ebb-events](https://pypi.org/project/ebb-events/) package to assist in the flow of time series data from event messages to various time series databases and and to read from various time series databases to export and analyze the data.

For writing to time series databases: Once an event is consumed off of a message broker, use this package to write the event's data to your desired database for storage and further analysis. The combined use of these two EbbCarbon packages will enable you to streamline your data pipeline from edge node all the way to the cloud. NOTE: In order to use this package, the event writers expect to receive `ebb-event EventConsumer` objects with payloads of the `ebb-event` structure.

For reading and exporting from time series databases: TBD...

# Use:
Install the `ebb-time-series` package from pip installer via: `pip install ebb-time-series`.
Use `ebb-time-series` to write your event message data to a database.
```python
from ebb_time_series.writers.aws_timestream_data_writer import AwsTimestreamDataWriter
from ebb_events.consumers.event_consumer import EventConsumer

my_ebb_event_payload = {...}  # payload matching ebb-event structure from message broker
my_consumer = EventConsumer(payload=my_ebb_event_payload)
my_writer = AwsTimestreamDataWriter(aws_region="my-aws-region", db_name="my-db-name", table_name="my-table-name")

# Parsing of data in my_consumer is abstracted away in this write_event_records method
try:
    my_writer.write_event_records(consumer=my_consumer)
except EbbTimeSeriesWriteException
    # handle exception here
```

# Data Structure:
The time series writer parses the data in the event payload expecting the data to follow this structure:
```python
{
    "my_variable_1": {
        "value": ___,
        "unites": ___,
    },
    "my_variable_2": {
        "value": ___,
        "unites": ___,
    },
    "my_variable_3": {
        "value": ___,
        "unites": ___,
    },
    ...
}
```

# Release new version to PyPI:
In order to release a new version to PyPI, run the following command pre-merging of PR:
1. `poetry version patch/minor/major`
2. `poetry build`

Once the PR is approved and merged. Checkout `main`, pull the latest, and run:
1. `poetry publish`

Check that your new release was successfully pushed to PyPI [here](https://pypi.org/project/ebb-time-series/)!