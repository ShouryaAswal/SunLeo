import { useState } from 'react';
import { useToast } from '../components/Toast';
import { sendFeedback } from '../services/api';
import { Send } from 'lucide-react';
import { motion } from 'framer-motion';
import ScrollReveal from '../components/ScrollReveal';

const categories = ['Bug Report', 'Feature Request', 'General Feedback', 'Other'];

export default function Feedback() {
  const { addToast } = useToast();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [category, setCategory] = useState('Bug Report');
  const [rating, setRating] = useState(5);
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [errors, setErrors] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = [];
    if (!name.trim()) errs.push('Name is required');
    if (!email.includes('@')) errs.push('Valid email is required');
    if (message.length < 10) errs.push('Message must be at least 10 characters');
    if (errs.length) { setErrors(errs); return; }
    setErrors([]);
    setSubmitting(true);
    try {
      await sendFeedback({ name, email, category, rating, message });
      addToast('Feedback sent! Thank you 🎉', 'success');
      setSubmitted(true);
    } catch (e) {
      addToast(e.message || 'Failed to send', 'error');
    }
    setSubmitting(false);
  };

  const reset = () => { setName(''); setEmail(''); setCategory('Bug Report'); setRating(5); setMessage(''); setSubmitted(false); setErrors([]); };

  if (submitted) {
    return (
      <div className="page-content">
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
          style={{ textAlign: 'center', padding: '3rem 1.5rem' }} className="glass-card">
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✅</div>
          <h2 style={{ fontFamily: 'var(--font-display)', marginBottom: '0.5rem' }}>Thank you!</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>Your feedback has been sent to the development team.</p>
          <button className="btn btn-secondary" onClick={reset}>Send Another</button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="page-content">
      <ScrollReveal>
        <h1 className="hero-title gradient-text">📝 Feedback & Support</h1>
        <p className="hero-subtitle">Help us improve Sun Leo. We read every message.</p>
      </ScrollReveal>
      <hr className="divider" />
      <ScrollReveal delay={0.15}>
        <form className="glass-card" onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div>
              <label style={lbl}>Name</label>
              <input className="input" value={name} onChange={e => setName(e.target.value)} placeholder="Your name" />
            </div>
            <div>
              <label style={lbl}>Email</label>
              <input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@email.com" />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div>
              <label style={lbl}>Category</label>
              <select className="input" value={category} onChange={e => setCategory(e.target.value)}>
                {categories.map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label style={lbl}>Rating</label>
              <div className="star-rating">
                {[1, 2, 3, 4, 5].map(i => (
                  <button key={i} type="button" className="star-rating-btn"
                    style={{ color: i <= rating ? '#fbbf24' : 'var(--text-dim)' }}
                    onClick={() => setRating(i)}>★</button>
                ))}
              </div>
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={lbl}>Message</label>
            <textarea className="input" rows={5} value={message} onChange={e => setMessage(e.target.value)}
              placeholder="Describe your feedback, bug, or feature request..." />
          </div>
          {errors.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              {errors.map((err, i) => <p key={i} style={{ color: 'var(--color-danger)', fontSize: '0.85rem' }}>• {err}</p>)}
            </div>
          )}
          <button className="btn btn-primary btn-full" type="submit" disabled={submitting}>
            <Send size={16} /> {submitting ? 'Sending...' : '🚀 Submit Feedback'}
          </button>
        </form>
      </ScrollReveal>
    </div>
  );
}

const lbl = { display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 };
