"""Sync JSON data files to/from a GCS bucket. Pull on startup and every 20s; push on every write."""
import logging
import threading
import time
from pathlib import Path
from typing import Optional

from app.core.config import Settings

logger = logging.getLogger(__name__)

# Blob name in bucket is the filename only (e.g. users.json).
SYNC_INTERVAL_SECONDS = 20
_background_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()


def _client():
    from google.cloud import storage
    return storage.Client()


def _data_file_pairs(settings: Settings) -> list[tuple[str, Path]]:
    """Return (blob_name, local_path) for each JSON data file."""
    paths = [
        settings.user_store_path,
        settings.subscription_store_path,
        str(Path(settings.subscription_store_path).parent / "contact_submissions.json"),
    ]
    return [(Path(p).name, Path(p)) for p in paths]


def pull_file(bucket_name: str, blob_name: str, local_path: Path) -> None:
    """Download blob from bucket to local path. No-op if blob does not exist."""
    try:
        client = _client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        if not blob.exists():
            return
        local_path.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(local_path))
        logger.debug("Pulled %s -> %s", blob_name, local_path)
    except Exception as e:
        logger.warning("Pull %s: %s", blob_name, e)


def push_file(bucket_name: str, blob_name: str, local_path: Path) -> None:
    """Upload local file to bucket. No-op if file does not exist."""
    if not local_path.exists():
        return
    try:
        client = _client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(str(local_path))
        logger.debug("Pushed %s -> %s", local_path, blob_name)
    except Exception as e:
        logger.warning("Push %s: %s", blob_name, e)


def sync_from_bucket(settings: Settings) -> None:
    """Pull all data files from the bucket into local paths."""
    bucket = settings.gcs_data_bucket
    if not bucket:
        return
    for blob_name, local_path in _data_file_pairs(settings):
        pull_file(bucket, blob_name, local_path)


def push_data_file(settings: Settings, local_path: str | Path) -> None:
    """Push a single data file to the bucket. No-op if bucket not configured."""
    bucket = settings.gcs_data_bucket
    if not bucket:
        return
    path = Path(local_path)
    blob_name = path.name
    push_file(bucket, blob_name, path)


def _sync_loop(settings_getter) -> None:
    """Background thread: pull from bucket every SYNC_INTERVAL_SECONDS."""
    while not _stop_event.wait(timeout=SYNC_INTERVAL_SECONDS):
        try:
            settings = settings_getter()
            if settings.gcs_data_bucket:
                sync_from_bucket(settings)
        except Exception as e:
            logger.warning("Background sync: %s", e)


def start_background_sync(settings_getter) -> None:
    """Start the background thread that pulls from bucket every 20 seconds."""
    global _background_thread
    if _background_thread is not None:
        return
    _stop_event.clear()
    _background_thread = threading.Thread(
        target=_sync_loop,
        args=(settings_getter,),
        daemon=True,
        name="gcs-sync",
    )
    _background_thread.start()
    logger.info("GCS background sync started (interval=%ss)", SYNC_INTERVAL_SECONDS)


def stop_background_sync() -> None:
    """Signal the background sync thread to stop (e.g. on shutdown)."""
    _stop_event.set()
