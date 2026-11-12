"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Bell,
  CheckCheck,
  ShieldAlert,
  FileText,
  Info,
  Trash2,
  ExternalLink,
  Check,
  Clock,
  Filter
} from "lucide-react";
import {
  fetchNotifications,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  deleteNotification,
  NotificationItem
} from "@/lib/api";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [filter, setFilter] = useState<"ALL" | "UNREAD" | "SECURITY_ALERT" | "REPORT_UPDATE">("ALL");

  useEffect(() => {
    loadNotifications();
  }, [filter]);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const res = await fetchNotifications(filter === "UNREAD", 50, 0);
      setNotifications(res.items);
      setUnreadCount(res.unread_count);
    } catch {
      // User might be unauthenticated
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (id: string) => {
    try {
      await markNotificationAsRead(id);
      setNotifications(notifications.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(Math.max(0, unreadCount - 1));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to mark as read");
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsAsRead();
      setNotifications(notifications.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to mark all as read");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteNotification(id);
      const target = notifications.find(n => n.id === id);
      if (target && !target.is_read) {
        setUnreadCount(Math.max(0, unreadCount - 1));
      }
      setNotifications(notifications.filter(n => n.id !== id));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to delete notification");
    }
  };

  const filteredItems = notifications.filter(n => {
    if (filter === "SECURITY_ALERT") return n.category === "SECURITY_ALERT";
    if (filter === "REPORT_UPDATE") return n.category === "REPORT_UPDATE";
    return true;
  });

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "SECURITY_ALERT":
        return <ShieldAlert className="w-5 h-5 text-rose-400" />;
      case "REPORT_UPDATE":
        return <FileText className="w-5 h-5 text-cyan-400" />;
      default:
        return <Info className="w-5 h-5 text-blue-400" />;
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-16">
      {/* Top Banner */}
      <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center shrink-0 border border-cyan-500/30">
            <Bell className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-black text-white">Citizen Security Alerts &amp; Notifications</h1>
              {unreadCount > 0 && (
                <span className="px-2.5 py-0.5 text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30 rounded-full">
                  {unreadCount} Unread
                </span>
              )}
            </div>
            <p className="text-xs sm:text-sm text-slate-300 mt-0.5">
              Real-time updates regarding your submitted threat reports and verified community defense warnings.
            </p>
          </div>
        </div>

        {unreadCount > 0 && (
          <button
            type="button"
            onClick={handleMarkAllRead}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition-colors flex items-center gap-1.5 shrink-0"
          >
            <CheckCheck className="w-4 h-4 text-cyan-400" />
            Mark All Read
          </button>
        )}
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setFilter("ALL")}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all border ${
            filter === "ALL"
              ? "bg-cyan-500 text-slate-950 border-cyan-400 font-extrabold shadow-md"
              : "bg-slate-900 text-slate-300 border-slate-800 hover:border-slate-700"
          }`}
        >
          All Notifications
        </button>
        <button
          type="button"
          onClick={() => setFilter("UNREAD")}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all border ${
            filter === "UNREAD"
              ? "bg-cyan-500 text-slate-950 border-cyan-400 font-extrabold shadow-md"
              : "bg-slate-900 text-slate-300 border-slate-800 hover:border-slate-700"
          }`}
        >
          Unread Only ({unreadCount})
        </button>
        <button
          type="button"
          onClick={() => setFilter("SECURITY_ALERT")}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all border ${
            filter === "SECURITY_ALERT"
              ? "bg-cyan-500 text-slate-950 border-cyan-400 font-extrabold shadow-md"
              : "bg-slate-900 text-slate-300 border-slate-800 hover:border-slate-700"
          }`}
        >
          Security Alerts
        </button>
        <button
          type="button"
          onClick={() => setFilter("REPORT_UPDATE")}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all border ${
            filter === "REPORT_UPDATE"
              ? "bg-cyan-500 text-slate-950 border-cyan-400 font-extrabold shadow-md"
              : "bg-slate-900 text-slate-300 border-slate-800 hover:border-slate-700"
          }`}
        >
          Report Updates
        </button>
      </div>

      {/* Notifications Feed */}
      {loading ? (
        <div className="text-center py-12 text-slate-500 text-xs">Loading notifications...</div>
      ) : filteredItems.length === 0 ? (
        <div className="p-8 bg-slate-900 border border-slate-800 rounded-3xl text-center space-y-2">
          <Bell className="w-8 h-8 text-slate-600 mx-auto" />
          <h3 className="font-bold text-white text-sm">No Notifications Found</h3>
          <p className="text-xs text-slate-400">
            {filter === "UNREAD" ? "You have read all your notifications!" : "You're completely up to date."}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredItems.map((item) => (
            <div
              key={item.id}
              className={`p-4 rounded-2xl border transition-all flex items-start justify-between gap-4 ${
                !item.is_read
                  ? "bg-slate-900 border-cyan-500/40 shadow-sm shadow-cyan-950/20"
                  : "bg-slate-900/60 border-slate-800/80 text-slate-400"
              }`}
            >
              <div className="flex items-start gap-3.5">
                <div className="w-10 h-10 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-center shrink-0 mt-0.5">
                  {getCategoryIcon(item.category)}
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-bold ${!item.is_read ? "text-white" : "text-slate-300"}`}>
                      {item.title}
                    </span>
                    {!item.is_read && (
                      <span className="w-2 h-2 rounded-full bg-cyan-400 shrink-0" />
                    )}
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    {item.message}
                  </p>

                  <div className="flex items-center gap-3 pt-1 text-[11px] text-slate-400">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(item.created_at).toLocaleString()}
                    </span>

                    {item.action_url && (
                      <Link
                        href={item.action_url}
                        className="text-cyan-400 hover:text-cyan-300 font-bold flex items-center gap-1"
                      >
                        <span>View Details</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </Link>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-1 shrink-0">
                {!item.is_read && (
                  <button
                    type="button"
                    onClick={() => handleMarkAsRead(item.id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-slate-800 transition-colors"
                    title="Mark as read"
                  >
                    <Check className="w-4 h-4" />
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => handleDelete(item.id)}
                  className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-slate-800 transition-colors"
                  title="Delete notification"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

