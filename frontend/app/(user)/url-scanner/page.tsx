"use client";

import React, { useState } from "react";
import {
  Link2,
  AlertTriangle,
  CheckCircle2,
  ShieldCheck,
  Search,
  Sparkles,
  Info,
  Send,
  Lock,
  Unlock,
  Server,
  Globe,
  Radio,
  RefreshCw,
  ExternalLink
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { API_BASE_URL } from "@/lib/api";

const PRESET_URLS = [
  {
    label: "Bank Lookalike (.xyz)",
    url: "http://onlinesbi-pan-kyc.xyz/login.html",
  },
  {
    label: "Raw IP Phishing Host",
    url: "http://185.199.110.153/update-pan.php",
  },
  {
    label: "Shortened Link Mask",
    url: "https://bit.ly/bank-offer-update",
  },
  {
    label: "Legitimate SBI Portal",
    url: "https://onlinesbi.sbi/portal",
  },
  {
    label: "National Cybercrime Portal",
    url: "https://cybercrime.gov.in/",
  },
];

interface UrlScanResult {
  id: string;
  url: string;
  domain: string;
  risk_score: number;
  risk_level: string;
  is_ip_host: boolean;
  has_ssl: boolean;
  is_shortened: boolean;
  lookalike_target?: string | null;
  matched_indicators: Array<{
    rule: string;
    description: string;
    weight: number;
  }>;
  analysis_details: {
    protocol?: string;
    has_ssl?: boolean;
    tld?: string;
    subdomains_count?: number;
    is_ip_host?: boolean;
    is_shortened?: boolean;
    detected_keywords?: string[];
    matched_brand?: string | null;
    ssrf_blocked?: boolean;
  };
  explanation: string;
  recommendations: string[];
  created_at: string;
}

export default function UrlScannerPage() {
  const { token } = useAuth();
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<UrlScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Reporting
  const [reporting, setReporting] = useState(false);
  const [reportSuccess, setReportSuccess] = useState<string | null>(null);

  const handleScan = async (urlToScan?: string) => {
    const targetUrl = urlToScan || url;
    if (!targetUrl || targetUrl.trim().length < 3) {
      setError("Please provide a valid web address or domain to analyze.");
      return;
    }

    setLoading(true);
    setError(null);
    setReportSuccess(null);

    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE_URL}/url/scan`, {
        method: "POST",
        headers,
        body: JSON.stringify({ url: targetUrl.trim() }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to scan URL");
      }

      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Network error communicating with scanner");
    } finally {
      setLoading(false);
    }
  };

  const handlePresetClick = (presetUrl: string) => {
    setUrl(presetUrl);
    handleScan(presetUrl);
  };

  const handleReportUrl = async () => {
    if (!result) return;
    setReporting(true);
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE_URL}/url/report`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          scan_id: result.id,
          target_value: result.url,
          description: `Phishing URL Threat: ${result.url} (Risk: ${result.risk_score}/100, Lookalike: ${result.lookalike_target || "None"})`,
        }),
      });

      if (res.ok) {
        const repData = await res.json();
        setReportSuccess(`Submitted to Community Threat Intel! Report ID: ${repData.report_code}`);
      }
    } catch (e) {
      console.error("Report failed", e);
    } finally {
      setReporting(false);
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-6xl mx-auto w-full">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold">
          <Link2 className="w-3.5 h-3.5" />
          Module 2: Intelligent Phishing URL Scanner
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          Phishing & Lookalike Domain Inspector
        </h1>
        <p className="text-xs md:text-sm text-slate-400 max-w-3xl leading-relaxed">
          Inspect suspicious links safely without exposing your device. Features strict anti-SSRF protection,
          homoglyph typo-squatting detection against authentic Indian banking domains, and raw IP host checks.
        </p>
      </div>

      {/* Preset Test Chips */}
      <div className="space-y-2">
        <div className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          Test with Real-World Phishing Examples:
        </div>
        <div className="flex flex-wrap gap-2">
          {PRESET_URLS.map((preset, idx) => (
            <button
              key={idx}
              onClick={() => handlePresetClick(preset.url)}
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
          <Globe className="w-5 h-5 text-slate-500 absolute left-4 top-4" />
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste suspicious website link or domain (e.g. onlinesbi-pan.xyz)..."
            className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-slate-950 border border-slate-800 focus:border-cyan-500 text-sm text-slate-100 placeholder-slate-600 focus:outline-none transition-colors"
          />
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            Anti-SSRF Protected • Blocks loopback, RFC 1918, and cloud metadata (169.254.169.254)
          </div>

          <button
            onClick={() => handleScan()}
            disabled={loading || url.trim().length < 3}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm shadow-md shadow-cyan-500/20 disabled:opacity-50 transition-all"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Auditing Destination...
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                Scan URL Safety
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
            {/* Score Card */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
              <div className="text-xs font-semibold text-slate-400">Threat Risk Score</div>
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
                  {result.risk_level} PHISHING RISK
                </span>
              </div>
            </div>

            {/* Target Identity Card */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
              <div className="text-xs font-semibold text-slate-400">Target Domain & Mimicry</div>
              <div className="my-2">
                <div className="text-base font-bold text-white truncate font-mono">
                  {result.domain}
                </div>
                {result.lookalike_target ? (
                  <div className="text-xs text-red-400 font-semibold mt-1 flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                    Impersonates: {result.lookalike_target}
                  </div>
                ) : (
                  <div className="text-xs text-emerald-400 mt-1">
                    No active brand impersonation detected
                  </div>
                )}
              </div>
              <div className="text-[11px] text-slate-500 truncate">
                Scanned: {result.url}
              </div>
            </div>

            {/* Community Threat Escalation */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
              <div className="text-xs font-semibold text-slate-400">Community Defense</div>
              <p className="text-xs text-slate-300 my-2">
                Report this URL to add it to the community threat intelligence database.
              </p>
              {reportSuccess ? (
                <div className="text-xs text-emerald-400 font-semibold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  {reportSuccess}
                </div>
              ) : (
                <button
                  onClick={handleReportUrl}
                  disabled={reporting}
                  className="w-full flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all"
                >
                  <Send className="w-3.5 h-3.5" />
                  {reporting ? "Submitting Report..." : "Submit to Threat Intel"}
                </button>
              )}
            </div>
          </div>

          {/* Technical Diagnostics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-3">
              {result.has_ssl ? (
                <Lock className="w-6 h-6 text-emerald-400" />
              ) : (
                <Unlock className="w-6 h-6 text-red-400" />
              )}
              <div>
                <div className="text-[11px] text-slate-500">Encryption</div>
                <div className="text-xs font-bold text-slate-200">
                  {result.has_ssl ? "HTTPS Secure" : "Unencrypted HTTP"}
                </div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-3">
              <Server className="w-6 h-6 text-cyan-400" />
              <div>
                <div className="text-[11px] text-slate-500">Host Type</div>
                <div className="text-xs font-bold text-slate-200">
                  {result.is_ip_host ? "Raw IP Host (High Risk)" : "Named Domain"}
                </div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-3">
              <Globe className="w-6 h-6 text-blue-400" />
              <div>
                <div className="text-[11px] text-slate-500">Top-Level Domain</div>
                <div className="text-xs font-bold text-slate-200 uppercase">
                  .{result.analysis_details.tld || "unknown"}
                </div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-3">
              <Link2 className="w-6 h-6 text-amber-400" />
              <div>
                <div className="text-[11px] text-slate-500">Shortened Mask</div>
                <div className="text-xs font-bold text-slate-200">
                  {result.is_shortened ? "Yes (Masked)" : "Direct URL"}
                </div>
              </div>
            </div>
          </div>

          {/* Matched Phishing Indicators */}
          {result.matched_indicators.length > 0 && (
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                Detected URL Risk Indicators ({result.matched_indicators.length})
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {result.matched_indicators.map((ind, i) => (
                  <div key={i} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-200">{ind.rule}</span>
                      <span className="text-[10px] font-semibold text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded">
                        +{ind.weight} pts
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">{ind.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Transparent Explanation Card */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Info className="w-4 h-4 text-cyan-400" />
              Explainable Risk Assessment
            </h3>
            <p className="text-xs md:text-sm text-slate-300 leading-relaxed">
              {result.explanation}
            </p>
          </div>

          {/* Recommendations Card */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Safety Recommendations
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
        </div>
      )}
    </div>
  );
}

