import hmac
import hashlib
from pathlib import Path
from typing import List, Union


class HashManager:
    """Provides cryptographic SHA-256 hashing and integrity verification for file chunks."""

    @staticmethod
    def calculate_bytes_hash(data: bytes) -> str:
        """Purpose: Calculates SHA-256 hexadecimal digest for raw byte data in memory."""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def calculate_file_hash(file_path: Union[str, Path]) -> str:
        """Purpose: Reads a file from disk in 64 KB blocks and computes its overall SHA-256 digest."""
        path_obj = Path(file_path).resolve()
        if not path_obj.exists() or not path_obj.is_file():
            raise FileNotFoundError(f"File not found for hashing: {path_obj}")

        sha256_hash = hashlib.sha256()
        with open(path_obj, "rb") as f:
            while True:
                buffer = f.read(64 * 1024)
                if not buffer:
                    break
                sha256_hash.update(buffer)
        return sha256_hash.hexdigest()

    @staticmethod
    def calculate_chunk_hashes(
        file_path: Union[str, Path],
        chunk_size: int,
    ) -> List[str]:
        """Purpose: Reads a file in `chunk_size` blocks and returns an ordered list of SHA-256 hashes
        corresponding to each chunk.
        """
        path_obj = Path(file_path).resolve()
        if not path_obj.exists() or not path_obj.is_file():
            raise FileNotFoundError(f"File not found for chunk hashing: {path_obj}")

        hashes: List[str] = []
        with open(path_obj, "rb") as f:
            while True:
                chunk_bytes = f.read(chunk_size)
                if not chunk_bytes and len(hashes) > 0:
                    break
                hashes.append(hashlib.sha256(chunk_bytes).hexdigest())
                if not chunk_bytes:
                    break
        return hashes

    @staticmethod
    def verify_chunk(data: bytes, expected_hash: str) -> bool:
        """Purpose: Calculates SHA-256 hash of `data` and verifies it against `expected_hash`.
        Returns True if hash matches; False if data is corrupted or tampered with.
        """
        actual_hash = hashlib.sha256(data).hexdigest()
        # Secure constant-time comparison to prevent timing attacks
        return hmac.compare_digest(actual_hash.lower(), expected_hash.lower())
