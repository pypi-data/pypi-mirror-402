import pandas as pd
from .schemas.address import AddressSchema
from brynq_sdk_functions import Functions

class Address:
    """Class for interacting with Sage 100 France address history endpoints"""

    # Get column names from schema
    COLUMN_NAMES = list(AddressSchema.to_schema().columns.keys())
    
    def __init__(self, sage_100_france):
        """Initialize Address class
        
        Args:
            sage_100_france: Parent Sage 100 France instance for authentication and configuration
        """
        self.sage_100_france = sage_100_france
        self.db_table = "T_HST_ADRESSE"
    
    def get(self):
        """Get all address history records
        
        Returns:
            pandas.DataFrame: DataFrame containing address history data with schema validation
            
        Raises:
            ValueError: If there is an error processing the address data
        """
        address = self.sage_100_france.get(table_name=self.db_table, columns=self.COLUMN_NAMES)
        try:
            df = pd.DataFrame(address)
            if not df.empty:
                df.columns = self.COLUMN_NAMES
                valid_data, invalid_data = Functions.validate_data(df, AddressSchema)
                return valid_data, invalid_data
            return df
        except Exception as e:
            raise ValueError(f"There was an error processing the Address data: {e}")
