import os
from pathlib import Path
from typing import List, Optional
from peer.config import PeerConfig


class FileManager:
    """Manages file storage, scanning, path validation, and disk I/O for a peer."""

    def __init__(self, config: PeerConfig) -> None:
        self.shared_dir: Path = config.shared_dir.resolve()
        self.downloads_dir: Path = config.downloads_dir.resolve()
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create shared and downloads directories if they do not exist."""
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

    def scan_shared_files(self) -> List[str]:
        """Scan the shared directory and return a list of hosted filenames."""
        if not self.shared_dir.exists():
            return []
        
        filenames: List[str] = []
        for entry in self.shared_dir.iterdir():
            if entry.is_file():
                filenames.append(entry.name)
        return sorted(filenames)

    def get_shared_file_path(self, filename: str) -> Optional[Path]:
        """Validate and resolve a requested filename inside the shared directory.
        
        Guards against directory traversal (e.g. '../../etc/passwd').
        Returns None if file does not exist or falls outside shared_dir.
        """
        # Strip path separators to prevent basic directory traversal
        clean_filename = os.path.basename(filename)
        target_path = (self.shared_dir / clean_filename).resolve()

        # Security check: Ensure target path is strictly within shared_dir
        try:
            target_path.relative_to(self.shared_dir)
        except ValueError:
            return None

        if target_path.is_file():
            return target_path
        return None

    def get_file_size(self, filename: str) -> Optional[int]:
        """Get byte size of a shared file."""
        file_path = self.get_shared_file_path(filename)
        if file_path and file_path.exists():
            return file_path.stat().st_size
        return None

    def get_download_path(self, filename: str) -> Path:
        """Get the absolute destination path for a downloaded file."""
        clean_filename = os.path.basename(filename)
        return self.downloads_dir / clean_filename
