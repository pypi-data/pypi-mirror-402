import pytest
import os
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from carestack.base.base_types import ClientConfig
from carestack.base.errors import EhrApiError
from carestack.common.enums import AI_ENDPOINTS, HealthInformationTypes

from carestack.ai.ai_service import AiService
from carestack.ai.ai_dto import (
    RadiologySummaryResponse,
    JobResponse,
    FhirBundleResponse,
    ProcessDSDto,
)
from carestack.common.config_test import client_config


@pytest.fixture(scope="class")
def mock_radiology_summary_response() -> RadiologySummaryResponse:
        """Fixture to provide a mock radiology summary response."""
        return RadiologySummaryResponse([
            {
                "reportId": "rad-001",
                "patientName": "John Doe",
                "age": 45,
                "gender": "Male",
                "studyType": "X-Ray Chest",
                "findings": "No acute cardiopulmonary abnormality detected.",
                "impression": "Normal chest radiograph.",
                "recommendations": ["Routine follow-up after 6 months"]
            },
            {
                "reportId": "rad-002",
                "patientName": "Jane Smith",
                "age": 52,
                "gender": "Female",
                "studyType": "MRI Brain",
                "findings": "Mild white matter hyperintensities suggestive of chronic microvascular ischemia.",
                "impression": "No evidence of acute infarction.",
                "recommendations": ["Clinical correlation advised"]
            }
        ])

class TestAiService:
    """Test cases for AiService class."""

    @pytest.fixture
    def ai_service(self, client_config: ClientConfig) -> AiService:
        """AiService instance fixture."""
        with patch("carestack.ai.ai_service.AiUtilities") as mock_utilities:
            with patch.dict(os.environ, {"AI_SERVICE_KEY": "test_ai_key"}):
                service = AiService(client_config)
                service.utilities = mock_utilities.return_value
                # Mock the post and put methods from BaseService
                service.post = AsyncMock()
                service.put = AsyncMock()
                return service

    @pytest.fixture
    def ai_service_no_env(self, client_config: ClientConfig) -> AiService:
        """AiService instance fixture without environment variables."""
        with patch("carestack.ai.ai_service.AiUtilities") as mock_utilities:
            with patch.dict(os.environ, {}, clear=True):
                service = AiService(client_config)
                service.utilities = mock_utilities.return_value
                service.post = AsyncMock()
                service.put = AsyncMock()
                return service

    @pytest.fixture
    def mock_fhir_bundle_response(self):
        """Mock FHIR bundle response fixture."""
        return FhirBundleResponse(
            root={"resourceType": "Bundle", "id": "test-bundle", "entry": []}
        )

    @pytest.fixture
    def mock_discharge_summary_response(self) -> JobResponse:
        """Mock discharge summary response fixture."""
        return JobResponse(
            id="mock-id-123",
            dischargeSummary={"summary": "Sample discharge summary"},
            extractedData={"diagnosis": "sample diagnosis"},
            fhirBundle={"resourceType": "Bundle", "entry": []},
        )

    @pytest.fixture
    def valid_process_ds_data(self):
        """Valid ProcessDS data fixture."""
        return {
            "files": ["file1.pdf", "file2.pdf"],
            "encrypted_data": None,
            "public_key": "test-public-key",
        }

    @pytest.fixture
    def valid_process_ds_data_with_encrypted(self):
        """Valid ProcessDS data with encrypted data fixture."""
        return {
            "files": None,
            "encrypted_data": "encrypted-test-data",
            "public_key": "test-public-key",
        }

    @pytest.fixture
    def valid_fhir_bundle_data(self):
        """Valid FHIR bundle data fixture."""
        return {
            "caseType": "DischargeSummary",
            "enableExtraction": True,
            "extractedData": {"patient": "test-patient"},
            "documentReferences": ["doc_ref_1", "doc_ref_2"],
            "recordId": "rec-123",
            "publicKey": "test-public-key",
        }

    @pytest.fixture
    def valid_partial_upload_data(self):
        """Valid partial upload data fixture."""
        return {
            "files": ["file1.pdf"],
            "encounterId": "encounter-123",
            "date": "2025-01-01T00:00:00Z",
            "publicKey": "test-public-key",
        }

    class TestValidateData:
        """Test cases for validating ProcessDSDto with AiService._validate_data"""

        @pytest.mark.asyncio
        async def test_validate_data_success_with_files(self, ai_service: AiService):
            """Valid data with files should pass validation"""
            data = {
                "files": ["file1.pdf", "file2.pdf"],
                "public_key": "test-public-key",
            }

            result = await ai_service._validate_data(ProcessDSDto, data)

            assert isinstance(result, ProcessDSDto)
            assert result.files == ["file1.pdf", "file2.pdf"]
            assert result.public_key == "test-public-key"

        @pytest.mark.asyncio
        async def test_validate_data_success_with_encrypted_data(self, ai_service: AiService):
            """Valid data with encrypted_data should pass validation"""
            data = {
                "encrypted_data": "secret-123",
                "public_key": "test-public-key",
            }

            result = await ai_service._validate_data(ProcessDSDto, data)

            assert isinstance(result, ProcessDSDto)
            assert result.encrypted_data == "secret-123"
            assert result.public_key == "test-public-key"

        @pytest.mark.asyncio
        async def test_validate_data_with_alias_field(self, ai_service: AiService):
            """encounterId alias should map correctly to encounter_id"""
            data = {
                "files": ["file1.pdf"],
                "encounterId": "enc-123",
                "public_key": "test-public-key",
            }

            result = await ai_service._validate_data(ProcessDSDto, data)

            assert isinstance(result, ProcessDSDto)
            assert result.encounter_id == "enc-123"

        @pytest.mark.asyncio
        async def test_validate_data_validation_error_missing_required_type(self, ai_service: AiService):
            """Invalid type should raise EhrApiError"""
            data = {"files": "not-a-list"}  # files should be list[str] but got str

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service._validate_data(ProcessDSDto, data)

            assert exc_info.value.status_code == 400
            assert "Validation failed" in str(exc_info.value.message)   

    class TestGenerateDischargeSummary:
        """Test cases for generate_discharge_summary method."""

        @pytest.mark.asyncio
        async def test_generate_discharge_summary_success_with_files(
            self, ai_service: AiService, valid_process_ds_data, mock_discharge_summary_response
        ):
            """Test successful discharge summary generation with files."""

            ai_service.generate_case_summary = AsyncMock(return_value=mock_discharge_summary_response)

            result = await ai_service.generate_discharge_summary(valid_process_ds_data)

            assert result == mock_discharge_summary_response

            ai_service.generate_case_summary.assert_called_once_with(
                valid_process_ds_data,
                HealthInformationTypes.DISCHARGE_SUMMARY.value,
            )



        @pytest.mark.asyncio
        async def test_generate_discharge_summary_success_with_encrypted_data(
            self, ai_service: AiService, valid_process_ds_data_with_encrypted, mock_discharge_summary_response
        ):
            """Test successful discharge summary generation with encrypted data."""
            ai_service.utilities.encryption = AsyncMock()

            # Mock generate_case_summary
            ai_service.generate_case_summary = AsyncMock(return_value=mock_discharge_summary_response)

            # Call the method
            result = await ai_service.generate_discharge_summary(valid_process_ds_data_with_encrypted)

            # Validate output
            assert result == mock_discharge_summary_response

            # Encryption should not happen
            ai_service.utilities.encryption.assert_not_called()

            # generate_case_summary should receive the encrypted payload as-is
            ai_service.generate_case_summary.assert_called_once_with(
                valid_process_ds_data_with_encrypted,
                HealthInformationTypes.DISCHARGE_SUMMARY.value,
            )


        @pytest.mark.asyncio
        async def test_generate_discharge_summary_no_data_provided(
            self, ai_service: AiService
        ):
            """Test discharge summary generation with no files or encrypted data."""
            data = {
                "files": None,
                "encryptedData": None,
                "public_key": "test-key",
            }

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service.generate_discharge_summary(data)

            assert exc_info.value.status_code == 422
            assert "No files or encrypted data provided" in str(exc_info.value.message)


    class TestGenerateOpConsultationSummary:
        """Test cases for generate_op_consultation_summary method."""

        @pytest.mark.asyncio
        async def test_generate_op_consultation_success(
            self, ai_service: AiService, valid_process_ds_data, mock_discharge_summary_response
        ):
            """Test successful OP consultation summary generation."""
            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(return_value=mock_discharge_summary_response)

            result = await ai_service.generate_op_consultation_summary(valid_process_ds_data)

            assert result == mock_discharge_summary_response
            ai_service.post.assert_called_once_with(
                AI_ENDPOINTS.GENERATE_DISCHARGE_SUMMARY,
                {
                    "caseType": HealthInformationTypes.OPCONSULTATION.value,
                    "encryptedData": "encrypted-data",
                    "callbackUrl": None,
                    "publicKey": "test-public-key",
                },
                response_model=JobResponse,
            )


        @pytest.mark.asyncio
        async def test_generate_op_consultation_no_data(self, ai_service: AiService):
            """Test OP consultation generation with no data."""
            data = {"files": None, "encryptedData": None}

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service.generate_op_consultation_summary(data)

            assert exc_info.value.status_code == 422
            assert "No files or encrypted data provided" in str(exc_info.value.message)

    class TestGenerateRadiologySummary:
        """Test cases for generate_radiology_summary method."""

        @pytest.mark.asyncio
        async def test_generate_radiology_summary_success(
            self,
            ai_service: AiService,
            valid_process_ds_data
        ):
            """Test successful radiology summary generation."""
            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            mock_job_response = JobResponse(
                jobId="job-123",
                recordId="rec-456",
                status="QUEUED",
                estimatedCompletionMs=3000,
                message="Processing started"
            )
            ai_service.post = AsyncMock(return_value=mock_job_response)
            result = await ai_service.generate_radiology_summary(valid_process_ds_data)

             # Assertions
            assert isinstance(result, JobResponse)
            assert result == mock_job_response
            ai_service.post.assert_called_once_with(
                AI_ENDPOINTS.GENERATE_RADIOLOGY_SUMMARY,
                {
                    "caseType": HealthInformationTypes.DIAGNOSTIC_REPORT.value,
                    "encryptedData": "encrypted-data",
                    "publicKey": "test-public-key",

                },
                response_model=JobResponse,
            )

        @pytest.mark.asyncio
        async def test_generate_radiology_summary_with_encrypted_data(
            self, ai_service: AiService, valid_process_ds_data_with_encrypted, mock_discharge_summary_response
        ):
            """Test radiology summary generation with pre-encrypted data."""
            ai_service.post = AsyncMock(return_value=mock_discharge_summary_response)

            result = await ai_service.generate_radiology_summary(valid_process_ds_data_with_encrypted)

            assert result == mock_discharge_summary_response
            ai_service.utilities.encryption.assert_not_called()

        @pytest.mark.asyncio
        async def test_generate_radiology_summary_api_error(
            self, ai_service: AiService, valid_process_ds_data
        ):
            """Test radiology summary generation with API error."""
            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.post = AsyncMock(side_effect=EhrApiError("Radiology API Error", 500))

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service.generate_radiology_summary(valid_process_ds_data)

            assert exc_info.value.status_code == 500
            assert "Radiology API Error" in str(exc_info.value.message)

        @pytest.mark.asyncio
        async def test_generate_radiology_summary_unexpected_error(
            self, ai_service: AiService, valid_process_ds_data
        ):
            """Test radiology summary generation with unexpected error."""
            ai_service.utilities.encryption = AsyncMock(side_effect=Exception("Encryption failed"))

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service.generate_radiology_summary(valid_process_ds_data)

            assert exc_info.value.status_code == 500
            assert "An unexpected error occurred while generating radiology summary" in str(exc_info.value.message)

    class TestGenerateFhirBundle:
        """Test cases for generate_fhir_bundle method."""

        @pytest.mark.asyncio
        async def test_generate_fhir_bundle_with_extraction_enabled(
            self, ai_service: AiService, valid_fhir_bundle_data, mock_fhir_bundle_response
        ):
            """Test FHIR bundle generation with extraction enabled."""
            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.post = AsyncMock(return_value=mock_fhir_bundle_response)

            result = await ai_service.generate_fhir_bundle(valid_fhir_bundle_data)

            assert result == mock_fhir_bundle_response.root
            ai_service.post.assert_called_once()

        @pytest.mark.asyncio
        async def test_generate_fhir_bundle_with_extraction_disabled(
            self, ai_service: AiService, mock_fhir_bundle_response
        ):
            """Test FHIR bundle generation with extraction disabled."""
            
            data = {
                    "caseType": "DischargeSummary",
                    "enableExtraction": False,
                    "documentReferences": ["doc1", "doc2"],
                    "patientDetails": {
                        "firstName": "John",
                        "lastName": "Doe",
                        "mobileNumber": "1234567890",
                        "address": "123 Street",
                        "pincode": "560001",
                        "state": "Karnataka",
                        "gender": "male",
                        "birthDate": "1990-01-01",
                        "idNumber": "P123",
                        "idType": "MRN"
                    },
                    "doctorsDetails": [{
                        "firstName": "Smith",
                        "lastName": "John",
                        "specialty": "Cardiology",
                        "identifier": "D123",
                        "birthDate": "1980-01-01",
                        "gender": "male",
                        "mobileNumber": "9876543210",
                        "address": "Hospital Street",
                        "pincode": "560001",
                        "state": "Karnataka",
                        "designation": "Consultant",
                        "department": "Cardiology",
                        "registrationId": "REG123"
                    }]
            }


            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.post = AsyncMock(return_value=mock_fhir_bundle_response)

            result = await ai_service.generate_fhir_bundle(data)

            assert result == mock_fhir_bundle_response.root

        @pytest.mark.asyncio
        async def test_generate_fhir_bundle_no_extracted_data(self, ai_service: AiService):
            """Test FHIR bundle generation with no extracted data when extraction enabled."""
            data = {
                "caseType": "DischargeSummary",
                "enableExtraction": True,
                "documentReferences": ["doc1", "doc2"],
            }

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service.generate_fhir_bundle(data)

            assert exc_info.value.status_code == 422
            assert "No extracted data is provided" in str(exc_info.value.message)

        @pytest.mark.asyncio
        async def test_generate_fhir_bundle_validation_error(self, ai_service: AiService):
            """Test FHIR bundle generation with validation error."""
            invalid_data = {"invalid_field": "invalid_value"}

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service.generate_fhir_bundle(invalid_data)

            assert exc_info.value.status_code == 400
            assert "Validation failed" in str(exc_info.value.message)

    class TestPartialUploadForDischargeSummary:
        """Test cases for partial_upload_for_discharge_summary method."""

        @pytest.mark.asyncio
        async def test_partial_upload_success(self, ai_service: AiService, valid_partial_upload_data):
            """Test successful partial upload."""
            mock_response = {"status": "uploaded", "id": "upload-123"}
            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(return_value=mock_response)

            # Pass dict instead of DTO
            result = await ai_service.partial_upload_for_discharge_summary(valid_partial_upload_data)

            assert result == mock_response
            ai_service.post.assert_called_once()
            ai_service.utilities.encryption.assert_called_once()

        @pytest.mark.asyncio
        async def test_partial_upload_with_encrypted_data(self, ai_service: AiService):
            """Test partial upload with pre-encrypted data."""
            data = {
                "encrypted_data": "pre-encrypted-data",
                "encounter_id": "encounter-123",
                "public_key": "test-key"
            }
            mock_response = {"status": "uploaded", "id": "upload-123"}
            ai_service.post = AsyncMock(return_value=mock_response)
            ai_service.utilities.encryption = AsyncMock()  # Should not be called

            result = await ai_service.partial_upload_for_discharge_summary(data)

            assert result == mock_response
            ai_service.utilities.encryption.assert_not_called()
            ai_service.post.assert_called_once()

        @pytest.mark.asyncio
        async def test_partial_upload_no_data(self, ai_service: AiService):
            """Test partial upload with no files or encrypted data."""
            data = {
                "encounter_id": "encounter-123"
            }

            with pytest.raises(ValueError) as exc_info:
                await ai_service.partial_upload_for_discharge_summary(data)

            assert "No files or encrypted data provided" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_partial_upload_with_default_date(self, ai_service: AiService):
            """Test partial upload uses default date when not provided."""
            data = {
                "files": ["file1.pdf"],
                "encounter_id": "encounter-123",
                "public_key": "test-key"
            }
            mock_response = {"status": "uploaded", "id": "upload-123"}
            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(return_value=mock_response)

            # Patch datetime correctly
            fixed_datetime = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            with patch("carestack.ai.ai_service.datetime") as mock_datetime:
                mock_datetime.now.return_value = fixed_datetime

                result = await ai_service.partial_upload_for_discharge_summary(data)

                assert result == mock_response
                assert ai_service.post.call_count == 1
                ai_service.utilities.encryption.assert_called_once()
                mock_datetime.now.assert_called_once()

    class TestTriggerDischargeSummary:
        """Test cases for trigger_discharge_summary method."""

        @pytest.mark.asyncio
        async def test_trigger_discharge_summary_success(self, ai_service: AiService):
            """Test successful discharge summary trigger."""
            encounter_id = "encounter-123"
            mock_response = {"status": "triggered", "encounterId": encounter_id}
            ai_service.put = AsyncMock(return_value=mock_response)

            result = await ai_service.trigger_discharge_summary(encounter_id)

            assert result == mock_response
            ai_service.put.assert_called_once_with(
                f"{AI_ENDPOINTS.UPDATE_DISCHARGE_SUMMARY_URL}/{encounter_id}",
                {"updateType": "Generate Discharge"},
                response_model=dict
            )

        @pytest.mark.asyncio
        async def test_trigger_discharge_summary_empty_encounter_id(self, ai_service: AiService):
            """Test trigger with empty encounter ID."""
            with pytest.raises(ValueError) as exc_info:
                await ai_service.trigger_discharge_summary("")

            assert "Encounter ID must not be blank" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_trigger_discharge_summary_whitespace_encounter_id(self, ai_service: AiService):
            """Test trigger with whitespace-only encounter ID."""
            with pytest.raises(ValueError) as exc_info:
                await ai_service.trigger_discharge_summary("   ")

            assert "Encounter ID must not be blank" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_trigger_discharge_summary_none_encounter_id(self, ai_service: AiService):
            """Test trigger with None encounter ID."""
            with pytest.raises(ValueError) as exc_info:
                await ai_service.trigger_discharge_summary(None)

            assert "Encounter ID must not be blank" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_trigger_discharge_summary_api_error(self, ai_service: AiService):
            """Test trigger with API error."""
            encounter_id = "encounter-123"
            ai_service.put = AsyncMock(side_effect=Exception("API Error"))

            with pytest.raises(Exception) as exc_info:
                await ai_service.trigger_discharge_summary(encounter_id)

            assert "API Error" in str(exc_info.value)

    class TestGenerateCareplan:
        """Test cases for generate_careplan method."""

        @pytest.mark.asyncio
        async def test_generate_careplan_success(self, ai_service: AiService):
            """Test successful care plan generation."""
            data = {
                "files": ["careplan_file.pdf"],
                "public_key": "test-key"
            }
            mock_response = JobResponse(
                                jobId="123",
                                recordId=None,
                                status="success",
                                estimatedCompletionMs=None,
                                message="Generated care plan content"
                            )
            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(return_value=mock_response)

            result = await ai_service.generate_careplan(data)

            assert result == mock_response
            ai_service.post.assert_called_once_with(
                AI_ENDPOINTS.GENERATE_CAREPLAN,
                {
                    "encryptedData": "encrypted-data",
                    "publicKey": "test-key",
                },
                response_model=JobResponse,
            )

        @pytest.mark.asyncio
        async def test_generate_careplan_with_encrypted_data(self, ai_service: AiService):
            """Test care plan generation with pre-encrypted data."""
            data = {
                "encrypted_data": "pre-encrypted-careplan-data",
                "public_key": "test-key"
            }
            mock_response = JobResponse(
                                jobId="123",
                                recordId=None,
                                status="success",
                                estimatedCompletionMs=None,
                                message="Generated care plan content"
                            )
            ai_service.post = AsyncMock(return_value=mock_response)
            ai_service.utilities.encryption = AsyncMock()  # Should not be called

            result = await ai_service.generate_careplan(data)

            assert result == mock_response
            ai_service.utilities.encryption.assert_not_called()
            ai_service.post.assert_called_once()

        @pytest.mark.asyncio
        async def test_generate_careplan_no_data(self, ai_service: AiService):
            """Test care plan generation with no files or encrypted data."""
            data = {"public_key": "test-key"}

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service.generate_careplan(data)

            assert exc_info.value.status_code == 422
            assert "No files or encrypted data provided" in str(exc_info.value.message)


        @pytest.mark.asyncio
        async def test_generate_careplan_api_error(self, ai_service: AiService):
            """Test care plan generation with API error."""
            data = {
                "files": ["file.pdf"],
                "public_key": "test-key"
            }
            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(side_effect=EhrApiError("Care plan API Error", 500))

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service.generate_careplan(data)

            assert exc_info.value.status_code == 500
            assert "Care plan API Error" in str(exc_info.value.message)

        @pytest.mark.asyncio
        async def test_generate_careplan_unexpected_error(self, ai_service: AiService):
            """Test care plan generation with unexpected error."""
            data = {
                "files": ["file.pdf"],
                "public_key": "test-key"
            }
            ai_service.utilities.encryption = AsyncMock(side_effect=Exception("Unexpected error"))

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service.generate_careplan(data)

            assert exc_info.value.status_code == 500
            assert "An unexpected error occurred while generating care plan" in str(exc_info.value.message)

    class TestGenerateCaseSummary:
        """Test cases for generate_case_summary method."""

        @pytest.mark.asyncio
        async def test_generate_case_summary_success(
            self, ai_service: AiService, valid_process_ds_data, mock_discharge_summary_response
        ):
            """Test successful case summary generation."""
            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(return_value=mock_discharge_summary_response)

            result = await ai_service.generate_case_summary(valid_process_ds_data, "TestCase")

            assert result == mock_discharge_summary_response
            ai_service.post.assert_called_once_with(
                AI_ENDPOINTS.GENERATE_DISCHARGE_SUMMARY,
                {
                    "caseType": "TestCase",
                    "encryptedData": "encrypted-data",
                    "callbackUrl": None,  
                    "publicKey": "test-public-key",
                },
                response_model=JobResponse,
            )

        @pytest.mark.asyncio
        async def test_generate_case_summary_without_public_key(
            self, ai_service: AiService, mock_discharge_summary_response
        ):
            """Test case summary generation without public key."""
            data = {"files": ["file1.pdf"]}
            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(return_value=mock_discharge_summary_response)

            result = await ai_service.generate_case_summary(data, "TestCase")

            assert result == mock_discharge_summary_response
            # Verify publicKey is not included in payload when not provided
            call_args = ai_service.post.call_args[0][1]
            assert "publicKey" not in call_args

    class TestInitialization:
        """Test cases for AiService initialization."""

        def test_init_success(self, client_config):
            """Test successful AiService initialization."""
            with patch("carestack.ai.ai_service.AiUtilities") as mock_utilities:
                with patch.dict(os.environ, {"AI_SERVICE_KEY": "test_ai_key"}):
                    service = AiService(client_config)

                    assert service.config == client_config
                    assert service.utilities is not None
                    mock_utilities.assert_called_once()

        def test_logger_initialization(self, client_config):
            """Test logger is properly initialized."""
            with patch("carestack.ai.ai_service.AiUtilities"):
                with patch.dict(os.environ, {"AI_SERVICE_KEY": "test_ai_key"}):
                    service = AiService(client_config)

                    assert hasattr(service, "logger")
                    assert service.logger.name == "carestack.ai.ai_service"

        def test_init_without_env_vars(self, client_config):
            """Test AiService initialization without environment variables."""
            with patch("carestack.ai.ai_service.AiUtilities") as mock_utilities:
                with patch.dict(os.environ, {}, clear=True):
                    service = AiService(client_config)

                    assert service.config == client_config
                    assert service.utilities is not None
                    mock_utilities.assert_called_once()

    class TestEdgeCases:
        """Test cases for edge cases and boundary conditions."""

        @pytest.mark.asyncio
        async def test_empty_files_list(self, ai_service: AiService):
            """Test discharge summary generation with empty files list."""
            data = {
                "files": [],
                "encryptedData": None,
                "publicKey": "test-key",
            }

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service.generate_discharge_summary(data)

            assert exc_info.value.status_code == 422

        @pytest.mark.asyncio
        async def test_large_data_handling(
            self, ai_service: AiService, mock_discharge_summary_response
        ):
            """Test handling of large data payloads."""
            large_files = [f"file_{i}.pdf" for i in range(100)]
            data = {
                "files": large_files,
                "encryptedData": None,
                "publicKey": "test-key",
            }

            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-large-data")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(return_value=mock_discharge_summary_response)

            result = await ai_service.generate_discharge_summary(data)

            assert result == mock_discharge_summary_response
            ai_service.utilities.encryption.assert_called_once_with(
                payload={"files": large_files}
            )

        @pytest.mark.asyncio
        async def test_none_values_handling(self, ai_service: AiService):
            """Test handling of None values in various fields."""
            data = {
                "files": None,
                "encryptedData": None,
                "publicKey": None,
            }

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service.generate_discharge_summary(data)

            assert exc_info.value.status_code == 422
            assert "No files or encrypted data provided" in str(exc_info.value.message)

        @pytest.mark.asyncio
        async def test_encryption_failure_handling(self, ai_service: AiService):
            """Test handling of encryption failures."""
            data = {
                "files": ["file1.pdf"],
                "encryptedData": None,
                "publicKey": "test-key",
            }

            ai_service.utilities.encryption = AsyncMock(side_effect=Exception("Encryption service unavailable"))

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service.generate_discharge_summary(data)

            assert exc_info.value.status_code == 500
            assert "An unexpected error occurred while generating DischargeSummary summary" in str(exc_info.value.message)

        @pytest.mark.asyncio
        async def test_special_characters_in_files(self, ai_service: AiService, mock_discharge_summary_response):
            """Test handling of special characters in file names."""
            data = {
                "files": ["file_with_ñoño.pdf", "café_report.pdf", "patient&data.pdf"],
                "encryptedData": None,
                "publicKey": "test-key",
            }

            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-special-chars")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(return_value=mock_discharge_summary_response)

            result = await ai_service.generate_discharge_summary(data)

            assert result == mock_discharge_summary_response
            ai_service.utilities.encryption.assert_called_once()

        @pytest.mark.asyncio
        async def test_concurrent_requests_handling(self, ai_service: AiService, mock_discharge_summary_response):
            """Test handling multiple concurrent requests."""
            import asyncio
            
            data = {
                "files": ["file1.pdf"],
                "encryptedData": None,
                "publicKey": "test-key",
            }

            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(return_value=mock_discharge_summary_response)

            # Simulate concurrent requests
            tasks = [
                ai_service.generate_discharge_summary(data),
                ai_service.generate_op_consultation_summary(data),
                ai_service.generate_radiology_summary(data)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All should succeed
            assert all(result == mock_discharge_summary_response for result in results)
            assert ai_service.utilities.encryption.call_count == 3
            assert ai_service.post.call_count == 3

    class TestEnvironmentConfiguration:
        """Test cases for environment configuration scenarios."""

        def test_service_with_env_variables(self, client_config):
            """Test AiService with environment variables set."""
            test_env = {
                "AI_SERVICE_KEY": "production_key",
                "AI_DEBUG": "true",
                "AI_TIMEOUT": "60",
            }

            with patch("carestack.ai.ai_service.AiUtilities") as mock_utilities:
                with patch.dict(os.environ, test_env):
                    service = AiService(client_config)

                    assert service.config == client_config
                    assert service.utilities is not None
                    mock_utilities.assert_called_once()

        def test_service_env_override(self, client_config):
            """Test AiService behavior with environment variable overrides."""
            original_env = {"AI_SERVICE_KEY": "original_key"}
            override_env = {"AI_SERVICE_KEY": "override_key"}

            with patch("carestack.ai.ai_service.AiUtilities"):
                # Test with original environment
                with patch.dict(os.environ, original_env):
                    service1 = AiService(client_config)
                    assert service1.config == client_config

                # Test with override environment
                with patch.dict(os.environ, override_env):
                    service2 = AiService(client_config)
                    assert service2.config == client_config

    class TestErrorHandling:
        """Test cases for comprehensive error handling scenarios."""

        @pytest.mark.asyncio
        async def test_network_timeout_handling(self, ai_service: AiService, valid_process_ds_data):
            """Test handling of network timeouts."""
            import asyncio
            
            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.post = AsyncMock(side_effect=asyncio.TimeoutError("Request timeout"))

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service.generate_discharge_summary(valid_process_ds_data)

            assert exc_info.value.status_code == 500
            assert "An unexpected error occurred while generating DischargeSummary summary" in str(exc_info.value.message)

        @pytest.mark.asyncio
        async def test_malformed_response_handling(self, ai_service: AiService, valid_process_ds_data):
            """Test handling of malformed API responses."""
            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(side_effect=ValueError("Invalid JSON response"))

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service.generate_discharge_summary(valid_process_ds_data)

            assert exc_info.value.status_code == 422
            assert "Invalid JSON response" in str(exc_info.value.message)

        @pytest.mark.asyncio
        async def test_authentication_error_handling(self, ai_service: AiService, valid_process_ds_data):
            """Test handling of authentication errors."""
            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(side_effect=EhrApiError("Unauthorized", 401))

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service.generate_discharge_summary(valid_process_ds_data)

            assert exc_info.value.status_code == 401
            assert "Unauthorized" in str(exc_info.value.message)

        @pytest.mark.asyncio
        async def test_rate_limiting_error_handling(self, ai_service: AiService, valid_process_ds_data):
            """Test handling of rate limiting errors."""
            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(side_effect=EhrApiError("Rate limit exceeded", 429))

            with pytest.raises(EhrApiError) as exc_info:
                await ai_service.generate_discharge_summary(valid_process_ds_data)

            assert exc_info.value.status_code == 429
            assert "Rate limit exceeded" in str(exc_info.value.message)

    class TestDataIntegrity:
        """Test cases for data integrity and validation."""

        @pytest.mark.asyncio
        async def test_data_consistency_across_methods(self, ai_service: AiService, mock_discharge_summary_response):
            """Test data consistency across different summary generation methods."""
            data = {
                    "files": ["consistent_file.pdf"],
                    "encrypted_data": None,
                    "public_key": "test-key",
                }

            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-consistent-data")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)

            ai_service.post = AsyncMock(return_value=mock_discharge_summary_response)

            # Test all three methods use consistent data
            discharge_result = await ai_service.generate_discharge_summary(data)
            op_result = await ai_service.generate_op_consultation_summary(data)
            radiology_result = await ai_service.generate_radiology_summary(data)

            assert discharge_result == mock_discharge_summary_response
            assert op_result == mock_discharge_summary_response
            assert radiology_result == mock_discharge_summary_response
            
            # Verify encryption was called consistently
            assert ai_service.utilities.encryption.call_count == 3
            for call in ai_service.utilities.encryption.call_args_list:
                assert call[1]["payload"] == {"files": ["consistent_file.pdf"]}

        @pytest.mark.asyncio
        async def test_encrypted_data_integrity(self, ai_service: AiService, mock_discharge_summary_response):
            """Test that encrypted data is passed through without modification."""
            original_encrypted = "original-encrypted-data-12345"
            data = {
                "files": None,
                "encrypted_data": original_encrypted,
                "public_key": "test-key",
            }

            ai_service.post = AsyncMock(return_value=mock_discharge_summary_response)

            result = await ai_service.generate_discharge_summary(data)

            # Verify encrypted data was passed through unchanged
            call_args = ai_service.post.call_args[0][1]
            assert call_args["encryptedData"] == original_encrypted
            
            # Verify encryption was not called
            ai_service.utilities.encryption.assert_not_called()

        @pytest.mark.asyncio
        async def test_public_key_handling(self, ai_service: AiService, mock_discharge_summary_response):
            """Test proper handling of public key in various scenarios."""
            # Test with public key
            data_with_key = {
                "files": ["file1.pdf"],
                "encrypted_data": None,
                "public_key": "test-public-key",
            }

            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(return_value=mock_discharge_summary_response)

            await ai_service.generate_discharge_summary(data_with_key)

            call_args_with_key = ai_service.post.call_args[0][1]
            assert "publicKey" in call_args_with_key
            assert call_args_with_key["publicKey"] == "test-public-key"

            # Test without public key
            ai_service.post.reset_mock()
            data_without_key = {
                "files": ["file1.pdf"],
                "encryptedData": None,
            }

            await ai_service.generate_discharge_summary(data_without_key)

            call_args_without_key = ai_service.post.call_args[0][1]
            assert "publicKey" not in call_args_without_key

    class TestLoggingAndDebugging:
        """Test cases for logging and debugging functionality."""

        @pytest.mark.asyncio
        async def test_error_logging(self, ai_service: AiService, valid_process_ds_data):
            """Test that errors are properly logged."""
            with patch.object(ai_service.logger, 'error') as mock_logger:
                ai_service.utilities.encryption = AsyncMock(side_effect=Exception("Test error"))

                with pytest.raises(EhrApiError):
                    await ai_service.generate_discharge_summary(valid_process_ds_data)

                # Verify error was logged
                mock_logger.assert_called()
                assert "Unexpected error in DischargeSummary summary" in str(mock_logger.call_args)

        @pytest.mark.asyncio
        async def test_info_logging(self, ai_service: AiService, valid_process_ds_data, mock_discharge_summary_response):
            """Test that successful operations are logged."""
            with patch.object(ai_service.logger, 'info') as mock_logger:
                ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
                ai_service.utilities.validate_files = AsyncMock(return_value=None)
                ai_service.post = AsyncMock(return_value=mock_discharge_summary_response)

                await ai_service.generate_discharge_summary(valid_process_ds_data)

                # Verify info logging occurred
                mock_logger.assert_called()
                assert "Starting generation of DischargeSummary summary" in str(mock_logger.call_args)

        @pytest.mark.asyncio
        async def test_validation_error_logging(self, ai_service: AiService):
            """Test that validation errors are properly logged."""
            with patch.object(ai_service.logger, 'error') as mock_logger:
                invalid_data = {"invalid_field": "invalid_value"}

                with pytest.raises(EhrApiError):
                    await ai_service.generate_discharge_summary(invalid_data)

                # Verify validation error was logged
                mock_logger.assert_called()
                assert "Validation error in DischargeSummary summary generation" in str(mock_logger.call_args)

    class TestPerformanceAndScalability:
        """Test cases for performance and scalability considerations."""

        @pytest.mark.asyncio
        async def test_memory_efficiency_large_payloads(self, ai_service: AiService, mock_discharge_summary_response):
            """Test memory efficiency with large payloads."""
            # Create a large payload simulation
            large_data = {
                "files": [f"large_file_{i}.pdf" for i in range(50)],
                "encryptedData": None,
                "publicKey": "test-key",
            }

            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-large-payload")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(return_value=mock_discharge_summary_response)

            # Should handle large payloads without issues
            result = await ai_service.generate_discharge_summary(large_data)
            assert result == mock_discharge_summary_response

        @pytest.mark.asyncio
        async def test_resource_cleanup_on_error(self, ai_service: AiService, valid_process_ds_data, mock_discharge_summary_response):
            """Test that resources are properly cleaned up on errors."""
            # Simulate an error after partial processing
            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-data")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(side_effect=EhrApiError("Service unavailable", 503))

            with pytest.raises(EhrApiError):
                await ai_service.generate_discharge_summary(valid_process_ds_data)

            # Verify the service can still process new requests after error
            ai_service.post = AsyncMock(return_value=mock_discharge_summary_response)
            result = await ai_service.generate_discharge_summary(valid_process_ds_data)
            # This should succeed, indicating proper cleanup

    class TestBoundaryConditions:
        """Test cases for boundary conditions and edge cases."""

        @pytest.mark.asyncio
        async def test_minimum_required_fields(self, ai_service: AiService, mock_discharge_summary_response):
            """Test with minimum required fields only."""
            minimal_data = {
                "files": ["minimal.pdf"]
            }

            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-minimal")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(return_value=mock_discharge_summary_response)

            result = await ai_service.generate_discharge_summary(minimal_data)
            assert result == mock_discharge_summary_response

        @pytest.mark.asyncio
        async def test_maximum_field_values(self, ai_service: AiService, mock_discharge_summary_response):
            """Test with maximum realistic field values."""
            max_data = {
                "files": [f"file_{i:04d}.pdf" for i in range(100)],
                "encryptedData": None,
                "publicKey": "a" * 1000,  # Very long public key
            }

            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-max-data")
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.post = AsyncMock(return_value=mock_discharge_summary_response)

            result = await ai_service.generate_discharge_summary(max_data)
            assert result == mock_discharge_summary_response

        @pytest.mark.asyncio
        async def test_unicode_handling(self, ai_service: AiService, mock_discharge_summary_response):
            """Test handling of various Unicode characters."""
            unicode_data = {
                "files": ["файл.pdf", "文件.pdf", "ملف.pdf", "🏥_report.pdf"],
                "encryptedData": None,
                "publicKey": "unicode-key-测试",
            }
            ai_service.utilities.validate_files = AsyncMock(return_value=None)
            ai_service.utilities.encryption = AsyncMock(return_value="encrypted-unicode-data")
            ai_service.post = AsyncMock(return_value=mock_discharge_summary_response)

            result = await ai_service.generate_discharge_summary(unicode_data)
            assert result == mock_discharge_summary_response

        @pytest.mark.asyncio
        async def test_empty_string_handling(self, ai_service: AiService):
            """Test handling of empty strings in various fields."""
            empty_data = {
                "files": [""],  # Empty string in files list
                "encryptedData": "",  # Empty encrypted data
                "publicKey": "",  # Empty public key
            }

            # This should likely fail validation or be handled gracefully
            with pytest.raises((EhrApiError, ValueError)):
                await ai_service.generate_discharge_summary(empty_data)