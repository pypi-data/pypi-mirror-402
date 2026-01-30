"""SCANOSS SDK client using protobuf binary protocol."""

from __future__ import annotations

import struct
import subprocess
import threading
from pathlib import Path
from typing import Any

from .binary import get_binary_path
from .v1 import commands_pb2, enums_pb2


class ScanossError(Exception):
    """Exception raised for SCANOSS errors."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class Scanoss:
    """
    SCANOSS SDK client.

    This client communicates with the SCANOSS daemon process via stdin/stdout
    using length-prefixed protobuf binary protocol.

    Wire format:
        ┌──────────────────┬─────────────────────────┐
        │  4 bytes (BE)    │  N bytes                │
        │  message length  │  protobuf binary data   │
        └──────────────────┴─────────────────────────┘

    Example:
        >>> scanoss = Scanoss()
        >>> result = scanoss.scan("/path/to/project")
        >>> print(result)
        >>> scanoss.close()

    Or use as context manager:
        >>> with Scanoss() as scanoss:
        ...     result = scanoss.scan("/path/to/project")
        ...     print(result)
    """

    def __init__(self, binary_path: str | None = None):
        """
        Initialize the SCANOSS client.

        Args:
            binary_path: Optional path to the scanoss binary. If not provided,
                        the binary will be auto-detected.
        """
        self._binary_path = binary_path or get_binary_path()
        self._process: subprocess.Popen | None = None
        self._request_id = 0
        self._lock = threading.Lock()
        self._start()

    def _start(self) -> None:
        """Start the daemon process in binary mode."""
        self._process = subprocess.Popen(
            [self._binary_path, "daemon"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,  # Unbuffered for binary
        )

    def _send(self, request: commands_pb2.Request) -> commands_pb2.Response:
        """
        Send a protobuf request to the daemon and wait for response.

        Args:
            request: The protobuf request message.

        Returns:
            The protobuf response from the daemon.

        Raises:
            ScanossError: If the daemon returns an error.
            RuntimeError: If the daemon process is not running.
        """
        if self._process is None or self._process.poll() is not None:
            raise RuntimeError("Daemon process is not running")

        with self._lock:
            # Serialize request
            data = request.SerializeToString()

            # Write length prefix (4 bytes, big-endian)
            self._process.stdin.write(struct.pack(">I", len(data)))
            # Write protobuf data
            self._process.stdin.write(data)
            self._process.stdin.flush()

            # Read response length (4 bytes, big-endian)
            length_bytes = self._process.stdout.read(4)
            if len(length_bytes) < 4:
                raise RuntimeError("Daemon process closed unexpectedly")

            response_len = struct.unpack(">I", length_bytes)[0]

            # Read response data
            response_data = self._process.stdout.read(response_len)
            if len(response_data) < response_len:
                raise RuntimeError("Incomplete response from daemon")

            # Parse response
            response = commands_pb2.Response()
            response.ParseFromString(response_data)

            # Check for error
            if response.HasField("error"):
                raise ScanossError(response.error.code, response.error.message)

            return response

    def scan(
        self,
        path: str,
        format: str = "json",
        scan_type: str = "identify",
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        api_url: str | None = None,
        api_key: str | None = None,
    ) -> commands_pb2.ScanResult:
        """
        Scan files for open source matches.

        Args:
            path: Path to the file or directory to scan.
            format: Output format ("json", "spdx", "cyclonedx", "csv").
            scan_type: Type of scan ("identify", "blacklist").
            include: Glob patterns for files to include.
            exclude: Glob patterns for files to exclude.
            api_url: SCANOSS API URL (optional).
            api_key: API key (optional).

        Returns:
            ScanResult protobuf message containing matches.
        """
        self._request_id += 1

        cmd = commands_pb2.ScanCommand(
            path=str(Path(path).absolute()),
            format=self._format_to_enum(format),
            scan_type=self._scan_type_to_enum(scan_type),
            include=include or [],
            exclude=exclude or [],
        )
        if api_url:
            cmd.api_url = api_url
        if api_key:
            cmd.api_key = api_key

        request = commands_pb2.Request(id=self._request_id, scan=cmd)
        response = self._send(request)
        return response.scan

    def filter_files(
        self,
        path: str,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        skip_hidden: bool = True,
    ) -> commands_pb2.FilterFilesResult:
        """
        Filter files in a directory.

        Args:
            path: Path to the directory.
            include: Glob patterns for files to include.
            exclude: Glob patterns for files to exclude.
            skip_hidden: Whether to skip hidden files.

        Returns:
            FilterFilesResult protobuf message with file list.
        """
        self._request_id += 1

        cmd = commands_pb2.FilterFilesCommand(
            path=str(Path(path).absolute()),
            include=include or [],
            exclude=exclude or [],
            skip_hidden=skip_hidden,
        )

        request = commands_pb2.Request(id=self._request_id, filter_files=cmd)
        response = self._send(request)
        return response.filter_files

    def fingerprint(
        self,
        path: str,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> commands_pb2.FingerprintResult:
        """
        Generate WFP fingerprints for files.

        Args:
            path: Path to the file or directory.
            include: Glob patterns for files to include.
            exclude: Glob patterns for files to exclude.

        Returns:
            FingerprintResult protobuf message with WFP content.
        """
        self._request_id += 1

        cmd = commands_pb2.FingerprintCommand(
            path=str(Path(path).absolute()),
            include=include or [],
            exclude=exclude or [],
        )

        request = commands_pb2.Request(id=self._request_id, fingerprint=cmd)
        response = self._send(request)
        return response.fingerprint

    def generate_sbom(
        self,
        path: str,
        format: str = "spdx",
    ) -> commands_pb2.GenerateSbomResult:
        """
        Generate SBOM from scan results.

        Args:
            path: Path to scan results or directory.
            format: SBOM format ("spdx", "cyclonedx").

        Returns:
            GenerateSbomResult protobuf message with SBOM content.
        """
        self._request_id += 1

        cmd = commands_pb2.GenerateSbomCommand(
            input_path=str(Path(path).absolute()),
            format=self._format_to_enum(format),
        )

        request = commands_pb2.Request(id=self._request_id, generate_sbom=cmd)
        response = self._send(request)
        return response.generate_sbom

    def version(self) -> commands_pb2.VersionResult:
        """
        Get version information.

        Returns:
            VersionResult protobuf message with version info.
        """
        self._request_id += 1

        cmd = commands_pb2.VersionCommand()
        request = commands_pb2.Request(id=self._request_id, version=cmd)
        response = self._send(request)
        return response.version

    def close(self) -> None:
        """Close the daemon process."""
        if self._process is not None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

    def __enter__(self) -> "Scanoss":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def __del__(self) -> None:
        """Destructor to ensure process cleanup."""
        self.close()

    @staticmethod
    def _format_to_enum(format: str) -> int:
        """Convert format string to protobuf enum value."""
        formats = {
            "json": enums_pb2.OUTPUT_FORMAT_JSON,
            "spdx": enums_pb2.OUTPUT_FORMAT_SPDX,
            "cyclonedx": enums_pb2.OUTPUT_FORMAT_CYCLONEDX,
            "csv": enums_pb2.OUTPUT_FORMAT_CSV,
            "wfp": enums_pb2.OUTPUT_FORMAT_WFP,
        }
        return formats.get(format.lower(), enums_pb2.OUTPUT_FORMAT_JSON)

    @staticmethod
    def _scan_type_to_enum(scan_type: str) -> int:
        """Convert scan type string to protobuf enum value."""
        types = {
            "identify": enums_pb2.SCAN_TYPE_IDENTIFY,
            "blacklist": enums_pb2.SCAN_TYPE_BLACKLIST,
        }
        return types.get(scan_type.lower(), enums_pb2.SCAN_TYPE_IDENTIFY)
