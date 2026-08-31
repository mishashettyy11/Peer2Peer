import os
import shutil
import tempfile
import unittest
from pathlib import Path
from chunk_manager.chunk_manager import ChunkManager, ChunkMetadata


class TestChunkManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.chunks_dir = self.test_dir / "chunks"
        self.chunk_manager = ChunkManager(
            chunk_size=1024,  # Use 1 KB chunk size for fast unit testing
            chunks_dir=self.chunks_dir,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_split_and_merge_small_file(self):
        # Create a small file (500 bytes < 1024 byte chunk size)
        source_file = self.test_dir / "small.txt"
        data = b"Hello P2P Chunking World! " * 20  # ~520 bytes
        source_file.write_bytes(data)

        # Split file
        metadata, chunk_paths = self.chunk_manager.split_file(source_file)
        self.assertEqual(metadata.total_chunks, 1)
        self.assertEqual(len(chunk_paths), 1)
        self.assertTrue(chunk_paths[0].exists())

        # Merge file
        merged_file = self.test_dir / "small_merged.txt"
        reconstructed = self.chunk_manager.merge_chunks(chunk_paths, merged_file)
        self.assertTrue(reconstructed.exists())
        self.assertEqual(reconstructed.read_bytes(), data)

    def test_split_and_merge_multi_chunk_file(self):
        # Create a file spanning multiple chunks (2500 bytes with 1000 byte chunk size -> 3 chunks)
        custom_manager = ChunkManager(chunk_size=1000, chunks_dir=self.chunks_dir)
        source_file = self.test_dir / "payload.bin"
        data = os.urandom(2500)
        source_file.write_bytes(data)

        metadata, chunk_paths = custom_manager.split_file(source_file)
        self.assertEqual(metadata.total_chunks, 3)
        self.assertEqual(len(chunk_paths), 3)

        # Check chunk sizes: 1000, 1000, 500 bytes
        self.assertEqual(chunk_paths[0].stat().st_size, 1000)
        self.assertEqual(chunk_paths[1].stat().st_size, 1000)
        self.assertEqual(chunk_paths[2].stat().st_size, 500)

        # Merge and assert byte-for-byte exact match
        merged_file = self.test_dir / "payload_reconstructed.bin"
        custom_manager.merge_chunks(chunk_paths, merged_file)
        self.assertEqual(merged_file.read_bytes(), data)

    def test_cleanup_chunks(self):
        source_file = self.test_dir / "data.txt"
        source_file.write_bytes(b"A" * 3000)

        metadata, chunk_paths = self.chunk_manager.split_file(source_file)
        for cp in chunk_paths:
            self.assertTrue(cp.exists())

        self.chunk_manager.cleanup_chunks(chunk_paths)
        for cp in chunk_paths:
            self.assertFalse(cp.exists())

    def test_empty_file_chunking(self):
        empty_file = self.test_dir / "empty.txt"
        empty_file.write_bytes(b"")

        metadata, chunk_paths = self.chunk_manager.split_file(empty_file)
        self.assertEqual(metadata.file_size, 0)
        self.assertEqual(len(chunk_paths), 1)

        merged_empty = self.test_dir / "empty_merged.txt"
        self.chunk_manager.merge_chunks(chunk_paths, merged_empty)
        self.assertEqual(merged_empty.read_bytes(), b"")


if __name__ == "__main__":
    unittest.main()
