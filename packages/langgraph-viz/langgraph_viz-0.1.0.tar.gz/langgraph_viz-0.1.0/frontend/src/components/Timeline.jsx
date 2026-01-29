import { Circle } from 'lucide-react'

export function Timeline({ events, currentIndex, onSeek }) {
  if (!events || events.length === 0) {
    return (
      <div className="content-centered">
        <p>No events yet</p>
      </div>
    )
  }

  const formatTime = (timestamp) => {
    const date = new Date(timestamp * 1000)
    return date.toLocaleTimeString()
  }

  const getEventColor = (node) => {
    const colors = {
      router: '#3b82f6',
      planner: '#a78bfa',
      executor: '#4ade80',
      direct_answer: '#f59e0b',
      __interrupt__: '#fb923c',
      __end__: '#6b7280',
    }
    return colors[node] || '#06b6d4'
  }

  return (
    <div className="timeline-container">
      <div className="timeline-list">
        {events.map((event, idx) => (
          <div
            key={idx}
            onClick={() => onSeek(idx)}
            className={`timeline-item ${idx === currentIndex ? 'active' : ''}`}
          >
            <div className="timeline-header">
              <div className="timeline-node">
                <div 
                  className="node-indicator"
                  style={{ background: getEventColor(event.node) }}
                />
                <span className="node-name">{event.node}</span>
              </div>
              <span className="timeline-timestamp">
                {formatTime(event.timestamp)}
              </span>
            </div>
            
            {event.event_type && (
              <div className="timeline-type">
                {event.event_type}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
