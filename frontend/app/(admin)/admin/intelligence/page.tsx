"use client";

import React, { useState, useEffect } from "react";
import {
  Radio,
  Search,
  Filter,
  RefreshCw,
  Megaphone,
  CheckCircle2,
  AlertTriangle,
  Edit2,
  Share2,
  Clock,
  Shield
} from "lucide-react";
import {
  fetchAdminThreats,
  updateAdminThreat,
  broadcastThreatAlert,
  AdminThreatItem
} from "@/lib/api";

export default function AdminThreatIntelligencePage() {
  const [threats, setThreats] = useState<AdminThreatItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeOnly, setActiveOnly] = useState(false);
  const [broadcastMessage, setBroadcastMessage] = useState<string | null>(null);

  // Edit threat modal
  const [editingThreat, setEditingThreat] = useState<AdminThreatItem | null>(null);
  const [editLevel, setEditLevel] = useState<string>("HIGH");
  const [editActive, setEditActive] = useState<boolean>(true);
  const [editDesc, setEditDesc] = useState<string>("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadThreats();
  }, [activeOnly]);

  const loadThreats = async () => {
    try {
      setLoading(true);
      const data = await fetchAdminThreats(activeOnly);
      setThreats(data);
    } catch {
      // Error
    } finally {
      setLoading(false);
    }
  };

  const handleBroadcast = async (threatId: string) => {
    if (!confirm("Broadcast this verified threat alert to all active platform citizens?")) return;

    try {
      const res = await broadcastThreatAlert(threatId);
      setBroadcastMessage(`Threat alert successfully broadcasted to ${res.recipient_count} citizens!`);
      setTimeout(() => setBroadcastMessage(null), 5000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to broadcast threat");
    }
  };

  const handleSaveThreat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingThreat) return;

    setSaving(true);
    try {
      const updated = await updateAdminThreat(editingThreat.id, {
        threat_level: editLevel,
        is_active: editActive,
        description: editDesc
      });
      setThreats(threats.map(t => t.id === editingThreat.id ? updated : t));
      setEditingThreat(null);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to update threat");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header Banner */}
      <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center shrink-0 border border-cyan-500/30">
            <Radio className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-black text-white">SOC Cyber Threat Intelligence Feed</h1>
              <span className="px-2.5 py-0.5 text-xs font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 rounded-full">
                Active IOC Indicators
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-300 mt-0.5">
              Curate verified phishing domains, malicious phone numbers, and rogue APKs published to the public defense feed.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={loadThreats}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition-colors flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Feed
        </button>
      </div>

      {broadcastMessage && (
        <div className="p-4 bg-emerald-950/60 border border-emerald-500/50 rounded-2xl text-xs text-emerald-300 flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{broadcastMessage}</span>
        </div>
      )}

      {/* Filter Bar */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-between gap-3">
        <label className="flex items-center gap-2 text-xs font-bold text-slate-300 cursor-pointer">
          <input
            type="checkbox"
            checked={activeOnly}
            onChange={(e) => setActiveOnly(e.target.checked)}
            className="rounded border-slate-700 text-cyan-500 focus:ring-cyan-500 bg-slate-950"
          />
          <span>Show Active Indicators Only</span>
        </label>
        <span className="text-xs text-slate-400 font-semibold">{threats.length} indicators tracked</span>
      </div>

      {/* Threats Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="text-center py-12 text-slate-500 text-xs">Loading threat intelligence...</div>
        ) : threats.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">No threat indicators recorded.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Indicator Type</th>
                  <th className="py-3.5 px-4">Indicator Target Value</th>
                  <th className="py-3.5 px-4">Threat Level</th>
                  <th className="py-3.5 px-4">Incidents</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 font-medium">
                {threats.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-black uppercase bg-slate-800 border border-slate-700 text-slate-300">
                        {t.indicator_type}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="font-bold text-white text-xs font-mono">{t.indicator_value}</div>
                      <div className="text-[11px] text-slate-400 truncate max-w-sm mt-0.5">{t.description}</div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase border ${
                          t.threat_level === "CRITICAL"
                            ? "bg-red-500/20 text-red-300 border-red-500/40"
                            : t.threat_level === "HIGH"
                            ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                            : "bg-blue-500/20 text-blue-300 border-blue-500/40"
                        }`}
                      >
                        {t.threat_level}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-cyan-400 font-bold">
                      {t.incident_count} reports
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          t.is_active
                            ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                            : "bg-slate-800 text-slate-400 border-slate-700"
                        }`}
                      >
                        {t.is_active ? "Broadcasting" : "Retired"}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          type="button"
                          onClick={() => {
                            setEditingThreat(t);
                            setEditLevel(t.threat_level);
                            setEditActive(t.is_active);
                            setEditDesc(t.description);
                          }}
                          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors flex items-center gap-1"
                        >
                          <Edit2 className="w-3 h-3 text-cyan-400" />
                          Edit
                        </button>

                        <button
                          type="button"
                          onClick={() => handleBroadcast(t.id)}
                          className="px-2.5 py-1 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold shadow-sm transition-colors flex items-center gap-1"
                          title="Broadcast urgent alert to citizens"
                        >
                          <Megaphone className="w-3 h-3" />
                          Broadcast
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Edit Threat Modal */}
      {editingThreat && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-white">Modify Threat Indicator</h3>
              <button onClick={() => setEditingThreat(null)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <form onSubmit={handleSaveThreat} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Target Indicator</label>
                <div className="p-2.5 bg-slate-950 border border-slate-700 rounded-xl font-mono text-xs text-cyan-400">
                  {editingThreat.indicator_value}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Threat Level</label>
                <select
                  value={editLevel}
                  onChange={(e) => setEditLevel(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                >
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HIGH">HIGH</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Public Description / Guidance</label>
                <textarea
                  rows={3}
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <label className="flex items-center gap-2 cursor-pointer pt-1">
                <input
                  type="checkbox"
                  checked={editActive}
                  onChange={(e) => setEditActive(e.target.checked)}
                  className="rounded border-slate-700 text-cyan-500 focus:ring-cyan-500 bg-slate-950"
                />
                <span className="text-xs text-slate-300 font-semibold">Active in Public Threat Feeds</span>
              </label>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingThreat(null)}
                  className="flex-1 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs"
                >
                  {saving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

