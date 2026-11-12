"use client";

import React, { useState, useEffect } from "react";
import {
  FileText,
  ShieldCheck,
  ShieldAlert,
  Clock,
  CheckCircle2,
  XCircle,
  Copy,
  Check,
  AlertTriangle,
  RefreshCw,
  Search,
  Filter,
  Phone,
  Link as LinkIcon,
  MessageSquare,
  Eye,
  SlidersHorizontal
} from "lucide-react";
import {
  fetchAdminReportQueue,
  reviewAdminReport,
  ReportItem
} from "@/lib/api";

export default function AdminReportsQueuePage() {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [statusFilter, setStatusFilter] = useState("PENDING");
  const [loading, setLoading] = useState(false);
  const [selectedReport, setSelectedReport] = useState<ReportItem | null>(null);

  // Review Form
  const [action, setAction] = useState<"APPROVE_VERIFY" | "REJECT" | "MARK_DUPLICATE" | "RESOLVE">("APPROVE_VERIFY");
  const [threatLevel, setThreatLevel] = useState<"CRITICAL" | "HIGH" | "MEDIUM">("HIGH");
  const [publishPublic, setPublishPublic] = useState(true);
  const [internalNotes, setInternalNotes] = useState("");
  const [publicNotes, setPublicNotes] = useState("");
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewSuccess, setReviewSuccess] = useState<string | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);

  const loadQueue = async () => {
    setLoading(true);
    try {
      const data = await fetchAdminReportQueue(statusFilter);
      setReports(data);
    } catch (err: any) {
      console.error("Queue load error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, [statusFilter]);

  const handleOpenReview = (report: ReportItem) => {
    setSelectedReport(report);
    setAction("APPROVE_VERIFY");
    setThreatLevel("HIGH");
    setPublishPublic(true);
    setInternalNotes(`Verified indicator against blacklists. Confirmed malicious pattern.`);
    setPublicNotes(`Confirmed ${report.threat_type.toLowerCase()} fraud indicator. Do not engage or click.`);
    setReviewSuccess(null);
    setReviewError(null);
  };

  const handleExecuteReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReport) return;

    setSubmittingReview(true);
    setReviewError(null);
    try {
      await reviewAdminReport(selectedReport.id, {
        action,
        internal_notes: internalNotes.trim(),
        public_notes: publicNotes.trim() || undefined,
        publish_as_public_alert: action === "APPROVE_VERIFY" ? publishPublic : false,
        threat_level: threatLevel
      });
      setReviewSuccess(`Report ${selectedReport.report_code} updated to ${action}!`);
      setTimeout(() => {
        setSelectedReport(null);
        loadQueue();
      }, 1200);
    } catch (err: any) {
      setReviewError(err.message || "Failed to process review.");
    } finally {
      setSubmittingReview(false);
    }
  };

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <FileText className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-black text-white flex items-center gap-2">
              Community Incident Moderation Queue
              <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                SOC Analyst Portal
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Audit citizen reports • Verify malicious indicators • Publish community warnings
            </p>
          </div>
        </div>

        {/* Status Filters */}
        <div className="flex items-center gap-2 overflow-x-auto">
          {["PENDING", "UNDER_REVIEW", "VERIFIED", "REJECTED", "DUPLICATE"].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                statusFilter === status
                  ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20"
                  : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              {status}
            </button>
          ))}
          <button
            onClick={loadQueue}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 hover:text-white"
            title="Refresh queue"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-cyan-400" : ""}`} />
          </button>
        </div>
      </div>

      {/* Reports Table / Cards */}
      {reports.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center space-y-3">
          <ShieldCheck className="w-12 h-12 text-emerald-400 mx-auto" />
          <h3 className="text-base font-bold text-white">Queue Clear</h3>
          <p className="text-xs text-slate-400">
            No incident reports currently waiting under the <strong>{statusFilter}</strong> status.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {reports.map((report) => (
            <div
              key={report.id}
              className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all"
            >
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-cyan-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                    {report.report_code}
                  </span>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    {report.threat_type}
                  </span>
                  {report.region && (
                    <span className="text-[11px] text-slate-400">📍 {report.region}</span>
                  )}
                  {report.is_duplicate && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      ⚠️ Duplicate Matched
                    </span>
                  )}
                </div>

                <div className="font-mono text-sm font-bold text-white tracking-wide">
                  {report.target_value}
                </div>

                <p className="text-xs text-slate-400 line-clamp-2">
                  {report.description}
                </p>

                <div className="text-[10px] text-slate-500">
                  Submitted {new Date(report.created_at).toLocaleString()}
                </div>
              </div>

              {/* Action Button */}
              <div className="flex items-center gap-2 self-end md:self-center">
                <button
                  onClick={() => handleOpenReview(report)}
                  className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs transition-colors flex items-center gap-1.5 shadow-md shadow-cyan-600/20"
                >
                  <Eye className="w-3.5 h-3.5" />
                  Review & Moderate
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Review Modal */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-cyan-400" />
                  Incident Moderation: {selectedReport.report_code}
                </h3>
                <div className="text-xs text-slate-400">
                  Category: {selectedReport.threat_type} • Region: {selectedReport.region || "Unspecified"}
                </div>
              </div>
              <button
                onClick={() => setSelectedReport(null)}
                className="text-slate-400 hover:text-white p-1 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            {/* Target Value Preview */}
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
              <div className="text-[11px] text-slate-400">Suspect Indicator:</div>
              <div className="font-mono text-sm font-bold text-cyan-400">{selectedReport.target_value}</div>
              <div className="text-[11px] text-slate-400 pt-1">Citizen Narrative:</div>
              <div className="text-xs text-slate-300">{selectedReport.description}</div>
            </div>

            {reviewSuccess && (
              <div className="p-3 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{reviewSuccess}</span>
              </div>
            )}

            {reviewError && (
              <div className="p-3 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{reviewError}</span>
              </div>
            )}

            <form onSubmit={handleExecuteReview} className="space-y-4">
              {/* Action Selection */}
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  Moderation Verdict
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { val: "APPROVE_VERIFY", label: "Approve & Verify" },
                    { val: "REJECT", label: "Reject (Unverified)" },
                    { val: "MARK_DUPLICATE", label: "Mark Duplicate" },
                    { val: "RESOLVE", label: "Mark Resolved" },
                  ].map((item) => (
                    <button
                      key={item.val}
                      type="button"
                      onClick={() => setAction(item.val as any)}
                      className={`p-2.5 rounded-xl text-xs font-bold transition-all border ${
                        action === item.val
                          ? "bg-cyan-500/20 border-cyan-500 text-cyan-300"
                          : "bg-slate-950 border-slate-800 text-slate-400 hover:text-white"
                      }`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Threat Level & Public Publish (If approved) */}
              {action === "APPROVE_VERIFY" && (
                <div className="space-y-3 p-3.5 bg-slate-950 rounded-xl border border-slate-800">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-slate-300">Threat Severity</label>
                    <div className="flex gap-1.5">
                      {(["MEDIUM", "HIGH", "CRITICAL"] as const).map((lvl) => (
                        <button
                          key={lvl}
                          type="button"
                          onClick={() => setThreatLevel(lvl)}
                          className={`px-2.5 py-1 rounded-lg text-[11px] font-black border transition-all ${
                            threatLevel === lvl
                              ? lvl === "CRITICAL"
                                ? "bg-rose-500 text-white border-rose-400"
                                : lvl === "HIGH"
                                ? "bg-amber-500 text-slate-950 border-amber-400"
                                : "bg-cyan-500 text-slate-950 border-cyan-400"
                              : "bg-slate-900 border-slate-800 text-slate-400"
                          }`}
                        >
                          {lvl}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-1 border-t border-slate-800/80">
                    <input
                      type="checkbox"
                      id="publishPublicCheck"
                      checked={publishPublic}
                      onChange={(e) => setPublishPublic(e.target.checked)}
                      className="rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-0 w-4 h-4"
                    />
                    <label htmlFor="publishPublicCheck" className="text-xs text-slate-300 cursor-pointer">
                      Publish as Verified Community Threat Alert (Broadcast to feed)
                    </label>
                  </div>
                </div>
              )}

              {/* Internal SOC Notes */}
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  Internal SOC Audit Notes
                </label>
                <textarea
                  value={internalNotes}
                  onChange={(e) => setInternalNotes(e.target.value)}
                  placeholder="Record verification methodology, blacklist match, or investigation notes..."
                  rows={2}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl px-3 py-2 text-xs text-white outline-none"
                  required
                />
              </div>

              {/* Public Feedback Notes */}
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  Public Safety Notes (Visible to citizen tracking code)
                </label>
                <textarea
                  value={publicNotes}
                  onChange={(e) => setPublicNotes(e.target.value)}
                  placeholder="Advice for the citizen regarding this specific scam indicator..."
                  rows={2}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl px-3 py-2 text-xs text-white outline-none"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedReport(null)}
                  className="flex-1 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingReview}
                  className="flex-1 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold transition-colors shadow-lg shadow-cyan-600/20 disabled:opacity-50"
                >
                  {submittingReview ? "Processing..." : "Submit Verdict"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

