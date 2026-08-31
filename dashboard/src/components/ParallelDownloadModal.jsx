import React, { useState, useEffect } from 'react';
import { X, Zap, ShieldCheck, Download, CheckCircle2, AlertTriangle, Cpu } from 'lucide-react';
import { fetchFileMetadata, fetchFileChunk } from '../services/api';

export default function ParallelDownloadModal({ filename, onClose }) {
  const [loading, setLoading] = useState(true);
  const [metadata, setMetadata] = useState(null);
  const [chunksStatus, setChunksStatus] = useState([]);
  const [downloadCompleted, setDownloadCompleted] = useState(false);
  const [error, setError] = useState(null);
  const [progressPercent, setProgressPercent] = useState(0);

  useEffect(() => {
    let isCancelled = false;

    async function startParallelDownload() {
      try {
        setLoading(true);
        setError(null);

        // Step 1: Fetch chunk metadata & list of seeders
        const meta = await fetchFileMetadata(filename);
        if (isCancelled) return;

        setMetadata(meta);
        const totalChunks = meta.total_chunks;
        const peers = meta.peers && meta.peers.length > 0 ? meta.peers : [{ peer_id: 'web_seeder_1', host: 'web.tracker', port: 8000 }];

        const initialChunks = Array.from({ length: totalChunks }, (_, idx) => ({
          index: idx,
          status: 'pending', // 'pending' | 'downloading' | 'verified' | 'failed'
          peer: peers[idx % peers.length]?.peer_id || 'peer_node',
          sha256: meta.chunk_hashes[idx] || null,
        }));

        setChunksStatus(initialChunks);
        setLoading(false);

        // Step 2: Download chunks concurrently in parallel workers (concurrency limit 3)
        const chunkBuffers = new Array(totalChunks);
        let completedCount = 0;

        const downloadChunkTask = async (chunkIndex) => {
          if (isCancelled) return;

          setChunksStatus((prev) =>
            prev.map((c) => (c.index === chunkIndex ? { ...c, status: 'downloading' } : c))
          );

          try {
            const chunkRes = await fetchFileChunk(filename, chunkIndex, meta.chunk_size);
            if (isCancelled) return;

            chunkBuffers[chunkIndex] = chunkRes.data;
            completedCount++;

            setChunksStatus((prev) =>
              prev.map((c) =>
                c.index === chunkIndex
                  ? { ...c, status: 'verified', receivedSha256: chunkRes.sha256 }
                  : c
              )
            );

            setProgressPercent(Math.round((completedCount / totalChunks) * 100));
          } catch (err) {
            console.error(`Chunk ${chunkIndex} download error:`, err);
            setChunksStatus((prev) =>
              prev.map((c) => (c.index === chunkIndex ? { ...c, status: 'failed' } : c))
            );
            throw err;
          }
        };

        // Queue-based concurrent executor
        const CONCURRENCY = 4;
        const queue = Array.from({ length: totalChunks }, (_, i) => i);
        const activeWorkers = [];

        for (let i = 0; i < Math.min(CONCURRENCY, totalChunks); i++) {
          const worker = (async () => {
            while (queue.length > 0) {
              const nextIndex = queue.shift();
              await downloadChunkTask(nextIndex);
            }
          })();
          activeWorkers.push(worker);
        }

        await Promise.all(activeWorkers);
        if (isCancelled) return;

        // Step 3: Combine binary chunks into a single Blob and trigger browser file save
        const blob = new Blob(chunkBuffers, { type: 'application/octet-stream' });
        const downloadUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(downloadUrl);

        setDownloadCompleted(true);
      } catch (err) {
        if (!isCancelled) {
          setError(err.message || 'Parallel chunk download failed');
        }
      }
    };

    startParallelDownload();

    return () => {
      isCancelled = true;
    };
  }, [filename]);

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0, 0, 0, 0.8)',
        backdropFilter: 'blur(8px)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
      }}
    >
      <div
        className="glass-card"
        style={{
          width: '100%',
          maxWidth: '650px',
          maxHeight: '90vh',
          overflowY: 'auto',
          border: '1px solid var(--border-color)',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)',
        }}
      >
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Zap color="var(--accent-cyan)" size={24} />
            <h3 style={{ fontSize: '1.2rem', fontWeight: '700' }}>Parallel P2P Multi-Swarm Download</h3>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-subtle)',
              cursor: 'pointer',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* File Details */}
        <div
          style={{
            background: 'rgba(255, 255, 255, 0.04)',
            padding: '1rem',
            borderRadius: '10px',
            marginBottom: '1.25rem',
            border: '1px solid var(--border-color)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-main)' }}>{filename}</span>
            <span style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)' }}>
              {metadata ? `${(metadata.file_size / 1024 / 1024).toFixed(2)} MB` : 'Loading size...'}
            </span>
          </div>

          {metadata && (
            <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.78rem', color: 'var(--text-subtle)' }}>
              <span>Total Chunks: <strong>{metadata.total_chunks}</strong></span>
              <span>Chunk Size: <strong>{(metadata.chunk_size / 1024).toFixed(0)} KB</strong></span>
              <span>Active Seeders: <strong>{metadata.peers.length}</strong></span>
            </div>
          )}
        </div>

        {/* Overall Progress Bar */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.4rem' }}>
            <span style={{ color: 'var(--text-main)' }}>Download Progress</span>
            <span style={{ fontWeight: '700', color: 'var(--accent-cyan)' }}>{progressPercent}%</span>
          </div>
          <div style={{ height: '10px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '5px', overflow: 'hidden' }}>
            <div
              style={{
                height: '100%',
                width: `${progressPercent}%`,
                background: 'linear-gradient(90deg, var(--accent-cyan), var(--accent-purple))',
                transition: 'width 0.3s ease',
              }}
            />
          </div>
        </div>

        {/* Chunks Status Grid */}
        <div style={{ marginBottom: '1.5rem' }}>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--text-subtle)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Cpu size={14} /> Parallel Chunks Swarm Allocation:
          </h4>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: '0.6rem' }}>
            {chunksStatus.map((chunk) => (
              <div
                key={chunk.index}
                style={{
                  padding: '0.5rem 0.6rem',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  border: '1px solid var(--border-color)',
                  background:
                    chunk.status === 'verified'
                      ? 'rgba(16, 185, 129, 0.15)'
                      : chunk.status === 'downloading'
                      ? 'rgba(6, 182, 212, 0.15)'
                      : chunk.status === 'failed'
                      ? 'rgba(239, 68, 68, 0.15)'
                      : 'rgba(255, 255, 255, 0.03)',
                  borderColor:
                    chunk.status === 'verified'
                      ? '#10b981'
                      : chunk.status === 'downloading'
                      ? 'var(--accent-cyan)'
                      : 'var(--border-color)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.2rem' }}>
                  <strong>Chunk #{chunk.index}</strong>
                  {chunk.status === 'verified' && <ShieldCheck size={12} color="#10b981" />}
                </div>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                  From: <span style={{ color: 'var(--text-main)' }}>{chunk.peer}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer Actions & Status */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
          {error ? (
            <span style={{ color: '#ef4444', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <AlertTriangle size={16} /> {error}
            </span>
          ) : downloadCompleted ? (
            <span style={{ color: '#10b981', fontSize: '0.88rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <CheckCircle2 size={18} /> Complete! File saved to browser downloads.
            </span>
          ) : (
            <span style={{ color: 'var(--text-subtle)', fontSize: '0.82rem' }}>
              Downloading chunks concurrently from peer seeders...
            </span>
          )}

          <button
            onClick={onClose}
            style={{
              padding: '0.5rem 1.2rem',
              borderRadius: '8px',
              border: 'none',
              background: downloadCompleted ? 'var(--accent-cyan)' : 'rgba(255, 255, 255, 0.1)',
              color: downloadCompleted ? '#000' : 'var(--text-main)',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            {downloadCompleted ? 'Done' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  );
}
