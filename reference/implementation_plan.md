# Technical Implementation Plan: Mini P2P File Sharing System

## Overview
This document specifies the architecture, component design, and protocol specification for a BitTorrent-inspired **Peer-to-Peer (P2P) File Sharing System** built in Python with a FastAPI central Tracker server and a React visualization dashboard.

---

## 1. Architectural Architecture & Component Layers

```
                               ┌─────────────────────────┐
                               │  Central Tracker Server │
                               │   (FastAPI on :8000)    │
                               └────────────┬────────────┘
                                            │ HTTP REST
                       ┌────────────────────┼────────────────────┐
                       │                    │                    │
                       ▼                    ▼                    ▼
             ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
             │ Peer A (:8001)   │  │ Peer B (:8002)   │  │ Peer C (:8003)   │
             │ TCP Server/Client│  │ TCP Server/Client│  │ TCP Server/Client│
             └─────────┬────────┘  └─────────┬────────┘  └─────────┬────────┘
                       │                     │                     │
                       └─────────────────────┴─────────────────────┘
                                   Peer-to-Peer TCP Sockets
                                  (Parallel Chunk Transfer)
```

### Components Summary:
1. **Tracker Server (`tracker/`)**:
   - Manages peer registrations, heartbeats, and file availability index.
   - Provides REST APIs for querying peers holding specific files or listing network peers.
   - Never handles or streams file contents.

2. **Peer Node (`peer/`)**:
   - Dual functionality: **TCP Server** (listens for chunk upload requests) and **TCP Client** (initiates parallel chunk downloads).
   - Scans shared directories, hashes local files, and advertises availability to the Tracker.

3. **Chunk Manager (`chunk_manager/`)**:
   - Handles splitting large files into fixed-size chunks (default: 1 MB).
   - Merges verified chunks into original files upon download completion.

4. **Hash Manager (`hash_manager/`)**:
   - Calculates SHA-256 digests for individual chunks and full files to guarantee end-to-end data integrity.

5. **Resume Manager (`resume_manager/`)**:
   - Maintains chunk download state checkpoints (`.resume/` files) enabling automatic download resumption after disconnects.

6. **Parallel Downloader (`peer/parallel_downloader.py`)**:
   - Multi-threaded worker pool requesting different chunks simultaneously from available seeders in the swarm.

7. **React Dashboard (`dashboard/`)**:
   - Modern web UI built with React + Vite.
   - Periodically polls Tracker REST endpoints to show live peer network, shared file explorer, and interactive parallel chunk download visualizer with SHA-256 verification status.

---

## 2. API & Data Schemas

### Tracker REST Endpoints (`http://127.0.0.1:8000`)
- `POST /register`: Register or update a peer's advertised shared files.
- `GET /peers`: List all active peers and their hosted files.
- `GET /files/{filename}/peers`: Get list of peer addresses hosting a specific file.
- `GET /health`: Health status and network totals.

### Peer Socket Protocol (TCP Protocol format)
Commands exchanged over raw TCP socket streams between peer nodes:
- `GET_CHUNK:<filename>:<chunk_index>`: Request a specific chunk.
- Server returns raw byte payload prefixed by size header and chunk SHA-256 digest.

---

## 3. Directory Structure
```
peer2peer/
├── chunk_manager/       # Chunk splitting and file merging engine
├── dashboard/           # Vite + React Dashboard UI
├── downloads/           # Saved completed downloads & temporary chunks
├── hash_manager/        # SHA-256 cryptographic verification utility
├── peer/                # Peer CLI, Client, Server, and Parallel Downloader
├── reference/           # Architectural design docs & implementation reference
├── resume_manager/      # Resumable download checkpoint state manager
├── shared_files/        # Default shared folder for Peer 1
├── shared_files_2/      # Shared folder for Peer 2
├── tracker/             # FastAPI central tracker server
├── requirements.txt     # Python dependencies
└── Readme.md            # Root context documentation
```

---

## 4. Verification & Testing Plan
- **Unit Tests (`tests/`)**: Test chunk creation, hash verification, resume state persistence, and tracker storage.
- **Integration Test**: Spin up 3 peers on separate ports, share a 1.42 GB file on Peer 8001, download in parallel using Peer 8004, verify SHA-256 hashes, and confirm merged output matches original file.
- **UI Verification**: Open `http://localhost:5173` to verify real-time polling, peer state cards, and parallel chunk visualization.
