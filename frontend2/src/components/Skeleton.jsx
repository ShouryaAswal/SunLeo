export function TrackSkeleton() {
  return (
    <div className="track-row">
      <div className="skeleton skeleton-avatar" />
      <div style={{ flex: 1 }}>
        <div className="skeleton skeleton-text" style={{ width: '60%' }} />
        <div className="skeleton skeleton-text-sm" style={{ width: '40%' }} />
      </div>
      <div className="skeleton" style={{ width: 70, height: 32, borderRadius: 8 }} />
    </div>
  );
}

export function CardSkeleton() {
  return <div className="skeleton skeleton-card" />;
}

export function ChatSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div className="skeleton skeleton-text" style={{ width: '80%' }} />
      <div className="skeleton skeleton-text" style={{ width: '55%' }} />
      <div className="skeleton skeleton-text" style={{ width: '70%' }} />
    </div>
  );
}
