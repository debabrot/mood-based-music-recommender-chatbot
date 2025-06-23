import React, { useState, useRef, useEffect } from 'react';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const [sessionId, setSessionId] = useState(null); // NEW

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    try {
      const requestBody = {
        message: currentInput,
        ...(sessionId && { session_id: sessionId })  // Include session ID if it exists
      };

      const response = await fetch('https://3anz8jfjij.execute-api.eu-west-1.amazonaws.com/prod/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      // If session_id is returned, store it
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }

      const botMessage = { sender: 'bot', text: data.response || 'No response' };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      setMessages(prev => [...prev, { sender: 'bot', text: 'Error connecting to backend.' }]);
    } finally {
      setIsLoading(false);
      // Refocus input
      setTimeout(() => {
        const textarea = document.querySelector('textarea');
        if (textarea) textarea.focus();
      }, 100);
    }
  };


  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{
      maxWidth: '600px',
      margin: '20px auto',
      height: '80vh',
      display: 'flex',
      flexDirection: 'column',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      border: '1px solid #e1e5e9',
      borderRadius: '12px',
      backgroundColor: '#ffffff',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
      position: 'relative',
      left: '50%',
      transform: 'translateX(-50%)'
    }}>
      {/* Header */}
      <div style={{
        padding: '20px',
        borderBottom: '1px solid #e1e5e9',
        backgroundColor: '#f8f9fa',
        borderRadius: '12px 12px 0 0'
      }}>
        <h2 style={{
          margin: 0,
          fontSize: '20px',
          fontWeight: '600',
          color: '#2c3e50',
          textAlign: 'center'
        }}>
          🎵 Mood-Based Music Chat
        </h2>
      </div>

      {/* Messages Container */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        backgroundColor: '#fafbfc'
      }}>
        {messages.length === 0 && (
          <div style={{
            textAlign: 'center',
            color: '#6c757d',
            fontStyle: 'italic',
            margin: 'auto'
          }}>
            Start a conversation about your music preferences!
          </div>
        )}
        
        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start'
            }}
          >
            <div style={{
              maxWidth: '75%',
              padding: '12px 16px',
              borderRadius: '18px',
              backgroundColor: msg.sender === 'user' ? '#007bff' : '#ffffff',
              color: msg.sender === 'user' ? '#ffffff' : '#2c3e50',
              border: msg.sender === 'bot' ? '1px solid #e1e5e9' : 'none',
              fontSize: '14px',
              lineHeight: '1.4',
              wordWrap: 'break-word'
            }}>
              <div style={{
                fontSize: '11px',
                fontWeight: '600',
                marginBottom: '4px',
                opacity: 0.8,
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                {msg.sender === 'user' ? 'You' : 'Bot'}
              </div>
              {msg.text}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div style={{
            display: 'flex',
            justifyContent: 'flex-start'
          }}>
            <div style={{
              maxWidth: '75%',
              padding: '12px 16px',
              borderRadius: '18px',
              backgroundColor: '#ffffff',
              border: '1px solid #e1e5e9',
              fontSize: '14px',
              color: '#6c757d'
            }}>
              <div style={{
                fontSize: '11px',
                fontWeight: '600',
                marginBottom: '4px',
                opacity: 0.8,
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                Bot
              </div>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}>
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: '#007bff',
                  animation: 'pulse 1.4s ease-in-out infinite both'
                }}></div>
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: '#007bff',
                  animation: 'pulse 1.4s ease-in-out 0.2s infinite both'
                }}></div>
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: '#007bff',
                  animation: 'pulse 1.4s ease-in-out 0.4s infinite both'
                }}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{
        padding: '20px',
        borderTop: '1px solid #e1e5e9',
        backgroundColor: '#ffffff',
        borderRadius: '0 0 12px 12px'
      }}>
        <div style={{
          display: 'flex',
          gap: '10px',
          alignItems: 'flex-end'
        }}>
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type your message here..."
            disabled={isLoading}
            autoFocus
            style={{
              flex: 1,
              minHeight: '44px',
              maxHeight: '120px',
              padding: '12px 16px',
              border: '1px solid #e1e5e9',
              borderRadius: '22px',
              resize: 'none',
              fontSize: '14px',
              fontFamily: 'inherit',
              outline: 'none',
              backgroundColor: isLoading ? '#f8f9fa' : '#ffffff',
              color: '#2c3e50',
              transition: 'border-color 0.2s ease',
              boxSizing: 'border-box'
            }}
            onFocus={e => e.target.style.borderColor = '#007bff'}
            onBlur={e => e.target.style.borderColor = '#e1e5e9'}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            style={{
              minWidth: '44px',
              height: '44px',
              borderRadius: '22px',
              border: 'none',
              backgroundColor: input.trim() && !isLoading ? '#007bff' : '#e1e5e9',
              color: '#ffffff',
              cursor: input.trim() && !isLoading ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '16px',
              transition: 'all 0.2s ease',
              boxSizing: 'border-box'
            }}
            onMouseEnter={e => {
              if (input.trim() && !isLoading) {
                e.target.style.backgroundColor = '#0056b3';
              }
            }}
            onMouseLeave={e => {
              if (input.trim() && !isLoading) {
                e.target.style.backgroundColor = '#007bff';
              }
            }}
          >
            {isLoading ? '...' : '→'}
          </button>
        </div>
      </div>

      <style jsx>{`
        @keyframes pulse {
          0%, 80%, 100% {
            transform: scale(0);
            opacity: 0.5;
          }
          40% {
            transform: scale(1);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};

export default Chat;