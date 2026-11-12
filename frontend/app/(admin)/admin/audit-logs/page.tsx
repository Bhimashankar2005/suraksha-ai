"use client";

import React, { useState, useEffect } from "react";
import {
  ScrollText,
  Filter,
  RefreshCw,
  Search,
  ShieldCheck,
  User,
  Clock,
  Eye,
  Info
} from "lucide-react";
import { fetchAdminAuditLogs, AuditLogListItem } from "@/lib/api";

export default function AdminAuditLogsPage() {
  const [logs, setLogs] = useState<AuditLogListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState<string>("");
  const [resourceFilter, setResourceFilter] = useState<string>("");
  const [selectedLog, setSelectedLog] = useState<AuditLogListItem | null>(null);

  useEffect(() => {
    loadLogs();
  }, [actionFilter, resourceFilter]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const data = await fetchAdminAuditLogs(
        actionFilter || undefined,
        resourceFilter || undefined,
        50
      );
      setLogs(data);
    } catch {
      // Admin error
    } finally {
      setLoading(false);
    }
  };

  const getActionColor = (action: string) => {
    if (action.includes("LOGIN") || action.includes("AUTH")) {
      return "bg-blue-500/20 text-blue-300 border-blue-500/30";
    }
    if (action.includes("DEACTIVATE") || action.includes("FAILED") || action.includes("DELETE")) {
      return "bg-red-500/20 text-red-300 border-red-500/30";
    }
    if (action.includes("ROLE") || action.includes("BROADCAST")) {
      return "bg-purple-500/20 text-purple-300 border-purple-500/30";
    }
    if (action.includes("VERIFY") || action.includes("APPROVE") || action.includes("ACTIVATE")) {
      return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
    }
    return "bg-slate-800 text-slate-300 border-slate-700";
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header Banner */}
      <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center shrink-0 border border-cyan-500/30">
            <ScrollText className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-black text-white">Append-Only Security Audit Trail</h1>
              <span className="px-2.5 py-0.5 text-xs font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 rounded-full">
                Compliance &amp; Governance
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-300 mt-0.5">
              Tamper-evident system event log tracking authorization decisions, moderation actions, and administrative operations.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={loadLogs}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition-colors flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Trail
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <Filter className="w-3.5 h-3.5 text-cyan-400" />
            Filters:
          </span>

          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Actions</option>
            <option value="UPDATE_USER_ROLE">Update User Role</option>
            <option value="ACCOUNT_ACTIVATED">Account Activated</option>
            <option value="ACCOUNT_DEACTIVATED">Account Deactivated</option>
            <option value="BROADCAST_NOTIFICATION">Broadcast Notification</option>
            <option value="REPORT_REVIEW">Report Review</option>
            <option value="DEEPFAKE_MEDIA_SCAN">Deepfake Scan</option>
            <option value="WOMEN_SAFETY_ASSESSMENT">Women Safety Assessment</option>
          </select>

          <select
            value={resourceFilter}
            onChange={(e) => setResourceFilter(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Resource Types</option>
            <option value="USER">USER</option>
            <option value="REPORT">REPORT</option>
            <option value="THREAT">THREAT</option>
            <option value="NOTIFICATION">NOTIFICATION</option>
            <option value="DEEPFAKE_SCAN">DEEPFAKE_SCAN</option>
          </select>
        </div>

        <span className="text-xs text-slate-400 font-semibold">{logs.length} events logged</span>
      </div>

      {/* Audit Log Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="text-center py-12 text-slate-500 text-xs">Loading audit trail...</div>
        ) : logs.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">No matching audit events recorded.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Timestamp</th>
                  <th className="py-3.5 px-4">Action</th>
                  <th className="py-3.5 px-4">Target Resource</th>
                  <th className="py-3.5 px-4">Executing Actor</th>
                  <th className="py-3.5 px-4">IP Address</th>
                  <th className="py-3.5 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 font-mono text-[11px]">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 text-slate-400 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>

                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${getActionColor(log.action)}`}>
                        {log.action}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="text-slate-200 font-bold">{log.resource_type}</span>
                      <span className="text-slate-500 block text-[10px] truncate max-w-[150px]">{log.resource_id}</span>
                    </td>

                    <td className="py-3.5 px-4 text-slate-300">
                      {log.user_email || log.user_id || "SYSTEM"}
                    </td>

                    <td className="py-3.5 px-4 text-slate-500">
                      {log.ip_address || "127.0.0.1"}
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <button
                        type="button"
                        onClick={() => setSelectedLog(log)}
                        className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-400 font-sans font-bold text-xs inline-flex items-center gap-1 border border-slate-700 transition-colors"
                      >
                        <Eye className="w-3 h-3" />
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Inspect Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
                <ScrollText className="w-4 h-4 text-cyan-400" />
                Audit Event Metadata
              </h3>
              <button onClick={() => setSelectedLog(null)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Action:</span>
                <span className="font-bold text-white font-mono">{selectedLog.action}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Resource:</span>
                <span className="text-slate-200 font-mono">{selectedLog.resource_type} / {selectedLog.resource_id}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Actor Email:</span>
                <span className="text-slate-200">{selectedLog.user_email || "System/Guest"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Timestamp:</span>
                <span className="text-slate-200">{new Date(selectedLog.created_at).toISOString()}</span>
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-xs font-bold text-slate-300">Payload Details (JSON):</span>
              <pre className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-[11px] font-mono text-cyan-300 overflow-x-auto max-h-48">
                {JSON.stringify(selectedLog.details, null, 2)}
              </pre>
            </div>

            <button
              type="button"
              onClick={() => setSelectedLog(null)}
              className="w-full py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

