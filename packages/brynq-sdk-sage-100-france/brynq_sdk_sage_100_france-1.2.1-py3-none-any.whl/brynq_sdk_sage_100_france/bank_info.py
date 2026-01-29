import pandas as pd
from brynq_sdk_functions import Functions

from .schemas.bank_info import BankInfoSchema


class BankInfo:
    """Class for interacting with Sage 100 France bank information endpoints"""

    # Get column names from schema
    COLUMN_NAMES = list(BankInfoSchema.to_schema().columns.keys())

    def __init__(self, sage_100_france):
        """Initialize BankInfo class

        Args:
            sage_100_france: Parent Sage 100 France instance for authentication and configuration
        """
        self.sage_100_france = sage_100_france
        self.db_table = "T_INFOBANQUE"

    def get(self):
        """Get all bank information records

        Returns:
            pandas.DataFrame: DataFrame containing bank information data with schema validation

        Raises:
            ValueError: If there is an error processing the bank information data
        """
        bank_info = self.sage_100_france.get(table_name=self.db_table, columns=self.COLUMN_NAMES)
        try:
            df = pd.DataFrame(bank_info)
            if not df.empty:
                df.columns = self.COLUMN_NAMES
                valid_data, invalid_data = Functions.validate_data(df, BankInfoSchema)
                return valid_data, invalid_data
            return df
        except Exception as e:
            raise ValueError(f"There was an error processing the Bank Info data: {e}")
