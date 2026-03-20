import React, { useEffect, useRef, useState } from 'react'

interface LogFile {
  name: string
  label: string
  description?: string
}

interface LogEvent {
  success: boolean
  lines: string[]
  updated_at: string
  available_files?: LogFile[]
  error?: string
}

const TABS: { key: string; label: string; fileParam: string }[] = [
  { key: 'presales', label: '售前', fileParam: 'presales' },
  { key: 'operations', label: '运营', fileParam: 'operations' },
  { key: 'aftersales', label: '售后', fileParam: 'aftersales' },
  { key: 'app', label: '应用', fileParam: 'app' },
]

const LogTerminal: React.FC = () => {
  const [activeTab, setActiveTab] = useState('presales')
  const [lines, setLines] = useState<string[]>([])
  const [connected, setConnected] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<string>('')
  const [availableFiles, setAvailableFiles] = useState<LogFile[]>([])
  const [error, setError] = useState<string>('')
  const eventSourceRef = useRef<EventSource | null>(null)
  const bottomRef = useRef<HTMLDivElement | null>(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const logContainerRef = useRef<HTMLDivElement>(null)

  const connect = (tabKey: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }
    setLines([])
    setConnected(false)
    setError('')

    const tab = TABS.find((t) => t.key === tabKey)
    const file = tab?.fileParam || 'presales'
    const url = `/api/logs/realtime/stream?file=${encodeURIComponent(file)}&tail=200`
    const es = new EventSource(url)
    eventSourceRef.current = es

    es.onopen = () => {
      setConnected(true)
      setError('')
    }

    es.onmessage = (e: MessageEvent) => {
      try {
        const data: LogEvent = JSON.parse(e.data)
        if (!data.success) {
          setError(data.error || 'unknown error')
          return
        }
        if (data.available_files && data.available_files.length > 0) {
          setAvailableFiles(data.available_files)
        }
        if (data.lines && data.lines.length > 0) {
          setLines(data.lines)
          setLastUpdated(data.updated_at || '')
          if (autoScroll) {
            setTimeout(() => {
              bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
            }, 50)
          }
        }
      } catch {
        // ignore parse errors
      }
    }

    es.onerror = () => {
      setConnected(false)
      setError('SSE 连接中断')
      es.close()
    }
  }

  useEffect(() => {
    connect(activeTab)
    return () => {
      eventSourceRef.current?.close()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab])

  const handleClear = () => {
    setLines([])
  }

  const handleScroll = () => {
    const el = logContainerRef.current
    if (!el) return
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60
    setAutoScroll(atBottom)
  }

  const formatTime = (iso: string) => {
    if (!iso) return ''
    try {
      return iso.split('T')[1]?.slice(0, 8) || ''
    } catch {
      return ''
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-xy-bg">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-xy-border bg-xy-surface">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-xy-text-primary">实时日志</h1>
          {/* Live indicator */}
          <div className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}
            />
            <span className={`text-xs font-medium ${connected ? 'text-green-600' : 'text-gray-400'}`}>
              {connected ? 'LIVE' : 'DISCONNECTED'}
            </span>
          </div>
          {lastUpdated && (
            <span className="text-xs text-xy-text-secondary">
              更新于 {formatTime(lastUpdated)}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleClear}
            className="px-3 py-1.5 text-xs font-medium text-xy-text-secondary border border-xy-border rounded-lg hover:bg-xy-gray-50 transition-colors"
          >
            清屏
          </button>
          <label className="flex items-center gap-1.5 text-xs text-xy-text-secondary cursor-pointer">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="rounded"
            />
            自动滚动
          </label>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-xy-border bg-xy-surface px-6">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-xy-brand-500 text-xy-brand-600'
                : 'border-transparent text-xy-text-secondary hover:text-xy-text-primary hover:border-xy-border'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Log output */}
      <div
        ref={logContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto bg-[#0d1117] px-6 py-3 font-mono text-xs leading-5"
      >
        {error && (
          <div className="text-red-400 py-2">
            <span className="text-red-600">[ERROR]</span> {error}
          </div>
        )}
        {lines.length === 0 && !error && (
          <div className="text-gray-500 py-4">
            {connected ? '等待日志输出...' : '正在连接...'}
          </div>
        )}
        {lines.map((line, i) => (
          <div
            key={i}
            className={`${
              line.includes('ERROR') || line.includes('[E]')
                ? 'text-red-400'
                : line.includes('WARN') || line.includes('[W]')
                ? 'text-yellow-400'
                : line.includes('INFO') || line.includes('[I]')
                ? 'text-blue-400'
                : line.includes('DEBUG') || line.includes('[D]')
                ? 'text-gray-500'
                : 'text-gray-200'
            }`}
          >
            {line}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}

export default LogTerminal
