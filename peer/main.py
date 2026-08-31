import argparse
import sys
from pathlib import Path
from peer.config import PeerConfig
from peer.file_manager import FileManager
from peer.registration import TrackerRegistrationClient
from peer.server import PeerServer
from peer.client import PeerClient
from peer.parallel_downloader import ParallelDownloader
from chunk_manager.chunk_manager import ChunkManager, DEFAULT_CHUNK_SIZE
from resume_manager.resume_manager import ResumeManager


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P2P Peer Node CLI with Parallel Downloader and Resume Manager")
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port for peer TCP server to listen on (default: 8001)",
    )
    parser.add_argument(
        "--peer-id",
        type=str,
        default="",
        help="Unique peer identifier (default: auto-generated peer_<port>)",
    )
    parser.add_argument(
        "--tracker-url",
        type=str,
        default="http://127.0.0.1:8000",
        help="Base URL of central Tracker server (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--shared-dir",
        type=str,
        default="shared_files",
        help="Directory containing files to share (default: shared_files)",
    )
    parser.add_argument(
        "--downloads-dir",
        type=str,
        default="downloads",
        help="Directory to save downloaded files (default: downloads)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help="Chunk size in bytes (default: 1048576 = 1MB)",
    )
    return parser.parse_args()


def interactive_cli(
    config: PeerConfig,
    file_manager: FileManager,
    tracker_client: TrackerRegistrationClient,
    peer_client: PeerClient,
    parallel_downloader: ParallelDownloader,
) -> None:
    """CLI interactive loop for peer user commands."""
    print("\n--- Peer Interactive Console ---")
    print("Commands:")
    print("  1. list        - List all registered peers in network")
    print("  2. search      - Find peers holding a specific file")
    print("  3. download    - Download file from a remote peer (Single Peer)")
    print("  4. pdownload   - Download file in parallel from multiple peers (Supports Resume)")
    print("  5. files       - List local shared files")
    print("  6. exit        - Stop peer and exit")

    while True:
        try:
            cmd = input(f"\n[{config.peer_id}] Enter command (1-6): ").strip().lower()
            if cmd in ("1", "list"):
                peers = tracker_client.list_all_peers()
                print(f"\n--- Registered Peers ({len(peers)}) ---")
                for p in peers:
                    print(f"  • {p.get('peer_id')} at {p.get('host')}:{p.get('port')} - Files: {p.get('files')}")

            elif cmd in ("2", "search"):
                filename = input("Enter filename to search: ").strip()
                if filename:
                    peers = tracker_client.get_peers_for_file(filename)
                    print(f"\n--- Peers hosting '{filename}' ({len(peers)}) ---")
                    for p in peers:
                        print(f"  • {p.get('peer_id')} ({p.get('host')}:{p.get('port')})")

            elif cmd in ("3", "download"):
                filename = input("Enter filename to download: ").strip()
                if not filename:
                    continue

                peers = tracker_client.get_peers_for_file(filename)
                if not peers:
                    print(f"[CLI] No active peers found hosting '{filename}'.")
                    continue

                available_peers = [p for p in peers if p.get("peer_id") != config.peer_id]
                if not available_peers:
                    print(f"[CLI] You are the only peer hosting '{filename}'.")
                    continue

                print("\nAvailable Peer Sources:")
                for i, p in enumerate(available_peers, 1):
                    print(f"  [{i}] {p.get('peer_id')} ({p.get('host')}:{p.get('port')})")

                choice_str = input(f"Select peer [1-{len(available_peers)}]: ").strip()
                try:
                    choice = int(choice_str) - 1
                    if 0 <= choice < len(available_peers):
                        target = available_peers[choice]
                        success = peer_client.download_file(
                            target_host=target["host"],
                            target_port=target["port"],
                            filename=filename,
                        )
                        if success:
                            updated_files = file_manager.scan_shared_files()
                            tracker_client.register(updated_files)
                    else:
                        print("Invalid selection.")
                except ValueError:
                    print("Invalid input integer.")

            elif cmd in ("4", "pdownload", "parallel"):
                filename = input("Enter filename to download in parallel: ").strip()
                if not filename:
                    continue

                peers = tracker_client.get_peers_for_file(filename)
                available_peers = [p for p in peers if p.get("peer_id") != config.peer_id]

                if not available_peers:
                    print(f"[CLI] No external peers found hosting '{filename}'.")
                    continue

                size_str = input("Enter total file size in bytes (or press Enter if unknown, default 1000000): ").strip()
                total_size = int(size_str) if size_str.isdigit() else 1000000

                success = parallel_downloader.download_file_parallel(
                    filename=filename,
                    available_peers=available_peers,
                    total_file_size=total_size,
                    chunk_size=config.buffer_size * 256,
                )
                if success:
                    updated_files = file_manager.scan_shared_files()
                    tracker_client.register(updated_files)

            elif cmd in ("5", "files"):
                shared = file_manager.scan_shared_files()
                print(f"\n--- Local Shared Files ({len(shared)}) ---")
                for f in shared:
                    sz = file_manager.get_file_size(f)
                    print(f"  • {f} ({sz} bytes)")

            elif cmd in ("6", "exit", "quit"):
                print("Exiting Peer application...")
                break

            else:
                print("Unknown command. Options: list, search, download, pdownload, files, exit")

        except KeyboardInterrupt:
            print("\nShutting down peer...")
            break


def main() -> None:
    args = parse_args()
    peer_id = args.peer_id if args.peer_id else f"peer_{args.port}"

    config = PeerConfig(
        peer_id=peer_id,
        host="127.0.0.1",
        port=args.port,
        tracker_url=args.tracker_url,
        shared_dir=Path(args.shared_dir),
        downloads_dir=Path(args.downloads_dir),
        buffer_size=4096,
    )

    file_manager = FileManager(config)
    chunk_manager = ChunkManager(chunk_size=args.chunk_size, chunks_dir=config.downloads_dir / "chunks")
    resume_manager = ResumeManager(resume_dir=config.downloads_dir / ".resume")
    tracker_client = TrackerRegistrationClient(config)

    shared_files = file_manager.scan_shared_files()
    print(f"[{config.peer_id}] Initialized with shared dir '{config.shared_dir}' and downloads dir '{config.downloads_dir}'")
    print(f"[{config.peer_id}] Found {len(shared_files)} shared file(s): {shared_files}")

    registered = tracker_client.register(shared_files)
    if registered:
        print(f"[{config.peer_id}] Successfully registered with Tracker at {config.tracker_url}")
    else:
        print(f"[{config.peer_id}] Warning: Tracker registration failed.")

    peer_server = PeerServer(config, file_manager)
    peer_server.start()

    peer_client = PeerClient(config, file_manager)
    parallel_downloader = ParallelDownloader(
        config=config,
        file_manager=file_manager,
        chunk_manager=chunk_manager,
        resume_manager=resume_manager,
    )

    try:
        interactive_cli(config, file_manager, tracker_client, peer_client, parallel_downloader)
    finally:
        peer_server.stop()


if __name__ == "__main__":
    main()
