import os
import shutil
import tempfile
import unittest
from pathlib import Path

from peer.config import PeerConfig
from peer.file_manager import FileManager
from peer.server import PeerServer
from peer.parallel_downloader import ParallelDownloader
from chunk_manager.chunk_manager import ChunkManager


class TestParallelDownloader(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.shared_a = self.test_dir / "shared_a"
        self.shared_b = self.test_dir / "shared_b"
        self.downloads_c = self.test_dir / "downloads_c"

        # Peer A Config & Server (Port 9095)
        self.config_a = PeerConfig(peer_id="peer_A", host="127.0.0.1", port=9095, shared_dir=self.shared_a, downloads_dir=self.test_dir)
        self.fm_a = FileManager(self.config_a)
        self.server_a = PeerServer(self.config_a, self.fm_a)
        self.server_a.start()

        # Peer B Config & Server (Port 9096)
        self.config_b = PeerConfig(peer_id="peer_B", host="127.0.0.1", port=9096, shared_dir=self.shared_b, downloads_dir=self.test_dir)
        self.fm_b = FileManager(self.config_b)
        self.server_b = PeerServer(self.config_b, self.fm_b)
        self.server_b.start()

        # Peer C Config (Downloader)
        self.config_c = PeerConfig(peer_id="peer_C", host="127.0.0.1", port=9097, shared_dir=self.test_dir, downloads_dir=self.downloads_c)
        self.fm_c = FileManager(self.config_c)
        self.cm_c = ChunkManager(chunk_size=1024, chunks_dir=self.downloads_c / "chunks")
        self.downloader_c = ParallelDownloader(self.config_c, self.fm_c, self.cm_c, max_workers=4)

    def tearDown(self):
        self.server_a.stop()
        self.server_b.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_parallel_chunk_download_from_multiple_peers(self):
        filename = "shared_dataset.bin"
        # Generate 5,000 bytes test binary payload (~5 chunks with 1024 byte chunk size)
        test_payload = os.urandom(5000)

        (self.shared_a / filename).write_bytes(test_payload)
        (self.shared_b / filename).write_bytes(test_payload)

        available_peers = [
            {"peer_id": "peer_A", "host": "127.0.0.1", "port": 9095},
            {"peer_id": "peer_B", "host": "127.0.0.1", "port": 9096},
        ]

        # Execute parallel chunk download across Peer A and Peer B
        success = self.downloader_c.download_file_parallel(
            filename=filename,
            available_peers=available_peers,
            total_file_size=len(test_payload),
            chunk_size=1024,
        )

        self.assertTrue(success)

        reconstructed_file = self.downloads_c / filename
        self.assertTrue(reconstructed_file.exists())
        self.assertEqual(reconstructed_file.read_bytes(), test_payload)


if __name__ == "__main__":
    unittest.main()
