import {
  JobOffer,
  UserProfile,
  LetterVersion,
  HistoryEntry,
  AppSettings,
  PitchAndGap,
  InterviewQuestion,
  WorkerState,
  WorkerSettings
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8008";

async function extractErrorMessage(res: Response, fallback: string): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail) && data.detail.length > 0) {
      return data.detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join("; ");
    }
  } catch {
    // ignore JSON parse errors
  }
  return fallback;
}

export async function searchInternships(query: string, location: string): Promise<JobOffer[]> {
  try {
    const res = await fetch(`${API_BASE}/api/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, location }),
    });
    if (!res.ok) throw new Error(await extractErrorMessage(res, "Erreur de recherche"));
    const data = await res.json();
    return data.results || [];
  } catch (err) {
    console.error("API error search:", err);
    return [];
  }
}

export async function importOffer(url?: string, rawText?: string): Promise<JobOffer> {
  const res = await fetch(`${API_BASE}/api/search/import-offer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: url?.trim() || undefined, raw_text: rawText?.trim() || undefined }),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, "Impossible d'importer cette offre."));
  }
  const data = await res.json();
  if (!data?.offer) {
    throw new Error("Aucune offre n'a pu être extraite.");
  }
  return data.offer;
}

export interface AiKeywordsSuggestion {
  suggested_query: string;
  specialties: string[];
  alternative_queries?: { label: string; query: string }[];
  rationale?: string;
}

export async function suggestKeywordsFromCv(profile?: UserProfile): Promise<AiKeywordsSuggestion> {
  const res = await fetch(`${API_BASE}/api/search/suggest-keywords`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile }),
  });
  if (!res.ok) {
    throw new Error(
      await extractErrorMessage(
        res,
        "Veuillez d'abord importer votre CV ou renseigner vos compétences dans l'onglet Profil."
      )
    );
  }
  return await res.json();
}

export async function getPitchAndGap(job: JobOffer, profile?: UserProfile): Promise<PitchAndGap | null> {
  try {
    const res = await fetch(`${API_BASE}/api/letters/pitch-and-gap`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job, profile }),
    });
    if (!res.ok) throw new Error("Erreur analyse pitch et gap");
    const data = await res.json();
    return data.analysis || null;
  } catch (err) {
    console.error("API error pitch-and-gap:", err);
    return null;
  }
}

export async function getInterviewPrep(job: JobOffer, profile?: UserProfile): Promise<InterviewQuestion[]> {
  try {
    const res = await fetch(`${API_BASE}/api/letters/interview-prep`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job, profile }),
    });
    if (!res.ok) throw new Error("Erreur questions entretien");
    const data = await res.json();
    return data.questions || [];
  } catch (err) {
    console.error("API error interview prep:", err);
    return [];
  }
}

export async function getProfile(): Promise<UserProfile> {
  try {
    const res = await fetch(`${API_BASE}/api/cv/profile`);
    if (!res.ok) throw new Error("Erreur récupération profil");
    return await res.json();
  } catch (err) {
    console.warn("Backend non accessible pour le profil :", err);
    return {
      full_name: "",
      email: "",
      phone: "",
      education: "",
      target_domains: [],
      technical_skills: [],
      key_projects: [],
    };
  }
}

export async function updateProfile(profile: UserProfile): Promise<UserProfile> {
  try {
    const res = await fetch(`${API_BASE}/api/cv/profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    if (!res.ok) throw new Error(await extractErrorMessage(res, "Erreur mise à jour profil"));
    const data = await res.json();
    return data.profile;
  } catch (err) {
    console.error("Erreur updateProfile:", err);
    return profile;
  }
}

export async function uploadCvFile(file: File): Promise<UserProfile> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/cv/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, "Erreur lors du téléversement du CV."));
  }
  const data = await res.json();
  return data.profile;
}

export async function generateLetters(job: JobOffer, profile?: UserProfile): Promise<LetterVersion[]> {
  try {
    const res = await fetch(`${API_BASE}/api/letters/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job, profile }),
    });
    if (!res.ok) throw new Error("Erreur génération lettres");
    const data = await res.json();
    return data.versions || [];
  } catch (err) {
    console.error("Erreur generateLetters:", err);
    return [];
  }
}

export async function refineLetter(currentLetter: string, feedback: string, job: JobOffer): Promise<string> {
  const res = await fetch(`${API_BASE}/api/letters/refine`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ current_letter: currentLetter, feedback, job }),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, "Le service d'IA est temporairement indisponible pour réviser la lettre."));
  }
  const data = await res.json();
  return data.refined_letter || currentLetter;
}

export async function getHistory(): Promise<HistoryEntry[]> {
  try {
    const res = await fetch(`${API_BASE}/api/history`);
    if (!res.ok) return [];
    return await res.json();
  } catch (err) {
    console.warn("Backend non accessible pour l'historique :", err);
    return [];
  }
}

export async function saveHistoryEntry(entry: HistoryEntry): Promise<HistoryEntry[]> {
  try {
    const res = await fetch(`${API_BASE}/api/history`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entry),
    });
    if (!res.ok) throw new Error("Erreur sauvegarde historique");
    const data = await res.json();
    return data.history || [];
  } catch (err) {
    console.error("Erreur saveHistoryEntry:", err);
    return [];
  }
}

export async function updateHistoryStatus(id: string, status: HistoryEntry["status"]): Promise<HistoryEntry[] | null> {
  try {
    const res = await fetch(`${API_BASE}/api/history/${encodeURIComponent(id)}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    if (!res.ok) throw new Error("Erreur mise à jour statut");
    const data = await res.json();
    return data.history || [];
  } catch (err) {
    console.error("Erreur updateHistoryStatus:", err);
    return null;
  }
}

export async function deleteHistoryEntry(id: string): Promise<HistoryEntry[] | null> {
  try {
    const res = await fetch(`${API_BASE}/api/history/${encodeURIComponent(id)}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Erreur suppression historique");
    const data = await res.json();
    return data.history || [];
  } catch (err) {
    console.error("Erreur deleteHistoryEntry:", err);
    return null;
  }
}

export async function getSettings(): Promise<AppSettings> {
  try {
    const res = await fetch(`${API_BASE}/api/settings`);
    if (!res.ok) throw new Error("Erreur récupération paramètres");
    return await res.json();
  } catch (err) {
    console.warn("Backend non accessible pour les paramètres, utilisation du fallback :", err);
    return {
      active_provider: "gemini",
      ollama_base_url: "http://localhost:11434",
      ollama_model: "llama3:latest",
    };
  }
}

export async function saveSettings(settings: AppSettings): Promise<AppSettings> {
  try {
    const res = await fetch(`${API_BASE}/api/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });
    if (!res.ok) throw new Error("Erreur enregistrement paramètres");
    const data = await res.json();
    return data.settings || settings;
  } catch (err) {
    console.error("Erreur saveSettings:", err);
    return settings;
  }
}

export async function getWorkerStatus(): Promise<WorkerState> {
  try {
    const res = await fetch(`${API_BASE}/api/worker/status`);
    if (!res.ok) throw new Error("Erreur récupération statut worker");
    return await res.json();
  } catch (err) {
    console.warn("Backend non accessible pour le worker :", err);
    return {
      is_running: false,
      last_sync: null,
      total_jobs: 0,
      active_jobs: 0,
      expired_jobs: 0,
      last_error: null,
      sources_stats: {}
    };
  }
}

export async function triggerWorkerSync(): Promise<{ status: string; message: string; state: WorkerState }> {
  const res = await fetch(`${API_BASE}/api/worker/trigger`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Erreur déclenchement synchronisation");
  return await res.json();
}

export async function getWorkerSettings(): Promise<WorkerSettings> {
  try {
    const res = await fetch(`${API_BASE}/api/worker/settings`);
    if (!res.ok) throw new Error("Erreur récupération paramètres worker");
    return await res.json();
  } catch (err) {
    console.warn("Backend non accessible pour les paramètres worker :", err);
    return {
      scan_interval_hours: 6,
      auto_liveness_check: true,
      hide_expired_by_default: false,
      sources: [],
      target_locations: ["France", "Paris", "Europe", "Remote"]
    };
  }
}

export async function saveWorkerSettings(settings: WorkerSettings): Promise<WorkerSettings> {
  try {
    const res = await fetch(`${API_BASE}/api/worker/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });
    if (!res.ok) throw new Error("Erreur enregistrement paramètres worker");
    const data = await res.json();
    return data.settings || settings;
  } catch (err) {
    console.error("Erreur saveWorkerSettings:", err);
    return settings;
  }
}
