"""File handling utilities for plugins in sandbox environment.

This module provides file access capabilities for plugins running in sandbox.
Files are transferred as base64-encoded data for security and compatibility.
"""

import base64
import io
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Optional


@dataclass
class PluginFile:
    """File representation for plugin operations.

    This class wraps file data transferred from the workflow engine.
    Files are transferred as base64 for JSON compatibility.

    Attributes:
        file_id: Unique identifier from files table
        filename: Original filename
        content: Binary file content (decoded from base64)
        mimetype: MIME type
        size: File size in bytes
        extension: File extension without dot

    Example:
        >>> # In plugin node
        >>> file_data = inputs.get("document")
        >>> file = PluginFile.from_dict(file_data)
        >>> text = file.content.decode('utf-8')
        >>> print(f"Processing {file.filename} ({file.size} bytes)")
    """

    file_id: str
    filename: str
    content: bytes
    mimetype: str
    size: int
    extension: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PluginFile":
        """Create PluginFile from serialized dict.

        Args:
            data: Dictionary with file metadata and base64 content

        Returns:
            PluginFile instance

        Raises:
            ValueError: If required fields are missing or invalid

        Example:
            >>> file_data = {
            ...     "_type": "_plugin_file",
            ...     "file_id": "abc-123",
            ...     "filename": "data.txt",
            ...     "content_base64": "SGVsbG8gV29ybGQ=",
            ...     "mimetype": "text/plain",
            ...     "size": 11,
            ...     "extension": "txt"
            ... }
            >>> file = PluginFile.from_dict(file_data)
        """
        # Validate structure
        if not isinstance(data, dict):
            raise ValueError("File data must be a dictionary")

        if data.get("_type") != "_plugin_file":
            raise ValueError(
                f"Invalid file type marker: expected '_plugin_file', "
                f"got '{data.get('_type')}'"
            )

        # Extract fields
        try:
            file_id = data["file_id"]
            filename = data["filename"]
            content_base64 = data["content_base64"]
            mimetype = data.get("mimetype", "application/octet-stream")
            size = data["size"]
            extension = data.get("extension", "")
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")

        # Decode base64 content
        try:
            content = base64.b64decode(content_base64)
        except Exception as e:
            raise ValueError(f"Failed to decode base64 content: {e}")

        # Validate size
        actual_size = len(content)
        if actual_size != size:
            raise ValueError(
                f"Size mismatch: expected {size} bytes, got {actual_size} bytes"
            )

        return cls(
            file_id=file_id,
            filename=filename,
            content=content,
            mimetype=mimetype,
            size=size,
            extension=extension,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize PluginFile to dict (for output).

        Returns:
            Dictionary with file metadata and base64 content

        Example:
            >>> file = PluginFile(...)
            >>> file_data = file.to_dict()
            >>> return {"output_file": file_data}
        """
        return {
            "_type": "_plugin_file",
            "file_id": self.file_id,
            "filename": self.filename,
            "content_base64": base64.b64encode(self.content).decode("ascii"),
            "mimetype": self.mimetype,
            "size": self.size,
            "extension": self.extension,
        }

    def save_to(self, path: str | Path) -> None:
        """Save file content to disk.

        Args:
            path: Destination file path

        Example:
            >>> file = PluginFile.from_dict(file_data)
            >>> file.save_to("/tmp/output.pdf")
        """
        path = Path(path)
        path.write_bytes(self.content)

    def as_text(self, encoding: str = "utf-8") -> str:
        """Decode file content as text.

        Args:
            encoding: Text encoding (default: utf-8)

        Returns:
            Decoded text content

        Raises:
            UnicodeDecodeError: If content cannot be decoded

        Example:
            >>> file = PluginFile.from_dict(file_data)
            >>> text = file.as_text()
        """
        return self.content.decode(encoding)

    def as_stream(self) -> BinaryIO:
        """Get file content as binary stream.

        Returns:
            BytesIO stream positioned at start

        Example:
            >>> file = PluginFile.from_dict(file_data)
            >>> stream = file.as_stream()
            >>> data = stream.read()
        """
        return io.BytesIO(self.content)

    def __len__(self) -> int:
        """Return file size in bytes."""
        return self.size

    def __repr__(self) -> str:
        """Human-readable representation."""
        size_kb = self.size / 1024
        return (
            f"PluginFile(file_id='{self.file_id}', "
            f"filename='{self.filename}', "
            f"mimetype='{self.mimetype}', "
            f"size={size_kb:.1f} KB)"
        )


def is_plugin_file(obj: Any) -> bool:
    """Check if object is a plugin file dict.

    Args:
        obj: Object to check

    Returns:
        True if obj is a valid plugin file dict

    Example:
        >>> if is_plugin_file(inputs.get("document")):
        ...     file = PluginFile.from_dict(inputs["document"])
    """
    if not isinstance(obj, dict):
        return False
    return obj.get("_type") == "_plugin_file"


def create_plugin_file(
    filename: str,
    content: bytes,
    mimetype: Optional[str] = None,
    file_id: Optional[str] = None,
) -> dict[str, Any]:
    """Create plugin file dict from content.

    Helper for plugins that generate files as output.

    Args:
        filename: Output filename
        content: Binary content
        mimetype: MIME type (auto-detected if not provided)
        file_id: Optional file ID (generated if not provided)

    Returns:
        Plugin file dict ready for output

    Example:
        >>> # Generate CSV file in plugin
        >>> csv_content = "name,age\\nAlice,30\\nBob,25"
        >>> file_data = create_plugin_file(
        ...     filename="output.csv",
        ...     content=csv_content.encode('utf-8'),
        ...     mimetype="text/csv"
        ... )
        >>> return {"output_file": file_data}
    """
    # Auto-detect MIME type
    if mimetype is None:
        mimetype, _ = mimetypes.guess_type(filename)
        if mimetype is None:
            mimetype = "application/octet-stream"

    # Extract extension
    extension = filename.rsplit(".", 1)[1] if "." in filename else ""

    # Generate file_id if not provided
    if file_id is None:
        import uuid

        file_id = str(uuid.uuid4())

    # Encode content
    content_base64 = base64.b64encode(content).decode("ascii")

    return {
        "_type": "_plugin_file",
        "file_id": file_id,
        "filename": filename,
        "content_base64": content_base64,
        "mimetype": mimetype,
        "size": len(content),
        "extension": extension,
    }


def extract_files_from_inputs(inputs: dict[str, Any]) -> dict[str, PluginFile]:
    """Extract all plugin files from node inputs.

    Recursively searches inputs for plugin file dicts and converts them.

    Args:
        inputs: Node input dictionary

    Returns:
        Dictionary mapping input keys to PluginFile instances

    Example:
        >>> inputs = {
        ...     "document": {"_type": "_plugin_file", ...},
        ...     "other": "value"
        ... }
        >>> files = extract_files_from_inputs(inputs)
        >>> if "document" in files:
        ...     file = files["document"]
        ...     text = file.as_text()
    """
    files: dict[str, PluginFile] = {}

    def traverse(obj: Any, path: str = "") -> None:
        """Recursively find plugin files."""
        if is_plugin_file(obj):
            files[path] = PluginFile.from_dict(obj)
        elif isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                traverse(value, new_path)
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                new_path = f"{path}[{idx}]"
                traverse(item, new_path)

    traverse(inputs)
    return files


__all__ = [
    "PluginFile",
    "is_plugin_file",
    "create_plugin_file",
    "extract_files_from_inputs",
]
