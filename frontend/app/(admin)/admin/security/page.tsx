"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  HardDrive,
  Users,
  Activity,
  Cpu,
  RefreshCw,
  Megaphone,
  CheckCircle2,
  FileSpreadsheet,
  Lock,
  Database
} from "lucide-react";
import {
  fetchAdminTelemetry,
  broadcastAdminNotification,
  SystemHealthTelemetry
} from "@/lib/api";

export default function AdminSecurityMonitoringPage() {
  const [telemetry, setTelemetry] = useState<SystemHealthTelemetry | null>(null);
  const [loading, setLoading] = useState(true);

  // Broadcast modal
  const [showBroadcastModal, setShowBroadcastModal] = useState(false);
  const [bTitle, setBTitle] = useState("");
  const [bMessage, setBMessage] = useState("");
  const [bCategory, setBCategory] = useState("SECURITY_ALERT");
  const [broadcasting, setBroadcasting] = useState(false);
  const [broadcastResult, setBroadcastResult] = useState<string | null>(null);

  useEffect(() => {
    loadTelemetry();
  }, []);

  const loadTelemetry = async () => {
    try {
      setLoading(true);
      const data = await fetchAdminTelemetry();
      setTelemetry(data);
    } catch {
      // Error
    } finally {
      setLoading(false);
    }
  };

  const handleBroadcast = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bTitle || !bMessage) return;

    setBroadcasting(true);
    try {
      const res = await broadcastAdminNotification({
        title: bTitle,
        message: bMessage,
        category: bCategory
      });
      setBroadcastResult(`Successfully broadcasted to ${res.recipient_count} citizens!`);
      setShowBroadcastModal(false);
      setBTitle("");
      setBMessage("");
      loadTelemetry();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to broadcast notification");
    } finally {
      setBroadcasting(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Top Banner */}
      <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0 border border-rose-500/30">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-black text-white">SOC Telemetry &amp; System Health</h1>
              <span className="px-2.5 py-0.5 text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-full">
                All Services Nominal
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-300 mt-0.5">
              Live operational health monitoring, storage vault utilization, and citizen security alert dispatch.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowBroadcastModal(true)}
            className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow-md transition-colors flex items-center gap-1.5"
          >
            <Megaphone className="w-3.5 h-3.5" />
            Broadcast Alert
          </button>

          <button
            type="button"
            onClick={loadTelemetry}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {broadcastResult && (
        <div className="p-4 bg-emerald-950/60 border border-emerald-500/50 rounded-2xl text-xs text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{broadcastResult}</span>
        </div>
      )}

      {/* Telemetry Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-5 bg-slate-900 border border-slate-800 rounded-3xl space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold uppercase tracking-wider">
            <span>Database Engine</span>
            <Database className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-lg font-black text-white">{telemetry?.database.split(" ")[0]}</div>
          <p className="text-[11px] text-emerald-400 flex items-center gap-1 font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            Ready for PostgreSQL
          </p>
        </div>

        <div className="p-5 bg-slate-900 border border-slate-800 rounded-3xl space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold uppercase tracking-wider">
            <span>Registered Citizens</span>
            <Users className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black text-white">{telemetry?.total_users ?? 0}</div>
          <p className="text-[11px] text-slate-400">
            {telemetry?.active_users ?? 0} Active Citizen Accounts
          </p>
        </div>

        <div className="p-5 bg-slate-900 border border-slate-800 rounded-3xl space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold uppercase tracking-wider">
            <span>Total AI Scans</span>
            <Activity className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-amber-400">{telemetry?.total_scans ?? 0}</div>
          <p className="text-[11px] text-slate-400">
            Scam, URL, Image, Forensics, PII
          </p>
        </div>

        <div className="p-5 bg-slate-900 border border-slate-800 rounded-3xl space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold uppercase tracking-wider">
            <span>Evidence Vault</span>
            <HardDrive className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-black text-white">
            {formatBytes(telemetry?.evidence_vault_bytes ?? 0)}
          </div>
          <p className="text-[11px] text-slate-400">
            {telemetry?.total_evidence_files ?? 0} SHA-256 Evidence Files
          </p>
        </div>
      </div>

      {/* Threat and Event Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 bg-slate-900 border border-slate-800 rounded-3xl space-y-2">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
            Verified Threat Indicators
          </span>
          <div className="text-3xl font-black text-rose-400">
            {telemetry?.active_threat_indicators ?? 0}
          </div>
          <p className="text-xs text-slate-400">
            Actively protecting citizens across URLs and scam numbers.
          </p>
        </div>

        <div className="p-5 bg-slate-900 border border-slate-800 rounded-3xl space-y-2">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
            Community Reports Submitted
          </span>
          <div className="text-3xl font-black text-cyan-400">
            {telemetry?.total_reports ?? 0}
          </div>
          <p className="text-xs text-slate-400">
            {telemetry?.verified_threats ?? 0} Verified by SOC Moderation Team
          </p>
        </div>

        <div className="p-5 bg-slate-900 border border-slate-800 rounded-3xl space-y-2">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
            Security Audit Trail Events
          </span>
          <div className="text-3xl font-black text-purple-400">
            {telemetry?.audit_logs_count ?? 0}
          </div>
          <p className="text-xs text-slate-400">
            Append-only tamper evident audit records.
          </p>
        </div>
      </div>

      {/* Hardened Architecture Directives */}
      <div className="p-6 bg-slate-900 border border-slate-800 rounded-3xl space-y-4">
        <h3 className="font-bold text-sm text-white flex items-center gap-2">
          <Lock className="w-4 h-4 text-cyan-400" />
          Security Architecture &amp; Compliance Directives
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-slate-300">
          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-white block">Argon2id Password Hashing</span>
              State-of-the-art memory-hard key derivation resisting GPU/ASIC brute forcing.
            </div>
          </div>

          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-white block">SSRF Defense Gateway</span>
              Strict blocking of loopback, RFC 1918 private subnets, and cloud metadata (169.254.169.254).
            </div>
          </div>

          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-white block">Zero Cloud AI Leaks</span>
              All sensitive PII redaction and Error Level Analysis conducted on-device in local memory.
            </div>
          </div>

          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-white block">SHA-256 Tamper-Evident Hashing</span>
              Evidence files hashed with SHA-256 and stored using UUID aliases preventing path traversal.
            </div>
          </div>
        </div>
      </div>

      {/* Broadcast Alert Modal */}
      {showBroadcastModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
                <Megaphone className="w-4 h-4 text-rose-400" />
                Broadcast Security Announcement
              </h3>
              <button onClick={() => setShowBroadcastModal(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <form onSubmit={handleBroadcast} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Headline Title *</label>
                <input
                  type="text"
                  required
                  value={bTitle}
                  onChange={(e) => setBTitle(e.target.value)}
                  placeholder="e.g. CRITICAL: New Bank KYC Phishing Campaign Active"
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-rose-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Alert Message *</label>
                <textarea
                  required
                  rows={3}
                  value={bMessage}
                  onChange={(e) => setBMessage(e.target.value)}
                  placeholder="Provide urgent actionable guidance for citizens..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-slate-100 focus:outline-none focus:border-rose-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Category</label>
                <select
                  value={bCategory}
                  onChange={(e) => setBCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-rose-500"
                >
                  <option value="SECURITY_ALERT">Security Alert (High Urgency)</option>
                  <option value="SYSTEM_NOTICE">System Maintenance Notice</option>
                  <option value="COMMUNITY_WARNING">Community Threat Warning</option>
                </select>
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowBroadcastModal(false)}
                  className="flex-1 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={broadcasting}
                  className="flex-1 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs"
                >
                  {broadcasting ? "Broadcasting..." : "Dispatch Alert"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

