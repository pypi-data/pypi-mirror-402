import pandas as pd
from .schemas.contract import ContractSchema
from brynq_sdk_functions import Functions

class Contract:
    """Class for interacting with Sage 100 France contract endpoints"""

    # Get column names from schema
    COLUMN_NAMES = list(ContractSchema.to_schema().columns.keys())

    def __init__(self, sage_100_france):
        """Initialize Contract class

        Args:
            sage_100_france: Parent Sage 100 France instance for authentication and configuration
        """
        self.sage_100_france = sage_100_france
        self.db_table = "T_HST_CONTRAT"

    def get(self):
        """Get all contract records

        Returns:
            pandas.DataFrame: DataFrame containing contract data with schema validation

        Raises:
            ValueError: If there is an error processing the contract data
        """
        contract = self.sage_100_france.get(table_name=self.db_table, columns=self.COLUMN_NAMES)
        try:
            df = pd.DataFrame(contract)
            if not df.empty:
                df.columns = self.COLUMN_NAMES
                valid_data,  =  Functions.validate_data(df, ContractSchema)
                return valid_data
        except Exception as e:
            raise ValueError(f"There was an error processing the Contract data: {e}")
