import pandas as pd
from .schemas.event import EventSchema

class Event:
    """Class for interacting with Sage 100 France event endpoints"""

    def __init__(self, sage_100_france):
        """Initialize Event class

        Args:
            sage_100_france: Parent Sage 100 France instance for authentication and configuration
        """
        self.sage_100_france = sage_100_france

    def import_event_data(self, df: pd.DataFrame):
        """
        Import event data

        Args:
            df: DataFrame to import
        """
        # Add unique_code automatically - it's always "EV" for Event
        df = df.copy()
        df['unique_code'] = "EV"

        valid_data = EventSchema(df)

        rows = self.sage_100_france.prepare_formatted_rows(df=valid_data, schema=EventSchema)

        self.sage_100_france.add_rows_to_buffer(rows)
