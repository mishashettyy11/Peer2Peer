import React from 'react';
import { Users, HardDrive, Cpu, ShieldCheck } from 'lucide-react';

export default function StatCards({ health, totalPeers, totalFiles }) {
  const cards = [
    {
      title: 'Active Connected Peers',
      value: totalPeers,
      subtitle: 'Live registered P2P nodes',
      icon: Users,
      color: '#6366f1',
    },
    {
      title: 'Tracked Shared Files',
      value: totalFiles,
      subtitle: 'Unique files across swarm',
      icon: HardDrive,
      color: '#06b6d4',
    },
    {
      title: 'Tracker Status',
      value: health.status === 'ok' ? 'Operational' : 'Offline',
      subtitle: 'HTTP REST Directory Service',
      icon: Cpu,
      color: health.status === 'ok' ? '#10b981' : '#ef4444',
    },
    {
      title: 'Protocol & Verification',
      value: 'TCP + SHA-256',
      subtitle: 'Chunking, Resume & Integrity',
      icon: ShieldCheck,
      color: '#8b5cf6',
    },
  ];

  return (
    <div className="grid-stats">
      {cards.map((card, index) => {
        const IconComponent = card.icon;
        return (
          <div key={index} className="glass-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: '500' }}>
                  {card.title}
                </p>
                <h2 style={{ fontSize: '1.8rem', fontWeight: '800', margin: '0.3rem 0', color: 'var(--text-main)' }}>
                  {card.value}
                </h2>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
                  {card.subtitle}
                </p>
              </div>
              <div
                style={{
                  background: `${card.color}15`,
                  border: `1px solid ${card.color}30`,
                  padding: '0.75rem',
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <IconComponent size={22} color={card.color} />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
