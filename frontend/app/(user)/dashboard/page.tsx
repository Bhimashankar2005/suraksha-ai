"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  Search,
  MessageSquareWarning,
  Link2,
  FileSearch,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowUpRight,
  ShieldCheck,
  Bell,
  RefreshCw
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { API_BASE_URL } from "@/lib/api";

interface UserDashboardData {
  total_scans: number;
  suspicious_detections: number;
  submitted_reports: number;
  pending_reports: number;
  verified_reports: number;
  recent_activity: Array<{
    id: string;
    activity_type: string;
    title: string;
    risk_level?: string;
    status?: string;
    created_at: string;
  }>;
  notifications: Array<{
    id: string;
    title: string;
    message: string;
    category: string;
    is_read: boolean;
    created_at: string;
  }>;
}

export default function UserDashboardPage() {
  const { user, token } = useAuth();
  const [data, setData] = useState<UserDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const res = await fetch(`${API_BASE_URL}/dashboard/user`, {
        headers,
        cache: "no-store",
      });
      if (res.ok) {
        const json = await res.json();
        setData(json);
      } else {
        // Fallback or demo state if unauthenticated or new
        setData({
          total_scans: 0,
          suspicious_detections: 0,
          submitted_reports: 0,
          pending_reports: 0,
          verified_reports: 0,
          recent_activity: [],
          notifications: [],
        });
      }
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard metrics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [token]);

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto w-full">
      {/* Welcome Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 border border-slate-800">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" />
            Active Protection Engine: SQLite / Local Heuristics
          </div>
          <h1 className="text-2xl font-bold text-white">
            Welcome, {user?.full_name || "Citizen Defender"}
          </h1>
          <p className="text-xs text-slate-400">
            Real-time threat diagnostics, incident documentation, and community alerts
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchDashboardData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <Link
            href="/scam-detection"
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold shadow-md shadow-cyan-500/20 transition-all"
          >
            <Search className="w-3.5 h-3.5" />
            Quick Scam Scan
          </Link>
        </div>
      </div>

      {/* Real Database Metrics Cards (5 Required Cards) */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Scans */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="text-xs font-medium text-slate-400">Total Scans Run</div>
          <div className="text-2xl sm:text-3xl font-extrabold text-white mt-2">
            {data?.total_scans ?? 0}
          </div>
          <div className="text-[11px] text-cyan-400 mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" />
            Messages, URLs, Images
          </div>
        </div>

        {/* Suspicious Detections */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="text-xs font-medium text-slate-400">Suspicious Threats</div>
          <div className="text-2xl sm:text-3xl font-extrabold text-red-400 mt-2">
            {data?.suspicious_detections ?? 0}
          </div>
          <div className="text-[11px] text-red-400/80 mt-1 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            Score &ge; 50/100
          </div>
        </div>

        {/* Submitted Reports */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="text-xs font-medium text-slate-400">Submitted Reports</div>
          <div className="text-2xl sm:text-3xl font-extrabold text-slate-200 mt-2">
            {data?.submitted_reports ?? 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Community Triage</div>
        </div>

        {/* Pending Reports */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="text-xs font-medium text-slate-400">Under Review</div>
          <div className="text-2xl sm:text-3xl font-extrabold text-amber-400 mt-2">
            {data?.pending_reports ?? 0}
          </div>
          <div className="text-[11px] text-amber-400/80 mt-1 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Moderator Queue
          </div>
        </div>

        {/* Verified Reports */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 col-span-2 lg:col-span-1">
          <div className="text-xs font-medium text-slate-400">Verified Threats</div>
          <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400 mt-2">
            {data?.verified_reports ?? 0}
          </div>
          <div className="text-[11px] text-emerald-400/80 mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" />
            Confirmed & Alerted
          </div>
        </div>
      </div>

      {/* Quick Launch Protection Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          href="/scam-detection"
          className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/50 hover:bg-slate-900 transition-all group"
        >
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <MessageSquareWarning className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-4 h-4 text-slate-600 group-hover:text-cyan-400 transition-colors" />
          </div>
          <h3 className="font-semibold text-white mt-4 text-base">Analyze Scam Message</h3>
          <p className="text-xs text-slate-400 mt-1">
            Paste suspicious SMS, WhatsApp messages, or fake KYC lottery offers for immediate risk grading.
          </p>
        </Link>

        <Link
          href="/url-scanner"
          className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/50 hover:bg-slate-900 transition-all group"
        >
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <Link2 className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-4 h-4 text-slate-600 group-hover:text-cyan-400 transition-colors" />
          </div>
          <h3 className="font-semibold text-white mt-4 text-base">Scan Phishing URL</h3>
          <p className="text-xs text-slate-400 mt-1">
            Anti-SSRF inspection, domain homoglyph check, and lookalike detection without exposing your device.
          </p>
        </Link>

        <Link
          href="/screenshot-scanner"
          className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/50 hover:bg-slate-900 transition-all group"
        >
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <FileSearch className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-4 h-4 text-slate-600 group-hover:text-cyan-400 transition-colors" />
          </div>
          <h3 className="font-semibold text-white mt-4 text-base">Screenshot & OCR Check</h3>
          <p className="text-xs text-slate-400 mt-1">
            Upload fake payment receipts, banking screenshots, or QR codes to extract and audit text patterns.
          </p>
        </Link>
      </div>

      {/* Two Column Grid: Recent Activity & Notifications */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity List (Real DB values) */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-cyan-400" />
              Recent Personal Activity (Database Log)
            </h2>
            <span className="text-xs text-slate-500">Live records</span>
          </div>

          {loading ? (
            <div className="py-8 text-center text-xs text-slate-500">Loading activity...</div>
          ) : data?.recent_activity && data.recent_activity.length > 0 ? (
            <div className="divide-y divide-slate-800">
              {data.recent_activity.map((item) => (
                <div key={item.id} className="py-3 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-medium text-slate-200">{item.title}</div>
                    <div className="text-[10px] text-slate-500">
                      {new Date(item.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    {item.risk_level && (
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          item.risk_level === "CRITICAL"
                            ? "bg-red-500/20 text-red-400 border border-red-500/30"
                            : item.risk_level === "HIGH"
                            ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                            : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        }`}
                      >
                        {item.risk_level}
                      </span>
                    )}
                    {item.status && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300">
                        {item.status}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center space-y-2 border border-dashed border-slate-800 rounded-xl">
              <ShieldAlert className="w-8 h-8 text-slate-600 mx-auto" />
              <div className="text-xs text-slate-400 font-medium">No Scans Recorded Yet</div>
              <p className="text-[11px] text-slate-600 max-w-sm mx-auto">
                Paste your first SMS or URL scan above to populate your tamper-evident security vault.
              </p>
            </div>
          )}
        </div>

        {/* Notifications Column */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Bell className="w-4 h-4 text-cyan-400" />
              System Alerts
            </h2>
            <span className="text-xs text-slate-500">In-App</span>
          </div>

          {data?.notifications && data.notifications.length > 0 ? (
            <div className="space-y-3">
              {data.notifications.map((n) => (
                <div key={n.id} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs space-y-1">
                  <div className="font-semibold text-slate-200">{n.title}</div>
                  <div className="text-[11px] text-slate-400">{n.message}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-500">
              No new alerts. Your vault is clear.
            </div>
          )}

          {/* Official Helpline Reference Card */}
          <div className="pt-4 border-t border-slate-800 space-y-2">
            <div className="text-[11px] font-bold text-amber-400 uppercase tracking-wide">
              Official Indian Reporting
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              SURAKSHA AI assists in forensic evidence capture. To officially report cyber financial fraud within golden hours, dial <strong>1930</strong> immediately.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

