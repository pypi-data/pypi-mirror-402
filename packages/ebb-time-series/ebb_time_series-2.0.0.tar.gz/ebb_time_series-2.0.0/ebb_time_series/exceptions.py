class TimeSeriesWriteException(Exception):
    """Exception type raised for failure to write records to database"""

    def __init__(self, message="Unable to write records to database.", response={}):
        self.message = message
        self.response = response
        super().__init__(self.message)
