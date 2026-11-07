export interface JobOffer {
  id: string;
  title: string;
  company: string;
  location: string;
  contract: string;
  category: string;
  tags: string[];
  match_score: number;
  description: string;
  url: string;
  recruiter_type: string;
  recruiter_profile: string;
  source?: string;
  matched_skills?: string[];
  missing_skills?: string[];
  date_posted?: string;
  is_new?: boolean;
  is_active?: boolean;
  last_checked?: string;
  salary?: string;
  sponsorship?: string;
}

export interface UserProject {
  title: string;
  desc: string;
}

export interface UserProfile {
  full_name: string;
  email: string;
  phone: string;
  education: string;
  target_domains: string[];
  technical_skills: string[];
  key_projects: UserProject[];
  raw_cv_text?: string;
}

export interface LetterVersion {
  version_id: string;
  label: string;
  target_fit: string;
  tone: string;
  match_percentage: number;
  content: string;
}

export interface HistoryEntry {
  id: string;
  job_title: string;
  company: string;
  location: string;
  url: string;
  applied_at: string;
  status: "Enregistré" | "Candidaté" | "Entretien" | "Accepté" | "Refusé";
  selected_version: string;
  letter_content: string;
}

export interface AppSettings {
  active_provider: "gemini" | "openai" | "claude" | "ollama" | "mock";
  gemini_api_key?: string;
  openai_api_key?: string;
  claude_api_key?: string;
  ollama_base_url: string;
  ollama_model: string;
}

export interface PitchAndGap {
  cold_email_subject: string;
  cold_email_body: string;
  linkedin_note: string;
  bridge_advice: string;
  matched_skills: string[];
  missing_skills: string[];
}

export interface InterviewQuestion {
  question: string;
  expected_answer: string;
  tip: string;
}

export interface WorkerState {
  is_running: boolean;
  last_sync: string | null;
  total_jobs: number;
  active_jobs: number;
  expired_jobs: number;
  last_error: string | null;
  sources_stats: Record<string, number>;
}

export interface RegistrySource {
  id: string;
  name: string;
  url: string;
  type: string;
  enabled: boolean;
  description: string;
}

export interface WorkerSettings {
  scan_interval_hours: number;
  auto_liveness_check: boolean;
  hide_expired_by_default: boolean;
  sources: RegistrySource[];
  target_locations: string[];
}


