import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || '';

const App = () => {
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState('');
  const [serverPath, setServerPath] = useState('/Users/ashumishra/mcp/servers/terminal_server/main.py');
  const [status, setStatus] = useState({ connected: false, tools: [], server_path: '' });
  const [loading, setLoading] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await axios.get(`${API_BASE}/status`);
        setStatus(res.data);
      } catch (e) {
        console.error("Status check failed", e);
      }
    };
    checkStatus();

    const fetchHistory = async () => {
      try {
        const res = await axios.get(`${API_BASE}/history`);
        setMessages(res.data);
      } catch (e) { }
    };
    fetchHistory();
  }, []);

  const handleConnect = async () => {
    setConnecting(true);
    try {
      const res = await axios.post(`${API_BASE}/connect`, { server_path: serverPath });
      setStatus({ connected: true, tools: res.data.tools, server_path: serverPath });
    } catch (e) {
      alert("Connection failed: " + (e.response?.data?.detail || e.message));
    } finally {
      setConnecting(false);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!query.trim() || !status.connected || loading) return;

    const userMsg = { role: 'user', content: query };
    setMessages(prev => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/query`, { query });
      setMessages(prev => [...prev, res.data]);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${e.response?.data?.detail || e.message}`
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <header className="header">
        <h2>MCP Chat Interface</h2>
        <div className="status-indicator">
          <span className={`dot ${status.connected ? 'connected' : 'disconnected'}`} />
          {status.connected ? 'Connected' : 'Disconnected'}
        </div>
      </header>

      <section className="server-config">
        <input
          type="text"
          placeholder="Enter server script path (e.g., server.py)"
          value={serverPath}
          onChange={(e) => setServerPath(e.target.value)}
        />
        <button onClick={handleConnect} disabled={connecting}>
          {connecting ? 'Connecting...' : status.connected ? 'Reconnect' : 'Connect'}
        </button>
      </section>

      {status.connected && status.tools.length > 0 && (
        <div style={{ padding: '0 20px', fontSize: '12px', color: '#666' }}>
          <strong>Tools:</strong> {status.tools.join(', ')}
        </div>
      )}

      <div className="messages">
        {messages.length === 0 ? (
          <div style={{ textAlign: 'center', opacity: 0.5, marginTop: '100px' }}>
            No messages yet. Connect to a server to start chatting.
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              {msg.content}
            </div>
          ))
        )}
        {loading && (
          <div className="message assistant" style={{ fontStyle: 'italic' }}>
            Thinking...
          </div>
        )
        }
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="input-area">
        <input
          type="text"
          placeholder={status.connected ? "Type message..." : "Connect to server first..."}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={!status.connected || loading}
        />
        <button type="submit" disabled={!status.connected || !query.trim() || loading}>
          Send
        </button>
      </form>
    </div>
  );
};

export default App;
