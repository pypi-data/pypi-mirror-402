import pandas as pd
from .schemas.absence import AbsenceSchema
from brynq_sdk_functions import Functions

class Absence:
    """Class for interacting with Sage 100 France absence endpoints"""

    # Get column names from schema
    COLUMN_NAMES = list(AbsenceSchema.to_schema().columns.keys())
    
    def __init__(self, sage_100_france):
        """Initialize Absence class
        
        Args:
            sage_100_france: Parent Sage 100 France instance for authentication and configuration
        """
        self.sage_100_france = sage_100_france
        self.db_table = "T_MOTIFDABSENCE"
    
    def get(self):
        """Get all absence records
        
        Returns:
            pandas.DataFrame: DataFrame containing absence data with schema validation
        """
        absence = self.sage_100_france.get(table_name=self.db_table, columns=self.COLUMN_NAMES)
        try:
            df = pd.DataFrame(absence)
            if not df.empty:
                df.columns = self.COLUMN_NAMES
                valid_data, invalid_data = Functions.validate_data(df, AbsenceSchema)
                return valid_data, invalid_data
            return df
        except Exception as e:
            raise ValueError(f"There was an error processing the Absence data: {e}")
