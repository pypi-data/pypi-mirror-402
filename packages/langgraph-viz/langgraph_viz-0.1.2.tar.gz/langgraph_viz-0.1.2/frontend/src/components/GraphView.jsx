import { useState, useEffect, useRef } from 'react'
import mermaid from 'mermaid'
import { Workflow } from 'lucide-react'

mermaid.initialize({ 
  startOnLoad: true,
  theme: 'dark',
  flowchart: { curve: 'basis' }
})

export function GraphView({ events, currentIndex }) {
  const [mermaidDef, setMermaidDef] = useState('')
  const containerRef = useRef(null)

  useEffect(() => {
    if (!events || events.length === 0) return

    const nodes = new Set()
    const edges = []
    
    events.forEach((event, idx) => {
      const node = event.node
      if (node && node !== 'unknown' && node !== '__interrupt__' && node !== '__end__' && node !== 'final') {
        nodes.add(node)
        if (idx < events.length - 1) {
          const nextNode = events[idx + 1].node
          if (nextNode && nextNode !== '__interrupt__' && nextNode !== '__end__' && nextNode !== 'final' && nextNode !== 'unknown') {
            edges.push({from: node, to: nextNode})
          }
        }
      }
    })

    const activeNode = currentIndex >= 0 && currentIndex < events.length 
      ? events[currentIndex].node 
      : null

    let diagram = 'graph TD\\n'
    diagram += '  START([START])\\n'
    
    nodes.forEach(node => {
      const isActive = node === activeNode
      const style = isActive ? ':::active' : ''
      diagram += `  ${node}[${node}]${style}\\n`
    })
    
    const firstNode = Array.from(nodes)[0]
    if (firstNode) {
      diagram += `  START --> ${firstNode}\\n`
    }
    
    const uniqueEdges = [...new Map(edges.map(e => [`${e.from}-${e.to}`, e])).values()]
    uniqueEdges.forEach(edge => {
      diagram += `  ${edge.from} --> ${edge.to}\\n`
    })
    
    diagram += '\\n  classDef active fill:#10b981,stroke:#059669,stroke-width:3px,color:#000,font-weight:bold\\n'
    
    setMermaidDef(diagram)
  }, [events, currentIndex])

  useEffect(() => {
    if (!mermaidDef || !containerRef.current) return

    const render = async () => {
      try {
        containerRef.current.innerHTML = ''
        const { svg } = await mermaid.render('mermaid-graph', mermaidDef)
        containerRef.current.innerHTML = svg
      } catch (err) {
        console.error('Mermaid render error:', err)
      }
    }

    render()
  }, [mermaidDef])

  if (!events || events.length === 0) {
    return (
      <div className="content-centered">
        <div className="empty-state">
          <Workflow className="w-16 h-16" />
          <p>Waiting for workflow execution...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="mermaid-container">
      <div ref={containerRef}></div>
    </div>
  )
}
