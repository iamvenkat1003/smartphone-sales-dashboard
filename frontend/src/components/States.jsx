export function LoadingState({ label = 'Loading analytics…', compact = false }) {
  return (
    <div className={`state-panel ${compact ? 'state-panel--compact' : ''}`}>
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}

export function ErrorState({ error, onRetry, compact = false }) {
  return (
    <div className={`state-panel state-panel--error ${compact ? 'state-panel--compact' : ''}`}>
      <span className="state-icon" aria-hidden="true">!</span>
      <div>
        <strong>Unable to load this section</strong>
        <p>{error?.message || 'Unable to reach analytics API.'}</p>
      </div>
      {onRetry && (
        <button className="button button--quiet" type="button" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  )
}

export function EmptyState({ message = 'No data is available yet.' }) {
  return (
    <div className="state-panel">
      <span className="state-icon state-icon--muted" aria-hidden="true">–</span>
      <span>{message}</span>
    </div>
  )
}
