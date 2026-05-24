import { usePlayer } from '../contexts/PlayerContext';
import { Play, Pause, Volume2, VolumeX } from 'lucide-react';

const fmt = (s) => {
  if (!s || isNaN(s)) return '0:00';
  return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
};

export default function Player() {
  const { currentTrack, isPlaying, progress, duration, volume, togglePlay, seek, setVolume } = usePlayer();

  const handleProgressClick = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    seek(pct * duration);
  };

  return (
    <>
      <style>{`
        .player-inner { display:flex; align-items:center; height:100%; padding:0 16px; gap:16px; max-width:1400px; margin:0 auto; }
        .player-track { display:flex; align-items:center; gap:12px; flex:1; min-width:0; }
        .player-controls { display:flex; flex-direction:column; align-items:center; gap:4px; flex:2; }
        .player-play-btn { width:40px; height:40px; border-radius:50%; background:var(--accent-gradient); border:none; color:white; display:flex; align-items:center; justify-content:center; cursor:pointer; transition:transform 0.15s,box-shadow 0.15s; flex-shrink:0; }
        .player-play-btn:hover { transform:scale(1.08); box-shadow:var(--glow-violet); }
        .player-progress { width:100%; max-width:500px; cursor:pointer; }
        .player-time { font-size:0.75rem; color:var(--text-dim); display:flex; gap:8px; }
        .player-volume { display:flex; align-items:center; gap:8px; flex:1; justify-content:flex-end; }
        .player-volume input { width:100px; }
        .player-art { width:48px; height:48px; border-radius:8px; object-fit:cover; flex-shrink:0; }
        .player-art-placeholder { width:48px; height:48px; border-radius:8px; background:var(--accent-violet-dim); display:flex; align-items:center; justify-content:center; font-size:1.2rem; flex-shrink:0; }
        .player-empty { display:flex; align-items:center; justify-content:center; height:100%; color:var(--text-dim); font-size:0.85rem; }
      `}</style>
      <div className="app-player">
        {!currentTrack ? (
          <div className="player-empty">No track playing — download or search for music</div>
        ) : (
          <div className="player-inner">
            <div className="player-track">
              {currentTrack.artwork ? (
                <img className="player-art" src={currentTrack.artwork} alt="" />
              ) : (
                <div className="player-art-placeholder">🎵</div>
              )}
              <div style={{ minWidth: 0 }}>
                <div className="track-name">{currentTrack.title}</div>
                <div className="track-artist">{currentTrack.artist}</div>
              </div>
            </div>
            <div className="player-controls">
              <button className="player-play-btn" onClick={togglePlay}>
                {isPlaying ? <Pause size={18} /> : <Play size={18} style={{ marginLeft: 2 }} />}
              </button>
              <div className="player-progress" onClick={handleProgressClick}>
                <div className="progress-bar">
                  <div className="progress-bar-fill" style={{ width: `${duration ? (progress / duration) * 100 : 0}%` }} />
                </div>
              </div>
              <div className="player-time">
                <span>{fmt(progress)}</span>
                <span>{fmt(duration)}</span>
              </div>
            </div>
            <div className="player-volume">
              <button className="btn btn-icon btn-ghost" style={{ width: 32, height: 32 }}
                onClick={() => setVolume(volume > 0 ? 0 : 0.7)}>
                {volume > 0 ? <Volume2 size={16} /> : <VolumeX size={16} />}
              </button>
              <input type="range" min="0" max="1" step="0.01" value={volume}
                onChange={(e) => setVolume(parseFloat(e.target.value))} />
            </div>
          </div>
        )}
      </div>
    </>
  );
}
