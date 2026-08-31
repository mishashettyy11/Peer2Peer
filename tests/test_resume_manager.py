import os
import shutil
import tempfile
import unittest
from pathlib import Path

from resume_manager.resume_manager import ResumeManager, DownloadProgress
from peer.config import PeerConfig
from peer.file_manager import FileManager
from peer.server import PeerServer
from peer.parallel_downloader import ParallelDownloader
from chunk_manager.chunk_manager import ChunkManager


class TestResumeManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.resume_dir = self.test_dir / ".resume"
        self.resume_manager = ResumeManager(self.resume_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_and_load_progress(self):
        filename = "test_video.mp4"
        progress = DownloadProgress(
            filename=filename,
            file_size=5000000,
            chunk_size=1000000,
            total_chunks=5,
            completed_chunks=[0, 2],
        )

        self.resume_manager.save_progress(progress)
        state_file = self.resume_dir / f"{filename}.resume.json"
        self.assertTrue(state_file.exists())

        loaded = self.resume_manager.load_progress(filename)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.filename, filename)
        self.assertEqual(loaded.file_size, 5000000)
        self.assertEqual(loaded.total_chunks, 5)
        self.assertEqual(loaded.completed_chunks, [0, 2])

    def test_record_chunk_complete(self):
        filename = "archive.zip"
        self.resume_manager.record_chunk_complete(filename, 0, 4, 4000, 1000)
        self.resume_manager.record_chunk_complete(filename, 2, 4, 4000, 1000)
        self.resume_manager.record_chunk_complete(filename, 0, 4, 4000, 1000)  # Duplicate call

        loaded = self.resume_manager.load_progress(filename)
        self.assertEqual(loaded.completed_chunks, [0, 2])

    def test_clear_progress(self):
        filename = "image.png"
        self.resume_manager.record_chunk_complete(filename, 0, 1, 100, 100)
        self.assertTrue(self.resume_manager.get_progress_file(filename).exists())

        self.resume_manager.clear_progress(filename)
        self.assertFalse(self.resume_manager.get_progress_file(filename).exists())


class TestResumedDownloadIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.shared_a = self.test_dir / "shared_a"
        self.downloads_b = self.test_dir / "downloads_b"
        self.resume_dir = self.downloads_b / ".resume"

        # Peer A Config & Server (Port 9098)
        self.config_a = PeerConfig(peer_id="peer_A", host="127.0.0.1", port=9098, shared_dir=self.shared_a, downloads_dir=self.test_dir)
        self.fm_a = FileManager(self.config_a)
        self.server_a = PeerServer(self.config_a, self.fm_a)
        self.server_a.start()

        # Peer B Config (Downloader)
        self.config_b = PeerConfig(peer_id="peer_B", host="127.0.0.1", port=9099, shared_dir=self.test_dir, downloads_dir=self.downloads_b)
        self.fm_b = FileManager(self.config_b)
        self.cm_b = ChunkManager(chunk_size=1000, chunks_dir=self.downloads_b / "chunks")
        self.rm_b = ResumeManager(self.resume_dir)
        self.downloader_b = ParallelDownloader(
            config=self.config_b,
            file_manager=self.fm_b,
            chunk_manager=self.cm_b,
            resume_manager=self.rm_b,
            max_workers=2,
        )

    def tearDown(self):
        self.server_a.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_resume_skips_already_downloaded_chunks(self):
        filename = "resumable_file.bin"
        chunk0_data = b"A" * 1000
        chunk1_data = b"B" * 1000
        chunk2_data = b"C" * 500
        full_payload = chunk0_data + chunk1_data + chunk2_data

        # Write source file on Peer A
        (self.shared_a / filename).write_bytes(full_payload)

        # Pre-populate Peer B's temp chunk directory & JSON state with chunk 0 and 1 already completed
        temp_dir = self.downloads_b / f"temp_{filename}_chunks"
        temp_dir.mkdir(parents=True, exist_ok=True)
        (temp_dir / f"{filename}.part0000").write_bytes(chunk0_data)
        (temp_dir / f"{filename}.part0001").write_bytes(chunk1_data)

        self.rm_b.record_chunk_complete(filename, 0, 3, 2500, 1000)
        self.rm_b.record_chunk_complete(filename, 1, 3, 2500, 1000)

        available_peers = [{"peer_id": "peer_A", "host": "127.0.0.1", "port": 9098}]

        # Execute parallel download - should skip chunks 0 & 1, download only chunk 2, merge, and clear state
        success = self.downloader_b.download_file_parallel(
            filename=filename,
            available_peers=available_peers,
            total_file_size=len(full_payload),
            chunk_size=1000,
        )

        self.assertTrue(success)

        # Verify output file matches original data
        reconstructed = self.downloads_b / filename
        self.assertTrue(reconstructed.exists())
        self.assertEqual(reconstructed.read_bytes(), full_payload)

        # Verify resume state file was cleared upon completion
        self.assertFalse(self.rm_b.get_progress_file(filename).exists())


if __name__ == "__main__":
    unittest.main()
