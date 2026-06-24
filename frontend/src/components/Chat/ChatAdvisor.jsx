import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, MessageSquare, Loader2, CreditCard, HelpCircle } from 'lucide-react';

const QUICK_PROMPTS = [
  "Where did most of my money go?",
  "Show my largest transactions.",
  "How much did I spend on food?",
  "What is my savings rate?",
  "Show anomalies or duplicate charges."
];

// Lightweight custom markdown parser to render basic styling safely
const parseMarkdown = (text) => {
  if (!text) return '';
  
  // Clean up code blocks
  let parsed = text;
  
  // Line by line processing
  const lines = parsed.split('\n');
  return lines.map((line, idx) => {
    let content = line;
    
    // Header level 3
    if (content.startsWith('### ')) {
      return <h4 key={idx} className="text-sm font-bold text-white mt-3 mb-1.5">{content.substring(4)}</h4>;
    }
    // Header level 2
    if (content.startsWith('## ')) {
      return <h3 key={idx} className="text-base font-bold text-white mt-4 mb-2">{content.substring(3)}</h3>;
    }
    // Header level 1
    if (content.startsWith('# ')) {
      return <h2 key={idx} className="text-lg font-bold text-white mt-4 mb-2">{content.substring(2)}</h2>;
    }
    // Bullet list items
    if (content.startsWith('* ') || content.startsWith('- ')) {
      const bulletContent = parseInlineStyles(content.substring(2));
      return <li key={idx} className="ml-4 list-disc text-xs text-slate-300 mb-1">{bulletContent}</li>;
    }
    // Bold / italic parsing inline
    if (content.trim() === '') {
      return <div key={idx} className="h-2" />;
    }
    
    return <p key={idx} className="text-xs text-slate-300 leading-relaxed mb-2">{parseInlineStyles(content)}</p>;
  });
};

const parseInlineStyles = (text) => {
  // Regex to match bold **text**
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="font-bold text-white">{part.slice(2, -2)}</strong>;
    }
    return part;
  });
};

const ChatAdvisor = ({ token, transactions }) => {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'bot',
      text: "Hi! I am your FinSight AI Financial Advisor. Ask me anything about your uploaded transactions, monthly trends, anomalies, or savings projection forecasts!",
      references: []
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Auto-scroll chat to bottom
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (messageText) => {
    const textToSend = messageText || input;
    if (!textToSend.trim()) return;

    // Clear input
    if (!messageText) setInput('');

    // Append user message
    const userMsg = {
      id: String(Date.now()),
      sender: 'user',
      text: textToSend,
      references: []
    };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch('/api/chat/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: textToSend })
      });

      const data = await res.json();

      if (res.ok) {
        setMessages(prev => [...prev, {
          id: String(Date.now() + 1),
          sender: 'bot',
          text: data.answer,
          references: data.references || []
        }]);
      } else {
        throw new Error(data.detail || 'Query failed');
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        id: String(Date.now() + 1),
        sender: 'bot',
        text: `Error: Failed to fetch advisor response. ${err.message}`,
        references: []
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slateDark-card border border-slateDark-border rounded-none shadow-none overflow-hidden min-h-[500px]">
      
      {/* Advisor Header */}
      <div className="flex items-center gap-3 p-4 border-b border-slateDark-border bg-black shrink-0">
        <div className="flex items-center justify-center w-9 h-9 bg-slateDark-card text-white border border-slateDark-border rounded-none">
          <Bot className="w-5 h-5" />
        </div>
        <div>
          <h3 className="font-bold text-white text-sm uppercase tracking-bmw-display">FinSight AI Advisor</h3>
          <p className="text-[9px] text-emerald-400 font-bold flex items-center gap-1 uppercase tracking-wider">
            <span className="w-1.5 h-1.5 rounded-none bg-emerald-400" />
            Active & Grounded RAG Agent
          </p>
        </div>
      </div>

      {/* Messages Thread */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-3 max-w-[85%] ${
            msg.sender === 'user' ? 'ml-auto flex-row-reverse' : ''
          }`}>
            {/* Avatar icon */}
            <div className={`flex items-center justify-center w-7.5 h-7.5 rounded-none shrink-0 ${
              msg.sender === 'user' 
                ? 'bg-white text-black' 
                : 'bg-black border border-slateDark-border text-white'
            }`}>
              {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4 text-white" />}
            </div>

            {/* Content card */}
            <div className="space-y-2.5">
              <div className={`p-3 rounded-none border text-xs shadow-none leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-slateDark-cardHover border-slateDark-border text-white font-light'
                  : 'bg-black border-slateDark-border text-slate-300 font-light'
              }`}>
                {msg.sender === 'user' ? (
                  <p className="leading-relaxed font-light">{msg.text}</p>
                ) : (
                  <div>{parseMarkdown(msg.text)}</div>
                )}
              </div>

              {/* Transaction Citation Reference Cards */}
              {msg.references && msg.references.length > 0 && (
                <div className="pl-0 space-y-1.5">
                  <span className="text-[9px] uppercase font-bold text-slateDark-muted tracking-bmw-machined flex items-center gap-1.5">
                    <CreditCard className="w-3 h-3 text-white" />
                    Transaction Citations ({msg.references.length})
                  </span>
                  <div className="grid grid-cols-1 gap-1">
                    {msg.references.map((ref, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2.5 bg-black border border-slateDark-border rounded-none text-[10px] hover:border-white transition duration-200">
                        <div>
                          <p className="font-bold text-white truncate max-w-[150px] uppercase tracking-wide">{ref.description}</p>
                          <span className="text-[9px] text-slateDark-muted font-light mt-0.5 block uppercase tracking-wider">{ref.date} | {ref.category}</span>
                        </div>
                        <span className={`font-bold tracking-wider text-xs ${ref.amount >= 0 ? 'text-emerald-400' : 'text-slate-300'}`}>
                          {ref.amount >= 0 ? '+' : '-'}${Math.abs(ref.amount).toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

          </div>
        ))}
        {loading && (
          <div className="flex gap-3 max-w-[85%]">
            <div className="flex items-center justify-center w-7.5 h-7.5 rounded-none shrink-0 bg-black border border-slateDark-border text-slateDark-muted">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="flex items-center gap-2 p-3 bg-black border border-slateDark-border rounded-none text-xs text-slateDark-muted shadow-none">
              <Loader2 className="w-4 h-4 animate-spin text-white" />
              <span className="font-light uppercase tracking-wider text-[10px]">Analyzing transaction context...</span>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Suggested chips panel */}
      {transactions && transactions.length > 0 && (
        <div className="p-3 border-t border-slateDark-border bg-black shrink-0">
          <div className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-bmw-machined text-slateDark-muted mb-2">
            <Sparkles className="w-3.5 h-3.5 text-white" />
            Suggested Questions
          </div>
          <div className="flex flex-wrap gap-1.5 max-h-[70px] overflow-y-auto">
            {QUICK_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(prompt)}
                disabled={loading}
                className="text-[9px] font-bold uppercase tracking-wider px-2.5 py-1.5 bg-slateDark-card hover:bg-white border border-slateDark-border hover:border-white text-slate-300 hover:text-black rounded-none transition duration-150 disabled:opacity-50"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Chat input form */}
      <form
        onSubmit={(e) => { e.preventDefault(); handleSend(); }}
        className="flex items-center gap-2 p-4 border-t border-slateDark-border bg-black shrink-0"
      >
        <input
          type="text"
          placeholder={transactions.length === 0 ? "Upload bank statement to enable..." : "Ask your advisor..."}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading || transactions.length === 0}
          className="flex-1 bg-slateDark-card border border-slateDark-border focus:border-white rounded-none py-2.5 px-4 text-white placeholder-slateDark-muted focus:outline-none focus:ring-0 transition text-xs font-light disabled:opacity-40 disabled:cursor-not-allowed"
        />
        <button
          type="submit"
          disabled={loading || !input.trim() || transactions.length === 0}
          className="flex items-center justify-center w-10 h-10 bg-transparent hover:bg-white text-white hover:text-black border border-white rounded-none shadow-none transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed shrink-0 active:scale-95"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>

    </div>
  );
};

export default ChatAdvisor;
