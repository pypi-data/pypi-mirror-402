"""
Archive builder for creating artifacts.tar.zst files.

This module creates compressed tar archives containing command execution data
and optional attachments in the format required by the /collect API endpoint.
"""

import io
import json
import logging
import mimetypes
import os
import pathlib
import tarfile
import tempfile
from datetime import UTC, datetime
from typing import Dict, Optional

import zstandard as zstd
from pydantic import BaseModel

from obvyr_cli.schemas import RunCommandResponse

logger = logging.getLogger(__name__)

# Attachment governance limits (per pricing strategy)
MAX_ATTACHMENT_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB per file
MAX_TOTAL_ATTACHMENT_SIZE_BYTES = 10 * 1024 * 1024  # 10MB per observation

# Allowed MIME types for text-only attachments
ALLOWED_MIME_TYPES = {
    "text/plain",
    "text/xml",
    "application/xml",
    "application/json",
    "text/html",
    "text/csv",
    "application/x-yaml",
    "text/yaml",
    "application/yaml",  # Python 3.14+ uses this for .yaml files
}

# Priority levels for attachment selection (higher = more valuable)
MIME_TYPE_PRIORITY = {
    # High priority: Structured data that converts to server data
    "text/xml": 3,
    "application/xml": 3,
    "application/json": 3,
    # Medium priority: Semi-structured data
    "application/x-yaml": 2,
    "text/yaml": 2,
    "application/yaml": 2,
    "text/csv": 2,
    # Low priority: Plain text
    "text/plain": 1,
    "text/html": 1,
}


class AttachmentFileSizeExceededError(Exception):
    """Raised when an individual attachment file exceeds 5MB limit."""

    pass


class AttachmentTotalSizeExceededError(Exception):
    """Raised when total attachment size exceeds 10MB limit."""

    pass


class AttachmentInvalidFormatError(Exception):
    """Raised when attachment is not a text-based file."""

    pass


class ArchiveSummary(BaseModel):
    """Summary of archive contents and sizes."""

    archive_bytes: int
    members: Dict[str, Dict[str, int]]


def get_attachment_mime_type(attachment_path: pathlib.Path) -> str:
    """Get MIME type for an attachment file.

    Args:
        attachment_path: Path to the attachment file

    Returns:
        Detected MIME type string
    """
    mime_type, _ = mimetypes.guess_type(str(attachment_path))
    if mime_type is None:
        # If MIME type cannot be determined, check file extension
        # Default to text/plain for common text extensions
        text_extensions = {
            ".txt",
            ".log",
            ".xml",
            ".json",
            ".yaml",
            ".yml",
            ".csv",
        }
        if attachment_path.suffix.lower() not in text_extensions:
            mime_type = "application/octet-stream"
        else:
            mime_type = "text/plain"

    return mime_type


def validate_attachment_file(
    attachment_path: pathlib.Path,
) -> tuple[bool, Optional[str]]:
    """Validate individual attachment file.

    Args:
        attachment_path: Path to the attachment file

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    file_size = attachment_path.stat().st_size

    # Check individual file size limit (5MB)
    if file_size > MAX_ATTACHMENT_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        return (
            False,
            f"File '{attachment_path.name}' exceeds 5MB limit ({size_mb:.2f} MB)",
        )

    # Check MIME type (text-only restriction)
    mime_type = get_attachment_mime_type(attachment_path)

    if mime_type not in ALLOWED_MIME_TYPES:
        return (
            False,
            f"File '{attachment_path.name}' is not a text file (detected: {mime_type})",
        )

    return True, None


def select_attachments_with_priority(
    attachment_paths: list[pathlib.Path],
) -> list[pathlib.Path]:
    """Select attachments up to size limit with priority-based ordering.

    Prioritizes structured data (XML, JSON) over plain text files.
    Skips invalid files with warning logs instead of raising exceptions.

    Args:
        attachment_paths: List of attachment file paths

    Returns:
        List of valid attachment paths to include, up to 10MB total
    """
    # Filter out non-existent files
    existing_paths = [p for p in attachment_paths if p.exists()]

    # Validate each file and collect valid ones with metadata
    valid_files: list[tuple[pathlib.Path, str, int, int]] = []

    for path in existing_paths:
        is_valid, error_msg = validate_attachment_file(path)

        if not is_valid:
            logger.warning(f"Skipping attachment: {error_msg}")
            continue

        mime_type = get_attachment_mime_type(path)
        file_size = path.stat().st_size
        priority = MIME_TYPE_PRIORITY.get(mime_type, 0)

        valid_files.append((path, mime_type, file_size, priority))

    # Sort by priority (descending), then by size (ascending for better packing)
    valid_files.sort(key=lambda x: (-x[3], x[2]))

    # Select files up to 10MB limit
    selected_paths: list[pathlib.Path] = []
    total_size = 0

    for path, _mime_type, file_size, _priority in valid_files:
        if total_size + file_size <= MAX_TOTAL_ATTACHMENT_SIZE_BYTES:
            selected_paths.append(path)
            total_size += file_size
        else:
            size_mb = file_size / (1024 * 1024)
            logger.warning(
                f"Skipping attachment '{path.name}' ({size_mb:.2f} MB): "
                f"would exceed 10MB total limit"
            )

    return selected_paths


def build_artifacts_tar_zst(
    run_command_response: RunCommandResponse,
    attachment_paths: Optional[list[pathlib.Path]] = None,
    tmp_dir: Optional[pathlib.Path] = None,
    tags: Optional[list[str]] = None,
) -> pathlib.Path:
    """
    Build artifacts.tar.zst archive from command execution data.

    Creates a compressed tar archive containing:
    - /command.json (required)
    - /output.txt (optional; UTF-8 mixed stdout/stderr)
    - /attachment/<filename> (optional)

    Args:
        run_command_response: Command execution response containing metadata and output
        attachment_paths: Optional list of attachment files to include
        tmp_dir: Optional temporary directory for output file
        tags: Optional list of tags to include in command.json

    Returns:
        Path to the created artifacts.tar.zst file

    Note:
        Invalid or oversized attachments are skipped with warning logs.
        Attachments are prioritized by value (XML/JSON > YAML/CSV > TXT/LOG).
    """
    if tmp_dir is None:
        tmp_dir = pathlib.Path(tempfile.gettempdir())

    # Select valid attachments with priority-based ordering
    selected_attachments: list[pathlib.Path] = []
    if attachment_paths:
        selected_attachments = select_attachments_with_priority(
            attachment_paths
        )

    # Create output file path
    output_path = tmp_dir / "artifacts.tar.zst"

    # Prepare command.json data exactly as specified in the doc
    command_data = {
        "command": run_command_response.command,
        "user": run_command_response.user,
        "return_code": run_command_response.returncode,
        "execution_time_ms": round(run_command_response.execution_time * 1000),
        "executed": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "env": dict(os.environ),
        "tags": tags or [],
    }

    # Create tar archive in memory first
    tar_buffer = io.BytesIO()

    with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
        # Add command.json (required)
        command_json_bytes = json.dumps(
            command_data, separators=(",", ":")
        ).encode("utf-8")
        command_info = tarfile.TarInfo("command.json")
        command_info.size = len(command_json_bytes)
        tar.addfile(command_info, io.BytesIO(command_json_bytes))

        # Add output.txt if present (optional; mixed stdout/stderr)
        if run_command_response.output:
            output_bytes = run_command_response.output.encode("utf-8")
            output_info = tarfile.TarInfo("output.txt")
            output_info.size = len(output_bytes)
            tar.addfile(output_info, io.BytesIO(output_bytes))

        # Add selected attachments (optional)
        for attachment_path in selected_attachments:
            # Use attachment/<filename> structure as specified
            arcname = f"attachment/{attachment_path.name}"

            # Stream file without loading into memory
            with open(attachment_path, "rb") as f:
                attachment_info = tarfile.TarInfo(arcname)
                attachment_info.size = attachment_path.stat().st_size
                tar.addfile(attachment_info, f)

    # Compress tar with zstd
    tar_buffer.seek(0)
    tar_data = tar_buffer.read()

    compressor = zstd.ZstdCompressor(write_content_size=True)
    compressed_data = compressor.compress(tar_data)

    with open(output_path, "wb") as output_file:
        output_file.write(compressed_data)

    return output_path


def summarize_archive(archive_path: pathlib.Path) -> ArchiveSummary:
    """
    Summarise contents of an artifacts.tar.zst archive.

    Args:
        archive_path: Path to the artifacts.tar.zst file

    Returns:
        ArchiveSummary containing archive size and member information

    Raises:
        FileNotFoundError: If archive file doesn't exist
    """
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    # Get archive size
    archive_bytes = archive_path.stat().st_size

    # Extract and examine tar contents
    decompressor = zstd.ZstdDecompressor()
    members: Dict[str, Dict[str, int]] = {}

    with open(archive_path, "rb") as archive_file:
        with decompressor.stream_reader(archive_file) as reader:
            with tarfile.open(
                fileobj=reader, mode="r|"
            ) as tar:  # pragma: no branch
                # Note: The "no branch" pragma is needed because coverage.py reports
                # uncoverable branches for the context manager entry/exit in combination
                # with the for loop. Both branches (tar with/without members) are tested.
                for member in tar:
                    if member.isfile():
                        members[member.name] = {"bytes": member.size}

    return ArchiveSummary(archive_bytes=archive_bytes, members=members)
