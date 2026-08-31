import math
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from tracker.models.schemas import (
    RegisterPeerRequest,
    RegisterPeerResponse,
    PeerInfo,
    PeersListResponse,
    FilePeersResponse,
    HealthResponse,
)
from tracker.storage.memory_store import TrackerStore, store
from hash_manager.hash_manager import HashManager

UPLOAD_DIR = Path("uploaded_files")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_WEB_CHUNK_SIZE = 524288  # 512 KB per chunk for smooth web streaming


class TrackerService:
    """
    Business logic layer for tracker operations.
    Acts as an intermediary between controller routes, file storage, and state storage.
    """

    def __init__(self, data_store: TrackerStore = store) -> None:
        self.store = data_store

    def register_peer(self, request: RegisterPeerRequest) -> RegisterPeerResponse:
        """Processes registration for a new or existing peer."""
        peer_info = PeerInfo(
            peer_id=request.peer_id,
            host=request.host,
            port=request.port,
            files=request.files,
        )
        files_count = self.store.register_peer(peer_info)
        return RegisterPeerResponse(
            status="success",
            message=f"Peer '{request.peer_id}' registered successfully.",
            peer_id=request.peer_id,
            registered_files_count=files_count,
        )

    def list_peers(self) -> PeersListResponse:
        """Retrieves all registered peers."""
        peers = self.store.get_all_peers()
        return PeersListResponse(
            total_peers=len(peers),
            peers=peers,
        )

    def get_peers_for_file(self, filename: str) -> FilePeersResponse:
        """Finds peers hosting a given filename."""
        peers = self.store.get_peers_for_file(filename)
        return FilePeersResponse(
            filename=filename,
            peer_count=len(peers),
            peers=peers,
        )

    def check_health(self) -> HealthResponse:
        """Returns tracker status metrics."""
        active_peers, tracked_files = self.store.get_stats()
        return HealthResponse(
            status="ok",
            active_peers=active_peers,
            tracked_files_count=tracked_files,
        )

    def save_uploaded_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Saves a file uploaded via Web UI and registers it in the tracker store."""
        file_path = UPLOAD_DIR / filename
        with open(file_path, "wb") as f:
            f.write(content)

        self.store.register_web_file(filename)
        sha256 = HashManager.calculate_bytes_hash(content)

        return {
            "status": "success",
            "filename": filename,
            "size": len(content),
            "sha256": sha256,
            "message": f"File '{filename}' uploaded successfully.",
        }

    def get_file_path(self, filename: str) -> Optional[Path]:
        """Returns Path of an uploaded file if present."""
        path = UPLOAD_DIR / filename
        if path.exists() and path.is_file():
            return path
        # Fallback to shared_files directory if present
        fallback = Path("shared_files") / filename
        if fallback.exists() and fallback.is_file():
            return fallback
        return None

    def get_chunk_metadata(self, filename: str, chunk_size: int = DEFAULT_WEB_CHUNK_SIZE) -> Optional[Dict[str, Any]]:
        """Returns chunk count, chunk size, total size, and individual chunk SHA-256 hashes for a file."""
        path = self.get_file_path(filename)
        if not path:
            return None

        file_size = path.stat().st_size
        hashes = HashManager.calculate_chunk_hashes(path, chunk_size=chunk_size)
        total_chunks = len(hashes)

        peers = [p.model_dump() for p in self.store.get_peers_for_file(filename)]
        if not peers:
            peers = [{"peer_id": "web_seeder_1", "host": "web.tracker", "port": 8000, "files": [filename]}]

        return {
            "filename": filename,
            "file_size": file_size,
            "chunk_size": chunk_size,
            "total_chunks": total_chunks,
            "chunk_hashes": hashes,
            "peers": peers,
        }

    def get_file_chunk(self, filename: str, chunk_index: int, chunk_size: int = DEFAULT_WEB_CHUNK_SIZE) -> Optional[Tuple[bytes, str]]:
        """Returns chunk raw bytes and SHA-256 hash for a specific chunk index."""
        path = self.get_file_path(filename)
        if not path:
            return None

        file_size = path.stat().st_size
        offset = chunk_index * chunk_size
        if offset >= file_size and file_size > 0:
            return None

        with open(path, "rb") as f:
            f.seek(offset)
            chunk_bytes = f.read(chunk_size)

        sha256 = HashManager.calculate_bytes_hash(chunk_bytes)
        return chunk_bytes, sha256

