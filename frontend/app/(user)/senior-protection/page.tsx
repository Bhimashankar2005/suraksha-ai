"use client";

import React, { useState } from "react";
import {
  UserCheck,
  Volume2,
  VolumeX,
  PhoneCall,
  AlertOctagon,
  CheckCircle,
  HelpCircle,
  Sparkles,
  ArrowRight,
  Shield,
  Zap,
  Award,
  Users,
  Eye,
  Type
} from "lucide-react";
import { explainSeniorSafety, SeniorSafetyResponse } from "@/lib/api";

const SENIOR_PRESETS = [
  {
    category: "Pension / Jeevan Pramaan",
    label: "Pension Life Certificate Update",
    language: "en",
    text: "Dear Pensioner, Your Jeevan Pramaan digital life certificate expires today. Your monthly pension of Rs 34,200 is stopped. Download PensionApp.apk immediately to update your Aadhaar biometric details or your pension account will be permanently closed."
  },
  {
    category: "Electricity Power Cutoff",
    label: "Electricity Bill Cutoff at 9:30 PM",
    language: "en",
    text: "Dear Consumer, your electricity power supply will be disconnected tonight at 9:30 PM from the main electricity office because your previous month bill was not updated. Please immediately call our electricity officer at 9823456789."
  },
  {
    category: "Kannada Pension Scam",
    label: "ಪಿಂಚಣಿ ಪರಿಶೀಲನೆ (Kannada)",
    language: "kn",
    text: "ಆತ್ಮೀಯ ಪಿಂಚಣಿದಾರರೇ, ನಿಮ್ಮ ಪಿಂಚಣಿ ಖಾತೆ ಸ್ಥಗಿತಗೊಂಡಿದೆ. ತಕ್ಷಣ ಈ ಲಿಂಕ್ ಕ್ಲಿಕ್ ಮಾಡಿ ನಿಮ್ಮ ಆಧಾರ್ ಮತ್ತು ಬ್ಯಾಂಕ್ ಖಾತೆ ಪರಿಶೀಲಿಸಿ ಇಲ್ಲವಾದರೆ ಈ ತಿಂಗಳ ಹಣ ಬರುವುದಿಲ್ಲ."
  },
  {
    category: "Hindi Electricity Scam",
    label: "बिजली बिल कनेक्शन (Hindi)",
    language: "hi",
    text: "प्रिय उपभोक्ता आपकी बिजली आज रात 9:30 बजे काट दी जाएगी क्योंकि आपका पिछले महीने का बिल अपडेट नहीं हुआ है। तुरंत बिजली अधिकारी को फोन करें।"
  },
  {
    category: "Grandchild Emergency",
    label: "Grandchild / Relative Police Emergency",
    language: "en",
    text: "Hello Grandpa, this is an emergency. I was with my college friend and police caught us at a checkpoint. Police officer is demanding 20,000 rupees bribe right now on Google Pay or they will put me in jail. Please don't tell mom and dad, just send money quickly."
  }
];

export default function SeniorProtectionPage() {
  const [message, setMessage] = useState("");
  const [language, setLanguage] = useState<"en" | "kn" | "hi">("en");
  const [largeText, setLargeText] = useState(true);
  const [highContrast, setHighContrast] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SeniorSafetyResponse | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const handleExplain = async (customMessage?: string, customLang?: "en" | "kn" | "hi") => {
    const textToAnalyze = customMessage || message;
    const langToUse = customLang || language;
    if (!textToAnalyze.trim()) return;

    setLoading(true);
    setError(null);
    stopSpeaking();

    try {
      const res = await explainSeniorSafety(textToAnalyze, langToUse);
      setResult(res);
      // Auto-speak in senior mode if available
      speakText(res.voice_script, res.language);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to analyze the message. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const speakText = (text: string, langCode: string) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    if (langCode === "kn") {
      utterance.lang = "kn-IN";
    } else if (langCode === "hi") {
      utterance.lang = "hi-IN";
    } else {
      utterance.lang = "en-IN";
    }

    utterance.rate = 0.9; // Slightly slower, clear pace for seniors
    utterance.pitch = 1.0;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  return (
    <div className={`space-y-6 max-w-5xl mx-auto pb-16 ${highContrast ? "bg-black text-yellow-300" : ""}`}>
      {/* Senior Header & Accessibility Bar */}
      <div className="bg-slate-900 border-2 border-amber-500/40 rounded-3xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-14 h-14 rounded-2xl bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0 border-2 border-amber-500/40">
              <UserCheck className="w-8 h-8" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className={`${largeText ? "text-2xl sm:text-3xl" : "text-xl"} font-black text-white`}>
                  Senior Citizen Safety Zone
                </h1>
                <span className="px-2.5 py-1 text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 rounded-full">
                  Simple &amp; Easy
                </span>
              </div>
              <p className={`${largeText ? "text-base" : "text-xs"} text-slate-300 mt-1`}>
                Simple explanations with voice read-aloud in English, Kannada, and Hindi. Never lose your hard-earned pension or savings.
              </p>
            </div>
          </div>

          {/* Quick Access Emergency Hotline */}
          <div className="flex items-center gap-2 w-full md:w-auto">
            <a
              href="tel:1930"
              className="flex-1 md:flex-initial inline-flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-red-600 hover:bg-red-500 text-white font-black text-base shadow-lg shadow-red-950/40 transition-transform active:scale-95"
            >
              <PhoneCall className="w-5 h-5 animate-pulse" />
              Call 1930 (Cyber Police)
            </a>
          </div>
        </div>

        {/* Accessibility Switches */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setLargeText(!largeText)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-bold transition-colors ${
                largeText
                  ? "bg-amber-500 text-slate-950 border-amber-400 font-extrabold"
                  : "bg-slate-800 text-slate-300 border-slate-700"
              }`}
            >
              <Type className="w-3.5 h-3.5" />
              Large Text Mode: {largeText ? "ON" : "OFF"}
            </button>
            <button
              type="button"
              onClick={() => setHighContrast(!highContrast)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-bold transition-colors ${
                highContrast
                  ? "bg-yellow-400 text-slate-950 border-yellow-300"
                  : "bg-slate-800 text-slate-300 border-slate-700"
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              High Contrast: {highContrast ? "ON" : "OFF"}
            </button>
          </div>

          {/* Language Selector */}
          <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800">
            <span className="text-xs font-semibold text-slate-400 px-2">Language:</span>
            <button
              type="button"
              onClick={() => setLanguage("en")}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                language === "en"
                  ? "bg-amber-500 text-slate-950"
                  : "text-slate-300 hover:text-white"
              }`}
            >
              English
            </button>
            <button
              type="button"
              onClick={() => setLanguage("kn")}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                language === "kn"
                  ? "bg-amber-500 text-slate-950"
                  : "text-slate-300 hover:text-white"
              }`}
            >
              ಕನ್ನಡ (Kannada)
            </button>
            <button
              type="button"
              onClick={() => setLanguage("hi")}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                language === "hi"
                  ? "bg-amber-500 text-slate-950"
                  : "text-slate-300 hover:text-white"
              }`}
            >
              हिंदी (Hindi)
            </button>
          </div>
        </div>
      </div>

      {/* Common Scam Examples Bar */}
      <div className="space-y-2">
        <div className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <Sparkles className="w-4 h-4 text-amber-400" />
          Tap a Common Scam Message to Test:
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
          {SENIOR_PRESETS.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setMessage(preset.text);
                setLanguage(preset.language as "en" | "kn" | "hi");
                handleExplain(preset.text, preset.language as "en" | "kn" | "hi");
              }}
              className="p-3 bg-slate-900 hover:bg-slate-800/90 border border-slate-800 rounded-2xl text-left transition-all hover:border-amber-500/50 group"
            >
              <div className="text-[11px] font-bold text-amber-400 uppercase tracking-wider">
                {preset.category}
              </div>
              <div className="text-xs font-semibold text-white mt-1 group-hover:text-amber-200">
                {preset.label}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Input Box */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
        <label className={`block font-bold text-white ${largeText ? "text-lg" : "text-sm"}`}>
          Paste or Type What You Received in SMS, WhatsApp, or Call:
        </label>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          rows={4}
          placeholder="For example: 'Your electricity will be cut off tonight', 'Update pension certificate', 'Send OTP to claim prize'..."
          className={`w-full bg-slate-950 border-2 border-slate-700 rounded-2xl p-4 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-amber-500 transition-colors ${
            largeText ? "text-lg" : "text-sm"
          }`}
        />

        {error && (
          <div className="p-4 bg-red-950/60 border border-red-500 rounded-2xl text-red-200 text-sm">
            {error}
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-3">
          <button
            type="button"
            onClick={() => handleExplain()}
            disabled={loading || !message.trim()}
            className={`flex-1 py-4 px-6 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-black rounded-2xl shadow-xl shadow-amber-500/20 disabled:opacity-50 transition-all flex items-center justify-center gap-2 ${
              largeText ? "text-lg" : "text-base"
            }`}
          >
            {loading ? (
              <>
                <span className="w-5 h-5 border-3 border-slate-950/20 border-t-slate-950 rounded-full animate-spin" />
                Checking Safety...
              </>
            ) : (
              <>
                <HelpCircle className="w-6 h-6" />
                Check If This Is Safe or Scam
              </>
            )}
          </button>
        </div>
      </div>

      {/* Result Display Box */}
      {result && (
        <div className="bg-slate-900 border-2 border-slate-700 rounded-3xl p-6 sm:p-8 space-y-6 animate-in fade-in duration-300">
          {/* Big Clear Verdict Card */}
          <div
            className={`p-6 rounded-2xl border-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${
              result.verdict === "DANGEROUS SCAM"
                ? "bg-red-950/70 border-red-500 text-red-100"
                : result.verdict === "SUSPICIOUS"
                ? "bg-amber-950/60 border-amber-500 text-amber-100"
                : "bg-emerald-950/60 border-emerald-500 text-emerald-100"
            }`}
          >
            <div className="flex items-center gap-4">
              {result.verdict === "DANGEROUS SCAM" ? (
                <div className="w-14 h-14 rounded-2xl bg-red-500 text-white flex items-center justify-center shrink-0">
                  <AlertOctagon className="w-9 h-9" />
                </div>
              ) : result.verdict === "SUSPICIOUS" ? (
                <div className="w-14 h-14 rounded-2xl bg-amber-500 text-slate-950 flex items-center justify-center shrink-0">
                  <HelpCircle className="w-9 h-9" />
                </div>
              ) : (
                <div className="w-14 h-14 rounded-2xl bg-emerald-500 text-white flex items-center justify-center shrink-0">
                  <CheckCircle className="w-9 h-9" />
                </div>
              )}
              <div>
                <div className="text-xs font-bold uppercase tracking-wider opacity-90">
                  Safety Evaluation Verdict
                </div>
                <div className={`${largeText ? "text-2xl sm:text-3xl" : "text-xl"} font-black tracking-wide`}>
                  {result.verdict}
                </div>
                <div className="text-xs font-semibold mt-0.5 opacity-80">
                  Category: {result.scam_category.replace(/_/g, " ")}
                </div>
              </div>
            </div>

            {/* Voice Read Aloud Button */}
            <button
              type="button"
              onClick={() => {
                if (isSpeaking) {
                  stopSpeaking();
                } else {
                  speakText(result.voice_script, result.language);
                }
              }}
              className={`px-4 py-3 rounded-2xl font-black text-sm flex items-center gap-2 border shadow-lg transition-transform active:scale-95 ${
                isSpeaking
                  ? "bg-red-600 hover:bg-red-500 text-white border-red-400 animate-pulse"
                  : "bg-slate-900 hover:bg-slate-800 text-white border-slate-700"
              }`}
            >
              {isSpeaking ? (
                <>
                  <VolumeX className="w-5 h-5" />
                  Stop Voice
                </>
              ) : (
                <>
                  <Volume2 className="w-5 h-5 text-amber-400" />
                  Read Out Loud
                </>
              )}
            </button>
          </div>

          {/* Plain Language Explanation */}
          <div className="p-5 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
            <div className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-4 h-4" />
              In Simple Words (Zero Technical Jargon):
            </div>
            <p className={`${largeText ? "text-xl leading-relaxed" : "text-base leading-normal"} text-slate-100 font-medium`}>
              {result.plain_explanation}
            </p>
          </div>

          {/* Action Steps - What to do right now */}
          <div className="space-y-3">
            <h3 className={`font-black text-white flex items-center gap-2 ${largeText ? "text-xl" : "text-base"}`}>
              <Shield className="w-6 h-6 text-amber-400" />
              What You Should Do Right Now:
            </h3>
            <div className="space-y-2.5">
              {result.what_to_do_now.map((step, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 p-4 bg-slate-950 border border-slate-800 rounded-2xl"
                >
                  <span className="w-7 h-7 rounded-full bg-amber-500 text-slate-950 font-black flex items-center justify-center shrink-0 text-sm">
                    {idx + 1}
                  </span>
                  <span className={`text-slate-100 font-medium ${largeText ? "text-lg leading-relaxed" : "text-sm"}`}>
                    {step}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Golden Rules for Seniors */}
          <div className="p-5 bg-gradient-to-r from-amber-950/30 to-slate-900 border-2 border-amber-500/30 rounded-2xl space-y-3">
            <h4 className="font-black text-amber-400 text-sm uppercase tracking-wider flex items-center gap-1.5">
              <Zap className="w-4 h-4" />
              Golden Rules Never to Forget:
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs sm:text-sm text-slate-200">
              <div className="flex items-center gap-2">
                <span className="text-amber-400 font-bold text-base">✕</span>
                <span>Government &amp; Banks never cut electricity or pension over an SMS.</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-amber-400 font-bold text-base">✕</span>
                <span>Never tell your OTP, MPIN, or ATM card numbers to anyone on the phone.</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-amber-400 font-bold text-base">✕</span>
                <span>Never install any APK file sent over WhatsApp or SMS.</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-amber-400 font-bold text-base">✓</span>
                <span>When in doubt, immediately call your children, bank branch, or 1930.</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

