import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import StatCards from './components/StatCards';
import PeersList from './components/PeersList';
import FilesExplorer from './components/FilesExplorer';
import UploadSection from './components/UploadSection';
import ParallelDownloadModal from './components/ParallelDownloadModal';
import ChunkProgressViewer from './components/ChunkProgressViewer';
import { fetchHealth, fetchPeers } from './services/api';

export default function App() {
  const [health, setHealth] = useState({ status: 'offline', active_peers: 0, tracked_files_count: 0 });
  const [peers, setPeers] = useState([]);
  const [isOnline, setIsOnline] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [activeDownloadFilename, setActiveDownloadFilename] = useState(null);

  const loadNetworkData = useCallback(async () => {
    setIsRefreshing(true);
    const healthData = await fetchHealth();
    const peersData = await fetchPeers();

    setHealth(healthData);
    setPeers(peersData);
    setIsOnline(healthData.status === 'ok');
    setLastUpdated(new Date().toLocaleTimeString());
    setIsRefreshing(false);
  }, []);

  // Poll Tracker REST API every 3 seconds for live updates
  useEffect(() => {
    loadNetworkData();

    // Auto-open download modal if friend opens a share link with ?file=filename
    const params = new URLSearchParams(window.location.search);
    const sharedFile = params.get('file');
    if (sharedFile) {
      setActiveDownloadFilename(sharedFile);
    }

    const interval = setInterval(() => {
      loadNetworkData();
    }, 3000);
    return () => clearInterval(interval);
  }, [loadNetworkData]);


  // Calculate unique files across all peers
  const uniqueFilesSet = new Set();
  peers.forEach((peer) => {
    if (peer.files) {
      peer.files.forEach((f) => uniqueFilesSet.add(f));
    }
  });

  return (
    <div className="dashboard-container">
      <Header
        isOnline={isOnline}
        lastUpdated={lastUpdated}
        onRefresh={loadNetworkData}
        isRefreshing={isRefreshing}
      />

      <StatCards
        health={health}
        totalPeers={peers.length}
        totalFiles={uniqueFilesSet.size}
      />

      <UploadSection onUploadSuccess={loadNetworkData} />

      <div className="grid-two-column">
        <PeersList peers={peers} />
        <FilesExplorer
          peers={peers}
          onStartParallelDownload={(filename) => setActiveDownloadFilename(filename)}
        />
      </div>

      <ChunkProgressViewer peers={peers} />

      {activeDownloadFilename && (
        <ParallelDownloadModal
          filename={activeDownloadFilename}
          onClose={() => setActiveDownloadFilename(null)}
        />
      )}
    </div>
  );
}

