"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  ShieldCheck,
  LayoutGrid,
  Users,
  FileText,
  CheckCheck,
  Radio,
  BarChart3,
  Link2,
  FolderLock,
  Megaphone,
  Cpu,
  ShieldAlert,
  ScrollText,
  TrendingUp,
  Sliders,
  UserCheck,
  LogOut,
  Menu,
  X
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

const ADMIN_NAVIGATION = [
  { name: "Overview", href: "/admin/dashboard", icon: LayoutGrid },
  { name: "User Directory & RBAC", href: "/admin/users", icon: Users },
  { name: "Community Reports Queue", href: "/admin/reports", icon: FileText },
  { name: "Threat Intelligence & Broadcasts", href: "/admin/intelligence", icon: Radio },
  { name: "Security Telemetry & Storage", href: "/admin/security", icon: ShieldAlert },
  { name: "Security Audit Trail", href: "/admin/audit-logs", icon: ScrollText },
  { name: "Citizen Safety Portal", href: "/dashboard", icon: ShieldCheck },
  { name: "Platform Settings", href: "/settings", icon: Sliders },
];

export default function AdminPortalLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    router.push("/admin/login");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col md:flex-row">
      {/* Mobile Top Header */}
      <div className="md:hidden flex items-center justify-between p-4 bg-slate-900 border-b border-amber-500/20">
        <Link href="/admin/dashboard" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-amber-500 flex items-center justify-center text-slate-950 font-bold">
            <ShieldCheck className="w-5 h-5 text-slate-950" />
          </div>
          <span className="font-bold text-white tracking-wider">SURAKSHA<span className="text-amber-400"> SOC</span></span>
        </Link>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded-lg bg-slate-800 text-slate-300"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Admin Command Sidebar */}
      <aside
        className={`fixed md:sticky top-0 left-0 z-40 h-screen w-64 bg-slate-900/95 border-r border-amber-500/20 flex flex-col justify-between transition-transform duration-200 ease-in-out ${
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        <div className="flex flex-col h-full overflow-hidden">
          {/* Brand & SOC Indicator */}
          <div className="p-5 border-b border-slate-800/80">
            <Link href="/admin/dashboard" className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-amber-600 to-amber-400 flex items-center justify-center shadow-md shadow-amber-500/20">
                <ShieldCheck className="w-5 h-5 text-slate-950" />
              </div>
              <div>
                <div className="font-black text-base tracking-wider text-white">
                  SURAKSHA<span className="text-amber-400"> SOC</span>
                </div>
                <div className="text-[10px] text-amber-400 font-bold uppercase tracking-widest">
                  Restricted Console
                </div>
              </div>
            </Link>
          </div>

          {/* 16 Admin Navigation Links */}
          <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1 custom-scrollbar">
            {ADMIN_NAVIGATION.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                    isActive
                      ? "bg-amber-500 text-slate-950 font-bold shadow-md shadow-amber-500/10"
                      : "text-slate-400 hover:text-amber-300 hover:bg-slate-800/60"
                  }`}
                >
                  <Icon className={`w-4 h-4 shrink-0 ${isActive ? "text-slate-950" : "text-slate-500"}`} />
                  <span className="truncate">{item.name}</span>
                </Link>
              );
            })}

            {/* Link 16: Explicit Logout */}
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-red-400 hover:bg-red-950/40 hover:text-red-300 transition-colors"
            >
              <LogOut className="w-4 h-4 shrink-0 text-red-400" />
              <span>Logout</span>
            </button>
          </nav>

          {/* Admin Officer Footer */}
          <div className="p-4 border-t border-slate-800/80 bg-slate-950/60 flex items-center justify-between">
            <div className="flex items-center gap-2 truncate">
              <div className="w-8 h-8 rounded-full bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 font-bold text-xs shrink-0">
                A
              </div>
              <div className="truncate">
                <div className="text-xs font-bold text-amber-200 truncate">
                  {user?.full_name || "Chief Officer"}
                </div>
                <div className="text-[10px] text-slate-500 truncate">
                  Role: ADMIN
                </div>
              </div>
            </div>

            <button
              onClick={handleLogout}
              title="Sign Out"
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-800 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Admin Content */}
      <div className="flex-1 flex flex-col min-h-screen overflow-x-hidden">
        {children}
      </div>
    </div>
  );
}

