import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path
from hash_manager.hash_manager import HashManager


class TestHashManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_calculate_bytes_hash(self):
        data = b"Hello BitTorrent P2P World"
        expected = hashlib.sha256(data).hexdigest()
        calculated = HashManager.calculate_bytes_hash(data)
        self.assertEqual(calculated, expected)

    def test_calculate_file_hash(self):
        test_file = self.test_dir / "sample.txt"
        data = b"Sample text for file hashing test."
        test_file.write_bytes(data)

        expected = hashlib.sha256(data).hexdigest()
        calculated = HashManager.calculate_file_hash(test_file)
        self.assertEqual(calculated, expected)

    def test_calculate_chunk_hashes(self):
        test_file = self.test_dir / "multi_chunk.bin"
        chunk1 = b"A" * 100
        chunk2 = b"B" * 100
        chunk3 = b"C" * 50
        test_file.write_bytes(chunk1 + chunk2 + chunk3)

        hashes = HashManager.calculate_chunk_hashes(test_file, chunk_size=100)
        self.assertEqual(len(hashes), 3)
        self.assertEqual(hashes[0], hashlib.sha256(chunk1).hexdigest())
        self.assertEqual(hashes[1], hashlib.sha256(chunk2).hexdigest())
        self.assertEqual(hashes[2], hashlib.sha256(chunk3).hexdigest())

    def test_verify_chunk_success_and_failure(self):
        valid_data = b"Valid Payload Bytes"
        valid_hash = hashlib.sha256(valid_data).hexdigest()

        # Valid payload must pass verification
        self.assertTrue(HashManager.verify_chunk(valid_data, valid_hash))

        # Corrupted payload must fail verification
        corrupted_data = b"Corrupted Payload Bytes"
        self.assertFalse(HashManager.verify_chunk(corrupted_data, valid_hash))


if __name__ == "__main__":
    unittest.main()
