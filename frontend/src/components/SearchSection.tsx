"use client";

import React, { useState, useMemo, useEffect } from "react";
import { JobOffer, UserProfile } from "@/types";
import { Search, MapPin, ExternalLink, Sparkles, Building2, Layers, CheckCircle2, Link2, PlusCircle, FileText, Calendar, Clock, ArrowUpDown, RefreshCw, UserCheck } from "lucide-react";
import { importOffer } from "@/lib/api";

const formatDateFrench = (dateStr?: string) => {
  if (!dateStr || dateStr === "nan") return "Récemment";
  try {
    const parts = dateStr.slice(0, 10).split("-");
    if (parts.length === 3) {
      const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
      return d.toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" });
    }
  } catch {}
  return dateStr;
};

const isRecentOffer = (dateStr?: string) => {
  if (!dateStr || dateStr === "nan") return false;
  try {
    const parts = dateStr.slice(0, 10).split("-");
    if (parts.length === 3) {
      const postDate = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2])).getTime();
      const now = Date.now();
      const diffHours = (now - postDate) / (1000 * 3600);
      return diffHours <= 96; // within 4 days
    }
  } catch {}
  return false;
};

interface SearchSectionProps {
  offers: JobOffer[];
  loading: boolean;
  profile?: UserProfile;
  onSearch: (query: string, location: string) => void;
  onSelectForLetter: (job: JobOffer) => void;
  onAddCustomOffer?: (job: JobOffer) => void;
  onGoToCvTab?: () => void;
}

export const SearchSection: React.FC<SearchSectionProps> = ({
  offers,
  loading,
  profile,
  onSearch,
  onSelectForLetter,
  onAddCustomOffer,
  onGoToCvTab,
}) => {
  // Compute default search query dynamically from candidate's CV profile
  const defaultCvQuery = useMemo(() => {
    if (profile?.target_domains && profile.target_domains.length > 0) {
      return profile.target_domains.slice(0, 3).join(", ");
    }
    if (profile?.technical_skills && profile.technical_skills.length > 0) {
      return profile.technical_skills.slice(0, 4).join(", ");
    }
    return "";
  }, [profile]);

  const [query, setQuery] = useState(defaultCvQuery);
  const [location, setLocation] = useState("");
  const [sortBy, setSortBy] = useState<"novelty" | "match">("novelty");
  const [hideExpired, setHideExpired] = useState(false);

  // Synchronize search query whenever profile is loaded or updated
  useEffect(() => {
    if (defaultCvQuery && (!query || query === "Systèmes embarqués, Edge AI, Traitement du signal")) {
      setQuery(defaultCvQuery);
    }
  }, [defaultCvQuery]);

  const expiredCount = useMemo(() => {
    return offers.filter((j) => j.is_active === false).length;
  }, [offers]);

  const sortedOffers = useMemo(() => {
    let pool = [...offers];
    if (hideExpired) {
      pool = pool.filter((j) => j.is_active !== false);
    }
    return pool.sort((a, b) => {
      if (sortBy === "novelty") {
        const dA = (a.date_posted || "").slice(0, 10);
        const dB = (b.date_posted || "").slice(0, 10);
        if (dA !== dB) return dB.localeCompare(dA);
        return (b.match_score || 0) - (a.match_score || 0);
      } else {
        return (b.match_score || 0) - (a.match_score || 0);
      }
    });
  }, [offers, hideExpired, sortBy]);

  // Import Modal State
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [importUrl, setImportUrl] = useState("");
  const [importText, setImportText] = useState("");
  const [importing, setImporting] = useState(false);

  const handleImportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importUrl.trim() && !importText.trim()) return;
    setImporting(true);
    try {
      const newOffer = await importOffer(importUrl, importText);
      if (newOffer) {
        if (onAddCustomOffer) onAddCustomOffer(newOffer);
        setIsImportOpen(false);
        setImportUrl("");
        setImportText("");
        onSelectForLetter(newOffer);
      }
    } finally {
      setImporting(false);
    }
  };

  // Dynamically extract specialty filters strictly from candidate's CV profile
  const domainFilters = useMemo(() => {
    const filters = ["Tous"];
    const seen = new Set<string>(["tous"]);

    if (profile?.target_domains && Array.isArray(profile.target_domains)) {
      profile.target_domains.forEach((d) => {
        const clean = d.trim();
        if (clean && !seen.has(clean.toLowerCase())) {
          seen.add(clean.toLowerCase());
          filters.push(clean);
        }
      });
    }

    if (profile?.technical_skills && Array.isArray(profile.technical_skills)) {
      profile.technical_skills.forEach((s) => {
        const clean = s.trim();
        if (clean && !seen.has(clean.toLowerCase()) && filters.length < 9) {
          seen.add(clean.toLowerCase());
          filters.push(clean);
        }
      });
    }

    return filters;
  }, [profile]);

  const locationPills = [
    { label: "Toute la France", val: "" },
    { label: "Paris / IDF", val: "Paris, Île-de-France" },
    { label: "Toulouse", val: "Toulouse" },
    { label: "Lyon", val: "Lyon" },
    { label: "Grenoble", val: "Grenoble" },
    { label: "Sophia Antipolis", val: "Sophia Antipolis" },
    { label: "Rennes", val: "Rennes" },
    { label: "Remote / Télétravail", val: "Télétravail" },
  ];

  const handleFilterClick = (filter: string) => {
    if (filter === "Tous") {
      setQuery(defaultCvQuery);
      onSearch(defaultCvQuery, location);
    } else {
      setQuery(filter);
      onSearch(filter, location);
    }
  };

  const handleLocationClick = (locVal: string) => {
    setLocation(locVal);
    onSearch(query, locVal);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(query, location);
  };

  return (
    <div className="space-y-6">
      {/* Search Header / Filter Form */}
      <div className="swiss-card p-6">
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-12 gap-4">
          <div className="md:col-span-6 space-y-1">
            <div className="flex items-center justify-between">
              <label className="text-xs font-mono font-medium text-swiss-muted uppercase tracking-wider flex items-center space-x-1.5">
                <span>Mots-clés & Spécialités</span>
                {profile?.full_name && (
                  <span className="inline-flex items-center space-x-1 text-[10px] text-swiss-blue bg-blue-50 border border-swiss-blue/20 px-1.5 py-0.5 rounded font-mono normal-case">
                    <UserCheck className="w-3 h-3 text-swiss-blue" />
                    <span>CV : {profile.full_name}</span>
                  </span>
                )}
              </label>
              {defaultCvQuery && query !== defaultCvQuery && (
                <button
                  type="button"
                  onClick={() => {
                    setQuery(defaultCvQuery);
                    onSearch(defaultCvQuery, location);
                  }}
                  className="text-[10px] font-mono text-swiss-blue hover:underline flex items-center space-x-1"
                >
                  <RefreshCw className="w-2.5 h-2.5" />
                  <span>Rétablir mots-clés du CV</span>
                </button>
              )}
            </div>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-swiss-muted" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={defaultCvQuery || "Saisissez vos mots-clés ou importez votre CV..."}
                className="w-full pl-9 pr-4 py-2 text-sm bg-white border border-swiss-border rounded-swiss focus:border-swiss-blue focus:ring-1 focus:ring-swiss-blue outline-none"
              />
            </div>
          </div>

          <div className="md:col-span-4 space-y-1">
            <label className="text-xs font-mono font-medium text-swiss-muted uppercase tracking-wider">
              Localisation Cible (France & Régions)
            </label>
            <div className="relative">
              <MapPin className="w-4 h-4 absolute left-3 top-3 text-swiss-muted" />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Ex: Toulouse, Lyon, Grenoble, Paris, Remote..."
                className="w-full pl-9 pr-4 py-2 text-sm bg-white border border-swiss-border rounded-swiss focus:border-swiss-blue focus:ring-1 focus:ring-swiss-blue outline-none"
              />
            </div>
          </div>

          <div className="md:col-span-2 flex items-end">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 px-4 bg-swiss-blue hover:bg-swiss-blue-hover text-white text-xs font-mono font-semibold rounded-swiss transition-colors flex items-center justify-center space-x-2 shadow-sm disabled:opacity-50"
            >
              <Search className="w-3.5 h-3.5" />
              <span>{loading ? "RECHERCHE..." : "EXÉCUTER"}</span>
            </button>
          </div>
        </form>

        {/* Quick Filter Badges - Domains & Locations */}
        <div className="mt-4 pt-4 border-t border-swiss-neutral space-y-2.5">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] font-mono text-swiss-muted mr-1">
              Spécialités de votre CV :
            </span>
            {domainFilters.length > 1 ? (
              domainFilters.map((f) => {
                const active = query === f || (f === "Tous" && (!query || query === defaultCvQuery));
                return (
                  <button
                    key={f}
                    type="button"
                    onClick={() => handleFilterClick(f)}
                    className={`px-2.5 py-1 text-xs font-mono rounded transition-colors ${
                      active
                        ? "bg-swiss-blue text-white font-semibold"
                        : "bg-swiss-neutral/70 hover:bg-swiss-neutral text-swiss-black"
                    }`}
                  >
                    {f}
                  </button>
                );
              })
            ) : (
              <div className="flex items-center space-x-2">
                <span className="text-xs text-swiss-muted italic">
                  Aucune spécialité détectée dans le profil.
                </span>
                {onGoToCvTab && (
                  <button
                    type="button"
                    onClick={onGoToCvTab}
                    className="text-xs font-mono text-swiss-blue hover:underline font-semibold"
                  >
                    Importer mon CV →
                  </button>
                )}
              </div>
            )}
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-swiss-neutral/60">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-[11px] font-mono text-swiss-muted mr-1">Villes / Hubs :</span>
              {locationPills.map((loc) => {
                const active = location === loc.val || (!location && loc.val === "");
                return (
                  <button
                    key={loc.label}
                    type="button"
                    onClick={() => handleLocationClick(loc.val)}
                    className={`px-2 py-0.5 text-[11px] font-mono rounded border transition-colors ${
                      active
                        ? "bg-slate-800 text-white border-slate-800 font-semibold"
                        : "bg-white text-swiss-muted border-swiss-border hover:border-swiss-blue hover:text-swiss-black"
                    }`}
                  >
                    {loc.label}
                  </button>
                );
              })}
            </div>

            <button
              type="button"
              onClick={() => setIsImportOpen(true)}
              className="flex items-center space-x-1.5 px-3 py-1 bg-white border border-swiss-blue text-swiss-blue hover:bg-swiss-blue hover:text-white rounded-swiss text-xs font-mono font-medium transition-colors shadow-sm"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>IMPORTER UNE OFFRE (URL / TEXTE)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Import Modal */}
      {isImportOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-swiss max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-swiss-neutral pb-3">
              <div className="flex items-center space-x-2">
                <Link2 className="w-4 h-4 text-swiss-blue" />
                <h3 className="text-sm font-bold font-sans text-swiss-black">
                  Importer une Offre Externe avec Gemini
                </h3>
              </div>
              <button
                onClick={() => setIsImportOpen(false)}
                className="text-swiss-muted hover:text-swiss-black text-xs font-mono"
              >
                ✕ Fermer
              </button>
            </div>

            <form onSubmit={handleImportSubmit} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-mono text-swiss-muted uppercase">
                  Lien de l'offre (LinkedIn, WTTJ, Thales, CEA, etc.)
                </label>
                <input
                  type="url"
                  value={importUrl}
                  onChange={(e) => setImportUrl(e.target.value)}
                  placeholder="https://www.welcometothejungle.com/fr/companies/..."
                  className="w-full px-3 py-2 text-xs font-mono border border-swiss-border rounded-swiss outline-none focus:border-swiss-blue"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-mono text-swiss-muted uppercase">
                  Ou collez directement le texte de l'annonce
                </label>
                <textarea
                  value={importText}
                  onChange={(e) => setImportText(e.target.value)}
                  rows={5}
                  placeholder="Collez ici les missions, compétences demandées et informations de l'entreprise..."
                  className="w-full px-3 py-2 text-xs font-sans border border-swiss-border rounded-swiss outline-none focus:border-swiss-blue resize-none"
                />
              </div>

              <div className="p-3 bg-swiss-neutral/40 rounded border border-swiss-border text-[11px] font-sans text-swiss-muted">
                Gemini extrait automatiquement le titre, les compétences requises, la culture d'équipe et génère les lettres ciblées.
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t border-swiss-neutral">
                <button
                  type="button"
                  onClick={() => setIsImportOpen(false)}
                  className="px-3 py-1.5 text-xs font-mono border border-swiss-border rounded-swiss hover:bg-swiss-neutral"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={importing || (!importUrl.trim() && !importText.trim())}
                  className="px-4 py-1.5 bg-swiss-blue hover:bg-swiss-blue-hover text-white text-xs font-mono font-semibold rounded-swiss transition-colors flex items-center space-x-1.5 disabled:opacity-50"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{importing ? "ANALYSE PAR GEMINI..." : "ANALYSER & RÉDIGER"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Results Count & Metrics & Sorting Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between text-xs font-mono text-swiss-muted px-1 gap-2">
        <div className="flex items-center space-x-2">
          <span>RÉSULTATS DE RECHERCHE // {sortedOffers.length} OPPORTUNITÉS IDENTIFIÉES</span>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <span className="hidden lg:inline-block">OUTILS EN DIRECT: JOBSPY (INDEED/LINKEDIN) + DDGS CARRIÈRES (WTTJ/APEC) + LABOS R&D</span>
          
          {/* Liveness Hide Toggle */}
          {expiredCount > 0 && (
            <button
              type="button"
              onClick={() => setHideExpired(!hideExpired)}
              className={`px-2.5 py-1 rounded text-[11px] font-mono transition-colors border flex items-center space-x-1 ${
                hideExpired
                  ? "bg-slate-900 text-white border-slate-900 font-semibold shadow-sm"
                  : "bg-white text-slate-700 border-slate-300 hover:bg-slate-100"
              }`}
            >
              <span>{hideExpired ? "✓ Clôturées masquées" : `Masquer clôturées (${expiredCount})`}</span>
            </button>
          )}

          <div className="flex items-center space-x-1 border border-swiss-border rounded p-0.5 bg-white shadow-sm">
            <span className="text-[11px] font-mono text-swiss-muted px-1.5 flex items-center space-x-1">
              <ArrowUpDown className="w-3 h-3 text-swiss-blue" />
              <span>TRI :</span>
            </span>
            <button
              type="button"
              onClick={() => setSortBy("novelty")}
              className={`px-2.5 py-0.5 rounded text-[11px] font-mono transition-colors ${
                sortBy === "novelty"
                  ? "bg-swiss-blue text-white font-semibold"
                  : "text-swiss-black hover:bg-swiss-neutral"
              }`}
            >
              Nouveauté (Plus récent)
            </button>
            <button
              type="button"
              onClick={() => setSortBy("match")}
              className={`px-2.5 py-0.5 rounded text-[11px] font-mono transition-colors ${
                sortBy === "match"
                  ? "bg-swiss-blue text-white font-semibold"
                  : "text-swiss-black hover:bg-swiss-neutral"
              }`}
            >
              Score ATS
            </button>
          </div>
        </div>
      </div>

      {/* Loading Feedback State */}
      {loading && (
        <div className="swiss-card p-8 text-center space-y-3 bg-white border border-swiss-blue">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-2 border-swiss-blue border-t-transparent" />
          <h3 className="text-sm font-bold font-sans text-swiss-black">
            Recherche multi-plateformes en temps réel (JobSpy, Indeed, LinkedIn, R&D)...
          </h3>
          <p className="text-xs font-mono text-swiss-muted">
            Indexation des opportunités pour « {query || "Tous domaines"} » {location ? `à ${location}` : "en France"}
          </p>
        </div>
      )}

      {/* Offers Asymmetric Grid */}
      {!loading && (
        <div className="space-y-4">
          {sortedOffers.length === 0 ? (
            <div className="swiss-card p-12 text-center space-y-3">
              <Search className="w-8 h-8 text-swiss-muted mx-auto" />
              <h3 className="text-sm font-bold font-sans text-swiss-black">
                Aucune offre ne correspond exactement à ces critères
              </h3>
              <p className="text-xs text-swiss-muted font-sans max-w-md mx-auto">
                Essayez d'élargir votre recherche avec un filtre plus général (ex: « Systèmes Embarqués » ou « Tous ») ou importez directement une offre externe avec le bouton ci-dessus.
              </p>
              <button
                type="button"
                onClick={() => handleFilterClick("Tous")}
                className="px-3 py-1.5 bg-swiss-blue text-white text-xs font-mono rounded-swiss hover:bg-swiss-blue-hover"
              >
                RÉINITIALISER LES FILTRES
              </button>
            </div>
          ) : (
            sortedOffers.map((job) => (
              <div
                key={job.id}
                className="swiss-card p-6 hover:shadow-swiss-hover transition-shadow border-l-4 border-l-swiss-blue"
              >
                <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
                  <div className="space-y-2 max-w-3xl">
                    <div className="flex flex-wrap items-center gap-2">
                      {isRecentOffer(job.date_posted) && (
                        <span className="px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-mono text-[10px] font-bold tracking-wider">
                          NOUVEAU
                        </span>
                      )}
                      <span className={`swiss-badge font-mono font-semibold ${
                        job.match_score >= 90
                          ? "bg-emerald-50 text-emerald-800 border border-emerald-300"
                          : "bg-blue-50 text-swiss-blue border border-blue-200"
                      }`}>
                        ● {job.match_score}% MATCH ATS
                      </span>
                      {job.is_active === false ? (
                        <span className="swiss-badge bg-rose-50 text-rose-800 border border-rose-300 font-mono text-[10px] font-bold">
                          ● CLÔTURÉE / 404
                        </span>
                      ) : (
                        <span className="swiss-badge bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono text-[10px]">
                          ● ACTIVE
                        </span>
                      )}
                      {job.source && (
                        <span className={`swiss-badge font-mono text-[10px] ${
                          job.source.includes("SimplifyJobs")
                            ? "bg-purple-50 text-purple-800 border border-purple-200"
                            : job.source.includes("European Tech")
                            ? "bg-blue-50 text-blue-800 border border-blue-200"
                            : job.source.includes("speedyapply")
                            ? "bg-amber-50 text-amber-800 border border-amber-200"
                            : "bg-slate-100 text-slate-800 border border-slate-300"
                        }`}>
                          {job.source}
                        </span>
                      )}
                      {job.salary && (
                        <span className="swiss-badge bg-emerald-50 text-emerald-900 border border-emerald-300 font-mono text-[10px] font-bold">
                          💰 {job.salary}
                        </span>
                      )}
                      {job.sponsorship && (
                        <span className="swiss-badge bg-slate-50 text-slate-700 border border-slate-300 font-mono text-[10px]">
                          VISA: {job.sponsorship}
                        </span>
                      )}
                      <span className="swiss-badge bg-swiss-neutral text-swiss-black">
                        {job.contract}
                      </span>
                      <span className="swiss-badge bg-blue-50 text-swiss-blue border border-blue-200">
                        {job.category}
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-swiss-black font-sans leading-snug">
                      {job.title}
                    </h3>

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs font-mono text-swiss-muted">
                      <span className="flex items-center space-x-1 font-semibold text-swiss-black">
                        <Building2 className="w-3.5 h-3.5 text-swiss-blue" />
                        <span>{job.company}</span>
                      </span>
                      <span className="flex items-center space-x-1">
                        <MapPin className="w-3.5 h-3.5 text-swiss-muted" />
                        <span>{job.location}</span>
                      </span>
                      <span className="flex items-center space-x-1 text-slate-700 font-medium">
                        <Calendar className="w-3.5 h-3.5 text-swiss-blue" />
                        <span>Publié le {formatDateFrench(job.date_posted)}</span>
                      </span>
                    </div>

                    <p className="text-sm text-swiss-black/80 font-sans leading-relaxed pt-1">
                      {job.description && job.description !== "nan"
                        ? job.description
                        : `Opportunité de stage conventionné chez ${job.company} à ${job.location}. Conception, analyse et développement technique sur les projets opérationnels de l'équipe.`}
                    </p>

                    {/* Resume-Matcher ATS Insights: Matched & Missing Skills */}
                    {(job.matched_skills && job.matched_skills.length > 0 || job.missing_skills && job.missing_skills.length > 0) && (
                      <div className="p-3 bg-white rounded border border-swiss-border space-y-1.5 mt-2">
                        {job.matched_skills && job.matched_skills.length > 0 && (
                          <div className="flex items-center gap-1.5 flex-wrap text-xs">
                            <span className="text-[11px] font-mono text-emerald-800 font-semibold shrink-0">
                              Compétences Validées (CV) :
                            </span>
                            {job.matched_skills.map((s) => (
                              <span
                                key={s}
                                className="px-1.5 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-900 font-mono text-[10px]"
                              >
                                {s}
                              </span>
                            ))}
                          </div>
                        )}
                        {job.missing_skills && job.missing_skills.length > 0 && (
                          <div className="flex items-center gap-1.5 flex-wrap text-xs">
                            <span className="text-[11px] font-mono text-amber-800 font-semibold shrink-0">
                              Points à Valoriser :
                            </span>
                            {job.missing_skills.map((s) => (
                              <span
                                key={s}
                                className="px-1.5 py-0.5 rounded bg-amber-50 border border-amber-200 text-amber-900 font-mono text-[10px]"
                              >
                                {s}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Recruiter Demand Analysis */}
                    <div className="p-3 bg-swiss-neutral/30 rounded border border-swiss-border text-xs space-y-1 mt-2">
                      <div className="flex items-center space-x-1.5 font-mono text-swiss-blue font-semibold">
                        <Layers className="w-3.5 h-3.5" />
                        <span>ANALYSE DE LA DEMANDE DU RECRUTEUR ({job.recruiter_type}) :</span>
                      </div>
                      <p className="text-swiss-black/75 font-sans italic">
                        {job.recruiter_profile}
                      </p>
                    </div>

                    {/* Tech Stack Badges */}
                    <div className="flex flex-wrap items-center gap-1.5 pt-2">
                      {job.tags.map((tag) => (
                        <span
                          key={tag}
                          className="text-[11px] font-mono px-2 py-0.5 bg-white border border-swiss-border rounded text-swiss-muted"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex lg:flex-col items-center lg:items-end justify-between gap-2 shrink-0 pt-2 lg:pt-0">
                    <button
                      onClick={() => onSelectForLetter(job)}
                      className="w-full lg:w-48 py-2.5 px-4 bg-swiss-blue hover:bg-swiss-blue-hover text-white text-xs font-mono font-semibold rounded-swiss transition-colors flex items-center justify-center space-x-1.5 shadow-sm"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>RÉDIGER LA LETTRE</span>
                    </button>

                    <a
                      href={
                        job.url && job.url !== "nan" && job.url.startsWith("http")
                          ? job.url
                          : `https://www.google.com/search?q=${encodeURIComponent(`Stage ${job.title} ${job.company} ${job.location}`)}`
                      }
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full lg:w-48 py-2 px-3 border border-swiss-border hover:bg-white text-swiss-muted hover:text-swiss-black text-xs font-mono rounded-swiss transition-colors flex items-center justify-center space-x-1.5"
                    >
                      <ExternalLink className="w-3 h-3" />
                      <span>VOIR L'OFFRE SOURCE</span>
                    </a>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

