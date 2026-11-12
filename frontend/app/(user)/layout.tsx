"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Shield,
  LayoutDashboard,
  MessageSquareWarning,
  Link2,
  FileSearch,
  Mic,
  Bot,
  Users,
  Lock,
  EyeOff,
  Video,
  HeartHandshake,
  UserCheck,
  GraduationCap,
  Bell,
  User,
  Settings,
  LogOut,
  Menu,
  X,
  PhoneCall
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { fetchUnreadNotificationCount } from "@/lib/api";

const USER_NAVIGATION = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Scam Detection", href: "/scam-detection", icon: MessageSquareWarning },
  { name: "URL Scanner", href: "/url-scanner", icon: Link2 },
  { name: "Screenshot Scanner", href: "/screenshot-scanner", icon: FileSearch },
  { name: "Voice Analysis", href: "/voice-analysis", icon: Mic },
  { name: "AI Cyber Assistant", href: "/assistant", icon: Bot },
  { name: "Community Reports", href: "/community-reports", icon: Users },
  { name: "Evidence Vault", href: "/evidence-vault", icon: Lock },
  { name: "Privacy Protection", href: "/privacy-protection", icon: EyeOff },
  { name: "Deepfake Analysis", href: "/deepfake-analysis", icon: Video },
  { name: "Women Safety", href: "/women-safety", icon: HeartHandshake },
  { name: "Senior Protection", href: "/senior-protection", icon: UserCheck },
  { name: "Cyber Awareness", href: "/cyber-awareness", icon: GraduationCap },
  { name: "Notifications", href: "/notifications", icon: Bell },
  { name: "My Profile", href: "/profile", icon: User },
  { name: "Settings", href: "/settings", icon: Settings },
];

export default function UserPortalLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [seniorMode, setSeniorMode] = useState(false);
  const [unreadNotifs, setUnreadNotifs] = useState(0);

  useEffect(() => {
    fetchUnreadNotificationCount()
      .then(res => setUnreadNotifs(res.unread_count))
      .catch(() => {});
  }, [pathname]);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <div className={`min-h-screen bg-slate-950 text-slate-100 flex flex-col md:flex-row ${seniorMode ? "text-lg" : "text-sm"}`}>
      {/* Mobile Top Header */}
      <div className="md:hidden flex items-center justify-between p-4 bg-slate-900 border-b border-slate-800">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-cyan-500 flex items-center justify-center text-slate-950 font-bold">
            <Shield className="w-5 h-5 text-slate-950" />
          </div>
          <span className="font-bold text-white tracking-wider">SURAKSHA<span className="text-cyan-400"> AI</span></span>
        </Link>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded-lg bg-slate-800 text-slate-300"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Sidebar Navigation */}
      <aside
        className={`fixed md:sticky top-0 left-0 z-40 h-screen w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between transition-transform duration-200 ease-in-out ${
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        <div className="flex flex-col h-full overflow-hidden">
          {/* Brand & Senior Mode Toggle */}
          <div className="p-5 border-b border-slate-800/80">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-md shadow-cyan-500/20">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="font-extrabold text-base tracking-wider text-white">
                  SURAKSHA<span className="text-cyan-400"> AI</span>
                </div>
                <div className="text-[10px] text-cyan-400 font-semibold uppercase tracking-wider">
                  Citizen Defense Vault
                </div>
              </div>
            </Link>

            {/* Accessibility Senior Mode Switch */}
            <div className="mt-4 flex items-center justify-between p-2 rounded-lg bg-slate-950/70 border border-slate-800">
              <span className="text-xs text-slate-300 font-medium">Large Text Mode</span>
              <button
                type="button"
                onClick={() => setSeniorMode(!seniorMode)}
                className={`w-9 h-5 flex items-center rounded-full p-1 transition-colors ${
                  seniorMode ? "bg-cyan-500 justify-end" : "bg-slate-700 justify-start"
                }`}
              >
                <div className="w-3.5 h-3.5 rounded-full bg-white shadow-sm" />
              </button>
            </div>
          </div>

          {/* 16 Navigation Links */}
          <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1 custom-scrollbar">
            {USER_NAVIGATION.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center justify-between px-3 py-2 rounded-xl font-medium transition-colors ${
                    isActive
                      ? "bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/10 font-semibold"
                      : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/60"
                  }`}
                >
                  <div className="flex items-center gap-3 truncate">
                    <Icon className={`w-4 h-4 shrink-0 ${isActive ? "text-slate-950" : "text-slate-400"}`} />
                    <span className="truncate">{item.name}</span>
                  </div>
                  {item.href === "/notifications" && unreadNotifs > 0 && (
                    <span className="px-1.5 py-0.5 rounded-full text-[10px] font-black bg-rose-500 text-white shadow-sm">
                      {unreadNotifs}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* User Profile & Helpline Footer */}
          <div className="p-4 border-t border-slate-800/80 bg-slate-950/40 space-y-3">
            {/* 1930 Emergency Helpline Badge */}
            <a
              href="tel:1930"
              className="flex items-center justify-between p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs hover:bg-amber-500/20 transition-colors"
            >
              <div className="flex items-center gap-2">
                <PhoneCall className="w-3.5 h-3.5 text-amber-400" />
                <span className="font-semibold">Cyber Helpline</span>
              </div>
              <span className="font-bold text-amber-400">1930</span>
            </a>

            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-2 truncate">
                <div className="w-8 h-8 rounded-full bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-300 font-bold text-xs shrink-0">
                  {user?.full_name ? user.full_name.charAt(0).toUpperCase() : "U"}
                </div>
                <div className="truncate">
                  <div className="text-xs font-semibold text-white truncate">
                    {user?.full_name || "Citizen User"}
                  </div>
                  <div className="text-[10px] text-slate-500 truncate">
                    {user?.email || "Protected Account"}
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
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-h-screen overflow-x-hidden">
        {children}
      </div>
    </div>
  );
}

