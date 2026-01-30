from typing import Optional, Union

from httpx import Response

from earthscope_sdk.client.dropoff.models import (
    DropoffCategory,
    DropoffObject,
    GetDropoffObjectHistoryResult,
    ListDropoffObjectsResult,
    Page,
)
from earthscope_sdk.common.service import SdkService


class DropoffBaseService(SdkService):
    """
    L1 dropoff endpoints
    """

    def _get_dropoff_category_with_default(
        self,
        category: Union[DropoffCategory, str, None],
    ) -> str:
        """
        Get the dropoff category with a default value if not provided.

        Args:
            category: The category of the dropoff

        Returns:
            The dropoff category
        """
        if category:
            return DropoffCategory(category).value

        if cat := self.ctx.settings.dropoff.category:
            return cat.value

        raise ValueError("No category provided")

    async def _get_object_history(
        self,
        *,
        key: str,
        category: Union[DropoffCategory, str, None] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Page[DropoffObject]:
        """
        Get dropoff object history.

        When the same object key is uploaded to multiple times, this method will
        retrieve the history of that object key.

        The response is paginated. Use the `offset` and `limit` parameters to page through the results.

        Args:
            key: The key of the object to get history for
            category: The category of the dropoff
            offset: The offset of the objects to get
            limit: The limit of the objects to get

        Returns:
            The dropoff object history
        """
        category = self._get_dropoff_category_with_default(category)

        params: dict[str, Union[int, str]] = {
            "offset": offset,
            "limit": limit,
            "key": key,
        }

        req = self.ctx.httpx_client.build_request(
            method="GET",
            url=f"{self.resources.api_url}beta/dropoff/{category}/status",
            params=params,
        )

        resp: Response = await self._send_with_retries(req)

        return GetDropoffObjectHistoryResult.validate_json(resp.content)

    async def _list_objects(
        self,
        *,
        category: Union[DropoffCategory, str, None] = None,
        prefix: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Page[DropoffObject]:
        """
        List dropoff objects.

        The response is paginated. Use the `offset` and `limit` parameters to page through the results.

        Args:
            category: The category of the dropoff
            prefix: The prefix of the objects to list
            offset: The offset of the objects to list
            limit: The limit of the objects to list

        Returns:
            A page of dropoff objects.
        """
        category = self._get_dropoff_category_with_default(category)

        params: dict[str, Union[int, str]] = {
            "offset": offset,
            "limit": limit,
        }

        if prefix:
            params["prefix"] = prefix

        req = self.ctx.httpx_client.build_request(
            method="GET",
            url=f"{self.resources.api_url}beta/dropoff/{category}",
            params=params,
        )

        resp: Response = await self._send_with_retries(req)

        return ListDropoffObjectsResult.validate_json(resp.content)
