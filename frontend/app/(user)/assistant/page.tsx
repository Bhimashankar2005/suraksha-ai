"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Bot,
  User,
  Send,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Copy,
  Check,
  ShieldAlert,
  ShieldCheck,
  PhoneCall,
  ExternalLink,
  Sparkles,
  AlertTriangle,
  RefreshCw,
  Clock,
  Globe,
  Radio
} from "lucide-react";
import {
  sendChatMessage,
  fetchAssistantStatus,
  fetchChatResources,
  ChatMessageItem,
  ChatResponse,
  AssistantStatus,
  HelplineContact,
} from "@/lib/api";

type SupportedLang = "en" | "kn" | "hi";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  provider?: "ollama" | "deterministic_fallback";
  detectedTopic?: string;
  safetyWarning?: string | null;
  quickActions?: string[];
}

const PRESET_QUERIES: Record<SupportedLang, { label: string; query: string }[]> = {
  en: [
    {
      label: "💸 Lost UPI Money",
      query: "I lost money in a Google Pay UPI scam! What should I do immediately?",
    },
    {
      label: "🏦 Fake Bank KYC SMS",
      query: "Got an SMS saying my SBI bank account is blocked due to KYC. Is this real?",
    },
    {
      label: "🚨 Digital Arrest Threat",
      query: "Someone called on Skype in police uniform claiming a digital arrest for a drug parcel.",
    },
    {
      label: "🆔 Lock Aadhaar Biometrics",
      query: "How do I lock my Aadhaar biometrics and check fake SIM cards issued in my name?",
    },
  ],
  kn: [
    {
      label: "💸 ಯುಪಿಐ ಹಣ ವಂಚನೆ",
      query: "ನನ್ನ ಯುಪಿಐ ಹಣ ವಂಚನೆಯಾಗಿದೆ, ತಕ್ಷಣ ಹಣ ಮರಳಿ ಪಡೆಯಲು ಏನು ಮಾಡಬೇಕು?",
    },
    {
      label: "🏦 ನಕಲಿ ಕೆವೈಸಿ ಸಂದೇಶ",
      query: "ಬ್ಯಾಂಕ್ ಖಾತೆ ಬ್ಲಾಕ್ ಆಗಿದೆ ಕೆವೈಸಿ ಅಪ್ಡೇಟ್ ಮಾಡಿ ಎಂದು ಎಸ್ಎಂಎಸ್ ಬಂದಿದೆ.",
    },
    {
      label: "🚨 ಡಿಜಿಟಲ್ ಅರೆಸ್ಟ್ ಬೆದರಿಕೆ",
      query: "ಪೊಲೀಸ್ ಹೆಸರಿನಲ್ಲಿ ವಿಡಿಯೋ ಕಾಲ್ ಮಾಡಿ ಡಿಜಿಟಲ್ ಅರೆಸ್ಟ್ ಎಂದು ಬೆದರಿಸುತ್ತಿದ್ದಾರೆ.",
    },
    {
      label: "🆔 ಆಧಾರ್ ಬಯೋಮೆಟ್ರಿಕ್ ಲಾಕ್",
      query: "ಆಧಾರ್ ಬಯೋಮೆಟ್ರಿಕ್ ಲಾಕ್ ಮಾಡುವುದು ಹೇಗೆ ಮತ್ತು ನಕಲಿ ಸಿಮ್ ಪರಿಶೀಲಿಸುವುದು ಹೇಗೆ?",
    },
  ],
  hi: [
    {
      label: "💸 यूपीआई पैसे कट गए",
      query: "यूपीआई से पैसे कट गए हैं, धोखेबाज से पैसे वापस कैसे पाएं?",
    },
    {
      label: "🏦 फर्जी बैंक केवाईसी",
      query: "बैंक खाता बंद होने और केवाईसी लिंक पर क्लिक करने का मैसेज आया है।",
    },
    {
      label: "🚨 डिजिटल अरेस्ट की धमकी",
      query: "पुलिस की वर्दी में वीडियो कॉल करके डिजिटल अरेस्ट की धमकी दे रहे हैं।",
    },
    {
      label: "🆔 आधार बायोमेट्रिक लॉक",
      query: "आधार बायोमेट्रिक कैसे लॉक करें और नाम पर जारी फर्जी सिम कैसे चेक करें?",
    },
  ],
};

const WELCOME_MESSAGES: Record<SupportedLang, string> = {
  en: "Hello! I am **SURAKSHA AI**, your multilingual digital safety assistant. How can I protect you today? Ask about UPI fraud, fake bank KYC messages, digital arrest calls, or identity theft.",
  kn: "ನಮಸ್ಕಾರ! ನಾನು **ಸುರಕ್ಷಾ ಎಐ (SURAKSHA AI)**, ನಿಮ್ಮ ಡಿಜಿಟಲ್ ರಕ್ಷಣಾ ಸಹಾಯಕ. ಯುಪಿಐ ವಂಚನೆ, ನಕಲಿ ಬ್ಯಾಂಕ್ ಸಂದೇಶ, ಡಿಜಿಟಲ್ ಅರೆಸ್ಟ್ ಅಥವಾ ಸೈಬರ್ ಕಿರುಕುಳದ ಬಗ್ಗೆ ಯಾವುದೇ ಪ್ರಶ್ನೆ ಕೇಳಿ.",
  hi: "नमस्ते! मैं **सुरक्षा एआई (SURAKSHA AI)**, आपका डिजिटल सुरक्षा सहायक हूं। यूपीआई फ्रॉड, फर्जी बैंक संदेश, डिजिटल अरेस्ट या ऑनलाइन उत्पीड़न से संबंधित कोई भी सहायता मांग सकते हैं।",
};

export default function AssistantPage() {
  const [language, setLanguage] = useState<SupportedLang>("en");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome-1",
      sender: "assistant",
      text: WELCOME_MESSAGES.en,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      provider: "deterministic_fallback",
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<AssistantStatus | null>(null);
  const [resources, setResources] = useState<HelplineContact[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [speakingId, setSpeakingId] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [sensitiveWarning, setSensitiveWarning] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  // Scroll to bottom on new messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Load Assistant Status & Resources on mount
  useEffect(() => {
    fetchAssistantStatus()
      .then(setStatus)
      .catch((err) => console.error("Assistant status error:", err));

    fetchChatResources()
      .then(setResources)
      .catch((err) => console.error("Resources fetch error:", err));
  }, []);

  // Check user input for sensitive OTP / PIN patterns
  useEffect(() => {
    const sensitiveRegex = /\b(otp|pin|cvv|password|passcode)\b.*\b\d{4,6}\b|\b\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\b/i;
    if (sensitiveRegex.test(inputMessage)) {
      setSensitiveWarning(
        "⚠️ CRITICAL PRIVACY GUARD: You seem to be entering an OTP, PIN, or card number. SURAKSHA AI will NEVER ask for credentials! Please delete it before sending."
      );
    } else {
      setSensitiveWarning(null);
    }
  }, [inputMessage]);

  // Update welcome greeting when language changes
  const handleLanguageChange = (newLang: SupportedLang) => {
    setLanguage(newLang);
    setMessages((prev) => [
      ...prev,
      {
        id: `lang-change-${Date.now()}`,
        sender: "assistant",
        text: WELCOME_MESSAGES[newLang],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        provider: status?.ollama_available ? "ollama" : "deterministic_fallback",
      },
    ]);
  };

  // Send message handler
  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputMessage).trim();
    if (!query || loading) return;

    const userMessageId = `user-${Date.now()}`;
    const userMsg: Message = {
      id: userMessageId,
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage("");
    setSensitiveWarning(null);
    setLoading(true);

    try {
      const historyItems: ChatMessageItem[] = messages.slice(-6).map((m) => ({
        role: m.sender === "user" ? "user" : "assistant",
        content: m.text,
      }));

      const res: ChatResponse = await sendChatMessage(query, language, historyItems);

      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        sender: "assistant",
        text: res.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        provider: res.provider,
        detectedTopic: res.detected_topic,
        safetyWarning: res.safety_warning,
        quickActions: res.quick_actions,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: "assistant",
          text: "⚠️ Connection error: Unable to reach the assistant server. If this is an emergency, please dial **1930** immediately or visit **https://cybercrime.gov.in**.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          provider: "deterministic_fallback",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Web Speech API: Voice-to-Text
  const toggleSpeechRecognition = () => {
    if (isRecording) {
      recognitionRef.current?.stop();
      setIsRecording(false);
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.");
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = language === "kn" ? "kn-IN" : language === "hi" ? "hi-IN" : "en-IN";

      recognition.onstart = () => setIsRecording(true);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputMessage((prev) => (prev ? `${prev} ${transcript}` : transcript));
        setIsRecording(false);
      };
      recognition.onerror = (err: any) => {
        console.error("Speech recognition error:", err);
        setIsRecording(false);
      };
      recognition.onend = () => setIsRecording(false);

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error("Voice input error:", err);
      setIsRecording(false);
    }
  };

  // Web Speech API: Text-to-Speech
  const handleReadAloud = (msg: Message) => {
    if (speakingId === msg.id) {
      window.speechSynthesis.cancel();
      setSpeakingId(null);
      return;
    }

    window.speechSynthesis.cancel();
    // Clean markdown hashes/stars for clearer speech
    const cleanText = msg.text.replace(/[#*`>_]/g, "");
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = language === "kn" ? "kn-IN" : language === "hi" ? "hi-IN" : "en-IN";
    utterance.rate = 0.95;

    utterance.onend = () => setSpeakingId(null);
    utterance.onerror = () => setSpeakingId(null);

    setSpeakingId(msg.id);
    window.speechSynthesis.speak(utterance);
  };

  const copyToClipboard = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Banner & Language Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Bot className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-black text-white flex items-center gap-2">
              SURAKSHA AI Cyber Assistant
              <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                v1.0 Trilingual
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Immediate fraud guidance in English, ಕನ್ನಡ & हिन्दी • 100% Free & Open Source
            </p>
          </div>
        </div>

        {/* Language Selector & Engine Telemetry */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => handleLanguageChange("en")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                language === "en"
                  ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              English
            </button>
            <button
              onClick={() => handleLanguageChange("kn")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                language === "kn"
                  ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              ಕನ್ನಡ (Kannada)
            </button>
            <button
              onClick={() => handleLanguageChange("hi")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                language === "hi"
                  ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              हिन्दी (Hindi)
            </button>
          </div>

          {/* Engine Status Badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs">
            <span
              className={`w-2 h-2 rounded-full ${
                status?.ollama_available ? "bg-emerald-400 animate-pulse" : "bg-cyan-400"
              }`}
            />
            <span className="text-slate-300 font-medium">
              {status?.ollama_available ? "Ollama Local LLM Active" : "Deterministic Safety Rulebook"}
            </span>
          </div>
        </div>
      </div>

      {/* Main Grid: Chat Stream & Emergency Directory */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Chat Window */}
        <div className="lg:col-span-2 flex flex-col h-[650px] bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${
                  msg.sender === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {msg.sender === "assistant" && (
                  <div className="w-9 h-9 rounded-xl bg-cyan-600/30 border border-cyan-500/30 flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-5 h-5 text-cyan-400" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed ${
                    msg.sender === "user"
                      ? "bg-cyan-600 text-white rounded-tr-none shadow-md shadow-cyan-600/20"
                      : "bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none"
                  }`}
                >
                  {/* Safety Alert Banner */}
                  {msg.safetyWarning && (
                    <div className="mb-3 p-3 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs flex items-start gap-2">
                      <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
                      <span>{msg.safetyWarning}</span>
                    </div>
                  )}

                  {/* Message Content with Formatting */}
                  <div className="space-y-2 whitespace-pre-line font-sans">
                    {msg.text}
                  </div>

                  {/* Action Chips for Assistant */}
                  {msg.quickActions && msg.quickActions.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap gap-2">
                      {msg.quickActions.map((action, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-1 rounded-md bg-slate-800/80 text-cyan-300 text-[11px] font-semibold border border-slate-700/60"
                        >
                          ✓ {action}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Bubble Footer */}
                  <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-500">
                    <span>{msg.timestamp}</span>

                    {msg.sender === "assistant" && (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleReadAloud(msg)}
                          title={speakingId === msg.id ? "Stop voice" : "Read aloud"}
                          className="hover:text-cyan-400 transition-colors p-1"
                        >
                          {speakingId === msg.id ? (
                            <VolumeX className="w-3.5 h-3.5 text-cyan-400" />
                          ) : (
                            <Volume2 className="w-3.5 h-3.5" />
                          )}
                        </button>
                        <button
                          onClick={() => copyToClipboard(msg.id, msg.text)}
                          title="Copy reply"
                          className="hover:text-cyan-400 transition-colors p-1"
                        >
                          {copiedId === msg.id ? (
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {msg.sender === "user" && (
                  <div className="w-9 h-9 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0 mt-1">
                    <User className="w-5 h-5 text-slate-300" />
                  </div>
                )}
              </div>
            ))}

            {/* Thinking / Loading Animation */}
            {loading && (
              <div className="flex gap-3 justify-start">
                <div className="w-9 h-9 rounded-xl bg-cyan-600/30 border border-cyan-500/30 flex items-center justify-center shrink-0">
                  <Bot className="w-5 h-5 text-cyan-400 animate-pulse" />
                </div>
                <div className="bg-slate-950 border border-slate-800 rounded-2xl rounded-tl-none p-4 text-xs text-slate-400 flex items-center gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
                  <span>SURAKSHA AI is verifying safety protocols...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Preset Query Pills */}
          <div className="px-4 py-2 bg-slate-950/80 border-t border-slate-800/80 overflow-x-auto flex gap-2 no-scrollbar">
            {PRESET_QUERIES[language].map((preset, idx) => (
              <button
                key={idx}
                disabled={loading}
                onClick={() => handleSendMessage(preset.query)}
                className="shrink-0 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-700 hover:border-cyan-500 text-slate-300 hover:text-white text-xs transition-colors flex items-center gap-1.5"
              >
                <span>{preset.label}</span>
              </button>
            ))}
          </div>

          {/* Input & Voice Controls */}
          <div className="p-4 bg-slate-950 border-t border-slate-800 space-y-2">
            {/* Sensitive Data Alert */}
            {sensitiveWarning && (
              <div className="p-2.5 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{sensitiveWarning}</span>
              </div>
            )}

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={toggleSpeechRecognition}
                title={isRecording ? "Stop voice recording" : "Voice input"}
                className={`p-3 rounded-xl border transition-all ${
                  isRecording
                    ? "bg-rose-600 text-white border-rose-400 animate-pulse shadow-lg shadow-rose-600/30"
                    : "bg-slate-900 text-slate-300 border-slate-700 hover:text-white hover:border-cyan-500"
                }`}
              >
                {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </button>

              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder={
                  language === "kn"
                    ? "ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಇಲ್ಲಿ ಬರೆಯಿರಿ (ಉದಾ: ಯುಪಿಐ ವಂಚನೆ)..."
                    : language === "hi"
                    ? "अपना प्रश्न यहां लिखें (उदा: यूपीआई से पैसे कट गए)..."
                    : "Describe what happened (e.g., lost money in UPI scam)..."
                }
                className="flex-1 bg-slate-900 border border-slate-800 focus:border-cyan-500 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 outline-none transition-all"
              />

              <button
                onClick={() => handleSendMessage()}
                disabled={!inputMessage.trim() || loading}
                className="px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 text-white font-semibold text-sm transition-all flex items-center gap-2 shadow-lg shadow-cyan-600/20"
              >
                <Send className="w-4 h-4" />
                <span className="hidden sm:inline">Send</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right 1 Col: Official Helplines & Emergency Protocol */}
        <div className="space-y-6">
          {/* Golden Hour Urgency Protocol */}
          <div className="bg-gradient-to-br from-amber-950/40 via-slate-900 to-slate-900 border border-amber-500/30 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center gap-2.5 text-amber-400 mb-3 font-bold text-sm">
              <Clock className="w-5 h-5 animate-pulse" />
              <span>THE GOLDEN HOUR PROTOCOL</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              If you lost money in a cyber fraud, the <strong>first 2 to 3 hours</strong> are the only window to legally freeze money in the perpetrator's account before cash withdrawal.
            </p>
            <div className="mt-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
              <div className="text-[11px] text-amber-200 font-semibold mb-1">
                Emergency Action:
              </div>
              <a
                href="tel:1930"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-500 text-slate-950 font-black text-xs hover:bg-amber-400 transition-colors w-full justify-center"
              >
                <PhoneCall className="w-4 h-4" />
                CALL 1930 IMMEDIATELY
              </a>
            </div>
          </div>

          {/* Verified Official Helplines */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Verified Indian Helplines
              </h2>
              <span className="text-[10px] text-slate-400">Govt. Verified</span>
            </div>

            <div className="space-y-3">
              {resources.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-white">{item.name}</span>
                    <a
                      href={`tel:${item.number.split(" ")[0]}`}
                      className="text-xs font-black text-cyan-400 hover:underline flex items-center gap-1"
                    >
                      <PhoneCall className="w-3 h-3" />
                      {item.number}
                    </a>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed mb-2">
                    {item.description}
                  </p>
                  <div className="flex items-center justify-between text-[10px] text-slate-500">
                    <span>{item.operating_hours}</span>
                    {item.portal && (
                      <a
                        href={item.portal}
                        target="_blank"
                        rel="noreferrer"
                        className="text-cyan-400 hover:underline flex items-center gap-0.5"
                      >
                        Visit Portal <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Official Legal Disclaimer */}
            <div className="pt-2 border-t border-slate-800/80 text-[10px] text-slate-500 leading-relaxed">
              <strong>Notice</strong>: SURAKSHA AI provides educational safety guidance and threat analysis. It does not replace an official Police First Information Report (FIR) or bank dispute lodging.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

