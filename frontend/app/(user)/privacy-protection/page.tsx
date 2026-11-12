"use client";

import React, { useState, useEffect } from "react";
import {
  EyeOff,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Lock,
  Copy,
  Check,
  Download,
  FileText,
  Upload,
  RefreshCw,
  Sparkles,
  ExternalLink,
  CreditCard,
  Phone,
  Mail,
  Fingerprint,
  FileCode,
  Trash2,
  Clock
} from "lucide-react";
import {
  scanTextPrivacy,
  scanFilePrivacy,
  fetchPrivacyHistory,
  deletePrivacyScanHistory,
  PrivacyScanResponse,
  PrivacyHistoryItem
} from "@/lib/api";

const PRESET_PII_SAMPLES = [
  {
    label: "🆔 Aadhaar & Phone Leak",
    text: "Dear customer, your Aadhaar number 2847-5938-1025 and linked mobile +91 98765 43210 have been verified for KYC. Contact support at helpdesk@finance-update.in."
  },
  {
    label: "💳 Salary Slip with PAN & Card",
    text: "Employee Rajesh Kumar, PAN Card: BZRPK8974L. Salary credited to corporate debit card 4532 0151 1283 0366. For issues email payroll@company.com."
  },
  {
    label: "💸 UPI Payment Request with VPA",
    text: "Please send payment of Rs. 4,500 to my UPI handle suresh.kumar@okhdfcbank or call me at 9123456789. Ref code: TXN-8941."
  }
];

export default function PrivacyProtectionPage() {
  const [inputText, setInputText] = useState("");
  const [scanResult, setScanResult] = useState<PrivacyScanResponse | null>(null);
  const [history, setHistory] = useState<PrivacyHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedSanitized, setCopiedSanitized] = useState(false);
  const [activeTab, setActiveTab] = useState<"text" | "file" | "history">("text");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    fetchPrivacyHistory().then(setHistory).catch(() => {});
  }, []);

  const handleScanText = async (textToScan?: string) => {
    const text = (textToScan || inputText).trim();
    if (!text) {
      setError("Please enter or paste text to scan.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await scanTextPrivacy(text);
      setScanResult(res);
      fetchPrivacyHistory().then(setHistory).catch(() => {});
    } catch (err: any) {
      setError(err.message || "Privacy scan failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleScanFile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError("Please select a text or CSV file to sanitize.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await scanFilePrivacy(selectedFile);
      setScanResult(res);
      setSelectedFile(null);
      fetchPrivacyHistory().then(setHistory).catch(() => {});
    } catch (err: any) {
      setError(err.message || "File privacy scan failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopySanitized = () => {
    if (!scanResult) return;
    navigator.clipboard.writeText(scanResult.sanitized_text);
    setCopiedSanitized(true);
    setTimeout(() => setCopiedSanitized(false), 2000);
  };

  const handleDownloadSanitized = () => {
    if (!scanResult) return;
    const blob = new Blob([scanResult.sanitized_text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sanitized-redacted-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDeleteHistoryItem = async (id: string) => {
    try {
      await deletePrivacyScanHistory(id);
      setHistory((prev) => prev.filter((h) => h.id !== id));
    } catch (err: any) {
      alert("Failed to delete record: " + err.message);
    }
  };

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <EyeOff className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-black text-white flex items-center gap-2">
              Personal Data & Privacy Protection
              <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                Verhoeff & Luhn Validated
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Zero-cloud local in-memory redaction • Mask Aadhaar, PAN, Cards, Phone & UPI • Prevent identity theft
            </p>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab("text")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "text"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Redact Text
          </button>
          <button
            onClick={() => setActiveTab("file")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "file"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Redact File (.txt)
          </button>
          <button
            onClick={() => setActiveTab("history")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "history"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Past Scans ({history.length})
          </button>
        </div>
      </div>

      {/* Zero Cloud Leak Guarantee Banner */}
      <div className="bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/30 rounded-2xl p-4 flex items-center gap-3 shadow-lg">
        <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0" />
        <div className="text-xs text-slate-300">
          <strong>100% IN-MEMORY PRIVACY ASSURANCE:</strong> Your personal credentials never leave your browser or host memory.
          SURAKSHA AI processes redactions locally without external cloud APIs and never stores unmasked documents.
        </div>
      </div>

      {/* TAB 1: TEXT REDACTION */}
      {activeTab === "text" && (
        <div className="space-y-6">
          {/* Presets Bar */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-400 font-semibold flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" /> Test Presets:
            </span>
            {PRESET_PII_SAMPLES.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setInputText(preset.text);
                  handleScanText(preset.text);
                }}
                className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500/50 text-slate-300 hover:text-white text-xs transition-colors"
              >
                {preset.label}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input Box */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-white flex items-center gap-2">
                  <FileText className="w-4 h-4 text-cyan-400" />
                  Original Document / Text Input
                </h2>
                <span className="text-[11px] text-slate-500 font-mono">
                  {inputText.length} characters
                </span>
              </div>

              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Paste confidential text, salary slip, KYC message, or chat snippet containing Aadhaar, PAN, phone numbers, or bank cards..."
                rows={10}
                className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl p-4 text-xs text-white outline-none font-mono leading-relaxed resize-none"
              />

              {error && (
                <div className="p-3 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <button
                onClick={() => handleScanText()}
                disabled={loading || !inputText.trim()}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-xs transition-all shadow-lg shadow-cyan-600/20 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Scanning for Sensitive Identifiers...
                  </>
                ) : (
                  <>
                    <EyeOff className="w-4 h-4" />
                    Inspect & Redact Credentials
                  </>
                )}
              </button>
            </div>

            {/* Sanitized / Redacted Preview */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4 flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-bold text-white flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    Sanitized & Masked Output
                  </h2>
                  {scanResult && (
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[11px] font-black border ${
                        scanResult.risk_level === "CRITICAL"
                          ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                          : scanResult.risk_level === "HIGH"
                          ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                          : scanResult.risk_level === "MEDIUM"
                          ? "bg-blue-500/20 text-blue-300 border-blue-500/40"
                          : "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                      }`}
                    >
                      Risk: {scanResult.risk_level} ({scanResult.risk_score}/100)
                    </span>
                  )}
                </div>

                {scanResult ? (
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs text-slate-200 font-mono leading-relaxed h-[240px] overflow-y-auto whitespace-pre-wrap select-all">
                    {scanResult.sanitized_text}
                  </div>
                ) : (
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-8 text-center text-xs text-slate-500 h-[240px] flex flex-col items-center justify-center space-y-2">
                    <EyeOff className="w-8 h-8 text-slate-700" />
                    <span>Redacted text preview will appear here after scanning</span>
                  </div>
                )}
              </div>

              {scanResult && (
                <div className="flex gap-2 pt-2">
                  <button
                    onClick={handleCopySanitized}
                    className="flex-1 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs transition-colors flex items-center justify-center gap-1.5"
                  >
                    {copiedSanitized ? (
                      <>
                        <Check className="w-4 h-4 text-emerald-400" /> Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" /> Copy Redacted Text
                      </>
                    )}
                  </button>
                  <button
                    onClick={handleDownloadSanitized}
                    className="flex-1 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs transition-colors flex items-center justify-center gap-1.5 shadow-md shadow-cyan-600/20"
                  >
                    <Download className="w-4 h-4" /> Download Clean File
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Detailed Detection Breakdown & Advice */}
          {scanResult && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Detected Credentials Chips */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Fingerprint className="w-4 h-4 text-cyan-400" />
                  Detected Credentials ({scanResult.detected_entities.length})
                </h3>

                {scanResult.detected_entities.length === 0 ? (
                  <div className="p-4 bg-slate-950 rounded-xl text-center text-xs text-slate-500">
                    No sensitive identifiers found in this content.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {scanResult.detected_entities.map((ent, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className={`p-1 rounded ${
                              ent.type === "AADHAAR"
                                ? "bg-blue-500/20 text-blue-400"
                                : ent.type === "PAN"
                                ? "bg-amber-500/20 text-amber-400"
                                : ent.type === "PAYMENT_CARD"
                                ? "bg-rose-500/20 text-rose-400"
                                : ent.type === "PHONE_NUMBER"
                                ? "bg-emerald-500/20 text-emerald-400"
                                : "bg-cyan-500/20 text-cyan-400"
                            }`}
                          >
                            {ent.type === "AADHAAR" ? (
                              <Fingerprint className="w-3.5 h-3.5" />
                            ) : ent.type === "PAYMENT_CARD" ? (
                              <CreditCard className="w-3.5 h-3.5" />
                            ) : ent.type === "PHONE_NUMBER" ? (
                              <Phone className="w-3.5 h-3.5" />
                            ) : (
                              <Mail className="w-3.5 h-3.5" />
                            )}
                          </span>
                          <div>
                            <div className="font-bold text-white text-[11px]">{ent.type}</div>
                            <div className="font-mono text-[11px] text-slate-400">{ent.raw_preview}</div>
                          </div>
                        </div>

                        {ent.is_checksum_valid !== undefined && (
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                              ent.is_checksum_valid
                                ? "bg-emerald-500/20 text-emerald-400"
                                : "bg-slate-800 text-slate-400"
                            }`}
                          >
                            {ent.is_checksum_valid ? "Valid Checksum" : "Pattern Match"}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Privacy Recommendations (Right 2 cols) */}
              <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Actionable Privacy Protection Directives
                </h3>

                <div className="space-y-2">
                  {scanResult.recommendations.map((rec, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-300 leading-relaxed flex items-start gap-2.5"
                    >
                      <span className="text-cyan-400 font-bold">✓</span>
                      <span>{rec}</span>
                    </div>
                  ))}
                </div>

                <div className="pt-2 flex flex-wrap gap-3 text-xs">
                  <a
                    href="https://myaadhaar.uidai.gov.in"
                    target="_blank"
                    rel="noreferrer"
                    className="text-cyan-400 hover:underline flex items-center gap-1 font-semibold"
                  >
                    Lock Aadhaar Biometrics <ExternalLink className="w-3 h-3" />
                  </a>
                  <span className="text-slate-600">•</span>
                  <a
                    href="https://sancharsaathi.gov.in"
                    target="_blank"
                    rel="noreferrer"
                    className="text-cyan-400 hover:underline flex items-center gap-1 font-semibold"
                  >
                    Check SIMs on Sanchar Saathi <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: FILE REDACTION */}
      {activeTab === "file" && (
        <div className="max-w-xl mx-auto bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Upload className="w-5 h-5 text-cyan-400" />
              Upload Document for In-Memory Sanitization
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Supports .txt, .csv, and .log files up to 5MB. File bytes are scrubbed in memory and never written to disk.
            </p>
          </div>

          <form onSubmit={handleScanFile} className="space-y-4">
            <div className="border-2 border-dashed border-slate-800 hover:border-cyan-500/50 rounded-2xl p-6 text-center space-y-2 bg-slate-950/60 transition-colors">
              <FileCode className="w-8 h-8 text-cyan-400 mx-auto" />
              <div className="text-xs font-bold text-white">
                {selectedFile ? selectedFile.name : "Select a Text-Based File"}
              </div>
              <div className="text-[11px] text-slate-500">
                {selectedFile ? `${selectedFile.size} bytes` : "Supports UTF-8 Plaintext, CSV, or Logs"}
              </div>
              <input
                type="file"
                id="privacyFileInput"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setSelectedFile(e.target.files[0]);
                  }
                }}
                accept=".txt,.csv,.log"
                className="hidden"
              />
              <label
                htmlFor="privacyFileInput"
                className="inline-block px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold cursor-pointer transition-colors mt-2"
              >
                Browse File
              </label>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={!selectedFile || loading}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-xs transition-all shadow-lg shadow-cyan-600/20 disabled:opacity-50"
            >
              {loading ? "Sanitizing in Memory..." : "Sanitize File"}
            </button>
          </form>
        </div>
      )}

      {/* TAB 3: PAST SCANS HISTORY */}
      {activeTab === "history" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-cyan-400" />
              Past Privacy Audits ({history.length})
            </h2>
          </div>

          {history.length === 0 ? (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center space-y-3">
              <EyeOff className="w-12 h-12 text-slate-600 mx-auto" />
              <h3 className="text-base font-bold text-white">No Privacy History Found</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                Scan your first document or text to track detected credentials and risk scores.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-cyan-400">
                        Risk Score: {item.risk_score}/100
                      </span>
                      <span className="text-slate-600">•</span>
                      <span className="text-[11px] text-slate-400">
                        {new Date(item.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="text-xs font-mono text-slate-300 truncate max-w-lg">
                      {item.redacted_preview}
                    </div>
                  </div>

                  <button
                    onClick={() => handleDeleteHistoryItem(item.id)}
                    className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-950 text-rose-400 transition-colors self-end sm:self-center"
                    title="Delete Scan Record"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

