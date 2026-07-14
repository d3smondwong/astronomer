'use client';

import { useState, useRef, useEffect } from 'react';
import { Card, Input, Button, Avatar as AntAvatar, Spin } from 'antd';
import { Send, Bot, User as UserIcon } from 'lucide-react';
import { palette } from '@/lib/theme';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function AIOraclePage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Welcome to the AI Oracle. I am here to provide insights based on Bazi wisdom and ancient Chinese metaphysics. Feel free to ask me questions about your destiny, fortune, career, relationships, or any aspect of life you'd like guidance on.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch('/api/oracle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || "I apologize, but I'm unable to provide guidance at this moment. Please try again.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I apologize, but I encountered an error. Please try again later.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="h-full flex flex-col p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-semibold mb-2 font-serif text-gold-deep">AI Oracle Chat</h1>
        <p className="font-serif italic text-bronze-muted/70">Ask the oracle for guidance on your Bazi chart and life path</p>
      </div>

      <Card className="flex-1 flex flex-col border border-gold-deep/10" style={{ background: palette.parchment }}>
        <div
          className="flex-1 overflow-auto space-y-4 p-4 mb-4"
          ref={messagesEndRef}
        >
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' && (
                <div className="flex-shrink-0">
                  <AntAvatar
                    size={32}
                    icon={<Bot className="w-4 h-4" />}
                    style={{ backgroundColor: palette.goldDeep }}
                  />
                </div>
              )}

              <div
                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  message.role === 'user'
                    ? 'gold-gradient text-white'
                    : 'bg-gold-deep/5 border border-gold-deep/10 text-bronze-muted'
                }`}
              >
                <p className="text-sm leading-relaxed">{message.content}</p>
              </div>

              {message.role === 'user' && (
                <div className="flex-shrink-0">
                  <AntAvatar
                    size={32}
                    icon={<UserIcon className="w-4 h-4" />}
                    style={{ backgroundColor: palette.goldDeep }}
                  />
                </div>
              )}
            </div>
          ))}

          {isTyping && (
            <div className="flex gap-3 justify-start">
              <div className="flex-shrink-0">
                <AntAvatar
                  size={32}
                  icon={<Bot className="w-4 h-4" />}
                  style={{ backgroundColor: palette.goldDeep }}
                />
              </div>
              <div className="bg-gold-deep/5 border border-gold-deep/10 px-4 py-2 rounded-lg">
                <Spin size="small" />
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-gold-deep/10 pt-4 flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onPressEnter={handleSend}
            placeholder="Ask the oracle..."
            disabled={isTyping}
            size="large"
            className="bazi-input"
          />
          <Button
            icon={<Send className="w-4 h-4" />}
            onClick={handleSend}
            loading={isTyping}
            size="large"
            className="gold-gradient"
            style={{ color: 'white', border: 'none' }}
          />
        </div>
      </Card>
    </div>
  );
}
