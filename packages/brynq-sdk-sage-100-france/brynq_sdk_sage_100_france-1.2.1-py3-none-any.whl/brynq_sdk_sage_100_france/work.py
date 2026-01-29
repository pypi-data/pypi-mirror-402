import pandas as pd
from typing import Union, List, Dict, Any
from brynq_sdk_functions import Functions
from .schemas.work import AssignmentSchema, WorkLocationSchema, AssignmentSchema

class Work:
    """Class for interacting with Sage 100 France work-related endpoints"""

    def __init__(self, employee):
        """Initialize Work class

        Args:
            sage_100_france: Parent Sage 100 France instance for authentication and configuration
        """
        self.employee = employee


    def import_assignment_data(self, df: pd.DataFrame):
        """
        Import Assignment (Assignment) data

        Args:
            df: DataFrame to import
        """
        # Add unique_code automatically - it's always "04" for Affectation
        df = df.copy()
        df['unique_code'] = "04"

        valid_data = AssignmentSchema(df)

        rows = self.employee.sage_100_france.prepare_formatted_rows(df=valid_data, schema=AssignmentSchema)

        self.employee.sage_100_france.add_rows_to_buffer(rows)


    def import_work_location_data(self, df: pd.DataFrame):
        """
        Import work location data

        Args:
            df: DataFrame to import
        """
        # Add unique_code automatically - it's always "03" for Work Location
        df = df.copy()
        df['unique_code'] = "03"

        valid_data = WorkLocationSchema(df)
        rows = self.employee.sage_100_france.prepare_formatted_rows(df=valid_data, schema=WorkLocationSchema)
        self.employee.sage_100_france.add_rows_to_buffer(rows)
