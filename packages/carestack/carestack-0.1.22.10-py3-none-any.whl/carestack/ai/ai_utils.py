import logging
import re
from typing import Any, Optional
from urllib.parse import urlparse
from dotenv import load_dotenv
import httpx
from carestack.ai.ai_dto import EncryptionResponseType
from carestack.base.base_service import BaseService
from carestack.base.base_types import ClientConfig
from carestack.common.enums import AI_UTILITIES_ENDPOINTS


load_dotenv()


class AiUtilities(BaseService):
    """
    Utility class for cryptographic operations required by AI services, such as encryption of payloads
    and loading public keys from X.509 certificates and file validation functions  used by CareStack AI services.

    This class is intended to be used internally by AI-related service classes to ensure secure
    transmission of sensitive healthcare data to backend APIs.

    !!! note "Key Features"
        - Loads RSA public keys from PEM-encoded X.509 certificates and converts them to JWK format.
        - Encrypts arbitrary payloads using JWE (JSON Web Encryption) with RSA-OAEP-256 and AES-GCM.
        - Handles environment variable management for encryption keys.
        - Provides robust error handling and logging for all cryptographic operations.
        - Validation of file URLs and Base64 content

    Methods:
        load_public_key_from_x509_certificate : Loads an RSA public key from a PEM-encoded X.509 certificate and returns it as a JWK dictionary.
        encryption : Encrypts a payload dictionary using JWE with an RSA public key loaded from the `ENCRYPTION_PUBLIC_KEY` environment variable.

    Example usage:
        ```
        utils = AiUtilities()
        encrypted = await utils.encryption({"foo": "bar"})
        ```
    """

    def __init__(self, config: ClientConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)


    async def encryption(self, payload: dict[str, Any], public_key: Optional[str] = None) -> dict:
        """
        Calls the remote NestJS service to encrypt a payload using JWE.

        This method sends the plain payload dictionary to the `/encrypt` endpoint,
        along with an optional public key.

        ### Args:
            payload (Dict[str, Any]): The data to be encrypted.
            public_key (Optional[str]): An optional PEM-encoded public key to use for encryption.

        ### Returns:
            str: The JWE compact-serialized encrypted string returned by the service.

        ### Raises:
            RuntimeError: If the request to the encryption service fails or the service returns an error status.

        Example:
            ```
            utils = AiUtilities()
            encrypted_payload = await utils.encryption({"foo": "bar"})
            print(encrypted_payload)
            # Output: eyJhbGciOiJSU0EtT0FFUC0yNTYiLCJlbmMiOiJBMTI4R0NN...
            ```
        """

        request_body = {
            "input": payload
        }
        if public_key:
            request_body["key"] = public_key

        try:
            response = await self.post(
                AI_UTILITIES_ENDPOINTS.ENCRYPTION,
                request_body,
                response_model=EncryptionResponseType 
            )
            return response.encrypted_payload

        except httpx.HTTPStatusError as e:
            self.logger.error(
                f"Encryption service returned an error: {e.response.status_code} - {e.response.text}",
                exc_info=True
            )
            raise RuntimeError(f"Encryption failed with status {e.response.status_code}") from e

        except Exception as e:
            self.logger.error(
                f"An unexpected error occurred during encryption call: {e}",
                exc_info=True
            )
            raise RuntimeError(f"An unexpected error occurred: {e}") from e  
    
    async def decryption(self, encrypted_data: str, private_key: Optional[str] = None) -> dict:
        """
        Calls the remote NestJS service to decrypt a JWE payload.

        This method sends an encrypted JWE string to the `/decrypt` endpoint.
        It mirrors the structure of the NestJS controller, accepting the encrypted
        payload and an optional private key.

        ### Args:
            encrypted_data (str): The JWE compact-serialized string to be decrypted.
            private_key (Optional[str]): An optional PEM-encoded private key. If provided,
                it will be sent to the decryption service. Otherwise, the service
                will use its default key.

        ### Returns:
            Any: The decrypted payload returned from the service.

        ### Raises:
            RuntimeError: If the request to the decryption service fails or the
                          service returns an error status.

        Example:
            ```
            utils = AiUtilities()
            encrypted_jwe = "eyJhbGciOiJSU0EtT0FFUC0yNTYiLCJlbmMiOiJBMTI4R0NN..."
            decrypted_payload = await utils.decryption(encrypted_jwe)
            print(decrypted_payload)
            # Output from service: {'patientName': 'John Doe', 'diagnosis': 'Hypertension'}
            ```
        """
        request_body = {
            "payload": {"data": encrypted_data}
        }
        if private_key:
            request_body["key"] = private_key

        try:
            response = await self.post(AI_UTILITIES_ENDPOINTS.DECRYPTION,request_body,response_model= dict )
            return response
        except httpx.HTTPStatusError as e:
            self.logger.error(f"Decryption service returned an error: {e.response.status_code} - {e.response.text}", exc_info=True)
            raise RuntimeError(f"Decryption failed with status {e.response.status_code}") from e
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during decryption call: {e}", exc_info=True)
            raise RuntimeError(f"An unexpected error occurred: {e}") from e

    async def validate_files(self, files: list[str]) -> None:
        """
        Validates a list of file inputs (URL or Base64 encoded), ensuring
        only allowed extensions are accepted.

        Args:
            files (list[str]): List of file strings (URLs or Base64 data).

        Raises:
            ValueError: If any file is invalid or an unsupported extension
                        is detected.

        Example:
            >>> utils.validate_files([
            ...     "https://example.com/image.jpeg",
            ...     "data:image/png;base64,abcd1234..."
            ... ])
        """

        allowed_url_extensions = {".mp4", ".jpeg", ".jpg", ".pdf", ".mpeg"}

        allowed_base64_extensions = {
            ".jpeg", ".jpg", ".png", ".webp",
            ".mp4", ".webm", ".mkv", ".mov",
            ".pdf", ".txt",
            ".mp3", ".mpga", ".wav",
            ".m4a", ".opus", ".aac", ".flac", ".pcm"
        }

        for item in files:
            if not item or not isinstance(item, str):
                raise ValueError("Invalid file input.")

            # Base64 input
            if self._is_base64(item):
                ext = await self._extract_base64_extension(item)

                # No extension detected → skip
                if not ext:
                    continue

                if ext not in allowed_base64_extensions:
                    raise ValueError(
                        f"Unsupported base64 extension '{ext}'. "
                        f"Allowed: {', '.join(sorted(allowed_base64_extensions))}"
                    )
                continue

            # URL input → extract extension
            ext = self._extract_url_extension(item)

            if ext not in allowed_url_extensions:
                raise ValueError(
                    f"Unsupported file link extension '{ext}'. "
                    f"Allowed: {', '.join(sorted(allowed_url_extensions))}"
                )

    def _is_base64(self, value: str) -> bool:
        """
        Determines whether a string is Base64-encoded content.

        Supports:
        - Data URL format: data:<mime>;base64,<data>
        - Raw Base64 content without prefix

        Args:
            value (str): The string to check.

        Returns:
            bool: True if Base64, False otherwise.

        Example:
            >>> utils._is_base64("data:image/jpeg;base64,abcd1234")
            True
        """

        dataurl_pattern = r"^data:.*;base64,"
        plain_b64_pattern = r"^[A-Za-z0-9+/]+={0,2}$"

        return bool(re.match(dataurl_pattern, value)) or bool(
            re.match(plain_b64_pattern, value)
        )

    def _extract_base64_extension(self, base64_str: str) -> Optional[str]:
        """
        Extracts a file extension from a Base64 data URL.

        Example:
            data:image/png;base64,iVBORw0KGgo...

        Args:
            base64_str (str): Base64 string containing a MIME type header.

        Returns:
            Optional[str]: The corresponding file extension (".png", ".mp4", etc.)
                        or None if no MIME type was found.

        Example:
            >>> utils._extract_base64_extension("data:image/webp;base64,AAA...")
            '.webp'
        """

        match = re.match(r"^data:(.*?);base64", base64_str)
        if not match:
            return None

        mime = match.group(1).lower()

        mime_to_ext = {
            "image/jpeg": ".jpeg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "video/mp4": ".mp4",
            "video/webm": ".webm",
            "video/mkv": ".mkv",
            "video/quicktime": ".mov",
            "application/pdf": ".pdf",
            "text/plain": ".txt",
            "audio/mpeg": ".mp3",
            "audio/mpga": ".mpga",
            "audio/wav": ".wav",
            "audio/webm": ".webm",
            "audio/m4a": ".m4a",
            "audio/opus": ".opus",
            "audio/aac": ".aac",
            "audio/flac": ".flac",
            "audio/pcm": ".pcm",
        }

        return mime_to_ext.get(mime)

    def _extract_url_extension(self, url: str) -> str:
        """
        Extracts the file extension from a URL.

        Args:
            url (str): A valid URL string.

        Returns:
            str: The lowercase file extension (".jpg", ".pdf", etc.)
                or empty string if no extension is found.

        Raises:
            ValueError: If the input URL is malformed.

        Example:
            >>> utils._extract_url_extension("https://x.com/file.mp4")
            '.mp4'
        """

        try:
            parsed = urlparse(url)
            path = parsed.path

            if "." not in path:
                return ""

            return path[path.rfind("."):].lower()

        except Exception:
            raise ValueError(f"Invalid URL format: {url}")