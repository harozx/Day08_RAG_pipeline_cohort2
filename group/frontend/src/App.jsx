import { useState, useEffect, useRef } from 'react'
import { 
  Scale, 
  Send, 
  Trash2, 
  BookOpen, 
  Database, 
  Activity, 
  AlertCircle, 
  ExternalLink,
  ChevronDown,
  ChevronUp,
  X,
  FileText,
  User,
  Info
} from 'lucide-react'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [backendStats, setBackendStats] = useState({
    status: { gemini: 'OFFLINE', openai: 'OFFLINE', pageindex: 'FALLBACK' },
    stats: { indexed_documents: 8, total_chunks: 55, embedding_dimension: 384, indexer_status: '100% Synced' },
    vectorized_documents: { legal: [], news: [] }
  })
  
  // Custom API keys inputs state
  const [userGeminiKey, setUserGeminiKey] = useState(() => localStorage.getItem('user_gemini_key') || '')
  const [userOpenaiKey, setUserOpenaiKey] = useState(() => localStorage.getItem('user_openai_key') || '')
  const [showKeySettings, setShowKeySettings] = useState(false)

  const handleSaveKeys = () => {
    localStorage.setItem('user_gemini_key', userGeminiKey)
    localStorage.setItem('user_openai_key', userOpenaiKey)
    setShowKeySettings(false)
    alert('Đã lưu cấu hình API Key thành công! Hãy gửi tin nhắn mới để thử nghiệm.')
  }
  
  // Modals and UI Toggles
  const [activeModalSource, setActiveModalSource] = useState(null)
  const [expandedSourcesIdx, setExpandedSourcesIdx] = useState({})
  
  const chatViewportRef = useRef(null)
  const BACKEND_URL = 'http://127.0.0.1:8000'

  // Fetch backend statistics and API statuses
  const fetchStats = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/stats`)
      if (response.ok) {
        const data = await response.json()
        setBackendStats(data)
      }
    } catch (error) {
      console.error("Failed to fetch backend stats:", error)
    }
  }

  useEffect(() => {
    fetchStats()
    // Poll stats every 10s to reflect connection updates
    const interval = setInterval(fetchStats, 10000)
    return () => clearInterval(interval)
  }, [])

  // Auto-scroll to bottom of chat
  useEffect(() => {
    if (chatViewportRef.current) {
      chatViewportRef.current.scrollTop = chatViewportRef.current.scrollHeight
    }
  }, [messages, loading])

  // Clear chat history
  const handleClearHistory = () => {
    setMessages([])
    setExpandedSourcesIdx({})
  }

  // Handle suggestion click
  const handleSuggestionClick = (queryText) => {
    if (loading) return
    sendMessage(queryText)
  }

  // Send message
  const sendMessage = async (textToSend) => {
    const queryText = textToSend || inputValue.trim()
    if (!queryText || loading) return

    setInputValue('')
    setLoading(true)

    // Add user message to state
    const newUserMessage = { role: 'user', content: queryText }
    const updatedMessages = [...messages, newUserMessage]
    setMessages(updatedMessages)

    try {
      // Map React history format to API format
      const apiHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }))

      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: queryText,
          history: apiHistory,
          gemini_api_key: userGeminiKey || undefined,
          openai_api_key: userOpenaiKey || undefined
        })
      })

      if (response.ok) {
        const data = await response.json()
        // Add assistant response to state
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.answer,
          sources: data.sources,
          standaloneQuery: data.standalone_query
        }])
      } else {
        throw new Error("API returned non-200 status code")
      }
    } catch (error) {
      console.error("Error sending message:", error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `⚠️ Lỗi kết nối đến Backend: Không thể kết nối tới server tại ${BACKEND_URL}. Hãy chắc chắn rằng backend uvicorn đã được chạy.`,
        sources: [],
        standaloneQuery: queryText
      }])
    } finally {
      setLoading(false)
    }
  }

  // Toggle sources view
  const toggleSources = (index) => {
    setExpandedSourcesIdx(prev => ({
      ...prev,
      [index]: !prev[index]
    }))
  }

  // Show detailed info of a source citation in a modal popup
  const handleCitationClick = (label, messageSources = []) => {
    const normalizedLabel = label.toLowerCase()
    
    // Attempt fuzzy match on label name vs document source metadata
    let matched = messageSources.find(src => {
      const srcName = (src.metadata?.source || '').toLowerCase()
      return normalizedLabel.includes(srcName) || srcName.includes(normalizedLabel)
    })

    // Fallback: search all messages sources
    if (!matched) {
      for (const msg of messages) {
        if (msg.sources) {
          matched = msg.sources.find(src => {
            const srcName = (src.metadata?.source || '').toLowerCase()
            return normalizedLabel.includes(srcName) || srcName.includes(normalizedLabel)
          })
          if (matched) break
        }
      }
    }

    if (matched) {
      setActiveModalSource({
        title: matched.metadata?.source || 'Tài liệu trích dẫn',
        type: matched.metadata?.type || 'Văn bản pháp luật',
        score: matched.score,
        content: matched.content
      })
    } else {
      setActiveModalSource({
        title: label,
        type: 'Văn bản / Sự kiện liên quan',
        score: null,
        content: `Thông tin chi tiết về [${label}]. Hệ thống đã tham chiếu đến nguồn tài liệu này để lập luận đưa ra câu trả lời.`
      })
    }
  }

  // Markdown-like rendering + Citation Badge Injection
  const renderFormattedMessage = (messageObj) => {
    const text = messageObj.content
    const sources = messageObj.sources || []

    if (!text) return ''

    // Split text into paragraphs
    const paragraphs = text.split('\n\n')

    return paragraphs.map((para, pIdx) => {
      const trimmedPara = para.trim()
      
      // Render bullet list
      if (trimmedPara.startsWith('- ') || trimmedPara.startsWith('* ')) {
        const listItems = para.split(/\n[-*]\s+/)
        return (
          <ul key={pIdx} className="message-list" style={{ margin: '8px 0', paddingLeft: '20px' }}>
            {listItems.map((item, iIdx) => {
              // Clean leading symbol if first split contains it
              const cleanItem = iIdx === 0 ? item.replace(/^[-*]\s+/, '') : item
              return <li key={iIdx}>{renderInlineElements(cleanItem, sources)}</li>
            })}
          </ul>
        )
      }

      // Render standard paragraph
      return (
        <p key={pIdx} style={{ marginBottom: '8px', marginTop: '4px' }}>
          {renderInlineElements(trimmedPara, sources)}
        </p>
      )
    })
  }

  // Render bold text and turn brackets into clickable citation badges
  const renderInlineElements = (text, sources) => {
    const parts = text.split(/(\*\*[^*]+\*\*|\[[^\]]+\](?!\())/g)
    
    return parts.map((part, index) => {
      // Bold tags
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={index} style={{ color: '#fff', fontWeight: '700' }}>{part.slice(2, -2)}</strong>
      }
      // Citation badges
      if (part.startsWith('[') && part.endsWith(']')) {
        const label = part.slice(1, -1)
        return (
          <span 
            key={index} 
            className="source-badge"
            onClick={() => handleCitationClick(label, sources)}
            title="Nhấp để xem nguồn đối chiếu"
          >
            ⚖️ {label}
          </span>
        )
      }
      return part
    })
  }

  return (
    <div className="app-container">
      {/* 1. SIDEBAR */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <img src="https://img.icons8.com/color/120/scales.png" alt="Scales Logo" className="sidebar-logo" />
          <div className="sidebar-title-container">
            <h2>COHORT 2 — RAG</h2>
            <p className="sidebar-subtitle">Hệ thống tra cứu Luật ma túy</p>
          </div>
        </div>

        {/* API Statuses */}
        <div className="sidebar-section">
          <div className="sidebar-section-title">
            <Activity size={15} /> Trạng thái kết nối
          </div>
          <div className="status-list">
            <div className="status-item">
              <span>Gemini 2.5 Flash</span>
              <div className="status-dot-container">
                <span className={`status-dot ${backendStats.status.gemini === 'ONLINE' ? 'online' : 'offline'}`}></span>
                <span style={{ color: backendStats.status.gemini === 'ONLINE' ? '#10b981' : '#f59e0b' }}>
                  {backendStats.status.gemini}
                </span>
              </div>
            </div>
            <div className="status-item">
              <span>OpenAI (Mini Fallback)</span>
              <div className="status-dot-container">
                <span className={`status-dot ${backendStats.status.openai === 'ONLINE' ? 'online' : 'offline'}`}></span>
                <span style={{ color: backendStats.status.openai === 'ONLINE' ? '#10b981' : '#f59e0b' }}>
                  {backendStats.status.openai}
                </span>
              </div>
            </div>
            <div className="status-item">
              <span>PageIndex API</span>
              <div className="status-dot-container">
                <span className={`status-dot ${backendStats.status.pageindex === 'ACTIVE' ? 'online' : 'fallback'}`}></span>
                <span style={{ color: backendStats.status.pageindex === 'ACTIVE' ? '#10b981' : '#3b82f6' }}>
                  {backendStats.status.pageindex}
                </span>
              </div>
            </div>
          </div>
          
          {/* Custom API key configuration toggle */}
          <div style={{ marginTop: '10px' }}>
            <button 
              style={{
                width: '100%',
                background: 'rgba(99, 102, 241, 0.15)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                color: '#a5b4fc',
                borderRadius: '8px',
                padding: '6px 10px',
                fontSize: '0.8rem',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px'
              }}
              onClick={() => setShowKeySettings(!showKeySettings)}
            >
              🔑 {showKeySettings ? 'Đóng cài đặt Key' : 'Cài đặt API Key riêng'}
            </button>
            
            {showKeySettings && (
              <div style={{ 
                marginTop: '10px', 
                padding: '12px', 
                background: 'rgba(30, 41, 59, 0.4)', 
                border: '1px solid rgba(99, 102, 241, 0.2)', 
                borderRadius: '10px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                <div>
                  <label style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block', marginBottom: '4px', textAlign: 'left' }}>Gemini API Key:</label>
                  <input 
                    type="password" 
                    style={{
                      width: '100%',
                      background: '#070913',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '6px',
                      padding: '6px 8px',
                      color: 'white',
                      fontSize: '0.8rem',
                      outline: 'none'
                    }}
                    placeholder="AIzaSy..."
                    value={userGeminiKey}
                    onChange={(e) => setUserGeminiKey(e.target.value)}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block', marginBottom: '4px', textAlign: 'left' }}>OpenAI API Key:</label>
                  <input 
                    type="password" 
                    style={{
                      width: '100%',
                      background: '#070913',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '6px',
                      padding: '6px 8px',
                      color: 'white',
                      fontSize: '0.8rem',
                      outline: 'none'
                    }}
                    placeholder="sk-..."
                    value={userOpenaiKey}
                    onChange={(e) => setUserOpenaiKey(e.target.value)}
                  />
                </div>
                <button 
                  style={{
                    background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                    border: 'none',
                    color: 'white',
                    borderRadius: '6px',
                    padding: '6px 12px',
                    fontSize: '0.8rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                    marginTop: '4px'
                  }}
                  onClick={handleSaveKeys}
                >
                  Lưu cấu hình
                </button>
              </div>
            )}
          </div>
        </div>

        {/* RAG Stats */}
        <div className="sidebar-section">
          <div className="sidebar-section-title">
            <Database size={15} /> RAG System Stats
          </div>
          <div className="stat-card">
            <div className="stat-row">
              <span className="stat-label">Indexed Documents:</span>
              <span className="stat-value">{backendStats.stats.indexed_documents} files</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Total Text Chunks:</span>
              <span className="stat-value">{backendStats.stats.total_chunks} chunks</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Embedding Dim:</span>
              <span className="stat-value">{backendStats.stats.embedding_dimension} (MiniLM)</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Indexer Status:</span>
              <span className="stat-value active">{backendStats.stats.indexer_status}</span>
            </div>
          </div>
        </div>

        {/* Vectorized Documents */}
        <div className="sidebar-section">
          <div className="sidebar-section-title">
            <BookOpen size={15} /> Tài liệu đã vector
          </div>
          <div className="doc-card">
            <span className="doc-group-title">⚖️ Văn bản pháp luật (3)</span>
            <ul className="doc-list">
              {backendStats.vectorized_documents.legal?.length > 0 ? (
                backendStats.vectorized_documents.legal.map((doc, idx) => <li key={idx}>{doc}</li>)
              ) : (
                <>
                  <li>Bộ luật Hình sự 2015</li>
                  <li>Luật Phòng, chống ma túy 2021</li>
                  <li>Nghị định 105/2021/NĐ-CP</li>
                </>
              )}
            </ul>
            <span className="doc-group-title" style={{ marginTop: '8px', display: 'block' }}>📰 Tin tức báo chí (5)</span>
            <ul className="doc-list">
              {backendStats.vectorized_documents.news?.length > 0 ? (
                backendStats.vectorized_documents.news.map((doc, idx) => <li key={idx}>{doc}</li>)
              ) : (
                <>
                  <li>Chi Dân / An Tây / Trúc Phương</li>
                  <li>Diễn viên hài Hữu Tín</li>
                </>
              )}
            </ul>
          </div>
        </div>

        {/* Footer controls */}
        <div className="sidebar-footer">
          <button className="clear-btn" onClick={handleClearHistory}>
            <Trash2 size={16} />
            🧹 Clear Chat History
          </button>
          <div className="developer-info">
            Được phát triển bởi:<br />
            <span className="developer-name">Cao Văn Hảo — 2A202600874</span>
          </div>
        </div>
      </aside>

      {/* 2. MAIN CHAT AREA */}
      <main className="main-content">
        <header className="header">
          <div className="header-left">
            <img src="https://img.icons8.com/color/120/scales.png" alt="Scales Logo" className="header-icon" />
            <div>
              <h1 className="header-title-gradient">Drug Law Conversational RAG</h1>
              <p className="header-subtitle">Hỏi đáp thông minh về Luật ma túy & Nghệ sĩ vi phạm pháp luật</p>
            </div>
          </div>
        </header>

        {/* Chat Feed */}
        <div className="chat-viewport" ref={chatViewportRef}>
          {messages.length === 0 ? (
            /* Intro Screen if no chats */
            <div style={{ margin: 'auto' }}>
              <div className="intro-container">
                <h3 className="intro-title">👋 Chào mừng bạn đến với RAG Chatbot!</h3>
                <p className="intro-desc">
                  Hệ thống tích hợp kỹ thuật <b>Hybrid Search (Dense + Sparse)</b>, chấm điểm lại ứng viên bằng <b>Reranking</b>,
                  kết hợp cơ chế <b>PageIndex fallback</b> ngoại tuyến và mô hình ngôn ngữ lớn <b>Gemini 2.5 Flash</b> để
                  đưa ra câu trả lời chuẩn xác nhất kèm trích dẫn văn bản luật đối chiếu trực quan.
                </p>
                <div className="intro-features">
                  <div className="feature-box">
                    <h4>⚡ Hybrid Retrieval</h4>
                    <span className="feature-desc">Kết hợp thế mạnh tìm kiếm từ khóa chính xác BM25 và độ hiểu ngữ nghĩa của Vector Embeddings.</span>
                  </div>
                  <div className="feature-box">
                    <h4>📚 Citation Badges</h4>
                    <span className="feature-desc">Hỗ trợ trích dẫn nguồn văn bản rõ ràng đến từng Điều, Khoản của Luật hoặc đầu báo một cách chi tiết.</span>
                  </div>
                  <div className="feature-box">
                    <h4>🔄 Conversational RAG</h4>
                    <span className="feature-desc">Hỏi tiếp nối tự nhiên nhờ cơ chế Query Rewriting tự động viết lại câu hỏi theo ngữ cảnh chat lịch sử.</span>
                  </div>
                </div>
              </div>

              {/* Suggestion questions */}
              <div className="suggestions-title">
                <Info size={16} style={{ color: '#818cf8' }} />
                Câu hỏi gợi ý hỏi nhanh:
              </div>
              <div className="suggestions-grid">
                <button 
                  className="suggestion-card" 
                  onClick={() => handleSuggestionClick("Hình phạt cho tội tàng trữ trái phép chất ma tuý theo Điều 249 Bộ luật Hình sự?")}
                >
                  <span className="suggestion-icon">⚖️</span>
                  <span>Hình phạt tàng trữ ma túy theo Điều 249?</span>
                </button>
                <button 
                  className="suggestion-card" 
                  onClick={() => handleSuggestionClick("Ca sĩ Chi Dân và người mẫu An Tây bị truy tố về những tội danh gì?")}
                >
                  <span className="suggestion-icon">📰</span>
                  <span>Ca sĩ Chi Dân & An Tây bị truy tố tội gì?</span>
                </button>
                <button 
                  className="suggestion-card" 
                  onClick={() => handleSuggestionClick("Luật Phòng chống ma tuý 2021 quy định những hình thức cai nghiện nào?")}
                >
                  <span className="suggestion-icon">🏥</span>
                  <span>Hình thức cai nghiện theo luật 2021?</span>
                </button>
              </div>
            </div>
          ) : (
            /* Render Messages List */
            messages.map((msg, index) => (
              <div key={index} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                <div className={`chat-row ${msg.role}`}>
                  <div className="bubble">
                    {msg.role === 'user' ? (
                      msg.content
                    ) : (
                      <>
                        {renderFormattedMessage(msg)}
                        {msg.standaloneQuery && msg.standaloneQuery !== messages[index - 1]?.content && (
                          <div className="standalone-query-indicator">
                            🔄 Đã tối ưu câu hỏi lịch sử: "{msg.standaloneQuery}"
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>

                {/* Sources expander for bot messages */}
                {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                  <div className="sources-expander">
                    <div className="sources-header" onClick={() => toggleSources(index)}>
                      <div className="sources-header-left">
                        <BookOpen size={14} style={{ color: '#818cf8' }} />
                        <span>Nguồn thông tin đối chiếu ({msg.sources.length} tài liệu)</span>
                      </div>
                      {expandedSourcesIdx[index] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>

                    {expandedSourcesIdx[index] && (
                      <div className="sources-body">
                        {msg.sources.map((src, sIdx) => (
                          <div key={sIdx} className="source-item">
                            <div className="source-meta-row">
                              <span className="source-title">Tài liệu {sIdx + 1}: {src.metadata?.source || 'Tài liệu gốc'}</span>
                              <span className="source-tag">{src.metadata?.type || 'news'}</span>
                              <span className="source-score">Độ khớp: {src.score?.toFixed(3) || '0.000'}</span>
                            </div>
                            <div className="source-snippet">
                              "...{src.content?.trim()}..."
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}

          {/* Typing/Loader state */}
          {loading && (
            <div className="chat-row bot">
              <div className="bubble">
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <span style={{ fontSize: '0.85rem', color: '#a5b4fc', marginLeft: '6px' }}>
                    Đang tìm kiếm tài liệu pháp luật và tạo câu trả lời...
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="input-area">
          <div className="input-container">
            <input 
              type="text" 
              className="chat-input"
              placeholder="Nhập câu hỏi của bạn tại đây về Luật ma túy hoặc tin tức nghệ sĩ..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  sendMessage()
                }
              }}
              disabled={loading}
            />
            <button 
              className="send-btn"
              onClick={() => sendMessage()}
              disabled={loading || !inputValue.trim()}
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </main>

      {/* 3. MODAL POPUP FOR DETAILS */}
      {activeModalSource && (
        <div className="modal-overlay" onClick={() => setActiveModalSource(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setActiveModalSource(null)}>
              <X size={18} />
            </button>
            <div className="modal-title-row">
              <Scale size={24} style={{ color: '#818cf8' }} />
              <div>
                <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: '800', color: '#f1f5f9' }}>{activeModalSource.title}</h3>
                <span className="source-tag" style={{ marginTop: '4px', display: 'inline-block' }}>{activeModalSource.type}</span>
              </div>
            </div>
            <div className="modal-body">
              {activeModalSource.score !== null && (
                <div style={{ fontSize: '0.85rem', color: '#10b981', fontWeight: '600', marginBottom: '10px' }}>
                  Độ khớp tìm kiếm ngữ nghĩa: {activeModalSource.score?.toFixed(4)}
                </div>
              )}
              <div className="modal-snippet">
                {activeModalSource.content}
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '15px' }}>
                <button 
                  style={{
                    background: 'rgba(99, 102, 241, 0.2)',
                    border: '1px solid rgba(99, 102, 241, 0.4)',
                    color: '#a5b4fc',
                    borderRadius: '10px',
                    padding: '8px 16px',
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                  onClick={() => setActiveModalSource(null)}
                >
                  Đóng cửa sổ
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
