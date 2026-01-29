import { useState, useEffect, useRef } from 'react'

export function useWebSocket(url) {
  const [events, setEvents] = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState(null)
  const [graphDef, setGraphDef] = useState(null)
  const wsRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected')
      setIsConnected(true)
      setError(null)
    }

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data)
        console.log('Received:', data)

        if (data.type === 'history') {
          setEvents(data.data || [])
        } else if (data.type === 'update') {
          setEvents((prev) => [...prev, data.data])
        } else if (data.type === 'graph_def') {
          setGraphDef(data.data)
        }
      } catch (err) {
        console.error('Failed to parse message:', err)
      }
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
      setError('Connection error')
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setIsConnected(false)
    }

    // Ping every 30 seconds to keep connection alive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping')
      }
    }, 30000)

    return () => {
      clearInterval(pingInterval)
      ws.close()
    }
  }, [url])

  return { events, graphDef, isConnected, error }
}
