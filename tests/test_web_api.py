import unittest
from fastapi.testclient import TestClient
from tracker.main import app


class TestWebAPI(unittest.TestCase):
    """Test suite for Web UI upload and chunk streaming endpoints."""

    def setUp(self):
        self.client = TestClient(app)

    def test_upload_file_and_get_metadata(self):
        filename = "test_upload_video.mp4"
        file_bytes = b"0" * (1024 * 1024 + 500)  # 1MB + 500 bytes payload

        # Upload file via POST /upload
        response = self.client.post(
            "/upload",
            files={"file": (filename, file_bytes, "video/mp4")},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["filename"], filename)

        # Get metadata via GET /files/{filename}/metadata
        meta_resp = self.client.get(f"/files/{filename}/metadata?chunk_size=524288")
        self.assertEqual(meta_resp.status_code, 200)
        meta = meta_resp.json()
        self.assertEqual(meta["filename"], filename)
        self.assertEqual(meta["total_chunks"], 3)  # 524288 * 2 + remainder
        self.assertEqual(len(meta["chunk_hashes"]), 3)

        # Download Chunk 0 via GET /files/{filename}/chunks/0
        chunk0_resp = self.client.get(f"/files/{filename}/chunks/0?chunk_size=524288")
        self.assertEqual(chunk0_resp.status_code, 200)
        self.assertEqual(len(chunk0_resp.content), 524288)
        self.assertIn("x-sha256", chunk0_resp.headers)

        # Direct Full Download via GET /files/{filename}/download
        dl_resp = self.client.get(f"/files/{filename}/download")
        self.assertEqual(dl_resp.status_code, 200)
        self.assertEqual(len(dl_resp.content), len(file_bytes))


if __name__ == "__main__":
    unittest.main()
