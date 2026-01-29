"""
Specific job implementations for Petal Flight Log.

This module provides concrete implementations of the Job base class for:
- S3 file uploads
- ULog file downloads from Pixhawk (MAVLink)
- ULog file downloads from Pixhawk (MAVFTP)
- Flight record synchronization
"""

import asyncio
import os
import time
import uuid
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Set, List, Callable
from datetime import datetime

from petal_app_manager.proxies import S3BucketProxy

from .job_manager import Job, JobStatus
from petal_app_manager.proxies import (
    MavLinkFTPProxy,
    MavLinkExternalProxy,
    MQTTProxy,
    CloudDBProxy,
    LocalDBProxy
)
from petal_app_manager.models import MQTTMessage
from pydantic_core import ValidationError

from .data_model import FlightRecordMatch, GetFlightRecordsRequest

from . import (
    logger,
    __version__,
    FLIGHT_RECORD_TABLE,
    LEAF_FC_RECORD_TABLE,
)

class FetchFlightRecordsJob(Job):
    """
    Job for fetching and constructing flight records.
    
    This is a long-running job (~30 seconds) that:
    1. Scans for rosbag files
    2. Lists ULog files from Pixhawk via MAVFTP
    3. Matches them based on timestamps
    4. Stores results in local and cloud databases
    
    Features:
    - Status tracking (pending, in_progress, completed, error, cancelled)
    - MQTT progress publishing for status updates
    - Singleton per server (only one fetch job runs at a time)
    - Cancellation support
    """
    
    # Class-level singleton tracking
    _active_job_id: Optional[str] = None
    
    def __init__(
        self,
        request: GetFlightRecordsRequest,
        robot_instance_id: str,
        construct_flight_records_func,
        redis_proxy=None,
        local_db_proxy=None,
        cloud_db_proxy=None,
        job_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize fetch flight records job.
        
        Args:
            request: The request parameters for fetching flight records
            robot_instance_id: Robot/machine instance ID
            construct_flight_records_func: Async function to construct flight records
            redis_proxy: Redis proxy for state persistence
            local_db_proxy: Local database proxy
            cloud_db_proxy: Cloud database proxy
            job_id: Unique job identifier
            metadata: Additional metadata
        """
        job_metadata = {
            "tolerance_seconds": request.tolerance_seconds,
            "start_time": request.start_time,
            "end_time": request.end_time,
            "base": request.base,
            "robot_instance_id": robot_instance_id,
        }
        if metadata:
            job_metadata.update(metadata)
        
        super().__init__(job_id=job_id, redis_proxy=redis_proxy, metadata=job_metadata)
        
        self._request = request
        self._robot_instance_id = robot_instance_id
        self._construct_flight_records_func = construct_flight_records_func
        self._local_db_proxy = local_db_proxy
        self._cloud_db_proxy = cloud_db_proxy
        self._flight_records: List[FlightRecordMatch] = []
    
    @property
    def flight_records(self) -> List[FlightRecordMatch]:
        """Get the constructed flight records after job completion."""
        return self._flight_records
    
    async def run(self):
        """Execute flight records fetch operation."""
        logger.info(f"Starting fetch flight records job {self.job_id}")
        
        await self._update_progress(
            percentage=0.0,
            message="Starting flight records fetch..."
        )
        
        try:
            # Parse timestamps
            from datetime import datetime
            start_dt = None
            end_dt = None
            
            if self._request.start_time:
                start_dt = datetime.fromisoformat(self._request.start_time.replace('Z', '+00:00'))
            if self._request.end_time:
                end_dt = datetime.fromisoformat(self._request.end_time.replace('Z', '+00:00'))
            
            await self._update_progress(
                percentage=10.0,
                message="Scanning for flight records..."
            )
            
            # Check for cancellation
            if self.is_cancelled:
                raise asyncio.CancelledError("Job cancelled by user")
            
            # Construct flight records using the provided function
            self._flight_records = await self._construct_flight_records_func(
                robot_instance_id=self._robot_instance_id,
                start_dt=start_dt,
                end_dt=end_dt,
                tolerance_seconds=self._request.tolerance_seconds,
                base=self._request.base
            )
            
            await self._update_progress(
                percentage=50.0,
                message=f"Found {len(self._flight_records)} flight records, caching..."
            )
            
            # Check for cancellation
            if self.is_cancelled:
                raise asyncio.CancelledError("Job cancelled by user")
            
            # Cache flight records in Redis
            if self._redis_proxy:
                import json
                cache_key = f"flight_records:{self._robot_instance_id}"
                await self._redis_proxy.set(
                    cache_key, 
                    json.dumps([record.model_dump() for record in self._flight_records])
                )
            
            await self._update_progress(
                percentage=70.0,
                message="Storing flight records in databases..."
            )
            
            # Store flight records in local and cloud databases
            for i, record in enumerate(self._flight_records):
                # Check for cancellation periodically
                if self.is_cancelled:
                    raise asyncio.CancelledError("Job cancelled by user")
                
                # Save to local DB
                if self._local_db_proxy:
                    local_result = await self._local_db_proxy.set_item(
                        table_name=FLIGHT_RECORD_TABLE,
                        filter_key="id",
                        filter_value=record.id,
                        data=record.model_dump()
                    )
                    if "error" in local_result:
                        logger.error(f"Failed to save flight record {record.id} to local DB: {local_result['error']}")
                
                # Save to cloud DB
                if self._cloud_db_proxy:
                    cloud_result = await self._cloud_db_proxy.set_item(
                        table_name=FLIGHT_RECORD_TABLE,
                        filter_key="id",
                        filter_value=record.id,
                        data=record.model_dump()
                    )
                    if "error" in cloud_result:
                        logger.error(f"Failed to save flight record {record.id} to cloud DB: {cloud_result['error']}")
                
                # Update progress based on records processed
                progress = 70.0 + (30.0 * (i + 1) / len(self._flight_records)) if self._flight_records else 100.0
                await self._update_progress(
                    percentage=progress,
                    message=f"Stored {i + 1}/{len(self._flight_records)} flight records..."
                )
            
            # Store result count in metadata
            self._state.metadata["total_records"] = len(self._flight_records)
            
            await self._update_progress(
                percentage=100.0,
                message=f"Fetch completed. Found {len(self._flight_records)} flight records."
            )
            
            logger.info(f"Fetch flight records job {self.job_id} completed with {len(self._flight_records)} records")
            
        except asyncio.CancelledError:
            logger.info(f"Fetch flight records job {self.job_id} cancelled")
            raise
        except Exception as e:
            logger.error(f"Fetch flight records job {self.job_id} failed: {e}", exc_info=True)
            raise
    
    def _get_payload_model(self) -> type:
        """Override to specify FetchFlightRecordsProgressPayload as the expected model."""
        from .data_model import FetchFlightRecordsProgressPayload
        return FetchFlightRecordsProgressPayload
    
    def _get_mqtt_progress_data(self) -> Dict[str, Any]:
        """Override to provide fetch flight records-specific progress data format."""
        if not self._mqtt_device_id:
            logger.warning(f"FetchFlightRecordsJob {self.job_id}: Cannot generate MQTT progress data without device_id")
            return {}
        
        from .data_model import FetchFlightRecordsProgressPayload
        
        payload = FetchFlightRecordsProgressPayload(
            type="progress",
            job_id=self.job_id,
            machine_id=self._mqtt_device_id,
            status=self.status.value,
            progress=self._state.progress.percentage,
            completed=self.is_completed,
            message=self._state.progress.message or "",
            total_records=self._state.metadata.get("total_records")
        )
        return payload.model_dump()

class S3UploadJob(Job):
    """
    Job for uploading files to S3.
    
    Features:
    - Progress tracking based on file size
    - Automatic retry on transient failures
    - Cancellation support
    """
    
    def __init__(
        self,
        s3_key: str,
        bucket_proxy,
        file_path: Optional[str] = None,
        job_id: Optional[str] = None,
        redis_proxy=None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize S3 upload job.
        
        Args:
            s3_key: S3 key (destination path in bucket)
            bucket_proxy: S3BucketProxy instance
            file_path: Local file path to upload
            job_id: Unique job identifier
            redis_proxy: Redis proxy for state persistence
            metadata: Additional metadata
        """
        # Merge file info into metadata
        file_metadata = {
            "file_path": file_path,
            "s3_key": s3_key,
            "file_size": os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0,
        }
        if metadata:
            file_metadata.update(metadata)
        
        super().__init__(job_id=job_id, redis_proxy=redis_proxy, metadata=file_metadata)
        
        self.file_path = Path(file_path) if file_path else None
        self.s3_key = s3_key
        self._bucket_proxy: S3BucketProxy  = bucket_proxy
    
    def set_file_path(self, new_file_path: str):
        """Update the local file path to upload."""
        self.file_path = Path(new_file_path)
        self._state.metadata["file_path"] = new_file_path
        self._state.metadata["file_size"] = os.path.getsize(new_file_path) if os.path.exists(new_file_path) else 0

    async def run(self):
        """Execute S3 upload"""
        file_size = self.file_path.stat().st_size
        
        logger.info(f"Starting S3 upload: {self.file_path} -> s3://{self.s3_key} ({file_size} bytes)")
        
        await self._update_progress(
            percentage=0.0,
            current=0,
            total=file_size,
            message="Starting upload..."
        )
        
        try:
            # Upload file using bucket proxy
            # The bucket proxy's upload method should support cancellation
            result = await self._upload_with_progress(file_size)
            
            if self.is_cancelled:
                raise asyncio.CancelledError("Upload cancelled by user")
            
            await self._update_progress(
                percentage=100.0,
                current=file_size,
                total=file_size,
                message="Upload completed"
            )
            
            logger.info(f"S3 upload completed: {self.s3_key}")
            
            # Store result in metadata
            self._state.metadata["upload_result"] = result
            
        except asyncio.CancelledError:
            logger.info(f"S3 upload cancelled: {self.s3_key}")
            raise
        except FileNotFoundError as fnf_error:
            logger.error(f"S3 upload failed - file not found: {fnf_error}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"S3 upload failed: {e}", exc_info=True)
            raise
    
    async def _upload_with_progress(self, file_size: int):
        """
        Upload file with progress tracking.
        
        Note: This is a simplified version. In production, you'd want to:
        - Use multipart upload for large files
        - Implement chunked reading/uploading
        - Calculate transfer rate
        """
        # For now, use the bucket proxy's upload method
        # In future, we can enhance this with chunk-level progress
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        result = await self._bucket_proxy.upload_file(
            file_path=self.file_path,
            custom_s3_key=self.s3_key
        )
        
        # Simulate progress updates (bucket proxy should provide real progress)
        await self._update_progress(percentage=100.0, current=file_size, total=file_size)
        
        return result
    
    def _get_payload_model(self) -> type:
        """Override to specify S3UploadProgressPayload as the expected model."""
        from .data_model import S3UploadProgressPayload
        return S3UploadProgressPayload
    
    def _get_mqtt_progress_data(self) -> Dict[str, Any]:
        """Override to provide S3 upload-specific progress data format."""
        if not self._mqtt_device_id:
            logger.warning(f"S3UploadJob {self.job_id}: Cannot generate MQTT progress data without device_id")
            return {}
        
        from .data_model import S3UploadProgressPayload
        
        payload = S3UploadProgressPayload(
            type="progress",
            upload_job_id=self.job_id,
            s3_key=self.s3_key,
            machine_id=self._mqtt_device_id,
            progress=self._state.progress.percentage,
            completed=self.is_completed,
            message=self._state.progress.message or "",
            file_size=self._state.metadata.get("file_size", 0)
        )
        return payload.model_dump()


class ULogDownloadJobMAVLink(Job):
    """
    Job for downloading ULog files from Pixhawk via MAVLink protocol.
    
    Features:
    - Real-time progress tracking
    - Download rate calculation with smoothing
    - Cancellation support via threading.Event
    - WebSocket broadcasting for live updates
    - MQTT progress publishing
    - Buffered download with LOG_DATA stream
    """
    
    def __init__(
        self,
        log_id: int,
        file_path: str,
        mavlink_proxy,
        size_bytes: Optional[int] = None,
        job_id: Optional[str] = None,
        redis_proxy=None,
        timeout: float = 8.0,
        mqtt_proxy=None,
        mqtt_device_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize MAVLink ULog download job.
        
        Args:
            log_id: PX4 log ID
            file_path: Local destination path
            mavlink_proxy: MavLinkExternalProxy instance
            size_bytes: Expected file size (if known from log entries)
            job_id: Unique job identifier
            redis_proxy: Redis proxy for state persistence
            timeout: Timeout for MAVLink operations
            mqtt_proxy: MQTT proxy for publishing progress
            mqtt_device_id: Device ID for MQTT messages
            metadata: Additional metadata
        """
        file_metadata = {
            "log_id": log_id,
            "file_path": file_path,
            "size_bytes": size_bytes,
            "timeout": timeout,
            "protocol": "mavlink"
        }
        if metadata:
            file_metadata.update(metadata)
        
        super().__init__(job_id=job_id, redis_proxy=redis_proxy, metadata=file_metadata)
        
        self.log_id = log_id
        self.file_path = Path(file_path)
        self._mavlink_proxy: MavLinkExternalProxy = mavlink_proxy
        self.size_bytes = size_bytes
        self.timeout = timeout
        self._mqtt_proxy = mqtt_proxy
        self._mqtt_device_id = mqtt_device_id or 'unknown'
        
        # Threading events for MAVLink proxy
        self._cancel_event = threading.Event()
        self._completed_event = threading.Event()
        
        # Buffer for download
        self._buffer = bytearray()
        
        # Progress tracking for rate calculation
        self._start_time: Optional[float] = None
        self._last_progress_value: Optional[float] = None
        self._last_progress_time: Optional[float] = None
        self._current_rate: Optional[float] = None
    
    async def run(self):
        """Execute MAVLink ULog download"""
        logger.info(f"Starting MAVLink ULog download: log_id={self.log_id} -> {self.file_path}")
        
        await self._update_progress(
            percentage=0.0,
            message="Starting MAVLink download..."
        )
        
        try:
            # Ensure directory exists
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download using MAVLink proxy with progress callback
            self._start_time = time.time()
            
            download_task = asyncio.create_task(
                self._mavlink_proxy.download_log_buffered(
                    log_id=self.log_id,
                    completed_event=self._completed_event,
                    cancel_event=self._cancel_event,
                    timeout=self.timeout,
                    buffer=self._buffer,
                    callback=self._on_progress_callback,
                    size_bytes=self.size_bytes
                )
            )
            
            # Wait for download to complete
            result = await download_task
            
            if self.is_cancelled or self._cancel_event.is_set():
                raise asyncio.CancelledError("Download cancelled by user")
            
            # Write buffer to file
            self.file_path.write_bytes(self._buffer)
            
            actual_size = len(self._buffer)
            
            await self._update_progress(
                percentage=100.0,
                current=actual_size,
                total=actual_size,
                message="Download completed"
            )
            
            logger.info(f"MAVLink ULog download completed: {self.file_path} ({actual_size} bytes)")
            
            # Store result in metadata
            self._state.metadata["download_result"] = str(result) if result else None
            self._state.metadata["actual_file_size"] = actual_size
            
        except asyncio.CancelledError:
            logger.info(f"MAVLink ULog download cancelled: log_id={self.log_id}")
            # Clean up partial file
            if self.file_path.exists():
                self.file_path.unlink()
            raise
        except Exception as e:
            logger.error(f"MAVLink ULog download failed: {e}", exc_info=False)
            raise
    
    async def cancel(self) -> bool:
        """Override to set threading cancel event"""
        self._cancel_event.set()
        return await super().cancel()
    
    async def _on_progress_callback(self, received_bytes: int, event_str: str = "downloading"):
        """
        Progress callback matching MAVLink proxy signature.
        
        Args:
            received_bytes: Total bytes received so far
            event_str: Event description (e.g., "downloading")
        """
        # Check if already cancelled
        if self._cancel_event.is_set() or self.is_cancelled:
            return
        
        if not self.size_bytes or self.size_bytes == 0:
            # Can't calculate progress without size
            return
        
        progress = received_bytes / self.size_bytes
        current_time = time.time()
        elapsed_total = current_time - self._start_time
        
        # Calculate current transfer rate using recent interval
        if self._last_progress_value is not None and self._last_progress_time is not None:
            # Calculate data transferred since last update
            progress_delta = progress - self._last_progress_value
            time_delta = current_time - self._last_progress_time
            
            # Only update rate if meaningful time has passed (avoid division by very small numbers)
            if time_delta > 0.5:  # Only update rate calculation every half second
                # Calculate instantaneous rate based on progress since last update
                current_rate = (progress_delta * self.size_bytes) / 1024 / time_delta
                # Use a weighted average to smooth the rate display
                if self._current_rate is not None:
                    # Weighted average: 70% new rate, 30% previous rate
                    self._current_rate = round(0.7 * current_rate + 0.3 * self._current_rate, 1)
                else:
                    self._current_rate = round(current_rate, 1)
                
                # Update tracking variables
                self._last_progress_value = progress
                self._last_progress_time = current_time
        else:
            # First progress update - initialize tracking
            self._last_progress_value = progress
            self._last_progress_time = current_time
            # Use average rate for first update
            if elapsed_total > 0:
                self._current_rate = round(self.size_bytes * progress / 1024 / elapsed_total, 1)
            else:
                self._current_rate = None
        
        # Update progress percentage
        progress_percentage = round(progress * 100, 1)
        
        # Update job progress
        await self._update_progress(
            percentage=progress_percentage,
            current=received_bytes,
            total=self.size_bytes,
            message=f"{event_str}... {progress_percentage}%",
            rate_kbps=self._current_rate
        )
        
    def _get_payload_model(self) -> type:
        """Override to specify ULogDownloadProgressPayload as the expected model."""
        from .data_model import ULogDownloadProgressPayload
        return ULogDownloadProgressPayload
    
    def _get_mqtt_progress_data(self) -> Dict[str, Any]:
        """Override to provide MAVLink-specific progress data format."""
        if not self._mqtt_device_id:
            logger.warning(f"ULogDownloadJobMAVLink {self.job_id}: Cannot generate MQTT progress data without device_id")
            return {}
        
        from .data_model import ULogDownloadProgressPayload
        
        payload = ULogDownloadProgressPayload(
            type="progress",
            download_id=self.job_id,
            log_id=self.log_id,
            machine_id=self._mqtt_device_id,
            progress=self._state.progress.percentage,
            completed=self.is_completed,
            rate_kbps=self._current_rate,
            message=self._state.progress.message or ""
        )
        return payload.model_dump()


class ULogDownloadJobMAVFTP(Job):
    """
    Job for downloading ULog files from Pixhawk via MAVFTP protocol.
    
    Features:
    - Real-time progress tracking
    - Transfer rate calculation with smoothing
    - Cancellation support via threading.Event
    - WebSocket broadcasting for live updates
    - MQTT progress publishing
    """
    
    def __init__(
        self,
        px4_path: str,
        file_path: str,
        mavftp_proxy,
        size_bytes: Optional[int] = None,
        job_id: Optional[str] = None,
        redis_proxy=None,
        mqtt_proxy=None,
        mqtt_device_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize MAVFTP ULog download job.
        
        Args:
            px4_path: Path on Pixhawk (e.g., '/fs/microsd/log/LOG001.ulg')
            file_path: Local destination path
            mavftp_proxy: MavLinkFTPProxy instance
            size_bytes: Expected file size (if known)
            job_id: Unique job identifier
            redis_proxy: Redis proxy for state persistence
            mqtt_proxy: MQTT proxy for publishing progress
            mqtt_device_id: Device ID for MQTT messages
            metadata: Additional metadata
        """
        file_metadata = {
            "px4_path": px4_path,
            "file_path": file_path,
            "size_bytes": size_bytes,
            "protocol": "mavftp"
        }
        if metadata:
            file_metadata.update(metadata)
        
        super().__init__(job_id=job_id, redis_proxy=redis_proxy, metadata=file_metadata)
        
        self.px4_path = px4_path
        self.file_path = Path(file_path)
        self._mavftp_proxy: MavLinkFTPProxy = mavftp_proxy
        self.size_bytes = size_bytes
        self._mqtt_proxy: MQTTProxy = mqtt_proxy
        self._mqtt_device_id = mqtt_device_id or 'unknown'
        
        # Threading events for MAVFTP proxy
        self._cancel_event = threading.Event()
        self._completed_event = threading.Event()
        
        # Progress tracking for rate calculation
        self._start_time: Optional[float] = None
        self._last_progress_value: Optional[float] = None
        self._last_progress_time: Optional[float] = None
        self._current_rate: Optional[float] = None
    
    async def run(self):
        """Execute MAVFTP ULog download"""
        logger.info(f"Starting MAVFTP ULog download: {self.px4_path} -> {self.file_path}")
        
        await self._update_progress(
            percentage=0.0,
            message="Starting MAVFTP download..."
        )
        
        try:
            # Ensure directory exists
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download using MAVFTP proxy with progress callback
            self._start_time = time.time()
            
            download_task = asyncio.create_task(
                self._mavftp_proxy.download_ulog(
                    remote_path=self.px4_path,
                    local_path=self.file_path,
                    completed_event=self._completed_event,
                    on_progress=self._on_progress_callback,
                    cancel_event=self._cancel_event
                )
            )
            
            # Wait for download to complete
            result = await download_task
            
            if self.is_cancelled or self._cancel_event.is_set():
                raise asyncio.CancelledError("Download cancelled by user")
            
            # Verify file was downloaded
            if not self.file_path.exists():
                raise RuntimeError("Download completed but file not found")
            
            actual_size = self.file_path.stat().st_size
            
            await self._update_progress(
                percentage=100.0,
                current=actual_size,
                total=actual_size,
                message="Download completed"
            )
            
            logger.info(f"MAVFTP ULog download completed: {self.file_path} ({actual_size} bytes)")
            
            # Store result in metadata
            self._state.metadata["download_result"] = str(result) if result else None
            self._state.metadata["actual_file_size"] = actual_size
            
        except asyncio.CancelledError:
            logger.info(f"MAVFTP ULog download cancelled: {self.px4_path}")
            # Clean up partial file
            if self.file_path.exists():
                self.file_path.unlink()
            raise
        except RuntimeError as e:
            # Check for specific MAVFTP errors
            if "OpenFileRO failed" in str(e):
                logger.error(f"MAVFTP failed to open remote file '{self.px4_path}': {e}")
                raise RuntimeError(f"Failed to open ULog file on Pixhawk: {self.px4_path}. File may not exist or SD card is not accessible.") from e
            logger.error(f"MAVFTP ULog download failed: {e}", exc_info=False)
            raise
        except Exception as e:
            logger.error(f"MAVFTP ULog download failed: {e}", exc_info=False)
            raise
    
    async def cancel(self) -> bool:
        """Override to set threading cancel event"""
        self._cancel_event.set()
        return await super().cancel()
    
    async def _on_progress_callback(self, progress: float):
        """
        Progress callback matching MAVFTP proxy signature.
        
        Args:
            progress: Progress as float 0.0 to 1.0
        """
        # Check if already cancelled
        if self._cancel_event.is_set() or self.is_cancelled:
            return
        
        current_time = time.time()
        elapsed_total = current_time - self._start_time
        
        # Calculate current transfer rate using recent interval
        if self._last_progress_value is not None and self._last_progress_time is not None:
            # Calculate data transferred since last update
            progress_delta = progress - self._last_progress_value
            time_delta = current_time - self._last_progress_time
            
            # Only update rate if meaningful time has passed (avoid division by very small numbers)
            if time_delta > 0.5:  # Only update rate calculation every half second
                # Calculate instantaneous rate based on progress since last update
                if self.size_bytes:
                    current_rate = (progress_delta * self.size_bytes) / 1024 / time_delta
                    # Use a weighted average to smooth the rate display
                    if self._current_rate is not None:
                        # Weighted average: 70% new rate, 30% previous rate
                        self._current_rate = round(0.7 * current_rate + 0.3 * self._current_rate, 1)
                    else:
                        self._current_rate = round(current_rate, 1)
                else:
                    self._current_rate = None
                
                # Update tracking variables
                self._last_progress_value = progress
                self._last_progress_time = current_time
        else:
            # First progress update - initialize tracking
            self._last_progress_value = progress
            self._last_progress_time = current_time
            # Use average rate for first update
            if self.size_bytes and elapsed_total > 0:
                self._current_rate = round(self.size_bytes * progress / 1024 / elapsed_total, 1)
            else:
                self._current_rate = None
        
        # Update progress percentage
        progress_percentage = round(progress * 100, 1)
        bytes_downloaded = int(progress * self.size_bytes) if self.size_bytes else 0
        
        # Update job progress
        await self._update_progress(
            percentage=progress_percentage,
            current=bytes_downloaded,
            total=self.size_bytes or 0,
            message=f"Downloading... {progress_percentage}%",
            rate_kbps=self._current_rate
        )
    
    def _get_payload_model(self) -> type:
        """Override to specify ULogDownloadProgressPayload as the expected model."""
        from .data_model import ULogDownloadProgressPayload
        return ULogDownloadProgressPayload
    
    def _get_mqtt_progress_data(self) -> Dict[str, Any]:
        """Override to provide MAVFTP-specific progress data format."""
        if not self._mqtt_device_id:
            logger.warning(f"ULogDownloadJobMAVFTP {self.job_id}: Cannot generate MQTT progress data without device_id")
            return {}
        
        from .data_model import ULogDownloadProgressPayload
        
        payload = ULogDownloadProgressPayload(
            type="progress",
            download_id=self.job_id,
            px4_path=self.px4_path,
            machine_id=self._mqtt_device_id,
            progress=self._state.progress.percentage,
            completed=self.is_completed,
            rate_kbps=self._current_rate,
            message=self._state.progress.message or ""
        )
        return payload.model_dump()


class FlightRecordSyncJob(Job):
    """
    Composite job for synchronizing a complete flight record.
    
    This job orchestrates multiple sub-jobs:
    1. Download ULog from Pixhawk (if needed)
    2. Upload ULog to S3
    3. Upload Rosbag to S3
    
    Features:
    - Sub-job management
    - Parallel uploads when possible
    - Overall progress tracking
    - Atomic cancellation (cancels all sub-jobs)
    """
    
    def __init__(
        self,
        flight_record_id: str,
        ulog_download_job: Optional[Job] = None,
        s3_upload_ulog_job: Optional[Job] = None,
        s3_upload_rosbag_job: Optional[Job] = None,
        job_id: Optional[str] = None,
        redis_proxy=None,
        cloud_db_proxy: CloudDBProxy=None,
        local_db_proxy: LocalDBProxy=None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize flight record sync job.
        
        Args:
            flight_record_id: Flight record identifier
            ulog_download_job: Optional ULog download job
            s3_upload_ulog_job: Optional S3 upload job for ULog
            s3_upload_rosbag_job: Optional S3 upload job for Rosbag
            job_id: Unique job identifier
            redis_proxy: Redis proxy for state persistence
            cloud_db_proxy: Cloud database proxy for state persistence
            local_db_proxy: Local database proxy for state persistence
            metadata: Additional metadata
        """
        sync_metadata = {
            "flight_record_id": flight_record_id,
            "ulog_download_job_id": ulog_download_job.job_id if ulog_download_job else None,
            "s3_upload_ulog_job_id": s3_upload_ulog_job.job_id if s3_upload_ulog_job else None,
            "s3_upload_rosbag_job_id": s3_upload_rosbag_job.job_id if s3_upload_rosbag_job else None
        }
        if metadata:
            sync_metadata.update(metadata)
        
        super().__init__(job_id=job_id, redis_proxy=redis_proxy, metadata=sync_metadata)
        
        self.flight_record_id = flight_record_id
        self._ulog_download_job: Optional[ULogDownloadJobMAVFTP] = ulog_download_job
        self._s3_upload_ulog_job: Optional[S3UploadJob] = s3_upload_ulog_job
        self._s3_upload_rosbag_job: Optional[S3UploadJob] = s3_upload_rosbag_job
        self._cloud_db_proxy = cloud_db_proxy
        self._local_db_proxy = local_db_proxy
        
        # Track sub-jobs
        self._sub_jobs = [j for j in [ulog_download_job, s3_upload_ulog_job, s3_upload_rosbag_job] if j]
        
        # Calculate progress weights for each job
        self._job_weights = self._calculate_job_weights()
    
    def _calculate_job_weights(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate the progress weight (slice of the pie) for each sub-job.
        
        Returns a dict mapping job type to {'start': offset, 'weight': percentage}
        
        Weight distribution:
        - If ulog_download_job exists: 90% ulog download, 5% each S3 job
        - If no ulog_download_job: S3 jobs split evenly (50% each, or 100% if only one)
        """
        weights = {}
        s3_jobs = [j for j in [self._s3_upload_ulog_job, self._s3_upload_rosbag_job] if j]
        num_s3_jobs = len(s3_jobs)
        
        if self._ulog_download_job:
            # ULog download gets 90%, S3 jobs split the remaining 10%
            weights['ulog_download'] = {'start': 0.0, 'weight': 90.0}
            
            if num_s3_jobs > 0:
                s3_weight_each = 10.0 / num_s3_jobs  # 5% each if 2 jobs, 10% if 1 job
                current_offset = 90.0
                
                if self._s3_upload_ulog_job:
                    weights['s3_upload_ulog'] = {'start': current_offset, 'weight': s3_weight_each}
                    current_offset += s3_weight_each
                
                if self._s3_upload_rosbag_job:
                    weights['s3_upload_rosbag'] = {'start': current_offset, 'weight': s3_weight_each}
        else:
            # No ulog download, S3 jobs split 100%
            if num_s3_jobs > 0:
                s3_weight_each = 100.0 / num_s3_jobs  # 50% each if 2 jobs, 100% if 1 job
                current_offset = 0.0
                
                if self._s3_upload_ulog_job:
                    weights['s3_upload_ulog'] = {'start': current_offset, 'weight': s3_weight_each}
                    current_offset += s3_weight_each
                
                if self._s3_upload_rosbag_job:
                    weights['s3_upload_rosbag'] = {'start': current_offset, 'weight': s3_weight_each}
        
        return weights
    
    async def _run_wrapper(self):
        """Wrapper to run the main sync logic"""
        # get the flight record from cloud db
        flight_record_result = await self._cloud_db_proxy.get_item(
            table_name=FLIGHT_RECORD_TABLE,
            partition_key="id",
            partition_value=self.flight_record_id
        )
        if "error" in flight_record_result:
            raise RuntimeError(f"Failed to fetch flight record: {flight_record_result['error']}")
        
        try:
            self._flight_record: FlightRecordMatch = FlightRecordMatch.model_validate(flight_record_result.get("data"))
        except ValidationError as ve:
            raise RuntimeError(f"Invalid flight record data: {ve}") from ve

        self._flight_record.sync_job_status = self._state.status.value

        update_cloud_result = await self._cloud_db_proxy.set_item(
            table_name=FLIGHT_RECORD_TABLE,
            filter_key="id",
            filter_value=self.flight_record_id,
            data=self._flight_record.model_dump()
        )

        if "error" in update_cloud_result:
            logger.error(f"Failed to update flight record status: {update_cloud_result['error']}")
            raise RuntimeError(f"Failed to update flight record status: {update_cloud_result['error']}")

        try:
            await super()._run_wrapper()
        except Exception as e:
            # On error, update flight record status before re-raising
            self._flight_record.sync_job_status = self._state.status.value

            update_result = await self._cloud_db_proxy.set_item(
                table_name=FLIGHT_RECORD_TABLE,
                filter_key="id",
                filter_value=self.flight_record_id,
                data=self._flight_record.model_dump()
            )

            if "error" in update_result:
                logger.error(f"Failed to update flight record status: {update_result['error']}")
            raise e

        self._flight_record.sync_job_status = self._state.status.value

        # update sync job status in the cloud db
        update_result = await self._cloud_db_proxy.set_item(
            table_name=FLIGHT_RECORD_TABLE,
            filter_key="id",
            filter_value=self.flight_record_id,
            data=self._flight_record.model_dump()
        )

        if "error" in update_result:
            logger.error(f"Failed to update flight record status: {update_result['error']}")
            raise RuntimeError(f"Failed to update flight record status: {update_result['error']}")
        
        update_result_local = await self._local_db_proxy.set_item(
            table_name=FLIGHT_RECORD_TABLE,
            filter_key="id",
            filter_value=self.flight_record_id,
            data=self._flight_record.model_dump()
        )

        if "error" in update_result_local:
            logger.error(f"Failed to update local flight record status: {update_result_local['error']}")
            raise RuntimeError(f"Failed to update local flight record status: {update_result_local['error']}")

    async def run(self):
        """Execute flight record synchronization"""
        logger.info(f"Starting flight record sync: {self.flight_record_id}")
        
        # Track completed progress offset for proper weight accumulation
        self._completed_progress = 0.0
        
        try:
            # Step 1: Download ULog if needed
            if self._ulog_download_job:
                ulog_weights = self._job_weights.get('ulog_download', {'start': 0.0, 'weight': 0.0})
                
                await self._update_progress(
                    percentage=ulog_weights['start'],
                    message="Downloading ULog from Pixhawk..."
                )
                
                # Start the download job
                await self._ulog_download_job.start()
                
                # Start progress monitoring task that updates sync job progress based on sub-job
                progress_monitor_task = asyncio.create_task(
                    self._monitor_sub_job_progress(
                        sub_job=self._ulog_download_job,
                        step_message="Downloading ULog from Pixhawk...",
                        progress_start=ulog_weights['start'],
                        progress_weight=ulog_weights['weight']
                    )
                )
                
                try:
                    # Wait for download to complete
                    await self._ulog_download_job.wait_for_completion()
                finally:
                    # Always cancel the progress monitor task when sub-job finishes
                    # (whether success, error, or cancellation)
                    progress_monitor_task.cancel()
                    try:
                        await progress_monitor_task
                    except asyncio.CancelledError:
                        pass
                
                if self._ulog_download_job.status != JobStatus.COMPLETED:
                    raise RuntimeError(f"ULog download failed: {self._ulog_download_job._state.error_message}")
                
                ulog_download_job_state = self._ulog_download_job.get_state()
                self._flight_record.ulog.file_path = ulog_download_job_state.metadata.get("file_path")
                self._flight_record.ulog.storage_type = "local"
                
                update_cloud_result = await self._cloud_db_proxy.set_item(
                    table_name=FLIGHT_RECORD_TABLE,
                    filter_key="id",
                    filter_value=self.flight_record_id,
                    data=self._flight_record.model_dump()
                )

                if "error" in update_cloud_result:
                    logger.error(f"Failed to update flight record after ULog download: {update_cloud_result['error']}")
                    raise RuntimeError(f"Failed to update flight record after ULog download: {update_cloud_result['error']}")

                update_local_result = await self._local_db_proxy.set_item(
                    table_name=FLIGHT_RECORD_TABLE,
                    filter_key="id",
                    filter_value=self.flight_record_id,
                    data=self._flight_record.model_dump()
                )

                if "error" in update_local_result:
                    logger.error(f"Failed to update local flight record after ULog download: {update_local_result['error']}")
                    raise RuntimeError(f"Failed to update local flight record after ULog download: {update_local_result['error']}")
                
                self._completed_progress = ulog_weights['start'] + ulog_weights['weight']
            
            # Step 2 & 3: Upload ULog and Rosbag to S3 in parallel
            upload_jobs = [j for j in [self._s3_upload_ulog_job, self._s3_upload_rosbag_job] if j]
            
            if upload_jobs:
                await self._update_progress(
                    percentage=self._completed_progress,
                    message="Uploading files to S3..."
                )
                
                # Start all upload jobs
                upload_tasks = []
                for job in upload_jobs:

                    if job == self._s3_upload_ulog_job:
                        if self._flight_record.ulog.storage_type != "local" or not self._flight_record.ulog.file_path:
                            raise RuntimeError("ULog file path is not available for S3 upload")
                        job.set_file_path(self._flight_record.ulog.file_path)
                    elif job == self._s3_upload_rosbag_job:
                        job.set_file_path(self._flight_record.rosbag.file_path)

                    task = await job.start()
                    upload_tasks.append(task)
                
                # Start progress monitoring for S3 upload jobs
                s3_progress_monitors = []
                for job in upload_jobs:
                    if job == self._s3_upload_ulog_job:
                        job_key = 's3_upload_ulog'
                        step_msg = "Uploading ULog to S3..."
                    else:
                        job_key = 's3_upload_rosbag'
                        step_msg = "Uploading Rosbag to S3..."
                    
                    weights = self._job_weights.get(job_key, {'start': 0.0, 'weight': 0.0})
                    monitor_task = asyncio.create_task(
                        self._monitor_sub_job_progress(
                            sub_job=job,
                            step_message=step_msg,
                            progress_start=weights['start'],
                            progress_weight=weights['weight']
                        )
                    )
                    s3_progress_monitors.append(monitor_task)
                
                # Wait for all uploads to complete
                try:
                    await asyncio.gather(*[job.wait_for_completion() for job in upload_jobs])
                finally:
                    # Cancel all progress monitors when uploads finish
                    for monitor in s3_progress_monitors:
                        monitor.cancel()
                        try:
                            await monitor
                        except asyncio.CancelledError:
                            pass
                
                # Check if all succeeded
                for job in upload_jobs:
                    if job.status != JobStatus.COMPLETED:
                        raise RuntimeError(f"S3 upload failed: {job._state.error_message}")
                
                    job_state = job.get_state()
                    if job == self._s3_upload_ulog_job:
                        self._flight_record.ulog.s3_key = job_state.metadata.get("s3_key")
                    elif job == self._s3_upload_rosbag_job:
                        self._flight_record.rosbag.s3_key = job_state.metadata.get("s3_key")

                    # Update flight record in cloud and local DB
                    update_cloud_result = await self._cloud_db_proxy.set_item(
                        table_name=FLIGHT_RECORD_TABLE,
                        filter_key="id",
                        filter_value=self.flight_record_id,
                        data=self._flight_record.model_dump()
                    )

                    if "error" in update_cloud_result:
                        logger.error(f"Failed to update flight record after S3 uploads: {update_cloud_result['error']}")
                        raise RuntimeError(f"Failed to update flight record after S3 uploads: {update_cloud_result['error']}")

                    update_local_result = await self._local_db_proxy.set_item(
                        table_name=FLIGHT_RECORD_TABLE,
                        filter_key="id",
                        filter_value=self.flight_record_id,
                        data=self._flight_record.model_dump()
                    )

                    if "error" in update_local_result:
                        logger.error(f"Failed to update local flight record after S3 uploads: {update_local_result['error']}")
                        raise RuntimeError(f"Failed to update local flight record after S3 uploads: {update_local_result['error']}")

                # Update completed progress after all S3 uploads
                self._completed_progress = 100.0
            
            # Mark flight record as synced
            self._flight_record.sync_job_status = "completed"

            # Update flight record in cloud and local DB
            update_cloud_result = await self._cloud_db_proxy.set_item(
                table_name=FLIGHT_RECORD_TABLE,
                filter_key="id",
                filter_value=self.flight_record_id,
                data=self._flight_record.model_dump()
            )

            if "error" in update_cloud_result:
                logger.error(f"Failed to update flight record after sync completion: {update_cloud_result['error']}")
                raise RuntimeError(f"Failed to update flight record after sync completion: {update_cloud_result['error']}")

            update_local_result = await self._local_db_proxy.set_item(
                table_name=FLIGHT_RECORD_TABLE,
                filter_key="id",
                filter_value=self.flight_record_id,
                data=self._flight_record.model_dump()
            )

            if "error" in update_local_result:
                logger.error(f"Failed to update local flight record after sync completion: {update_local_result['error']}")
                raise RuntimeError(f"Failed to update local flight record after sync completion: {update_local_result['error']}")

            await self._update_progress(
                percentage=100.0,
                message="Flight record sync completed"
            )
            
            logger.info(f"Flight record sync completed: {self.flight_record_id}")
            
        except asyncio.CancelledError:
            logger.info(f"Flight record sync cancelled: {self.flight_record_id}")
            # Cancel all sub-jobs
            await self._cancel_sub_jobs()
            raise
        except Exception as e:
            logger.error(f"Flight record sync failed: {e}", exc_info=True)
            # Cancel all sub-jobs on error
            await self._cancel_sub_jobs()
            raise
    
    async def _monitor_sub_job_progress(
        self, 
        sub_job: Job, 
        step_message: str,
        progress_start: float,
        progress_weight: float,
        poll_interval: float = 0.5
    ):
        """
        Monitor a sub-job's progress and update the parent sync job's progress accordingly.
        
        This task runs while the sub-job is in progress and updates the sync job's
        overall progress to reflect the sub-job's progress based on its weight slice.
        
        Args:
            sub_job: The sub-job to monitor
            step_message: Message to display during this step
            progress_start: The starting percentage offset for this job's slice
            progress_weight: The percentage weight (slice of the pie) for this job
            poll_interval: How often to poll the sub-job's progress (in seconds)
        """
        try:
            while not sub_job.is_completed:
                sub_job_state = sub_job.get_state()
                sub_job_percentage = sub_job_state.progress.percentage
                rate_kbps = sub_job_state.progress.rate_kbps
                
                # Calculate sync job progress based on this job's weight slice
                # progress = start_offset + (sub_job_progress * weight / 100)
                sub_job_contribution = (sub_job_percentage / 100.0) * progress_weight
                sync_job_percentage = progress_start + sub_job_contribution
                
                # Build message with rate info if available
                message = step_message
                if rate_kbps is not None and rate_kbps > 0:
                    message = f"{step_message} ({rate_kbps:.1f} KB/s)"
                
                await self._update_progress(
                    percentage=sync_job_percentage,
                    message=message,
                    rate_kbps=rate_kbps
                )
                
                await asyncio.sleep(poll_interval)
                
        except asyncio.CancelledError:
            # Task was cancelled - this is expected when sub-job completes
            pass
    
    async def _cancel_sub_jobs(self):
        """Cancel all sub-jobs"""
        for job in self._sub_jobs:
            if not job.is_completed:
                await job.cancel()
    
    async def cancel(self) -> bool:
        """Override to cancel all sub-jobs"""
        await self._cancel_sub_jobs()
        return await super().cancel()
    
    def _get_payload_model(self) -> type:
        """Override to specify FlightRecordSyncProgressPayload as the expected model."""
        from .data_model import FlightRecordSyncProgressPayload
        return FlightRecordSyncProgressPayload
    
    def _get_mqtt_progress_data(self) -> Dict[str, Any]:
        """Override to provide flight record sync-specific progress data format."""
        if not self._mqtt_device_id:
            logger.warning(f"FlightRecordSyncJob {self.job_id}: Cannot generate MQTT progress data without device_id")
            return {}
        
        from .data_model import FlightRecordSyncProgressPayload
        
        payload = FlightRecordSyncProgressPayload(
            type="progress",
            sync_job_id=self.job_id,
            flight_record_id=self.flight_record_id,
            machine_id=self._mqtt_device_id,
            progress=self._state.progress.percentage,
            completed=self.is_completed,
            message=self._state.progress.message or "",
            sub_jobs={
                "ulog_download": self._ulog_download_job.job_id if self._ulog_download_job else None,
                "ulog_upload": self._s3_upload_ulog_job.job_id if self._s3_upload_ulog_job else None,
                "rosbag_upload": self._s3_upload_rosbag_job.job_id if self._s3_upload_rosbag_job else None
            }
        )
        return payload.model_dump()
