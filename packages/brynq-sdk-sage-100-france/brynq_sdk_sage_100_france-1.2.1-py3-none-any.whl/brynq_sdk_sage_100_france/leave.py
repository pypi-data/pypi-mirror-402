import pandas as pd
from .schemas.leave import LeaveSchema
from brynq_sdk_functions import Functions

class Leave:
    """Class for interacting with Sage 100 France leave history endpoints"""

    # Get column names from schema
    COLUMN_NAMES = list(LeaveSchema.to_schema().columns.keys())
    
    def __init__(self, sage_100_france):
        """Initialize Leave class
        
        Args:
            sage_100_france: Parent Sage 100 France instance for authentication and configuration
        """
        self.sage_100_france = sage_100_france
        self.db_table = "T_HST_CONGE"
    
    def get(self):
        """Get all leave history records
        
        Returns:
            pandas.DataFrame: DataFrame containing leave history data with schema validation
        """
        leave = self.sage_100_france.get(table_name=self.db_table, columns=self.COLUMN_NAMES)
        try:
            df = pd.DataFrame(leave)
            if not df.empty:
                df.columns = self.COLUMN_NAMES
                valid_data, invalid_data = Functions.validate_data(df, LeaveSchema)
                return valid_data, invalid_data
            return df
        except Exception as e:
            raise ValueError(f"There was an error processing the Leave data: {e}")