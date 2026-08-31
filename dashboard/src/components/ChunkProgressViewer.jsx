import React, { useState, useEffect } from 'react';
import { Layers, Play, CheckCircle2, ShieldCheck, RefreshCw, Zap } from 'lucide-react';

export default function ChunkProgressViewer({ peers }) {
  const [selectedFile, setSelectedFile] = useState('linux_distro.iso');
  const [totalChunks, setTotalChunks] = useState(16);
  const [chunkStates, setChunkStates] = useState([]);
  const [isSimulating, setIsSimulating] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);

  // Initialize simulated chunk array
  useEffect(() => {
    resetChunks(totalChunks);
  }, [totalChunks]);

  const resetChunks = (count) => {
    const initial = Array.from({ length: count }, (_, i) => ({
      id: i,
      status: 'pending', // 'pending', 'downloading', 'verified', 'error'
      peer: null,
      sha256: null,
    }));
    setChunkStates(initial);
    setProgressPercent(0);
    setIsSimulating(false);
  };

  const startParallelDownloadSimulation = () => {
    if (isSimulating) return;
    setIsSimulating(true);

    const peerNames = peers.length > 0 ? peers.map((p) => p.peer_id) : ['peer_8001', 'peer_8002'];

    let currentChunk = 0;
    const interval = setInterval(() => {
      setChunkStates((prev) => {
        const next = [...prev];
        if (currentChunk < next.length) {
          // Mark current chunk as verified
          const peer = peerNames[currentChunk % peerNames.length];
          next[currentChunk] = {
            ...next[currentChunk],
            status: 'verified',
            peer: peer,
            sha256: Math.random().toString(36).substring(2, 10) + '...',
          };
          currentChunk++;
        }
        return next;
      });

      setProgressPercent((prev) => {
        const nextPct = Math.min(100, Math.round(((currentChunk + 1) / totalChunks) * 100));
        if (currentChunk >= totalChunks) {
          clearInterval(interval);
          setIsSimulating(false);
        }
        return nextPct;
      });
    }, 400);
  };

  const verifiedCount = chunkStates.filter((c) => c.status === 'verified').length;

  return (
    <div className="glass-card" style={{ marginTop: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ background: 'rgba(139, 92, 246, 0.15)', padding: '0.5rem', borderRadius: '10px' }}>
            <Layers color="var(--accent-violet)" size={22} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: '700' }}>Parallel Chunk Transfer & SHA-256 Visualizer</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Simulate and monitor chunk allocation, parallel downloading, and cryptographic integrity checks
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            onClick={startParallelDownloadSimulation}
            disabled={isSimulating || verifiedCount === totalChunks}
            style={{
              background: isSimulating ? 'var(--bg-card)' : 'linear-gradient(135deg, var(--primary), var(--accent-violet))',
              border: 'none',
              color: '#ffffff',
              padding: '0.55rem 1.2rem',
              borderRadius: '10px',
              fontWeight: '600',
              fontSize: '0.85rem',
              cursor: isSimulating ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              boxShadow: '0 4px 15px rgba(99, 102, 241, 0.3)',
            }}
          >
            <Zap size={16} />
            {isSimulating ? 'Downloading Chunks...' : verifiedCount === totalChunks ? 'Transfer Complete' : 'Simulate Parallel Download'}
          </button>

          <button
            onClick={() => resetChunks(totalChunks)}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-muted)',
              padding: '0.55rem 0.8rem',
              borderRadius: '10px',
              cursor: 'pointer',
            }}
            title="Reset Simulation"
          >
            <RefreshCw size={15} />
          </button>
        </div>
      </div>

      {/* Progress Bar Header */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
          <span style={{ color: 'var(--text-muted)', fontWeight: '500' }}>
            Transfer Status: <strong style={{ color: 'var(--text-main)' }}>{verifiedCount} / {totalChunks} Chunks Verified</strong>
          </span>
          <span style={{ fontWeight: '700', color: 'var(--accent-cyan)' }}>{progressPercent}% Complete</span>
        </div>

        <div style={{ width: '100%', height: '10px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '5px', overflow: 'hidden' }}>
          <div
            style={{
              width: `${progressPercent}%`,
              height: '100%',
              background: 'linear-gradient(90deg, var(--accent-cyan), var(--primary), var(--success))',
              borderRadius: '5px',
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      </div>

      {/* Chunk Block Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(65px, 1fr))',
          gap: '0.6rem',
          padding: '1rem',
          background: 'rgba(0, 0, 0, 0.2)',
          borderRadius: '12px',
          border: '1px solid var(--border-color)',
        }}
      >
        {chunkStates.map((chunk) => {
          const isVerified = chunk.status === 'verified';
          return (
            <div
              key={chunk.id}
              style={{
                background: isVerified
                  ? 'rgba(16, 185, 129, 0.15)'
                  : 'rgba(255, 255, 255, 0.04)',
                border: isVerified
                  ? '1px solid rgba(16, 185, 129, 0.4)'
                  : '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '0.5rem',
                textAlign: 'center',
                transition: 'all 0.25s ease',
              }}
            >
              <div style={{ fontSize: '0.75rem', fontWeight: '700', color: isVerified ? '#34d399' : 'var(--text-subtle)' }}>
                #{chunk.id}
              </div>
              {isVerified ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.2rem', marginTop: '0.2rem' }}>
                  <ShieldCheck size={14} color="#10b981" />
                  <span style={{ fontSize: '0.65rem', color: '#a5b4fc' }}>{chunk.peer}</span>
                </div>
              ) : (
                <div style={{ fontSize: '0.65rem', color: 'var(--text-subtle)', marginTop: '0.4rem' }}>
                  Pending
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
