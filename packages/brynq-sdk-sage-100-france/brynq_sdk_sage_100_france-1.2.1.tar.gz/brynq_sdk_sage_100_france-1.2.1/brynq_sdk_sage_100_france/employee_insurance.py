import pandas as pd
from typing import Union, List, Dict, Any
from .schemas.employee_insurance import EmployeeInsuranceSchema
from brynq_sdk_functions import Functions

class EmployeeInsurance:
    """Class for interacting with Sage 100 France employee insurance affiliations"""

    # Get column names from schema
    COLUMN_NAMES = list(EmployeeInsuranceSchema.to_schema().columns.keys())

    def __init__(self, employee):
        """Initialize EmployeeInsurance class

        Args:
            sage_100_france: Parent Sage 100 France instance for authentication and configuration
        """
        self.employee = employee
        self.db_table = "T_SALARIE_CONTRAT_SOCIAL"

    def get(self):
        """Get all employee insurance affiliation records

        Returns:
            pandas.DataFrame: DataFrame containing employee insurance data with schema validation

        Raises:
            ValueError: If there is an error processing the employee insurance data
        """
        employee_insurance = self.employee.sage_100_france.get(table_name=self.db_table, columns=self.COLUMN_NAMES)
        try:
            df = pd.DataFrame(employee_insurance)
            if not df.empty:
                df.columns = self.COLUMN_NAMES
                valid_data, invalid_data = Functions.validate_data(df, EmployeeInsuranceSchema)
                return valid_data, invalid_data
            return df
        except Exception as e:
            raise ValueError(f"There was an error processing the Employee Insurance data: {e}")

