import { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';

const PlayerContext = createContext(null);

export function PlayerProvider({ children }) {
  const [currentTrack, setCurrentTrack] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolumeState] = useState(0.7);
  const audioRef = useRef(null);
  if (!audioRef.current) audioRef.current = new Audio();
  const prevVolume = useRef(0.7);

  const playTrack = useCallback((track) => {
    const audio = audioRef.current;
    setCurrentTrack(track);
    audio.src = track.url;
    audio.volume = volume;
    audio.play().catch(() => {});
    setIsPlaying(true);
  }, [volume]);

  const togglePlay = useCallback(() => {
    const audio = audioRef.current;
    if (!audio.src) return;
    if (audio.paused) { audio.play().catch(() => {}); setIsPlaying(true); }
    else { audio.pause(); setIsPlaying(false); }
  }, []);

  const seek = useCallback((time) => {
    audioRef.current.currentTime = Math.max(0, Math.min(time, audioRef.current.duration || 0));
  }, []);

  const setVolume = useCallback((v) => {
    const val = Math.max(0, Math.min(1, v));
    audioRef.current.volume = val;
    setVolumeState(val);
    if (val > 0) prevVolume.current = val;
  }, []);

  useEffect(() => {
    const audio = audioRef.current;
    const onTime = () => setProgress(audio.currentTime);
    const onMeta = () => setDuration(audio.duration);
    const onEnd = () => setIsPlaying(false);
    audio.addEventListener('timeupdate', onTime);
    audio.addEventListener('loadedmetadata', onMeta);
    audio.addEventListener('ended', onEnd);
    return () => {
      audio.removeEventListener('timeupdate', onTime);
      audio.removeEventListener('loadedmetadata', onMeta);
      audio.removeEventListener('ended', onEnd);
    };
  }, []);

  useEffect(() => {
    const handler = (e) => {
      const tag = document.activeElement?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      switch (e.key) {
        case ' ': e.preventDefault(); togglePlay(); break;
        case 'ArrowLeft': seek((audioRef.current.currentTime || 0) - 5); break;
        case 'ArrowRight': seek((audioRef.current.currentTime || 0) + 5); break;
        case 'ArrowUp': e.preventDefault(); setVolume(audioRef.current.volume + 0.1); break;
        case 'ArrowDown': e.preventDefault(); setVolume(audioRef.current.volume - 0.1); break;
        case 'm': case 'M':
          if (audioRef.current.volume > 0) { setVolume(0); }
          else { setVolume(prevVolume.current || 0.7); }
          break;
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [togglePlay, seek, setVolume]);

  return (
    <PlayerContext.Provider value={{ currentTrack, isPlaying, progress, duration, volume, playTrack, togglePlay, seek, setVolume }}>
      {children}
    </PlayerContext.Provider>
  );
}

export function usePlayer() {
  const ctx = useContext(PlayerContext);
  if (!ctx) throw new Error('usePlayer must be used within PlayerProvider');
  return ctx;
}
