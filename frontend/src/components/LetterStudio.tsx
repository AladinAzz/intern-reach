"use client";

import React, { useState, useEffect } from "react";
import { JobOffer, LetterVersion, HistoryEntry, PitchAndGap, InterviewQuestion, UserProfile } from "@/types";
import { Copy, Printer, Bookmark, Sparkles, MessageSquare, Check, RefreshCw, Building2, MapPin, Mail, Share2, HelpCircle, CheckCircle2, AlertTriangle, Lightbulb, AlertCircle } from "lucide-react";
import { getPitchAndGap, getInterviewPrep } from "@/lib/api";

interface LetterStudioProps {
  job: JobOffer | null;
  versions: LetterVersion[];
  loading: boolean;
  profile?: UserProfile;
  onRefine: (currentLetter: string, feedback: string) => Promise<string>;
  onSaveToHistory: (entry: HistoryEntry) => Promise<void>;
  onBackToSearch: () => void;
}

export const LetterStudio: React.FC<LetterStudioProps> = ({
  job,
  versions,
  loading,
  profile,
  onRefine,
  onSaveToHistory,
  onBackToSearch,
}) => {
  const [selectedVersionIdx, setSelectedVersionIdx] = useState(0);
  const [editedContent, setEditedContent] = useState("");
  const [feedback, setFeedback] = useState("");
  const [refining, setRefining] = useState(false);
  const [refineError, setRefineError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [saved, setSaved] = useState(false);

  // Pitch & Gap and Interview Prep State
  const [pitchAndGap, setPitchAndGap] = useState<PitchAndGap | null>(null);
  const [loadingPitch, setLoadingPitch] = useState(false);
  const [copiedEmail, setCopiedEmail] = useState(false);
  const [copiedLinkedIn, setCopiedLinkedIn] = useState(false);

  const [questions, setQuestions] = useState<InterviewQuestion[]>([]);
  const [isQuestionsOpen, setIsQuestionsOpen] = useState(false);
  const [loadingQuestions, setLoadingQuestions] = useState(false);

  // Sync editedContent with active version
  useEffect(() => {
    if (versions && versions.length > 0) {
      const idx = selectedVersionIdx < versions.length ? selectedVersionIdx : 0;
      if (versions[idx]) {
        setEditedContent(versions[idx].content);
      }
    }
  }, [versions, selectedVersionIdx]);

  // Load Pitch & Gap Analysis and reset per-job state when job or profile identity changes
  const jobKey = job?.id;
  const profileKey = `${profile?.full_name}-${profile?.technical_skills?.join(",")}`;

  useEffect(() => {
    setQuestions([]);
    setSelectedVersionIdx(0);
    setRefineError(null);
    if (job) {
      setLoadingPitch(true);
      getPitchAndGap(job, profile)
        .then((res) => setPitchAndGap(res))
        .finally(() => setLoadingPitch(false));
    } else {
      setPitchAndGap(null);
    }
  }, [jobKey, profileKey]);

  const handleOpenQuestions = async (forceRefresh = false) => {
    if (!job) return;
    setIsQuestionsOpen(true);
    if (questions.length === 0 || forceRefresh) {
      setLoadingQuestions(true);
      try {
        const res = await getInterviewPrep(job, profile);
        setQuestions(res);
      } finally {
        setLoadingQuestions(false);
      }
    }
  };

  if (!job) {
    return (
      <div className="swiss-card p-12 text-center space-y-4">
        <Sparkles className="w-10 h-10 text-swiss-muted mx-auto" />
        <h3 className="text-base font-bold font-sans text-swiss-black">
          Aucune offre sélectionnée pour le moment
        </h3>
        <p className="text-xs text-swiss-muted font-sans max-w-md mx-auto">
          Accédez à l&apos;onglet « Recherche d&apos;Offres » et cliquez sur « Rédiger la Lettre » pour analyser la demande d&apos;un recruteur et générer des versions adaptées.
        </p>
        <button
          onClick={onBackToSearch}
          className="px-4 py-2 bg-swiss-blue text-white text-xs font-mono font-semibold rounded-swiss hover:bg-swiss-blue-hover transition-colors"
        >
          EXPLORER LES OFFRES DISPONIBLES
        </button>
      </div>
    );
  }

  const activeVersion = versions[selectedVersionIdx] || versions[0];

  const handleCopy = () => {
    navigator.clipboard.writeText(editedContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleCopyEmail = () => {
    if (pitchAndGap) {
      const fullText = `Objet: ${pitchAndGap.cold_email_subject}\n\n${pitchAndGap.cold_email_body}`;
      navigator.clipboard.writeText(fullText);
      setCopiedEmail(true);
      setTimeout(() => setCopiedEmail(false), 2500);
    }
  };

  const handleCopyLinkedIn = () => {
    if (pitchAndGap) {
      navigator.clipboard.writeText(pitchAndGap.linkedin_note);
      setCopiedLinkedIn(true);
      setTimeout(() => setCopiedLinkedIn(false), 2500);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleRefineSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedback.trim()) return;
    setRefining(true);
    setRefineError(null);
    try {
      const updated = await onRefine(editedContent, feedback);
      setEditedContent(updated);
      setFeedback("");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erreur lors de la révision par l'IA.";
      setRefineError(msg);
    } finally {
      setRefining(false);
    }
  };

  const handleSave = async () => {
    const entry: HistoryEntry = {
      id: `${job.id}-${Date.now()}`,
      job_title: job.title,
      company: job.company,
      location: job.location,
      url: job.url,
      applied_at: new Date().toLocaleDateString("fr-FR"),
      status: "Enregistré",
      selected_version: activeVersion ? activeVersion.label : "Standard",
      letter_content: editedContent,
    };
    await onSaveToHistory(entry);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Target Job Header Banner */}
      <div className="swiss-card p-6 border-l-4 border-l-swiss-blue no-print">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="space-y-1">
            <span className="swiss-badge bg-blue-50 text-swiss-blue border border-blue-200">
              OFFRE CIBLÉE // {job.category}
            </span>
            <h2 className="text-lg font-bold font-sans text-swiss-black">
              {job.title}
            </h2>
            <div className="flex items-center space-x-4 text-xs font-mono text-swiss-muted">
              <span className="flex items-center space-x-1 font-semibold text-swiss-black">
                <Building2 className="w-3.5 h-3.5 text-swiss-blue" />
                <span>{job.company}</span>
              </span>
              <span className="flex items-center space-x-1">
                <MapPin className="w-3.5 h-3.5 text-swiss-muted" />
                <span>{job.location}</span>
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center space-x-2 shrink-0">
            <button
              onClick={() => handleOpenQuestions(false)}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-blue-50 border border-blue-200 text-swiss-blue hover:bg-blue-100 text-xs font-mono font-semibold rounded-swiss transition-colors"
              title="Anticiper les 5 questions techniques d'entretien"
            >
              <HelpCircle className="w-3.5 h-3.5" />
              <span>SIMULATEUR D&apos;ENTRETIEN</span>
            </button>
            <button
              onClick={handleCopy}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-swiss-border hover:bg-swiss-neutral text-xs font-mono text-swiss-black rounded-swiss transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-swiss-muted" />}
              <span>{copied ? "COPIÉ !" : "COPIER"}</span>
            </button>
            <button
              onClick={handlePrint}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-swiss-border hover:bg-swiss-neutral text-xs font-mono text-swiss-black rounded-swiss transition-colors"
            >
              <Printer className="w-3.5 h-3.5 text-swiss-muted" />
              <span>IMPRIMER / PDF</span>
            </button>
            <button
              onClick={handleSave}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-swiss-blue hover:bg-swiss-blue-hover text-white text-xs font-mono font-semibold rounded-swiss transition-colors shadow-sm"
            >
              <Bookmark className="w-3.5 h-3.5" />
              <span>{saved ? "ENREGISTRÉ !" : "SAUVEGARDER"}</span>
            </button>
          </div>
        </div>

        {/* ATS Gap Analysis & Direct Match Overview */}
        {pitchAndGap && (
          <div className="mt-4 pt-4 border-t border-swiss-neutral grid grid-cols-1 md:grid-cols-12 gap-4 text-xs font-sans">
            <div className="md:col-span-4 space-y-1">
              <span className="font-mono text-emerald-800 font-semibold flex items-center space-x-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Compétences Validées ({pitchAndGap.matched_skills.length})</span>
              </span>
              <div className="flex flex-wrap gap-1">
                {pitchAndGap.matched_skills.map((s) => (
                  <span key={s} className="px-1.5 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-900 font-mono text-[11px]">
                    {s}
                  </span>
                ))}
              </div>
            </div>

            <div className="md:col-span-4 space-y-1">
              <span className="font-mono text-amber-800 font-semibold flex items-center space-x-1">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                <span>Points d&apos;Attention / À Valoriser ({pitchAndGap.missing_skills.length})</span>
              </span>
              <div className="flex flex-wrap gap-1">
                {pitchAndGap.missing_skills.length > 0 ? (
                  pitchAndGap.missing_skills.map((s) => (
                    <span key={s} className="px-1.5 py-0.5 rounded bg-amber-50 border border-amber-200 text-amber-900 font-mono text-[11px]">
                      {s}
                    </span>
                  ))
                ) : (
                  <span className="text-swiss-muted text-[11px] italic">Profil 100% aligné sur les mots-clés</span>
                )}
              </div>
            </div>

            <div className="md:col-span-4 space-y-1">
              <span className="font-mono text-swiss-blue font-semibold flex items-center space-x-1">
                <Lightbulb className="w-3.5 h-3.5" />
                <span>Conseil Stratégique de Compensation</span>
              </span>
              <p className="text-[11px] text-swiss-black/80 italic leading-snug">
                {pitchAndGap.bridge_advice}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Version Selector Tabs */}
      {versions.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 no-print">
          {versions.map((ver, idx) => {
            const isSelected = selectedVersionIdx === idx;
            return (
              <button
                key={ver.version_id}
                onClick={() => setSelectedVersionIdx(idx)}
                className={`p-4 rounded-swiss text-left transition-all border ${
                  isSelected
                    ? "bg-white border-swiss-blue shadow-swiss ring-1 ring-swiss-blue"
                    : "bg-white/80 border-swiss-border hover:border-swiss-blue/50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-swiss-black">
                    {ver.label}
                  </span>
                  <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold">
                    {ver.match_percentage}% MATCH
                  </span>
                </div>
                <div className="text-[11px] font-sans text-swiss-muted mt-1 leading-snug">
                  {ver.target_fit}
                </div>
                <div className="text-[11px] font-mono text-swiss-blue mt-1">
                  Ton : {ver.tone}
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* Motivation Letter Live Editor */}
      <div className="swiss-card p-8 bg-white space-y-4">
        <div className="flex items-center justify-between border-b border-swiss-neutral pb-3 no-print">
          <span className="text-xs font-mono text-swiss-muted">
            DOCUMENT SCIENTIFIQUE // VERSION ACTIVE : {activeVersion?.label.toUpperCase() || "GÉNÉRATION EN COURS"}
          </span>
          <span className="text-xs font-mono text-swiss-muted">
            {editedContent.length} CARACTÈRES | {editedContent.split(/\s+/).filter(Boolean).length} MOTS
          </span>
        </div>

        {loading ? (
          <div className="py-16 text-center space-y-3">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-swiss-blue border-t-transparent" />
            <h4 className="text-sm font-bold font-sans text-swiss-black">
              Génération des 3 versions scientifiques par Gemini en cours...
            </h4>
            <p className="text-xs font-mono text-swiss-muted">
              Dérivation des arguments techniques pour {job.company} selon les exigences recruteur
            </p>
          </div>
        ) : (
          <textarea
            value={editedContent}
            onChange={(e) => setEditedContent(e.target.value)}
            rows={18}
            className="w-full text-sm font-sans text-swiss-black leading-relaxed outline-none border-none resize-none p-2 focus:ring-0 bg-transparent selection:bg-swiss-blue selection:text-white"
            placeholder="Génération du contenu de la lettre..."
          />
        )}
      </div>

      {/* Interactive User Feedback Refinement Bar */}
      <div className="swiss-card p-6 bg-swiss-neutral/30 no-print space-y-3">
        <div className="flex items-center space-x-2 text-xs font-mono font-semibold text-swiss-black">
          <MessageSquare className="w-4 h-4 text-swiss-blue" />
          <span>BOUCLE D&apos;ASSISTANCE & RETOURS UTILISATEUR</span>
        </div>
        <p className="text-xs text-swiss-muted font-sans">
          Indiquez vos ajustements sur cette version (ex: <em>« Insiste davantage sur mon projet de SLAM sous ROS 2 »</em> ou <em>« Raccourcis à 3 paragraphes »</em>).
        </p>

        {refineError && (
          <div data-testid="refine-letter-error" role="alert" className="p-2.5 bg-rose-50 border border-rose-200 text-rose-800 rounded text-xs font-mono flex items-center space-x-1.5">
            <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
            <span>{refineError}</span>
          </div>
        )}

        <form onSubmit={handleRefineSubmit} className="flex gap-2">
          <input
            type="text"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Écrivez votre demande de modification personnalisée..."
            className="flex-1 px-3 py-2 text-xs font-sans bg-white border border-swiss-border rounded-swiss outline-none focus:border-swiss-blue"
          />
          <button
            type="submit"
            disabled={refining || !feedback.trim()}
            className="px-4 py-2 bg-swiss-blue hover:bg-swiss-blue-hover text-white text-xs font-mono font-semibold rounded-swiss transition-colors flex items-center space-x-1.5 disabled:opacity-50 shadow-sm shrink-0"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refining ? "animate-spin" : ""}`} />
            <span>{refining ? "RÉVISION..." : "RÉVISER LA LETTRE"}</span>
          </button>
        </form>
      </div>

      {/* Cold Email & LinkedIn Pitch Section */}
      <div className="space-y-3 no-print pt-2">
        <div className="flex items-center justify-between px-1">
          <span className="text-xs font-mono font-bold text-swiss-black uppercase tracking-wider flex items-center space-x-1.5">
            <Mail className="w-4 h-4 text-swiss-blue" />
            <span>PITCH EMAIL & NOTE LINKEDIN // GÉNÉRATION DIRECTE</span>
          </span>
          <span className="text-[11px] font-mono text-swiss-muted">
            {loadingPitch ? "SYNTHÈSE EN COURS..." : "PRÊT À L'ENVOI"}
          </span>
        </div>

        {loadingPitch && (
          <div className="swiss-card p-6 text-center space-y-2 bg-white">
            <div className="inline-block animate-spin rounded-full h-5 w-5 border-2 border-swiss-blue border-t-transparent" />
            <p className="text-xs font-mono text-swiss-muted">
              Génération du Cold Email percutant et de l&apos;accroche LinkedIn (&lt;300 car.) par Gemini...
            </p>
          </div>
        )}

        {pitchAndGap && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="swiss-card p-5 space-y-2 bg-white border-l-2 border-l-swiss-blue shadow-sm">
              <div className="flex items-center justify-between border-b border-swiss-neutral pb-2">
                <span className="font-mono text-xs font-bold text-swiss-black flex items-center space-x-1.5">
                  <Mail className="w-3.5 h-3.5 text-swiss-blue" />
                  <span>PITCH EMAIL D&apos;ACCOMPAGNEMENT</span>
                </span>
                <button
                  onClick={handleCopyEmail}
                  className="px-2 py-0.5 text-xs font-mono bg-swiss-neutral hover:bg-swiss-blue hover:text-white rounded border border-swiss-border transition-colors flex items-center space-x-1"
                >
                  {copiedEmail ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3 text-swiss-muted" />}
                  <span>{copiedEmail ? "Copié !" : "Copier Email"}</span>
                </button>
              </div>
              <div className="text-[11px] font-mono text-swiss-muted">
                <strong>Objet :</strong> {pitchAndGap.cold_email_subject}
              </div>
              <div className="text-xs font-sans text-swiss-black/85 whitespace-pre-wrap leading-relaxed bg-swiss-neutral/30 p-3 rounded border border-swiss-border select-all">
                {pitchAndGap.cold_email_body}
              </div>
            </div>

            <div className="swiss-card p-5 space-y-2 bg-white border-l-2 border-l-swiss-blue shadow-sm">
              <div className="flex items-center justify-between border-b border-swiss-neutral pb-2">
                <span className="font-mono text-xs font-bold text-swiss-black flex items-center space-x-1.5">
                  <Share2 className="w-3.5 h-3.5 text-swiss-blue" />
                  <span>MESSAGE ACCROCHE LINKEDIN RECRUTEUR (&lt;300 CAR.)</span>
                </span>
                <button
                  onClick={handleCopyLinkedIn}
                  className="px-2 py-0.5 text-xs font-mono bg-swiss-neutral hover:bg-swiss-blue hover:text-white rounded border border-swiss-border transition-colors flex items-center space-x-1"
                >
                  {copiedLinkedIn ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3 text-swiss-muted" />}
                  <span>{copiedLinkedIn ? "Copié !" : "Copier Note"}</span>
                </button>
              </div>
              <div className="text-[11px] font-mono text-swiss-muted">
                <strong>Longueur :</strong> {pitchAndGap.linkedin_note.length} caractères (Limite LinkedIn : 300)
              </div>
              <div className="text-xs font-sans text-swiss-black/85 whitespace-pre-wrap leading-relaxed bg-swiss-neutral/30 p-3 rounded border border-swiss-border select-all">
                {pitchAndGap.linkedin_note}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Technical Interview Simulator Modal */}
      {isQuestionsOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4 no-print">
          <div className="bg-white rounded-swiss max-w-3xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] flex flex-col border border-swiss-border">
            <div className="flex items-start justify-between border-b border-swiss-neutral pb-3">
              <div>
                <div className="flex items-center space-x-2">
                  <HelpCircle className="w-4 h-4 text-swiss-blue" />
                  <h3 className="text-base font-bold font-sans text-swiss-black">
                    Simulateur d&apos;Entretien Technique — {job.company}
                  </h3>
                </div>
                <p className="text-xs text-swiss-muted font-sans mt-0.5">
                  Questions probables dérivées des exigences de l&apos;offre « {job.title} » et de votre profil.
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => handleOpenQuestions(true)}
                  disabled={loadingQuestions}
                  className="px-2.5 py-1 text-xs font-mono border border-swiss-border rounded-swiss hover:bg-swiss-neutral flex items-center space-x-1 disabled:opacity-50"
                >
                  <RefreshCw className={`w-3 h-3 ${loadingQuestions ? "animate-spin" : ""}`} />
                  <span>Régénérer</span>
                </button>
                <button
                  type="button"
                  onClick={() => setIsQuestionsOpen(false)}
                  className="text-swiss-muted hover:text-swiss-black text-xs font-mono px-2 py-1"
                >
                  ✕ Fermer
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {loadingQuestions ? (
                <div className="py-12 text-center space-y-2">
                  <div className="inline-block animate-spin rounded-full h-6 w-6 border-2 border-swiss-blue border-t-transparent" />
                  <p className="text-xs font-mono text-swiss-muted">
                    Génération des 5 questions techniques et grilles de réponse...
                  </p>
                </div>
              ) : questions.length === 0 ? (
                <div className="py-8 text-center text-xs text-swiss-muted font-mono">
                  Aucune question disponible pour le moment.
                </div>
              ) : (
                questions.map((q, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-swiss border border-swiss-border bg-swiss-neutral/20 space-y-2"
                  >
                    <div className="text-xs font-mono font-bold text-swiss-blue">
                      QUESTION 0{idx + 1} // {q.question}
                    </div>
                    <div className="text-xs font-sans text-swiss-black leading-relaxed">
                      <span className="font-mono font-semibold text-emerald-800">Axe de réponse attendu : </span>
                      {q.expected_answer}
                    </div>
                    <div className="text-[11px] font-sans text-swiss-muted italic border-t border-swiss-neutral pt-1.5">
                      <span className="font-mono not-italic font-semibold text-amber-800">Conseil recruteur : </span>
                      {q.tip}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
