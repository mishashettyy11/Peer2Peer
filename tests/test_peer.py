import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from peer.config import PeerConfig
from peer.file_manager import FileManager
from peer.registration import TrackerRegistrationClient
from peer.server import PeerServer
from peer.client import PeerClient


class TestFileManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.shared_dir = Path(self.test_dir) / "shared"
        self.downloads_dir = Path(self.test_dir) / "downloads"
        
        self.config = PeerConfig(
            peer_id="test_peer",
            shared_dir=self.shared_dir,
            downloads_dir=self.downloads_dir,
        )
        self.file_manager = FileManager(self.config)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_ensure_directories(self):
        self.assertTrue(self.shared_dir.exists())
        self.assertTrue(self.downloads_dir.exists())

    def test_scan_and_get_shared_files(self):
        # Create sample files
        file1 = self.shared_dir / "sample1.txt"
        file2 = self.shared_dir / "sample2.bin"
        file1.write_text("Hello World")
        file2.write_bytes(b"\x00\x01\x02\x03")

        files = self.file_manager.scan_shared_files()
        self.assertEqual(files, ["sample1.txt", "sample2.bin"])
        self.assertEqual(self.file_manager.get_file_size("sample1.txt"), 11)
        self.assertEqual(self.file_manager.get_file_size("sample2.bin"), 4)

    def test_path_traversal_prevention(self):
        # Create secret file outside shared_dir
        secret_file = Path(self.test_dir) / "secret.txt"
        secret_file.write_text("Secret Data")

        # Attempt relative traversal access
        result = self.file_manager.get_shared_file_path("../secret.txt")
        # Should sanitize to basename 'secret.txt' inside shared_dir, which doesn't exist in shared_dir
        self.assertIsNone(result)

    def test_get_download_path(self):
        dest = self.file_manager.get_download_path("downloaded_movie.mp4")
        self.assertEqual(dest, self.downloads_dir / "downloaded_movie.mp4")


class TestPeerServerAndClient(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.shared_dir = Path(self.test_dir) / "shared"
        self.downloads_dir = Path(self.test_dir) / "downloads"

        self.config = PeerConfig(
            peer_id="peer_server_test",
            host="127.0.0.1",
            port=9090,  # Test socket port
            shared_dir=self.shared_dir,
            downloads_dir=self.downloads_dir,
        )
        self.file_manager = FileManager(self.config)
        self.server = PeerServer(self.config, self.file_manager)
        self.server.start()

        self.client_config = PeerConfig(
            peer_id="peer_client_test",
            host="127.0.0.1",
            port=9091,
            shared_dir=self.shared_dir,
            downloads_dir=self.downloads_dir,
        )
        self.client_file_manager = FileManager(self.client_config)
        self.client = PeerClient(self.client_config, self.client_file_manager)

    def tearDown(self):
        self.server.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_successful_file_download(self):
        # Create a dummy file in server shared directory
        filename = "test_payload.dat"
        payload_content = b"P2P Network Transfer Test Content!" * 50
        (self.shared_dir / filename).write_bytes(payload_content)

        # Execute client download from server socket
        success = self.client.download_file("127.0.0.1", 9090, filename)
        self.assertTrue(success)

        # Verify downloaded file content matches original
        downloaded_file = self.downloads_dir / filename
        self.assertTrue(downloaded_file.exists())
        self.assertEqual(downloaded_file.read_bytes(), payload_content)

    def test_download_non_existent_file(self):
        success = self.client.download_file("127.0.0.1", 9090, "non_existent.txt")
        self.assertFalse(success)
        self.assertFalse((self.downloads_dir / "non_existent.txt").exists())


class TestTrackerRegistrationClient(unittest.TestCase):
    def setUp(self):
        self.config = PeerConfig(peer_id="peer_test", port=8001)
        self.client = TrackerRegistrationClient(self.config)

    @patch("requests.post")
    def test_register_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response

        res = self.client.register(["file1.txt", "file2.pdf"])
        self.assertTrue(res)
        mock_post.assert_called_once()

    @patch("requests.get")
    def test_get_peers_for_file(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "filename": "file1.txt",
            "peer_count": 1,
            "peers": [{"peer_id": "peer_8002", "host": "127.0.0.1", "port": 8002, "files": ["file1.txt"]}],
        }
        mock_get.return_value = mock_response

        peers = self.client.get_peers_for_file("file1.txt")
        self.assertEqual(len(peers), 1)
        self.assertEqual(peers[0]["peer_id"], "peer_8002")


if __name__ == "__main__":
    unittest.main()
