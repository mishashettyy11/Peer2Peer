import unittest
from fastapi.testclient import TestClient
from tracker.main import app
from tracker.storage.memory_store import store


class TestTrackerAPI(unittest.TestCase):
    def setUp(self):
        # Reset store before each test
        store._peers.clear()
        store._file_index.clear()
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["active_peers"], 0)
        self.assertEqual(data["tracked_files_count"], 0)

    def test_register_peer(self):
        payload = {
            "peer_id": "peer_8001",
            "host": "127.0.0.1",
            "port": 8001,
            "files": ["ubuntu.iso", "movie.mp4"],
        }
        response = self.client.post("/register", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["registered_files_count"], 2)

    def test_list_peers(self):
        # Register Peer A
        self.client.post(
            "/register",
            json={"peer_id": "peer_A", "host": "127.0.0.1", "port": 8001, "files": ["doc.pdf"]},
        )
        # Register Peer B
        self.client.post(
            "/register",
            json={"peer_id": "peer_B", "host": "127.0.0.1", "port": 8002, "files": ["doc.pdf", "image.png"]},
        )

        response = self.client.get("/peers")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_peers"], 2)

    def test_get_peers_for_file(self):
        self.client.post(
            "/register",
            json={"peer_id": "peer_A", "host": "127.0.0.1", "port": 8001, "files": ["shared.txt"]},
        )
        self.client.post(
            "/register",
            json={"peer_id": "peer_B", "host": "127.0.0.1", "port": 8002, "files": ["other.txt"]},
        )

        response = self.client.get("/peers/shared.txt")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["filename"], "shared.txt")
        self.assertEqual(data["peer_count"], 1)
        self.assertEqual(data["peers"][0]["peer_id"], "peer_A")


if __name__ == "__main__":
    unittest.main()
