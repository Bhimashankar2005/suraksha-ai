"use client";

import React, { useState, useEffect } from "react";
import {
  Video,
  Upload,
  FileCheck,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  Shield,
  Eye,
  Volume2,
  FileSpreadsheet,
  Clock,
  Sparkles,
  Info,
  Share2,
  ExternalLink
} from "lucide-react";
import {
  analyzeMediaAuthenticity,
  fetchDeepfakeHistory,
  reportDeepfakeScan,
  DeepfakeScanResponse,
  DeepfakeHistoryItem
} from "@/lib/api";

export default function DeepfakeAnalysisPage() {
  const [file, setFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DeepfakeScanResponse | null>(null);
  const [history, setHistory] = useState<DeepfakeHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Reporting modal
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportDesc, setReportDesc] = useState("");
  const [reporting, setReporting] = useState(false);
  const [reportResult, setReportResult] = useState<string | null>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      setHistoryLoading(true);
      const data = await fetchDeepfakeHistory();
      setHistory(data);
    } catch {
      // User might be guest
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleAnalyze = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!file) return;

    setAnalyzing(true);
    setError(null);
    setReportResult(null);

    try {
      const res = await analyzeMediaAuthenticity(file);
      setResult(res);
      loadHistory();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to analyze media file.");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleReportThreat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!result?.id) return;

    setReporting(true);
    try {
      const res = await reportDeepfakeScan(result.id, reportDesc || undefined);
      setReportResult(`Incident reported successfully! Reference Code: ${res.report_code}`);
      setShowReportModal(false);
      setReportDesc("");
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to report incident");
    } finally {
      setReporting(false);
    }
  };

  // Preset sample creators
  const handleLoadSample = (sampleType: "ai_art" | "cloned_voice" | "camera_photo") => {
    if (sampleType === "ai_art") {
      const content = "RIFF\x20\x00\x00\x00WEBPVP8 Software: Midjourney v6.0 prompt: ultra realistic face close-up, 8k";
      const sampleBlob = new Blob([content], { type: "image/webp" });
      const sampleFile = new File([sampleBlob], "sample_ai_portrait.webp", { type: "image/webp" });
      setFile(sampleFile);
    } else if (sampleType === "cloned_voice") {
      const content = "RIFF\x24\x00\x00\x00WAVEfmt Generated via ElevenLabs Speech Synthesis Engine voice_id=adam";
      const sampleBlob = new Blob([content], { type: "audio/wav" });
      const sampleFile = new File([sampleBlob], "sample_cloned_voice.wav", { type: "audio/wav" });
      setFile(sampleFile);
    } else {
      // 100x100 simple BMP header simulating standard camera
      const header = new Uint8Array([
        0x42, 0x4D, 0x46, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x36, 0x00, 0x00, 0x00,
        0x28, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x01, 0x00,
        0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x13, 0x0B, 0x00, 0x00,
        0x13, 0x0B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
      ]);
      const sampleBlob = new Blob([header], { type: "image/bmp" });
      const sampleFile = new File([sampleBlob], "authentic_camera_photo.bmp", { type: "image/bmp" });
      setFile(sampleFile);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="p-5 sm:p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl space-y-3">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center shrink-0 border border-cyan-500/30">
              <Video className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-black text-white">
                  Deepfake &amp; Media Authenticity Forensics
                </h1>
                <span className="px-2.5 py-0.5 text-xs font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 rounded-full">
                  Module 8
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-300 mt-0.5">
                On-device Error Level Analysis (ELA), EXIF software metadata audit, and neural voice synthesis detection.
              </p>
            </div>
          </div>
        </div>

        {/* Preset Sample Test Buttons */}
        <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            Test Preset Samples:
          </span>
          <button
            type="button"
            onClick={() => handleLoadSample("ai_art")}
            className="text-xs px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
          >
            🖼️ AI Diffusion Headshot (Midjourney/SD)
          </button>
          <button
            type="button"
            onClick={() => handleLoadSample("cloned_voice")}
            className="text-xs px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
          >
            🎙️ Voice Cloned Audio (ElevenLabs)
          </button>
          <button
            type="button"
            onClick={() => handleLoadSample("camera_photo")}
            className="text-xs px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
          >
            📷 Authentic Unmanipulated Media
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Upload & Analysis Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Upload Dropzone */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <Upload className="w-4 h-4 text-cyan-400" />
              Upload Media for Forensic Analysis
            </h2>
            <p className="text-xs text-slate-400">
              Supports Images (.jpg, .png, .webp), Audio (.wav, .mp3), and Video (.mp4, .webm) up to 25MB. Processed strictly on-device without cloud leakage.
            </p>

            <form onSubmit={handleAnalyze} className="space-y-4">
              <div className="border-2 border-dashed border-slate-700 hover:border-cyan-500 rounded-2xl p-6 text-center transition-colors bg-slate-950/60 cursor-pointer relative">
                <input
                  type="file"
                  onChange={handleFileChange}
                  accept="image/*,audio/*,video/*"
                  className="absolute inset-0 opacity-0 cursor-pointer"
                />
                <div className="flex flex-col items-center justify-center gap-2">
                  <div className="w-12 h-12 rounded-xl bg-slate-800 text-slate-300 flex items-center justify-center">
                    {file?.type.startsWith("audio") ? (
                      <Volume2 className="w-6 h-6 text-cyan-400" />
                    ) : file?.type.startsWith("video") ? (
                      <Video className="w-6 h-6 text-cyan-400" />
                    ) : (
                      <Eye className="w-6 h-6 text-cyan-400" />
                    )}
                  </div>
                  <div>
                    <span className="text-xs sm:text-sm font-bold text-white">
                      {file ? file.name : "Drop media file here, or click to browse"}
                    </span>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {file ? `${(file.size / 1024).toFixed(1)} KB • Ready to inspect` : "JPG, PNG, WEBP, MP3, WAV, MP4 up to 25MB"}
                    </p>
                  </div>
                </div>
              </div>

              {error && (
                <div className="p-3 bg-red-950/60 border border-red-500/50 rounded-xl text-xs text-red-300">
                  {error}
                </div>
              )}

              {reportResult && (
                <div className="p-3 bg-emerald-950/60 border border-emerald-500/50 rounded-xl text-xs text-emerald-300">
                  {reportResult}
                </div>
              )}

              <button
                type="submit"
                disabled={analyzing || !file}
                className="w-full py-3 px-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold rounded-xl text-xs sm:text-sm shadow-lg shadow-cyan-900/30 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
              >
                {analyzing ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    Running Error Level Analysis &amp; Metadata Inspection...
                  </>
                ) : (
                  <>
                    <Shield className="w-4 h-4" />
                    Run Deepfake &amp; Authenticity Scan
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Analysis Results */}
          {result && (
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-6 animate-in fade-in duration-200">
              {/* Verdict Banner */}
              <div
                className={`p-5 rounded-2xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${
                  result.verdict === "PROBABLE_SYNTHETIC_OR_MANIPULATED"
                    ? "bg-red-950/60 border-red-500 text-red-100"
                    : result.verdict === "SUSPICIOUS_ANOMALIES_DETECTED"
                    ? "bg-amber-950/60 border-amber-500 text-amber-100"
                    : "bg-emerald-950/60 border-emerald-500 text-emerald-100"
                }`}
              >
                <div>
                  <div className="text-[11px] font-bold uppercase tracking-wider opacity-80">
                    Forensic Verdict
                  </div>
                  <div className="text-xl sm:text-2xl font-black mt-0.5">
                    {result.verdict.replace(/_/g, " ")}
                  </div>
                  <div className="text-xs opacity-80 mt-1 font-mono">
                    SHA-256: {result.file_hash.slice(0, 16)}... • {result.media_type} ({result.file_size_kb} KB)
                  </div>
                </div>

                <div className="text-left sm:text-right shrink-0">
                  <div className="text-[11px] font-bold uppercase tracking-wider opacity-80">
                    Authenticity Confidence
                  </div>
                  <div className="text-3xl font-black">{result.authenticity_score}/100</div>
                  <div className="text-[10px] opacity-75">
                    {result.authenticity_score >= 70 ? "High Authenticity" : result.authenticity_score <= 40 ? "High Synthetic Probability" : "Equivocal / Inconclusive"}
                  </div>
                </div>
              </div>

              {/* Forensic Indicators Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Suspicious Risk Factors */}
                <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2.5">
                  <div className="text-xs font-bold text-red-400 uppercase tracking-wider flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4" />
                    Suspicious Indicators ({result.forensic_flags.suspicious_factors.length})
                  </div>
                  {result.forensic_flags.suspicious_factors.length === 0 ? (
                    <p className="text-xs text-slate-500">No overt tampering factors identified.</p>
                  ) : (
                    <ul className="space-y-1.5">
                      {result.forensic_flags.suspicious_factors.map((f, i) => (
                        <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
                          <span className="text-red-400 font-bold shrink-0">•</span>
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* Positive Authenticity Indicators */}
                <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2.5">
                  <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                    <CheckCircle className="w-4 h-4" />
                    Authenticity Markers ({result.forensic_flags.authenticity_indicators.length})
                  </div>
                  {result.forensic_flags.authenticity_indicators.length === 0 ? (
                    <p className="text-xs text-slate-500">No camera metadata or provenance signatures found.</p>
                  ) : (
                    <ul className="space-y-1.5">
                      {result.forensic_flags.authenticity_indicators.map((f, i) => (
                        <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
                          <span className="text-emerald-400 font-bold shrink-0">•</span>
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>

              {/* Error Level Analysis Details (If Image) */}
              {result.forensic_flags.ela_analysis && (
                <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
                  <div className="text-xs font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4" />
                    Error Level Analysis (ELA) Metrics
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
                      <span className="text-[10px] text-slate-400 block">Mean Error</span>
                      <span className="font-bold text-white text-sm">
                        {result.forensic_flags.ela_analysis.mean_error_level}
                      </span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
                      <span className="text-[10px] text-slate-400 block">Std Dev</span>
                      <span className="font-bold text-white text-sm">
                        {result.forensic_flags.ela_analysis.error_std_dev}
                      </span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
                      <span className="text-[10px] text-slate-400 block">Regional Variance</span>
                      <span className="font-bold text-white text-sm">
                        {result.forensic_flags.ela_analysis.regional_variance}
                      </span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
                      <span className="text-[10px] text-slate-400 block">Anomaly Detected</span>
                      <span className={`font-bold text-sm ${result.forensic_flags.ela_analysis.ela_anomaly_flag ? "text-red-400" : "text-emerald-400"}`}>
                        {result.forensic_flags.ela_analysis.ela_anomaly_flag ? "YES (Spliced)" : "NO (Uniform)"}
                      </span>
                    </div>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Assessment: {result.forensic_flags.ela_analysis.assessment}
                  </p>
                </div>
              )}

              {/* Action Bar: Report Threat */}
              <div className="p-4 rounded-2xl bg-gradient-to-r from-slate-900 to-slate-950 border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-bold text-white">Escalate to Community Cyber Threat Intelligence</div>
                  <div className="text-[11px] text-slate-400">
                    If this media is used in an impersonation, extortion, or investment fraud, publish it to alert others.
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setShowReportModal(true)}
                  className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shrink-0 flex items-center gap-1.5 transition-colors"
                >
                  <Share2 className="w-3.5 h-3.5" />
                  Report Suspicious Media
                </button>
              </div>

              {/* Statutory Disclaimer */}
              <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2.5">
                <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <span>{result.limitations_disclaimer}</span>
              </div>
            </div>
          )}
        </div>

        {/* Right Sidebar: Past Scans & Forensic Guide */}
        <div className="space-y-6">
          {/* History Drawer */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-cyan-400" />
                My Forensic Scans
              </h3>
              <span className="text-xs text-slate-500">{history.length} records</span>
            </div>

            {historyLoading ? (
              <div className="text-center py-6 text-xs text-slate-500">Loading history...</div>
            ) : history.length === 0 ? (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center text-xs text-slate-400">
                No past media scans recorded yet.
              </div>
            ) : (
              <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
                {history.map((item) => (
                  <div
                    key={item.id}
                    className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-white truncate max-w-[140px]">
                        {item.file_name || "media_file"}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          item.authenticity_score < 40
                            ? "bg-red-500/20 text-red-300"
                            : item.authenticity_score < 70
                            ? "bg-amber-500/20 text-amber-300"
                            : "bg-emerald-500/20 text-emerald-300"
                        }`}
                      >
                        {item.authenticity_score}%
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400 flex items-center justify-between">
                      <span>{item.media_type}</span>
                      <span>{new Date(item.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Educational Quick Guide */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-5 space-y-3 text-xs text-slate-300">
            <h4 className="font-bold text-white text-xs uppercase tracking-wider flex items-center gap-1.5">
              <HelpCircle className="w-4 h-4 text-cyan-400" />
              How Deepfake Detection Works
            </h4>
            <p className="text-[11px] text-slate-400">
              1. **Error Level Analysis (ELA)**: Detects compression discrepancies across regions when an image is repeatedly re-saved or infilled.
            </p>
            <p className="text-[11px] text-slate-400">
              2. **Metadata Traces**: Inspects text chunks for generative prompts from Midjourney, Stable Diffusion, or video muxers.
            </p>
            <p className="text-[11px] text-slate-400">
              3. **Audio Fingerprints**: Checks for unnatural mono 16kHz sampling and absence of natural breathing in cloned speech.
            </p>
          </div>
        </div>
      </div>

      {/* Escalation Modal */}
      {showReportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-white">Escalate Threat to Community Intelligence</h3>
              <button
                onClick={() => setShowReportModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleReportThreat} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Incident Description &amp; Scam Context
                </label>
                <textarea
                  rows={3}
                  value={reportDesc}
                  onChange={(e) => setReportDesc(e.target.value)}
                  placeholder="Explain how this synthetic media was used (e.g., impersonation call, blackmail threat, false endorsement)..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-slate-100 focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowReportModal(false)}
                  className="flex-1 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={reporting}
                  className="flex-1 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs"
                >
                  {reporting ? "Submitting..." : "Submit Community Report"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

