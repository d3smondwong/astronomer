'use client';

import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Bot, User as UserIcon } from 'lucide-react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

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
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
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

    // Simulate AI response (in a real app, this would call an API)
    setTimeout(() => {
      const response = generateOracleResponse(input);
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const generateOracleResponse = (question: string): string => {
    const lowerQuestion = question.toLowerCase();

    // Simple pattern matching for demonstration
    if (lowerQuestion.includes('career') || lowerQuestion.includes('job') || lowerQuestion.includes('work')) {
      return "In matters of career, the ancient wisdom teaches us that success comes from aligning with our elemental nature. Your strongest element should guide your professional path. Metal types excel in structured environments, Water types in creative fields, Wood types in growth-oriented roles, Fire types in leadership, and Earth types in nurturing professions. Consider what brings you both challenge and joy.";
    } else if (lowerQuestion.includes('relationship') || lowerQuestion.includes('love') || lowerQuestion.includes('partner')) {
      return "Relationships flourish when there is elemental harmony. The Day Pillar reveals your approach to partnerships. Those with strong Fire energy bring passion, Water brings depth, Earth brings stability, Metal brings loyalty, and Wood brings flexibility. Understanding both your nature and your partner's elements is key to lasting harmony.";
    } else if (lowerQuestion.includes('wealth') || lowerQuestion.includes('money') || lowerQuestion.includes('fortune')) {
      return "Wealth flows along the channels of your favorable elements. When you engage in activities that strengthen your lucky elements, prosperity naturally follows. The ancient masters taught that wealth is not forced but cultivated, like a garden that needs the right conditions to flourish. Align your endeavors with your chart's guidance.";
    } else if (lowerQuestion.includes('health') || lowerQuestion.includes('wellness')) {
      return "Health in Bazi philosophy is about elemental balance. When one element is too strong or too weak, disharmony manifests in the physical body. Pay attention to the elements that are imbalanced in your chart. Strengthen weak elements through colors, directions, foods, and activities associated with those elements.";
    } else if (lowerQuestion.includes('lucky') || lowerQuestion.includes('favorable')) {
      return "Your lucky elements are the keys to enhancing your fortune. Incorporate these elements into your daily life through colors, directions, materials, and career choices. The more you align with your favorable elements, the more opportunities and positive energy will flow to you naturally.";
    } else {
      return "The universe speaks in cycles and patterns. Your question touches upon the eternal dance of yin and yang, the interplay of the five elements. Remember that destiny is not fixed but rather a path illuminated by choices. Your Bazi chart reveals tendencies and potential, but your will shapes the outcome. Seek balance in all things, and harmony will follow.";
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="border-b px-6 py-4 bg-card">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Bot className="w-6 h-6 text-primary" />
          AI Oracle Chat
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Seek wisdom from the ancient art of Bazi fortune telling
        </p>
      </div>

      <ScrollArea className="flex-1 p-6" ref={scrollRef}>
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 ${
                message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
            >
              <Avatar className={message.role === 'user' ? 'bg-primary' : 'bg-secondary'}>
                <AvatarFallback>
                  {message.role === 'user' ? (
                    <UserIcon className="w-5 h-5" />
                  ) : (
                    <Bot className="w-5 h-5" />
                  )}
                </AvatarFallback>
              </Avatar>

              <Card className={`flex-1 ${message.role === 'user' ? 'bg-primary text-primary-foreground' : ''}`}>
                <CardContent className="p-4">
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">
                    {message.content}
                  </p>
                  <p className={`text-xs mt-2 ${
                    message.role === 'user' ? 'text-primary-foreground/70' : 'text-muted-foreground'
                  }`}>
                    {message.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </CardContent>
              </Card>
            </div>
          ))}

          {isTyping && (
            <div className="flex gap-4">
              <Avatar className="bg-secondary">
                <AvatarFallback>
                  <Bot className="w-5 h-5" />
                </AvatarFallback>
              </Avatar>
              <Card>
                <CardContent className="p-4">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></span>
                    <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:0.2s]"></span>
                    <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:0.4s]"></span>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="border-t p-4 bg-card">
        <div className="max-w-3xl mx-auto flex gap-2">
          <Input
            placeholder="Ask the oracle..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            disabled={isTyping}
          />
          <Button onClick={handleSend} disabled={isTyping || !input.trim()}>
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Sample Questions */}
      {messages.length === 1 && (
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl px-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-center">Try asking...</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 sm:grid-cols-2">
                <Button
                  variant="outline"
                  className="justify-start text-left h-auto py-3"
                  onClick={() => setInput("What career path suits my element?")}
                >
                  What career path suits my element?
                </Button>
                <Button
                  variant="outline"
                  className="justify-start text-left h-auto py-3"
                  onClick={() => setInput("How can I improve my luck?")}
                >
                  How can I improve my luck?
                </Button>
                <Button
                  variant="outline"
                  className="justify-start text-left h-auto py-3"
                  onClick={() => setInput("What should I know about relationships?")}
                >
                  What should I know about relationships?
                </Button>
                <Button
                  variant="outline"
                  className="justify-start text-left h-auto py-3"
                  onClick={() => setInput("Tell me about wealth and prosperity")}
                >
                  Tell me about wealth and prosperity
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
