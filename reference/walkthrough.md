# System Walkthrough & User Guide: Mini P2P File Sharing System

This walkthrough provides step-by-step instructions to run, operate, and visualize the **Mini Peer-to-Peer (P2P) File Sharing System**.

---

## 🚀 1. How to Start the Application

### Step 1: Start the Central Tracker Server
Open a terminal in the project root directory and run:
```powershell
uvicorn tracker.main:app --reload --port 8000
```
* **Tracker Endpoint**: `http://127.0.0.1:8000`
* **Swagger API Docs**: `http://127.0.0.1:8000/docs`

---

### Step 2: Start Peer Nodes (Seeders & Downloaders)

Open separate terminal windows for each peer node:

#### Peer 1 (Seeder hosting original files):
```powershell
python -m peer.main --port 8001 --shared-dir shared_files
```
*(Peer 8001 scans `shared_files/` and registers hosted files like your movie file with the Tracker.)*

#### Peer 2 (Downloader / Seeder):
```powershell
python -m peer.main --port 8003 --shared-dir shared_files_3
```

#### Peer 3 (Downloader using `downloads` folder):
```powershell
python -m peer.main --port 8004 --shared-dir downloads
```

---

### Step 3: Launch the React Visualization Dashboard
In a terminal inside the `dashboard/` directory (or project root):
```powershell
cd dashboard
npm run dev
```
Open your browser and navigate to:
👉 **[http://localhost:5173](http://localhost:5173)**

---

## 🎬 2. Step-by-Step File Download Walkthrough

### Downloading a File via Parallel Multi-Chunk Downloader (CLI):

1. Go to the terminal window of **`peer_8004`**.
2. Enter command **`4`** (or **`pdownload`**).
3. When prompted for the filename, enter the exact file name:
   ```text
   [MM]- Bougainvillea (2024)[Tamil - 720p HQ HDRip - x264 - [D.mkv
   ```
4. When prompted for total file size in bytes:
   * Enter: **`1523850897`** (or press Enter if downloading small files).
5. Watch the parallel downloader stream chunks simultaneously across active peers (`peer_8001`, `peer_8003`, etc.).
6. Upon completion:
   * **Verification**: Each chunk SHA-256 digest is validated.
   * **Merge**: Chunks are assembled into `downloads/` directory.
   * **Cleanup**: Temporary chunk files are automatically cleared.

---

## 📊 3. React Dashboard Guide

1. **Active Connected Peers**: Displays live connected nodes (`peer_8001`, `peer_8003`, `peer_8004`) and their host IP/ports.
2. **Network Shared Files**: Displays all files indexed across the swarm and highlights how many peers are currently seeding each file (`Available on 2 peer node(s)`).
3. **Parallel Chunk & SHA-256 Visualizer**:
   * Click **`⚡ Simulate Parallel Download`** at the bottom right.
   * Watch the visualizer allocate chunk requests across active online peers (`peer_8001`, `peer_8003`, `peer_8004`) with green SHA-256 verified badges!

---

## 📁 4. Key Directory Reference

* 📁 **[shared_files](file:///c:/Users/91636/OneDrive/Desktop/peer2peer/shared_files)**: Default directory for Peer 8001 hosting files.
* 📁 **[downloads](file:///c:/Users/91636/OneDrive/Desktop/peer2peer/downloads)**: Directory where completed downloaded files are saved.
* 📁 **[reference](file:///c:/Users/91636/OneDrive/Desktop/peer2peer/reference)**: Contains documentation, implementation plans, and walkthrough guides.
