import json
import socket
from pathlib import Path
from typing import Optional, Union
from peer.config import PeerConfig
from peer.file_manager import FileManager
from hash_manager.hash_manager import HashManager


class PeerClient:
    """TCP Socket Client for downloading files or chunks with SHA-256 integrity verification."""

    def __init__(self, config: PeerConfig, file_manager: FileManager) -> None:
        self.config: PeerConfig = config
        self.file_manager: FileManager = file_manager

    def download_file(self, target_host: str, target_port: int, filename: str) -> bool:
        """Connect to remote peer socket, request full file, and save to downloads directory."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)

        try:
            print(f"[PeerClient] Connecting to peer at {target_host}:{target_port} for file '{filename}'...")
            sock.connect((target_host, target_port))

            request_payload = {"filename": filename}
            sock.sendall((json.dumps(request_payload) + "\n").encode("utf-8"))

            header_data = b""
            while b"\n" not in header_data:
                chunk = sock.recv(self.config.buffer_size)
                if not chunk:
                    break
                header_data += chunk

            if not header_data:
                print("[PeerClient] Error: Remote peer closed connection without header response.")
                return False

            header_line, leftover_bytes = header_data.split(b"\n", 1)
            response_json = json.loads(header_line.decode("utf-8"))

            if response_json.get("status") != "OK":
                print(f"[PeerClient] Download failed: {response_json.get('message', 'Unknown error')}")
                return False

            filesize = response_json.get("filesize", 0)
            expected_sha256 = response_json.get("sha256")
            dest_path = self.file_manager.get_download_path(filename)

            bytes_received = 0
            downloaded_buffer = bytearray()

            if leftover_bytes:
                downloaded_buffer.extend(leftover_bytes)
                bytes_received += len(leftover_bytes)

            while bytes_received < filesize:
                chunk = sock.recv(min(self.config.buffer_size, filesize - bytes_received))
                if not chunk:
                    break
                downloaded_buffer.extend(chunk)
                bytes_received += len(chunk)

            if bytes_received != filesize:
                print(f"[PeerClient] Incomplete file download: Received {bytes_received}/{filesize} bytes.")
                return False

            # SHA-256 Verification
            if expected_sha256:
                if not HashManager.verify_chunk(bytes(downloaded_buffer), expected_sha256):
                    print(f"[PeerClient] SHA-256 verification FAILED for file '{filename}'! Rejecting download.")
                    return False
                print(f"[PeerClient] SHA-256 verification PASSED for file '{filename}'.")

            with open(dest_path, "wb") as f:
                f.write(downloaded_buffer)

            print(f"[PeerClient] Successfully downloaded '{filename}' ({bytes_received} bytes).")
            return True

        except Exception as e:
            print(f"[PeerClient] Error downloading file: {e}")
            return False
        finally:
            sock.close()

    def download_chunk(
        self,
        target_host: str,
        target_port: int,
        filename: str,
        chunk_index: int,
        chunk_size: int,
        output_chunk_path: Union[str, Path],
    ) -> bool:
        """Connect to remote peer, request chunk, verify SHA-256 integrity, and save to output_chunk_path."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)
        output_path = Path(output_chunk_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            sock.connect((target_host, target_port))
            request_payload = {
                "filename": filename,
                "chunk_index": chunk_index,
                "chunk_size": chunk_size,
            }
            sock.sendall((json.dumps(request_payload) + "\n").encode("utf-8"))

            header_data = b""
            while b"\n" not in header_data:
                chunk = sock.recv(self.config.buffer_size)
                if not chunk:
                    break
                header_data += chunk

            if not header_data:
                return False

            header_line, leftover_bytes = header_data.split(b"\n", 1)
            response_json = json.loads(header_line.decode("utf-8"))

            if response_json.get("status") != "OK":
                print(f"[PeerClient] Chunk {chunk_index} request error: {response_json.get('message')}")
                return False

            expected_size = response_json.get("filesize", 0)
            expected_sha256 = response_json.get("sha256")
            bytes_received = 0
            chunk_buffer = bytearray()

            if leftover_bytes:
                chunk_buffer.extend(leftover_bytes)
                bytes_received += len(leftover_bytes)

            while bytes_received < expected_size:
                chunk = sock.recv(min(self.config.buffer_size, expected_size - bytes_received))
                if not chunk:
                    break
                chunk_buffer.extend(chunk)
                bytes_received += len(chunk)

            if bytes_received != expected_size:
                print(f"[PeerClient] Incomplete chunk {chunk_index}: {bytes_received}/{expected_size} bytes.")
                return False

            # Verify SHA-256 hash integrity
            if expected_sha256:
                if not HashManager.verify_chunk(bytes(chunk_buffer), expected_sha256):
                    print(f"[PeerClient] SHA-256 Verification FAILED for Chunk {chunk_index}! Expected {expected_sha256[:8]}..., got {HashManager.calculate_bytes_hash(bytes(chunk_buffer))[:8]}... Rejecting chunk.")
                    if output_path.exists():
                        output_path.unlink()
                    return False

            with open(output_path, "wb") as f:
                f.write(chunk_buffer)

            return True

        except Exception as e:
            print(f"[PeerClient] Error downloading chunk {chunk_index} from {target_host}:{target_port}: {e}")
            if output_path.exists():
                try:
                    output_path.unlink()
                except OSError:
                    pass
            return False
        finally:
            sock.close()
