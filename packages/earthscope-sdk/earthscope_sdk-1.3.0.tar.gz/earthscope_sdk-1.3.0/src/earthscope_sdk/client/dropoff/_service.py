from __future__ import annotations

from os.path import join
from pathlib import Path
from typing import (
    IO,
    TYPE_CHECKING,
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Union,
)

import aioboto3
from typing_extensions import Buffer

from earthscope_sdk.client.dropoff._base import DropoffBaseService
from earthscope_sdk.client.dropoff._multipart_uploader import (
    AsyncS3MultipartUploader,
    UploadSpec,
    UploadStatus,
)
from earthscope_sdk.client.dropoff.models import DropoffCategory, UploadResult

if TYPE_CHECKING:
    from earthscope_sdk.client.user._service import AsyncUserService
    from earthscope_sdk.common.context import SdkContext
    from earthscope_sdk.config.models import RetrySettings


PutObjectBody = Union[
    str,  # converted to a Path
    Path,  # path to a file
    IO[bytes],  # file-like object
    bytes,  # in-memory bytes
    Buffer,  # buffer protocol
    AsyncIterator[bytes],  # async iterator of bytes
    AsyncIterable[bytes],  # async iterable of bytes
    Iterator[bytes],  # iterator of bytes
    Iterable[bytes],  # iterable of bytes
]


_ContentTypes: Dict[DropoffCategory, str] = {
    DropoffCategory.miniSEED: "application/vnd.fdsn.mseed",
}


def _get_absolute_s3_path(category: str, euid_b64: str, *components: str) -> str:
    """
    Get the absolute S3 path for a dropoff object.

    Implementation note:
        We expose a short path to the user as if each dropoff category is it's own bucket.
        Furthermore, each user has their own namespace in the bucket so that they can't
        overwrite (or access) each other's files. This is all handled in a single S3 path
        structure of `category/user_id/components...`. The user ID is base64 encoded to avoid
        special characters in the path.

    Args:
        category: The category of the dropoff
        euid_b64: The EarthScope user ID (base64 encoded)
        components: The components of the S3 path (i.e. the key the user interacts with)

    Returns:
        The absolute S3 path is in the format of `category/user_id/components...`.
    """
    return join(category, euid_b64, *components)


class _DropoffService(DropoffBaseService):
    """
    L2 dropoff service functionality
    """

    def __init__(self, ctx: "SdkContext", *, user_service: "AsyncUserService"):
        super().__init__(ctx)

        self._user_service = user_service

    async def _put_object(
        self,
        body: PutObjectBody,
        *,
        key: str,
        category: str,
        part_concurrency: Optional[int] = None,
        part_size: Optional[int] = None,
        retry_settings: Optional[RetrySettings] = None,
        progress_cb: Optional[
            Callable[[UploadStatus], Union[None, Awaitable[None]]]
        ] = None,
    ) -> UploadResult:
        """
        Upload an object to EarthScope's dropoff system.

        When multiple objects are being uploaded, use the `put_objects` method instead of
        multiple calls to `put_object` as it is more efficient.

        Args:
            body: The body of the object to upload. Can be a Path, bytes, file-like object, or async iterator.
            key: The S3 key of the object to upload
            category: The category of the object to upload
            part_concurrency: Maximum number of parts to upload at once
            part_size: Size of each part to upload
            retry_settings: Retry settings for each part upload
            progress_cb: This progress callback will be invoked throughout the upload process to report progress

        Returns:
            Upload result
        """
        # Use the multi-file implementation with a single file
        results = await self._put_objects(
            objects=[(body, key)],
            category=category,
            part_concurrency=part_concurrency,
            part_size=part_size,
            retry_settings=retry_settings,
            progress_cb=progress_cb,
        )
        return results[0]

    async def _put_objects(
        self,
        *,
        objects: Iterable[tuple[PutObjectBody, str]],
        category: str,
        object_concurrency: Optional[int] = None,
        part_concurrency: Optional[int] = None,
        part_size: Optional[int] = None,
        retry_settings: Optional[RetrySettings] = None,
        progress_cb: Optional[
            Callable[[UploadStatus], Union[None, Awaitable[None]]]
        ] = None,
    ) -> List[UploadResult]:
        """
        Upload multiple objects to EarthScope's dropoff system.

        Args:
            objects: Iterable of tuples containing (body, key) pairs.
                   The object body can be a Path, bytes, file-like object, or async iterator.
            category: The category of the objects to upload
            object_concurrency: Maximum number of objects to upload at once
            part_concurrency: Maximum number of parts to upload at once across all objects
            part_size: Size of each part to upload
            retry_settings: Retry settings for each part upload
            progress_cb: This progress callback will be invoked throughout the upload process to report progress

        Returns:
            List of upload results
        """
        if not objects:
            return []

        # SDK Defaults
        dropoff_settings = self.ctx.settings.dropoff
        category = self._get_dropoff_category_with_default(category)
        part_size = part_size or dropoff_settings.part_size
        retry_settings = retry_settings or dropoff_settings.retry
        part_concurrency = part_concurrency or dropoff_settings.part_concurrency
        object_concurrency = object_concurrency or dropoff_settings.object_concurrency

        # Prepare generator to yield upload specs for all objects
        content_type = _ContentTypes.get(category)
        euid_b64 = self._user_service.get_user_id(base64=True)

        def get_specs() -> Iterable[UploadSpec]:
            for body, key in objects:
                absolute_key = _get_absolute_s3_path(category, euid_b64, key)
                yield UploadSpec(
                    source=body,
                    bucket=dropoff_settings.bucket,
                    key=absolute_key,
                    content_type=content_type,
                    progress_key=key,  # Use user-provided key for progress
                )

        # Create S3 client and uploader
        creds = await self._user_service.get_aws_credentials(role="s3-dropoff")
        aio_session = aioboto3.Session(
            aws_access_key_id=creds.aws_access_key_id,
            aws_secret_access_key=creds.aws_secret_access_key,
            aws_session_token=creds.aws_session_token,
        )

        async with aio_session.client("s3") as s3_client:
            uploader = AsyncS3MultipartUploader(
                s3_client=s3_client,
                object_concurrency=object_concurrency,
                part_concurrency=part_concurrency,
                part_size=part_size,
                retry_settings=retry_settings,
                state_dir=self.ctx.settings.profile_dir / "dropoff",
                progress_cb=progress_cb,
            )

            # Upload all files with shared worker pool
            return await uploader.upload_many(get_specs())


class AsyncDropoffService(_DropoffService):
    """
    Dropoff functionality
    """

    def __init__(self, ctx: "SdkContext", *, user_service: "AsyncUserService"):
        super().__init__(ctx, user_service=user_service)

        self.get_object_history = self._get_object_history
        self.list_objects = self._list_objects
        self.put_object = self._put_object
        self.put_objects = self._put_objects


class DropoffService(_DropoffService):
    """
    Dropoff functionality
    """

    def __init__(self, ctx: "SdkContext", *, user_service: "AsyncUserService"):
        super().__init__(ctx, user_service=user_service)

        self.get_object_history = ctx.syncify(self._get_object_history)
        self.list_objects = ctx.syncify(self._list_objects)
        self.put_object = ctx.syncify(self._put_object)
        self.put_objects = ctx.syncify(self._put_objects)
