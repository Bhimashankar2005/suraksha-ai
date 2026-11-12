"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ShieldCheck, Lock, Mail, ArrowRight, AlertTriangle, KeyRound, Eye, EyeOff } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export default function AdminLoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const result = await login(email, password);
    setIsSubmitting(false);

    if (result.success) {
      if (result.role === "ADMIN") {
        router.push("/admin/dashboard");
      } else {
        setError("Access Denied: Administrator role required. Your account has standard USER privileges.");
      }
    } else {
      setError(result.error || "Authentication failed.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-950">
      <div className="w-full max-w-md space-y-6">
        {/* Admin Header with Distinct Security Identity */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400 shadow-xl shadow-amber-500/10 mb-2">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <div className="flex items-center justify-center gap-2">
            <span className="text-2xl font-black tracking-wider text-white">SURAKSHA<span className="text-amber-400"> SOC</span></span>
            <span className="px-2 py-0.5 text-[10px] font-bold tracking-widest uppercase bg-amber-500/20 text-amber-300 border border-amber-500/40 rounded">
              RESTRICTED
            </span>
          </div>
          <h2 className="text-sm font-semibold text-slate-300">Security Operations & Moderation Console</h2>
          <p className="text-xs text-slate-500">
            Authorized administrative officers only. All actions are cryptographically logged.
          </p>
        </div>

        {/* Card */}
        <div className="bg-slate-900/90 border border-amber-500/30 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6">
          {error && (
            <div className="p-3 rounded-lg bg-red-950/70 border border-red-700 text-red-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-amber-200/80 mb-1.5">
                Officer Email Identifier
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
                <input
                  type="email"
                  required
                  placeholder="admin@suraksha.gov.in"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500 rounded-xl px-10 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-amber-200/80 mb-1.5">
                Master Passphrase
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500 rounded-xl pl-10 pr-10 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-slate-500 hover:text-amber-400 focus:outline-none transition-colors"
                  title={showPassword ? "Hide passphrase" : "Show passphrase"}
                  aria-label={showPassword ? "Hide passphrase" : "Show passphrase"}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-sm shadow-lg shadow-amber-500/20 disabled:opacity-50 transition-all"
            >
              {isSubmitting ? "Authenticating Clearance..." : "Authorize SOC Session"}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
            <Link href="/login" className="hover:text-slate-300 transition-colors">
              &larr; Citizen Portal
            </Link>
            <span className="flex items-center gap-1 text-[11px] text-amber-400/80">
              <KeyRound className="w-3.5 h-3.5" />
              CLI Provisioned Only
            </span>
          </div>
        </div>

        <div className="text-center text-[11px] text-slate-600">
          SURAKSHA AI v1.0 • Internal Administrative Clearance
        </div>
      </div>
    </div>
  );
}

