import AuthGate from '../components/AuthGate';
import { useDownloads } from '../contexts/DownloadContext';
import { usePlayer } from '../contexts/PlayerContext';
import { useToast } from '../components/Toast';
import { getDownloadUrl } from '../services/api';
import { Play, Download, Scissors, Check, X, Loader } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

const sourceLabels = {
  home: '🏠 From Home', discovery: '🔍 From Discovery',
  chatbot: '🤖 From Chatbot', playlist: '📋 From Playlists',
};

const fmt = (s) => { if (!s || isNaN(s)) return ''; return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`; };

export default function Downloads() {
  const { jobs } = useDownloads();
  const { playTrack } = usePlayer();
  const { addToast } = useToast();
  const navigate = useNavigate();

  const grouped = {};
  jobs.forEach(j => { const s = j.source || 'home'; if (!grouped[s]) grouped[s] = []; grouped[s].push(j); });

  const handlePlay = (job) => {
    playTrack({ title: job.title, url: getDownloadUrl(job.jobId), artist: job.metadata?.uploader || '' });
    addToast(`Now playing: ${job.title}`, 'info');
  };

  const handleSave = (job) => {
    const a = document.createElement('a');
    a.href = getDownloadUrl(job.jobId);
    a.download = `${job.title || 'track'}.mp3`;
    a.click();
  };

  return (
    <AuthGate pageName="Downloads" pageIcon="⬇️">
      <div className="page-content">
        <h1 className="hero-title gradient-text">⬇️ Downloads</h1>
        <p className="hero-subtitle">All your session downloads in one place. Files available for 1 hour.</p>
        <hr className="divider" />

        {jobs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📭</div>
            <div className="empty-state-title">No downloads yet</div>
            <div className="empty-state-text">Download music from Home, Discovery, or the DJ Chatbot</div>
          </div>
        ) : (
          <>
            {Object.entries(sourceLabels).map(([key, label]) => {
              const group = grouped[key];
              if (!group || group.length === 0) return null;
              return (
                <div key={key}>
                  <h3 style={{ margin: '1.5rem 0 0.8rem', fontSize: '1rem' }}>{label}</h3>
                  {group.map(job => (
                    <motion.div key={job.jobId} className="track-row"
                      initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.25 }}>
                      {/* Status Icon */}
                      <div style={{ width: 24, display: 'flex', justifyContent: 'center' }}>
                        {job.status === 'completed' ? <Check size={18} style={{ color: 'var(--color-success)' }} /> :
                         job.status === 'failed' ? <X size={18} style={{ color: 'var(--color-danger)' }} /> :
                         <div className="spinner" />}
                      </div>
                      {/* Track Info */}
                      <div className="track-info">
                        <span className="track-name">{job.title}</span>
                        <span className="track-artist">
                          {job.metadata?.uploader || ''}
                          {job.metadata?.duration && ` · ${fmt(job.metadata.duration)}`}
                        </span>
                      </div>
                      {/* Badge */}
                      <span className={`badge ${job.status === 'completed' ? 'badge-success' : job.status === 'failed' ? 'badge-danger' : 'badge-violet'}`}>
                        {job.status}
                      </span>
                      {/* Actions */}
                      {job.status === 'completed' && (
                        <div className="track-actions">
                          <button className="btn btn-icon btn-ghost" onClick={() => handlePlay(job)} title="Play"><Play size={16} /></button>
                          <button className="btn btn-icon btn-ghost" onClick={() => handleSave(job)} title="Save"><Download size={16} /></button>
                          <button className="btn btn-icon btn-ghost" onClick={() => navigate(`/editor?job=${job.jobId}`)} title="Edit"><Scissors size={16} /></button>
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              );
            })}
            <hr className="divider" />
            <p style={{ textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.82rem' }}>
              {jobs.length} download(s) · Files auto-delete after 1 hour
            </p>
          </>
        )}
      </div>
    </AuthGate>
  );
}
