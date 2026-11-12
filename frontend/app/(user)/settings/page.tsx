"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Settings,
  Shield,
  Eye,
  Volume2,
  Globe,
  Trash2,
  CheckCircle2,
  PhoneCall,
  HeartHandshake,
  Lock,
  Sparkles,
  Sliders
} from "lucide-react";

export default function SettingsPage() {
  const [seniorMode, setSeniorMode] = useState(false);
  const [highContrast, setHighContrast] = useState(false);
  const [speechRate, setSpeechRate] = useState("1.0");
  const [preferredLang, setPreferredLang] = useState("en");
  const [cacheCleared, setCacheCleared] = useState(false);
  const [savedNotice, setSavedNotice] = useState<string | null>(null);

  useEffect(() => {
    // Load local settings
    try {
      const storedSenior = localStorage.getItem("suraksha_senior_mode");
      if (storedSenior) setSeniorMode(storedSenior === "true");

      const storedLang = localStorage.getItem("suraksha_lang");
      if (storedLang) setPreferredLang(storedLang);

      const storedRate = localStorage.getItem("suraksha_speech_rate");
      if (storedRate) setSpeechRate(storedRate);
    } catch (e) {
      console.error(e);
    }
  }, []);

  const handleSaveSettings = () => {
    try {
      localStorage.setItem("suraksha_senior_mode", String(seniorMode));
      localStorage.setItem("suraksha_lang", preferredLang);
      localStorage.setItem("suraksha_speech_rate", speechRate);
      setSavedNotice("Preferences saved successfully!");
      setTimeout(() => setSavedNotice(null), 3000);
    } catch (e) {
      console.error(e);
    }
  };

  const handleClearLocalCache = () => {
    if (confirm("Clear local temporary offline scan cache? Your account session will be preserved.")) {
      try {
        const token = localStorage.getItem("suraksha_token");
        const user = localStorage.getItem("suraksha_user");
        localStorage.clear();
        if (token) localStorage.setItem("suraksha_token", token);
        if (user) localStorage.setItem("suraksha_user", user);
        setCacheCleared(true);
        setTimeout(() => setCacheCleared(false), 3000);
      } catch (e) {
        console.error(e);
      }
    }
  };

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <Settings className="w-7 h-7 text-cyan-400" />
          Platform Preferences & Settings
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Customize accessibility, speech synthesis, language, and zero-cloud privacy controls.
        </p>
      </div>

      {savedNotice && (
        <div className="p-3.5 rounded-xl bg-emerald-950/70 border border-emerald-700 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
          <span>{savedNotice}</span>
        </div>
      )}

      {/* Accessibility & Audio Guidance */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
          <Volume2 className="w-5 h-5 text-cyan-400" />
          <h2 className="text-base font-bold text-slate-100">Accessibility & Audio Guidance</h2>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 rounded-xl bg-slate-950 border border-slate-800">
            <div>
              <span className="block text-sm font-semibold text-slate-200">Senior Citizen High-Contrast Mode</span>
              <span className="text-xs text-slate-400">
                Increases base text size to 18px and enables high-contrast cards for elderly users.
              </span>
            </div>
            <input
              type="checkbox"
              checked={seniorMode}
              onChange={(e) => setSeniorMode(e.target.checked)}
              className="w-5 h-5 accent-cyan-500 rounded cursor-pointer"
            />
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <label className="block text-sm font-semibold text-slate-200">
              Web Speech Text-to-Speech (TTS) Speed
            </label>
            <p className="text-xs text-slate-400">
              Controls the read-aloud voice rate in the AI Assistant and Senior Citizen Explainer.
            </p>
            <select
              value={speechRate}
              onChange={(e) => setSpeechRate(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-xl px-4 py-2 text-sm text-slate-100 focus:outline-none"
            >
              <option value="0.8">Slow (0.8x) — Recommended for Senior Citizens</option>
              <option value="1.0">Normal (1.0x) — Standard</option>
              <option value="1.2">Fast (1.2x) — Quick Review</option>
            </select>
          </div>
        </div>
      </div>

      {/* Language Preferences */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
          <Globe className="w-5 h-5 text-cyan-400" />
          <h2 className="text-base font-bold text-slate-100">Language & Localization</h2>
        </div>

        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
          <label className="block text-sm font-semibold text-slate-200">Default Safety Language</label>
          <p className="text-xs text-slate-400">
            Select your preferred language for the AI Assistant, scam alerts, and educational quizzes.
          </p>
          <select
            value={preferredLang}
            onChange={(e) => setPreferredLang(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-xl px-4 py-2 text-sm text-slate-100 focus:outline-none"
          >
            <option value="en">English (Pan-India)</option>
            <option value="kn">ಕನ್ನಡ (Kannada — Karnataka)</option>
            <option value="hi">हिन्दी (Hindi — Pan-India)</option>
          </select>
        </div>
      </div>

      {/* Privacy & Zero-Cloud Guard */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
          <Shield className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-bold text-slate-100">Zero-Cloud Privacy Architecture</h2>
        </div>

        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-slate-950 border border-emerald-900/50 space-y-2">
            <div className="flex items-center gap-2 text-emerald-400 text-sm font-bold">
              <CheckCircle2 className="w-4 h-4" />
              100% In-Memory Processing Active
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              SURAKSHA AI processes all pasted texts, Aadhaar numbers, and PAN cards locally in server memory.
              No citizen data is transmitted to external cloud APIs, OpenAI, or advertising telemetry.
            </p>
          </div>

          <div className="flex items-center justify-between p-4 rounded-xl bg-slate-950 border border-slate-800">
            <div>
              <span className="block text-sm font-semibold text-slate-200">Clear Temporary Offline Cache</span>
              <span className="text-xs text-slate-400">Purges offline threat scan previews from browser memory.</span>
            </div>
            <button
              onClick={handleClearLocalCache}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-950/70 hover:bg-red-900 border border-red-800 text-red-300 text-xs font-semibold transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              {cacheCleared ? "Cache Cleared!" : "Clear Cache"}
            </button>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex items-center justify-end gap-3 pt-2">
        <button
          onClick={handleSaveSettings}
          className="flex items-center gap-2 py-3 px-6 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm shadow-md shadow-cyan-500/20 transition-all"
        >
          <Sliders className="w-4 h-4" />
          Save All Preferences
        </button>
      </div>
    </div>
  );
}

