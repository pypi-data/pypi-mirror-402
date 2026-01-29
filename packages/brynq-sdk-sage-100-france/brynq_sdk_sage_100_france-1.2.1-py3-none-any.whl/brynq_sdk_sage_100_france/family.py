import pandas as pd
from .schemas.family import FamilySchema
from brynq_sdk_functions import Functions

class Family:
    """Class for interacting with Sage 100 France family history endpoints"""

    # Get column names from schema
    COLUMN_NAMES = list(FamilySchema.to_schema().columns.keys())
    
    def __init__(self, sage_100_france):
        """Initialize Family class
        
        Args:
            sage_100_france: Parent Sage 100 France instance for authentication and configuration
        """
        self.sage_100_france = sage_100_france
        self.db_table = "T_HST_FAMILLE"
    
    def get(self):
        """Get all family history records
        
        Returns:
            pandas.DataFrame: DataFrame containing family history data with schema validation
            
        Raises:
            ValueError: If there is an error processing the family data
        """
        family = self.sage_100_france.get(table_name=self.db_table, columns=self.COLUMN_NAMES)
        try:
            df = pd.DataFrame(family)
            if not df.empty:
                df.columns = self.COLUMN_NAMES
                valid_data, invalid_Data = Functions.validate_data(df, FamilySchema)
                return valid_data, invalid_Data
            return df
        except Exception as e:
            raise ValueError(f"There was an error processing the Family data: {e}")