import pandas as pd
from .schemas.position import PositionSchema
from brynq_sdk_functions import Functions

class Position:
    """Class for interacting with Sage 100 France position endpoints"""

    # Get column names from schema
    COLUMN_NAMES = list(PositionSchema.to_schema().columns.keys())
    
    def __init__(self, sage_100_france):
        """Initialize Position class
        
        Args:
            sage_100_france: Parent Sage 100 France instance for authentication and configuration
        """
        self.sage_100_france = sage_100_france
        self.db_table = "T_POSTES"
    
    def get(self):
        """Get all position records
        
        Returns:
            pandas.DataFrame: DataFrame containing position data with schema validation
            
        Raises:
            ValueError: If there is an error processing the position data
        """
        position = self.sage_100_france.get(table_name=self.db_table, columns=self.COLUMN_NAMES)
        try:
            df = pd.DataFrame(position)
            if not df.empty:
                df.columns = self.COLUMN_NAMES
                valid_data, invalid_data = Functions.validate_data(df, PositionSchema)
                return valid_data, invalid_data
            return df
        except Exception as e:
            raise ValueError(f"There was an error processing the Position data: {e}")