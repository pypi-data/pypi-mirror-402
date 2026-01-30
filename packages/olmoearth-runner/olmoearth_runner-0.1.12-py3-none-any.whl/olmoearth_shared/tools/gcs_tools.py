"""Google Cloud Storage utility functions for managing files."""
import logging
import time
from datetime import timedelta
from pathlib import Path

import google.cloud.storage as storage  # type: ignore[import-untyped]
from google.api_core import exceptions as gcp_exceptions
from google.cloud.storage import transfer_manager

logger = logging.getLogger(__name__)

# Default expiration for signed URLs (1 hour)
DEFAULT_SIGNED_URL_EXPIRATION = timedelta(hours=1)

def is_gcs_path(gcs_path: str) -> bool:
    """Check if a path is a GCS path."""
    return gcs_path.startswith("gs://")

def parse_gcs_path(gcs_path: str) -> tuple[str, str]:
    """Parse a GCS path into bucket name and blob name."""
    if not is_gcs_path(gcs_path):
        raise ValueError(f"Invalid GCS path: {gcs_path}")
    parts = gcs_path[5:].split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid GCS path format: {gcs_path}")
    return parts[0], parts[1]


def write_text_to_gcs(gcs_path: str, content: str) -> storage.Blob:
    """Write text content to a file in Google Cloud Storage."""
    client = storage.Client()
    bucket_name, file_path = parse_gcs_path(gcs_path)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    blob.upload_from_string(content)
    return blob


def read_text_from_gcs(gcs_path: str) -> str:
    """Read text content from a file in Google Cloud Storage."""
    bucket_name, file_path = parse_gcs_path(gcs_path)
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    return blob.download_as_text()


def get_blob(gcs_path: str) -> storage.Blob:
    """Returns the reference to the blob object in GCS."""
    bucket_name, file_path = parse_gcs_path(gcs_path)
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    blob.reload()
    return blob


def blob_exists(gcs_path: str) -> bool:
    """Check if a blob exists in Google Cloud Storage."""
    bucket_name, file_path = parse_gcs_path(gcs_path)
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    return blob.exists()


def generate_signed_url(gcs_path: str, expiration: timedelta = DEFAULT_SIGNED_URL_EXPIRATION) -> str:
    """Generate a signed URL for read access to a GCS object."""
    bucket_name, file_path = parse_gcs_path(gcs_path)
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    return blob.generate_signed_url(expiration=expiration, method="GET")


def copy_gcs_file(source_gcs_path: str, dest_gcs_path: str) -> storage.Blob:
    """
    Copy a file from one GCS location to another. Returns the new Blob.
    """
    # Parse paths
    source_bucket_name, source_path = parse_gcs_path(source_gcs_path)
    dest_bucket_name, dest_path = parse_gcs_path(dest_gcs_path)

    client = storage.Client()

    # Get source bucket and blob
    source_bucket = client.bucket(source_bucket_name)
    source_blob = source_bucket.blob(source_path)

    # Get destination bucket
    dest_bucket = client.bucket(dest_bucket_name)

    # Copy the blob
    return source_bucket.copy_blob(source_blob, dest_bucket, dest_path)


def write_file_to_gcs(local_path: str, gcs_dest_path: str) -> storage.Blob:
    """
    Write a local file to Google Cloud Storage.
    Returns the Blob object for the uploaded file.
    """
    client = storage.Client()
    bucket_name, file_path = parse_gcs_path(gcs_dest_path)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)

    # Upload the local file
    blob.upload_from_filename(local_path)
    return blob


def download_file_from_gcs(gcs_path: str, local_dest_path: str) -> None:
    """ Download a file from Google Cloud Storage to a local path."""
    bucket_name, file_path = parse_gcs_path(gcs_path)
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)

    # Download the blob to the local path
    blob.download_to_filename(local_dest_path)


def parse_and_normalize_gcs_directory_path(gcs_path: str) -> tuple[str, str]:
    """
    Parse a GCS path and normalize it for directory-like behavior.

    Returns (bucket_name, normalized_prefix) where the prefix ends with a slash.
    Uses parse_gcs_path for validation and parsing, then normalizes the prefix.
    """
    bucket_name, prefix = parse_gcs_path(gcs_path)

    # Normalize the prefix to ensure it ends with a slash for directory-like behavior
    # Special case: if prefix is empty (root bucket), keep it empty for proper matching
    if prefix and not prefix.endswith("/"):
        prefix = prefix + "/"

    return bucket_name, prefix


def gcs_directory_exists(gcs_path: str) -> bool:
    """
    Check if a GCS directory-like path exists and contains files.

    This validates that the path represents a directory containing files, not just
    a prefix that might match unrelated files.
    """
    try:
        bucket_name, prefix = parse_and_normalize_gcs_directory_path(gcs_path)

        client = storage.Client()
        bucket = client.bucket(bucket_name)

        # List blobs with the exact prefix (directory-like) to see if any exist
        # This ensures we only find blobs that are actually "in" the directory
        blobs = list(bucket.list_blobs(prefix=prefix, max_results=1))
        return len(blobs) > 0

    except gcp_exceptions.NotFound:
        return False
    except Exception:
        return False


def validate_gcs_directory(gcs_path: str) -> None:
    """
    Cloud storage prefixes are not actually fs directories, they are just a prefix of the path.
    `gs://bucket/prefix` will match both:
    `gs://bucket/prefix/` --> what we care about
    `gs://bucket/prefix_heehee.txt` --> not something we want to mistake for a directory

    Here we check that the prefix can be treated as a directory and confirm its existence in storage.

    Raises ValueError if the directory doesn't exist or is empty.
    This is a convenience function that combines normalization and existence checking.
    """
    try:
        bucket_name, prefix = parse_and_normalize_gcs_directory_path(gcs_path)

        client = storage.Client()
        bucket = client.bucket(bucket_name)

        # List blobs with the exact prefix (directory-like) to see if any exist
        blobs = list(bucket.list_blobs(prefix=prefix, max_results=1))
        if not blobs:
            raise ValueError(f"GCS directory not found or empty: {gcs_path}")

    except gcp_exceptions.NotFound as e:
        raise ValueError(f"GCS resource not found: {gcs_path}") from e

def copy_gcs_directory(source_gcs_dir: str, dest_gcs_dir: str) -> None:
    """
    Copy all files from one GCS directory to another.

    Args:
        source_gcs_dir: Source GCS directory path (e.g., "gs://bucket/source/")
        dest_gcs_dir: Destination GCS directory path (e.g., "gs://bucket/dest/")

    Raises:
        ValueError: If the source directory doesn't exist
    """
    # Validate source directory exists
    validate_gcs_directory(source_gcs_dir)

    # Parse source and destination paths
    source_bucket_name, source_prefix = parse_and_normalize_gcs_directory_path(source_gcs_dir)
    dest_bucket_name, dest_prefix = parse_and_normalize_gcs_directory_path(dest_gcs_dir)

    client = storage.Client()
    source_bucket = client.bucket(source_bucket_name)
    dest_bucket = client.bucket(dest_bucket_name)

    # List all blobs in the source directory
    source_blobs = source_bucket.list_blobs(prefix=source_prefix)

    for source_blob in source_blobs:
        # Calculate relative path from source prefix
        relative_path = source_blob.name[len(source_prefix):]

        # Skip empty relative paths (this would be the directory marker itself)
        if not relative_path:
            continue

        # Construct destination blob name
        dest_blob_name = dest_prefix + relative_path

        # Copy the blob
        source_bucket.copy_blob(source_blob, dest_bucket, dest_blob_name)


def _find_common_prefix(blob_names: list[str]) -> str:
    """
    Find the longest common directory prefix across blob names.

    Returns a prefix ending with '/' or empty string if no common prefix.
    For a single blob, returns its parent directory.
    """
    if not blob_names:
        return ""

    if len(blob_names) == 1:
        # For a single file, use its parent directory as prefix
        if '/' in blob_names[0]:
            return blob_names[0].rsplit('/', 1)[0] + '/'
        return ""

    # Find common prefix across all blob names
    common = blob_names[0]
    for name in blob_names[1:]:
        # Find common prefix between current common and this name
        while not name.startswith(common):
            common = common[:-1]
            if not common:
                return ""

    # Ensure we end at a directory boundary (last '/')
    if '/' in common:
        return common[:common.rfind('/') + 1]
    return ""


def copy_files_to_gcs_directory(local_dir: str, gcs_dest_dir: str, num_workers: int, worker_type: str) -> None:
    """
    Upload all files from a local directory to a GCS directory using parallel uploads.

    Args:
        local_dir: Local directory path containing files to upload
        gcs_dest_dir: Destination GCS directory path (e.g., "gs://bucket/dest")
        num_workers: Number of parallel workers to use for upload
        worker_type: 'process' or 'thread' for upload concurrency. See: google.cloud.storage.transfer_manager.[THREAD|PROCESS]
          `thread` is recommended for many small files,
          `process` for fewer large files
    """
    client = storage.Client()
    files_to_upload = [str(p.relative_to(local_dir)) for p in Path(local_dir).rglob("*") if p.is_file()]
    bucket_name, bucket_path = parse_gcs_path(gcs_dest_dir)
    logger.info(f"Uploading {len(files_to_upload)} files from {local_dir} to {gcs_dest_dir} using {num_workers} {worker_type} workers")
    results = transfer_manager.upload_many_from_filenames(
        bucket=client.bucket(bucket_name),
        filenames=files_to_upload,
        source_directory=local_dir,
        blob_name_prefix=bucket_path + '/',  # Add / to the end of the prefix because the filenames get exactly appended to this string.
        worker_type=worker_type,
        max_workers=num_workers,
    )

    # `results` is a list of UploadResult objects. None means success, otherwise log the error.
    if any(results):
        for result in filter(None, results):
            logger.error(f"Upload failed for {result.source_filename} to {result.blob.name}: {result.exception}")
        raise RuntimeError("Uploading files failed. See logs for details.")
    logger.info(f"Successfully uploaded {len(files_to_upload)} files from {local_dir} to {gcs_dest_dir}")

def get_gcs_directory_size_mb(gcs_dir: str) -> float:
    """Calculate total size of GCS directory in megabytes."""
    bucket_name, prefix = parse_and_normalize_gcs_directory_path(gcs_dir)
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    total_bytes = sum(
        blob.size for blob in bucket.list_blobs(prefix=prefix)
        if not blob.name.endswith('/')
    )
    return total_bytes / (1024 * 1024)


def list_gcs_directory(gcs_source_dir: str, page_size: int = 5000) -> list[str]:
    """List all files in a GCS directory."""
    client = storage.Client()
    bucket_name, bucket_prefix = parse_and_normalize_gcs_directory_path(gcs_source_dir)
    bucket = client.bucket(bucket_name)

    gcs_paths = []
    for blob in bucket.list_blobs(prefix=bucket_prefix, page_size=page_size):
        if not blob.name.endswith('/'):
            gcs_paths.append(f"gs://{bucket_name}/{blob.name}")

    return gcs_paths


def download_gcs_files(
    gcs_paths: list[str],
    local_dest_dir: Path,
    num_workers: int = 8,
    worker_type: str = "thread",
    blob_prefix: str | None = None,
) -> list[Path]:
    """Download specific files from GCS to a local directory using parallel downloads."""
    if not gcs_paths:
        raise ValueError("gcs_paths cannot be empty")

    # Parse all GCS paths and validate they're in the same bucket
    client = storage.Client()
    parsed_paths = [parse_gcs_path(path) for path in gcs_paths]
    bucket_names = {bucket_name for bucket_name, _ in parsed_paths}

    if len(bucket_names) > 1:
        raise ValueError(f"All GCS paths must be in the same bucket. Found buckets: {bucket_names}")

    bucket_name = bucket_names.pop()
    blob_names = [blob_name for _, blob_name in parsed_paths]

    # Auto-detect common prefix if not provided
    if blob_prefix is None:
        blob_prefix = _find_common_prefix(blob_names)

    # Calculate relative blob names by stripping the prefix
    relative_blob_names = [name[len(blob_prefix):] for name in blob_names]

    logger.info(f"Starting download of {len(gcs_paths)} files to {local_dest_dir} using {num_workers} {worker_type} workers...")
    local_dest_dir.mkdir(parents=True, exist_ok=True)
    download_start_time = time.monotonic()

    bucket = client.bucket(bucket_name)
    results = transfer_manager.download_many_to_path(
        bucket=bucket,
        blob_names=relative_blob_names,
        destination_directory=str(local_dest_dir),
        blob_name_prefix=blob_prefix,
        worker_type=worker_type,
        max_workers=num_workers,
    )
    download_elapsed = time.monotonic() - download_start_time
    logger.info(f"Downloaded {len(gcs_paths)} files in {download_elapsed}s.")

    # `results` is a list of DownloadResult objects. None means success, otherwise it contains an exception.
    for blob_name, result in zip(relative_blob_names, results, strict=True):
        if result is not None:
            logger.error(f"Download failed for {blob_name}: {result}")
            raise RuntimeError("Downloading files failed. See logs for details.")

    # Return list of local file paths
    return [local_dest_dir / relative_name for relative_name in relative_blob_names]


def copy_files_from_gcs_directory(
    gcs_source_dir: str,
    local_dest_dir: str,
    num_workers: int,
    worker_type: str,
    initialize_dir_if_empty: bool = True,
) -> None:
    """
    Download all files from a GCS directory to a local directory using parallel downloads.

    Args:
        gcs_source_dir: Source GCS directory path (e.g., "gs://bucket/source")
        local_dest_dir: Destination local directory path
        num_workers: Number of parallel workers to use for download
        worker_type: 'process' or 'thread' for download concurrency. See: google.cloud.storage.transfer_manager.[THREAD|PROCESS]
          `thread` is recommended for many small files,
          `process` for fewer large files
        initialize_dir_if_empty: If True and the GCS directory is empty or doesn't exist,
          create an empty local directory instead of raising an error. Defaults to True.
    """
    # List all files in the directory
    gcs_paths = list_gcs_directory(gcs_source_dir)

    # Handle empty GCS directory
    if not gcs_paths:
        if initialize_dir_if_empty:
            Path(local_dest_dir).mkdir(parents=True, exist_ok=True)
            return
        else:
            raise ValueError(f"GCS directory is empty or does not exist: {gcs_source_dir}")

    # Get the normalized prefix to use for downloads
    _, bucket_prefix = parse_and_normalize_gcs_directory_path(gcs_source_dir)

    # Download all files using the explicit prefix
    download_gcs_files(
        gcs_paths=gcs_paths,
        local_dest_dir=Path(local_dest_dir),
        num_workers=num_workers,
        worker_type=worker_type,
        blob_prefix=bucket_prefix,
    )
