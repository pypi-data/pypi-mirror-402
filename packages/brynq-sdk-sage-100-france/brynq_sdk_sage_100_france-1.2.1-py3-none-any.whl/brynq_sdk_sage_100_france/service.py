import pandas as pd
from .schemas.service import ServiceSchema
from brynq_sdk_functions import Functions

class Service:
    """Class for interacting with Sage 100 France service endpoints"""

    # Get column names from schema
    COLUMN_NAMES = list(ServiceSchema.to_schema().columns.keys())
    
    def __init__(self, sage_100_france):
        """Initialize Service class
        
        Args:
            sage_100_france: Parent Sage 100 France instance for authentication and configuration
        """
        self.sage_100_france = sage_100_france
        self.db_table = "T_SERVICE"
    
    def get(self):
        """Get all service records
        
        Returns:
            pandas.DataFrame: DataFrame containing service data with schema validation
        """
        service = self.sage_100_france.get(table_name=self.db_table, columns=self.COLUMN_NAMES)
        try:
            df = pd.DataFrame(service)
            if not df.empty:
                df.columns = self.COLUMN_NAMES
                valid_data, invalid_data = Functions.validate_data(df, ServiceSchema)
                return valid_data, invalid_data
            return df
        except Exception as e:
            raise ValueError(f"There was an error processing the Service data: {e}")