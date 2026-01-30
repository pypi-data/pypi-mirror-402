from aiobaseclient import BaseStandardClient
from izihawa_loglib.request_context import RequestContext


class StoreApiClient(BaseStandardClient):
    """Client for Store API - document retrieval from AlloyDB documents store.

    Args:
        base_url (str): The base URL of the Store API.
        api_key (str | None, optional): API key for authentication. Defaults to None.
        user_id (str | int | None, optional): User ID of the user. Defaults to None.
        max_retries (int, optional): Maximum number of retry attempts. Defaults to 2.
        retry_delay (float, optional): Delay between retry attempts in seconds. Defaults to 0.5.
    """

    def __init__(
        self,
        base_url: str = "https://api.spacefrontiers.org",
        api_key: str | None = None,
        user_id: str | int | None = None,
        max_retries: int = 2,
        retry_delay: float = 0.5,
        default_headers: dict[str, str] | None = None,
    ):
        if default_headers is None:
            default_headers = {}
        default_headers.update(self._build_headers(api_key, user_id))
        super().__init__(
            base_url=base_url,
            default_headers=default_headers,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )

    def _build_headers(
        self,
        api_key: str | None = None,
        user_id: str | int | None = None,
    ) -> dict[str, str]:
        headers = {}
        if api_key is not None:
            headers["X-Api-Key"] = api_key
        if user_id is not None:
            headers["X-User-Id"] = str(user_id)
        return headers

    async def get(
        self,
        document_id: str,
        request_context: RequestContext | None = None,
        timeout: float = 60.0,
        api_key: str | None = None,
        user_id: str | int | None = None,
    ) -> dict:
        """Get a document by its ID.

        Args:
            document_id: The document ID (nexus_id for library documents)
            request_context: Context for the request with tracking information.
            timeout: Request timeout in seconds. Defaults to 60.0.
            api_key: API key for authorization.
            user_id: User ID for authorization.

        Returns:
            Document JSON with id, type, uris, and blob fields merged
        """
        return await self.get_request(
            f"/v1/store/{document_id}",
            timeout=timeout,
            request_context=request_context,
            headers=self._build_headers(api_key, user_id),
        )

    async def get_by_uri(
        self,
        uri: str,
        request_context: RequestContext | None = None,
        timeout: float = 60.0,
        api_key: str | None = None,
        user_id: str | int | None = None,
    ) -> dict:
        """Get a document by one of its URIs.

        Args:
            uri: The document URI (e.g., doi://10.1000/123, isbn://1234567890)
            request_context: Context for the request with tracking information.
            timeout: Request timeout in seconds. Defaults to 60.0.
            api_key: API key for authorization.
            user_id: User ID for authorization.

        Returns:
            Document JSON with id, type, uris, and blob fields merged
        """
        return await self.get_request(
            f"/v1/store/by-uri/{uri}",
            timeout=timeout,
            request_context=request_context,
            headers=self._build_headers(api_key, user_id),
        )
