import { useState } from 'react';
import { motion } from 'framer-motion';
import ScrollReveal from '../components/ScrollReveal';
import { useAuth } from '../contexts/AuthContext';
import { useDownloads } from '../contexts/DownloadContext';
import { useToast } from '../components/Toast';
import { convertBatch } from '../services/api';
import { Rocket, LogIn } from 'lucide-react';

const trendingPlaylists = [
  { title: 'Top Hits', img: 'https://images.unsplash.com/photo-1511376777868-611b54f68947?w=400' },
  { title: 'Night Vibes', img: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400' },
  { title: 'Upbeat Mix', img: 'https://images.unsplash.com/photo-1492724441997-5dc865305da7?w=400' },
  { title: 'Jazz Essentials', img: 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400' },
];

export default function Home() {
  const [urls, setUrls] = useState('');
  const [loading, setLoading] = useState(false);
  const { user, loginWithGoogle } = useAuth();
  const { jobs, addJob } = useDownloads();
  const { addToast } = useToast();

  const homeJobs = jobs.filter(j => j.source === 'home');

  const handleDownload = async () => {
    const list = urls.split('\n').map(u => u.trim()).filter(Boolean);
    if (list.length === 0) return addToast('Paste at least one YouTube URL', 'error');
    if (list.length > 10) return addToast('Maximum 10 URLs per batch', 'error');
    setLoading(true);
    try {
      const data = await convertBatch(list);
      data.jobs.forEach(j => addJob({ jobId: j.job_id, title: j.url, source: 'home', status: 'queued' }));
      addToast(`${data.jobs.length} download(s) queued!`, 'success');
      setUrls('');
    } catch (e) {
      addToast(e.message || 'Download failed', 'error');
    } finally { setLoading(false); }
  };

  return (
    <div className="page-content">
      {/* Hero */}
      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
        <h1 className="hero-title gradient-text">Find the melody<br />that moves you</h1>
        <p className="hero-subtitle">Download any song from YouTube, discover new music by mood, and let our AI DJ build your perfect playlist.</p>
      </motion.div>

      {/* Download */}
      <ScrollReveal delay={0.15}>
        <div style={{ marginTop: '2.5rem' }}>
          <div className="section-label">FREE — NO ACCOUNT NEEDED</div>
          <h2 style={{ marginBottom: '1rem' }}>Download from YouTube</h2>
          <div className="glass-card glass-card-glow">
            <textarea className="input" rows={4} placeholder="Paste YouTube links, one per line..."
              value={urls} onChange={e => setUrls(e.target.value)} />
            <button className="btn btn-primary btn-full" style={{ marginTop: 12 }}
              onClick={handleDownload} disabled={loading}>
              <Rocket size={18} /> {loading ? 'Processing...' : 'Download MP3s'}
            </button>
          </div>
        </div>
      </ScrollReveal>

      {/* Active Downloads */}
      {homeJobs.length > 0 && (
        <ScrollReveal delay={0.1}>
          <div style={{ marginTop: '1.5rem' }}>
            <h3 style={{ marginBottom: '0.8rem', fontSize: '1rem' }}>Active Downloads</h3>
            {homeJobs.map(j => (
              <div key={j.jobId} className="track-row">
                <span className={`status-dot status-dot-${j.status === 'completed' ? 'completed' : j.status === 'failed' ? 'failed' : 'processing'}`} />
                <div className="track-info">
                  <span className="track-name">{j.title}</span>
                </div>
                <span className={`badge badge-${j.status === 'completed' ? 'success' : j.status === 'failed' ? 'danger' : 'violet'}`}>
                  {j.status}
                </span>
              </div>
            ))}
          </div>
        </ScrollReveal>
      )}

      {/* Feature Comparison */}
      {!user && (
        <ScrollReveal delay={0.2}>
          <div style={{ marginTop: '3rem' }}>
            <div className="section-label">WHY SIGN IN?</div>
            <h2 style={{ marginBottom: '1rem' }}>Unlock Premium Features</h2>
            <table className="feature-table">
              <thead><tr><th>Feature</th><th>Free</th><th>Account</th></tr></thead>
              <tbody>
                <tr><td>🔗 URL → MP3 Download</td><td>✅</td><td>✅</td></tr>
                <tr><td>🔍 Music Discovery</td><td>❌</td><td>✅</td></tr>
                <tr><td>🎵 AI Playlists</td><td>❌</td><td>✅</td></tr>
                <tr><td>🤖 Chatbot DJ</td><td>❌</td><td>✅</td></tr>
                <tr><td>🎛️ Audio Editor</td><td>❌</td><td>✅</td></tr>
                <tr><td>📝 Feedback & Support</td><td>✅</td><td>✅</td></tr>
              </tbody>
            </table>
            <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={loginWithGoogle}>
              <LogIn size={18} /> Create Free Account
            </button>
          </div>
        </ScrollReveal>
      )}

      {/* Trending Playlists */}
      <ScrollReveal delay={0.25}>
        <div style={{ marginTop: '3rem' }}>
          <div className="section-label">TRENDING</div>
          <h2 style={{ marginBottom: '1rem' }}>Popular Playlists</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 16 }}>
            {trendingPlaylists.map((p, i) => (
              <ScrollReveal key={p.title} delay={0.1 * i}>
                <div className="playlist-card">
                  <img src={p.img} alt={p.title} loading="lazy" />
                  <div className="playlist-card-title">{p.title}</div>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </ScrollReveal>

      {/* Footer */}
      <hr className="divider" />
      <p style={{ textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.85rem', paddingBottom: '1rem' }}>
        Built with ♥ by Sun Leo
      </p>
    </div>
  );
}
