import { useState, useEffect, useRef } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { Wifi, WifiOff, Activity, ChevronDown, ChevronUp } from 'lucide-react'
import mermaid from 'mermaid'

mermaid.initialize({ 
  startOnLoad: true,
  theme: 'dark',
  flowchart: { curve: 'basis' }
})

function App() {
  // Use current page's port for WebSocket connection to support multiple visualizers
  const port = window.location.port || '8765'  // Fallback to 8765 if no port specified
  const wsUrl = `ws://${window.location.hostname}:${port}/ws`
  const { events, graphDef, isConnected, error } = useWebSocket(wsUrl)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const graphRef = useRef(null)

  useEffect(() => {
    if (events.length > 0 && !isPlaying) {
      setCurrentIndex(events.length - 1)
    }
  }, [events.length, isPlaying])

  useEffect(() => {
    if (!isPlaying) return
    const interval = setInterval(() => {
      setCurrentIndex((prev) => {
        if (prev >= events.length - 1) {
          setIsPlaying(false)
          return prev
        }
        return prev + 1
      })
    }, 1000)
    return () => clearInterval(interval)
  }, [isPlaying, events.length])

  // Render mermaid graph
  useEffect(() => {
    if (!graphRef.current) return

    let diagram = 'graph TD\n'
    diagram += '  START([START])\n'
    
    // Determine active node
    const activeNode = currentIndex >= 0 && currentIndex < events.length 
      ? events[currentIndex].node 
      : null

    if (graphDef && graphDef.nodes && graphDef.nodes.length > 0) {
       // Use server-provided graph definition
       const { nodes, edges } = graphDef
       let firstRealNode = null
       
       nodes.forEach(n => {
           const node = n.id
           if (!node.startsWith('__')) {
               const isActive = node === activeNode
               const style = isActive ? ':::active' : ''
               diagram += `  ${node}[${node}]${style}\n`
               if (!firstRealNode) firstRealNode = node
           }
       })
       
       if (firstRealNode) {
         diagram += `  START --> ${firstRealNode}\n`
       }
       
       edges.forEach(edge => {
           const from = edge.source
           const to = edge.target
           if (!from.startsWith('__') && !to.startsWith('__')) {
               diagram += `  ${from} --> ${to}\n`
           }
       })

    } else {
        // Fallback: Infer from events (Dynamic)
        if (!events || events.length === 0) return

        const nodes = new Set()
        const edges = []
        
        events.forEach((event, idx) => {
          const node = event.node
          if (node) {
            nodes.add(node)
            if (idx < events.length - 1) {
              const nextNode = events[idx + 1].node
              if (nextNode) {
                edges.push({from: node, to: nextNode})
              }
            }
          }
        })

        let firstRealNode = null
        nodes.forEach(node => {
          if (!node.startsWith('__')) {
            const isActive = node === activeNode
            const style = isActive ? ':::active' : ''
            diagram += `  ${node}[${node}]${style}\n`
            if (!firstRealNode) firstRealNode = node
          }
        })
        
        if (firstRealNode) {
          diagram += `  START --> ${firstRealNode}\n`
        }
        
        const uniqueEdges = [...new Map(edges.map(e => [`${e.from}-${e.to}`, e])).values()]
        uniqueEdges.forEach(edge => {
          if (!edge.from.startsWith('__') && !edge.to.startsWith('__')) {
            diagram += `  ${edge.from} --> ${edge.to}\n`
          }
        })
    }
    
    diagram += '\n  classDef active fill:#10b981,stroke:#059669,stroke-width:3px,color:#000,font-weight:bold\n'

    const render = async () => {
      try {
        graphRef.current.innerHTML = ''
        const { svg } = await mermaid.render('mermaid-graph', diagram)
        graphRef.current.innerHTML = svg
      } catch (err) {
        console.error('Mermaid error:', err)
      }
    }

    render()
  }, [events, currentIndex, graphDef])

  // Show ALL events in timeline
  const filteredEvents = events

  const currentSnapshot = events[currentIndex]
  const progress = events.length > 1 ? ((currentIndex / (events.length - 1)) * 100) : 0

  return (
    <div className="visualizer">
      {/* Header */}
      <div className="header">
        <div className="header-left">
          <div className="logo">
            <Activity size={24} color="white" />
          </div>
          <div className="title">
            <h1>LangGraph Visualizer</h1>
            <p>Real-time workflow debugging</p>
          </div>
        </div>
        <div className="header-right">
          <div className={`badge ${isConnected ? 'connected' : 'error'}`}>
            {isConnected ? <Wifi size={16} /> : <WifiOff size={16} />}
            {isConnected ? 'Connected' : error || 'Disconnected'}
          </div>
          <div className="badge info">
            {filteredEvents.length} Events
          </div>
        </div>
      </div>

      {/* Content - 20% / 20% / 60% */}
      <div className="content">
        {/* Graph Panel - 20% */}
        <div className="panel panel-graph">
          <div className="panel-header">
            <h2>Workflow Graph</h2>
            <p>Visual representation</p>
          </div>
          <div className="panel-body">
            {events.length === 0 ? (
              <div className="empty">Waiting for events...</div>
            ) : (
              <div className="graph-container" ref={graphRef}></div>
            )}
          </div>
        </div>

        {/* Timeline Panel - 20% */}
        <div className="panel panel-timeline">
          <div className="panel-header">
            <h2>Event Timeline</h2>
            <p>Execution history</p>
          </div>
          <div className="panel-body">
            {filteredEvents.length === 0 ? (
              <div className="empty">No events</div>
            ) : (
              filteredEvents.map((event, idx) => (
                <div
                  key={idx}
                  className={`timeline-item ${idx === currentIndex ? 'active' : ''}`}
                  onClick={() => setCurrentIndex(idx)}
                >
                  <div className="timeline-row">
                    <div className="timeline-node">
                      <div className="node-dot" style={{ background: '#06b6d4' }} />
                      <span className="node-name">{event.node}</span>
                    </div>
                  </div>
                  <div className="timestamp">
                    {new Date(event.timestamp * 1000).toLocaleTimeString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* State Panel - 60% */}
        <div className="panel panel-state">
          <div className="panel-header">
            <h2>State Inspector</h2>
            <p>Current state and changes</p>
          </div>
          <div className="panel-body">
            {!currentSnapshot ? (
              <div className="empty">Select an event</div>
            ) : (
              <>
                {/* Full State */}
                <div className="state-section">
                  <div className="section-title">
                    <span>
                      Full State 
                      <span style={{ fontSize: '11px', color: '#6b7280', fontWeight: 'normal', marginLeft: '8px' }}>
                        ({currentSnapshot.node})
                      </span>
                    </span>
                  </div>
                  <div className="section-content">
                    <div className="json-view">
                      <pre>{JSON.stringify(currentSnapshot.state, null, 2)}</pre>
                    </div>
                  </div>
                </div>

                {/* Changes */}
                {currentSnapshot.diff && (
                  <div className="state-section">
                    <div className="section-title">
                      <span>Changes (Delta)</span>
                    </div>
                    
                    <div className="section-content">
                        {currentSnapshot.diff.added?.length > 0 && (
                          <div className="diff-card added">
                            <div className="diff-title" style={{ color: '#34d399' }}>
                              + Added ({currentSnapshot.diff.added.length})
                            </div>
                            <div className="diff-items">
                              {currentSnapshot.diff.added.map((key, i) => (
                                <div key={i} className="diff-item" style={{ color: '#6ee7b7' }}>
                                  {key}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {currentSnapshot.diff.removed?.length > 0 && (
                          <div className="diff-card removed">
                            <div className="diff-title" style={{ color: '#f87171' }}>
                              - Removed ({currentSnapshot.diff.removed.length})
                            </div>
                            <div className="diff-items">
                              {currentSnapshot.diff.removed.map((key, i) => (
                                <div key={i} className="diff-item" style={{ color: '#fca5a5' }}>
                                  {key}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {currentSnapshot.diff.modified && Object.keys(currentSnapshot.diff.modified).length > 0 && (
                          <div className="diff-card modified">
                            <div className="diff-title" style={{ color: '#fbbf24' }}>
                              ✎ Modified ({Object.keys(currentSnapshot.diff.modified).length})
                            </div>
                            <div className="diff-items">
                              {Object.entries(currentSnapshot.diff.modified).map(([key, change], i) => (
                                <div key={i} style={{ marginBottom: '8px' }}>
                                  <div style={{ color: '#fbbf24' }}>{key}:</div>
                                  <div style={{ paddingLeft: '16px', fontSize: '11px' }}>
                                    <div style={{ color: '#fca5a5' }}>- {JSON.stringify(change.old)}</div>
                                    <div style={{ color: '#6ee7b7' }}>+ {JSON.stringify(change.new)}</div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {(!currentSnapshot.diff.added || currentSnapshot.diff.added.length === 0) &&
                         (!currentSnapshot.diff.removed || currentSnapshot.diff.removed.length === 0) &&
                         (!currentSnapshot.diff.modified || Object.keys(currentSnapshot.diff.modified).length === 0) && (
                          <div style={{ padding: '16px', fontSize: '13px', color: '#6b7280', textAlign: 'center' }}>
                            No changes detected
                          </div>
                        )}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Playback Controls */}
      {events.length > 0 && (
        <div className="controls">
          <div className="progress">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
              <input
                type="range"
                min="0"
                max={events.length - 1}
                value={currentIndex}
                onChange={(e) => setCurrentIndex(parseInt(e.target.value))}
                className="progress-slider"
              />
            </div>
            <div className="progress-text">
              <span>Event {currentIndex + 1} of {events.length}</span>
              <span>{Math.round((currentIndex / events.length) * 100)}% complete</span>
            </div>
          </div>
          <div className="buttons">
            <button className="btn" onClick={() => setCurrentIndex(0)}>
              ⟲
            </button>
            <button
              className="btn"
              onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
              disabled={currentIndex === 0}
            >
              ◀
            </button>
            <button
              className="btn play"
              onClick={() => isPlaying ? setIsPlaying(false) : setIsPlaying(true)}
            >
              {isPlaying ? '⏸' : '▶'}
            </button>
            <button
              className="btn"
              onClick={() => setCurrentIndex(Math.min(events.length - 1, currentIndex + 1))}
              disabled={currentIndex >= events.length - 1}
            >
              ▶
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
