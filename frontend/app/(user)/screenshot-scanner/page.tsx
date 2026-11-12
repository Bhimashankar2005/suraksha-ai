"use client";

import React, { useState, useRef } from "react";
import {
  FileSearch,
  Upload,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Info,
  Send,
  Image as ImageIcon,
  ScanLine,
  CreditCard,
  Hash,
  Sparkles,
  RefreshCw,
  FileText
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { API_BASE_URL } from "@/lib/api";

const PRESET_IMAGE_SAMPLES = [
  {
    label: "Fake PhonePe Payment (Rs 45,000)",
    text: "Payment Successful. Rs 45,000 paid to Rajesh Kumar. Transferred from PhonePe Wallet / HDFC Bank. UTR: 928491028401. Transaction Successful.",
  },
  {
    label: "Fake QR Code Cashback Deception",
    text: "Scan QR code to credit cashback of Rs 2,500 into your Google Pay account. Enter UPI PIN to confirm receipt.",
  },
  {
    label: "Fake PNB Account Block SMS",
    text: "Dear PNB customer, your debit card is blocked today. Update your KYC immediately at http://pnb-verify.xyz to avoid suspension.",
  },
];

interface ImageScanResult {
  id: string;
  file_hash: string;
  file_name: string;
  file_size_bytes: number;
  dimensions: number[];
  mime_type: string;
  extracted_text: string;
  risk_score: number;
  risk_level: string;
  scam_category: string;
  detected_entities: {
    is_payment_screenshot?: boolean;
    detected_apps?: string[];
    utr_references?: string[];
    amounts_mentioned?: string[];
  };
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
  ocr_engine: string;
  created_at: string;
}

export default function ScreenshotScannerPage() {
  const { token } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [textOverride, setTextOverride] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImageScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Community Reporting
  const [reporting, setReporting] = useState(false);
  const [reportSuccess, setReportSuccess] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setError(null);
      setResult(null);
      setReportSuccess(null);

      const reader = new FileReader();
      reader.onload = (event) => {
        setImagePreview(event.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handlePresetSelect = (presetText: string) => {
    setTextOverride(presetText);
    // If no file is selected, create a dummy sample blob so the form submission succeeds
    if (!selectedFile) {
      const canvas = document.createElement("canvas");
      canvas.width = 400;
      canvas.height = 200;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.fillStyle = "#0f172a";
        ctx.fillRect(0, 0, 400, 200);
        ctx.fillStyle = "#38bdf8";
        ctx.font = "14px sans-serif";
        ctx.fillText("SURAKSHA AI Sample Screenshot", 20, 100);
      }
      canvas.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], "sample_screenshot.png", { type: "image/png" });
          setSelectedFile(file);
          setImagePreview(canvas.toDataURL("image/png"));
        }
      });
    }
  };

  const handleScan = async () => {
    if (!selectedFile) {
      setError("Please select an image file to upload.");
      return;
    }

    setLoading(true);
    setError(null);
    setReportSuccess(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      if (textOverride && textOverride.trim()) {
        formData.append("ocr_text_override", textOverride.trim());
      }

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE_URL}/image/scan`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Image analysis failed");
      }

      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Network error uploading image");
    } finally {
      setLoading(false);
    }
  };

  const handleReport = async () => {
    if (!result) return;
    setReporting(true);
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE_URL}/image/report`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          scan_id: result.id,
          target_value: result.file_name,
          description: `Screenshot Scam Report: ${result.file_name} (Risk: ${result.risk_score}/100, SHA-256: ${result.file_hash})`,
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
          <FileSearch className="w-3.5 h-3.5" />
          Module 3: Screenshot & Image Scam Detection
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          Screenshot & Fake Receipt Analyzer
        </h1>
        <p className="text-xs md:text-sm text-slate-400 max-w-3xl leading-relaxed">
          Upload screenshots of fake UPI payment receipts, SMS banking threats, or suspicious QR codes.
          The engine computes cryptographic SHA-256 hashes, extracts text via OCR, and detects fraud patterns.
        </p>
      </div>

      {/* Mandatory Safety Rule Alert */}
      <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 flex items-start gap-3 text-amber-200 text-xs md:text-sm">
        <AlertTriangle className="w-5 h-5 shrink-0 text-amber-400 mt-0.5" />
        <div>
          <strong className="text-amber-300">Golden Cyber Rule:</strong> A payment screenshot{" "}
          <strong>NEVER proves that money was received</strong>. Fraudsters use spoof apps (e.g. fake Paytm/PhonePe generators) to fake "Payment Successful" screens. Always check your actual bank balance in your official banking app.
        </div>
      </div>

      {/* Preset Test Chips */}
      <div className="space-y-2">
        <div className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          Test with Real Fraud Screenshot Samples:
        </div>
        <div className="flex flex-wrap gap-2">
          {PRESET_IMAGE_SAMPLES.map((preset, idx) => (
            <button
              key={idx}
              onClick={() => handlePresetSelect(preset.text)}
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-cyan-500 hover:text-cyan-300 text-slate-300 transition-colors"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Upload Box Card */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-6">
        {error && (
          <div className="p-3 rounded-xl bg-red-950/60 border border-red-800 text-red-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Dropzone */}
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-700 hover:border-cyan-500 rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-colors bg-slate-950/50 min-h-[220px]"
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="image/png,image/jpeg,image/webp"
              className="hidden"
            />
            {imagePreview ? (
              <div className="space-y-3">
                <img
                  src={imagePreview}
                  alt="Screenshot Preview"
                  className="max-h-40 max-w-full rounded-lg object-contain mx-auto border border-slate-800"
                />
                <div className="text-xs text-cyan-400 font-semibold truncate max-w-xs mx-auto">
                  {selectedFile?.name} ({(selectedFile?.size ? selectedFile.size / 1024 : 0).toFixed(1)} KB)
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mx-auto">
                  <Upload className="w-6 h-6" />
                </div>
                <div className="text-sm font-semibold text-slate-200">
                  Click or drag screenshot here
                </div>
                <div className="text-xs text-slate-500">
                  Supports JPG, PNG, WEBP (Max 15MB)
                </div>
              </div>
            )}
          </div>

          {/* OCR Text / Manual Verification Input */}
          <div className="space-y-2 flex flex-col justify-between">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5 flex items-center justify-between">
                <span>Extracted / Sample Receipt Text</span>
                <span className="text-[10px] text-slate-500">Optional Text Override</span>
              </label>
              <textarea
                rows={7}
                value={textOverride}
                onChange={(e) => setTextOverride(e.target.value)}
                placeholder="Text extracted from image or preset text will appear here. You can also paste text directly to simulate OCR..."
                className="w-full p-3.5 rounded-xl bg-slate-950 border border-slate-800 focus:border-cyan-500 text-xs text-slate-100 placeholder-slate-600 focus:outline-none transition-colors"
              />
            </div>
            <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
              <ScanLine className="w-3.5 h-3.5 text-cyan-400" />
              OCR extracts text locally • SHA-256 tamper verification
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 border-t border-slate-800/80">
          <div className="text-[11px] text-slate-500">
            Files stored locally in isolated vault • Zero cloud leak
          </div>

          <button
            onClick={handleScan}
            disabled={loading || !selectedFile}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm shadow-md shadow-cyan-500/20 disabled:opacity-50 transition-all"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Processing Image & OCR...
              </>
            ) : (
              <>
                <FileSearch className="w-4 h-4" />
                Audit Screenshot Fraud
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
            {/* Risk Gauge */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
              <div className="text-xs font-semibold text-slate-400">Calculated Fraud Risk</div>
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

            {/* Detection Summary */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
              <div className="text-xs font-semibold text-slate-400">Screenshot Classification</div>
              <div className="my-2 space-y-1">
                <div className="text-lg font-bold text-white">
                  {result.scam_category.replace(/_/g, " ")}
                </div>
                <div className="text-xs text-slate-400">
                  OCR Engine: <span className="font-mono text-cyan-400">{result.ocr_engine}</span>
                </div>
              </div>
              <div className="text-[11px] text-slate-500 font-mono truncate">
                SHA-256: {result.file_hash.substring(0, 16)}...
              </div>
            </div>

            {/* Community Escalation */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
              <div className="text-xs font-semibold text-slate-400">Community Intelligence</div>
              <p className="text-xs text-slate-300 my-2">
                Escalate this fraudulent screenshot to warn other citizens.
              </p>
              {reportSuccess ? (
                <div className="text-xs text-emerald-400 font-semibold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  {reportSuccess}
                </div>
              ) : (
                <button
                  onClick={handleReport}
                  disabled={reporting}
                  className="w-full flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all"
                >
                  <Send className="w-3.5 h-3.5" />
                  {reporting ? "Submitting Report..." : "Submit to Threat Intel"}
                </button>
              )}
            </div>
          </div>

          {/* Payment Screenshot Entity Diagnostics */}
          {result.detected_entities && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-3">
                <CreditCard className="w-6 h-6 text-cyan-400" />
                <div>
                  <div className="text-[11px] text-slate-500">Payment Screen</div>
                  <div className="text-xs font-bold text-slate-200">
                    {result.detected_entities.is_payment_screenshot ? "Detected" : "None"}
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-3">
                <Hash className="w-6 h-6 text-amber-400" />
                <div>
                  <div className="text-[11px] text-slate-500">Amounts Found</div>
                  <div className="text-xs font-bold text-slate-200">
                    {result.detected_entities.amounts_mentioned?.length
                      ? result.detected_entities.amounts_mentioned.join(", ")
                      : "None"}
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-3">
                <ScanLine className="w-6 h-6 text-blue-400" />
                <div>
                  <div className="text-[11px] text-slate-500">UTR / Txn ID</div>
                  <div className="text-xs font-bold text-slate-200 truncate max-w-[120px]">
                    {result.detected_entities.utr_references?.length
                      ? result.detected_entities.utr_references[0]
                      : "None"}
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-3">
                <FileText className="w-6 h-6 text-emerald-400" />
                <div>
                  <div className="text-[11px] text-slate-500">Apps Identified</div>
                  <div className="text-xs font-bold text-slate-200 uppercase truncate max-w-[120px]">
                    {result.detected_entities.detected_apps?.length
                      ? result.detected_entities.detected_apps.join(", ")
                      : "General"}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Extracted Text Inspector */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ScanLine className="w-4 h-4 text-cyan-400" />
              Extracted OCR Text & Forensic Stream
            </h3>
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 leading-relaxed max-h-48 overflow-y-auto">
              {result.extracted_text}
            </div>

            {result.highlighted_tokens.length > 0 && (
              <div className="pt-2">
                <span className="text-xs font-semibold text-slate-400">Trigger Tokens: </span>
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

          {/* Recommendations Card */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Forensic Safety Advice
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

