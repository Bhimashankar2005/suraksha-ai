"use client";

import React, { useState, useEffect } from "react";
import {
  Users,
  Search,
  Shield,
  ShieldAlert,
  UserCheck,
  UserX,
  Filter,
  RefreshCw,
  Edit2,
  CheckCircle2,
  AlertTriangle
} from "lucide-react";
import {
  fetchAdminUsers,
  updateAdminUserRole,
  toggleAdminUserStatus,
  AdminUserListItem
} from "@/lib/api";

export default function AdminUserManagementPage() {
  const [users, setUsers] = useState<AdminUserListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("");
  const [activeFilter, setActiveFilter] = useState<string>("");

  // Edit role modal state
  const [editingUser, setEditingUser] = useState<AdminUserListItem | null>(null);
  const [selectedRole, setSelectedRole] = useState<string>("USER");
  const [savingRole, setSavingRole] = useState(false);
  const [roleError, setRoleError] = useState<string | null>(null);

  useEffect(() => {
    loadUsers();
  }, [roleFilter, activeFilter]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const isActiveParam = activeFilter === "true" ? true : activeFilter === "false" ? false : undefined;
      const data = await fetchAdminUsers(
        searchTerm || undefined,
        roleFilter || undefined,
        isActiveParam
      );
      setUsers(data);
    } catch {
      // Admin might not be logged in or error
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadUsers();
  };

  const handleToggleStatus = async (user: AdminUserListItem) => {
    const actionLabel = user.is_active ? "deactivate" : "activate";
    if (!confirm(`Are you sure you want to ${actionLabel} account for ${user.email}?`)) return;

    try {
      await toggleAdminUserStatus(user.id, !user.is_active);
      setUsers(users.map(u => u.id === user.id ? { ...u, is_active: !user.is_active } : u));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to toggle user status");
    }
  };

  const handleSaveRole = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;

    setSavingRole(true);
    setRoleError(null);
    try {
      await updateAdminUserRole(editingUser.id, selectedRole);
      setUsers(users.map(u => u.id === editingUser.id ? { ...u, role: selectedRole } : u));
      setEditingUser(null);
    } catch (err: unknown) {
      setRoleError(err instanceof Error ? err.message : "Failed to update role");
    } finally {
      setSavingRole(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header Banner */}
      <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center shrink-0 border border-cyan-500/30">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-black text-white">Identity &amp; Role Management</h1>
              <span className="px-2.5 py-0.5 text-xs font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 rounded-full">
                SOC Admin
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-300 mt-0.5">
              Manage platform citizens, triage analysts, and system administrators with role-based governance.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={loadUsers}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition-colors flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Directory
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <form onSubmit={handleSearch} className="flex-1 flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by email address or full name..."
              className="w-full bg-slate-950 border border-slate-700 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs rounded-xl transition-colors"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-2">
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Roles</option>
            <option value="USER">Citizens (USER)</option>
            <option value="COMMUNITY_MODERATOR">Moderators (ANALYST)</option>
            <option value="ADMIN">Administrators (ADMIN)</option>
          </select>

          <select
            value={activeFilter}
            onChange={(e) => setActiveFilter(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Statuses</option>
            <option value="true">Active Only</option>
            <option value="false">Suspended Only</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="text-center py-12 text-slate-500 text-xs">Loading user directory...</div>
        ) : users.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">No matching user accounts located.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Citizen / User</th>
                  <th className="py-3.5 px-4">Role</th>
                  <th className="py-3.5 px-4">Activity Counts</th>
                  <th className="py-3.5 px-4">Account Status</th>
                  <th className="py-3.5 px-4">Registered Date</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 font-medium">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="font-bold text-white text-xs">{u.email}</div>
                      <div className="text-[11px] text-slate-500">
                        {u.full_name || "Unspecified Name"} {u.phone_number ? `• ${u.phone_number}` : ""}
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-wider uppercase border ${
                          u.role === "ADMIN"
                            ? "bg-purple-500/20 text-purple-300 border-purple-500/30"
                            : u.role === "COMMUNITY_MODERATOR"
                            ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/30"
                            : "bg-slate-800 text-slate-300 border-slate-700"
                        }`}
                      >
                        {u.role}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="text-[11px] text-slate-300">
                        <span className="font-bold text-cyan-400">{u.scans_count}</span> Scans •{" "}
                        <span className="font-bold text-amber-400">{u.reports_count}</span> Reports
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                          u.is_active
                            ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                            : "bg-red-500/20 text-red-300 border-red-500/30"
                        }`}
                      >
                        {u.is_active ? "Active" : "Suspended"}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => {
                            setEditingUser(u);
                            setSelectedRole(u.role);
                            setRoleError(null);
                          }}
                          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors flex items-center gap-1"
                        >
                          <Edit2 className="w-3 h-3 text-cyan-400" />
                          Role
                        </button>

                        <button
                          type="button"
                          onClick={() => handleToggleStatus(u)}
                          className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition-colors flex items-center gap-1 ${
                            u.is_active
                              ? "bg-red-950/40 hover:bg-red-900/60 text-red-300 border-red-500/30"
                              : "bg-emerald-950/40 hover:bg-emerald-900/60 text-emerald-300 border-emerald-500/30"
                          }`}
                        >
                          {u.is_active ? <UserX className="w-3 h-3" /> : <UserCheck className="w-3 h-3" />}
                          {u.is_active ? "Suspend" : "Activate"}
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

      {/* Edit Role Modal */}
      {editingUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-white">Modify Authorization Role</h3>
              <button onClick={() => setEditingUser(null)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <p className="text-xs text-slate-300">
              Select access role for <span className="font-bold text-white">{editingUser.email}</span>.
            </p>

            <form onSubmit={handleSaveRole} className="space-y-4">
              <div className="space-y-2">
                {[
                  { id: "USER", label: "Citizen (USER)", desc: "Standard scan, educational, and reporting access." },
                  { id: "COMMUNITY_MODERATOR", label: "Community Moderator (ANALYST)", desc: "Can review and triage citizen threat reports." },
                  { id: "ADMIN", label: "Administrator (ADMIN)", desc: "Full security operation control, role assignment, and audit inspection." }
                ].map((roleOpt) => (
                  <label
                    key={roleOpt.id}
                    className={`block p-3 rounded-xl border cursor-pointer text-xs transition-colors ${
                      selectedRole === roleOpt.id
                        ? "bg-cyan-950/60 border-cyan-500 text-cyan-200"
                        : "bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center gap-2 font-bold">
                      <input
                        type="radio"
                        name="role"
                        value={roleOpt.id}
                        checked={selectedRole === roleOpt.id}
                        onChange={() => setSelectedRole(roleOpt.id)}
                        className="text-cyan-500 focus:ring-cyan-500 bg-slate-950"
                      />
                      <span>{roleOpt.label}</span>
                    </div>
                    <p className="text-[11px] text-slate-400 pl-5 mt-0.5">{roleOpt.desc}</p>
                  </label>
                ))}
              </div>

              {roleError && (
                <div className="p-2.5 bg-red-950/60 border border-red-500/50 rounded-xl text-xs text-red-300 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>{roleError}</span>
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingUser(null)}
                  className="flex-1 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingRole}
                  className="flex-1 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs"
                >
                  {savingRole ? "Saving..." : "Update Role"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

