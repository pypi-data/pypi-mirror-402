import asyncio
import inspect
import json
import warnings
from contextlib import suppress
from dataclasses import dataclass
from functools import cached_property
from itertools import chain
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    TypeVar,
    Union,
)

import aiofiles
from aiobotocore.client import AioBaseClient
from aiofiles.os import unlink
from botocore.exceptions import BotoCoreError, ClientError
from typing_extensions import Buffer

from earthscope_sdk.client.dropoff.models import UploadResult, UploadSpec, UploadStatus
from earthscope_sdk.config.models import RetrySettings

MIN_PART_SIZE = 5 * 1024 * 1024  # 5 MB

T = TypeVar("T")


def _wrap_sync_iter(iterable: Iterable[T]) -> AsyncIterator[T]:
    """
    Wraps a synchronous iterable into an asynchronous iterator.
    """

    async def _async_iterator() -> AsyncIterator[T]:
        for item in iterable:
            yield item

    return _async_iterator()


class _UploadState:
    """
    Manages state for a single upload within the multi-upload system.
    """

    def __init__(
        self,
        upload_id: str,
        spec: UploadSpec,
        state_dir: Path,
        progress_cb: Optional[Callable[[UploadStatus], Union[None, Awaitable[None]]]],
    ):
        self.upload_id = upload_id
        self.spec = spec
        self.state_dir = state_dir
        self.progress_cb = progress_cb

        # Per-file state
        self.parts: Dict[int, str] = {}  # part_number -> ETag
        self.bytes_buffered: int = 0
        self.bytes_done: int = 0
        self.bytes_resumed: int = 0  # Bytes already uploaded in previous session
        self.total_bytes: Optional[int] = None
        self.lock = asyncio.Lock()  # Per-file lock for state updates
        self.expected_part_count: Optional[int] = None  # Set by producer when done
        self.completed: bool = False  # Tracks if upload has been completed

        # Derived
        self.progress_key = spec.progress_key or spec.key

    @cached_property
    def state_path(self) -> Path:
        """Path to state file for this upload."""
        safe_key = self.spec.key.replace("/", "__")
        return self.state_dir / f"{self.spec.bucket}__{safe_key}.json"

    async def save_state(self) -> None:
        """Save state to disk (with per-file locking).

        The write operation is shielded from cancellation to ensure atomicity.
        """
        data = {
            "UploadId": self.upload_id,
            "Parts": self.parts,
            "Completed": self.completed,
            "TotalBytes": self.total_bytes,
        }
        body = json.dumps(data, indent=2)

        async def _write_state():
            async with self.lock:
                async with aiofiles.open(self.state_path, "w") as f:
                    await f.write(body)

        # Shield the write from cancellation
        task = asyncio.create_task(_write_state())
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            # Wait for the write to complete before re-raising
            await task
            raise

    async def load_state(self) -> Optional[Dict[str, Any]]:
        """Load state from disk if it exists."""
        with suppress(FileNotFoundError, json.JSONDecodeError):
            async with aiofiles.open(self.state_path, "r") as f:
                txt = await f.read()
                return json.loads(txt)
        return None

    async def delete_state(self) -> None:
        """Delete state file."""
        with suppress(FileNotFoundError):
            await unlink(self.state_path)

    async def call_progress(self) -> None:
        """Call progress callback for this upload."""
        if not self.progress_cb:
            return

        status = UploadStatus(
            key=self.progress_key,
            bytes_buffered=self.bytes_buffered,
            bytes_done=self.bytes_done,
            bytes_resumed=self.bytes_resumed,
            total_bytes=self.total_bytes,
            complete=self.completed,
        )

        if inspect.iscoroutinefunction(self.progress_cb):
            await self.progress_cb(status)
            return

        result = self.progress_cb(status)
        if inspect.isawaitable(result):
            await result


@dataclass
class _QueuedPart:
    """
    A part queued for upload, tagged with its upload context.
    """

    upload_id: str  # Identifies which upload this part belongs to
    part_number: int
    data: bytes


class AsyncS3MultipartUploader:
    """
    Async, concurrent, resumable multipart uploader for S3.

    Designed for uploading multiple files concurrently with shared worker pool.
    All uploads share a single queue and worker pool to maximize throughput.
    """

    def __init__(
        self,
        s3_client: AioBaseClient,
        *,
        object_concurrency: int = 3,
        part_concurrency: int = 8,
        part_size: int = MIN_PART_SIZE,
        retry_settings: RetrySettings = RetrySettings(),
        state_dir: Union[str, Path] = Path(".multipart_upload_state"),
        progress_cb: Optional[
            Callable[[UploadStatus], Union[None, Awaitable[None]]]
        ] = None,
    ) -> None:
        """
        Initialize the multi-file uploader with shared resources.

        Args:
            s3_client: The S3 client to use for all uploads
            object_concurrency: Maximum concurrent files to upload
            part_concurrency: Maximum concurrent parts across ALL uploads
            part_size: Size of each part to upload
            retry_settings: Retry behavior for uploads
            state_dir: Directory to store state files
            progress_cb: Progress callback for all uploads (distinguishes by key)
        """
        # Validate part_size
        if not isinstance(part_size, int) or part_size < MIN_PART_SIZE:
            warnings.warn(
                f"invalid part_size {part_size}; setting to minimum {MIN_PART_SIZE:,} bytes.",
            )
            part_size = MIN_PART_SIZE

        self._s3 = s3_client
        self._part_size = part_size
        self._object_concurrency = object_concurrency
        self._part_concurrency = part_concurrency
        self._retry_settings = retry_settings
        self._progress_cb = progress_cb

        # State management
        self._state_dir = Path(state_dir)
        self._state_dir.mkdir(parents=True, exist_ok=True)

        # Shared resources for all uploads
        self._upload_states: Dict[str, _UploadState] = {}  # upload_id -> state

    # ========== S3 Operations ==========

    async def _create_multipart_upload(self, spec: UploadSpec) -> str:
        """Start a new multipart upload session and return UploadId."""
        args = {"Bucket": spec.bucket, "Key": spec.key}
        if spec.content_type:
            args["ContentType"] = spec.content_type

        try:
            resp = await self._s3.create_multipart_upload(**args)
        except Exception as e:
            raise RuntimeError(f"Failed to create multipart upload for {spec.key}: {e}")

        return resp["UploadId"]

    async def _list_parts(self, spec: UploadSpec, upload_id: str) -> Dict[int, str]:
        """List already uploaded parts from S3."""
        uploaded: Dict[int, str] = {}
        kwargs = {"Bucket": spec.bucket, "Key": spec.key, "UploadId": upload_id}

        while True:
            try:
                resp = await self._s3.list_parts(**kwargs)
            except ClientError as e:
                if e.response["Error"]["Code"] in {"NoSuchUpload", "404"}:
                    return {}
                raise

            for p in resp.get("Parts", []):
                uploaded[p["PartNumber"]] = p["ETag"]

            if not resp.get("IsTruncated"):
                break

            kwargs["PartNumberMarker"] = resp.get("NextPartNumberMarker")

        return uploaded

    async def _complete_multipart_upload(self, state: _UploadState) -> None:
        """Complete the multipart upload."""
        parts_list = [
            {"ETag": etag, "PartNumber": pn} for pn, etag in sorted(state.parts.items())
        ]
        await self._s3.complete_multipart_upload(
            Bucket=state.spec.bucket,
            Key=state.spec.key,
            UploadId=state.upload_id,
            MultipartUpload={"Parts": parts_list},
        )

        # Mark as completed and report final progress
        state.completed = True
        if state.total_bytes is not None and state.bytes_done != state.total_bytes:
            state.bytes_done = state.total_bytes

    async def _try_complete_upload(self, state: _UploadState) -> bool:
        """
        Check if upload is ready to complete and complete it if so.

        Returns:
            True if upload was completed, False otherwise
        """
        async with state.lock:
            # Check if already completed
            if state.completed:
                return True

            # Check if we know the expected count and have all parts
            if state.expected_part_count is not None:
                if len(state.parts) == state.expected_part_count:
                    await self._complete_multipart_upload(state)
                    return True

            return False

    async def _abort_uploads_and_ignore_errors(
        self,
        upload_states: Iterable[_UploadState],
    ) -> None:
        """Abort the multipart uploads and ignore errors."""

        async def _abort_upload(state: _UploadState) -> None:
            with suppress(Exception):
                await self._abort_multipart_upload(state)

        await asyncio.gather(*[_abort_upload(s) for s in upload_states])

    async def _abort_multipart_upload(self, state: _UploadState) -> None:
        """Abort the multipart upload and clean up state."""

        with suppress(ClientError):
            await self._s3.abort_multipart_upload(
                Bucket=state.spec.bucket,
                Key=state.spec.key,
                UploadId=state.upload_id,
            )

        await state.delete_state()

    # ========== Upload Session Management ==========

    async def _start_or_resume_upload(self, spec: UploadSpec) -> _UploadState:
        """Start or resume a single upload, return its state object."""
        state_obj = _UploadState(
            upload_id="",  # Will be set below
            spec=spec,
            state_dir=self._state_dir,
            progress_cb=self._progress_cb,
        )

        # Try to load existing state
        saved_state = await state_obj.load_state()

        if saved_state and (uid := saved_state.get("UploadId")):
            # Resume existing upload
            state_obj.upload_id = uid
            state_obj.parts = {
                int(k): v for k, v in saved_state.get("Parts", {}).items()
            }

            # Check if upload was already completed
            if saved_state.get("Completed", False):
                # Upload was already completed - mark as such and skip reconciliation
                state_obj.completed = True

                # Restore the total bytes and mark as fully uploaded
                state_obj.total_bytes = saved_state.get("TotalBytes")
                state_obj.bytes_done = state_obj.total_bytes or 0
                state_obj.bytes_resumed = state_obj.bytes_done
                state_obj.expected_part_count = len(state_obj.parts)

                # Report progress for the completed upload
                await state_obj.call_progress()

                return state_obj

            # Reconcile with S3
            remote = await self._list_parts(spec, uid)

            # If upload doesn't exist on S3 (was completed/aborted), start fresh
            if not remote and state_obj.parts:
                # Stale state file - start new upload
                state_obj.upload_id = await self._create_multipart_upload(spec)
                state_obj.parts = {}
                state_obj.bytes_resumed = 0  # Not actually resumed since starting fresh
                await state_obj.save_state()
            else:
                # Valid resume - update parts and save
                state_obj.parts.update(remote)
                await state_obj.save_state()
        else:
            # Start new upload
            state_obj.upload_id = await self._create_multipart_upload(spec)
            await state_obj.save_state()

        return state_obj

    # ========== Source Adapters ==========

    async def _iter_file_parts(
        self, path: Path, state: _UploadState
    ) -> AsyncIterator[tuple[int, bytes]]:
        """Yield (part_number, data) tuples from a file."""
        file_size = path.stat().st_size
        state.total_bytes = file_size

        total_parts = (file_size + self._part_size - 1) // self._part_size
        state.expected_part_count = total_parts

        # Calculate bytes already done (for resume)
        already_uploaded_bytes = sum(
            min(self._part_size, file_size - (pn - 1) * self._part_size)
            for pn in state.parts.keys()
        )
        state.bytes_done = already_uploaded_bytes
        state.bytes_buffered = already_uploaded_bytes
        state.bytes_resumed = already_uploaded_bytes
        await state.call_progress()

        # Open file and read parts
        async with aiofiles.open(path, "rb") as f:
            for part_num in range(1, total_parts + 1):
                if part_num in state.parts:
                    continue

                start = (part_num - 1) * self._part_size
                to_read = min(self._part_size, file_size - start)
                await f.seek(start)
                data = await f.read(to_read)
                yield part_num, data

    async def _iter_bytes_parts(
        self, data: Union[bytes, Buffer], state: _UploadState
    ) -> AsyncIterator[tuple[int, bytes]]:
        """Yield (part_number, data) tuples from in-memory bytes."""
        data_bytes = bytes(data)
        state.total_bytes = len(data_bytes)

        total_parts = (len(data_bytes) + self._part_size - 1) // self._part_size
        state.expected_part_count = total_parts

        for part_num in range(1, total_parts + 1):
            if part_num in state.parts:
                continue

            start = (part_num - 1) * self._part_size
            end = min(start + self._part_size, len(data_bytes))
            yield part_num, data_bytes[start:end]

    async def _iter_stream_parts(
        self, stream: AsyncIterator[bytes], state: _UploadState
    ) -> AsyncIterator[tuple[int, bytes]]:
        """Yield (part_number, data) tuples from an async iterator/generator."""
        state.total_bytes = None  # Unknown for streams

        part_num = 1
        buffer = bytearray()

        async for chunk in stream:
            buffer.extend(chunk)

            while len(buffer) >= self._part_size:
                part_data = bytes(buffer[: self._part_size])
                yield part_num, part_data
                buffer = buffer[self._part_size :]
                part_num += 1

        if buffer:
            yield part_num, bytes(buffer)

    async def _iter_filelike_parts(
        self, file_obj: Any, state: _UploadState
    ) -> AsyncIterator[tuple[int, bytes]]:
        """Yield (part_number, data) tuples from a file-like object."""
        # Try to determine total size if seekable
        if hasattr(file_obj, "seek") and hasattr(file_obj, "tell"):
            try:
                current_pos = await asyncio.to_thread(file_obj.tell)
                await asyncio.to_thread(file_obj.seek, 0, 2)
                file_size = await asyncio.to_thread(file_obj.tell)
                await asyncio.to_thread(file_obj.seek, current_pos)
                state.total_bytes = file_size - current_pos
            except (OSError, IOError, ValueError):
                state.total_bytes = None
        else:
            state.total_bytes = None

        part_num = 1
        while True:
            data = await asyncio.to_thread(file_obj.read, self._part_size)
            if not data:
                break
            yield part_num, data
            part_num += 1

    # ========== Producer (shared pool) ==========

    async def _producer_worker(
        self,
        spec_queue: asyncio.Queue[Optional[UploadSpec]],
        part_queue: asyncio.Queue[Optional[_QueuedPart]],
        upload_states: List[_UploadState],
    ) -> None:
        """
        Worker that consumes specs from queue, initializes uploads, and produces parts.

        Multiple workers run concurrently (limited by object_concurrency), providing
        natural backpressure on the input iterable consumption.

        Args:
            spec_queue: Queue of specs to process (None sentinel indicates shutdown)
            part_queue: Queue of parts to process (None sentinel indicates shutdown)
            upload_states: Shared list to append initialized states to
        """
        while True:
            spec = await spec_queue.get()

            try:
                if spec is None:
                    # None sentinel signals shutdown
                    return

                # Initialize the upload (may involve API calls)
                state = await self._start_or_resume_upload(spec)

                # Register state in both tracking structures
                self._upload_states[state.upload_id] = state
                upload_states.append(state)

                # Produce parts for this upload
                await self._produce_parts(spec, state, part_queue)

            finally:
                spec_queue.task_done()

    async def _produce_parts(
        self,
        spec: UploadSpec,
        state: _UploadState,
        part_queue: asyncio.Queue[Optional[_QueuedPart]],
    ) -> int:
        """
        Read parts from source and queue them for upload.

        Called by producer workers. Concurrency is limited by the number of
        producer workers.
        """
        # If upload is already completed, skip part production
        if state.completed:
            return 0

        source = spec.source

        # Convert str to Path
        if isinstance(source, str):
            source = Path(source)

        # Dispatch to appropriate adapter
        if isinstance(source, Path):
            part_iter = self._iter_file_parts(source, state)
        elif isinstance(source, (bytes, bytearray)) or hasattr(source, "__buffer__"):
            part_iter = self._iter_bytes_parts(source, state)
        elif hasattr(source, "read"):
            part_iter = self._iter_filelike_parts(source, state)
        elif hasattr(source, "__aiter__"):
            part_iter = self._iter_stream_parts(source, state)
        elif hasattr(source, "__iter__"):
            part_iter = self._iter_stream_parts(_wrap_sync_iter(source), state)
        else:
            raise TypeError(
                f"Unsupported upload source type. Got {type(source)}, "
                f"expected Path, bytes, file-like object, or (Async)Iterator[bytes]"
            )

        part_count = 0
        async for part_num, data in part_iter:
            # Queue the part with upload context
            queued_part = _QueuedPart(
                upload_id=state.upload_id,
                part_number=part_num,
                data=data,
            )
            await part_queue.put(queued_part)
            part_count += 1

            # Track buffered bytes
            state.bytes_buffered += len(data)
            await state.call_progress()

        # Set expected part count if not already set by the iterator (for sources with unknown size)
        if state.expected_part_count is None:
            state.expected_part_count = part_count

        # If no parts were queued, this may be a resumed upload with all parts uploaded:
        # Try to complete it.
        if part_count == 0 and await self._try_complete_upload(state):
            await state.save_state()
            await state.call_progress()

        return part_count

    # ========== Consumer (shared pool) ==========

    async def _consume_parts(
        self,
        part_queue: asyncio.Queue[Optional[_QueuedPart]],
    ) -> None:
        """
        Consumer that pulls parts from the shared queue and uploads them.
        Multiple consumers run concurrently, all sharing the same queue.
        """
        while True:
            item = await part_queue.get()

            # None sentinel signals shutdown
            if item is None:
                return

            # Get the upload state for this part
            state = self._upload_states.get(item.upload_id)
            if not state:
                # Upload was cancelled or not found
                continue

            # Upload with retry
            async for attempt in self._retry_settings.retry_context(
                BotoCoreError, ClientError
            ):
                with attempt:
                    resp = await self._s3.upload_part(
                        Bucket=state.spec.bucket,
                        Key=state.spec.key,
                        UploadId=item.upload_id,
                        PartNumber=item.part_number,
                        Body=item.data,
                    )

                    # Record success
                    if item.part_number not in state.parts:
                        state.bytes_done += len(item.data)

                    state.parts[item.part_number] = resp["ETag"]

            # Try to complete the upload if all parts have been uploaded
            await self._try_complete_upload(state)

            # Always save state (either partial or completed)
            await state.save_state()

            # Report progress
            await state.call_progress()

    # ========== Utilities ==========

    async def _shutdown_workers(
        self,
        workers: List[asyncio.Task[Any]],
        queue: asyncio.Queue[Optional[Any]],
    ) -> None:
        """
        Shutdown a list of workers and wait for them to finish.

        Args:
            workers: List of worker tasks to shutdown
            queue: Queue to send sentinel to signal shutdown
        """
        for worker in workers:
            # Send sentinel to queue to signal shutdown
            with suppress(asyncio.QueueFull):
                queue.put_nowait(None)

            if not worker.done():
                worker.cancel()

        await asyncio.gather(*workers, return_exceptions=True)

    # ========== Public API ==========

    async def upload_many(self, specs: Iterable[UploadSpec]) -> List[UploadResult]:
        """
        Upload multiple files concurrently with shared worker pool.

        All uploads share the same queue and worker pool, maximizing throughput.
        The input iterable is consumed incrementally with backpressure - new specs
        are only consumed when a producer worker is ready to process them.

        Args:
            specs: Iterable of upload specifications (can be a list, generator, etc.)

        Returns:
            List of upload results (one per spec)
        """
        # Track states as they're created by producer workers
        upload_states: List[_UploadState] = []

        # Queues for feeding specs to producer workers and parts to consumers
        # Queue sizes provide backpressure in order to:
        # - limit the input iterable consumption (caps concurrent object uploads)
        # - limit the number of parts in-flight (caps memory usage and concurrent part uploads)
        spec_queue: asyncio.Queue[Optional[UploadSpec]] = asyncio.Queue(
            maxsize=self._object_concurrency * 2
        )
        part_queue: asyncio.Queue[Optional[_QueuedPart]] = asyncio.Queue(
            maxsize=self._part_concurrency * 2
        )

        # Start shared part consumer pool
        part_consumers = [
            asyncio.create_task(self._consume_parts(part_queue))
            for _ in range(self._part_concurrency)
        ]

        # Start producer workers
        producer_workers = [
            asyncio.create_task(
                self._producer_worker(
                    spec_queue=spec_queue,
                    part_queue=part_queue,
                    upload_states=upload_states,
                )
            )
            for _ in range(self._object_concurrency)
        ]

        try:
            # Feed specs to producers incrementally, followed by sentinels to signal completion
            for spec in chain(specs, [None] * len(producer_workers)):
                await spec_queue.put(spec)
            await asyncio.gather(*producer_workers)

            # Now that producers are done, signal consumers to shutdown and wait for them to finish
            send_sentinels = [part_queue.put(None) for _ in part_consumers]
            await asyncio.gather(*(send_sentinels + part_consumers))

            # Complete any remaining uploads and verify all succeeded
            results = []
            for state in upload_states:
                # Try to complete if not already done
                if not await self._try_complete_upload(state):
                    expected = state.expected_part_count or 0
                    raise RuntimeError(
                        f"Upload incomplete for {state.spec.key}: "
                        f"{expected - len(state.parts)} of {expected} parts failed"
                    )

                # Build result for successfully completed upload
                results.append(
                    UploadResult(
                        bucket=state.spec.bucket,
                        key=state.progress_key,
                        # If total_bytes is None (i.e for generators) use bytes_done
                        size=state.total_bytes or state.bytes_done,
                    )
                )

            # All uploads succeeded - now safe to delete state files
            await asyncio.gather(*[state.delete_state() for state in upload_states])

            return results

        except KeyboardInterrupt:
            # Convert KeyboardInterrupt to CancelledError for proper async cleanup
            raise asyncio.CancelledError("Upload cancelled by user")

        except asyncio.CancelledError:
            # User cancelled - DON'T abort uploads to allow resumption from saved state
            raise

        except Exception:
            # Actual error (not cancellation) - abort uploads since they may be in bad state
            await self._abort_uploads_and_ignore_errors(upload_states)
            raise

        finally:
            # Clean up all workers
            await asyncio.gather(
                self._shutdown_workers(producer_workers, spec_queue),
                self._shutdown_workers(part_consumers, part_queue),
            )

            # Clean up state tracking
            for state in upload_states:
                self._upload_states.pop(state.upload_id, None)

    async def upload(
        self,
        source: Union[Path, str, bytes, Buffer, AsyncIterator[bytes], Any],
        *,
        bucket: str,
        key: str,
        content_type: Optional[str] = None,
        progress_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload a single file (convenience wrapper around upload_many).

        Args:
            source: The source data to upload
            bucket: S3 bucket name
            key: S3 object key
            content_type: Content type for the upload
            progress_key: Key to use in progress callbacks

        Returns:
            Upload result
        """
        spec = UploadSpec(
            source=source,
            bucket=bucket,
            key=key,
            content_type=content_type,
            progress_key=progress_key,
        )
        results = await self.upload_many([spec])
        return results[0]
