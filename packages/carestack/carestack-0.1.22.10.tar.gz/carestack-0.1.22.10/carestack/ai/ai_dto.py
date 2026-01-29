from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator

from carestack.encounter.dto.encounter_dto import DoctorDetails, PatientDetails

class EncryptionResponseType(BaseModel):
    model_config= ConfigDict(populate_by_name= True)
    encrypted_payload: str = Field(..., alias="encryptedPayload")

class DecryptionResponseType(BaseModel):
    model_config= ConfigDict(populate_by_name=True)
    decrypted_payload: dict = Field(..., alias="decryptedPayload")
    protected_headers: dict = Field(..., alias="protectedHeader")

class ProcessDSDto(BaseModel):
    """
    Data Transfer Object for processing discharge summary requests.

    Attributes:
        case_type (str): The type of case (e.g., `OPConsultation`, `DischargeSummary`). Serialized as `caseType`.
        files (Optional[list[str]]): List of file paths or file identifiers to be processed.
        encrypted_data (Optional[str]): Pre-encrypted data, if available.
        public_key (Optional[str]): Public key for encryption, if required.
        encounter_id (Optional[str]): 
            Unique identifier for the encounter, serialized as `encounterId`, used for partial upload. 
            Example: "enc12345"
        date (Optional[str]): 
            The date of the request, usually in ISO 8601 format. 
            Example: "2025-09-23T12:30:00Z"
        
        Example:
        ProcessDSDto(
             files=["file1.pdf"],
             public_key="test-key",
             encounter_id="enc123",
             date="2025-09-23T12:30:00Z"
         )
        ProcessDSDto(files=['file1.pdf'], encrypted_data=None, public_key='test-key',
                     encounter_id='enc123', date='2025-09-23T12:30:00Z')
    """

    model_config = ConfigDict(populate_by_name=True)
    files: Optional[list[str]] = None
    encrypted_data: Optional[str] = None
    public_key: Optional[str] = None
    encounter_id: Optional[str] = Field(None, alias="encounterId")
    date: Optional[str] = None
    callback_url: Optional[str] = Field(None, alias="callbackUrl")


class JobResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, exclude_none=True)
    
    jobId: Optional[str] = None
    recordId: Optional[str] = None
    status: Optional[str] = None
    estimatedCompletionMs: Optional[int] = None
    message: Optional[str] = None


class CallbackPayload(BaseModel):    
    model_config = ConfigDict(populate_by_name=True, exclude_none=True)

    jobId: Optional[str] = None
    recordId: Optional[str] = None
    status: Optional[str] = None
    result: Optional[Any] = None
    childJobId: Optional[str] = None
    completedAt: Optional[str] = None
    error: Optional[Any] = None

class PreviewPdfResponse(BaseModel):
    fileName: Optional[str] = None
    mimeType: Optional[str] = None
    pdf: Optional[str] = None 

class DischargeSummaryResponse(BaseModel):
    """
    Represents the response for a discharge summary generation request.

    Attributes:
        id (str): Unique identifier for the discharge summary.
        discharge_summary (Optional[dict[str, Any]]): The generated discharge summary content, if available.
        extracted_data (dict[str, Any]): Extracted clinical data from the input.
        fhir_bundle (dict[str, Any]): FHIR-compliant bundle generated from the case data.
    """

    id: Optional[str] = Field(None)
    discharge_summary: Optional[dict[str, Any]] = Field(None, alias="dischargeSummary")
    extracted_data: Optional[dict[str, Any]] = Field(None, alias="extractedData")
    fhir_bundle: Optional[dict[str, Any]] = Field(None, alias="fhirBundle")
    encrypted_response: Optional[str] = Field(None, alias="encryptedResponse")

    @field_validator("discharge_summary", mode="before")
    @classmethod
    def handle_empty_string(cls, value):
        if value == "" or value is None:
            return None
        if isinstance(value, dict):
            return value
        raise ValueError("dischargeSummary must be a dictionary or empty string")

class RadiologySummaryResponse(RootModel[list[dict[str, Any]]]):
    pass
    
class GenerateFhirBundleDto(BaseModel):
    """
    Data Transfer Object for generating a FHIR bundle.

    Attributes:
        case_type (str): The type of case (e.g., `OPConsultation`, `DischargeSummary`). Serialized as `caseType`.
        enable_extraction (bool): Flag to enable data extraction from the provided documents.
        document_references (list[str]): List of document references to be included in the bundle.
        record_id (Optional[str]): Identifier for the record, if available. Serialized as `recordId`.
        extracted_data (Optional[dict[str, Any]]): Extracted clinical data for the bundle.
        encrypted_data (Optional[str]): Pre-encrypted data, if available.
        public_key (Optional[str]): Public key for encryption, if required.
    """

    model_config = ConfigDict(populate_by_name=True)
    case_type: str = Field(..., alias="caseType")
    enable_extraction: bool = Field(..., alias="enableExtraction")
    record_id: Optional[str] = Field(None, alias="recordId")
    extracted_data: Optional[dict[str, Any]] = Field(None, alias="extractedData")
    encrypted_data: Optional[str] = Field(None, alias="encryptedData")
    patient_details: Optional[PatientDetails] = Field(None, alias="patientDetails")
    doctors_details: Optional[list[DoctorDetails]] = Field(None, alias="doctorsDetails")
    document_references: list[str] = Field(..., alias="documentReferences")
    public_key: Optional[str] = Field(None, alias="publicKey")


class FhirBundleResponse(RootModel[dict[str, Any]]):
    """
    Represents the response for a FHIR bundle generation request.

    The root model is a dictionary containing the FHIR bundle content.
    """

    pass

