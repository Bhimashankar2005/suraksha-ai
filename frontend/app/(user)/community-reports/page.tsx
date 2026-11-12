"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Search,
  PlusCircle,
  FileText,
  AlertTriangle,
  Clock,
  CheckCircle2,
  XCircle,
  Copy,
  Check,
  Users,
  EyeOff,
  Filter,
  Phone,
  Link as LinkIcon,
  MessageSquare,
  Sparkles,
  RefreshCw,
  ExternalLink
} from "lucide-react";
import {
  submitThreatReport,
  trackReport,
  fetchUserReports,
  fetchThreatAlerts,
  fetchThreatStats,
  ReportItem,
  ReportTrackResponse,
  ThreatAlertItem,
  ThreatStats
} from "@/lib/api";

type TabMode = "feed" | "submit" | "track" | "my-reports";

const SAMPLE_PRESETS = [
  {
    type: "PHONE",
    target: "+91 98765 43210",
    desc: "Caller claimed electricity cutoff at 9:30 PM due to pending bill, demanded Rs 10 payment.",
    region: "Karnataka"
  },
  {
    type: "URL",
    target: "https://www-sbi-online-kyc-verify.top",
    desc: "Phishing SMS claiming bank account suspended, asking to download an APK file.",
    region: "Delhi"
  },
  {
    type: "PHONE",
    target: "+91 91234 56789",
    desc: "Digital arrest threat on WhatsApp call impersonating Mumbai Police officer.",
    region: "Maharashtra"
  }
];

const INDIAN_STATES = [
  "Karnataka",
  "Maharashtra",
  "Delhi NCR",
  "Tamil Nadu",
  "Telangana",
  "Uttar Pradesh",
  "West Bengal",
  "Gujarat",
  "Rajasthan",
  "Kerala",
  "Other"
];

export default function CommunityReportsPage() {
  const [activeTab, setActiveTab] = useState<TabMode>("feed");
  const [stats, setStats] = useState<ThreatStats | null>(null);
  const [alerts, setAlerts] = useState<ThreatAlertItem[]>([]);
  const [alertsFilter, setAlertsFilter] = useState<string>("ALL");
  const [myReports, setMyReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Form State
  const [threatType, setThreatType] = useState<string>("PHONE");
  const [targetValue, setTargetValue] = useState("");
  const [description, setDescription] = useState("");
  const [region, setRegion] = useState("Karnataka");
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [submittedReport, setSubmittedReport] = useState<ReportItem | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // Track State
  const [trackCode, setTrackCode] = useState("");
  const [trackedReport, setTrackedReport] = useState<ReportTrackResponse | null>(null);
  const [trackError, setTrackError] = useState<string | null>(null);
  const [copiedCode, setCopiedCode] = useState(false);

  // Load Initial Data
  const loadData = async () => {
    setRefreshing(true);
    try {
      const [statsRes, alertsRes] = await Promise.all([
        fetchThreatStats().catch(() => null),
        fetchThreatAlerts().catch(() => [])
      ]);
      if (statsRes) setStats(statsRes);
      setAlerts(alertsRes);

      // Try load user reports if token present
      fetchUserReports().then(setMyReports).catch(() => {});
    } catch (err) {
      console.error("Failed to load community intel:", err);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handlePresetSelect = (preset: typeof SAMPLE_PRESETS[0]) => {
    setThreatType(preset.type);
    setTargetValue(preset.target);
    setDescription(preset.desc);
    setRegion(preset.region);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!targetValue.trim() || !description.trim()) {
      setFormError("Please fill out the threat value and description.");
      return;
    }

    setLoading(true);
    try {
      const res = await submitThreatReport({
        threat_type: threatType,
        target_value: targetValue.trim(),
        description: description.trim(),
        region: region || undefined,
        is_anonymous: isAnonymous
      });
      setSubmittedReport(res);
      // Reset form fields
      setTargetValue("");
      setDescription("");
      loadData();
    } catch (err: any) {
      setFormError(err.message || "Failed to submit report. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleTrackSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!trackCode.trim()) return;

    setLoading(true);
    setTrackError(null);
    try {
      const res = await trackReport(trackCode.trim());
      setTrackedReport(res);
    } catch (err: any) {
      setTrackedReport(null);
      setTrackError(err.message || "Report code not found.");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  const filteredAlerts = alertsFilter === "ALL"
    ? alerts
    : alerts.filter((a) => a.indicator_type === alertsFilter);

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Users className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-black text-white flex items-center gap-2">
              Community Cyber Threat Intelligence
              <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                Live SOC Moderated
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Crowdsourced public digital safety • Anonymous submissions • Verified warning alerts
            </p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab("feed")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "feed"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Verified Alerts
          </button>
          <button
            onClick={() => setActiveTab("submit")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "submit"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Submit Threat
          </button>
          <button
            onClick={() => setActiveTab("track")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "track"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Track Status
          </button>
          <button
            onClick={() => setActiveTab("my-reports")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "my-reports"
                ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            My Reports ({myReports.length})
          </button>
        </div>
      </div>

      {/* Live Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Total Community Reports
          </div>
          <div className="text-2xl font-black text-white mt-1">
            {stats ? stats.total_reports : "—"}
          </div>
          <div className="text-[10px] text-cyan-400 mt-0.5">Crowdsourced submissions</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Verified Threat Alerts
          </div>
          <div className="text-2xl font-black text-emerald-400 mt-1">
            {stats ? stats.verified_threats : "—"}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">SOC analyst approved</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Pending Moderation
          </div>
          <div className="text-2xl font-black text-amber-400 mt-1">
            {stats ? stats.pending_reviews : "—"}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">Under investigation</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Active Indicators
          </div>
          <div className="text-2xl font-black text-cyan-400 mt-1">
            {stats ? stats.active_threat_indicators : "—"}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">Active blacklisted entities</div>
        </div>
      </div>

      {/* TAB 1: VERIFIED THREAT FEED */}
      {activeTab === "feed" && (
        <div className="space-y-4">
          {/* Filter Pills */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium flex items-center gap-1">
                <Filter className="w-3.5 h-3.5" /> Filter by:
              </span>
              {["ALL", "PHONE", "URL", "MESSAGE"].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setAlertsFilter(cat)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    alertsFilter === cat
                      ? "bg-slate-800 text-cyan-400 border border-cyan-500/40"
                      : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            <button
              onClick={loadData}
              disabled={refreshing}
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-cyan-400" : ""}`} />
              Refresh Feed
            </button>
          </div>

          {/* Alerts List */}
          {filteredAlerts.length === 0 ? (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center space-y-3">
              <ShieldCheck className="w-12 h-12 text-emerald-400 mx-auto" />
              <h3 className="text-base font-bold text-white">No Public Alerts in this Category</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                No active threats verified under this filter. If you encountered a suspicious caller or link, click "Submit Threat" to report it.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredAlerts.map((alert) => (
                <div
                  key={alert.threat_id}
                  className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 shadow-lg space-y-3 transition-all"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-cyan-400">
                        {alert.indicator_type === "PHONE" ? (
                          <Phone className="w-4 h-4" />
                        ) : alert.indicator_type === "URL" ? (
                          <LinkIcon className="w-4 h-4" />
                        ) : (
                          <MessageSquare className="w-4 h-4" />
                        )}
                      </span>
                      <div>
                        <div className="font-mono text-sm font-bold text-white tracking-wide">
                          {alert.indicator_value}
                        </div>
                        <div className="text-[11px] text-slate-400">
                          Category: {alert.indicator_type}
                        </div>
                      </div>
                    </div>

                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[11px] font-black border ${
                        alert.threat_level === "CRITICAL"
                          ? "bg-rose-500/20 text-rose-300 border-rose-500/30"
                          : alert.threat_level === "HIGH"
                          ? "bg-amber-500/20 text-amber-300 border-amber-500/30"
                          : "bg-blue-500/20 text-blue-300 border-blue-500/30"
                      }`}
                    >
                      {alert.threat_level}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-950 p-3 rounded-xl border border-slate-800/80">
                    {alert.description}
                  </p>

                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                    <span className="flex items-center gap-1 font-semibold text-slate-400">
                      <Users className="w-3.5 h-3.5 text-cyan-400" />
                      Reported by {alert.incident_count} citizen{alert.incident_count > 1 ? "s" : ""}
                    </span>
                    <span>Verified {new Date(alert.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: SUBMIT THREAT REPORT */}
      {activeTab === "submit" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Submission Form (Left 2 cols) */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <PlusCircle className="w-5 h-5 text-cyan-400" />
                Submit Citizen Threat Intelligence
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Help protect fellow citizens from recurring scams. Every report is audited and verified before being published.
              </p>
            </div>

            {/* Success Banner */}
            {submittedReport && (
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                    <CheckCircle2 className="w-5 h-5" />
                    Threat Report Successfully Registered!
                  </div>
                  <button
                    onClick={() => setSubmittedReport(null)}
                    className="text-xs text-slate-400 hover:text-white"
                  >
                    Dismiss
                  </button>
                </div>
                <div className="text-xs text-slate-300">
                  Your official reference tracking ID is:
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-base font-black text-cyan-400 bg-slate-950 px-3 py-1 rounded-lg border border-slate-800">
                    {submittedReport.report_code}
                  </span>
                  <button
                    onClick={() => copyToClipboard(submittedReport.report_code)}
                    className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                    title="Copy Code"
                  >
                    {copiedCode ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
                {submittedReport.is_duplicate && (
                  <div className="text-[11px] text-amber-300 bg-amber-500/10 p-2 rounded-lg border border-amber-500/20">
                    ℹ️ Note: This indicator was already flagged by other citizens. Your report has increased its threat priority count!
                  </div>
                )}
              </div>
            )}

            {formError && (
              <div className="p-3 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Threat Type */}
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1.5">
                    Threat Category
                  </label>
                  <select
                    value={threatType}
                    onChange={(e) => setThreatType(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl px-4 py-2.5 text-xs text-white outline-none"
                  >
                    <option value="PHONE">Phone Number / Scam Call</option>
                    <option value="URL">Phishing Website / Malicious URL</option>
                    <option value="MESSAGE">Fraud SMS / WhatsApp Text</option>
                    <option value="SCREENSHOT">Fake Payment Receipt / QR</option>
                    <option value="HARASSMENT">Cyber Harassment / Blackmail</option>
                  </select>
                </div>

                {/* State / Region */}
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1.5">
                    State / Region (Optional)
                  </label>
                  <select
                    value={region}
                    onChange={(e) => setRegion(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl px-4 py-2.5 text-xs text-white outline-none"
                  >
                    {INDIAN_STATES.map((st) => (
                      <option key={st} value={st}>
                        {st}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Target Value */}
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  Suspicious Phone Number, URL, or Indicator
                </label>
                <input
                  type="text"
                  value={targetValue}
                  onChange={(e) => setTargetValue(e.target.value)}
                  placeholder="e.g., +91 98765 43210 or sbi-kyc-verify.top or paytm-fraud@upi"
                  className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl px-4 py-2.5 text-xs text-white outline-none font-mono"
                  required
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  Incident Description & Details
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Explain what the fraudster said or claimed (e.g. threatened power cut, posed as Mumbai Police, asked for OTP)..."
                  rows={4}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl px-4 py-2.5 text-xs text-white outline-none"
                  required
                />
              </div>

              {/* Anonymous Checkbox */}
              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="anonymousCheck"
                  checked={isAnonymous}
                  onChange={(e) => setIsAnonymous(e.target.checked)}
                  className="rounded bg-slate-950 border-slate-800 text-cyan-500 focus:ring-0 w-4 h-4"
                />
                <label htmlFor="anonymousCheck" className="text-xs text-slate-300 cursor-pointer flex items-center gap-1.5">
                  <EyeOff className="w-3.5 h-3.5 text-slate-400" />
                  Submit Anonymously (Do not link this report to my account profile)
                </label>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-bold text-xs transition-all shadow-lg shadow-cyan-600/20 disabled:opacity-50"
              >
                {loading ? "Submitting Threat Intelligence..." : "Submit Threat Report"}
              </button>
            </form>
          </div>

          {/* Quick Presets & Guidelines (Right 1 col) */}
          <div className="space-y-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
              <h3 className="text-xs font-bold text-white flex items-center gap-1.5 uppercase tracking-wider">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                Quick Test Presets
              </h3>
              <p className="text-[11px] text-slate-400">
                Click any real-world scam scenario to autofill:
              </p>
              <div className="space-y-2">
                {SAMPLE_PRESETS.map((p, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handlePresetSelect(p)}
                    className="w-full text-left p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-cyan-500/50 transition-colors"
                  >
                    <div className="text-xs font-bold text-cyan-400">{p.type} Threat</div>
                    <div className="font-mono text-[11px] text-white mt-0.5 truncate">{p.target}</div>
                    <div className="text-[10px] text-slate-400 mt-1 line-clamp-2">{p.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Official Notice */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 text-xs text-slate-400 space-y-2">
              <div className="font-bold text-slate-300">Privacy & Legal Protection:</div>
              <p className="text-[11px] leading-relaxed">
                SURAKSHA AI verifies reports prior to public distribution. Never submit private personal communications or unverified accusations.
              </p>
              <p className="text-[11px] leading-relaxed">
                For official FIR filing, please visit <strong>cybercrime.gov.in</strong> or dial <strong>1930</strong>.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: TRACK REPORT STATUS */}
      {activeTab === "track" && (
        <div className="max-w-2xl mx-auto space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Search className="w-5 h-5 text-cyan-400" />
                Track Community Report Status
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Enter your unique reference number (e.g., SUR-REP-XXXXXX) to monitor moderation and verification outcomes.
              </p>
            </div>

            <form onSubmit={handleTrackSubmit} className="flex gap-2">
              <input
                type="text"
                value={trackCode}
                onChange={(e) => setTrackCode(e.target.value.toUpperCase())}
                placeholder="SUR-REP-XXXXXX"
                className="flex-1 bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl px-4 py-2.5 text-sm text-white font-mono uppercase outline-none"
                required
              />
              <button
                type="submit"
                disabled={loading}
                className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs transition-colors"
              >
                Track
              </button>
            </form>

            {trackError && (
              <div className="p-3 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
                <XCircle className="w-4 h-4 shrink-0" />
                <span>{trackError}</span>
              </div>
            )}
          </div>

          {/* Tracking Results Card */}
          {trackedReport && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <div className="text-xs text-slate-400">Report Reference Code</div>
                  <div className="font-mono text-lg font-black text-white">{trackedReport.report_code}</div>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-black border ${
                    trackedReport.status === "VERIFIED"
                      ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                      : trackedReport.status === "REJECTED"
                      ? "bg-rose-500/20 text-rose-400 border-rose-500/40"
                      : trackedReport.status === "RESOLVED"
                      ? "bg-blue-500/20 text-blue-400 border-blue-500/40"
                      : "bg-amber-500/20 text-amber-400 border-amber-500/40"
                  }`}
                >
                  {trackedReport.status}
                </span>
              </div>

              {/* Status Timeline Progress */}
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="p-3 rounded-xl bg-slate-950 border border-emerald-500/40 text-emerald-400">
                  <CheckCircle2 className="w-4 h-4 mx-auto mb-1 text-emerald-400" />
                  <div className="font-bold">1. Submitted</div>
                  <div className="text-[10px] text-slate-500">Recorded in Vault</div>
                </div>

                <div
                  className={`p-3 rounded-xl bg-slate-950 border ${
                    trackedReport.status !== "PENDING"
                      ? "border-emerald-500/40 text-emerald-400"
                      : "border-amber-500/40 text-amber-400"
                  }`}
                >
                  <Clock className="w-4 h-4 mx-auto mb-1" />
                  <div className="font-bold">2. SOC Analysis</div>
                  <div className="text-[10px] text-slate-500">Threat Verification</div>
                </div>

                <div
                  className={`p-3 rounded-xl bg-slate-950 border ${
                    trackedReport.status === "VERIFIED" || trackedReport.status === "RESOLVED"
                      ? "border-emerald-500/40 text-emerald-400"
                      : "border-slate-800 text-slate-500"
                  }`}
                >
                  <ShieldCheck className="w-4 h-4 mx-auto mb-1" />
                  <div className="font-bold">3. Action Taken</div>
                  <div className="text-[10px] text-slate-500">
                    {trackedReport.status === "VERIFIED" ? "Published Alert" : "Completed"}
                  </div>
                </div>
              </div>

              {/* Report Summary */}
              <div className="space-y-3 text-xs">
                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1.5">
                  <div className="text-slate-400">Target Value:</div>
                  <div className="font-mono text-cyan-400 font-bold">{trackedReport.target_value}</div>
                  <div className="text-slate-400 pt-1">Citizen Description:</div>
                  <div className="text-slate-200">{trackedReport.description}</div>
                </div>

                {/* Moderator Review Notes */}
                {trackedReport.reviews && trackedReport.reviews.length > 0 && (
                  <div className="bg-indigo-950/30 p-3.5 rounded-xl border border-indigo-500/30 space-y-2">
                    <div className="font-bold text-indigo-300 flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4" /> Security Analyst Feedback:
                    </div>
                    {trackedReport.reviews.map((rev, idx) => (
                      <div key={idx} className="text-[11px] text-slate-300">
                        {rev.public_notes || "Verified by security analyst and registered into the national threat feed."}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: MY SUBMITTED REPORTS */}
      {activeTab === "my-reports" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-cyan-400" />
              My Submitted Reports ({myReports.length})
            </h2>
          </div>

          {myReports.length === 0 ? (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center space-y-3">
              <FileText className="w-12 h-12 text-slate-600 mx-auto" />
              <h3 className="text-base font-bold text-white">No Reports Submitted Yet</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                You haven't submitted any threat reports under this account. If you received a suspicious message or call, click "Submit Threat".
              </p>
              <button
                onClick={() => setActiveTab("submit")}
                className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs transition-colors"
              >
                Submit Threat Report
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {myReports.map((r) => (
                <div
                  key={r.id}
                  className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold text-cyan-400">{r.report_code}</span>
                      <span className="text-xs text-slate-400">• {r.threat_type}</span>
                    </div>
                    <div className="text-xs font-mono text-slate-300">{r.target_value}</div>
                    <div className="text-[11px] text-slate-400">{r.description}</div>
                  </div>

                  <div className="flex items-center gap-3 self-end sm:self-center">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[11px] font-black border ${
                        r.status === "VERIFIED"
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                          : r.status === "REJECTED"
                          ? "bg-rose-500/20 text-rose-400 border-rose-500/40"
                          : "bg-amber-500/20 text-amber-400 border-amber-500/40"
                      }`}
                    >
                      {r.status}
                    </span>
                    <button
                      onClick={() => {
                        setTrackCode(r.report_code);
                        setActiveTab("track");
                      }}
                      className="text-xs text-cyan-400 hover:underline font-semibold"
                    >
                      Track →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

