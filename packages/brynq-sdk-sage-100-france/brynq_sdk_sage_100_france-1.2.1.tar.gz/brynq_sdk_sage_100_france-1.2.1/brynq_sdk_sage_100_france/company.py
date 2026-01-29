import pandas as pd
import pandera as pa
from pandera.typing import Series
from typing import Union, List, Dict, Any
from .schemas.company import CompanySchema
from brynq_sdk_functions import Functions

class Company:
    """Class for interacting with Sage 100 France company endpoints"""

    # Get column names from schema
    COLUMN_NAMES = list(CompanySchema.to_schema().columns.keys())

    def __init__(self, sage_100_france):
        """Initialize Company class

        Args:
            sage_100_france: Parent Sage 100 France instance for authentication and configuration
        """
        self.sage_100_france = sage_100_france
        self.db_table = "T_SOCIETE"

    def get(self):
        """Get company information

        Returns:
            pandas.DataFrame: DataFrame containing company data with schema validation

        Raises:
            ValueError: If there is an error processing the company data
        """
        company = self.sage_100_france.get(table_name=self.db_table, columns=self.COLUMN_NAMES)
        try:
            df = pd.DataFrame(company)
            if not df.empty:
                df.columns = self.COLUMN_NAMES
                valid_data, invalid_data = Functions.validate_data(df, CompanySchema)
                return valid_data, invalid_data
            return df
        except Exception as e:
            raise ValueError(f"There was an error processing the Company data: {e}")

