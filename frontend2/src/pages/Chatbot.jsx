import { useState, useRef, useEffect } from 'react';
import AuthGate from '../components/AuthGate';
import { useAuth } from '../contexts/AuthContext';
import { useDownloads } from '../contexts/DownloadContext';
import { useToast } from '../components/Toast';
import { sendChatMessage } from '../services/api';
import { Send, Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const quickActions = [
  { label: '🎭 Chill vibes', prompt: 'Find me some chill relaxing music' },
  { label: '💪 Workout mix', prompt: 'Give me high-energy workout songs' },
  { label: '😔 Feeling sad', prompt: 'I need some sad but beautiful songs' },
  { label: '🎉 Party time', prompt: 'Get me hype party music' },
  { label: '📚 Study focus', prompt: 'I need focus music for studying' },
  { label: '📋 My Playlists', prompt: 'Show me my playlists' },
];

const welcomeMsg = {
  role: 'bot',
  content: "Hey! 🎵 I'm **SunLeo DJ**, your AI music assistant.\n\nI can help you:\n- 🔍 **Search** for any song or artist\n- 🎭 **Discover** music by mood\n- ⬇️ **Download** songs as MP3\n- 📋 **Create & manage** playlists\n\nWhat are you in the mood for today?",
};

export default function Chatbot() {
  const { user } = useAuth();
  const { addJob } = useDownloads();
  const { addToast } = useToast();
  const [messages, setMessages] = useState([welcomeMsg]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (text) => {
    if (!text.trim()) return;
    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setLoading(true);
    try {
      const data = await sendChatMessage(text, sessionId, user.uid);
      setMessages(prev => [...prev, { role: 'bot', content: data.reply || data.response || 'No response' }]);
      if (data.actions) {
        data.actions.forEach(a => {
          if (a.type === 'download_queued' && a.job_id) {
            addJob({ jobId: a.job_id, title: a.track_name || 'Unknown', source: 'chatbot', status: 'queued' });
            addToast(`Queued download: ${a.track_name || 'track'}`, 'success');
          }
        });
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'bot', content: `⚠️ Error: ${e.message || 'Something went wrong.'}` }]);
    }
    setLoading(false);
  };

  const renderContent = (text) => {
    // Simple markdown bold
    return text.split('\n').map((line, i) => (
      <span key={i}>
        {line.split(/\*\*(.*?)\*\*/).map((part, j) =>
          j % 2 === 1 ? <strong key={j}>{part}</strong> : part
        )}
        {i < text.split('\n').length - 1 && <br />}
      </span>
    ));
  };

  return (
    <AuthGate pageName="DJ Chat" pageIcon="🤖">
      <div className="page-content" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - var(--player-height) - var(--header-height, 0px))', maxHeight: 'calc(100vh - 100px)', padding: '1.5rem 2rem' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontFamily: 'var(--font-display)' }}>
              <span className="gradient-text">🤖 SunLeo DJ</span>{' '}
              <span className="badge badge-success" style={{ fontSize: '0.65rem', verticalAlign: 'middle' }}>LIVE</span>
            </h1>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem' }}>Powered by Groq Llama 3</p>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={() => setMessages([welcomeMsg])}>
            <Trash2 size={14} /> Clear
          </button>
        </div>

        {/* Quick Actions */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
          {quickActions.map(a => (
            <button key={a.label} className="btn btn-ghost btn-sm" onClick={() => handleSend(a.prompt)}>
              {a.label}
            </button>
          ))}
        </div>

        <hr className="divider" style={{ margin: '0.5rem 0' }} />

        {/* Chat Messages */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 12, paddingTop: 8, paddingBottom: 8 }}>
          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25 }}
                style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                <div className={`chat-bubble chat-bubble-${msg.role === 'user' ? 'user' : 'bot'}`}>
                  {renderContent(msg.content)}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div className="chat-bubble chat-bubble-bot">
                <div className="typing-indicator">
                  <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
                </div>
              </div>
            </div>
          )}
          <div ref={scrollRef} />
        </div>

        {/* Input */}
        <form onSubmit={e => { e.preventDefault(); handleSend(inputValue.trim()); }}
          style={{ display: 'flex', gap: 12, marginTop: 8 }}>
          <input className="input" value={inputValue} onChange={e => setInputValue(e.target.value)}
            placeholder="Ask the DJ anything..." disabled={loading} />
          <button className="btn btn-primary" type="submit" disabled={loading || !inputValue.trim()}>
            <Send size={16} />
          </button>
        </form>
      </div>
    </AuthGate>
  );
}
