import { useState, useEffect, useRef } from 'react';
import AuthGate from '../components/AuthGate';
import ScrollReveal from '../components/ScrollReveal';
import { TrackSkeleton } from '../components/Skeleton';
import { useDownloads } from '../contexts/DownloadContext';
import { useToast } from '../components/Toast';
import { searchTracks, getMoodTracks, resolveAndQueue } from '../services/api';
import { Search, Download, RefreshCw } from 'lucide-react';

const moods = [
  { label: '😌 Chill', tag: 'chill' }, { label: '🏋️ Workout', tag: 'workout' },
  { label: '😢 Sad', tag: 'sad' }, { label: '😄 Happy', tag: 'happy' },
  { label: '🎯 Focus', tag: 'focus' }, { label: '🎉 Party', tag: 'party' },
  { label: '💤 Sleep', tag: 'sleep' }, { label: '🚗 Road Trip', tag: 'road trip' },
  { label: '📚 Study', tag: 'study' }, { label: '🎸 Indie', tag: 'indie' },
  { label: '🎹 Lo-fi', tag: 'lo-fi' }, { label: '🎷 Jazz', tag: 'jazz' },
];

const fmtDur = (ms) => ms ? `${Math.floor(ms / 60000)}:${String(Math.floor((ms % 60000) / 1000)).padStart(2, '0')}` : '';

export default function Discovery() {
  const [activeTab, setActiveTab] = useState('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [moodResults, setMoodResults] = useState([]);
  const [selectedMood, setSelectedMood] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const { addJob } = useDownloads();
  const { addToast } = useToast();
  const timerRef = useRef(null);

  // Debounced search
  useEffect(() => {
    if (searchQuery.length < 2) { setSearchResults([]); return; }
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      setSearchLoading(true);
      try {
        const data = await searchTracks(searchQuery);
        setSearchResults(data);
      } catch { setSearchResults([]); }
      setSearchLoading(false);
    }, 300);
    return () => clearTimeout(timerRef.current);
  }, [searchQuery]);

  const handleMood = async (tag) => {
    setSelectedMood(tag);
    setLoading(true);
    try {
      const data = await getMoodTracks(tag);
      setMoodResults(data);
    } catch { setMoodResults([]); addToast('Failed to load mood tracks', 'error'); }
    setLoading(false);
  };

  const handleDownload = async (track) => {
    try {
      addToast(`Queueing "${track.track_name}"...`, 'info');
      const data = await resolveAndQueue(track.track_name, track.artist_name, track.search_query);
      addJob({ jobId: data.job_id, title: track.track_name, source: 'discovery', status: data.status });
      addToast(`"${track.track_name}" queued!`, 'success');
    } catch (e) { addToast(e.message || 'Download failed', 'error'); }
  };

  const TrackRow = ({ track }) => (
    <div className="track-row">
      {track.artwork_url ? (
        <img className="track-artwork" src={track.artwork_url} alt="" />
      ) : (
        <div className="track-artwork-placeholder">🎵</div>
      )}
      <div className="track-info">
        <span className="track-name">{track.track_name}</span>
        <span className="track-artist">
          {track.artist_name}
          {track.album_name && ` · ${track.album_name}`}
          {track.duration_ms && ` · ${fmtDur(track.duration_ms)}`}
        </span>
        {track.genre && <span className="track-meta">{track.genre}</span>}
      </div>
      <div className="track-actions">
        <button className="btn btn-sm btn-primary" onClick={() => handleDownload(track)}>
          <Download size={14} /> Download
        </button>
      </div>
    </div>
  );

  return (
    <AuthGate pageName="Discovery" pageIcon="🔍">
      <div className="page-content">
        <h1 className="hero-title gradient-text">🔍 Discover Music</h1>
        <p className="hero-subtitle">Search millions of songs or explore by mood.</p>

        <div style={{ display: 'flex', gap: 8, marginTop: '1.5rem' }}>
          <button className={`btn ${activeTab === 'search' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab('search')}>Search Songs</button>
          <button className={`btn ${activeTab === 'mood' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab('mood')}>Discover by Mood</button>
        </div>
        <hr className="divider" />

        {activeTab === 'search' && (
          <div>
            <div style={{ display: 'flex', gap: 12, marginBottom: '1rem' }}>
              <input className="input" placeholder="Search songs, artists, albums..."
                value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
              <button className="btn btn-primary" onClick={() => {
                if (searchQuery.length >= 2) {
                  setSearchLoading(true);
                  searchTracks(searchQuery).then(setSearchResults).catch(() => setSearchResults([])).finally(() => setSearchLoading(false));
                }
              }}><Search size={16} /></button>
            </div>
            {searchLoading && [1, 2, 3].map(i => <TrackSkeleton key={i} />)}
            {!searchLoading && searchResults.length > 0 && (
              <>
                <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', marginBottom: 8 }}>{searchResults.length} results</p>
                {searchResults.map((t, i) => <TrackRow key={i} track={t} />)}
              </>
            )}
            {!searchLoading && searchQuery.length >= 2 && searchResults.length === 0 && (
              <div className="empty-state"><div className="empty-state-icon">🔍</div>
                <div className="empty-state-title">No results found</div>
                <div className="empty-state-text">Try a different search term</div></div>
            )}
          </div>
        )}

        {activeTab === 'mood' && (
          <div>
            <div className="mood-grid" style={{ marginBottom: '1.5rem' }}>
              {moods.map(m => (
                <button key={m.tag} className={`mood-btn${selectedMood === m.tag ? ' active' : ''}`}
                  onClick={() => handleMood(m.tag)}>{m.label}</button>
              ))}
            </div>
            {loading && [1, 2, 3].map(i => <TrackSkeleton key={i} />)}
            {!loading && moodResults.length > 0 && (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>{moodResults.length} tracks</p>
                  <button className="btn btn-ghost btn-sm" onClick={() => selectedMood && handleMood(selectedMood)}>
                    <RefreshCw size={14} /> Shuffle
                  </button>
                </div>
                {moodResults.map((t, i) => <TrackRow key={i} track={t} />)}
              </>
            )}
          </div>
        )}
      </div>
    </AuthGate>
  );
}
