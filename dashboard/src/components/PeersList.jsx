import React from 'react';
import { Server, Folder, FileText } from 'lucide-react';

export default function PeersList({ peers }) {
  return (
    <div className="glass-card" style={{ height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
        <Server color="var(--primary)" size={20} />
        <h3 style={{ fontSize: '1.15rem', fontWeight: '700' }}>Connected Peers Network</h3>
        <span className="badge badge-cyan" style={{ marginLeft: 'auto' }}>
          {peers.length} Node(s) Online
        </span>
      </div>

      {peers.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-subtle)' }}>
          <Server size={40} style={{ opacity: 0.3, marginBottom: '0.75rem' }} />
          <p>No active peers currently registered with Tracker.</p>
          <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
            Start a peer using <code>python -m peer.main --port 8001</code>
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {peers.map((peer, idx) => (
            <div
              key={idx}
              style={{
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--border-color)',
                borderRadius: '12px',
                padding: '1rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span className="status-dot" />
                  <strong style={{ fontSize: '0.95rem', color: '#a5b4fc' }}>{peer.peer_id}</strong>
                </div>
                <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
                  {peer.host}:{peer.port}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                <Folder size={14} color="var(--accent-cyan)" />
                <span>Shared Files ({peer.files ? peer.files.length : 0}):</span>
              </div>

              {peer.files && peer.files.length > 0 ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.4rem' }}>
                  {peer.files.map((file, fIdx) => (
                    <span
                      key={fIdx}
                      style={{
                        background: 'rgba(99, 102, 241, 0.1)',
                        border: '1px solid rgba(99, 102, 241, 0.2)',
                        color: '#cbd5e1',
                        padding: '0.15rem 0.5rem',
                        borderRadius: '6px',
                        fontSize: '0.75rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                      }}
                    >
                      <FileText size={12} color="var(--primary)" />
                      {file}
                    </span>
                  ))}
                </div>
              ) : (
                <p style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', fontStyle: 'italic', marginTop: '0.2rem' }}>
                  No shared files advertised
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
