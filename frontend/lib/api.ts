export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export interface HealthCheckResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  database: string;
  timestamp: string;
  services: {
    database_engine: string;
    storage_vault: string;
    ollama_integration: string;
  };
}

export async function fetchHealth(): Promise<HealthCheckResponse> {
  const res = await fetch(`${API_BASE_URL}/health`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch health status: ${res.statusText}`);
  }
  return res.json();
}

export interface HelplineContact {
  name: string;
  number: string;
  portal?: string;
  description: string;
  operating_hours: string;
}

export interface ChatMessageItem {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatResponse {
  reply: string;
  language: string;
  provider: "ollama" | "deterministic_fallback";
  detected_topic: string;
  safety_warning?: string | null;
  quick_actions: string[];
  emergency_contacts: HelplineContact[];
  timestamp: string;
}

export interface AssistantStatus {
  ollama_available: boolean;
  configured_model: string;
  base_url: string;
  fallback_active: boolean;
  supported_languages: string[];
}

export async function sendChatMessage(
  message: string,
  language: "en" | "kn" | "hi" = "en",
  conversation_history?: ChatMessageItem[]
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE_URL}/chat/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, language, conversation_history }),
  });
  if (!res.ok) {
    throw new Error(`Chat assistant request failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchChatResources(): Promise<HelplineContact[]> {
  const res = await fetch(`${API_BASE_URL}/chat/resources`);
  if (!res.ok) {
    throw new Error(`Failed to fetch chat resources: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchAssistantStatus(): Promise<AssistantStatus> {
  const res = await fetch(`${API_BASE_URL}/chat/status`);
  if (!res.ok) {
    throw new Error(`Failed to fetch assistant status: ${res.statusText}`);
  }
  return res.json();
}


// --- Community Threat Reports API ---

export interface ReportItem {
  id: string;
  report_code: string;
  threat_type: string;
  target_value: string;
  description: string;
  region?: string | null;
  status: string;
  is_public_alert: boolean;
  is_duplicate: boolean;
  created_at: string;
}

export interface ReviewHistoryItem {
  action_taken: string;
  public_notes?: string | null;
  created_at: string;
}

export interface ReportTrackResponse {
  report_code: string;
  threat_type: string;
  target_value: string;
  description: string;
  region?: string | null;
  status: string;
  is_public_alert: boolean;
  is_duplicate: boolean;
  created_at: string;
  updated_at: string;
  reviews: ReviewHistoryItem[];
}

export interface ThreatAlertItem {
  threat_id: string;
  indicator_type: string;
  indicator_value: string;
  threat_level: string;
  description: string;
  incident_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ThreatStats {
  total_reports: number;
  pending_reviews: number;
  verified_threats: number;
  resolved_reports: number;
  by_category: Record<string, number>;
  by_region: Record<string, number>;
  active_threat_indicators: number;
}

export async function submitThreatReport(data: {
  threat_type: string;
  target_value: string;
  description: string;
  region?: string;
  is_anonymous?: boolean;
}): Promise<ReportItem> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/reports/submit`, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Report submission failed: ${res.statusText}`);
  }
  return res.json();
}

export async function trackReport(reportCode: string): Promise<ReportTrackResponse> {
  const res = await fetch(`${API_BASE_URL}/reports/track/${encodeURIComponent(reportCode.trim())}`);
  if (!res.ok) {
    if (res.status === 404) throw new Error("Report not found. Please double-check your code.");
    throw new Error(`Tracking request failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchUserReports(): Promise<ReportItem[]> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/reports/my-reports`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch user reports: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchThreatAlerts(threatType?: string): Promise<ThreatAlertItem[]> {
  const url = threatType
    ? `${API_BASE_URL}/reports/alerts?threat_type=${encodeURIComponent(threatType)}`
    : `${API_BASE_URL}/reports/alerts`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch threat alerts: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchThreatStats(): Promise<ThreatStats> {
  const res = await fetch(`${API_BASE_URL}/reports/stats`);
  if (!res.ok) {
    throw new Error(`Failed to fetch threat stats: ${res.statusText}`);
  }
  return res.json();
}


export async function fetchAdminReportQueue(statusFilter: string = "PENDING"): Promise<ReportItem[]> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/reports/admin/queue?status_filter=${encodeURIComponent(statusFilter)}`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch admin moderation queue: ${res.statusText}`);
  }
  return res.json();
}

export async function reviewAdminReport(
  reportId: string,
  actionData: {
    action: string;
    internal_notes: string;
    public_notes?: string;
    publish_as_public_alert?: boolean;
    threat_level?: string;
  }
): Promise<ReportItem> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/reports/admin/${encodeURIComponent(reportId)}/review`, {
    method: "POST",
    headers,
    body: JSON.stringify(actionData),
  });
  if (!res.ok) {
    throw new Error(`Failed to submit report review: ${res.statusText}`);
  }
  return res.json();
}


// --- Cybercrime Evidence Management API ---

export interface EvidenceFileItem {
  id: string;
  file_code: string;
  original_name: string;
  mime_type: string;
  file_size_bytes: number;
  sha256_hash: string;
  incident_category: string;
  incident_date: string;
  description?: string | null;
  created_at: string;
}

export interface IncidentReportResponse {
  id: string;
  incident_title: string;
  category: string;
  total_financial_loss: number;
  timeline_summary: string;
  evidence_files: EvidenceFileItem[];
  official_portal_guidance: string;
  disclaimer: string;
  created_at: string;
}

export interface EvidenceVaultStats {
  total_files: number;
  total_size_bytes: number;
  total_incident_reports: number;
  total_documented_loss_inr: number;
}

export async function uploadEvidenceFile(
  file: File,
  category: string,
  incidentDate?: string,
  description?: string
): Promise<EvidenceFileItem> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const formData = new FormData();
  formData.append("file", file);
  formData.append("incident_category", category);
  if (incidentDate) formData.append("incident_date", incidentDate);
  if (description) formData.append("description", description);

  const res = await fetch(`${API_BASE_URL}/evidence/upload`, {
    method: "POST",
    headers,
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Evidence upload failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchUserVault(): Promise<EvidenceFileItem[]> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/evidence/my-vault`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch evidence vault: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchUserVaultStats(): Promise<EvidenceVaultStats> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/evidence/stats`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch vault statistics: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteEvidenceFile(fileId: string): Promise<void> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/evidence/${encodeURIComponent(fileId)}`, {
    method: "DELETE",
    headers,
  });
  if (!res.ok) {
    throw new Error(`Failed to delete evidence file: ${res.statusText}`);
  }
}

export async function compileIncidentDossier(data: {
  incident_title: string;
  category: string;
  total_financial_loss: number;
  timeline_summary: string;
  evidence_file_ids: string[];
}): Promise<IncidentReportResponse> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/evidence/incident-reports`, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to compile incident report: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchIncidentDossiers(): Promise<IncidentReportResponse[]> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/evidence/incident-reports`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch incident dossiers: ${res.statusText}`);
  }
  return res.json();
}


// --- Personal Data & Privacy Protection API ---

export interface DetectedEntityItem {
  type: string;
  raw_preview: string;
  start: number;
  end: number;
  confidence: number;
  is_checksum_valid?: boolean | null;
}

export interface PrivacyScanResponse {
  scan_id?: string | null;
  detected_entities: DetectedEntityItem[];
  detected_counts: Record<string, number>;
  risk_score: number;
  risk_level: string;
  sanitized_text: string;
  recommendations: string[];
  created_at: string;
}

export interface PrivacyHistoryItem {
  id: string;
  redacted_preview: string;
  detected_types: Record<string, number>;
  risk_score: number;
  created_at: string;
}

export async function scanTextPrivacy(text: string): Promise<PrivacyScanResponse> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/privacy/scan-text`, {
    method: "POST",
    headers,
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Privacy scan failed: ${res.statusText}`);
  }
  return res.json();
}

export async function scanFilePrivacy(file: File): Promise<PrivacyScanResponse> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/privacy/scan-file`, {
    method: "POST",
    headers,
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Privacy file scan failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchPrivacyHistory(): Promise<PrivacyHistoryItem[]> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/privacy/history`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch privacy history: ${res.statusText}`);
  }
  return res.json();
}

export async function deletePrivacyScanHistory(scanId: string): Promise<void> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/privacy/history/${encodeURIComponent(scanId)}`, {
    method: "DELETE",
    headers,
  });
  if (!res.ok) {
    throw new Error(`Failed to delete privacy scan: ${res.statusText}`);
  }
}

// --- Specialized Demographic Modules API (Women Safety & Senior Protection) ---

export interface HarassmentAnalysisResponse {
  threat_severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL_EMERGENCY";
  detected_patterns: string[];
  risk_score: number;
  immediate_actions: string[];
  emergency_helplines: {
    name: string;
    number: string;
    portal?: string | null;
    description: string;
  }[];
  evidence_checklist: string[];
  official_filing_link: string;
}

export interface SeniorSafetyResponse {
  verdict: "DANGEROUS SCAM" | "SUSPICIOUS" | "LIKELY LEGITIMATE";
  plain_explanation: string;
  voice_script: string;
  scam_category: string;
  what_to_do_now: string[];
  emergency_helpline: string;
  language: string;
}

export interface TrustedContactItem {
  id: string;
  name: string;
  relationship_type: string;
  phone_number: string;
  email?: string | null;
  has_explicit_consent: boolean;
  notify_on_critical_scam: boolean;
  created_at: string;
}

export interface TrustedContactAlertResponse {
  contact_name: string;
  phone_number: string;
  draft_sms_text: string;
  whatsapp_share_url: string;
}

export async function analyzeWomenSafetyThreat(
  content: string,
  context?: string
): Promise<HarassmentAnalysisResponse> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/demographics/women-safety/analyze`, {
    method: "POST",
    headers,
    body: JSON.stringify({ content, context }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Safety assessment failed: ${res.statusText}`);
  }
  return res.json();
}

export async function explainSeniorSafety(
  message: string,
  language: "en" | "kn" | "hi" = "en"
): Promise<SeniorSafetyResponse> {
  const res = await fetch(`${API_BASE_URL}/demographics/senior-safety/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, language }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Senior scam explainer failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchTrustedContacts(): Promise<TrustedContactItem[]> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/demographics/trusted-contacts`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch trusted contacts: ${res.statusText}`);
  }
  return res.json();
}

export async function createTrustedContact(data: {
  name: string;
  relationship_type: string;
  phone_number: string;
  email?: string;
  has_explicit_consent: boolean;
  notify_on_critical_scam: boolean;
}): Promise<TrustedContactItem> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/demographics/trusted-contacts`, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to add trusted contact: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteTrustedContact(contactId: string): Promise<void> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/demographics/trusted-contacts/${encodeURIComponent(contactId)}`, {
    method: "DELETE",
    headers,
  });
  if (!res.ok) {
    throw new Error(`Failed to delete contact: ${res.statusText}`);
  }
}

export async function generateTrustedContactAlert(data: {
  contact_id: string;
  incident_type: string;
  incident_details?: string;
}): Promise<TrustedContactAlertResponse> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/demographics/trusted-contacts/generate-alert`, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to generate alert: ${res.statusText}`);
  }
  return res.json();
}

// --- Deepfake & Media Authenticity Analysis API ---

export interface DeepfakeScanResponse {
  id?: string | null;
  file_name: string;
  file_hash: string;
  media_type: string;
  file_size_kb: number;
  authenticity_score: number;
  verdict: string;
  forensic_flags: {
    media_type: string;
    file_size_kb: number;
    metadata: {
      has_exif: boolean;
      software_tags: string[];
      ai_signatures: string[];
      editing_signatures: string[];
      raw_text_traces: string[];
      c2pa_manifest_found: boolean;
    };
    ela_analysis?: {
      mean_error_level: number;
      error_std_dev: number;
      peak_error: number;
      regional_variance: number;
      ela_anomaly_flag: boolean;
      assessment: string;
    } | null;
    audio_forensics?: {
      channels?: number | null;
      sample_rate_hz?: number | null;
      duration_seconds?: number | null;
      synthetic_voice_indicators: string[];
    } | null;
    video_forensics?: {
      format: string;
      detected_atoms: string[];
      encoder_clues: string[];
    } | null;
    suspicious_factors: string[];
    authenticity_indicators: string[];
  };
  limitations_disclaimer: string;
  created_at?: string | null;
}

export interface DeepfakeHistoryItem {
  id: string;
  file_name?: string | null;
  media_type: string;
  file_hash: string;
  verdict: string;
  authenticity_score: number;
  created_at: string;
}

export async function analyzeMediaAuthenticity(file: File): Promise<DeepfakeScanResponse> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/deepfake/analyze`, {
    method: "POST",
    headers,
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Media authenticity analysis failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchDeepfakeHistory(): Promise<DeepfakeHistoryItem[]> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/deepfake/history`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch deepfake history: ${res.statusText}`);
  }
  return res.json();
}

export async function reportDeepfakeScan(scanId: string, description?: string): Promise<{
  report_code: string;
  threat_type: string;
  target_value: string;
  status: string;
  message: string;
}> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/deepfake/report`, {
    method: "POST",
    headers,
    body: JSON.stringify({ scan_id: scanId, description }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to report threat: ${res.statusText}`);
  }
  return res.json();
}

// --- Cyber Awareness & Education API ---

export interface LessonItem {
  id: string;
  order_index: number;
  title: string;
  content: string;
  is_completed: boolean;
}

export interface QuizQuestionOut {
  id: number;
  question: string;
  options: string[];
}

export interface QuizDetail {
  id: string;
  title: string;
  passing_score: number;
  total_questions: number;
  questions: QuizQuestionOut[];
}

export interface CourseListItem {
  id: string;
  slug: string;
  title: string;
  description: string;
  target_audience: string;
  language: string;
  total_lessons: number;
  completed_lessons: number;
  is_completed: boolean;
  has_quiz: boolean;
  quiz_passed: boolean;
  highest_score?: number | null;
}

export interface CourseDetail {
  id: string;
  slug: string;
  title: string;
  description: string;
  target_audience: string;
  language: string;
  lessons: LessonItem[];
  quiz?: QuizDetail | null;
  progress_percentage: number;
  is_completed: boolean;
  quiz_passed: boolean;
}

export interface QuizQuestionResult {
  question_id: number;
  question: string;
  user_answer_index?: number | null;
  correct_answer_index: number;
  is_correct: boolean;
  explanation: string;
}

export interface QuizSubmissionResponse {
  quiz_id: string;
  score: number;
  passed: boolean;
  passing_score: number;
  correct_count: number;
  total_questions: number;
  question_results: QuizQuestionResult[];
  badge_earned?: string | null;
}

export interface BadgeItem {
  name: string;
  title: string;
  description: string;
  icon: string;
  earned_at?: string | null;
}

export interface LearningStatsResponse {
  courses_enrolled: number;
  courses_completed: number;
  lessons_completed: number;
  quizzes_taken: number;
  quizzes_passed: number;
  badges: BadgeItem[];
}

export async function fetchCourses(audience?: string): Promise<CourseListItem[]> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const query = audience ? `?audience=${encodeURIComponent(audience)}` : "";
  const res = await fetch(`${API_BASE_URL}/education/courses${query}`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch courses: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchCourseDetail(slug: string): Promise<CourseDetail> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/education/courses/${encodeURIComponent(slug)}`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch course: ${res.statusText}`);
  }
  return res.json();
}

export async function completeCourseLesson(lessonId: string): Promise<{
  status: string;
  lesson_id: string;
  course_id: string;
  completed_count: number;
  total_lessons: number;
  course_completed: boolean;
}> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/education/lessons/${encodeURIComponent(lessonId)}/complete`, {
    method: "POST",
    headers,
  });
  if (!res.ok) {
    throw new Error(`Failed to mark lesson completed: ${res.statusText}`);
  }
  return res.json();
}

export async function submitCourseQuiz(
  quizId: string,
  answers: Record<string, number>
): Promise<QuizSubmissionResponse> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/education/quizzes/${encodeURIComponent(quizId)}/submit`, {
    method: "POST",
    headers,
    body: JSON.stringify({ answers }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Quiz submission failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchLearningProgress(): Promise<LearningStatsResponse> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/education/my-progress`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch learning progress: ${res.statusText}`);
  }
  return res.json();
}

// --- In-App Notifications API ---

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  category: string;
  is_read: boolean;
  action_url?: string | null;
  created_at: string;
}

export interface NotificationListResponse {
  total: number;
  unread_count: number;
  items: NotificationItem[];
}

export async function fetchNotifications(
  unreadOnly: boolean = false,
  limit: number = 50,
  skip: number = 0
): Promise<NotificationListResponse> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const query = `?unread_only=${unreadOnly}&limit=${limit}&skip=${skip}`;
  const res = await fetch(`${API_BASE_URL}/notifications${query}`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch notifications: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchUnreadNotificationCount(): Promise<{ unread_count: number }> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/notifications/unread-count`, { headers });
  if (!res.ok) {
    return { unread_count: 0 };
  }
  return res.json();
}

export async function markNotificationAsRead(id: string): Promise<NotificationItem> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/notifications/${encodeURIComponent(id)}/read`, {
    method: "POST",
    headers,
  });
  if (!res.ok) {
    throw new Error(`Failed to mark notification read: ${res.statusText}`);
  }
  return res.json();
}

export async function markAllNotificationsAsRead(): Promise<{ status: string; marked_read_count: number }> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/notifications/read-all`, {
    method: "POST",
    headers,
  });
  if (!res.ok) {
    throw new Error(`Failed to mark all read: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteNotification(id: string): Promise<void> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/notifications/${encodeURIComponent(id)}`, {
    method: "DELETE",
    headers,
  });
  if (!res.ok) {
    throw new Error(`Failed to delete notification: ${res.statusText}`);
  }
}

export async function broadcastAdminNotification(data: {
  title: string;
  message: string;
  category?: string;
  action_url?: string;
}): Promise<{ recipient_count: number; title: string; status: string }> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/notifications/admin/broadcast`, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to broadcast notification: ${res.statusText}`);
  }
  return res.json();
}

// --- Admin Security, Monitoring & Threat Intelligence API ---

export interface AdminUserListItem {
  id: string;
  email: string;
  role: string;
  role_id: number;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  scans_count: number;
  reports_count: number;
  full_name?: string | null;
  phone_number?: string | null;
}

export interface AuditLogListItem {
  id: string;
  user_id?: string | null;
  user_email?: string | null;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, any>;
  ip_address?: string | null;
  created_at: string;
}

export interface SystemHealthTelemetry {
  database: string;
  total_users: number;
  active_users: number;
  total_scans: number;
  total_reports: number;
  verified_threats: number;
  total_evidence_files: number;
  evidence_vault_bytes: number;
  active_threat_indicators: number;
  recent_security_events: number;
  audit_logs_count: number;
  uptime_status: string;
}

export interface AdminThreatItem {
  id: string;
  indicator_type: string;
  indicator_value: string;
  threat_level: string;
  description: string;
  incident_count: number;
  is_active: boolean;
  origin_report_id?: string | null;
  created_at: string;
  updated_at: string;
}

export async function fetchAdminUsers(
  search?: string,
  role?: string,
  isActive?: boolean
): Promise<AdminUserListItem[]> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const params = new URLSearchParams();
  if (search) params.append("search", search);
  if (role) params.append("role", role);
  if (isActive !== undefined) params.append("is_active", String(isActive));

  const res = await fetch(`${API_BASE_URL}/admin/users?${params.toString()}`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch admin users: ${res.statusText}`);
  }
  return res.json();
}

export async function updateAdminUserRole(userId: string, roleName: string): Promise<any> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/admin/users/${encodeURIComponent(userId)}/role`, {
    method: "PUT",
    headers,
    body: JSON.stringify({ role_name: roleName }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to update role: ${res.statusText}`);
  }
  return res.json();
}

export async function toggleAdminUserStatus(userId: string, isActive: boolean): Promise<any> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/admin/users/${encodeURIComponent(userId)}/status`, {
    method: "PUT",
    headers,
    body: JSON.stringify({ is_active: isActive }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to toggle status: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchAdminAuditLogs(
  action?: string,
  resourceType?: string,
  limit: number = 50
): Promise<AuditLogListItem[]> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const params = new URLSearchParams();
  if (action) params.append("action", action);
  if (resourceType) params.append("resource_type", resourceType);
  params.append("limit", String(limit));

  const res = await fetch(`${API_BASE_URL}/admin/audit-logs?${params.toString()}`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch audit logs: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchAdminTelemetry(): Promise<SystemHealthTelemetry> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/admin/telemetry`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch telemetry: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchAdminThreats(activeOnly: boolean = false): Promise<AdminThreatItem[]> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/admin/threats?active_only=${activeOnly}`, { headers });
  if (!res.ok) {
    throw new Error(`Failed to fetch threats: ${res.statusText}`);
  }
  return res.json();
}

export async function updateAdminThreat(
  threatId: string,
  data: { threat_level?: string; is_active?: boolean; description?: string }
): Promise<AdminThreatItem> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/admin/threats/${encodeURIComponent(threatId)}`, {
    method: "PUT",
    headers,
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to update threat: ${res.statusText}`);
  }
  return res.json();
}

export async function broadcastThreatAlert(threatId: string): Promise<any> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/admin/threats/${encodeURIComponent(threatId)}/broadcast`, {
    method: "POST",
    headers,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to broadcast threat: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchCurrentUserProfile(): Promise<any> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/auth/me`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch user profile.");
  }
  return res.json();
}

export async function updateUserProfile(payload: {
  full_name?: string;
  phone_number?: string;
  preferred_language?: string;
  senior_mode?: boolean;
}): Promise<any> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/auth/me/profile`, {
    method: "PUT",
    headers,
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update profile.");
  }
  return res.json();
}

export async function changeUserPassword(payload: {
  current_password: string;
  new_password: string;
}): Promise<any> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/auth/me/password`, {
    method: "PUT",
    headers,
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to change password.");
  }
  return res.json();
}
