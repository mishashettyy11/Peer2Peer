import React from 'react';
import { Network, RefreshCw, Activity } from 'lucide-react';

export default function Header({ isOnline, lastUpdated, onRefresh, isRefreshing }) {
  return (
    <header className="navbar">
      <div className="brand-section">
        <div className="brand-icon">
          <Network color="#ffffff" size={26} />
        </div>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '800' }}>
            Mini <span className="gradient-text">P2P Sharing System</span>
          </h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Real-Time BitTorrent Architecture Monitoring Dashboard
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        <div className={isOnline ? 'badge badge-success' : 'badge badge-danger'}>
          <span className={isOnline ? 'status-dot' : ''} />
          {isOnline ? 'Tracker Connected' : 'Tracker Disconnected'}
        </div>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            color: 'var(--text-main)',
            padding: '0.5rem 1rem',
            borderRadius: '10px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.85rem',
            fontWeight: '500',
            transition: 'all 0.2s ease',
          }}
          onMouseOver={(e) => (e.currentTarget.style.borderColor = 'var(--primary)')}
          onMouseOut={(e) => (e.currentTarget.style.borderColor = 'var(--border-color)')}
        >
          <RefreshCw size={15} className={isRefreshing ? 'spin' : ''} />
          {isRefreshing ? 'Refreshing...' : 'Refresh Network'}
        </button>
      </div>
    </header>
  );
}
