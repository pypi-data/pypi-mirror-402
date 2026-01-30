"""Archive wrapper for zcompact CLI."""

import json
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Callable

from .exceptions import ZcompactError, RecordNotFoundError, ArchiveError


def _find_zcompact() -> str:
    """Find the zcompact binary."""
    path = shutil.which("zcompact")
    if path is None:
        raise ZcompactError(
            "zcompact binary not found. Install it with: brew install zzmarks26/zcompact/zcompact"
        )
    return path


class Archive:
    """
    Python wrapper for zcompact archives.

    Example:
        # Create a new archive
        archive = Archive.create("data.jcpk", id_field="id", index_field="_domain_uuid")
        archive.import_files(["data1.json.gz", "data2.json.gz"])

        # Open existing archive
        archive = Archive("data.jcpk")

        # Query records
        record = archive.get("user-123")
        records = archive.query_index("company-uuid")
    """

    def __init__(self, path: Union[str, Path]):
        """
        Open an existing archive.

        Args:
            path: Path to the .jcpk archive file.
        """
        self.path = Path(path)
        self._bin = _find_zcompact()

        if not self.path.exists():
            raise ArchiveError(f"Archive not found: {self.path}")

    @classmethod
    def create(
        cls,
        path: Union[str, Path],
        id_field: str = "id",
        index_field: Optional[str] = None,
        compression_level: int = 3,
    ) -> "Archive":
        """
        Create a new empty archive.

        Args:
            path: Path for the new archive file.
            id_field: Field name to use as primary ID.
            index_field: Optional field name for secondary index.
            compression_level: Zstd compression level (1-22).

        Returns:
            Archive instance.
        """
        path = Path(path)
        bin_path = _find_zcompact()

        # Create with a dummy empty gzip file, then we'll use insert for records
        # Actually, we need at least one file to create. Let's create an empty temp file.
        import tempfile
        import gzip

        with tempfile.NamedTemporaryFile(suffix=".json.gz", delete=False) as tmp:
            tmp_path = tmp.name
            with gzip.open(tmp_path, 'wt') as gz:
                gz.write("")  # Empty file

        try:
            cmd = [bin_path, "create", str(path), tmp_path, "--id-field", id_field]
            if index_field:
                cmd.extend(["--index-field", index_field])
            cmd.extend(["--compression", str(compression_level)])

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise ArchiveError(f"Failed to create archive: {result.stderr}")
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        archive = cls(path)
        archive._id_field = id_field
        archive._index_field = index_field
        return archive

    @classmethod
    def create_from_files(
        cls,
        path: Union[str, Path],
        files: List[Union[str, Path]],
        id_field: str = "id",
        index_field: Optional[str] = None,
        compression_level: int = 3,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> "Archive":
        """
        Create an archive from gzip NDJSON files.

        Args:
            path: Path for the new archive file.
            files: List of .json.gz files to import.
            id_field: Field name to use as primary ID.
            index_field: Optional field name for secondary index.
            compression_level: Zstd compression level (1-22).
            progress_callback: Optional callback for progress updates.

        Returns:
            Archive instance.
        """
        path = Path(path)
        bin_path = _find_zcompact()

        cmd = [bin_path, "create", str(path)]
        cmd.extend([str(f) for f in files])
        cmd.extend(["--id-field", id_field])
        if index_field:
            cmd.extend(["--index-field", index_field])
        cmd.extend(["--compression", str(compression_level)])
        cmd.append("--verbose")

        if progress_callback:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            for line in process.stderr:
                progress_callback(line.strip())
            process.wait()
            if process.returncode != 0:
                raise ArchiveError(f"Failed to create archive")
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise ArchiveError(f"Failed to create archive: {result.stderr}")

        archive = cls(path)
        archive._id_field = id_field
        archive._index_field = index_field
        return archive

    def get(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a record by primary ID.

        Args:
            record_id: The record's primary ID.

        Returns:
            Record as a dictionary, or None if not found.
        """
        result = subprocess.run(
            [self._bin, "get", str(self.path), record_id],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            if "not found" in result.stderr.lower():
                return None
            raise ArchiveError(f"Failed to get record: {result.stderr}")

        return json.loads(result.stdout.strip())

    def get_or_raise(self, record_id: str) -> Dict[str, Any]:
        """
        Get a record by primary ID, raising if not found.

        Args:
            record_id: The record's primary ID.

        Returns:
            Record as a dictionary.

        Raises:
            RecordNotFoundError: If record is not found.
        """
        record = self.get(record_id)
        if record is None:
            raise RecordNotFoundError(f"Record not found: {record_id}")
        return record

    def search(self, prefix: str, limit: int = 0) -> List[str]:
        """
        Search for record IDs by prefix.

        Args:
            prefix: ID prefix to search for.
            limit: Maximum number of results (0 = unlimited).

        Returns:
            List of matching record IDs.
        """
        cmd = [self._bin, "search", str(self.path), "--prefix", prefix]
        if limit > 0:
            cmd.extend(["--limit", str(limit)])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            if "No records found" in result.stderr:
                return []
            raise ArchiveError(f"Search failed: {result.stderr}")

        output = result.stdout.strip()
        if not output:
            return []
        return output.split("\n")

    def query_index(self, index_value: str, limit: int = 0) -> List[Dict[str, Any]]:
        """
        Query records by secondary index value.

        Args:
            index_value: The secondary index value to query.
            limit: Maximum number of results (0 = unlimited).

        Returns:
            List of matching records as dictionaries.
        """
        cmd = [self._bin, "query-index", str(self.path), index_value]
        if limit > 0:
            cmd.extend(["--limit", str(limit)])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            if "No records found" in result.stderr:
                return []
            if "no secondary index" in result.stderr.lower():
                raise ArchiveError("Archive has no secondary index")
            raise ArchiveError(f"Query failed: {result.stderr}")

        output = result.stdout.strip()
        if not output:
            return []

        return [json.loads(line) for line in output.split("\n") if line]

    def insert(self, record_id: str, record: Union[Dict[str, Any], str]) -> None:
        """
        Insert a new record.

        Args:
            record_id: The record's primary ID.
            record: Record as a dictionary or JSON string.
        """
        if isinstance(record, dict):
            record = json.dumps(record)

        result = subprocess.run(
            [self._bin, "insert", str(self.path), record_id, record],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise ArchiveError(f"Failed to insert record: {result.stderr}")

    def update(self, record_id: str, record: Union[Dict[str, Any], str]) -> None:
        """
        Update an existing record.

        Args:
            record_id: The record's primary ID.
            record: Record as a dictionary or JSON string.
        """
        if isinstance(record, dict):
            record = json.dumps(record)

        result = subprocess.run(
            [self._bin, "update", str(self.path), record_id, record],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise ArchiveError(f"Failed to update record: {result.stderr}")

    def delete(self, record_id: str) -> None:
        """
        Delete a record.

        Args:
            record_id: The record's primary ID.
        """
        result = subprocess.run(
            [self._bin, "delete", str(self.path), record_id],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            if "not found" in result.stderr.lower():
                raise RecordNotFoundError(f"Record not found: {record_id}")
            raise ArchiveError(f"Failed to delete record: {result.stderr}")

    def compact(self) -> None:
        """Compact the archive to remove deleted records and reclaim space."""
        result = subprocess.run(
            [self._bin, "compact", str(self.path)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise ArchiveError(f"Failed to compact archive: {result.stderr}")

    def stats(self) -> Dict[str, Any]:
        """
        Get archive statistics.

        Returns:
            Dictionary with archive stats.
        """
        result = subprocess.run(
            [self._bin, "stats", str(self.path)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise ArchiveError(f"Failed to get stats: {result.stderr}")

        # Parse the stats output
        stats = {}
        for line in result.stdout.strip().split("\n"):
            if ":" in line and not line.startswith("Archive:"):
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()

                # Try to convert to appropriate type
                if value.endswith(" bytes"):
                    value = int(value.replace(" bytes", ""))
                elif value.endswith("x"):
                    value = float(value.replace("x", ""))
                elif value.isdigit():
                    value = int(value)

                stats[key] = value

        return stats

    def import_files(
        self,
        files: List[Union[str, Path]],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Import additional .gz NDJSON files into the archive.

        Note: This creates a new archive with the combined data.

        Args:
            files: List of .json.gz files to import.
            progress_callback: Optional callback for progress updates.
        """
        # Get current stats to find id_field and index_field
        current_stats = self.stats()
        index_field = current_stats.get("secondary_index_field")

        # For now, we need to recreate. Get all existing data + new files.
        # This is a limitation of the CLI - in the future we could add
        # an "import" command that appends to existing archive.
        raise NotImplementedError(
            "Importing into existing archive not yet supported. "
            "Use Archive.create_from_files() instead."
        )

    def __repr__(self) -> str:
        return f"Archive({self.path!r})"
