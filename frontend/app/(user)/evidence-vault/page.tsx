"use client";

import React, { useState, useEffect } from "react";
import {
  Lock,
  Upload,
  FileText,
  FileCheck2,
  Trash2,
  Download,
  Copy,
  Check,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Clock,
  IndianRupee,
  PlusCircle,
  ExternalLink,
  RefreshCw,
  FolderLock,
  FileSpreadsheet,
  FileCode,
  Calendar,
  CheckCircle2,
  Printer
} from "lucide-react";
import {
  uploadEvidenceFile,
  fetchUserVault,
  fetchUserVaultStats,
  deleteEvidenceFile,
  compileIncidentDossier,
  fetchIncidentDossiers,
  EvidenceFileItem,
  IncidentReportResponse,
  EvidenceVaultStats,
  API_BASE_URL
} from "@/lib/api";

type VaultTab = "vault" | "upload" | "dossiers";

const CATEGORIES = [
  { value: "UPI_FRAUD", label: "UPI & Payment Fraud" },
  { value: "FAKE_BANK", label: "Fake Bank & KYC Scam" },
  { value: "DIGITAL_ARREST", label: "Digital Arrest / Police Impersonation" },
  { value: "BLACKMAIL", label: "Cyber Harassment & Blackmail" },
  { value: "IDENTITY_THEFT", label: "Identity Theft & SIM Cloning" },
  { value: "OTHER", label: "Other Cyber Incident" }
];

export default function EvidenceVaultPage() {
  const [activeTab, setActiveTab] = useState<VaultTab>("vault");
  const [files, setFiles] = useState<EvidenceFileItem[]>([]);
  const [stats, setStats] = useState<EvidenceVaultStats | null>(null);
  const [dossiers, setDossiers] = useState<IncidentReportResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Upload Form State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadCategory, setUploadCategory] = useState<string>("UPI_FRAUD");
  const [uploadDate, setUploadDate] = useState<string>(new Date().toISOString().slice(0, 16));
  const [uploadDesc, setUploadDesc] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<EvidenceFileItem | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Dossier Generator Form State
  const [dossierTitle, setDossierTitle] = useState("");
  const [dossierCategory, setDossierCategory] = useState("UPI_FRAUD");
  const [financialLoss, setFinancialLoss] = useState<number>(0);
  const [timelineSummary, setTimelineSummary] = useState("");
  const [selectedEvidenceIds, setSelectedEvidenceIds] = useState<string[]>([]);
  const [generatingDossier, setGeneratingDossier] = useState(false);
  const [dossierError, setDossierError] = useState<string | null>(null);
  const [activeDossierPreview, setActiveDossierPreview] = useState<IncidentReportResponse | null>(null);

  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  const loadVaultData = async () => {
    setRefreshing(true);
    try {
      const [vaultRes, statsRes, dossiersRes] = await Promise.all([
        fetchUserVault().catch(() => []),
        fetchUserVaultStats().catch(() => null),
        fetchIncidentDossiers().catch(() => [])
      ]);
      setFiles(vaultRes);
      if (statsRes) setStats(statsRes);
      setDossiers(dossiersRes);
    } catch (err) {
      console.error("Vault load error:", err);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadVaultData();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      if (f.size > 15 * 1024 * 1024) {
        setUploadError("File size exceeds maximum allowed 15MB limit.");
        return;
      }
      setSelectedFile(f);
      setUploadError(null);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError("Please select a file to upload.");
      return;
    }

    setUploading(true);
    setUploadError(null);
    try {
      const res = await uploadEvidenceFile(
        selectedFile,
        uploadCategory,
        uploadDate,
        uploadDesc.trim() || undefined
      );
      setUploadSuccess(res);
      setSelectedFile(null);
      setUploadDesc("");
      loadVaultData();
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload evidence.");
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    if (!confirm("Are you sure you want to permanently delete this evidence file?")) return;
    try {
      await deleteEvidenceFile(fileId);
      loadVaultData();
    } catch (err: any) {
      alert("Failed to delete file: " + err.message);
    }
  };

  const handleDownloadFile = (fileId: string) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const url = `${API_BASE_URL}/evidence/${fileId}/download`;
    // Trigger direct download
    fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then((res) => {
        if (!res.ok) throw new Error("Download failed");
        return res.blob();
      })
      .then((blob) => {
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `evidence-${fileId.slice(0, 8)}.dat`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      })
      .catch((err) => alert("Download error: " + err.message));
  };

  const handleToggleEvidenceSelect = (id: string) => {
    setSelectedEvidenceIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleCreateDossier = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dossierTitle.trim() || !timelineSummary.trim()) {
      setDossierError("Please provide an incident title and timeline summary.");
      return;
    }

    setGeneratingDossier(true);
    setDossierError(null);
    try {
      const res = await compileIncidentDossier({
        incident_title: dossierTitle.trim(),
        category: dossierCategory,
        total_financial_loss: Number(financialLoss) || 0.0,
        timeline_summary: timelineSummary.trim(),
        evidence_file_ids: selectedEvidenceIds
      });
      setActiveDossierPreview(res);
      setDossierTitle("");
      setTimelineSummary("");
      setFinancialLoss(0);
      setSelectedEvidenceIds([]);
      loadVaultData();
    } catch (err: any) {
      setDossierError(err.message || "Failed to compile dossier.");
    } finally {
      setGeneratingDossier(false);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(id);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-cyan-600 to-emerald-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <FolderLock className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-black text-white flex items-center gap-2">
              Cybercrime Evidence Vault & Legal Dossiers
              <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                SHA-256 Verified
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Tamper-evident evidence storage • Cryptographic integrity hashes • 1930 / cybercrime.gov.in ready
            </p>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab("vault")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "vault"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Secured Vault ({files.length})
          </button>
          <button
            onClick={() => setActiveTab("upload")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "upload"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Upload Evidence
          </button>
          <button
            onClick={() => setActiveTab("dossiers")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "dossiers"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Police Dossiers ({dossiers.length})
          </button>
        </div>
      </div>

      {/* Official Reporting Callout */}
      <div className="bg-gradient-to-r from-cyan-950/40 via-slate-900 to-slate-900 border border-cyan-500/30 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-lg">
        <div className="flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
          <div className="text-xs text-slate-300">
            <strong>OFFICIAL POLICE NOTICE:</strong> SURAKSHA AI preserves cryptographic evidence for legal presentation.
            To freeze fraudulent bank accounts, call <strong>1930</strong> or register at{" "}
            <a href="https://cybercrime.gov.in" target="_blank" rel="noreferrer" className="text-cyan-400 underline font-semibold">
              cybercrime.gov.in
            </a>{" "}
            within the <strong>Golden Hour</strong>.
          </div>
        </div>
        <a
          href="tel:1930"
          className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-black text-xs shrink-0 text-center transition-colors shadow-md shadow-amber-500/20"
        >
          CALL 1930
        </a>
      </div>

      {/* Vault Telemetry Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Secured Files
          </div>
          <div className="text-2xl font-black text-white mt-1">
            {stats ? stats.total_files : files.length}
          </div>
          <div className="text-[10px] text-cyan-400 mt-0.5">Isolated local storage</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Vault Storage
          </div>
          <div className="text-2xl font-black text-cyan-400 mt-1">
            {stats ? formatBytes(stats.total_size_bytes) : "—"}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">Tamper-evident hashed</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Incident Dossiers
          </div>
          <div className="text-2xl font-black text-emerald-400 mt-1">
            {stats ? stats.total_incident_reports : dossiers.length}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">FIR-ready dossiers</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Documented Loss
          </div>
          <div className="text-2xl font-black text-rose-400 mt-1">
            ₹{stats ? stats.total_documented_loss_inr.toLocaleString("en-IN") : "0"}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">Financial fraud sum</div>
        </div>
      </div>

      {/* TAB 1: EVIDENCE VAULT */}
      {activeTab === "vault" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <FileCheck2 className="w-4 h-4 text-emerald-400" />
              Cryptographic Evidence Repository
            </h2>
            <button
              onClick={loadVaultData}
              disabled={refreshing}
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-cyan-400" : ""}`} />
              Refresh
            </button>
          </div>

          {files.length === 0 ? (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center space-y-3">
              <FolderLock className="w-12 h-12 text-slate-600 mx-auto" />
              <h3 className="text-base font-bold text-white">Evidence Vault is Empty</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                No evidence files stored yet. Upload bank statements, WhatsApp chat logs, or scam screenshots to generate tamper-evident SHA-256 hashes.
              </p>
              <button
                onClick={() => setActiveTab("upload")}
                className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs transition-colors"
              >
                Upload Evidence File
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {files.map((file) => (
                <div
                  key={file.id}
                  className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 shadow-lg space-y-3 transition-all"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-cyan-400 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
                        {file.file_code}
                      </span>
                      <span className="text-xs font-bold text-white truncate max-w-xs">
                        {file.original_name}
                      </span>
                      <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        {file.incident_category}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-slate-400">{formatBytes(file.file_size_bytes)}</span>
                      <span className="text-slate-600">•</span>
                      <span className="text-slate-400">
                        {new Date(file.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  {file.description && (
                    <p className="text-xs text-slate-300 bg-slate-950 p-2.5 rounded-xl border border-slate-800/80">
                      {file.description}
                    </p>
                  )}

                  {/* Tamper-Evident SHA-256 Bar */}
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                    <div className="flex items-center gap-2 overflow-hidden">
                      <span className="text-[10px] uppercase font-bold text-slate-500 shrink-0">
                        SHA-256:
                      </span>
                      <span className="font-mono text-[11px] text-emerald-400 truncate">
                        {file.sha256_hash}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => copyToClipboard(file.sha256_hash, file.id)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] flex items-center gap-1 transition-colors"
                        title="Copy SHA-256 Hash"
                      >
                        {copiedHash === file.id ? (
                          <>
                            <Check className="w-3 h-3 text-emerald-400" /> Copied
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" /> Copy Hash
                          </>
                        )}
                      </button>
                      <button
                        onClick={() => handleDownloadFile(file.id)}
                        className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                        title="Download Original File"
                      >
                        <Download className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteFile(file.id)}
                        className="p-1 rounded bg-slate-800 hover:bg-rose-950 text-rose-400 transition-colors"
                        title="Delete from Vault"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: UPLOAD EVIDENCE */}
      {activeTab === "upload" && (
        <div className="max-w-2xl mx-auto bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Upload className="w-5 h-5 text-cyan-400" />
              Secure Evidence Upload
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Supports JPEG, PNG, WEBP screenshots, PDF bank statements, and TXT logs up to 15MB.
            </p>
          </div>

          {uploadSuccess && (
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                  <CheckCircle2 className="w-5 h-5" />
                  Evidence Sealed and Hashed in Vault!
                </div>
                <button
                  onClick={() => setUploadSuccess(null)}
                  className="text-xs text-slate-400 hover:text-white"
                >
                  Dismiss
                </button>
              </div>
              <div className="text-xs text-slate-300 font-mono">
                Code: <strong className="text-cyan-400">{uploadSuccess.file_code}</strong>
              </div>
              <div className="text-[11px] font-mono text-emerald-400 bg-slate-950 p-2 rounded-lg border border-slate-800 truncate">
                SHA-256: {uploadSuccess.sha256_hash}
              </div>
            </div>
          )}

          {uploadError && (
            <div className="p-3 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          <form onSubmit={handleUploadSubmit} className="space-y-4">
            {/* File Dropzone */}
            <div className="border-2 border-dashed border-slate-800 hover:border-cyan-500/50 rounded-2xl p-6 text-center space-y-2 bg-slate-950/60 transition-colors">
              <Upload className="w-8 h-8 text-cyan-400 mx-auto" />
              <div className="text-xs font-bold text-white">
                {selectedFile ? selectedFile.name : "Select an Evidence File"}
              </div>
              <div className="text-[11px] text-slate-500">
                {selectedFile
                  ? `${formatBytes(selectedFile.size)} • Ready for hashing`
                  : "Drag and drop or browse from your device"}
              </div>
              <input
                type="file"
                id="evidenceFileInput"
                onChange={handleFileChange}
                accept=".jpg,.jpeg,.png,.webp,.pdf,.txt"
                className="hidden"
              />
              <label
                htmlFor="evidenceFileInput"
                className="inline-block px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold cursor-pointer transition-colors mt-2"
              >
                Browse Files
              </label>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  Incident Category
                </label>
                <select
                  value={uploadCategory}
                  onChange={(e) => setUploadCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl px-4 py-2.5 text-xs text-white outline-none"
                >
                  {CATEGORIES.map((cat) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  Incident Date & Time
                </label>
                <input
                  type="datetime-local"
                  value={uploadDate}
                  onChange={(e) => setUploadDate(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl px-4 py-2.5 text-xs text-white outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5">
                Evidence Context / Description
              </label>
              <textarea
                value={uploadDesc}
                onChange={(e) => setUploadDesc(e.target.value)}
                placeholder="Describe what this screenshot, PDF, or chat log represents (e.g. fraudulent transaction on Google Pay, threatening WhatsApp call)..."
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl px-4 py-2.5 text-xs text-white outline-none"
              />
            </div>

            <button
              type="submit"
              disabled={!selectedFile || uploading}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-white font-bold text-xs transition-all shadow-lg shadow-cyan-600/20 disabled:opacity-50"
            >
              {uploading ? "Sealing & Calculating SHA-256..." : "Seal in Evidence Vault"}
            </button>
          </form>
        </div>
      )}

      {/* TAB 3: INCIDENT DOSSIERS (POLICE READY) */}
      {activeTab === "dossiers" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Dossier Compiler Form (Left 2 cols) */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-cyan-400" />
                Compile Structured Police Incident Dossier
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Combines incident narrative, documented financial loss, and cryptographic hashes of attached evidence for direct lodging on <strong>cybercrime.gov.in</strong>.
              </p>
            </div>

            {dossierError && (
              <div className="p-3 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{dossierError}</span>
              </div>
            )}

            <form onSubmit={handleCreateDossier} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1.5">
                    Incident Title
                  </label>
                  <input
                    type="text"
                    value={dossierTitle}
                    onChange={(e) => setDossierTitle(e.target.value)}
                    placeholder="e.g. Unauthorized UPI debit via Fake SBI KYC APK"
                    className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl px-4 py-2.5 text-xs text-white outline-none"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1.5">
                    Total Financial Loss (₹ INR)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={financialLoss}
                    onChange={(e) => setFinancialLoss(parseFloat(e.target.value) || 0)}
                    placeholder="e.g. 50000"
                    className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl px-4 py-2.5 text-xs text-white outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  Chronological Timeline Summary
                </label>
                <textarea
                  value={timelineSummary}
                  onChange={(e) => setTimelineSummary(e.target.value)}
                  placeholder="Detail the sequence: 1. Received scam message at 10:00 AM. 2. Clicked link at 10:15 AM. 3. Bank debited ₹50,000 via UTR 123456789012 at 10:20 AM..."
                  rows={4}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl px-4 py-2.5 text-xs text-white outline-none"
                  required
                />
              </div>

              {/* Attach Evidence Files Selector */}
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  Select Evidence to Seal into Dossier ({selectedEvidenceIds.length} selected)
                </label>
                {files.length === 0 ? (
                  <div className="text-xs text-slate-500 p-3 bg-slate-950 rounded-xl border border-slate-800">
                    No evidence files found in vault. Upload files first under "Upload Evidence".
                  </div>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto p-2 bg-slate-950 rounded-xl border border-slate-800">
                    {files.map((file) => (
                      <label
                        key={file.id}
                        className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-900 cursor-pointer text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={selectedEvidenceIds.includes(file.id)}
                            onChange={() => handleToggleEvidenceSelect(file.id)}
                            className="rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-0"
                          />
                          <span className="font-mono text-cyan-400 font-bold">{file.file_code}</span>
                          <span className="text-white truncate max-w-xs">{file.original_name}</span>
                        </div>
                        <span className="font-mono text-[10px] text-slate-500">
                          {file.sha256_hash.slice(0, 12)}...
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              <button
                type="submit"
                disabled={generatingDossier}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-xs transition-all shadow-lg shadow-cyan-600/20 disabled:opacity-50"
              >
                {generatingDossier ? "Compiling Cryptographic Dossier..." : "Compile Incident Dossier"}
              </button>
            </form>
          </div>

          {/* Dossiers History & Active Preview (Right 1 col) */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <FileCheck2 className="w-4 h-4 text-emerald-400" />
              Compiled Dossiers ({dossiers.length})
            </h3>

            {dossiers.length === 0 ? (
              <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl text-center text-xs text-slate-500">
                No dossiers compiled yet. Fill out the form to package your evidence.
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {dossiers.map((dos) => (
                  <div
                    key={dos.id}
                    onClick={() => setActiveDossierPreview(dos)}
                    className="p-3 bg-slate-900 border border-slate-800 hover:border-cyan-500/50 rounded-xl cursor-pointer transition-colors space-y-1"
                  >
                    <div className="text-xs font-bold text-white truncate">{dos.incident_title}</div>
                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <span>Loss: ₹{dos.total_financial_loss.toLocaleString("en-IN")}</span>
                      <span>{dos.evidence_files.length} Files Attached</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Dossier Printable / Inspection Modal */}
      {activeDossierPreview && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-400" />
                  Structured Cyber Incident Dossier
                </h3>
                <div className="text-xs text-slate-400">
                  Ready for official FIR filing at cybercrime.gov.in
                </div>
              </div>
              <button
                onClick={() => setActiveDossierPreview(null)}
                className="text-slate-400 hover:text-white p-1 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            {/* Dossier Content */}
            <div className="space-y-3 text-xs leading-relaxed">
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                <div className="text-sm font-bold text-cyan-400">{activeDossierPreview.incident_title}</div>
                <div className="grid grid-cols-2 gap-2 text-slate-300">
                  <div>
                    Category: <strong className="text-white">{activeDossierPreview.category}</strong>
                  </div>
                  <div>
                    Documented Loss:{" "}
                    <strong className="text-rose-400">
                      ₹{activeDossierPreview.total_financial_loss.toLocaleString("en-IN")}
                    </strong>
                  </div>
                </div>
                <div className="pt-2 border-t border-slate-800/80 text-slate-400">
                  Timeline Narrative:
                </div>
                <p className="text-slate-200 whitespace-pre-line">{activeDossierPreview.timeline_summary}</p>
              </div>

              {/* Attached Evidence Manifest */}
              <div className="space-y-2">
                <div className="font-bold text-slate-300">
                  Cryptographic Evidence Manifest ({activeDossierPreview.evidence_files.length} items):
                </div>
                <div className="space-y-1.5">
                  {activeDossierPreview.evidence_files.map((file) => (
                    <div
                      key={file.id}
                      className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between gap-2"
                    >
                      <div>
                        <span className="font-mono text-cyan-400 font-bold">{file.file_code}: </span>
                        <span className="text-white">{file.original_name}</span>
                      </div>
                      <span className="font-mono text-[10px] text-emerald-400 shrink-0">
                        SHA: {file.sha256_hash.slice(0, 16)}...
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Statutory Notice */}
              <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-[11px] text-amber-200">
                {activeDossierPreview.disclaimer}
              </div>
            </div>

            <div className="flex gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => window.print()}
                className="flex-1 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs transition-colors flex items-center justify-center gap-1.5"
              >
                <Printer className="w-3.5 h-3.5" /> Print Dossier
              </button>
              <button
                onClick={() => {
                  const blob = new Blob([JSON.stringify(activeDossierPreview, null, 2)], {
                    type: "application/json"
                  });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `incident-dossier-${activeDossierPreview.id.slice(0, 8)}.json`;
                  a.click();
                }}
                className="flex-1 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs transition-colors flex items-center justify-center gap-1.5 shadow-md shadow-cyan-600/20"
              >
                <Download className="w-3.5 h-3.5" /> Export JSON
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

