import threading
from typing import Dict, List, Set, Tuple
from tracker.models.schemas import PeerInfo


class TrackerStore:
    """
    Thread-safe in-memory store for keeping track of connected peers and file availability.

    Data Structures:
    - _peers: maps peer_id -> PeerInfo
    - _file_index: maps filename -> set of peer_ids owning that file
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._peers: Dict[str, PeerInfo] = {}
        self._file_index: Dict[str, Set[str]] = {}

    def register_peer(self, peer: PeerInfo) -> int:
        """
        Registers or updates a peer in the store.
        Re-indexes the files provided by the peer.
        Returns the number of files registered for this peer.
        """
        with self._lock:
            # If peer previously registered files, clean up old file index references
            if peer.peer_id in self._peers:
                old_peer = self._peers[peer.peer_id]
                for old_file in old_peer.files:
                    if old_file in self._file_index:
                        self._file_index[old_file].discard(peer.peer_id)
                        if not self._file_index[old_file]:
                            del self._file_index[old_file]

            # Save/Update peer record
            self._peers[peer.peer_id] = peer

            # Update reverse index: filename -> set of peer_ids
            for filename in peer.files:
                if filename not in self._file_index:
                    self._file_index[filename] = set()
                self._file_index[filename].add(peer.peer_id)

            return len(peer.files)

    def get_all_peers(self) -> List[PeerInfo]:
        """Returns a list of all currently registered peers."""
        with self._lock:
            return list(self._peers.values())

    def get_peers_for_file(self, filename: str) -> List[PeerInfo]:
        """
        Returns a list of PeerInfo objects for peers holding the specified filename.
        """
        with self._lock:
            peer_ids = self._file_index.get(filename, set())
            return [self._peers[pid] for pid in peer_ids if pid in self._peers]

    def register_web_file(self, filename: str) -> None:
        """Registers a web-uploaded file under a virtual 'web_seeder' peer."""
        with self._lock:
            web_peer_id = "web_seeder_1"
            if web_peer_id not in self._peers:
                self._peers[web_peer_id] = PeerInfo(
                    peer_id=web_peer_id,
                    host="web.tracker",
                    port=8000,
                    files=[],
                )
            if filename not in self._peers[web_peer_id].files:
                self._peers[web_peer_id].files.append(filename)

            if filename not in self._file_index:
                self._file_index[filename] = set()
            self._file_index[filename].add(web_peer_id)

    def get_stats(self) -> Tuple[int, int]:
        """Returns total active peers and total tracked files."""
        with self._lock:
            return len(self._peers), len(self._file_index)



# Global singleton instance of the in-memory store
store = TrackerStore()

