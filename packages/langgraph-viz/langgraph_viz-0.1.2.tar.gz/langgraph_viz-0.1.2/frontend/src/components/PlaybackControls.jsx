import { Play, Pause, SkipBack, SkipForward, RotateCcw } from 'lucide-react'

export function PlaybackControls({ 
  currentIndex, 
  totalEvents, 
  isPlaying, 
  onPlay, 
  onPause, 
  onNext, 
  onPrev, 
  onReset,
  onSeek 
}) {
  const progress = totalEvents > 1 ? ((currentIndex / (totalEvents - 1)) * 100) : 0
  const percentComplete = totalEvents > 0 ? Math.round(((currentIndex + 1) / totalEvents) * 100) : 0

  return (
    <div className="playback-controls">
      {/* Progress Bar */}
      <div className="progress-container">
        <div className="progress-bar-wrapper">
          <div 
            className="progress-bar-fill" 
            style={{ width: `${progress}%` }}
          />
          <input
            type="range"
            min="0"
            max={Math.max(0, totalEvents - 1)}
            value={currentIndex}
            onChange={(e) => onSeek(parseInt(e.target.value))}
            className="progress-bar-input"
          />
        </div>
        <div className="progress-info">
          <span>Event {currentIndex + 1} of {totalEvents}</span>
          <span>{percentComplete}% complete</span>
        </div>
      </div>

      {/* Control Buttons */}
      <div className="controls-buttons">
        <button
          onClick={onReset}
          className="control-btn"
          title="Reset to start"
        >
          <RotateCcw className="w-5 h-5" />
        </button>

        <button
          onClick={onPrev}
          disabled={currentIndex === 0}
          className="control-btn"
          title="Previous event"
        >
          <SkipBack className="w-5 h-5" />
        </button>

        <button
          onClick={isPlaying ? onPause : onPlay}
          className="control-btn play"
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6" />}
        </button>

        <button
          onClick={onNext}
          disabled={currentIndex >= totalEvents - 1}
          className="control-btn"
          title="Next event"
        >
          <SkipForward className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}
