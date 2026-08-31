import React, { useState, useRef } from 'react';
import { UploadCloud, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { uploadFile } from '../services/api';

export default function UploadSection({ onUploadSuccess }) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = async (files) => {
    if (!files || files.length === 0) return;
    const file = files[0];

    setUploading(true);
    setStatusMsg(null);

    try {
      const res = await uploadFile(file);
      setStatusMsg({ type: 'success', text: `Uploaded '${file.name}' (${(file.size / 1024 / 1024).toFixed(2)} MB) to P2P network!` });
      if (onUploadSuccess) onUploadSuccess();
    } catch (err) {
      console.error(err);
      setStatusMsg({ type: 'error', text: err.message || 'Upload failed' });
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  return (
    <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem' }}>
        <UploadCloud color="var(--accent-purple)" size={22} />
        <h3 style={{ fontSize: '1.15rem', fontWeight: '700' }}>Share File with P2P Swarm</h3>
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${isDragging ? 'var(--accent-cyan)' : 'rgba(255, 255, 255, 0.15)'}`,
          borderRadius: '12px',
          padding: '2rem 1.5rem',
          textAlign: 'center',
          background: isDragging ? 'rgba(6, 182, 212, 0.08)' : 'rgba(255, 255, 255, 0.02)',
          cursor: 'pointer',
          transition: 'all 0.2s ease-in-out',
        }}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => handleFileSelect(e.target.files)}
          style={{ display: 'none' }}
        />

        {uploading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.6rem' }}>
            <Loader2 size={32} color="var(--accent-cyan)" className="spin-animation" />
            <p style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>Seeding file to P2P network...</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
            <UploadCloud size={40} color={isDragging ? 'var(--accent-cyan)' : 'var(--text-subtle)'} />
            <p style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-main)' }}>
              Drag & Drop your movie or file here, or <span style={{ color: 'var(--accent-cyan)' }}>Browse</span>
            </p>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Supports video (MP4/MKV), documents, images, zip files up to 500 MB+
            </span>
          </div>
        )}
      </div>

      {statusMsg && (
        <div
          style={{
            marginTop: '0.85rem',
            padding: '0.6rem 0.9rem',
            borderRadius: '8px',
            fontSize: '0.82rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: statusMsg.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            color: statusMsg.type === 'success' ? '#10b981' : '#ef4444',
            border: `1px solid ${statusMsg.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
          }}
        >
          {statusMsg.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          <span>{statusMsg.text}</span>
        </div>
      )}
    </div>
  );
}
