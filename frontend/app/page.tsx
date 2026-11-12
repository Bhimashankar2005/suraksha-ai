import Link from "next/link";
import { Shield, ShieldAlert, Cpu, Lock, Users, AlertTriangle, ArrowRight, CheckCircle2 } from "lucide-react";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col justify-between">
      {/* Top Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-wider text-white">SURAKSHA<span className="text-cyan-400"> AI</span></span>
              <span className="hidden sm:inline-block ml-2 px-2 py-0.5 text-[10px] font-semibold tracking-wide uppercase bg-cyan-950 text-cyan-300 border border-cyan-800 rounded-full">
                Public Cyber Defense
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <Link
              href="/login"
              className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="px-4 py-2 text-sm font-medium bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-lg shadow-md shadow-cyan-500/25 transition-all"
            >
              Get Protected
            </Link>
            <Link
              href="/admin/login"
              className="hidden sm:inline-flex px-3 py-1.5 text-xs font-medium border border-slate-700 hover:border-slate-500 text-slate-400 hover:text-slate-200 rounded-md transition-colors"
            >
              Admin Portal
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative px-4 sm:px-6 lg:px-8 py-20 max-w-7xl mx-auto flex-1 flex flex-col justify-center">
        <div className="text-center max-w-3xl mx-auto space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 text-xs font-semibold">
            <ShieldAlert className="w-4 h-4" />
            Empowering 1.4 Billion Citizens with Zero-Cost Digital Safety
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
            AI-Powered Community <br />
            <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400 bg-clip-text text-transparent">
              Cyber Defense & Digital Safety
            </span>
          </h1>

          <p className="text-base sm:text-lg text-slate-400 leading-relaxed">
            Shielding ordinary citizens, students, women, and seniors from UPI fraud, phishing links, fake KYC messages, cyber harassment, and deepfakes using 100% free, local, explainable AI.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link
              href="/register"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold shadow-lg shadow-cyan-500/25 transition-all"
            >
              Start Free Cyber Scan
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/dashboard"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold transition-all"
            >
              Access User Portal
            </Link>
          </div>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 max-w-5xl mx-auto w-full">
          <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-colors">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-4">
              <Cpu className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Explainable AI & ML</h3>
            <p className="text-sm text-slate-400">
              Scam & phishing detection using transparent Scikit-Learn classifiers and rule-based heuristics. No black-box guesses.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-colors">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-4">
              <Users className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Community Intelligence</h3>
            <p className="text-sm text-slate-400">
              Submit emerging scam messages and fake numbers. Human-in-the-loop admin verification before public alerts are broadcast.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-colors">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4">
              <Lock className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Tamper-Proof Evidence Vault</h3>
            <p className="text-sm text-slate-400">
              SHA-256 cryptographic evidence preservation formatted for official submission to the National Cyber Crime Reporting Portal (1930).
            </p>
          </div>
        </div>

        {/* Official Helpline Notice */}
        <div className="mt-12 p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 max-w-3xl mx-auto flex items-center gap-3 text-amber-200 text-sm">
          <AlertTriangle className="w-5 h-5 shrink-0 text-amber-400" />
          <span>
            <strong>Official Indian Cybercrime Helpline:</strong> Call <strong>1930</strong> or visit{" "}
            <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer" className="underline font-semibold hover:text-white">
              cybercrime.gov.in
            </a>{" "}
            for official FIR filing. SURAKSHA AI helps you detect, document, and preserve evidence.
          </span>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/80 py-6 px-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            &copy; 2026 SURAKSHA AI. 100% Free & Open-Source Community Defense.
          </div>
          <div className="flex gap-4">
            <span className="flex items-center gap-1 text-slate-400">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              English, ಕನ್ನಡ, हिन्दी
            </span>
            <span className="text-slate-600">•</span>
            <Link href="/admin/login" className="hover:text-cyan-400 transition-colors">
              Admin Portal
            </Link>
          </div>
        </div>
      </footer>
    </main>
  );
}

