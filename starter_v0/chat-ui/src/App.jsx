import { useState, useEffect, useRef, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import * as api from './api'
import './App.css'

const PROVIDERS = [
  { id: 'openrouter', label: 'OpenRouter', defaultModel: 'openai/gpt-4o-mini' },
  { id: 'openai',    label: 'OpenAI',     defaultModel: 'gpt-4o-mini' },
  { id: 'anthropic', label: 'Anthropic',  defaultModel: 'claude-haiku-4-5-20251001' },
  { id: 'gemini',    label: 'Gemini',     defaultModel: 'gemini-3.5-flash' },
]

// ── New Conversation Modal ────────────────────────────────────────────────────
function NewConvModal({ onClose, onCreate }) {
  const [provider, setProvider] = useState('openrouter')
  const [model, setModel]       = useState('openai/gpt-4o-mini')
  const [version, setVersion]   = useState('v0')
  const [histWin, setHistWin]   = useState(5)
  const [maxRounds, setMaxRounds] = useState(4)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)

  const handleProviderChange = (p) => {
    setProvider(p)
    const found = PROVIDERS.find(x => x.id === p)
    if (found) setModel(found.defaultModel)
  }

  const handleCreate = async () => {
    setLoading(true); setError(null)
    try {
      const conv = await api.newConversation({
        provider, model: model || null,
        version, history_window: histWin, max_tool_rounds: maxRounds,
      })
      onCreate(conv)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally { setLoading(false) }
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <h2>New Conversation</h2>

        <div className="modal-field">
          <label>Provider</label>
          <select value={provider} onChange={e => handleProviderChange(e.target.value)}>
            {PROVIDERS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
          </select>
        </div>

        <div className="modal-field">
          <label>Model (leave blank for default)</label>
          <input type="text" value={model} onChange={e => setModel(e.target.value)} placeholder="default" />
        </div>

        <div className="modal-field">
          <label>Version label</label>
          <input type="text" value={version} onChange={e => setVersion(e.target.value)} placeholder="v0" />
        </div>

        <div className="modal-row">
          <div className="modal-field">
            <label>History window (turns)</label>
            <input type="number" min="0" max="50" value={histWin} onChange={e => setHistWin(+e.target.value)} />
          </div>
          <div className="modal-field">
            <label>Max tool rounds</label>
            <input type="number" min="0" max="20" value={maxRounds} onChange={e => setMaxRounds(+e.target.value)} />
          </div>
        </div>

        {error && <div style={{ color: '#fca5a5', fontSize: 12, marginTop: 6 }}>{error}</div>}

        <div className="modal-actions">
          <button className="btn-cancel" onClick={onClose}>Cancel</button>
          <button className="btn-create" onClick={handleCreate} disabled={loading}>
            {loading ? 'Creating…' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Settings bar for active conversation ─────────────────────────────────────
function SettingsBar({ conv, onApply }) {
  const [provider,   setProvider]   = useState(conv.provider)
  const [model,      setModel]      = useState(conv.model || '')
  const [version,    setVersion]    = useState(conv.version)
  const [histWin,    setHistWin]    = useState(conv.history_window)
  const [maxRounds,  setMaxRounds]  = useState(conv.max_tool_rounds)
  const [loading,    setLoading]    = useState(false)
  const dirty = provider !== conv.provider || (model || null) !== conv.model
    || version !== conv.version || histWin !== conv.history_window || maxRounds !== conv.max_tool_rounds

  const handleProviderChange = (p) => {
    setProvider(p)
    const found = PROVIDERS.find(x => x.id === p)
    if (found) setModel(found.defaultModel)
  }

  const handleApply = async () => {
    setLoading(true)
    try {
      await onApply({ provider, model: model || null, version, history_window: histWin, max_tool_rounds: maxRounds })
    } finally { setLoading(false) }
  }

  return (
    <div className="settings-bar">
      <h3>Settings</h3>

      <div className="field">
        <label>Provider</label>
        <select value={provider} onChange={e => handleProviderChange(e.target.value)}>
          {PROVIDERS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
        </select>
      </div>

      <div className="field">
        <label>Model</label>
        <input type="text" value={model} onChange={e => setModel(e.target.value)}
          style={{ width: 200 }} placeholder="default" />
      </div>

      <div className="field">
        <label>Version</label>
        <input type="text" value={version} onChange={e => setVersion(e.target.value)}
          style={{ width: 60 }} />
      </div>

      <div className="field">
        <label>History</label>
        <input type="number" min="0" max="50" value={histWin} onChange={e => setHistWin(+e.target.value)} />
      </div>

      <div className="field">
        <label>Tool rounds</label>
        <input type="number" min="0" max="20" value={maxRounds} onChange={e => setMaxRounds(+e.target.value)} />
      </div>

      {dirty && (
        <button className="btn-apply" onClick={handleApply} disabled={loading}>
          {loading ? '…' : 'Apply'}
        </button>
      )}
    </div>
  )
}

// ── Tool steps panel ─────────────────────────────────────────────────────────
function ToolSteps({ rounds }) {
  const [open, setOpen] = useState(false)
  if (!rounds || rounds.length === 0) return null

  const totalCalls = rounds.reduce((n, r) => n + (r.tool_calls?.length || 0), 0)
  if (totalCalls === 0) return null

  return (
    <div className="tool-steps">
      <button className="tool-steps-toggle" onClick={() => setOpen(o => !o)}>
        <span className="tool-steps-icon">{open ? '▾' : '▸'}</span>
        {totalCalls} tool call{totalCalls !== 1 ? 's' : ''}
        {rounds.length > 1 ? ` across ${rounds.length} rounds` : ''}
      </button>

      {open && (
        <div className="tool-steps-body">
          {rounds.map((round, ri) => (
            <div key={ri} className="tool-step-round">
              {rounds.length > 1 && (
                <div className="tool-step-round-label">Round {round.round}</div>
              )}
              {(round.tool_calls || []).map((call, ci) => {
                const result = round.tool_results?.[ci]?.result
                return (
                  <div key={ci} className="tool-step-call">
                    <div className="tool-step-header">
                      <span className="tool-step-name">🔧 {call.name}</span>
                    </div>
                    <div className="tool-step-args">
                      <span className="tool-step-label">args</span>
                      <pre>{JSON.stringify(call.args, null, 2)}</pre>
                    </div>
                    {result !== undefined && (
                      <div className="tool-step-result">
                        <span className="tool-step-label">result</span>
                        <pre>{JSON.stringify(result, null, 2).slice(0, 600)}{JSON.stringify(result, null, 2).length > 600 ? '\n…' : ''}</pre>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Message bubble ────────────────────────────────────────────────────────────
function Message({ msg }) {
  return (
    <div className={`msg ${msg.role}`}>
      {msg.rounds?.length > 0 && <ToolSteps rounds={msg.rounds} />}

      <div className="msg-bubble">
        {msg.role === 'assistant'
          ? <ReactMarkdown>{msg.content}</ReactMarkdown>
          : msg.content}
      </div>

      {msg.status && (
        <div className="msg-meta">
          <span className={`status-badge status-${msg.status}`}>{msg.status}</span>
        </div>
      )}
    </div>
  )
}

// ── Chat area ─────────────────────────────────────────────────────────────────
function ChatArea({ conv, onSettingsApply }) {
  const [messages, setMessages]   = useState([])
  const [input,    setInput]      = useState('')
  const [sending,  setSending]    = useState(false)
  const [error,    setError]      = useState(null)
  const bottomRef = useRef(null)

  // Load existing turns when conversation changes
  useEffect(() => {
    const load = async () => {
      try {
        const full = await api.getConversation(conv.id)
        const msgs = []
        for (const turn of full.turns || []) {
          msgs.push({ role: 'user', content: turn.user })
          if (turn.assistant_text) {
            msgs.push({
              role: 'assistant', content: turn.assistant_text,
              status: turn.status, rounds: turn.rounds, tool_events: turn.tool_events,
            })
          } else if (turn.error) {
            msgs.push({ role: 'error', content: turn.error })
          }
        }
        setMessages(msgs)
      } catch { /* ignore */ }
    }
    load()
    setError(null)
  }, [conv.id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  const send = async () => {
    const text = input.trim()
    if (!text || sending) return
    setInput('')
    setError(null)
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setSending(true)
    try {
      const res = await api.sendMessage(conv.id, text)
      setMessages(prev => [...prev, {
        role: 'assistant', content: res.assistant_text,
        status: res.status, rounds: res.rounds, tool_events: res.tool_events,
      }])
    } catch (e) {
      const detail = e.response?.data?.detail || e.message
      setError(detail)
      setMessages(prev => [...prev, { role: 'error', content: detail }])
    } finally { setSending(false) }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <>
      <SettingsBar conv={conv} onApply={onSettingsApply} />

      <div className="messages">
        {messages.length === 0 && (
          <div className="empty-state">
            <h2>Start chatting</h2>
            <p>{conv.provider} · {conv.model || 'default'}</p>
          </div>
        )}
        {messages.map((msg, i) => <Message key={i} msg={msg} />)}
        {sending && (
          <div className="typing-indicator">
            <div className="typing-dot" />
            <div className="typing-dot" />
            <div className="typing-dot" />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="input-bar">
        <textarea
          rows={3}
          placeholder="Send a message… (Enter to send, Shift+Enter for newline)"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          disabled={sending}
        />
        <button className="btn-send" onClick={send} disabled={sending || !input.trim()}>
          ↑
        </button>
      </div>
    </>
  )
}

// ── App root ──────────────────────────────────────────────────────────────────
export default function App() {
  const [conversations, setConversations] = useState([])
  const [activeId,      setActiveId]      = useState(null)
  const [showModal,     setShowModal]     = useState(false)
  const [theme,         setTheme]         = useState(() => localStorage.getItem('theme') || 'dark')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark')

  const activeConv = conversations.find(c => c.id === activeId) || null

  const refreshList = useCallback(async () => {
    try { setConversations(await api.listConversations()) } catch { /* backend not up yet */ }
  }, [])

  useEffect(() => { refreshList() }, [refreshList])

  const handleCreate = (conv) => {
    setConversations(prev => [conv, ...prev])
    setActiveId(conv.id)
    setShowModal(false)
  }

  const handleDelete = async (e, id) => {
    e.stopPropagation()
    if (!confirm('Delete this conversation?')) return
    try {
      await api.deleteConversation(id)
      setConversations(prev => prev.filter(c => c.id !== id))
      if (activeId === id) setActiveId(null)
    } catch (err) { alert(err.response?.data?.detail || err.message) }
  }

  const handleSettingsApply = async (settings) => {
    // Re-create the conversation with new settings (history is lost on provider/model change)
    try {
      const conv = await api.newConversation(settings)
      setConversations(prev => [conv, ...prev.filter(c => c.id !== activeId)])
      setActiveId(conv.id)
    } catch (e) { alert(e.response?.data?.detail || e.message) }
  }

  const fmtMeta = (c) => `${c.provider} · ${c.turn_count} turn${c.turn_count !== 1 ? 's' : ''}`

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>Conversations</h2>
          <button className="btn-theme" onClick={toggleTheme} title="Toggle theme">
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
          <button className="btn-new" onClick={() => setShowModal(true)}>+ New</button>
        </div>
        <div className="conv-list">
          {conversations.length === 0 && (
            <div style={{ padding: '14px', fontSize: 12, color: '#555', textAlign: 'center' }}>
              No conversations yet
            </div>
          )}
          {conversations.map(c => (
            <div key={c.id} className={`conv-item ${c.id === activeId ? 'active' : ''}`}
              onClick={() => setActiveId(c.id)}>
              <div className="conv-item-text">
                <div className="conv-title">{c.title}</div>
                <div className="conv-meta">{fmtMeta(c)}</div>
              </div>
              <button className="btn-delete" onClick={e => handleDelete(e, c.id)} title="Delete">✕</button>
            </div>
          ))}
        </div>
      </aside>

      {/* Main panel */}
      <main className="main">
        {activeConv ? (
          <ChatArea
            key={activeConv.id}
            conv={activeConv}
            onSettingsApply={handleSettingsApply}
          />
        ) : (
          <div className="no-conv">
            <h2>Research Agent</h2>
            <p>Select a conversation or create a new one</p>
          </div>
        )}
      </main>

      {showModal && <NewConvModal onClose={() => setShowModal(false)} onCreate={handleCreate} />}
    </div>
  )
}
