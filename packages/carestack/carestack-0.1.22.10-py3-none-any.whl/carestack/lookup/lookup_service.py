import logging
from typing import List
from carestack.base.base_service import BaseService
from carestack.base.base_types import ClientConfig
from carestack.base.errors import EhrApiError
from carestack.common.enums import  LOOKUP_ENDPOINTS
from carestack.lookup.lookup_dto import (
    GetCodeDto,
    LoincCodeEnum,
    SnomedCodeListResponse,
    SnomedCodeResponse,
)


class LookupService(BaseService):
    """
    Service for terminology lookups, such as finding SNOMED CT or LOINC codes.

    This service provides methods to query terminology servers for clinical codes
    based on search terms and semantic tags.

    Key Features:
        - Fetch SNOMED CT codes with flexible semantic tags.
        - Fetch LOINC codes for radiology imaging.
        - Centralized code lookup logic.

    Args:
        config (ClientConfig): API credentials and settings for service initialization.

    Example:
        ```python
        config = ClientConfig(api_key="your_api_key")
        lookup_service = LookupService(config)

        # Get SNOMED codes
        snomed_codes = await lookup_service.get_snomed_code("Fever", "finding")

        # Get LOINC codes for radiology
        loinc_codes = await lookup_service.get_loinc_code("Chest X-Ray")
        ```
    """

    def __init__(self, config: ClientConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

    async def get_code(
        self, semantic_tag: str, search_term: str
    ) -> List[SnomedCodeResponse]:
        """
        Calls the remote service to get a clinical code based on a search term and semantic tag.

        Args:
            semantic_tag (str): The semantic tag to filter the search (e.g., 'finding', 'procedure').
            search_term (str): The term to search for.

        Returns:
            List[SnomedCodeResponse]: A list of matching codes.

        Raises:
            EhrApiError: If the API call fails.
        """
        self.logger.info(
            f"Requesting code for searchTerm='{search_term}' with semanticTag='{semantic_tag}'"
        )
        try:
            dto = GetCodeDto(semanticTag=semantic_tag, searchTerm=search_term)
            payload = dto.model_dump(by_alias=True)

            response = await self.post(
                LOOKUP_ENDPOINTS.GET_CODE,
                payload,
                response_model=SnomedCodeListResponse,
            )
            return response.root[:3]
        except Exception as e:
            self.logger.error(
                f"An unexpected error occurred during get_code call: {e}",
                exc_info=True,
            )
            raise EhrApiError(
                f"An unexpected error occurred while fetching code: {e}", 500
            ) from e

    async def get_snomed_code(
        self, search_term: str, semantic_tag: str
    ) -> List[SnomedCodeResponse]:
        """
        Gets a SNOMED CT code for a given search term and semantic tag.

        Args:
            search_term (str): The clinical term to search for (e.g., 'Myocardial Infarction').
            semantic_tag (str): The SNOMED CT semantic tag (e.g., 'finding', 'procedure').

        Returns:
            List[SnomedCodeResponse]: A list of matching SNOMED codes.
        """
        return await self.get_code(semantic_tag, search_term)

    async def get_loinc_code(self, search_term: str) -> List[SnomedCodeResponse]:
        """
        Gets a LOINC code for a given radiology imaging search term.

        Args:
            search_term (str): The radiology imaging term to search for (e.g., 'MRI of brain').

        Returns:
            List[SnomedCodeResponse]: A list of matching LOINC codes.
        """
        return await self.get_code(LoincCodeEnum.RADIOLOGY_IMAGING.value, search_term)
