from typing import Dict, Any, List, Optional
import requests
from peer.config import PeerConfig


class TrackerRegistrationClient:
    """Client helper for interacting with the central Tracker server API."""

    def __init__(self, config: PeerConfig) -> None:
        self.config: PeerConfig = config
        self.tracker_url: str = config.tracker_url.rstrip("/")

    def register(self, files: List[str]) -> bool:
        """Register peer metadata and hosted file list with Tracker API.
        
        Endpoint: POST /register
        Payload: { "peer_id": str, "host": str, "port": int, "files": List[str] }
        """
        url = f"{self.tracker_url}/register"
        payload = {
            "peer_id": self.config.peer_id,
            "host": self.config.host,
            "port": self.config.port,
            "files": files,
        }
        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 201:
                return True
            print(f"[Tracker] Registration failed with status {response.status_code}: {response.text}")
            return False
        except requests.RequestException as e:
            print(f"[Tracker] Could not connect to Tracker server at {url}: {e}")
            return False

    def get_peers_for_file(self, filename: str) -> List[Dict[str, Any]]:
        """Fetch list of peers hosting a requested file from Tracker API.
        
        Endpoint: GET /peers/{filename}
        """
        url = f"{self.tracker_url}/peers/{filename}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("peers", [])
            print(f"[Tracker] Error fetching peers for file {filename}: {response.status_code}")
            return []
        except requests.RequestException as e:
            print(f"[Tracker] Connection error to Tracker: {e}")
            return []

    def list_all_peers(self) -> List[Dict[str, Any]]:
        """Fetch all registered peers in the P2P network.
        
        Endpoint: GET /peers
        """
        url = f"{self.tracker_url}/peers"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("peers", [])
            return []
        except requests.RequestException as e:
            print(f"[Tracker] Connection error to Tracker: {e}")
            return []
