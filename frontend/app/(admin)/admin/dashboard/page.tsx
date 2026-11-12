"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Users,
  FileText,
  AlertTriangle,
  Link2,
  Clock,
  CheckCircle2,
  XCircle,
  Copy,
  ScrollText,
  RefreshCw,
  Sliders,
  Radio
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { API_BASE_URL } from "@/lib/api";

interface AdminDashboardData {
  total_users: number;
  active_users: number;
  suspended_users: number;
  total_reports: number;
  pending_reports: number;
  verified_reports: number;
  rejected_reports: number;
  duplicate_reports: number;
  total_scans: number;
  suspicious_urls: number;
  threat_categories: Record<string, number>;
  recent_admin_actions: Array<{
    id: string;
    action: string;
    resource_type: string;
    resource_id: string;
    details: Record<string, any>;
    ip_address?: string;
    admin_email?: string;
    created_at: string;
  }>;
}

export default function AdminDashboardPage() {
  const { user, token } = useAuth();
  const [data, setData] = useState<AdminDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAdminMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const res = await fetch(`${API_BASE_URL}/dashboard/admin`, {
        headers,
        cache: "no-store",
      });
      if (res.ok) {
        const json = await res.json();
        setData(json);
      } else {
        setError("Failed to fetch admin metrics. Please verify administrator session.");
      }
    } catch (err: any) {
      setError(err.message || "Network error loading admin telemetry");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminMetrics();
  }, [token]);

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto w-full">
      {/* Top SOC Status Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-amber-950/30 border border-amber-500/20">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold">
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            Security Operations Console • Real-Time Database Metrics
          </div>
          <h1 className="text-2xl font-black text-white tracking-wide">
            SOC Operations & Moderation Command
          </h1>
          <p className="text-xs text-slate-400">
            Monitoring threat streams, audit telemetry, and community threat verification
          </p>
        </div>

        <button
          onClick={fetchAdminMetrics}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-300 text-xs font-bold border border-slate-700 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh Metrics
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/60 border border-red-800 text-red-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
          <Link href="/admin/login" className="underline font-bold text-red-200">
            Sign in as Admin &rarr;
          </Link>
        </div>
      )}

      {/* Primary KPI Grid (User & Scan Counts from DB) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Users */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Total Registered Users</span>
            <Users className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-white">
            {data?.total_users ?? 0}
          </div>
          <div className="text-[11px] text-slate-500 flex gap-2">
            <span className="text-emerald-400 font-medium">{data?.active_users ?? 0} Active</span>
            <span>•</span>
            <span className="text-red-400 font-medium">{data?.suspended_users ?? 0} Suspended</span>
          </div>
        </div>

        {/* Total Scans */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Total Engine Scans</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-white">
            {data?.total_scans ?? 0}
          </div>
          <div className="text-[11px] text-slate-500">
            Messages, Phishing URLs, OCR
          </div>
        </div>

        {/* Suspicious URLs */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Flagged Phishing URLs</span>
            <Link2 className="w-4 h-4 text-red-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-red-400">
            {data?.suspicious_urls ?? 0}
          </div>
          <div className="text-[11px] text-red-400/80">
            Risk &ge; 50/100 Lookalikes
          </div>
        </div>

        {/* Total Community Reports */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Community Threat Reports</span>
            <FileText className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-white">
            {data?.total_reports ?? 0}
          </div>
          <div className="text-[11px] text-amber-400 font-medium flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {data?.pending_reports ?? 0} Pending Verification
          </div>
        </div>
      </div>

      {/* Community Report Verification Lifecycle Breakdown (5 Status Cards) */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <FileText className="w-4 h-4 text-amber-400" />
            Report Moderation Lifecycle Breakdown
          </h2>
          <span className="text-xs text-slate-500">Real database counts</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <div className="p-4 rounded-xl bg-slate-950/70 border border-amber-500/20 text-center">
            <div className="text-xs font-semibold text-amber-400 flex items-center justify-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              PENDING
            </div>
            <div className="text-2xl font-black text-amber-300 mt-1">
              {data?.pending_reports ?? 0}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-emerald-500/20 text-center">
            <div className="text-xs font-semibold text-emerald-400 flex items-center justify-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              VERIFIED
            </div>
            <div className="text-2xl font-black text-emerald-300 mt-1">
              {data?.verified_reports ?? 0}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-red-500/20 text-center">
            <div className="text-xs font-semibold text-red-400 flex items-center justify-center gap-1">
              <XCircle className="w-3.5 h-3.5" />
              REJECTED
            </div>
            <div className="text-2xl font-black text-red-300 mt-1">
              {data?.rejected_reports ?? 0}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-blue-500/20 text-center">
            <div className="text-xs font-semibold text-blue-400 flex items-center justify-center gap-1">
              <Copy className="w-3.5 h-3.5" />
              DUPLICATE
            </div>
            <div className="text-2xl font-black text-blue-300 mt-1">
              {data?.duplicate_reports ?? 0}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-700 text-center col-span-2 sm:col-span-1">
            <div className="text-xs font-semibold text-slate-400">
              TOTAL TRIAGE
            </div>
            <div className="text-2xl font-black text-slate-100 mt-1">
              {data?.total_reports ?? 0}
            </div>
          </div>
        </div>
      </div>

      {/* Two Columns: Threat Categories & Live Audit Trail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Threat Categories */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            Threat Categories Aggregation
          </h2>

          {data?.threat_categories && Object.keys(data.threat_categories).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(data.threat_categories).map(([cat, count]) => (
                <div key={cat} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 text-xs">
                  <span className="font-medium text-slate-300">{cat}</span>
                  <span className="font-bold text-amber-400">{count}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-500">
              No threat categories recorded yet.
            </div>
          )}
        </div>

        {/* Live Admin Audit Log (Append-Only Stream) */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <ScrollText className="w-4 h-4 text-amber-400" />
              Append-Only Security Audit Trail (Recent Actions)
            </h2>
            <span className="text-xs text-slate-500">Real-time log</span>
          </div>

          {loading ? (
            <div className="py-8 text-center text-xs text-slate-500">Loading audit stream...</div>
          ) : data?.recent_admin_actions && data.recent_admin_actions.length > 0 ? (
            <div className="divide-y divide-slate-800">
              {data.recent_admin_actions.map((act) => (
                <div key={act.id} className="py-3 flex items-start justify-between text-xs">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-amber-300 bg-amber-500/10 px-1.5 py-0.5 rounded text-[10px]">
                        {act.action}
                      </span>
                      <span className="text-slate-400 text-[11px]">
                        by {act.admin_email}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Target: {act.resource_type} [{act.resource_id}] • IP: {act.ip_address || "127.0.0.1"}
                    </div>
                  </div>
                  <div className="text-[10px] text-slate-500 text-right shrink-0">
                    {new Date(act.created_at).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-500">
              Audit log is clear.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

