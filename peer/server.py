import json
import socket
import threading
from typing import Optional
from peer.config import PeerConfig
from peer.file_manager import FileManager
from hash_manager.hash_manager import HashManager


class PeerServer:
    """Multithreaded TCP Socket Server for serving complete files or chunk ranges with SHA-256 integrity metadata."""

    def __init__(self, config: PeerConfig, file_manager: FileManager) -> None:
        self.config: PeerConfig = config
        self.file_manager: FileManager = file_manager
        self.server_socket: Optional[socket.socket] = None
        self.is_running: bool = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start TCP server in a background thread."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.config.host, self.config.port))
        self.server_socket.listen(10)
        self.is_running = True

        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print(f"[PeerServer] Listening on {self.config.host}:{self.config.port}")

    def _listen_loop(self) -> None:
        """Main listening loop for incoming client connections."""
        while self.is_running and self.server_socket:
            try:
                client_sock, client_addr = self.server_socket.accept()
                handler_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, client_addr),
                    daemon=True,
                )
                handler_thread.start()
            except OSError:
                break

    def _handle_client(self, client_sock: socket.socket, client_addr: tuple) -> None:
        """Handle client request for full file or chunk range with SHA-256 metadata."""
        try:
            client_sock.settimeout(10.0)
            request_data = b""
            while b"\n" not in request_data:
                chunk = client_sock.recv(self.config.buffer_size)
                if not chunk:
                    break
                request_data += chunk

            if not request_data:
                client_sock.close()
                return

            request_str = request_data.decode("utf-8").strip()
            request_json = json.loads(request_str)
            filename = request_json.get("filename")
            chunk_index = request_json.get("chunk_index")
            chunk_size = request_json.get("chunk_size")

            if not filename:
                response = {"status": "ERROR", "message": "Missing 'filename' parameter"}
                client_sock.sendall((json.dumps(response) + "\n").encode("utf-8"))
                client_sock.close()
                return

            file_path = self.file_manager.get_shared_file_path(filename)
            total_file_size = self.file_manager.get_file_size(filename)

            if not file_path or total_file_size is None:
                response = {"status": "ERROR", "message": f"File '{filename}' not found on peer"}
                client_sock.sendall((json.dumps(response) + "\n").encode("utf-8"))
                client_sock.close()
                return

            with open(file_path, "rb") as f:
                if chunk_index is not None and chunk_size is not None:
                    offset = chunk_index * chunk_size
                    if offset >= total_file_size:
                        response = {"status": "ERROR", "message": f"Chunk index {chunk_index} out of bounds"}
                        client_sock.sendall((json.dumps(response) + "\n").encode("utf-8"))
                        client_sock.close()
                        return

                    f.seek(offset)
                    data_to_send = f.read(chunk_size)
                    bytes_len = len(data_to_send)

                    # Compute SHA-256 hash for chunk data
                    chunk_sha256 = HashManager.calculate_bytes_hash(data_to_send)

                    response = {
                        "status": "OK",
                        "chunk_index": chunk_index,
                        "filesize": bytes_len,
                        "sha256": chunk_sha256,
                    }
                    client_sock.sendall((json.dumps(response) + "\n").encode("utf-8"))
                    client_sock.sendall(data_to_send)
                    print(f"[PeerServer] Sent chunk {chunk_index} ({bytes_len} bytes, SHA-256: {chunk_sha256[:8]}...) to {client_addr}")
                else:
                    # Serve full file
                    file_sha256 = HashManager.calculate_file_hash(file_path)
                    response = {"status": "OK", "filesize": total_file_size, "sha256": file_sha256}
                    client_sock.sendall((json.dumps(response) + "\n").encode("utf-8"))

                    while True:
                        bytes_read = f.read(self.config.buffer_size)
                        if not bytes_read:
                            break
                        client_sock.sendall(bytes_read)
                    print(f"[PeerServer] Sent full file '{filename}' ({total_file_size} bytes) to {client_addr}")

        except Exception as e:
            print(f"[PeerServer] Error handling client {client_addr}: {e}")
        finally:
            try:
                client_sock.close()
            except Exception:
                pass

    def stop(self) -> None:
        """Stop TCP server and close socket."""
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None
        print("[PeerServer] Server stopped.")
