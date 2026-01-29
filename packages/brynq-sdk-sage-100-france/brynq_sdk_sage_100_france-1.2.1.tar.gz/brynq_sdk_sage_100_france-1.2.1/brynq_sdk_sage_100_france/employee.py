import pandas as pd
from typing import Dict, Any, Type
from pydantic import BaseModel
from brynq_sdk_functions import Functions
from .schemas.employee import EmployeeSchema, EmployeeExcelImport
from .schemas.employee import PersonnelRecordTimePageSchema
from .schemas.employee import RegistrationSchema
from .schemas.employee import CivilStatusSchema
from .schemas.employee import DadsUSchema
from .work import Work
from .employee_insurance import EmployeeInsurance
class Employee:
    """Class for interacting with Sage 100 France employee endpoints"""

    # Get column names from schema
    COLUMN_NAMES = list(EmployeeSchema.to_schema().columns.keys())

    def __init__(self, sage_100_france):
        """Initialize Employees class

        Args:
            sage_100_france: Parent Sage 100 France instance for authentication and configuration
        """
        self.sage_100_france = sage_100_france
        self.work = Work(self)
        self.insurance = EmployeeInsurance(self)
        self.db_table = "T_CONTACT"



    def get(self):
        """Get all employees

        Returns:
            pandas.DataFrame: DataFrame containing employee data with schema validation

        Raises:
            ValueError: If there is an error processing the employee data
        """
        employee = self.sage_100_france.get(table_name=self.db_table, columns=self.COLUMN_NAMES)
        try:
            df = pd.DataFrame(employee)
            if not df.empty:
                df.columns = self.COLUMN_NAMES
                valid_data, invalid_data = Functions.validate_data(df, EmployeeSchema)
                return valid_data, invalid_data
            return df
        except Exception as e:
            raise ValueError(f"There was an error processing the Employee data: {e}")

    def import_registration_data(self, df: pd.DataFrame):
        """
        Import registration data

        Args:
            df: DataFrame to import
        """
        # Add unique_code automatically - it's always "01" for Registration
        df = df.copy()
        df['unique_code'] = "01"

        valid_data = RegistrationSchema(df)

        rows = self.sage_100_france.prepare_formatted_rows(df=valid_data, schema=RegistrationSchema)

        self.sage_100_france.add_rows_to_buffer(rows)


    def export_to_excel(
        self,
        df: pd.DataFrame,
        output_excel_path: str,
        schema: Type[BaseModel] = EmployeeExcelImport
    ):
        """
        Validate employee DataFrame with Pydantic schema and export to Excel.

        Args:
            df: pandas DataFrame with employee data
            output_excel_path: Path to output Excel file
            schema: Pydantic BaseModel schema for validation (default: EmployeeExcelImport)

        Returns:
            Tuple of (validated_df, error_count)
        """

        # Warning for custom schemas
        if schema != EmployeeExcelImport:
            print("⚠ WARNING: Using custom schema.")
            print("⚠ For Sage 100 France import Excel:")
            print("⚠ Field order in schema MUST match EXACTLY the format definition.")
            print("⚠ Fields must be defined in schema in the same order as in the format.")
            print()

        records = df.to_dict("records")

        validated_rows = []
        error_count = 0

        for i, rec in enumerate(records, start=1):
            try:
                m = schema.model_validate(rec)
                validated_rows.append(m.model_dump(by_alias=True))
            except Exception as e:
                print(f"✗ Row {i} validation error: {e}")
                error_count += 1

        if not validated_rows:
            raise ValueError("No valid rows found in data")

        validated_df = pd.DataFrame(validated_rows)
        validated_df.to_excel(output_excel_path, index=False, sheet_name="Employees")

        print(f"✓ Validated {len(validated_rows)} rows successfully")
        if error_count:
            print(f"✗ {error_count} rows had validation errors")

        return output_excel_path



    def _generate_child_field_specs(self, max_children: int) -> dict:
        """
        Generate field specifications for child data dynamically.

        Args:
            max_children: Maximum number of children to support

        Returns:
            Dictionary with child field specifications
        """
        child_specs = {}

        # Starting position for first child (after number_of_children field)
        base_position = 364

        for child_num in range(1, max_children + 1):
            # Each child takes 62 positions (2+20+30+8+1+1)
            child_base_pos = base_position + ((child_num - 1) * 62)

            child_specs.update({
                f'child_{child_num}_number': {'position': child_base_pos, 'length': 2},
                f'child_{child_num}_first_name': {'position': child_base_pos + 2, 'length': 20},
                f'child_{child_num}_last_name': {'position': child_base_pos + 22, 'length': 30},
                f'child_{child_num}_birth_date': {'position': child_base_pos + 52, 'length': 8},
                f'child_{child_num}_gender': {'position': child_base_pos + 60, 'length': 1},
                f'child_{child_num}_dependent': {'position': child_base_pos + 61, 'length': 1},
            })

        return child_specs

    def _fill_missing_child_data(self, df: pd.DataFrame, max_children: int = 100) -> pd.DataFrame:
        """
        Fill missing child data with default values for up to max_children.

        For each child that doesn't exist in the data, fill with:
        - child_X_number: 0
        - child_X_first_name: ""
        - child_X_last_name: ""
        - child_X_birth_date: ""
        - child_X_gender: 0
        - child_X_dependent: 0

        Args:
            df: DataFrame with child data
            max_children: Maximum number of children to support

        Returns:
            DataFrame with all child fields filled
        """
        df = df.copy()

        # Define default values for missing child data
        child_defaults = {
            'number': 0,  # Numeric field
            'first_name': "",
            'last_name': "",
            'birth_date': "",
            'gender': 0,  # Numeric field (0 = not specified)
            'dependent': 0  # Numeric field (0 = not dependent)
        }

        # Collect all missing columns and their default values
        missing_columns = {}

        # Check for missing child columns (1 to max_children)
        for child_num in range(1, max_children + 1):
            for field, default_value in child_defaults.items():
                column_name = f"child_{child_num}_{field}"
                if column_name not in df.columns:
                    # Column doesn't exist, add to missing columns
                    missing_columns[column_name] = [default_value] * len(df)
                else:
                    # Column exists but may have NaN values, fill them
                    df[column_name] = df[column_name].fillna(default_value)

        # Add all missing columns at once using pd.concat for better performance
        if missing_columns:
            missing_df = pd.DataFrame(missing_columns, index=df.index)
            df = pd.concat([df, missing_df], axis=1)

        return df

    def import_civil_status_data(self, df: pd.DataFrame):
        """
        Import civil status data

        Args:
            df: DataFrame to import
        """
        # Add unique_code automatically - it's always "02" for Civil Status
        df = df.copy()
        df['unique_code'] = "02"

        df = self._fill_missing_child_data(df, max_children=99)

        valid_data = CivilStatusSchema(df)

        rows = self.sage_100_france.prepare_formatted_rows(df=valid_data, schema=CivilStatusSchema)

        self.sage_100_france.add_rows_to_buffer(rows)

    def import_time_page_data(self, df: pd.DataFrame):
        """
        Import time page data

        Args:
            df: DataFrame to import
        """
        # Add unique_code automatically - it's always "GT" for Time Page
        df = df.copy()
        df['unique_code'] = "GT"

        valid_data = PersonnelRecordTimePageSchema(df)

        rows = self.sage_100_france.prepare_formatted_rows(df=valid_data, schema=PersonnelRecordTimePageSchema)

        self.sage_100_france.add_rows_to_buffer(rows)

    def import_dads_u_data(self, df: pd.DataFrame):
        """
        Import DADS-U (Données DADS-U) data

        Args:
            df: DataFrame to import
        """
        # Add unique_code automatically - it's always "DU" for DADS-U
        df = df.copy()
        df['unique_code'] = "DU"

        valid_data = DadsUSchema(df)

        rows = self.sage_100_france.prepare_formatted_rows(df=valid_data, schema=DadsUSchema)

        self.sage_100_france.add_rows_to_buffer(rows)
