import pandas as pd
from typing import Union, List, Dict, Any
from .schemas.insurance import InsuranceSchema
from brynq_sdk_functions import Functions

class Insurance:
    """Class for interacting with Sage 100 France insurance endpoints"""

    # Get column names from schema
    COLUMN_NAMES = list(InsuranceSchema.to_schema().columns.keys())

    def __init__(self, sage_100_france):
        """Initialize Insurance class

        Args:
            sage_100_france: Parent Sage 100 France instance for authentication and configuration
        """
        self.sage_100_france = sage_100_france
        self.db_table = "T_CONTRAT_SOCIAL"

    def get(self):
        """Get all insurance records

        Returns:
            pandas.DataFrame: DataFrame containing insurance data with schema validation

        Raises:
            ValueError: If there is an error processing the insurance data
        """
        insurance = self.sage_100_france.get(table_name=self.db_table, columns=self.COLUMN_NAMES)
        try:
            df = pd.DataFrame(insurance)
            if not df.empty:
                df.columns = self.COLUMN_NAMES
                valid_data, invalid_data = Functions.validate_data(df, InsuranceSchema)
                return valid_data, invalid_data
            return df
        except Exception as e:
            raise ValueError(f"There was an error processing the Insrance data: {e}")
