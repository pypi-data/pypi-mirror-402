from brynq_sdk_functions import BrynQPanderaDataFrameModel
from typing import Optional
import pandas as pd
import pandera as pa
from pandera.typing import Series, String, Float

class EventSchema(BrynQPanderaDataFrameModel):
    """Schema for Event (Évènement) from Sage 100 France."""
    unique_code: Optional[Series[String]] = pa.Field(eq="EV", coerce=True, nullable=True, description="EV", metadata={"position": 1, "length": 2})
    employee_id: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Matricule", metadata={"position": 3, "length": 10})
    event_nature_code: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 4}, description="Code nature d'événements", metadata={"position": 13, "length": 4})
    start_date: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date de début", metadata={"position": 17, "length": 8})
    start_time: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Heure de début", metadata={"position": 25, "length": 5})
    end_date: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date de fin", metadata={"position": 30, "length": 8})
    end_time: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 5}, description="Heure de fin", metadata={"position": 38, "length": 5})
    quantity: Optional[Series[Float]] = pa.Field(coerce=True, nullable=True, description="Nombre", metadata={"position": 43, "length": 12})
    assignment_code_1: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Code affectation 1", metadata={"position": 55, "length": 10})
    assignment_number_1: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Numéro de l'affectation 1", metadata={"position": 65, "length": 10})
    assignment_code_2: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Code affectation 2", metadata={"position": 75, "length": 10})
    assignment_number_2: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Numéro de l'affectation 2", metadata={"position": 85, "length": 10})
    assignment_code_3: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Code affectation 3", metadata={"position": 95, "length": 10})
    assignment_number_3: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Numéro de l'affectation 3", metadata={"position": 105, "length": 10})
    assignment_code_4: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Code affectation 4", metadata={"position": 115, "length": 10})
    assignment_number_4: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Numéro de l'affectation 4", metadata={"position": 125, "length": 10})
    calculated_event_indicator: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Indicateur d'événement calculé", metadata={"position": 135, "length": 1})
    deleted_event_indicator: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Indicateur d'événement Supprimé", metadata={"position": 136, "length": 1})
    overtime_generated_indicator: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Indicateur d'événement HS générée", metadata={"position": 137, "length": 1})
    compensatory_rest_hour_generated_indicator: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Indicateur d'événement heure RC générée", metadata={"position": 138, "length": 1})
    overtime_origin_indicator: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Indicateur d'événement origine d'HS", metadata={"position": 139, "length": 1})
    compensatory_rest_origin_indicator: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Indicateur d'événement origine de RC", metadata={"position": 140, "length": 1})
    compensatory_rest_day_generated_indicator: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Indicateur d'événement jour de RC généré", metadata={"position": 141, "length": 1})
    automatically_generated_indicator: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Indicateur d'événement généré automatiquement", metadata={"position": 142, "length": 1})
    imported_event_indicator: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Indicateur d'événement importé", metadata={"position": 143, "length": 1})
    reserved_area: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 7}, description="Zone réservée", metadata={"position": 144, "length": 7})
    daily_count: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Nombre par jour", metadata={"position": 151, "length": 1})
    calculated_value: Optional[Series[Float]] = pa.Field(coerce=True, nullable=True, description="Valeur calculée", metadata={"position": 152, "length": 12})
    absence_reason_code: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Code du motif d'absence", metadata={"position": 164, "length": 10})
    comment: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 30}, description="Commentaire", metadata={"position": 174, "length": 30})
    creation_date: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date de création", metadata={"position": 204, "length": 8})
    creation_time: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 11}, description="Heure de création", metadata={"position": 212, "length": 11})
    user_code: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 3}, description="Code utilisateur", metadata={"position": 223, "length": 3})
    afternoon_indicator: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Après-midi (0: Non et 1: Oui)", metadata={"position": 226, "length": 1})
    morning_indicator: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Matin (0: Non et 1: Oui)", metadata={"position": 227, "length": 1})
    validity_date: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Date de validité", metadata={"position": 228, "length": 8})
    assignment_code_1_extended: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 13}, description="Code affectation 1", metadata={"position": 236, "length": 13})
    assignment_code_2_extended: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 13}, description="Code affectation 2", metadata={"position": 249, "length": 13})
    assignment_code_3_extended: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 13}, description="Code affectation 3", metadata={"position": 262, "length": 13})
    assignment_code_4_extended: Optional[Series[String]] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 13}, description="Code affectation 4", metadata={"position": 275, "length": 13})

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "employee_id"
        foreign_keys = {}

    class Config:
        """Schema configuration"""
        coerce = True
        strict = False
