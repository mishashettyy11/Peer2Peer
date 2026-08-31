import React, { useState } from 'react';
import { HardDrive, Search, Users, FileText, Zap, Share2, Check } from 'lucide-react';

export default function FilesExplorer({ peers, onStartParallelDownload }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [copiedFile, setCopiedFile] = useState(null);

  // Consolidate unique files and their hosting peers
  const fileMap = {};
  peers.forEach((peer) => {
    if (peer.files) {
      peer.files.forEach((filename) => {
        if (!fileMap[filename]) {
          fileMap[filename] = [];
        }
        fileMap[filename].push(peer);
      });
    }
  });

  const fileEntries = Object.entries(fileMap).filter(([filename]) =>
    filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCopyShareLink = (filename) => {
    const shareUrl = `${window.location.origin}/?file=${encodeURIComponent(filename)}`;
    navigator.clipboard.writeText(shareUrl);
    setCopiedFile(filename);
    setTimeout(() => setCopiedFile(null), 2500);
  };

  return (
    <div className="glass-card" style={{ height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <HardDrive color="var(--accent-cyan)" size={20} />
          <h3 style={{ fontSize: '1.15rem', fontWeight: '700' }}>Network Shared Files</h3>
        </div>

        <div style={{ position: 'relative', width: '220px' }}>
          <Search size={14} color="var(--text-subtle)" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            placeholder="Search files..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-main)',
              padding: '0.4rem 0.6rem 0.4rem 2rem',
              borderRadius: '8px',
              fontSize: '0.8rem',
              outline: 'none',
            }}
          />
        </div>
      </div>

      {fileEntries.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-subtle)' }}>
          <FileText size={40} style={{ opacity: 0.3, marginBottom: '0.75rem' }} />
          <p>No shared files found across connected peers.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {fileEntries.map(([filename, hostPeers], idx) => (
            <div
              key={idx}
              style={{
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--border-color)',
                borderRadius: '10px',
                padding: '0.85rem 1rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '0.75rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <div style={{ background: 'rgba(6, 182, 212, 0.15)', padding: '0.4rem', borderRadius: '8px' }}>
                  <FileText size={18} color="var(--accent-cyan)" />
                </div>
                <div>
                  <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>{filename}</strong>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Available on {hostPeers.length} peer node(s)
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{ display: 'flex', gap: '0.3rem' }}>
                  {hostPeers.map((p, pIdx) => (
                    <span
                      key={pIdx}
                      className="badge badge-cyan"
                      title={`Listening on ${p.host}:${p.port}`}
                      style={{ fontSize: '0.7rem' }}
                    >
                      <Users size={10} />
                      {p.peer_id}
                    </span>
                  ))}
                </div>

                <button
                  onClick={() => handleCopyShareLink(filename)}
                  style={{
                    background: 'rgba(255, 255, 255, 0.08)',
                    border: '1px solid var(--border-color)',
                    color: copiedFile === filename ? '#10b981' : 'var(--text-main)',
                    fontWeight: '600',
                    fontSize: '0.78rem',
                    padding: '0.45rem 0.7rem',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    transition: 'all 0.2s ease',
                  }}
                  title="Copy share link for a friend"
                >
                  {copiedFile === filename ? <Check size={13} color="#10b981" /> : <Share2 size={13} />}
                  {copiedFile === filename ? 'Link Copied!' : 'Share Link'}
                </button>

                <button
                  onClick={() => onStartParallelDownload && onStartParallelDownload(filename)}
                  style={{
                    background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-purple))',
                    border: 'none',
                    color: '#000',
                    fontWeight: '700',
                    fontSize: '0.78rem',
                    padding: '0.45rem 0.85rem',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    boxShadow: '0 4px 12px rgba(6, 182, 212, 0.25)',
                    transition: 'transform 0.15s ease',
                  }}
                >
                  <Zap size={13} /> Download (Parallel P2P)
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


