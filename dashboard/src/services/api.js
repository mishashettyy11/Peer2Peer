const TRACKER_BASE_URL = (import.meta.env.VITE_TRACKER_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');


/**
 * Fetch operational health status and active peer/file statistics from Tracker.
 */
export async function fetchHealth() {
  try {
    const response = await fetch(`${TRACKER_BASE_URL}/health`);
    if (!response.ok) throw new Error(`HTTP error ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Tracker API Health check failed:', error);
    return { status: 'offline', active_peers: 0, tracked_files_count: 0 };
  }
}

/**
 * Fetch list of all registered peers in the P2P network.
 */
export async function fetchPeers() {
  try {
    const response = await fetch(`${TRACKER_BASE_URL}/peers`);
    if (!response.ok) throw new Error(`HTTP error ${response.status}`);
    const data = await response.json();
    return data.peers || [];
  } catch (error) {
    console.error('Tracker API Fetch Peers failed:', error);
    return [];
  }
}

/**
 * Fetch all peers hosting a specific filename.
 */
export async function fetchFilePeers(filename) {
  try {
    const response = await fetch(`${TRACKER_BASE_URL}/peers/${encodeURIComponent(filename)}`);
    if (!response.ok) throw new Error(`HTTP error ${response.status}`);
    const data = await response.json();
    return data.peers || [];
  } catch (error) {
    console.error(`Tracker API Fetch File Peers for '${filename}' failed:`, error);
    return [];
  }
}

/**
 * Upload a file to the P2P Tracker seeder via Web UI.
 */
export async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${TRACKER_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Upload failed: ${errText}`);
  }
  return await response.json();
}

/**
 * Fetch file chunking metadata and peer seeders list for parallel download.
 */
export async function fetchFileMetadata(filename) {
  const response = await fetch(`${TRACKER_BASE_URL}/files/${encodeURIComponent(filename)}/metadata`);
  if (!response.ok) throw new Error(`Failed to fetch metadata for '${filename}'`);
  return await response.json();
}

/**
 * Fetch an individual binary chunk with X-SHA256 checksum header for parallel downloading.
 */
export async function fetchFileChunk(filename, chunkIndex, chunkSize = 524288) {
  const url = `${TRACKER_BASE_URL}/files/${encodeURIComponent(filename)}/chunks/${chunkIndex}?chunk_size=${chunkSize}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Chunk ${chunkIndex} download failed`);

  const arrayBuffer = await response.arrayBuffer();
  const sha256Header = response.headers.get('X-SHA256') || response.headers.get('x-sha256');

  return {
    chunkIndex,
    data: new Uint8Array(arrayBuffer),
    sha256: sha256Header,
  };
}

/**
 * Direct file download URL helper.
 */
export function getFileDownloadUrl(filename) {
  return `${TRACKER_BASE_URL}/files/${encodeURIComponent(filename)}/download`;
}

