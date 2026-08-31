import math
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any, Optional

from peer.config import PeerConfig
from peer.file_manager import FileManager
from peer.client import PeerClient
from chunk_manager.chunk_manager import ChunkManager, DEFAULT_CHUNK_SIZE
from resume_manager.resume_manager import ResumeManager


class ParallelDownloader:
    """Orchestrates parallel downloading of file chunks with SHA-256 verification and resume download capability."""

    def __init__(
        self,
        config: PeerConfig,
        file_manager: FileManager,
        chunk_manager: ChunkManager,
        resume_manager: Optional[ResumeManager] = None,
        max_workers: int = 5,
        max_retries: int = 3,
    ) -> None:
        """Purpose: Initializes ParallelDownloader with config, file manager, chunk manager, resume manager, and worker limit."""
        self.config: PeerConfig = config
        self.file_manager: FileManager = file_manager
        self.chunk_manager: ChunkManager = chunk_manager
        self.resume_manager: ResumeManager = (
            resume_manager if resume_manager else ResumeManager(config.downloads_dir / ".resume")
        )
        self.max_workers: int = max_workers
        self.max_retries: int = max_retries
        self.peer_client: PeerClient = PeerClient(config, file_manager)

    def _download_chunk_with_retry(
        self,
        filename: str,
        chunk_index: int,
        chunk_size: int,
        total_chunks: int,
        total_file_size: int,
        output_chunk_path: Path,
        available_peers: List[Dict[str, Any]],
    ) -> bool:
        """Purpose: Downloads chunk with SHA-256 verification and records completed chunk to JSON progress state."""
        for attempt in range(1, self.max_retries + 1):
            peer = available_peers[(chunk_index + attempt - 1) % len(available_peers)]
            target_host = peer["host"]
            target_port = peer["port"]

            print(f"[ParallelDownloader] Attempt {attempt}/{self.max_retries} for Chunk {chunk_index} from {target_host}:{target_port}...")
            success = self.peer_client.download_chunk(
                target_host=target_host,
                target_port=target_port,
                filename=filename,
                chunk_index=chunk_index,
                chunk_size=chunk_size,
                output_chunk_path=output_chunk_path,
            )

            if success:
                print(f"[ParallelDownloader] Chunk {chunk_index} downloaded and verified (SHA-256 OK).")
                # Record chunk completion in JSON state file
                self.resume_manager.record_chunk_complete(
                    filename=filename,
                    chunk_index=chunk_index,
                    total_chunks=total_chunks,
                    file_size=total_file_size,
                    chunk_size=chunk_size,
                )
                return True
            else:
                print(f"[ParallelDownloader] Chunk {chunk_index} download failed on attempt {attempt}. Retrying...")

        print(f"[ParallelDownloader] ERROR: Chunk {chunk_index} failed all {self.max_retries} retry attempts.")
        return False

    def download_file_parallel(
        self,
        filename: str,
        available_peers: List[Dict[str, Any]],
        total_file_size: int,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> bool:
        """Purpose: Downloads missing chunks concurrently, skips previously downloaded chunks using ResumeManager,
        verifies SHA-256 integrity, merges chunks, and clears JSON progress state.
        """
        if not available_peers:
            print("[ParallelDownloader] Error: No available peers provided.")
            return False

        total_chunks = max(1, math.ceil(total_file_size / chunk_size)) if total_file_size > 0 else 1
        print(f"[ParallelDownloader] Starting parallel verified download for '{filename}' ({total_file_size} bytes, {total_chunks} chunk(s)) across {len(available_peers)} peer(s).")

        # Load existing JSON download progress state
        progress_state = self.resume_manager.load_progress(filename)
        completed_set = set(progress_state.completed_chunks) if progress_state else set()

        temp_chunks_dir = self.config.downloads_dir / f"temp_{filename}_chunks"
        temp_chunks_dir.mkdir(parents=True, exist_ok=True)

        chunk_paths: List[Path] = []
        chunks_to_download: List[int] = []

        for chunk_idx in range(total_chunks):
            chunk_filename = f"{filename}.part{chunk_idx:04d}"
            chunk_out_path = temp_chunks_dir / chunk_filename
            chunk_paths.append(chunk_out_path)

            # Resume check: Skip chunk if recorded completed AND file exists on disk
            if chunk_idx in completed_set and chunk_out_path.exists() and chunk_out_path.stat().st_size > 0:
                print(f"[ParallelDownloader] Resuming: Chunk {chunk_idx} already downloaded & verified. Skipping.")
            else:
                chunks_to_download.append(chunk_idx)

        print(f"[ParallelDownloader] Resume Status: {len(chunk_paths) - len(chunks_to_download)}/{len(chunk_paths)} chunk(s) already exist. {len(chunks_to_download)} chunk(s) remaining to download.")

        download_failed = False
        if chunks_to_download:
            workers_count = min(self.max_workers, len(chunks_to_download))
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers_count) as executor:
                future_to_chunk = {}
                for chunk_idx in chunks_to_download:
                    chunk_out_path = chunk_paths[chunk_idx]
                    future = executor.submit(
                        self._download_chunk_with_retry,
                        filename=filename,
                        chunk_index=chunk_idx,
                        chunk_size=chunk_size,
                        total_chunks=total_chunks,
                        total_file_size=total_file_size,
                        output_chunk_path=chunk_out_path,
                        available_peers=available_peers,
                    )
                    future_to_chunk[future] = chunk_idx

                for future in concurrent.futures.as_completed(future_to_chunk):
                    chunk_idx = future_to_chunk[future]
                    try:
                        success = future.result()
                        if not success:
                            download_failed = True
                    except Exception as exc:
                        print(f"[ParallelDownloader] Chunk {chunk_idx} exception: {exc}")
                        download_failed = True

        if download_failed:
            print(f"[ParallelDownloader] Download interrupted. Progress saved in JSON state file. You can resume anytime.")
            return False

        # All chunks ready -> merge into destination file
        final_download_path = self.file_manager.get_download_path(filename)
        print(f"[ParallelDownloader] All {total_chunks} chunk(s) ready. Merging into '{final_download_path}'...")

        try:
            self.chunk_manager.merge_chunks(chunk_paths, final_download_path)
            print(f"[ParallelDownloader] File '{filename}' successfully merged at '{final_download_path}'.")
            
            # Cleanup temporary chunks and clear JSON progress state file
            self.chunk_manager.cleanup_chunks(chunk_paths)
            self.resume_manager.clear_progress(filename)

            if temp_chunks_dir.exists():
                try:
                    temp_chunks_dir.rmdir()
                except OSError:
                    pass
            return True
        except Exception as e:
            print(f"[ParallelDownloader] Error merging chunks for '{filename}': {e}")
            return False
