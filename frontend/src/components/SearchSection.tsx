"use client";

import React, { useState } from "react";
import { JobOffer } from "@/types";
import { Search, MapPin, ExternalLink, Sparkles, Building2, Layers, CheckCircle2, Link2, PlusCircle, FileText } from "lucide-react";
import { importOffer } from "@/lib/api";

interface SearchSectionProps {
  offers: JobOffer[];
  loading: boolean;
  onSearch: (query: string, location: string) => void;
  onSelectForLetter: (job: JobOffer) => void;
  onAddCustomOffer?: (job: JobOffer) => void;
}

export const SearchSection: React.FC<SearchSectionProps> = ({
  offers,
  loading,
  onSearch,
  onSelectForLetter,
  onAddCustomOffer,
}) => {
  const [query, setQuery] = useState("Systèmes embarqués, Edge AI, Traitement du signal");
  const [location, setLocation] = useState("Paris, Île-de-France");

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

  const quickFilters = [
    "Tous",
    "Systèmes Embarqués",
    "Edge AI & TinyML",
    "Traitement du Signal",
    "Computer Vision",
    "FPGA & DSP",
  ];

  const handleFilterClick = (filter: string) => {
    if (filter === "Tous") {
      setQuery("");
      onSearch("", location);
    } else {
      setQuery(filter);
      onSearch(filter, location);
    }
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
            <label className="text-xs font-mono font-medium text-swiss-muted uppercase tracking-wider">
              Mots-clés & Spécialités
            </label>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-swiss-muted" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ex: Edge AI, C++, PyTorch, Radar, Vision, FPGA..."
                className="w-full pl-9 pr-4 py-2 text-sm bg-white border border-swiss-border rounded-swiss focus:border-swiss-blue focus:ring-1 focus:ring-swiss-blue outline-none"
              />
            </div>
          </div>

          <div className="md:col-span-4 space-y-1">
            <label className="text-xs font-mono font-medium text-swiss-muted uppercase tracking-wider">
              Localisation Cible
            </label>
            <div className="relative">
              <MapPin className="w-4 h-4 absolute left-3 top-3 text-swiss-muted" />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Ex: Paris, Saclay, Gennevilliers..."
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

        {/* Quick Filter Badges */}
        <div className="mt-4 pt-4 border-t border-swiss-neutral flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-mono text-swiss-muted mr-1">Filtres Rapides :</span>
            {quickFilters.map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => handleFilterClick(f)}
                className="px-2.5 py-1 text-xs font-mono bg-swiss-neutral/70 hover:bg-swiss-blue hover:text-white rounded text-swiss-black transition-colors"
              >
                {f}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={() => setIsImportOpen(true)}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-swiss-blue text-swiss-blue hover:bg-swiss-blue hover:text-white rounded-swiss text-xs font-mono font-medium transition-colors shadow-sm"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>IMPORTER UNE OFFRE (URL / TEXTE)</span>
          </button>
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

      {/* Results Count & Metrics */}
      <div className="flex items-center justify-between text-xs font-mono text-swiss-muted px-1">
        <span>RÉSULTATS DE RECHERCHE // {offers.length} OPPORTUNITÉS IDENTIFIÉES</span>
        <span>INDEXATION: TEMPS RÉEL (PARIS & ÎLE-DE-FRANCE)</span>
      </div>

      {/* Offers Asymmetric Grid */}
      <div className="space-y-4">
        {offers.map((job) => (
          <div
            key={job.id}
            className="swiss-card p-6 hover:shadow-swiss-hover transition-shadow border-l-4 border-l-swiss-blue"
          >
            <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
              <div className="space-y-2 max-w-3xl">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="swiss-badge bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold">
                    {job.match_score}% ADÉQUATION PROFIL
                  </span>
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

                <p className="text-sm text-swiss-black/80 font-sans leading-relaxed pt-1">
                  {job.description}
                </p>

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
                  href={job.url}
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
        ))}
      </div>
    </div>
  );
};

