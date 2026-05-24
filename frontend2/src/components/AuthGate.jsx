import { useAuth } from '../contexts/AuthContext';
import { motion } from 'framer-motion';
import { LogIn } from 'lucide-react';

export default function AuthGate({ children, pageName = 'this page', pageIcon = '🔒' }) {
  const { user, loading, loginWithGoogle } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <div className="spinner" />
      </div>
    );
  }

  if (!user) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', textAlign: 'center', padding: '2rem' }}
      >
        <div style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>{pageIcon}</div>
        <h2 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem', fontFamily: 'var(--font-display)' }}>
          Sign in to access {pageName}
        </h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', maxWidth: 400 }}>
          Create a free Sun Leo account to unlock this feature and more.
        </p>
        <button className="btn btn-primary" onClick={loginWithGoogle}>
          <LogIn size={18} /> Sign in with Google
        </button>
      </motion.div>
    );
  }

  return <>{children}</>;
}
