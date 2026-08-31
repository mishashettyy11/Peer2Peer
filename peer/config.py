from dataclasses import dataclass
from pathlib import Path


@dataclass
class PeerConfig:
    """Configuration settings for an individual Peer node in the P2P network.
    
    Attributes:
        peer_id: Unique identifier for this peer (e.g., 'peer_8001').
        host: IP address or hostname for TCP server binding (default: '127.0.0.1').
        port: TCP port number for incoming peer connections (e.g., 8001).
        tracker_url: Base HTTP URL of the Tracker server (default: 'http://127.0.0.1:8000').
        shared_dir: Path to the local directory containing files shared by this peer.
        downloads_dir: Path to the local directory where downloaded files will be saved.
        buffer_size: Socket read/write chunk buffer size in bytes (default: 4096).
    """
    peer_id: str
    host: str = "127.0.0.1"
    port: int = 8001
    tracker_url: str = "http://127.0.0.1:8000"
    shared_dir: Path = Path("shared_files")
    downloads_dir: Path = Path("downloads")
    buffer_size: int = 4096

    def __post_init__(self) -> None:
        """Convert string paths to Path objects if necessary."""
        if isinstance(self.shared_dir, str):
            self.shared_dir = Path(self.shared_dir)
        if isinstance(self.downloads_dir, str):
            self.downloads_dir = Path(self.downloads_dir)
