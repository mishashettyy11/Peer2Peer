import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Union, Optional, Tuple
from hash_manager.hash_manager import HashManager

DEFAULT_CHUNK_SIZE: int = 1024 * 1024


@dataclass
class ChunkMetadata:
    """Dataclass holding metadata about a split file and its constituent chunks including SHA-256 hashes."""
    filename: str
    file_size: int
    chunk_size: int
    total_chunks: int
    chunk_paths: List[Path]
    chunk_hashes: List[str]


class ChunkManager:
    """Manages file chunking, ordered chunk directory storage, hash calculation, and chunk reassembly."""

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunks_dir: Union[str, Path] = Path("chunks"),
    ) -> None:
        """Purpose: Configures ChunkManager instance with configurable chunk size and working directory."""
        self.chunk_size: int = chunk_size
        self.chunks_dir: Path = Path(chunks_dir)
        self._ensure_dir(self.chunks_dir)

    def _ensure_dir(self, directory: Path) -> Path:
        """Purpose: Ensures that a specified directory path exists on disk."""
        resolved = directory.resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    def split_file(
        self,
        file_path: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Tuple[ChunkMetadata, List[Path]]:
        """Purpose: Reads an input file in binary blocks of `chunk_size`, computes SHA-256 hash for each chunk,
        saves ordered chunk files, and returns ChunkMetadata containing hashes.
        """
        source_path = Path(file_path).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        if not source_path.is_file():
            raise ValueError(f"Path is not a regular file: {source_path}")

        target_dir = self._ensure_dir(Path(output_dir)) if output_dir else self.chunks_dir
        file_size = source_path.stat().st_size

        created_chunks: List[Path] = []
        chunk_hashes: List[str] = []

        with open(source_path, "rb") as src_file:
            chunk_index = 0
            while True:
                chunk_bytes = src_file.read(self.chunk_size)
                if not chunk_bytes and chunk_index > 0:
                    break

                # Compute SHA-256 hash of this chunk
                chunk_hash = HashManager.calculate_bytes_hash(chunk_bytes)
                chunk_hashes.append(chunk_hash)

                chunk_filename = f"{source_path.name}.part{chunk_index:04d}"
                chunk_file_path = target_dir / chunk_filename

                with open(chunk_file_path, "wb") as chunk_file:
                    chunk_file.write(chunk_bytes)

                created_chunks.append(chunk_file_path)
                chunk_index += 1

                if not chunk_bytes:
                    break

        metadata = ChunkMetadata(
            filename=source_path.name,
            file_size=file_size,
            chunk_size=self.chunk_size,
            total_chunks=len(created_chunks),
            chunk_paths=created_chunks,
            chunk_hashes=chunk_hashes,
        )

        return metadata, created_chunks

    def merge_chunks(
        self,
        chunk_paths: List[Union[str, Path]],
        output_file_path: Union[str, Path],
    ) -> Path:
        """Purpose: Reassembles an ordered list of chunk files into a single destination file."""
        dest_path = Path(output_file_path).resolve()
        self._ensure_dir(dest_path.parent)

        resolved_chunks = [Path(p).resolve() for p in chunk_paths]
        for cp in resolved_chunks:
            if not cp.exists() or not cp.is_file():
                raise FileNotFoundError(f"Chunk file missing or invalid: {cp}")

        with open(dest_path, "wb") as out_file:
            for cp in resolved_chunks:
                with open(cp, "rb") as chunk_file:
                    while True:
                        buffer = chunk_file.read(64 * 1024)
                        if not buffer:
                            break
                        out_file.write(buffer)

        return dest_path

    def cleanup_chunks(self, chunk_paths: List[Union[str, Path]]) -> None:
        """Purpose: Deletes temporary chunk files from disk."""
        for p in chunk_paths:
            path_obj = Path(p).resolve()
            if path_obj.exists() and path_obj.is_file():
                try:
                    path_obj.unlink()
                except OSError as e:
                    print(f"[ChunkManager] Could not delete chunk {path_obj}: {e}")
