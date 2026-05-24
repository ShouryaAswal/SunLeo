import { useState, useEffect } from 'react';
import AuthGate from '../components/AuthGate';
import { useAuth } from '../contexts/AuthContext';
import { useDownloads } from '../contexts/DownloadContext';
import { useToast } from '../components/Toast';
import { CardSkeleton } from '../components/Skeleton';
import ScrollReveal from '../components/ScrollReveal';
import { getPlaylists, createPlaylist, deletePlaylist, addTracksToPlaylist, removeTrackFromPlaylist, searchTracks } from '../services/api';
import { Plus, Search, Trash2, Download, X, Music } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Playlists() {
  const { user } = useAuth();
  const { addJob } = useDownloads();
  const { addToast } = useToast();
  const [playlists, setPlaylists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const [sq, setSq] = useState('');
  const [sr, setSr] = useState([]);
  const [sel, setSel] = useState([]);
  const [targetPid, setTargetPid] = useState('');
  const [delConfirm, setDelConfirm] = useState(null);

  const load = async () => {
    if (!user) return;
    try { const d = await getPlaylists(user.uid); setPlaylists(d); } catch {}
    setLoading(false);
  };
  useEffect(() => { load(); }, [user]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    try { await createPlaylist(user.uid, newName); addToast('Playlist created!', 'success'); setNewName(''); setShowCreate(false); load(); }
    catch (e) { addToast(e.message, 'error'); }
  };

  const handleSearch = async () => {
    if (sq.length < 2) return;
    try { setSr(await searchTracks(sq)); } catch { setSr([]); }
  };

  const toggleTrack = (t) => {
    const key = `${t.track_name}|${t.artist_name}`;
    setSel(prev => prev.find(x => `${x.track_name}|${x.artist_name}` === key) ? prev.filter(x => `${x.track_name}|${x.artist_name}` !== key) : [...prev, t]);
  };

  const handleAdd = async () => {
    if (!targetPid || sel.length === 0) return;
    const tracks = sel.map(t => ({ track_name: t.track_name, artist_name: t.artist_name, search_query: t.search_query }));
    try { await addTracksToPlaylist(user.uid, targetPid, tracks); addToast(`${sel.length} track(s) added!`, 'success'); setSel([]); load(); }
    catch (e) { addToast(e.message, 'error'); }
  };

  const handleDel = async (pid) => {
    if (delConfirm !== pid) { setDelConfirm(pid); return; }
    try { await deletePlaylist(user.uid, pid); addToast('Playlist deleted', 'success'); setDelConfirm(null); load(); }
    catch (e) { addToast(e.message, 'error'); }
  };

  const handleRemove = async (pid, idx) => {
    try { await removeTrackFromPlaylist(user.uid, pid, idx); load(); } catch {}
  };

  return (
    <AuthGate pageName="Playlists" pageIcon="📋">
      <div className="page-content">
        <h1 className="hero-title gradient-text">📋 My Playlists</h1>
        <p className="hero-subtitle">Create, manage, and download your music collections.</p>

        <div style={{ display: 'flex', gap: 8, marginTop: '1.5rem' }}>
          <button className="btn btn-primary" onClick={() => { setShowCreate(!showCreate); setShowSearch(false); }}><Plus size={16} /> Create Playlist</button>
          <button className="btn btn-secondary" onClick={() => { setShowSearch(!showSearch); setShowCreate(false); }}><Search size={16} /> Search & Add</button>
        </div>

        <AnimatePresence>
          {showCreate && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
              style={{ overflow: 'hidden', marginTop: 12 }}>
              <form className="glass-card" onSubmit={handleCreate} style={{ display: 'flex', gap: 12 }}>
                <input className="input" placeholder="Playlist name..." value={newName} onChange={e => setNewName(e.target.value)} />
                <button className="btn btn-primary" type="submit">Create</button>
              </form>
            </motion.div>
          )}
          {showSearch && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
              style={{ overflow: 'hidden', marginTop: 12 }}>
              <div className="glass-card">
                <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
                  <input className="input" placeholder="Search tracks to add..." value={sq} onChange={e => setSq(e.target.value)} />
                  <button className="btn btn-primary" onClick={handleSearch}><Search size={16} /></button>
                </div>
                {sr.length > 0 && (
                  <div style={{ maxHeight: 250, overflowY: 'auto', marginBottom: 12 }}>
                    {sr.map((t, i) => {
                      const isSelected = sel.find(x => x.track_name === t.track_name && x.artist_name === t.artist_name);
                      return (
                        <label key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 4px', cursor: 'pointer', borderBottom: '1px solid var(--border-subtle)' }}>
                          <input type="checkbox" checked={!!isSelected} onChange={() => toggleTrack(t)} />
                          {t.artwork_url ? <img src={t.artwork_url} alt="" style={{ width: 36, height: 36, borderRadius: 6, objectFit: 'cover' }} /> : <div className="track-artwork-placeholder" style={{ width: 36, height: 36, fontSize: '0.9rem' }}>🎵</div>}
                          <div><span className="track-name" style={{ fontSize: '0.88rem' }}>{t.track_name}</span><br /><span className="track-artist">{t.artist_name}</span></div>
                        </label>
                      );
                    })}
                  </div>
                )}
                {sel.length > 0 && (
                  <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{sel.length} selected</span>
                    <select className="input" style={{ flex: 1 }} value={targetPid} onChange={e => setTargetPid(e.target.value)}>
                      <option value="">Select a playlist...</option>
                      {playlists.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                    </select>
                    <button className="btn btn-primary btn-sm" onClick={handleAdd} disabled={!targetPid}>Add Selected</button>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <hr className="divider" />

        {loading ? [1, 2, 3].map(i => <CardSkeleton key={i} />) : playlists.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">🎵</div>
            <div className="empty-state-title">No playlists yet</div>
            <div className="empty-state-text">Create your first playlist to get started</div></div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {playlists.map(pl => (
              <ScrollReveal key={pl.id}>
                <div className="glass-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                    <h3 style={{ fontSize: '1.1rem' }}>{pl.name}</h3>
                    <span className="badge badge-violet">{pl.tracks?.length || 0} tracks</span>
                  </div>
                  {(!pl.tracks || pl.tracks.length === 0) ? (
                    <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>No tracks yet — use Search & Add above</p>
                  ) : (
                    pl.tracks.map((t, idx) => (
                      <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                        <span style={{ color: 'var(--accent-violet-light)', fontWeight: 600, fontSize: '0.85rem', width: 24 }}>{idx + 1}</span>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <span className="track-name" style={{ fontSize: '0.9rem' }}>{t.track_name}</span>
                          <span style={{ color: 'var(--text-dim)', fontSize: '0.82rem' }}> · {t.artist_name}</span>
                        </div>
                        <button className="btn btn-icon btn-ghost" style={{ width: 28, height: 28 }} onClick={() => handleRemove(pl.id, idx)}>
                          <X size={14} />
                        </button>
                      </div>
                    ))
                  )}
                  <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                    <button className="btn btn-sm btn-primary" onClick={() => {
                      addToast('Bulk download not yet wired — download tracks individually from Discovery', 'info');
                    }}><Download size={14} /> Download All</button>
                    <button className={`btn btn-sm btn-ghost`}
                      style={delConfirm === pl.id ? { color: 'var(--color-danger)', borderColor: 'var(--color-danger)' } : {}}
                      onClick={() => handleDel(pl.id)}>
                      <Trash2 size={14} /> {delConfirm === pl.id ? 'Confirm Delete?' : 'Delete'}
                    </button>
                  </div>
                </div>
              </ScrollReveal>
            ))}
          </div>
        )}
      </div>
    </AuthGate>
  );
}
