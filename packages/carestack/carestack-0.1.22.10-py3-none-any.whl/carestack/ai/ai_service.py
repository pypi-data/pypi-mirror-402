from datetime import datetime, timezone
import logging
import base64
from typing import Any, Dict, Type, TypeVar

from pydantic import BaseModel, ValidationError

from carestack.ai.ai_utils import AiUtilities
from carestack.base.base_service import BaseService
from carestack.base.base_types import ClientConfig
from carestack.base.errors import EhrApiError
from carestack.common.enums import AI_ENDPOINTS, HealthInformationTypes
from carestack.ai.ai_dto import (
    JobResponse,
    FhirBundleResponse,
    GenerateFhirBundleDto,
    ProcessDSDto,
    CallbackPayload,
    PreviewPdfResponse,
)

_DTO_T = TypeVar("_DTO_T", bound=BaseModel)


class AiService(BaseService):
    """
        High-level interface for AI-powered healthcare document generation.

        This service allows SDK users to interact with CareStack AI endpoints for:
        - Generating discharge summaries
        - Generating OP consultation summaries
        - Generating radiology reports
        - Generating FHIR bundles
        - Generating care plans
        - Performing partial uploads for discharge summaries
        - Triggering discharge summary generation

        Key Features:
            * Validates input data using Pydantic models
            * Handles encryption of sensitive data before transmission
            * Provides robust error handling and logging

        Args:
            config (ClientConfig): API credentials and settings for service initialization.

        Raises:
            EhrApiError: Raised for validation, API, or unexpected errors.

        Example:
            ```python
            config = ClientConfig(api_key="your_api_key")
            service = AiService(config)

            summary = await service.generate_discharge_summary({...})   
            fhir_bundle = await service.generate_fhir_bundle({...})
            ```"
    """

    def __init__(self, config: ClientConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.utilities = AiUtilities(config)

    async def _validate_data(
        self, dto_type: Type[_DTO_T], request_data: dict[str, Any]
    ) -> _DTO_T:
        """
        Validate dictionary data against a Pydantic model.

        This internal utility ensures that the provided dictionary matches the expected schema for the AI API.
        Raises an EhrApiError if validation fails.

        Args:
            dto_type (Type[_DTO_T]): The Pydantic model class to validate against.
            request_data (dict): The data to validate.

        Returns:
            _DTO_T: An instance of the validated Pydantic model.

        ### Raises:
            EhrApiError: If validation fails.
        """
        try:
            validated_instance: _DTO_T = dto_type(**request_data)
            return validated_instance
        except ValidationError as err:
            self.logger.error(
                f"Pydantic validation failed: {err.errors()}", exc_info=True
            )
            raise EhrApiError(f"Validation failed: {err.errors()}", 400) from err

    async def generate_case_summary(
        self, process_data: dict[str, Any], case_type: str
    ) -> JobResponse:
        """
        Generic case summary generator for all case types (DischargeSummary, OpConsultation, Radiology).
        """
        self.logger.info(f"Starting generation of {case_type} summary with data: {process_data}")

        try:
            process_dto: ProcessDSDto = await self._validate_data(ProcessDSDto, process_data)

            # Throw error if no encryptedData or files
            if not process_dto.encrypted_data and not process_dto.files:
                raise ValueError("No files or encrypted data provided.")
            
            if process_dto.files:
                await self.utilities.validate_files(process_dto.files)

            # Use encryptedData if provided, else encrypt files
            if process_dto.encrypted_data:
                encrypted_data = process_dto.encrypted_data
            else:
                payload_to_encrypt = {"files": process_dto.files}
                encrypted_data = await self.utilities.encryption(payload=payload_to_encrypt)

            payload = {
                "caseType": case_type,
                "encryptedData": encrypted_data,
                "callbackUrl": process_dto.callback_url,
            }

            if process_dto.public_key:
                payload["publicKey"] = process_dto.public_key
            response: JobResponse = await self.post(
                AI_ENDPOINTS.GENERATE_DISCHARGE_SUMMARY,
                payload,
                response_model=JobResponse,
            )

            return response

        except EhrApiError as e:
            self.logger.error(f"EHR API Error during {case_type} summary generation: {e.message}", exc_info=True)
            raise
        except ValueError as e:
            self.logger.error(f"Validation error in {case_type} summary generation: {e}", exc_info=True)
            raise EhrApiError(str(e), 422) from e
        except Exception as error:
            error_message = str(error)
            self.logger.error(f"Unexpected error in {case_type} summary generation: {error_message}", exc_info=True)
            raise EhrApiError(
                f"An unexpected error occurred while generating {case_type} summary: {error_message}", 500
            ) from error


    async def generate_fhir_bundle(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Generates a FHIR bundle based on the provided data.

        This method validates and processes the input, encrypts extracted data if necessary, and sends it to the AI API
        to generate a FHIR-compliant bundle. Use this method to automate generation of interoperable FHIR bundles from structured clinical data.

        Attributes:
            generate_fhir_bundle_data (GenerateFhirBundleDto): GenerateFhirBundleDto containing required inputs for generating the bundle.

        ### Args:
            generate_fhir_bundle_data (dict): Dictionary containing:
                - caseType (str): Type of the case (`inpatient`, `outpatient`, etc.)
                - enableExtraction (bool): Flag to enable data extraction from provided documents.
                - documentReferences (list[str]): List of document references to include in the bundle.
                - recordId (Optional[str]): Unique identifier for the record.
                - extractedData (Optional[dict]): Structured clinical data to generate the bundle.
                - encryptedData (Optional[str]): If provided, skips encryption and uses this encrypted payload.
                - publicKey (Optional[str]): Required if using `extractedData` without pre-encryption.

        ### Returns:
            dict[str, Any]: The generated FHIR-compliant bundle.
                Example:
                {
                    "resourceType": "Bundle",
                    "type": "document",
                    "entry": [
                        {
                            "resource": {
                                "resourceType": "Patient",
                                "id": "123",
                                ...
                            }
                        },
                        ...
                    ]
                }

        Raises:
            ValidationError: If input fails Pydantic model validation.
            EhrApiError: Raised on API failure (status 400/422/500).
            ValueError: If both `extractedData` and `encryptedData` are missing.

        ### Example (Success):

            response = await service.generate_fhir_bundle({
                "caseType": "DischargeSummary",
                "enableExtraction": True,
                "documentReferences": ["doc123", "doc456"],
                "recordId": "rec-789",
                "extractedData": {
                    "patientName": "John Doe",
                    "diagnosis": "Hypertension",
                    "treatment": "Medication and lifestyle changes"
                },
                "publicKey": "-----BEGIN PUBLIC KEY-----...",
            })

            print(response)

            Output will look like:

            {
                "resourceType": "Bundle",
                "entry": [
                    {"resource": {"resourceType": "Patient", "id": "123", ...}},
                    ...
                ]
            }

        ### Example (Validation Failure):

            await service.generate_fhir_bundle({
                "caseType": "DischargeSummary"
            })
            # Raises EhrApiError: No extracted data or encrypted data provided (422)
        """
        self.logger.info(f"Starting generation of FHIR bundle with data: {data}")
        try:
            validated_data: GenerateFhirBundleDto = await self._validate_data(
                GenerateFhirBundleDto, data
            )
            encryption_payload: dict[str, Any] = {}
            if validated_data.enable_extraction:
                if not validated_data.extracted_data:
                    raise ValueError("No extracted data is provided.")
                else:
                    encryption_payload["extractedData"] = validated_data.extracted_data
            else:
                if validated_data.patient_details and validated_data.doctors_details:
                    encryption_payload["patientDetails"] = (
                        validated_data.patient_details.model_dump(by_alias=True)
                    )
                    encryption_payload["practitionersDetails"] = [
                        doc.model_dump(by_alias=True)
                        for doc in validated_data.doctors_details
                    ]
                else:
                    raise ValueError("patient and practitioner details are required.")

            encryption_payload["documentReferences"] = (
                validated_data.document_references
            )
            encryptedData = await self.utilities.encryption(payload=encryption_payload)

            payload = {
                "caseType": validated_data.case_type,
                "enableExtraction": validated_data.enable_extraction,
                "encryptedData": encryptedData,
            }

            if validated_data.record_id:
                payload["recordId"] = validated_data.record_id

            if validated_data.public_key:
                payload["publicKey"] = validated_data.public_key

            fhir_bundle_response: FhirBundleResponse = await self.post(
                AI_ENDPOINTS.GENERATE_FHIR_BUNDLE,
                payload,
                response_model=FhirBundleResponse,
            )

            return fhir_bundle_response.root

        except EhrApiError as e:
            self.logger.error(
                f"EHR API Error during FHIR bundle generation: {e.message}",
                exc_info=True,
            )
            raise
        except ValueError as e:
            self.logger.error(
                f"Validation error in FHIR bundle generation: {e}", exc_info=True
            )
            raise EhrApiError(str(e), 422) from e
        except Exception as error:
            error_message = str(error)
            self.logger.error(
                f"Unexpected error in generate_fhir_bundle: {error_message}",
                exc_info=True,
            )
            raise EhrApiError(
                "An unexpected error occurred while generating FHIR bundle: "
                f"{error_message}",
                500,
            ) from error
        

    async def generate_discharge_summary(self, process_data: dict[str, Any]) -> JobResponse:
        """
            Initiate AI-based generation of a discharge summary.

            This method delegates to `generate_case_summary` after supplying the
            `DISCHARGE_SUMMARY` case type. It validates input data, performs encryption
            when required (inside `generate_case_summary`), and submits the request to
            the AI service. The API responds asynchronously, returning a `JobResponse`
            containing job metadata for tracking completion status.

            Args:
                process_data (dict[str, Any]):
                    Input payload containing any of the following:
                        - files (list[str]): Raw files to encrypt and process.
                        - encryptedData (str): Pre-encrypted payload. If provided,
                        no encryption will be performed.
                        - publicKey (str, optional): Public key used for encryption.
                        - callbackUrl (str, optional): URL the AI service will call
                        with job completion status.

            Returns:
                JobResponse:
                    Contains job tracking information:
                        - jobId (str): Unique ID for the submitted job.
                        - recordId (str): Record identifier associated with the job.
                        - status (str): Initial job status.
                        - estimatedCompletionMs (int): Estimated time to completion.
                        - message (str): Additional status or informational message.

            Raises:
                EhrApiError:
                    - If input validation fails (wrapped ValueError → 422).
                    - If the AI API returns 400 / 422 / 500 responses.
                Exception:
                    - Any unexpected error is wrapped into an EhrApiError(500).

            Example:
                ```python
                response = await service.generate_discharge_summary({
                    "files": ["case_123.pdf"],
                    "publicKey": "xyz-public-key"
                })

                print(response.jobId)
        """
        return await self.generate_case_summary(process_data, HealthInformationTypes.DISCHARGE_SUMMARY.value)


    async def generate_op_consultation_summary(self, process_data: dict[str, Any]) -> JobResponse:
        """
            Initiate AI-based generation of an OP consultation summary.

            This method delegates to `generate_case_summary` with the case type set
            to `OPCONSULTATION`. The method handles validation, optional encryption,
            and submission of the job request to the AI processing service. The result
            is an asynchronous job descriptor, not the final OP consultation summary.

            Args:
                process_data (dict[str, Any]):
                    Input payload containing any of the following:
                        - files (list[str]): Source files to encrypt and process.
                        - encryptedData (str): Pre-encrypted payload; bypasses encryption.
                        - publicKey (str, optional): Public key used for encryption.
                        - callbackUrl (str, optional): URL to receive async job status callbacks.

            Returns:
                JobResponse:
                    Contains job metadata for tracking:
                        - jobId (str): Unique identifier for the submitted AI job.
                        - recordId (str): Associated record identifier.
                        - status (str): Initial job status.
                        - estimatedCompletionMs (int): Estimated completion time.
                        - message (str): Informational or status message.

            Raises:
                EhrApiError:
                    Raised on validation failure, encryption error, or AI API errors
                    (400, 422, 500).
                Exception:
                    Any unexpected exception is wrapped into an EhrApiError(500).

            Example:
                ```python
                response = await service.generate_op_consultation_summary({
                    "files": ["op_notes.pdf"],
                    "publicKey": "xyz-public-key"
                })

                print(response.jobId)
                ```
        """
        return await self.generate_case_summary(process_data, HealthInformationTypes.OPCONSULTATION.value)


    async def generate_radiology_summary(
        self, process_data: dict[str, Any]
    ) -> JobResponse:
        """
    Initiate AI-based generation of a radiology/diagnostic report summary.

    This method validates incoming data, performs encryption when required,
    and submits a summary-generation job to the AI service. The API processes
    the radiology/diagnostic report asynchronously and returns a `JobResponse`
    containing metadata for tracking job completion.

    Args:
        process_data (dict[str, Any]):
            Input payload that may include:
                - files (list[str]): Source documents to encrypt.
                - encryptedData (str): Pre-encrypted input; bypasses encryption.
                - publicKey (str, optional): Public key used for encryption.
                - callbackUrl (str, optional): URL for asynchronous callbacks.

    Returns:
        JobResponse:
            Contains job tracking details:
                - jobId (str): Unique identifier of the submitted job.
                - recordId (str): Associated record reference.
                - status (str): Initial job processing status.
                - estimatedCompletionMs (int): Estimated completion time.
                - message (str): Informational status message.

    Raises:
        EhrApiError:
            Raised when validation fails or when the AI API responds with
            400 / 422 / 500 level errors.
        Exception:
            Unexpected errors are wrapped in an `EhrApiError` (status 500).

    Example:
        ```python
        response = await service.generate_radiology_summary({
            "files": ["scan1.pdf", "scan2.pdf"],
            "publicKey": "xyz-public-key",
            "callbackUrl": "https://example.com/radiology/callback"
        })

        print(response.jobId)
        """
        self.logger.info(f"Starting generation of radiology summary with data: {process_data}")

        try:
            process_dto: ProcessDSDto = await self._validate_data(ProcessDSDto, process_data)

            # Throw error if no encryptedData or files
            if not process_dto.encrypted_data and not process_dto.files:
                raise ValueError("No files or encrypted data provided.")

            # Use encryptedData if provided, else encrypt files
            if process_dto.encrypted_data:
                encrypted_data = process_dto.encrypted_data
            else:
                payload_to_encrypt = {"files": process_dto.files}
                encrypted_data = await self.utilities.encryption(payload=payload_to_encrypt)

            # Build payload
            payload = {
                "caseType": HealthInformationTypes.DIAGNOSTIC_REPORT.value,
                "encryptedData": encrypted_data,
            }
            if process_dto.public_key:
                payload["publicKey"] = process_dto.public_key
            if process_dto.callback_url:
                payload["callbackUrl"] = process_dto.callback_url
            
            response: JobResponse = await self.post(
                AI_ENDPOINTS.GENERATE_RADIOLOGY_SUMMARY,
                payload,
                response_model=JobResponse,
            )

            
            return response

            

        except EhrApiError as e:
            self.logger.error(f"EHR API Error during radiology summary generation: {e.message}", exc_info=True)
            raise
        except ValueError as e:
            self.logger.error(f"Validation error in radiology summary generation: {e}", exc_info=True)
            raise EhrApiError(str(e), 422) from e
        except Exception as error:
            error_message = str(error)
            self.logger.error(f"Unexpected error in radiology summary generation: {error_message}", exc_info=True)
            raise EhrApiError(
                f"An unexpected error occurred while generating radiology summary: {error_message}", 500
                ) from error

    async def partial_upload_for_discharge_summary(
        self, process_ds_dto: ProcessDSDto
    ) -> JobResponse:
        """
            Perform a partial upload for discharge summary generation.

            This method is used when uploading discharge-summary content in multiple
            chunks (partial uploads). It validates the input DTO, encrypts files if
            needed, builds the correct payload, and triggers a partial upload request
            to the AI service.

            A partial upload may or may not include an `encounterId`. For the first
            partial upload, the encounter ID is optional; for subsequent uploads, it
            will typically be returned by the API and included by the client.

            Args:
                process_ds_dto (ProcessDSDto):
                    DTO containing:
                    - files (list[str]) or encryptedData (str)
                    - encounter_id (str, optional)
                    - date (str, optional; ISO-8601). If omitted, the current UTC
                        timestamp is automatically used.
                    - public_key (str, optional)
                    - callback_url (str, optional)

            Returns:
                JobResponse:
                    A job-tracking response from the AI service, containing:
                        - jobId (str)
                        - recordId (str)
                        - status (str)
                        - estimatedCompletionMs (int)
                        - message (str)

            Raises:
                EhrApiError:
                    When encryption fails, validation fails, or the AI API returns
                    an error (400, 422, 500).
                ValueError:
                    Raised before wrapping inside `EhrApiError` if neither files nor
                    encryptedData is supplied.

            Example:
                ```python
                dto = ProcessDSDto(
                    files=["labs1.pdf", "labs2.pdf"],
                    date="2025-10-01T10:00:00Z"
                )

                result = await ai_service.partial_upload_for_discharge_summary(dto)
                print(result.jobId)
        """


        # Validate input
        process_dto: ProcessDSDto = await self._validate_data(ProcessDSDto, process_ds_dto)

        if not process_dto.encrypted_data and not process_dto.files:
            raise ValueError("No files or encrypted data provided.",422)
        
        if process_dto.files:
                await self.utilities.validate_files(process_dto.files)

        # Either use encrypted_data or perform encryption
        if process_dto.encrypted_data:
            encrypted_data = process_dto.encrypted_data
        else:
            payload_to_encrypt = {"files": process_dto.files}
            encrypted_data = await self.utilities.encryption(
                payload=payload_to_encrypt, public_key=process_dto.public_key
            )

        # Build payload
        payload: Dict[str, Any] = {
            "caseType": HealthInformationTypes.DISCHARGE_SUMMARY.value,
            "uploadMode": "Partial",
            "date": process_dto.date
            or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "encounterId": process_dto.encounter_id,
            "encryptedData": encrypted_data,
        }
        if process_dto.callback_url:
            payload["callbackUrl"] = process_dto.callback_url
        if process_dto.public_key:
            payload["publicKey"] = process_dto.public_key

        # Call API
        try:
            response = await self.post(
                AI_ENDPOINTS.GENERATE_DISCHARGE_SUMMARY,
                payload,
                response_model=JobResponse,
            )
            return response
        except EhrApiError as e:
            self.logger.error(
                f"EHR API Error during Partial upload for discharge summary generation: {e.message}",
                exc_info=True,
            )
            raise
        except ValueError as e:
            self.logger.error(
                f"Validation error in Partial upload for discharge summary generation: {e}", exc_info=True
            )
            raise EhrApiError(str(e), 422) from e
        except Exception as error:
            error_message = str(error)
            self.logger.error(
                f"Unexpected error in Partial upload for discharge summary generation: {error_message}",
                exc_info=True,
            )
            raise EhrApiError(
                "An unexpected error occurred while Partial upload for discharge summary generation: "
                f"{error_message}",
                500,
            ) from error

    async def trigger_discharge_summary(self, encounter_id: str) -> Any:
        """
            Trigger discharge summary generation for a given encounter ID.

            This method sends a PUT request to the AI service endpoint to initiate
            discharge summary generation for the specified encounter. It ensures the
            `encounter_id` is valid before making the request.

            Args:
                encounter_id (str): The unique identifier of the encounter.
                    Must be a non-empty string.

            Returns:
                Dict[str, Any]: The JSON response from the AI service containing
                the status of the discharge summary generation.

            Raises:
                ValueError: If `encounter_id` is missing or blank.
                EhrApiError: If an error occurs during the API request.

            Example:
                >>> result = await ai_service.trigger_discharge_summary("enc-12345")
                >>> print(result)
                {
                    "data": "{\n  \"patientDetails\": {\n    \"Name\": \"Mr. Sri Ram\",\n    \"Age\": \"16 years 6 months\",\n    \"Gender\": \"Male\",\n.........."}",
                    "message": "Discharge for record enc-12345 generated successfully"
                }
        """
        if not encounter_id or not encounter_id.strip():
            raise ValueError("Encounter ID must not be blank.")

        payload: Dict[str, Any] = {"updateType": "Generate Discharge"}
        url = f"{AI_ENDPOINTS.UPDATE_DISCHARGE_SUMMARY_URL}/{encounter_id}"

        try:
            response = await self.put(url, payload, response_model=dict)
            return response
        except EhrApiError:
            raise
        except Exception as error:
            error_message = str(error)
            self.logger.error(
                f"Unexpected error in trigger_discharge_summary for encounterId={encounter_id}: {error_message}",
                exc_info=True,
            )
            raise EhrApiError(
                f"An unexpected error occurred while triggering discharge summary for encounterId={encounter_id}: {error_message}",
                500,
            ) from error

    async def generate_careplan(self, process_ds_dto: ProcessDSDto) -> JobResponse:
        """
            Generate a patient care plan from provided files or encrypted data.

            This method validates the input data, encrypts it if required, and sends the
            payload to the AI service endpoint for care plan generation. It handles
            validation errors, encryption failures, and unexpected errors gracefully.

            Args:
                process_ds_dto (ProcessDSDto):
                    The input DTO containing files, encrypted data, and optional encryption keys.

            JobResponse:
            A job-tracking response from the AI service, containing:
                - jobId (str)
                - recordId (str)
                - status (str)
                - estimatedCompletionMs (int)
                - message (str)


            Raises:
                EhrApiError: If the API call fails (status code 500)
                ValueError: Raised internally for missing `files` or `encrypted_data` before being
                    wrapped as an `EhrApiError`.

            Example Input if files are provided:
                >>> dto = ProcessDSDto(
                ...     files=["file1.pdf", "file2.pdf"],
                ... )
                >>> response = await ai_service.generate_careplan(dto)

            Example Input if encrypted data is provided:
                >>> dto = ProcessDSDto(
                ...     encrypted_data="encrypted_payload_string",
                ...     public_key="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
                ... ) response = await ai_service.generate_careplan(dto)

            Example Output after job completion:
                {
                    "id": "a1956730-546534265f-4c2d-8902-a34fe3645886b24",
                    "carePlan": {
                        "patientDetails": {
                            "name": "Ram sai",
                            "age": "75Y(s) 6M(s) 30D(s)",
                            "sex": "Male",
                            "uhid": "MRKO252643654325015739",
                            "visitId": "IPKO243534005789",
                            "address": "Mumbai",
                            "contactNumber": "9876543210"
                        },
                        "doctorDetails": [
                            {
                                "name": "DR. BALAKRISHNA N",
                                "designation": "MBBS, MD, DM (Cardiology), Sr. Consultant Cardiologist.",
                                "department": "CARDIOLOGY"
                            },
                            {
                                "name": "DR. SHYAM SINGA ROY. G",
                                "designation": "MBBS, MD (General Medicine), DM (Neurology), Consultant Neurologist",
                                "department": "NEUROLOGY"
                            }
                        ],
                        ....
                    }
                }

        """
        try: 
            process_dto: ProcessDSDto = await self._validate_data(ProcessDSDto, process_ds_dto)

            if not process_dto.encrypted_data and not process_dto.files:
                raise ValueError("No files or encrypted data provided.")

            if process_dto.files:
                await self.utilities.validate_files(process_dto.files)

            if process_dto.encrypted_data:
                encrypted_data = process_dto.encrypted_data
            else:
                payload_to_encrypt = {"files": process_dto.files}
                encrypted_data = await self.utilities.encryption(
                    payload=payload_to_encrypt, public_key=process_dto.public_key
                )

            payload: Dict[str, Any] = {"encryptedData": encrypted_data}
            if process_dto.public_key:
                payload["publicKey"] = process_dto.public_key
            if process_dto.callback_url:
                payload["callbackUrl"] = process_dto.callback_url

            response = await self.post(
                AI_ENDPOINTS.GENERATE_CAREPLAN,
                payload,
                response_model=JobResponse,
            )

            if not isinstance(response, JobResponse):
                raise EhrApiError("Invalid response format from care plan API.", 502)
            
            return response

        except EhrApiError as e:
            self.logger.error(f"EHR API Error during care plan generation: {e.message}", exc_info=True)
            raise
        except ValueError as e:
            self.logger.error(f"Validation error in care plan generation: {e}", exc_info=True)
            raise EhrApiError(str(e), 422) from e
        except Exception as error:
            error_message = str(error)
            self.logger.error(f"Unexpected error while generating care plan: {error_message}", exc_info=True)
            raise EhrApiError(
                f"An unexpected error occurred while generating care plan: {error_message}",
                500,
            ) from error

    async def get_job_status(self, job_id: str) -> CallbackPayload:
        """
        Fetch the status of a job by jobId.

        Args:
            job_id (str): The job identifier.

        Returns:
            CallbackPayload: Parsed job status response.
        """
        if not job_id:
            raise ValueError("jobId must not be blank")

        params = {"jobId": job_id} if job_id else None
        response = await self.get(
            AI_ENDPOINTS.GET_JOB_STATUS,
            response_model=CallbackPayload,
            query_params=params,
        )


        return response.model_dump(exclude_none=True)
    
    async def get_preview_pdf(self, record_id: str) -> PreviewPdfResponse:
        """
        Get the PDF preview for a discharge summary.

        Args:
            record_id (str): The discharge summary record ID.

        Returns:
            PreviewPdfResponse: Contains fileName, mimeType, base64 PDF.
        """
        if not record_id:
            raise ValueError("recordId must not be blank")

        path = f"{AI_ENDPOINTS.DISCHARGE_SUMMARY_PREVIEW}/{record_id}/preview"
        response = await self.get(path, response_model=PreviewPdfResponse)
        print(f"[INFO] PDF Preview retrieved successfully for record: {record_id}")
        print(f"[INFO]   File name: {response.fileName}")
        print(f"[INFO]   MIME type: {response.mimeType}")
        print(f"[INFO]   PDF size: {len(response.pdf)} chars (base64)")

        return response


    async def download_pdf_bytes(self, record_id: str) -> bytes:
        """
        Download the PDF for a discharge summary and return as bytes.

        Args:
            record_id (str): The discharge summary record ID.

        Returns:
            bytes: Raw PDF byte data.
        """
        preview = await self.get_preview_pdf(record_id)

        try:
            pdf_bytes = base64.b64decode(preview.pdf)
            print(f"[INFO] PDF decoded successfully: {len(pdf_bytes)} bytes")
            return pdf_bytes

        except Exception as exc:
            print("[ERROR] Failed to decode PDF base64")
            raise RuntimeError("Failed to decode PDF") from exc