/* ═══════════════════════════════════════════════════════════
   SunLeo API Client — Centralized backend communication
   ═══════════════════════════════════════════════════════════ */

// ─── YTConverter (port 8000 via /api/) ───

export async function convertBatch(urls) {
  const res = await fetch('/api/convert/batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ urls }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getJobStatus(jobId) {
  const res = await fetch(`/api/status/${jobId}`);
  if (!res.ok) throw new Error(`Status check failed: ${res.status}`);
  return res.json();
}

export function getDownloadUrl(jobId) {
  return `/api/download/${jobId}`;
}

export async function editAudio(file, params) {
  const formData = new FormData();
  formData.append('file', file, 'audio.mp3');
  Object.entries(params).forEach(([k, v]) => formData.append(k, String(v)));
  const res = await fetch('/api/audio/edit', { method: 'POST', body: formData });
  if (!res.ok) throw new Error(await res.text());
  return res;
}

// ─── Recommendation Service (port 8001 via /api/recommend/) ───

export async function searchTracks(query, limit = 15) {
  const res = await fetch(`/api/recommend/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getMoodTracks(tag, limit = 20) {
  const res = await fetch(`/api/recommend/mood?tag=${encodeURIComponent(tag)}&limit=${limit}&page=0`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function resolveAndQueue(trackName, artistName, searchQuery) {
  const res = await fetch('/api/recommend/resolve-and-queue', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      track_name: trackName,
      artist_name: artistName,
      search_query: searchQuery || `${trackName} ${artistName} audio`,
    }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(data.detail || `Error ${res.status}`);
  }
  return res.json();
}

export async function getAvailableMoods() {
  const res = await fetch('/api/recommend/moods');
  if (!res.ok) return { moods: [] };
  return res.json();
}

// ─── Chatbot Service (port 8002 via /api/chat/) ───

export async function sendChatMessage(message, sessionId, userUid) {
  const res = await fetch('/api/chat/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId, user_uid: userUid }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPlaylists(uid) {
  const res = await fetch(`/api/chat/playlists/${uid}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createPlaylist(uid, name, tracks = []) {
  const res = await fetch(`/api/chat/playlists/${uid}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, tracks }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deletePlaylist(uid, pid) {
  const res = await fetch(`/api/chat/playlists/${uid}/${pid}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await res.text());
}

export async function addTracksToPlaylist(uid, pid, tracks) {
  const res = await fetch(`/api/chat/playlists/${uid}/${pid}/tracks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tracks }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function removeTrackFromPlaylist(uid, pid, idx) {
  const res = await fetch(`/api/chat/playlists/${uid}/${pid}/tracks/${idx}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await res.text());
}

export async function bulkDownloadPlaylist(uid, pid) {
  const res = await fetch(`/api/chat/playlists/${uid}/${pid}/download`, { method: 'POST' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ─── Feedback (EmailJS) ───

export async function sendFeedback({ name, email, category, rating, message }) {
  const serviceId = import.meta.env.VITE_EMAILJS_SERVICE_ID;
  const templateId = import.meta.env.VITE_EMAILJS_TEMPLATE_ID;
  const publicKey = import.meta.env.VITE_EMAILJS_PUBLIC_KEY;

  if (!serviceId || !templateId || !publicKey) {
    throw new Error('EmailJS is not configured. Set VITE_EMAILJS_SERVICE_ID, VITE_EMAILJS_TEMPLATE_ID, and VITE_EMAILJS_PUBLIC_KEY in your .env file.');
  }

  const res = await fetch('https://api.emailjs.com/api/v1.0/email/send', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      service_id: serviceId,
      template_id: templateId,
      user_id: publicKey,
      template_params: {
        from_name: name,
        reply_to: email,
        category,
        rating: `${rating}/5`,
        message,
      },
    }),
  });

  if (!res.ok) throw new Error(`EmailJS error: ${res.status}`);
  return true;
}
