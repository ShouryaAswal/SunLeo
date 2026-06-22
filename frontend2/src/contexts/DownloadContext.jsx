import { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { getJobStatus } from '../services/api';

const DownloadContext = createContext(null);

export function DownloadProvider({ children }) {
  const [jobs, setJobs] = useState([]);
  const intervalRef = useRef(null);

  const addJob = useCallback((job) => {
    setJobs(prev => {
      if (prev.find(j => j.jobId === job.jobId)) return prev;
      return [...prev, job];
    });
  }, []);

  const removeJob = useCallback((jobId) => {
    setJobs(prev => prev.filter(j => j.jobId !== jobId));
  }, []);

  useEffect(() => {
    const poll = async () => {
      setJobs(prev => {
        const pending = prev.filter(j => j.status === 'queued' || j.status === 'running');
        if (pending.length === 0) return prev;
        // Fire polling outside of setState
        Promise.allSettled(pending.map(async (job) => {
          try {
            const data = await getJobStatus(job.jobId);
            setJobs(p => p.map(j => j.jobId === job.jobId ? {
              ...j,
              status: data.status,
              title: data.title || j.title,
              downloadUrl: data.download_url || j.downloadUrl,
              metadata: data.metadata || j.metadata,
            } : j));
          } catch {}
        }));
        return prev;
      });
    };
    intervalRef.current = setInterval(poll, 3000);
    return () => clearInterval(intervalRef.current);
  }, []);

  return (
    <DownloadContext.Provider value={{ jobs, addJob, removeJob }}>
      {children}
    </DownloadContext.Provider>
  );
}

export function useDownloads() {
  const ctx = useContext(DownloadContext);
  if (!ctx) throw new Error('useDownloads must be used within DownloadProvider');
  return ctx;
}
