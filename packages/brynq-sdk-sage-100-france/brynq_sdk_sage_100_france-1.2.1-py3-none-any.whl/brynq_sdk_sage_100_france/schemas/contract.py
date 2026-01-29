import pandera as pa
import pandas as pd
from pandera.typing import Series, String, DateTime
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class ContractSchema(BrynQPanderaDataFrameModel):
    """Schema for validating contract data from Sage 100 France T_HST_CONTRAT table"""

    employee_number: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Employee number", alias="NumSalarie")
    history_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="History date", alias="DateHist")
    contract_start_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Contract start date", alias="DateDebutContrat")
    contract_end_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Contract end date", alias="DateFinContrat")
    contract_number: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Contract number", alias="NoContrat")
    contract_nature_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Contract nature code", alias="CodeNatureDeContrat")
    trial_period_end: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Trial period end date", alias="FinPeriodeEssai")
    start_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Start date", alias="DateDebut")
    administrative_situation: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Administrative situation", alias="SituationAdministrative")
    non_compete_clause: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Non-compete clause", alias="ClauseDeNonConcurrence")
    contract_ref_or_mi_contract_number: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 20}, description="Contract reference or MI contract number", alias="RefContratOuNoContratMi")
    entry_type: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Entry type", alias="TypeDEntree")
    last_worked_and_paid_day: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Last worked and paid day", alias="DernierJourTravailleEtPaye")
    departure_reason_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Departure reason code", alias="CodeMotifDepart")
    termination_notification_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Termination notification date", alias="DateNotificationRupture")
    dismissal_commitment_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Dismissal commitment date", alias="DateEngageLicenciement")
    notice_type_and_payment: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Notice type and payment", alias="TypeReaEtPaiementPreavis")
    notice_type_start_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Notice type start date", alias="DateDebutTypeDePreavis")
    notice_type_end_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Notice type end date", alias="DateFinTypeDePreavis")
    notice_type_and_payment_2: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Notice type and payment 2", alias="TypeReaEtPaiementPreavis_2")
    notice_type_start_date_2: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Notice type start date 2", alias="DateDebutTypeDePreavis_2")
    notice_type_end_date_2: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Notice type end date 2", alias="DateFinTypeDePreavis_2")
    notice_type_and_payment_3: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Notice type and payment 3", alias="TypeReaEtPaiementPreavis_3")
    notice_type_start_date_3: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Notice type start date 3", alias="DateDebutTypeDePreavis_3")
    notice_type_end_date_3: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Notice type end date 3", alias="DateFinTypeDePreavis_3")
    contract_reason_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Contract reason code", alias="CodeMotifDeContrat")
    replaced_employee_id: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Replaced employee ID", alias="MatriculeSalarieRemplace")
    temporary_worker: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Temporary worker flag", alias="Vacataire")
    vacation_nature_code: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 4}, description="Vacation nature code", alias="CodeNatureDeVacation")
    contract_comment: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 60}, description="Contract comment", alias="CommentaireContrat")
    contract_history_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=False, description="Contract history ID", alias="IdHstContrat")
    conventional_termination_date: Series[DateTime] = pa.Field(coerce=True, nullable=True, description="Conventional termination date", alias="DateRuptureConventionnelle")
    transaction_in_progress: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Transaction in progress", alias="TransactionEnCours")
    current_info: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, default=0, description="Current information flag", alias="InfoEnCours")
    attachment_siret: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 14}, description="Attachment SIRET", alias="SiretDeRattachement")
    derogatory_circuit: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Derogatory circuit", alias="CircuitDerogatoire")
    maintain_collective_agreement_affiliation: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Maintain collective agreement affiliation", alias="MaintienAffilAuxContCollOC")
    short_contract: Series[pd.Int64Dtype] = pa.Field(coerce=True, nullable=True, description="Short contract flag", alias="ContratCourt")
    previous_declarant_siret: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 14}, description="Previous declarant SIRET", alias="SiretDeclarantPrecedent")
    previous_contract_number: Series[String] = pa.Field(coerce=True, nullable=True, str_length={"max_value": 10}, description="Previous contract number", alias="NumeroContratPrecedent")

    class _Annotation:
        """Schema annotation for relationships and constraints"""
        primary_key = "contract_history_id"
        foreign_keys = {
            "employee_number": {
                "parent_schema": "EmployeeSchema",
                "parent_column": "employee_number",
                "cardinality": "N:1"
            }
        }

    class Config:
        """Schema configuration"""
        strict = True  # Ensure no additional columns are present
        coerce = True  # Try to coerce types when possible
