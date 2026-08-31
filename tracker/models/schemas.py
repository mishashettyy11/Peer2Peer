from typing import List
from pydantic import BaseModel, Field


class RegisterPeerRequest(BaseModel):
    """Request payload sent by a peer to register with the tracker server."""
    peer_id: str = Field(..., description="Unique identifier for the peer (e.g. 'peer_8001')")
    host: str = Field(..., description="IP address or hostname where peer listens (e.g. '127.0.0.1')")
    port: int = Field(..., description="Port number where peer listens for incoming requests (e.g. 8001)")
    files: List[str] = Field(default_factory=list, description="List of filenames currently hosted by this peer")


class PeerInfo(BaseModel):
    """Public details of a registered peer."""
    peer_id: str
    host: str
    port: int
    files: List[str]


class RegisterPeerResponse(BaseModel):
    """Response returned after successful peer registration."""
    status: str = "success"
    message: str
    peer_id: str
    registered_files_count: int


class PeersListResponse(BaseModel):
    """Response for listing all registered peers."""
    total_peers: int
    peers: List[PeerInfo]


class FilePeersResponse(BaseModel):
    """Response containing peers that possess a requested file."""
    filename: str
    peer_count: int
    peers: List[PeerInfo]


class HealthResponse(BaseModel):
    """Tracker server health status."""
    status: str = "ok"
    active_peers: int
    tracked_files_count: int
