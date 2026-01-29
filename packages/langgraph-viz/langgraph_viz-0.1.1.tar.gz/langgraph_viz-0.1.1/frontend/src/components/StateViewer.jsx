import { JsonView, darkStyles } from 'react-json-view-lite'
import 'react-json-view-lite/dist/index.css'
import { FileCode, Plus, Minus, Edit2 } from 'lucide-react'

export function StateViewer({ snapshot }) {
  if (!snapshot) {
    return (
      <div className="content-centered">
        <div className="empty-state">
          <FileCode className="w-16 h-16" />
          <p>Select an event to view state</p>
        </div>
      </div>
    )
  }

  const { state, diff } = snapshot

  const hasDiff = diff && (
    diff.added?.length > 0 || 
    diff.removed?.length > 0 || 
    Object.keys(diff.modified || {}).length > 0
  )

  return (
    <div className="state-viewer">
      {/* Current State */}
      <div className="state-section">
        <div className="state-section-header">
          <FileCode className="w-5 h-5" style={{ color: '#60a5fa' }} />
          <h3>Current State</h3>
          <span className="node-badge">{snapshot.node}</span>
        </div>
        <div className="state-content">
          <JsonView 
            data={state || {}} 
            shouldExpandNode={(level) => level <= 1}
            style={darkStyles}
          />
        </div>
      </div>

      {/* Changes */}
      {hasDiff && (
        <div className="state-section">
          <div className="state-section-header">
            <Edit2 className="w-5 h-5" style={{ color: '#fb923c' }} />
            <h3>Changes</h3>
          </div>
          
          <div className="diff-list">
            {/* Added Keys */}
            {diff.added && diff.added.length > 0 && (
              <div className="diff-card added">
                <div className="diff-header added">
                  <Plus className="w-4 h-4" />
                  <span>Added ({diff.added.length})</span>
                </div>
                <div className="diff-items">
                  {diff.added.map((key, idx) => (
                    <div key={idx} className="diff-item added">
                      + {key}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Removed Keys */}
            {diff.removed && diff.removed.length > 0 && (
              <div className="diff-card removed">
                <div className="diff-header removed">
                  <Minus className="w-4 h-4" />
                  <span>Removed ({diff.removed.length})</span>
                </div>
                <div className="diff-items">
                  {diff.removed.map((key, idx) => (
                    <div key={idx} className="diff-item removed">
                      - {key}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Modified Keys */}
            {diff.modified && Object.keys(diff.modified).length > 0 && (
              <div className="diff-card modified">
                <div className="diff-header modified">
                  <Edit2 className="w-4 h-4" />
                  <span>Modified ({Object.keys(diff.modified).length})</span>
                </div>
                <div className="diff-items">
                  {Object.entries(diff.modified).map(([key, change], idx) => (
                    <div key={idx} className="diff-change">
                      <div className="diff-change-key">{key}</div>
                      <div className="diff-change-values">
                        <div style={{ color: '#fca5a5' }}>
                          - {JSON.stringify(change.old)}
                        </div>
                        <div style={{ color: '#6ee7b7' }}>
                          + {JSON.stringify(change.new)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
