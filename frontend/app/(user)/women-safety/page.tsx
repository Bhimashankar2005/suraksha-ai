"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  HeartHandshake,
  ShieldAlert,
  PhoneCall,
  Lock,
  ExternalLink,
  AlertTriangle,
  CheckCircle2,
  Share2,
  UserPlus,
  Trash2,
  Copy,
  Info,
  LifeBuoy,
  FileCheck2,
  FileSpreadsheet
} from "lucide-react";
import {
  analyzeWomenSafetyThreat,
  HarassmentAnalysisResponse,
  fetchTrustedContacts,
  createTrustedContact,
  deleteTrustedContact,
  generateTrustedContactAlert,
  TrustedContactItem,
  TrustedContactAlertResponse
} from "@/lib/api";

const PRESET_SCENARIOS = [
  {
    title: "Morphing & Sextortion Threat",
    context: "Instagram DM / WhatsApp",
    sample: "I have morphed your photos with private nude pictures. If you do not pay 25,000 rupees to my UPI ID within 2 hours, I will send them to your father, college professors, and all your followers."
  },
  {
    title: "Persistent Cyberstalking & Physical Threat",
    context: "Telegram / SMS",
    sample: "I know you leave your office at 6:30 PM every day and take the metro from MG Road. Stop ignoring my messages or you will regret it. I am watching you right now."
  },
  {
    title: "Fake Profile Impersonation",
    context: "Facebook / Instagram",
    sample: "Someone created a fake profile with my name and photos, sharing derogatory remarks and messaging my colleagues with vulgar requests."
  }
];

export default function WomenSafetyPage() {
  const [content, setContent] = useState("");
  const [contextPlatform, setContextPlatform] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<HarassmentAnalysisResponse | null>(null);

  // Trusted Contacts state
  const [contacts, setContacts] = useState<TrustedContactItem[]>([]);
  const [contactsLoading, setContactsLoading] = useState(false);
  const [showAddContactModal, setShowAddContactModal] = useState(false);
  const [newContact, setNewContact] = useState({
    name: "",
    relationship_type: "parent",
    phone_number: "",
    email: "",
    has_explicit_consent: false,
    notify_on_critical_scam: true
  });
  const [contactError, setContactError] = useState<string | null>(null);
  const [generatedAlert, setGeneratedAlert] = useState<TrustedContactAlertResponse | null>(null);
  const [alertingContactId, setAlertingContactId] = useState<string | null>(null);
  const [copiedAlert, setCopiedAlert] = useState(false);

  useEffect(() => {
    loadContacts();
  }, []);

  const loadContacts = async () => {
    try {
      setContactsLoading(true);
      const data = await fetchTrustedContacts();
      setContacts(data);
    } catch {
      // User might not be logged in or have zero contacts
    } finally {
      setContactsLoading(false);
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await analyzeWomenSafetyThreat(content, contextPlatform || undefined);
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to analyze message.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateContact = async (e: React.FormEvent) => {
    e.preventDefault();
    setContactError(null);
    if (!newContact.has_explicit_consent) {
      setContactError("Explicit consent is legally required before registering a trusted contact.");
      return;
    }

    try {
      await createTrustedContact({
        name: newContact.name,
        relationship_type: newContact.relationship_type,
        phone_number: newContact.phone_number,
        email: newContact.email || undefined,
        has_explicit_consent: newContact.has_explicit_consent,
        notify_on_critical_scam: newContact.notify_on_critical_scam
      });
      setShowAddContactModal(false);
      setNewContact({
        name: "",
        relationship_type: "parent",
        phone_number: "",
        email: "",
        has_explicit_consent: false,
        notify_on_critical_scam: true
      });
      loadContacts();
    } catch (err: unknown) {
      setContactError(err instanceof Error ? err.message : "Failed to register trusted contact.");
    }
  };

  const handleDeleteContact = async (id: string) => {
    if (!confirm("Remove this trusted emergency contact?")) return;
    try {
      await deleteTrustedContact(id);
      setContacts(contacts.filter(c => c.id !== id));
      if (generatedAlert && alertingContactId === id) {
        setGeneratedAlert(null);
      }
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to delete contact");
    }
  };

  const handleGenerateAlert = async (contactId: string) => {
    try {
      setAlertingContactId(contactId);
      const res = await generateTrustedContactAlert({
        contact_id: contactId,
        incident_type: result?.threat_severity === "CRITICAL_EMERGENCY" ? "CYBER_BLACKMAIL_EMERGENCY" : "HARASSMENT_THREAT",
        incident_details: result?.detected_patterns.join(", ") || "Threatening messages received online"
      });
      setGeneratedAlert(res);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to generate alert SOS");
    }
  };

  const handleCopyAlert = () => {
    if (generatedAlert) {
      navigator.clipboard.writeText(generatedAlert.draft_sms_text);
      setCopiedAlert(true);
      setTimeout(() => setCopiedAlert(false), 3000);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Top Emergency Action Header */}
      <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-rose-950/80 via-slate-900 to-slate-900 border border-rose-500/30 shadow-lg shadow-rose-950/20">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0 border border-rose-500/30">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-black text-white">Women Digital Safety & Crisis Vault</h1>
                <span className="px-2 py-0.5 text-[11px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 rounded-full">
                  24x7 Emergency
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-300 mt-0.5">
                Confidential cyberstalking, morphing extortion, and harassment defense powered by privacy-first local AI.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
            <a
              href="tel:1091"
              className="flex-1 md:flex-initial inline-flex items-center justify-center gap-2 px-3.5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow-md transition-colors"
            >
              <PhoneCall className="w-3.5 h-3.5" />
              1091 Women Helpline
            </a>
            <a
              href="tel:112"
              className="flex-1 md:flex-initial inline-flex items-center justify-center gap-2 px-3.5 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold text-xs shadow-md transition-colors"
            >
              <PhoneCall className="w-3.5 h-3.5" />
              112 Police Emergency
            </a>
            <a
              href="https://cybercrime.gov.in"
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 md:flex-initial inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
            >
              <span>cybercrime.gov.in</span>
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Threat Analyzer Column */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <HeartHandshake className="w-5 h-5 text-rose-400" />
              <h2 className="text-base font-bold text-white">Confidential Harassment & Threat Assessment</h2>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Paste suspicious messages, blackmail threats, or abusive messages. All analysis is conducted deterministically on-device without cloud leakage.
            </p>

            {/* Presets */}
            <div className="mb-4">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Quick Test Samples:
              </div>
              <div className="flex flex-wrap gap-2">
                {PRESET_SCENARIOS.map((p, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setContent(p.sample);
                      setContextPlatform(p.context);
                    }}
                    className="text-xs bg-slate-800 hover:bg-slate-700/80 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg transition-colors text-left"
                  >
                    {p.title}
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleAnalyze} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Message Content / Threat Excerpt *
                </label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Paste abusive messages, blackmailer demands, stalking messages, or extortion claims..."
                  rows={4}
                  required
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-rose-500 focus:ring-1 focus:ring-rose-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Platform or Context (Optional)
                </label>
                <input
                  type="text"
                  value={contextPlatform}
                  onChange={(e) => setContextPlatform(e.target.value)}
                  placeholder="e.g. Instagram Direct Message, WhatsApp Unknown Number, Telegram group"
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-rose-500 transition-colors"
                />
              </div>

              {error && (
                <div className="p-3 bg-red-950/50 border border-red-500/50 rounded-xl text-xs text-red-300">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading || !content.trim()}
                className="w-full py-2.5 px-4 bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 disabled:opacity-50 text-white font-bold rounded-xl text-xs sm:text-sm shadow-md transition-all flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    Analyzing Threat Factors...
                  </>
                ) : (
                  <>
                    <ShieldAlert className="w-4 h-4" />
                    Assess Threat & Get Immediate Guidance
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Assessment Result Card */}
          {result && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-5 animate-in fade-in duration-200">
              {/* Severity Banner */}
              <div
                className={`p-4 rounded-xl border flex items-center justify-between gap-4 ${
                  result.threat_severity === "CRITICAL_EMERGENCY"
                    ? "bg-rose-950/60 border-rose-500 text-rose-200"
                    : result.threat_severity === "HIGH"
                    ? "bg-amber-950/60 border-amber-500 text-amber-200"
                    : result.threat_severity === "MEDIUM"
                    ? "bg-yellow-950/40 border-yellow-500 text-yellow-200"
                    : "bg-emerald-950/40 border-emerald-500 text-emerald-200"
                }`}
              >
                <div>
                  <div className="text-[11px] font-bold uppercase tracking-wider opacity-80">
                    Threat Severity Assessment
                  </div>
                  <div className="text-lg font-black tracking-wide mt-0.5">
                    {result.threat_severity.replace("_", " ")}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[11px] font-bold uppercase tracking-wider opacity-80">
                    Calculated Risk
                  </div>
                  <div className="text-2xl font-black">{result.risk_score}/100</div>
                </div>
              </div>

              {/* Detected Patterns */}
              <div>
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  Identified Threat Modalities
                </h3>
                <div className="flex flex-wrap gap-2">
                  {result.detected_patterns.map((p, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-800 border border-slate-700 text-slate-200"
                    >
                      {p}
                    </span>
                  ))}
                </div>
              </div>

              {/* Immediate Safety Instructions */}
              <div>
                <h3 className="text-xs font-bold text-rose-300 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-rose-400" />
                  Immediate Do&apos;s &amp; Don&apos;ts
                </h3>
                <ul className="space-y-2">
                  {result.immediate_actions.map((action, idx) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200"
                    >
                      <span className="w-5 h-5 rounded-full bg-rose-500/20 text-rose-400 font-bold flex items-center justify-center shrink-0 text-[10px]">
                        {idx + 1}
                      </span>
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Legal & Digital Evidence Checklist */}
              <div>
                <h3 className="text-xs font-bold text-cyan-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <FileCheck2 className="w-4 h-4 text-cyan-400" />
                  Digital Evidence Preservation Protocol
                </h3>
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs text-slate-300">
                  {result.evidence_checklist.map((item, idx) => (
                    <div key={idx} className="flex items-start gap-2">
                      <span className="text-cyan-400 font-bold">•</span>
                      <span>{item}</span>
                    </div>
                  ))}
                  <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                    <span className="text-[11px] text-slate-400">
                      Store screenshots in your tamper-evident vault:
                    </span>
                    <Link
                      href="/evidence-vault"
                      className="inline-flex items-center gap-1 text-xs font-bold text-cyan-400 hover:text-cyan-300"
                    >
                      <Lock className="w-3 h-3" />
                      Open Evidence Vault
                    </Link>
                  </div>
                </div>
              </div>

              {/* Official Helplines Reference */}
              <div>
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                  <LifeBuoy className="w-4 h-4 text-rose-400" />
                  Official Dedicated Support Helplines
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {result.emergency_helplines.map((h, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex flex-col justify-between"
                    >
                      <div>
                        <div className="font-bold text-xs text-white">{h.name}</div>
                        <div className="text-[11px] text-slate-400 mt-0.5">{h.description}</div>
                      </div>
                      <div className="mt-2.5 pt-2 border-t border-slate-800 flex items-center justify-between">
                        <a
                          href={`tel:${h.number.replace(/[^0-9]/g, "")}`}
                          className="text-xs font-black text-rose-400 hover:text-rose-300 flex items-center gap-1"
                        >
                          <PhoneCall className="w-3 h-3" />
                          {h.number}
                        </a>
                        {h.portal && (
                          <a
                            href={h.portal}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[10px] text-cyan-400 hover:underline flex items-center gap-0.5"
                          >
                            <span>Portal</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Official FIR Portal CTA */}
              <div className="p-4 rounded-xl bg-gradient-to-r from-cyan-950/40 to-slate-900 border border-cyan-800/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div>
                  <div className="font-bold text-xs text-white">File Official Anonymous Complaint</div>
                  <div className="text-[11px] text-slate-300 mt-0.5">
                    Indian National Cyber Crime Reporting Portal offers confidential &apos;Report Cyber Crime Against Women &amp; Children&apos; without public exposure.
                  </div>
                </div>
                <a
                  href={result.official_filing_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs shrink-0 inline-flex items-center gap-1.5 transition-colors"
                >
                  <span>National Portal (cybercrime.gov.in)</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          )}
        </div>

        {/* Right Sidebar: Trusted Emergency Contacts */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-cyan-400" />
                <h3 className="font-bold text-sm text-white">Trusted Emergency Circle</h3>
              </div>
              <button
                onClick={() => setShowAddContactModal(true)}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-xs font-semibold hover:bg-cyan-500/30 transition-colors"
              >
                <UserPlus className="w-3.5 h-3.5" />
                Add Contact
              </button>
            </div>
            <p className="text-xs text-slate-400">
              Designate trusted contacts who can be alerted with pre-drafted SOS details in an emergency. Requires explicit consent under India&apos;s DPDP Act.
            </p>

            {/* Contacts List */}
            {contactsLoading ? (
              <div className="text-center py-6 text-xs text-slate-500">Loading circle...</div>
            ) : contacts.length === 0 ? (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center">
                <p className="text-xs text-slate-400">No trusted contacts configured yet.</p>
                <button
                  onClick={() => setShowAddContactModal(true)}
                  className="mt-2 text-xs text-cyan-400 font-semibold hover:underline"
                >
                  + Add First Contact
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {contacts.map((contact) => (
                  <div
                    key={contact.id}
                    className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-bold text-xs text-white">{contact.name}</div>
                        <div className="text-[11px] text-slate-400 capitalize">
                          {contact.relationship_type} • {contact.phone_number}
                        </div>
                      </div>
                      <button
                        onClick={() => handleDeleteContact(contact.id)}
                        className="text-slate-500 hover:text-red-400 p-1 rounded"
                        title="Remove contact"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <div className="flex items-center justify-between pt-1 border-t border-slate-800/80">
                      <span className="text-[10px] text-emerald-400 font-medium flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        Consent Verified
                      </span>
                      <button
                        onClick={() => handleGenerateAlert(contact.id)}
                        className="inline-flex items-center gap-1 text-[11px] font-bold text-rose-400 hover:text-rose-300"
                      >
                        <Share2 className="w-3 h-3" />
                        Draft SOS
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Generated SOS Preview */}
            {generatedAlert && (
              <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/40 space-y-3 animate-in fade-in">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-rose-300">
                    SOS Draft for {generatedAlert.contact_name}
                  </span>
                  <button
                    onClick={handleCopyAlert}
                    className="text-[11px] text-slate-300 hover:text-white flex items-center gap-1"
                  >
                    <Copy className="w-3 h-3" />
                    {copiedAlert ? "Copied!" : "Copy"}
                  </button>
                </div>
                <p className="text-[11px] bg-slate-950/80 p-2.5 rounded-lg border border-slate-800 text-slate-200 font-mono">
                  {generatedAlert.draft_sms_text}
                </p>
                <div className="flex gap-2">
                  <a
                    href={generatedAlert.whatsapp_share_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 py-1.5 px-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs text-center flex items-center justify-center gap-1 transition-colors"
                  >
                    <Share2 className="w-3 h-3" />
                    Share on WhatsApp
                  </a>
                  <a
                    href={`sms:${generatedAlert.phone_number}?body=${encodeURIComponent(generatedAlert.draft_sms_text)}`}
                    className="py-1.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold text-center transition-colors"
                  >
                    SMS
                  </a>
                </div>
              </div>
            )}
          </div>

          {/* Legal Rights Card */}
          <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl space-y-2 text-xs text-slate-300">
            <div className="flex items-center gap-1.5 font-bold text-white text-xs">
              <Info className="w-4 h-4 text-cyan-400" />
              Know Your Legal Rights (IT Act &amp; BNS)
            </div>
            <p className="text-[11px] text-slate-400">
              Under Section 66E and 67A of the Information Technology Act and Bharatiya Nyaya Sanhita (BNS), morphing photos, sharing non-consensual images, cyberstalking, and extortion are non-bailable criminal offenses punishable by up to 5-7 years imprisonment.
            </p>
          </div>
        </div>
      </div>

      {/* Add Contact Modal */}
      {showAddContactModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-white">Register Trusted Emergency Contact</h3>
              <button
                onClick={() => setShowAddContactModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateContact} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  value={newContact.name}
                  onChange={(e) => setNewContact({ ...newContact, name: e.target.value })}
                  placeholder="e.g. Suman Sharma"
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Relationship *</label>
                <select
                  value={newContact.relationship_type}
                  onChange={(e) => setNewContact({ ...newContact, relationship_type: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                >
                  <option value="parent">Parent</option>
                  <option value="child">Child / Daughter / Son</option>
                  <option value="spouse">Spouse / Partner</option>
                  <option value="sibling">Sibling / Sister / Brother</option>
                  <option value="friend">Trusted Friend / Colleague</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Phone Number *</label>
                <input
                  type="tel"
                  required
                  value={newContact.phone_number}
                  onChange={(e) => setNewContact({ ...newContact, phone_number: e.target.value })}
                  placeholder="e.g. 9876543210"
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Email (Optional)</label>
                <input
                  type="email"
                  value={newContact.email}
                  onChange={(e) => setNewContact({ ...newContact, email: e.target.value })}
                  placeholder="e.g. contact@example.com"
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="pt-2 border-t border-slate-800 space-y-2">
                <label className="flex items-start gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newContact.has_explicit_consent}
                    onChange={(e) => setNewContact({ ...newContact, has_explicit_consent: e.target.checked })}
                    className="mt-0.5 rounded border-slate-700 text-rose-500 focus:ring-rose-500 bg-slate-950"
                  />
                  <span className="text-[11px] text-slate-300 leading-snug">
                    I confirm that I have informed this contact and obtained their explicit consent to save their details and send them safety alerts.
                  </span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newContact.notify_on_critical_scam}
                    onChange={(e) => setNewContact({ ...newContact, notify_on_critical_scam: e.target.checked })}
                    className="rounded border-slate-700 text-rose-500 focus:ring-rose-500 bg-slate-950"
                  />
                  <span className="text-[11px] text-slate-300">
                    Include in high-priority critical threat alert broadcasts
                  </span>
                </label>
              </div>

              {contactError && (
                <div className="p-2.5 bg-red-950/60 border border-red-500/50 rounded-xl text-xs text-red-300">
                  {contactError}
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddContactModal(false)}
                  className="flex-1 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs"
                >
                  Save Contact
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

