import { useState, useEffect, useRef } from 'react';
import AuthGate from '../components/AuthGate';
import { useDownloads } from '../contexts/DownloadContext';
import { useToast } from '../components/Toast';
import { getDownloadUrl, editAudio } from '../services/api';
import { useSearchParams } from 'react-router-dom';
import { Play, Download } from 'lucide-react';
import ScrollReveal from '../components/ScrollReveal';

const formatOpts = {
  'MP3 — 128 kbps': ['mp3', '128'], 'MP3 — 192 kbps': ['mp3', '192'], 'MP3 — 320 kbps': ['mp3', '320'],
  'WAV (lossless)': ['wav', 'lossless'], 'OGG — 128 kbps': ['ogg', '128'], 'OGG — 192 kbps': ['ogg', '192'],
  'FLAC (lossless)': ['flac', 'lossless'], 'AAC — 192 kbps': ['aac', '192'],
};

const lbl = { display: 'block', fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 4 };
const fmtTime = (s) => isNaN(s) ? '0:00' : `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

export default function AudioEditor() {
  const { jobs } = useDownloads();
  const { addToast } = useToast();
  const [searchParams] = useSearchParams();
  const completed = jobs.filter(j => j.status === 'completed');

  const [selectedJobId, setSelectedJobId] = useState('');
  const [audioUrl, setAudioUrl] = useState(null);
  const [maxDuration, setMaxDuration] = useState(0);
  const [trimStart, setTrimStart] = useState(0);
  const [trimEnd, setTrimEnd] = useState(0);
  const [fadeIn, setFadeIn] = useState(0);
  const [fadeOut, setFadeOut] = useState(0);
  const [volumeDb, setVolumeDb] = useState(0);
  const [bassDb, setBassDb] = useState(0);
  const [trebleDb, setTrebleDb] = useState(0);
  const [speed, setSpeed] = useState(1.0);
  const [formatKey, setFormatKey] = useState('MP3 — 192 kbps');
  const [previewUrl, setPreviewUrl] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [loading, setLoading] = useState(false);
  const canvasRef = useRef(null);
  const audioRef = useRef(null);

  useEffect(() => {
    const job = searchParams.get('job');
    if (job && completed.find(j => j.jobId === job)) setSelectedJobId(job);
    else if (!selectedJobId && completed.length > 0) setSelectedJobId(completed[0].jobId);
  }, [completed.length]);

  useEffect(() => {
    if (!selectedJobId) return;
    setLoading(true);
    setPreviewUrl(null);
    const url = getDownloadUrl(selectedJobId);
    setAudioUrl(url);
    fetch(url).then(r => r.arrayBuffer()).then(buf => {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      ctx.decodeAudioData(buf.slice(0), (decoded) => {
        const dur = decoded.duration;
        setMaxDuration(dur);
        setTrimStart(0);
        setTrimEnd(dur);
        drawWaveform(decoded);
        ctx.close();
        setLoading(false);
      }, () => { setMaxDuration(0); setLoading(false); });
    }).catch(() => setLoading(false));
  }, [selectedJobId]);

  const drawWaveform = (buffer) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const data = buffer.getChannelData(0);
    const w = canvas.width = canvas.offsetWidth * 2;
    const h = canvas.height = 240;
    ctx.clearRect(0, 0, w, h);
    const step = Math.ceil(data.length / w);
    ctx.fillStyle = '#7c3aed';
    for (let i = 0; i < w; i++) {
      let min = 1, max = -1;
      for (let j = 0; j < step; j++) {
        const val = data[i * step + j] || 0;
        if (val < min) min = val;
        if (val > max) max = val;
      }
      const barH = Math.max(1, (max - min) * h * 0.45);
      ctx.globalAlpha = 0.6 + Math.abs(max) * 0.4;
      ctx.fillRect(i, (h - barH) / 2, 1, barH);
    }
  };

  const handleProcess = async (isPreview) => {
    if (!audioUrl) return;
    isPreview ? setPreviewing(true) : setExporting(true);
    try {
      const blob = await fetch(audioUrl).then(r => r.blob());
      const file = new File([blob], 'audio.mp3', { type: 'audio/mpeg' });
      const [fmt, qual] = isPreview ? ['mp3', '128'] : (formatOpts[formatKey] || ['mp3', '192']);
      const params = {
        trim_start_ms: Math.round(trimStart * 1000), trim_end_ms: Math.round(trimEnd * 1000),
        fade_in_ms: Math.round(fadeIn * 1000), fade_out_ms: Math.round(fadeOut * 1000),
        bass_boost_db: bassDb, treble_boost_db: trebleDb, volume_change_db: volumeDb,
        speed_factor: speed, output_format: fmt, output_quality: qual,
      };
      const res = await editAudio(file, params);
      const resBlob = await res.blob();
      const url = URL.createObjectURL(resBlob);
      if (isPreview) { setPreviewUrl(url); addToast('Preview ready!', 'success'); }
      else {
        const a = document.createElement('a');
        a.href = url; a.download = `sunleo_edited.${fmt}`; a.click();
        addToast('Export complete!', 'success');
      }
    } catch (e) { addToast(e.message || 'Processing failed', 'error'); }
    isPreview ? setPreviewing(false) : setExporting(false);
  };

  const estSize = () => {
    const dur = (trimEnd - trimStart) / speed;
    const [fmt, qual] = formatOpts[formatKey] || ['mp3', '192'];
    if (fmt === 'wav') return `${((dur * 44100 * 4) / 1048576).toFixed(1)} MB`;
    if (fmt === 'flac') return `${((dur * 44100 * 4 * 0.6) / 1048576).toFixed(1)} MB`;
    const kbps = parseInt(qual) || 192;
    return `${((dur * kbps * 1000 / 8) / 1048576).toFixed(1)} MB`;
  };

  const Slider = ({ label, value, onChange, min, max, step: s, unit = '' }) => (
    <div>
      <label style={lbl}>{label}: <strong style={{ color: 'var(--text-primary)' }}>{typeof value === 'number' ? value.toFixed(s < 1 ? 1 : 0) : value}{unit}</strong></label>
      <input type="range" min={min} max={max} step={s} value={value} onChange={e => onChange(parseFloat(e.target.value))} />
    </div>
  );

  return (
    <AuthGate pageName="Audio Editor" pageIcon="🎛️">
      <div className="page-content">
        <h1 className="hero-title gradient-text">🎛️ Audio Editor</h1>
        <p className="hero-subtitle">Trim, boost, and export your downloaded tracks.</p>

        <div style={{ marginTop: '1rem', marginBottom: '1rem' }}>
          <label style={lbl}>Select Track</label>
          <select className="input" value={selectedJobId} onChange={e => setSelectedJobId(e.target.value)}>
            <option value="">Choose a completed download...</option>
            {completed.map(j => <option key={j.jobId} value={j.jobId}>{j.title}</option>)}
          </select>
        </div>

        {completed.length === 0 && (
          <div className="empty-state"><div className="empty-state-icon">🎛️</div>
            <div className="empty-state-title">No tracks to edit</div>
            <div className="empty-state-text">Download some music first from Home or Discovery</div></div>
        )}

        {selectedJobId && audioUrl && !loading && (
          <>
            <div style={{ marginBottom: '1rem' }}>
              <audio ref={audioRef} controls src={audioUrl} style={{ width: '100%', borderRadius: 8 }} />
            </div>

            <div className="waveform-container" style={{ marginBottom: '1.5rem' }}>
              <canvas ref={canvasRef} />
            </div>

            <ScrollReveal>
              <div className="glass-card" style={{ marginBottom: 16 }}>
                <h4 style={{ marginBottom: 12 }}>✂️ Trim & Cut</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <Slider label="Start" value={trimStart} onChange={v => setTrimStart(Math.min(v, trimEnd))} min={0} max={maxDuration} step={0.5} unit="s" />
                  <Slider label="End" value={trimEnd} onChange={v => setTrimEnd(Math.max(v, trimStart))} min={0} max={maxDuration} step={0.5} unit="s" />
                </div>
                <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem', marginTop: 8 }}>
                  Selected: {fmtTime(trimStart)} → {fmtTime(trimEnd)} ({fmtTime(trimEnd - trimStart)} total)
                </p>
              </div>
            </ScrollReveal>

            <ScrollReveal delay={0.1}>
              <div className="glass-card" style={{ marginBottom: 16 }}>
                <h4 style={{ marginBottom: 12 }}>🎚️ Effects</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
                  <Slider label="Fade In" value={fadeIn} onChange={setFadeIn} min={0} max={10} step={0.5} unit="s" />
                  <Slider label="Fade Out" value={fadeOut} onChange={setFadeOut} min={0} max={10} step={0.5} unit="s" />
                  <Slider label="Volume" value={volumeDb} onChange={setVolumeDb} min={-12} max={12} step={0.5} unit=" dB" />
                  <Slider label="Bass Boost" value={bassDb} onChange={setBassDb} min={-12} max={12} step={0.5} unit=" dB" />
                  <Slider label="Treble Boost" value={trebleDb} onChange={setTrebleDb} min={-12} max={12} step={0.5} unit=" dB" />
                  <Slider label="Speed" value={speed} onChange={setSpeed} min={0.5} max={2} step={0.05} unit="x" />
                </div>
              </div>
            </ScrollReveal>

            <ScrollReveal delay={0.15}>
              <div className="glass-card" style={{ marginBottom: 16 }}>
                <h4 style={{ marginBottom: 12 }}>📤 Export</h4>
                <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                  <div style={{ flex: 1, minWidth: 200 }}>
                    <label style={lbl}>Format</label>
                    <select className="input" value={formatKey} onChange={e => setFormatKey(e.target.value)}>
                      {Object.keys(formatOpts).map(k => <option key={k}>{k}</option>)}
                    </select>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    Est. size: <strong style={{ color: 'var(--text-primary)' }}>{estSize()}</strong>
                  </div>
                </div>
              </div>
            </ScrollReveal>

            <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
              <button className="btn btn-secondary" onClick={() => handleProcess(true)} disabled={previewing}>
                <Play size={16} /> {previewing ? 'Processing...' : 'Preview'}
              </button>
              <button className="btn btn-primary" onClick={() => handleProcess(false)} disabled={exporting}>
                <Download size={16} /> {exporting ? 'Exporting...' : 'Export'}
              </button>
            </div>

            {previewUrl && (
              <div style={{ marginTop: '1.5rem' }}>
                <hr className="divider" />
                <h4 style={{ marginBottom: 8 }}>🔊 Preview</h4>
                <audio controls src={previewUrl} style={{ width: '100%', borderRadius: 8 }} />
              </div>
            )}
          </>
        )}

        {loading && <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}><div className="spinner" /></div>}
      </div>
    </AuthGate>
  );
}
