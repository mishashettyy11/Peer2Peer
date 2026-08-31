import json
import threading
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Union, Set


@dataclass
class DownloadProgress:
    """Dataclass holding JSON-serializable download state metadata."""
    filename: str
    file_size: int
    chunk_size: int
    total_chunks: int
    completed_chunks: List[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DownloadProgress":
        return cls(
            filename=data["filename"],
            file_size=data["file_size"],
            chunk_size=data["chunk_size"],
            total_chunks=data["total_chunks"],
            completed_chunks=list(set(data.get("completed_chunks", []))),
        )


class ResumeManager:
    """Manages saving, loading, tracking, and clearing download progress state using JSON files."""

    def __init__(self, resume_dir: Union[str, Path] = Path(".resume")) -> None:
        """Purpose: Configures ResumeManager working directory and ensures directory exists."""
        self.resume_dir: Path = Path(resume_dir).resolve()
        self.resume_dir.mkdir(parents=True, exist_ok=True)
        self._lock: threading.Lock = threading.Lock()

    def get_progress_file(self, filename: str) -> Path:
        """Purpose: Returns path to the JSON state file for a given filename."""
        clean_name = Path(filename).name
        return self.resume_dir / f"{clean_name}.resume.json"

    def load_progress(self, filename: str) -> Optional[DownloadProgress]:
        """Purpose: Reads and parses JSON progress file if it exists on disk."""
        state_file = self.get_progress_file(filename)
        if not state_file.exists():
            return None

        with self._lock:
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return DownloadProgress.from_dict(data)
            except Exception as e:
                print(f"[ResumeManager] Error loading progress for '{filename}': {e}")
                return None

    def save_progress(self, progress: DownloadProgress) -> None:
        """Purpose: Serializes DownloadProgress object to JSON file on disk."""
        state_file = self.get_progress_file(progress.filename)
        with self._lock:
            try:
                # Deduplicate and sort chunk indices
                progress.completed_chunks = sorted(list(set(progress.completed_chunks)))
                with open(state_file, "w", encoding="utf-8") as f:
                    json.dump(progress.to_dict(), f, indent=2)
            except Exception as e:
                print(f"[ResumeManager] Error saving progress for '{progress.filename}': {e}")

    def record_chunk_complete(
        self,
        filename: str,
        chunk_index: int,
        total_chunks: int,
        file_size: int,
        chunk_size: int,
    ) -> DownloadProgress:
        """Purpose: Records a completed chunk index and updates JSON state file."""
        progress = self.load_progress(filename)
        if progress is None:
            progress = DownloadProgress(
                filename=filename,
                file_size=file_size,
                chunk_size=chunk_size,
                total_chunks=total_chunks,
                completed_chunks=[],
            )

        if chunk_index not in progress.completed_chunks:
            progress.completed_chunks.append(chunk_index)

        self.save_progress(progress)
        return progress

    def is_chunk_completed(self, filename: str, chunk_index: int) -> bool:
        """Purpose: Checks if a chunk index is listed in the saved JSON progress state."""
        progress = self.load_progress(filename)
        if progress and chunk_index in progress.completed_chunks:
            return True
        return False

    def clear_progress(self, filename: str) -> None:
        """Purpose: Deletes JSON state file upon successful file download completion and merging."""
        state_file = self.get_progress_file(filename)
        with self._lock:
            if state_file.exists():
                try:
                    state_file.unlink()
                    print(f"[ResumeManager] Cleared resume state file for '{filename}'.")
                except OSError as e:
                    print(f"[ResumeManager] Could not remove state file '{state_file}': {e}")
