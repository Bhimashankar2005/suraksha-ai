"use client";

import React, { useState, useEffect } from "react";
import {
  MessageSquareWarning,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Search,
  Sparkles,
  Info,
  Radio,
  Star,
  Send,
  History,
  ArrowRight,
  ExternalLink,
  ShieldCheck,
  RefreshCw
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { API_BASE_URL } from "@/lib/api";

const PRESET_MESSAGES = [
  {
    label: "Fake Bank KYC Block",
    text: "Dear SBI customer, your bank account will be suspended today due to missing PAN card. Update your KYC immediately by clicking: http://bit.ly/sbi-pan-update to avoid permanent block.",
  },
  {
    label: "Electricity Cutoff Tonight",
    text: "Dear consumer, tonight 9:30 PM electricity power will be disconnected from the electricity office because previous month bill was not updated. Immediately contact electricity officer at 9876543210.",
  },
  {
    label: "UPI PIN Cashback Scam",
    text: "Congratulations! You have received a cashback reward of Rs 2,500. To credit the money into your bank account, click here and enter your 6-digit UPI PIN.",
  },
  {
    label: "YouTube Job Scam",
    text: "Part-time work from home! Like 3 YouTube videos and earn Rs 3,000 to Rs 5,000 daily. No qualifications needed. Contact our task coordinator on Telegram @AgentTask2026.",
  },
  {
    label: "Legitimate Bank Alert",
    text: "Dear customer, your SBI account ending in 4102 was debited by Rs 450.00 for groceries at Metro Cash & Carry on 01-Nov-2026. Avl Bal: Rs 18,420.00.",
  },
];

interface AnalysisResult {
  id: string;
  content_snippet: string;
  risk_score: number;
  risk_level: string;
  scam_category: string;
  ml_probability: number;
  matched_indicators: Array<{
    rule_id: string;
    category: string;
    description: string;
    weight: number;
    matched_terms: string[];
  }>;
  highlighted_tokens: string[];
  explanation: string;
  recommendations: string[];
  created_at: string;
}

export default function ScamDetectionPage() {
  const { token } = useAuth();
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Reporting State
  const [reportSuccess, setReportSuccess] = useState<string | null>(null);
  const [reporting, setReporting] = useState(false);
  const [suspectContact, setSuspectContact] = useState("");

  // Feedback State
  const [rating, setRating] = useState<number>(5);
  const [feedbackSent, setFeedbackSent] = useState(false);

  const handleScan = async (textToScan?: string) => {
    const text = textToScan || content;
    if (!text || text.trim().length < 5) {
      setError("Please paste a message with at least 5 characters.");
      return;
    }

    setLoading(true);
    setError(null);
    setReportSuccess(null);
    setFeedbackSent(false);

    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch(`${API_BASE_URL}/scam/scan`, {
        method: "POST",
        headers,
        body: JSON.stringify({ content: text.trim() }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to analyze message");
      }

      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Network error analyzing message");
    } finally {
      setLoading(false);
    }
  };

  const handlePresetClick = (presetText: string) => {
    setContent(presetText);
    handleScan(presetText);
  };

  const handleReportToCommunity = async () => {
    if (!result) return;
    setReporting(true);
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE_URL}/scam/report`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          scan_id: result.id,
          target_value: suspectContact || "Reported from Scam Scanner",
          description: `Community Report from Scam Detection Engine: Category: ${result.scam_category}, Score: ${result.risk_score}/100`,
        }),
      });

      if (res.ok) {
        const repData = await res.json();
        setReportSuccess(`Submitted to Community Intel! Unique Tracking ID: ${repData.report_code}`);
      }
    } catch (e) {
      console.error("Report submission failed", e);
    } finally {
      setReporting(false);
    }
  };

  const handleSendFeedback = async () => {
    if (!result) return;
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      await fetch(`${API_BASE_URL}/scam/feedback`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          scan_id: result.id,
          rating,
          feedback_text: `User rating: ${rating} stars`,
        }),
      });
      setFeedbackSent(true);
    } catch (e) {
      console.error("Failed to submit feedback", e);
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-6xl mx-auto w-full">
      {/* Module Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold">
          <MessageSquareWarning className="w-3.5 h-3.5" />
          Module 1: Explainable AI Scam Message Detection
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          Suspicious Message & Fraud Analyzer
        </h1>
        <p className="text-xs md:text-sm text-slate-400 max-w-3xl leading-relaxed">
          Paste any SMS, WhatsApp alert, Telegram offer, or email. The engine parses linguistic triggers,
          matches transparent heuristic rules, calculates ML scam probability, and explains the risks clearly.
        </p>
      </div>

      {/* Preset Test Chips */}
      <div className="space-y-2">
        <div className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          Test with Real-World Threat Samples:
        </div>
        <div className="flex flex-wrap gap-2">
          {PRESET_MESSAGES.map((preset, idx) => (
            <button
              key={idx}
              onClick={() => handlePresetClick(preset.text)}
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-cyan-500 hover:text-cyan-300 text-slate-300 transition-colors"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Input Box Card */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-4">
        {error && (
          <div className="p-3 rounded-xl bg-red-950/60 border border-red-800 text-red-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        <div className="relative">
          <textarea
            rows={5}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste suspicious SMS, WhatsApp message, lottery notification, job offer, or email here..."
            className="w-full p-4 rounded-xl bg-slate-950 border border-slate-800 focus:border-cyan-500 text-sm text-slate-100 placeholder-slate-600 focus:outline-none transition-colors"
          />
          <div className="absolute right-3 bottom-3 text-[11px] text-slate-500">
            {content.length} characters
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            Local explainable compute • Zero data sent to paid third-party AI APIs
          </div>

          <button
            onClick={() => handleScan()}
            disabled={loading || content.trim().length < 5}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm shadow-md shadow-cyan-500/20 disabled:opacity-50 transition-all"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Analyzing Patterns...
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                Analyze Threat Level
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results Section */}
      {result && (
        <div className="space-y-6 animate-fadeIn">
          {/* Top Score Banner */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Risk Gauge Card */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
              <div className="text-xs font-semibold text-slate-400">Calculated Risk Score</div>
              <div className="flex items-baseline gap-2 my-2">
                <span
                  className={`text-5xl font-black ${
                    result.risk_level === "CRITICAL"
                      ? "text-red-400"
                      : result.risk_level === "HIGH"
                      ? "text-amber-400"
                      : result.risk_level === "MEDIUM"
                      ? "text-blue-400"
                      : "text-emerald-400"
                  }`}
                >
                  {result.risk_score}
                </span>
                <span className="text-slate-500 text-sm">/ 100</span>
              </div>
              <div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold ${
                    result.risk_level === "CRITICAL"
                      ? "bg-red-500/20 text-red-300 border border-red-500/30"
                      : result.risk_level === "HIGH"
                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                      : result.risk_level === "MEDIUM"
                      ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                      : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  }`}
                >
                  {result.risk_level} THREAT
                </span>
              </div>
            </div>

            {/* Category Card */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
              <div className="text-xs font-semibold text-slate-400">Scam Classification</div>
              <div className="text-xl font-bold text-white my-2">
                {result.scam_category.replace(/_/g, " ")}
              </div>
              <div className="text-xs text-slate-400">
                ML Probability: <strong>{Math.round(result.ml_probability * 100)}%</strong>
              </div>
            </div>

            {/* Action Banner */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
              <div className="text-xs font-semibold text-slate-400">Community Defense</div>
              <p className="text-xs text-slate-300 my-2">
                Submit this message to warn other citizens in your community.
              </p>
              {reportSuccess ? (
                <div className="text-xs text-emerald-400 font-semibold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  {reportSuccess}
                </div>
              ) : (
                <div className="space-y-2">
                  <input
                    type="text"
                    placeholder="Sender phone / handle (optional)"
                    value={suspectContact}
                    onChange={(e) => setSuspectContact(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-600 focus:outline-none"
                  />
                  <button
                    onClick={handleReportToCommunity}
                    disabled={reporting}
                    className="w-full flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all"
                  >
                    <Send className="w-3.5 h-3.5" />
                    {reporting ? "Submitting..." : "Submit Community Report"}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Transparent Explanation Card */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Info className="w-4 h-4 text-cyan-400" />
              Why Was This Flagged? (Explainable Assessment)
            </h3>
            <p className="text-xs md:text-sm text-slate-300 leading-relaxed">
              {result.explanation}
            </p>

            {result.highlighted_tokens.length > 0 && (
              <div className="pt-2">
                <span className="text-xs font-semibold text-slate-400">Detected Trigger Tokens: </span>
                <div className="inline-flex flex-wrap gap-1.5 mt-1">
                  {result.highlighted_tokens.map((token, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded text-[11px] font-mono bg-red-950/60 text-red-300 border border-red-800/60"
                    >
                      {token}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Matched Heuristic Rules */}
          {result.matched_indicators.length > 0 && (
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                Matched Fraud Indicators ({result.matched_indicators.length})
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {result.matched_indicators.map((ind, i) => (
                  <div key={i} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-200">{ind.rule_id}</span>
                      <span className="text-[10px] font-semibold text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded">
                        +{ind.weight} pts
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">{ind.description}</p>
                    {ind.matched_terms.length > 0 && (
                      <div className="text-[10px] text-slate-500">
                        Trigger: <em>"{ind.matched_terms.join(", ")}"</em>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations Card */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Recommended Safety Actions
            </h3>
            <ul className="space-y-2">
              {result.recommendations.map((rec, i) => (
                <li key={i} className="flex items-start gap-2 text-xs md:text-sm text-slate-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-2 shrink-0" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Accuracy Feedback Widget */}
          <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-xs text-slate-400 text-center sm:text-left">
              Was this analysis helpful and accurate? Help improve the open community model.
            </div>

            {feedbackSent ? (
              <span className="text-xs text-emerald-400 font-semibold">
                Thank you for your feedback!
              </span>
            ) : (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setRating(star)}
                      className={`p-1 text-sm ${rating >= star ? "text-amber-400" : "text-slate-600"}`}
                    >
                      <Star className="w-4 h-4 fill-current" />
                    </button>
                  ))}
                </div>
                <button
                  onClick={handleSendFeedback}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 font-medium border border-slate-700 transition-colors"
                >
                  Submit Rating
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

