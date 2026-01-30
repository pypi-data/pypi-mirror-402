import datetime as dt
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, AsyncIterator, Optional, TypeVar, Union

from pydantic import BaseModel, Field, TypeAdapter
from typing_extensions import Buffer, Generic

P = TypeVar("P", bound=BaseModel)


class DropoffCategory(str, Enum):
    miniSEED = "miniseed"


class DropoffObject(BaseModel):
    path: str
    received_at: dt.datetime
    status: str
    status_message: Optional[str] = None
    size: int
    sha256: Annotated[str, Field(validation_alias="hash")]


class Page(BaseModel, Generic[P]):
    items: list[P]
    offset: int
    limit: int
    has_next: bool = False


GetDropoffObjectHistoryResult = TypeAdapter(Page[DropoffObject])

ListDropoffObjectsResult = TypeAdapter(Page[DropoffObject])


@dataclass
class UploadResult:
    """
    Result of an individual upload.
    """

    bucket: str
    """The S3 bucket of the upload."""

    key: str
    """The object key of the upload."""

    size: int
    """The size of the uploaded object."""


@dataclass
class UploadStatus:
    """
    Status of an individual upload.
    """

    key: str
    """The object key of the upload to which progress is being reported."""

    bytes_done: int
    """The number of bytes uploaded thus far."""

    bytes_buffered: int
    """The number of bytes read and queued for upload (includes bytes_done)."""

    total_bytes: Optional[int]
    """The total number of bytes. May be None for streams with unknown size."""

    complete: bool
    """Whether or not the upload has been completed."""

    bytes_resumed: int = 0
    """The number of bytes that were already uploaded in a previous session (included in bytes_done)."""


@dataclass
class UploadSpec:
    """
    Specification for a single file upload.
    """

    source: Union[Path, str, bytes, Buffer, AsyncIterator[bytes], Any]
    """The source data to upload"""

    bucket: str
    """S3 bucket name"""

    key: str
    """S3 object key"""

    content_type: Optional[str] = None
    """Content type for the upload"""

    progress_key: Optional[str] = None
    """Key to use in progress callbacks (defaults to 'key')"""
