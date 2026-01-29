import pandas as pd
from .schemas.salary import SalaryGetSchema, SalarySchema
from brynq_sdk_functions import Functions

class Salary:
    """Class for interacting with Sage 100 France salary endpoints"""

    # Get column names from schema
    COLUMN_NAMES = list(SalaryGetSchema.to_schema().columns.keys())

    def __init__(self, sage_100_france):
        """Initialize Salary class

        Args:
            sage_100_france: Parent Sage 100 France instance for authentication and configuration
        """
        self.sage_100_france = sage_100_france
        self.db_table = "T_SAL"

    def get(self):
        """Get all salary records

        Returns:
            pandas.DataFrame: DataFrame containing salary data with schema validation

        Raises:
            ValueError: If there is an error processing the salary data
        """
        salary = self.sage_100_france.get(table_name=self.db_table, columns=self.COLUMN_NAMES)
        try:
            df = pd.DataFrame(salary)
            if df.empty:
                df.columns = self.COLUMN_NAMES
                valid_data, invalid_data= Functions.validate_data(df, SalaryGetSchema)
                return valid_data, invalid_data
            return df
        except Exception as e:
            raise ValueError(f"There was an error processing the Salary data: {e}")



