import React, { useState } from 'react';
import { 
  MessageSquare, 
  X, 
  Send, 
  Sparkles, 
  Bot, 
  User, 
  Lock, 
  CheckCircle2, 
  ShieldAlert
} from 'lucide-react';

export default function GroundedChatDrawer({ 
  profile, 
  userState, 
  isOpen, 
  onClose 
}) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: `Hello ${userState.userName}! I am your Apogee Grounded Assistant. I can answer questions specifically about your ${profile.role} route, prerequisite graph, or primary bottleneck.`
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  if (!isOpen) return null;

  const handleSend = (textToSend) => {
    const query = textToSend || inputValue;
    if (!query.trim()) return;

    const userMsg = { id: Date.now(), sender: 'user', text: query };
    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputValue('');
    setIsTyping(true);

    setTimeout(() => {
      let botResponse = "";

      const lower = query.toLowerCase();
      if (lower.includes('bottleneck') || lower.includes('stuck') || lower.includes('block')) {
        botResponse = `Based on your telemetry, your primary bottleneck is **${profile.bottleneck}**. You need to complete PyTorch Tensor Ops to unlock neural network architectures.`;
      } else if (lower.includes('locked') || lower.includes('why not')) {
        botResponse = `Vision Transformers (ViT) and CNN Architectures are currently **Locked** because downstream prerequisites require PyTorch Tensor Operations mastery to be **Verified** first (FR10 Unlock Rule).`;
      } else if (lower.includes('readiness') || lower.includes('confidence')) {
        botResponse = `Your current readiness is **${userState.readinessBand.min}% – ${userState.readinessBand.max}%**. Submitting proof of skill for PyTorch Tensors will narrow the uncertainty band down to ±2%.`;
      } else {
        botResponse = `I have verified your route for **${profile.role}**. You have completed ${userState.hoursCompleted} of ${userState.hoursTotal} hours across 24 sprints with zero prerequisite violations (FR1).`;
      }

      setMessages((prev) => [...prev, { id: Date.now() + 1, sender: 'bot', text: botResponse }]);
      setIsTyping(false);
    }, 800);
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-surface-container border-l border-outline-variant/60 shadow-2xl flex flex-col animate-slideLeft">
      {/* Header */}
      <div className="p-4 bg-surface-container-high border-b border-outline-variant/50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary-container text-white flex items-center justify-center border border-indigo-400/40">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-on-surface font-headline-sm">Grounded Assistant (C15)</h3>
            <span className="text-[10px] text-tertiary font-mono">Bounded to your Route Data</span>
          </div>
        </div>

        <button onClick={onClose} className="p-1.5 rounded-lg text-outline hover:text-on-surface hover:bg-surface-container-highest">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-3">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-2 text-xs leading-relaxed max-w-[88%] ${
              msg.sender === 'user' ? 'self-end flex-row-reverse' : 'self-start'
            }`}
          >
            <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
              msg.sender === 'user' ? 'bg-primary text-on-primary font-bold' : 'bg-surface-container-highest text-secondary border border-outline-variant/40'
            }`}>
              {msg.sender === 'user' ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
            </div>

            <div className={`p-3 rounded-2xl ${
              msg.sender === 'user'
                ? 'bg-primary-container text-white rounded-tr-none'
                : 'bg-surface-container-lowest text-on-surface border border-outline-variant/40 rounded-tl-none'
            }`}>
              {msg.text}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex gap-2 items-center text-xs text-outline self-start">
            <Bot className="w-4 h-4 animate-spin text-secondary" />
            <span>Consulting route telemetry...</span>
          </div>
        )}
      </div>

      {/* Suggested prompts */}
      <div className="p-2 border-t border-outline-variant/30 flex flex-wrap gap-1.5 bg-surface-container-lowest">
        {[
          "What is my primary bottleneck?",
          "Why is Vision Transformers locked?",
          "How can I narrow my readiness band?"
        ].map((prompt, i) => (
          <button
            key={i}
            onClick={() => handleSend(prompt)}
            className="text-[10px] px-2.5 py-1 rounded-full bg-surface-container-high hover:bg-surface-container-highest text-on-surface-variant border border-outline-variant/40"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="p-3 bg-surface-container-high border-t border-outline-variant/50 flex items-center gap-2">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask about your route, prerequisites..."
          className="flex-1 p-2.5 rounded-xl bg-surface-container-lowest text-on-surface text-xs border border-outline-variant/60 focus:outline-none focus:ring-1 focus:ring-primary"
        />
        <button
          onClick={() => handleSend()}
          className="p-2.5 rounded-xl bg-primary text-on-primary font-bold flex items-center justify-center hover:bg-primary/90 transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
