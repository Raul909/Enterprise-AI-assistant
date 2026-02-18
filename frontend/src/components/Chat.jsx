import { useState, useRef, useEffect } from 'react'
import { Send, LogOut, User, Sparkles, FileText, Database, Github, Ticket } from 'lucide-react'
import { chat } from '../api'
import './Chat.css'

const toolIcons = {
  search_documents: FileText,
  query_database: Database,
  search_github: Github,
  search_jira: Ticket
}

export default function Chat({ user, onLogout }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(scrollToBottom, [messages])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await chat.send(input)
      const aiMessage = {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
        tools: response.data.tools_used
      }
      setMessages(prev => [...prev, aiMessage])
    } catch (err) {
      const errorMessage = {
        role: 'error',
        content: err.response?.data?.detail || 'Failed to get response'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-container">
      <header className="chat-header">
        <div className="header-left">
          <div className="logo-small">AI</div>
          <div>
            <h2>Enterprise AI Assistant</h2>
            <p>Ask anything about your company knowledge</p>
          </div>
        </div>
        <div className="header-right">
          <div className="user-info">
            <User size={18} />
            <span>{user?.email || 'User'}</span>
            <span className="role-badge">{user?.role || 'employee'}</span>
          </div>
          <button onClick={onLogout} className="logout-btn">
            <LogOut size={18} />
          </button>
        </div>
      </header>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <Sparkles size={48} className="welcome-icon" />
            <h3>Welcome to your AI Assistant</h3>
            <p>Ask questions about documents, databases, GitHub, or Jira</p>
            <div className="example-queries">
              <button onClick={() => setInput('What are the company vacation policies?')}>
                Company policies
              </button>
              <button onClick={() => setInput('Show me recent pull requests')}>
                Recent PRs
              </button>
              <button onClick={() => setInput('What are the open critical bugs?')}>
                Critical bugs
              </button>
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.role === 'assistant' && (
              <div className="message-avatar ai">AI</div>
            )}
            {msg.role === 'user' && (
              <div className="message-avatar user">
                <User size={16} />
              </div>
            )}
            <div className="message-content">
              <div className="message-text">{msg.content}</div>
              {msg.tools && msg.tools.length > 0 && (
                <div className="tools-used">
                  <span className="tools-label">Tools used:</span>
                  {msg.tools.map((tool, i) => {
                    const Icon = toolIcons[tool] || FileText
                    return (
                      <span key={i} className="tool-badge">
                        <Icon size={14} />
                        {tool.replace(/_/g, ' ')}
                      </span>
                    )
                  })}
                </div>
              )}
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources">
                  <span className="sources-label">Sources:</span>
                  {msg.sources.map((src, i) => (
                    <div key={i} className="source-item">
                      <FileText size={14} />
                      {src}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-avatar ai">AI</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me anything..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          <Send size={20} />
        </button>
      </form>
    </div>
  )
}
