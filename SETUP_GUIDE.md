# 🚀 Mini P2P File Sharing System - Setup & Quickstart Guide

Welcome to the **Mini BitTorrent-like Peer-to-Peer File Sharing System**! Follow the steps below to clone, install dependencies, and run the tracker, peers, and dashboard on your machine.

---

## 📌 Repository URL
**GitHub Repository:** [https://github.com/manjunathashetty548/Peer2peer](https://github.com/manjunathashetty548/Peer2peer)

---

## 🛠️ Step 1: Clone the Repository

Open your terminal (PowerShell, Command Prompt, or Terminal) and run:

```bash
git clone https://github.com/manjunathashetty548/Peer2peer.git
cd Peer2peer
```

---

## 📦 Step 2: Install Python Dependencies

Create and activate a virtual environment, then install requirements:

### On Windows:
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### On Mac / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🌐 Step 3: Run the Tracker Server

The tracker server coordinates file availability and peer registration on `http://127.0.0.1:8000`.

In **Terminal 1**:
```bash
uvicorn tracker.main:app --reload --port 8000
```

---

## 💻 Step 4: Run Peer Nodes

You can run multiple local peer nodes on different ports.

### Start Peer 1 (Terminal 2):
```bash
python -m peer.main --port 8001 --peer-id peer_1 --shared-dir shared_files
```

### Start Peer 2 (Terminal 3):
```bash
python -m peer.main --port 8002 --peer-id peer_2 --shared-dir shared_files_2
```

---

## 📊 Step 5: Start the Visualization Dashboard (Optional)

In **Terminal 4**:
```bash
cd dashboard
npm install
npm run dev
```

Open your browser at `http://localhost:5173` to view real-time swarm activity and chunk transfer metrics!
