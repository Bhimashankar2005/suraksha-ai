"use client";

import React, { useState, useEffect } from "react";
import {
  Mic,
  MicOff,
  PhoneCall,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  FileAudio,
  UploadCloud,
  ArrowRight,
  Radio,
  Play,
  RotateCcw,
  Sparkles,
  Volume2
} from "lucide-react";
import { API_BASE_URL, analyzeMediaAuthenticity } from "@/lib/api";

const VOICE_SCENARIO_PRESETS = [
  {
    title: "Fake Police / Digital Arrest Threat",
    category: "DIGITAL_ARREST",
    text: "This is Inspector Vijay Rathore from Crime Branch Cyber Cell. An illegal courier in your name containing passports and narcotics was intercepted. A digital arrest warrant is issued. Stay on this WhatsApp call and transfer security bail money immediately."
  },
  {
    title: "Electricity Power Cut Extortion",
    category: "UTILITY_CUTOFF",
    text: "URGENT WARNING: Your domestic electricity connection will be cut off tonight at 9:30 PM by the electricity board due to pending updates. Immediately call our power officer at 9822334455 to avoid disconnection."
  },
  {
    title: "Grandchild Hospital Emergency",
    category: "RELATIVE_EMERGENCY",
    text: "Grandpa, it's me Rahul! I got into a terrible car accident in Delhi and the police have detained me. The hospital needs Rs 45,000 right now for surgery. Please send it to this doctor's UPI immediately, please don't tell mom!"
  },
  {
    title: "Bank KYC & Debit Card Block",
    category: "BANK_KYC",
    text: "Dear customer, your bank debit card and NetBanking services have been blocked due to unverified KYC. I am calling from head office. Please read out the 6-digit verification OTP received on your phone right now to unfreeze your account."
  }
];

export default function VoiceAnalysisPage() {
  const [activeTab, setActiveTab] = useState<"transcript" | "audio">("transcript");

  // Transcript state
  const [transcript, setTranscript] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [analyzingTranscript, setAnalyzingTranscript] = useState(false);
  const [transcriptResult, setTranscriptResult] = useState<any>(null);
  const [transcriptError, setTranscriptError] = useState<string | null>(null);

  // Audio file state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [analyzingAudio, setAnalyzingAudio] = useState(false);
  const [audioResult, setAudioResult] = useState<any>(null);
  const [audioError, setAudioError] = useState<string | null>(null);

  // Escalation state
  const [escalating, setEscalating] = useState(false);
  const [escalatedCode, setEscalatedCode] = useState<string | null>(null);

  // Speech Recognition setup (Web Speech API)
  const toggleSpeechRecognition = () => {
    if (typeof window === "undefined") return;
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser. Please type or paste what the caller said.");
      return;
    }

    if (isRecording) {
      setIsRecording(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-IN";

      recognition.onstart = () => {
        setIsRecording(true);
      };

      recognition.onresult = (event: any) => {
        let currentText = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          currentText += event.results[i][0].transcript;
        }
        setTranscript((prev) => (prev ? prev + " " + currentText : currentText));
      };

      recognition.onerror = (err: any) => {
        console.error("Speech recognition error:", err);
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognition.start();
    } catch (e) {
      console.error(e);
      setIsRecording(false);
    }
  };

  const handleAnalyzeTranscript = async () => {
    if (!transcript.trim()) return;
    setTranscriptError(null);
    setTranscriptResult(null);
    setEscalatedCode(null);
    setAnalyzingTranscript(true);

    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE_URL}/scam/scan`, {
        method: "POST",
        headers,
        body: JSON.stringify({ content: transcript.trim() }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to analyze speech transcript.");
      }
      const data = await res.json();
      setTranscriptResult(data);
    } catch (err: any) {
      setTranscriptError(err.message || "Failed to analyze speech transcript.");
    } finally {
      setAnalyzingTranscript(false);
    }
  };

  const handleAnalyzeAudio = async () => {
    if (!selectedFile) return;
    setAudioError(null);
    setAudioResult(null);
    setAnalyzingAudio(true);

    try {
      const res = await analyzeMediaAuthenticity(selectedFile);
      setAudioResult(res);
    } catch (err: any) {
      setAudioError(err.message || "Failed to analyze audio recording.");
    } finally {
      setAnalyzingAudio(false);
    }
  };

  const handleEscalateThreat = async () => {
    if (!transcriptResult?.id) return;
    setEscalating(true);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE_URL}/scam/report`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          scan_id: transcriptResult.id,
          target_value: "Suspicious Voice Call",
          custom_description: `Fraudulent voice call detected: ${transcript.substring(0, 150)}...`,
          region: "Pan-India"
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to report threat.");
      }
      const rep = await res.json();
      setEscalatedCode(rep.report_code);
    } catch (err: any) {
      alert("Failed to escalate: " + err.message);
    } finally {
      setEscalating(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <PhoneCall className="w-7 h-7 text-cyan-400" />
          Voice & Call Scam Forensics Analyzer
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Detect voice scams, digital arrest coercion, cloned relative voices, and fake official threats.
        </p>
      </div>

      {/* Emergency Golden Hour Hotline */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-red-950/80 via-slate-900 to-slate-900 border border-red-800/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-red-600 flex items-center justify-center text-white font-bold shrink-0 shadow-lg shadow-red-600/30">
            1930
          </div>
          <div>
            <h3 className="text-sm font-bold text-red-200">Encountered an extortion call or lost funds?</h3>
            <p className="text-xs text-slate-400">
              Never transfer money during a call. Dial 1930 immediately or lodge on cybercrime.gov.in.
            </p>
          </div>
        </div>
        <a
          href="tel:1930"
          className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold text-xs shrink-0 flex items-center gap-2 shadow-md shadow-red-600/20 transition-all"
        >
          <PhoneCall className="w-4 h-4" />
          Call 1930 Now
        </a>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-3 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("transcript")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-xs transition-all ${
            activeTab === "transcript"
              ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
              : "text-slate-400 hover:text-slate-200 bg-slate-900"
          }`}
        >
          <Mic className="w-4 h-4" />
          Live Voice & Call Transcript Scanner
        </button>
        <button
          onClick={() => setActiveTab("audio")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-xs transition-all ${
            activeTab === "audio"
              ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
              : "text-slate-400 hover:text-slate-200 bg-slate-900"
          }`}
        >
          <FileAudio className="w-4 h-4" />
          Audio Deepfake & Synthetic Voice Scanner
        </button>
      </div>

      {activeTab === "transcript" ? (
        <div className="space-y-6">
          {/* Presets */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              Common Threat Scenarios (Click to test):
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {VOICE_SCENARIO_PRESETS.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => setTranscript(p.text)}
                  className="p-3 text-left rounded-xl bg-slate-900 hover:bg-slate-850 border border-slate-800 hover:border-cyan-500/50 transition-all text-xs space-y-1"
                >
                  <div className="font-bold text-slate-200 flex items-center justify-between">
                    <span>{p.title}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-cyan-300">
                      {p.category}
                    </span>
                  </div>
                  <p className="text-slate-400 line-clamp-2 text-[11px]">{p.text}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Input Box */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-300">
                Call Dialogue / Spoken Narrative
              </label>
              <button
                type="button"
                onClick={toggleSpeechRecognition}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  isRecording
                    ? "bg-red-600 text-white animate-pulse"
                    : "bg-slate-800 hover:bg-slate-700 text-cyan-400"
                }`}
              >
                {isRecording ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
                {isRecording ? "Listening... (Click to stop)" : "Dictate with Mic"}
              </button>
            </div>

            <textarea
              rows={4}
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              placeholder="Paste or speak what the caller told you... (e.g. demanding bail, threatening electricity cutoff, asking for OTP, claiming to be police)"
              className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl p-4 text-sm text-slate-100 placeholder-slate-600 focus:outline-none transition-colors"
            />

            <div className="flex items-center justify-between">
              <button
                onClick={() => setTranscript("")}
                className="text-xs text-slate-500 hover:text-slate-400 flex items-center gap-1"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Clear Text
              </button>
              <button
                onClick={handleAnalyzeTranscript}
                disabled={!transcript.trim() || analyzingTranscript}
                className="flex items-center gap-2 py-2.5 px-6 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm shadow-md shadow-cyan-500/20 disabled:opacity-50 transition-all"
              >
                {analyzingTranscript ? "Analyzing Call Fraud Heuristics..." : "Analyze Call Threat"}
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {transcriptError && (
            <div className="p-4 rounded-xl bg-red-950/70 border border-red-700 text-red-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{transcriptError}</span>
            </div>
          )}

          {/* Results Card */}
          {transcriptResult && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
                <div>
                  <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                    Voice Scam Assessment Verdict
                  </span>
                  <div className="flex items-center gap-3 mt-1">
                    <span
                      className={`text-2xl font-black ${
                        transcriptResult.risk_level === "CRITICAL"
                          ? "text-red-400"
                          : transcriptResult.risk_level === "HIGH"
                          ? "text-orange-400"
                          : transcriptResult.risk_level === "MEDIUM"
                          ? "text-amber-400"
                          : "text-emerald-400"
                      }`}
                    >
                      {transcriptResult.risk_level} RISK DETECTED
                    </span>
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-950 border border-slate-800 text-slate-300">
                      Score: {transcriptResult.risk_score} / 100
                    </span>
                  </div>
                </div>

                {!escalatedCode ? (
                  <button
                    onClick={handleEscalateThreat}
                    disabled={escalating}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-750 text-cyan-400 border border-slate-700 text-xs font-bold transition-all disabled:opacity-50"
                  >
                    <Radio className="w-3.5 h-3.5" />
                    {escalating ? "Reporting..." : "Escalate to Community Threats"}
                  </button>
                ) : (
                  <div className="px-4 py-2 rounded-xl bg-cyan-950 border border-cyan-800 text-cyan-300 text-xs font-bold flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                    Reported: {escalatedCode}
                  </div>
                )}
              </div>

              {/* Matched Indicators */}
              {transcriptResult.matched_indicators && transcriptResult.matched_indicators.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-bold text-slate-300">Matched Psychological & Fraud Patterns:</span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {transcriptResult.matched_indicators.map((ind: any, i: number) => (
                      <div key={i} className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                        <div className="font-bold text-amber-300">{ind.rule_name || ind.category}</div>
                        <div className="text-slate-400 text-[11px]">{ind.explanation}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4 text-cyan-400" />
                  Recommended Immediate Countermeasures:
                </span>
                <ul className="text-xs text-slate-300 space-y-1.5 list-disc pl-5">
                  {transcriptResult.recommendations?.map((r: string, i: number) => (
                    <li key={i}>{r}</li>
                  ))}
                  <li>Police and government agencies never conduct court trials or demand bail over WhatsApp video calls.</li>
                  <li>Hang up immediately. If money was transferred, call 1930 within the Golden Hour.</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Audio File Tab */
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <FileAudio className="w-5 h-5 text-cyan-400" />
              Upload Audio Clip for Deepfake Voice Forensics
            </h3>
            <p className="text-xs text-slate-400">
              Upload call recordings (.wav, .mp3, .m4a) to detect synthetic speech profiles and neural voice cloner watermarks.
            </p>

            <div className="border-2 border-dashed border-slate-800 rounded-xl p-8 text-center space-y-3 hover:border-cyan-500/50 transition-colors">
              <UploadCloud className="w-10 h-10 text-slate-500 mx-auto" />
              <div>
                <label className="cursor-pointer font-bold text-cyan-400 hover:text-cyan-300 text-sm">
                  Click to select audio file
                  <input
                    type="file"
                    accept="audio/*"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="hidden"
                  />
                </label>
                <p className="text-xs text-slate-500 mt-1">Supports WAV, MP3, M4A up to 15MB</p>
              </div>
              {selectedFile && (
                <div className="text-xs font-semibold text-emerald-400 flex items-center justify-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                </div>
              )}
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleAnalyzeAudio}
                disabled={!selectedFile || analyzingAudio}
                className="flex items-center gap-2 py-2.5 px-6 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm shadow-md shadow-cyan-500/20 disabled:opacity-50 transition-all"
              >
                {analyzingAudio ? "Analyzing Acoustic Signatures..." : "Run Voice Forensics"}
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {audioError && (
            <div className="p-4 rounded-xl bg-red-950/70 border border-red-700 text-red-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{audioError}</span>
            </div>
          )}

          {audioResult && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div>
                  <span className="text-xs text-slate-400 font-semibold uppercase">Acoustic Authenticity Score</span>
                  <div className="text-2xl font-black text-cyan-400 mt-1">
                    {audioResult.authenticity_score}% Authenticity Rating
                  </div>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-950 border border-slate-800 text-slate-300">
                  {audioResult.verdict}
                </span>
              </div>

              {audioResult.forensic_flags?.suspicious_factors && (
                <div className="space-y-2">
                  <span className="text-xs font-bold text-slate-300">Forensic Flags Detected:</span>
                  <ul className="text-xs text-amber-300 space-y-1 list-disc pl-5">
                    {audioResult.forensic_flags.suspicious_factors.map((f: string, i: number) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                </div>
              )}

              <p className="text-[11px] text-slate-500 italic border-t border-slate-800 pt-3">
                {audioResult.limitations_disclaimer}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
