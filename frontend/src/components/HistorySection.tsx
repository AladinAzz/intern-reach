"use client";

import React, { useState, useMemo } from "react";
import { HistoryEntry } from "@/types";
import {
  BookmarkCheck,
  ExternalLink,
  Copy,
  Check,
  Eye,
  Trash2,
  Building2,
  Printer,
  Search,
  Filter,
  CheckCircle2,
  Calendar,
  Layers,
  Sparkles,
} from "lucide-react";

interface HistorySectionProps {
  history: HistoryEntry[];
  onUpdateStatus?: (id: string, newStatus: HistoryEntry["status"]) => void;
  onDeleteEntry?: (id: string) => void;
}

const STATUS_CONFIG: Record<
  HistoryEntry["status"],
  { label: string; badge: string; dot: string }
> = {
  Enregistré: {
    label: "Enregistré",
    badge: "bg-slate-100 text-slate-800 border-slate-300",
    dot: "bg-slate-400",
  },
  Candidaté: {
    label: "Candidaté",
    badge: "bg-blue-50 text-blue-800 border-blue-200",
    dot: "bg-blue-500",
  },
  Entretien: {
    label: "Entretien",
    badge: "bg-amber-50 text-amber-800 border-amber-300",
    dot: "bg-amber-500",
  },
  Accepté: {
    label: "Accepté",
    badge: "bg-emerald-50 text-emerald-800 border-emerald-300",
    dot: "bg-emerald-500",
  },
  Refusé: {
    label: "Refusé",
    badge: "bg-rose-50 text-rose-800 border-rose-300",
    dot: "bg-rose-500",
  },
};

const ALL_STATUSES: HistoryEntry["status"][] = [
  "Enregistré",
  "Candidaté",
  "Entretien",
  "Accepté",
  "Refusé",
];

export const HistorySection: React.FC<HistorySectionProps> = ({
  history,
  onUpdateStatus,
  onDeleteEntry,
}) => {
  const [selectedEntry, setSelectedEntry] = useState<HistoryEntry | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const handleCopy = (id: string, text: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2500);
  };

  const handlePrintModal = () => {
    window.print();
  };

  // Safe external URL resolver
  const getSafeUrl = (url?: string, queryHint?: string) => {
    if (url && url !== "nan" && url.startsWith("http")) return url;
    return `https://www.google.com/search?q=${encodeURIComponent(
      queryHint || "stage systemes embarques"
    )}`;
  };

  // KPI Calculations
  const stats = useMemo(() => {
    const total = history.length;
    const registered = history.filter((h) => h.status === "Enregistré").length;
    const applied = history.filter((h) => h.status === "Candidaté").length;
    const interviews = history.filter((h) => h.status === "Entretien").length;
    const accepted = history.filter((h) => h.status === "Accepté").length;
    return { total, registered, applied, interviews, accepted };
  }, [history]);

  // Filtered entries
  const filteredHistory = useMemo(() => {
    return history.filter((item) => {
      const matchesStatus =
        statusFilter === "ALL" || item.status === statusFilter;
      const q = searchQuery.toLowerCase().trim();
      const matchesQuery =
        !q ||
        (item.company || "").toLowerCase().includes(q) ||
        (item.job_title || "").toLowerCase().includes(q) ||
        (item.location || "").toLowerCase().includes(q);
      return matchesStatus && matchesQuery;
    });
  }, [history, statusFilter, searchQuery]);

  if (!history || history.length === 0) {
    return (
      <div className="swiss-card p-12 text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-swiss-neutral flex items-center justify-center mx-auto text-swiss-muted">
          <BookmarkCheck className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold font-sans text-swiss-black">
          Aucune candidature enregistrée
        </h3>
        <p className="text-xs text-swiss-muted font-sans max-w-md mx-auto leading-relaxed">
          Lorsque vous rédigez ou ajustez une lettre dans le <strong>Studio</strong>, cliquez sur « Sauvegarder dans le suivi » pour archiver l'offre, son statut et le contenu complet de votre lettre.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Technical Metadata Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs font-mono text-swiss-muted px-1">
        <span className="flex items-center space-x-1.5">
          <Layers className="w-3.5 h-3.5 text-swiss-blue" />
          <span>ARCHIVES DES CANDIDATURES // SUIVI CENTRALISÉ</span>
        </span>
        <span>{history.length} CANDIDATURE{history.length > 1 ? "S" : ""} AU TOTAL</span>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="swiss-card p-3 flex flex-col justify-between">
          <span className="text-[10px] font-mono text-swiss-muted uppercase">Total Candidatures</span>
          <span className="text-xl font-bold font-mono text-swiss-black mt-1">{stats.total}</span>
        </div>
        <div className="swiss-card p-3 flex flex-col justify-between border-l-2 border-l-slate-400">
          <span className="text-[10px] font-mono text-slate-600 uppercase">Enregistrées</span>
          <span className="text-xl font-bold font-mono text-slate-800 mt-1">{stats.registered}</span>
        </div>
        <div className="swiss-card p-3 flex flex-col justify-between border-l-2 border-l-blue-500">
          <span className="text-[10px] font-mono text-blue-600 uppercase">Envoyées</span>
          <span className="text-xl font-bold font-mono text-blue-700 mt-1">{stats.applied}</span>
        </div>
        <div className="swiss-card p-3 flex flex-col justify-between border-l-2 border-l-amber-500">
          <span className="text-[10px] font-mono text-amber-600 uppercase">Entretiens</span>
          <span className="text-xl font-bold font-mono text-amber-700 mt-1">{stats.interviews}</span>
        </div>
        <div className="swiss-card p-3 flex flex-col justify-between border-l-2 border-l-emerald-500">
          <span className="text-[10px] font-mono text-emerald-600 uppercase">Offres Acceptées</span>
          <span className="text-xl font-bold font-mono text-emerald-700 mt-1">{stats.accepted}</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="swiss-card p-4 space-y-3">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          {/* Status Pills */}
          <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 md:pb-0 text-xs font-mono">
            <button
              onClick={() => setStatusFilter("ALL")}
              className={`px-3 py-1 rounded-swiss transition-colors whitespace-nowrap ${
                statusFilter === "ALL"
                  ? "bg-swiss-black text-white font-semibold"
                  : "bg-swiss-neutral text-swiss-muted hover:text-swiss-black"
              }`}
            >
              TOUS ({history.length})
            </button>
            {ALL_STATUSES.map((st) => {
              const count = history.filter((h) => h.status === st).length;
              const isActive = statusFilter === st;
              return (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2.5 py-1 rounded-swiss transition-colors whitespace-nowrap flex items-center space-x-1 ${
                    isActive
                      ? "bg-swiss-blue text-white font-semibold"
                      : "bg-swiss-neutral text-swiss-muted hover:text-swiss-black"
                  }`}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      STATUS_CONFIG[st]?.dot || "bg-slate-400"
                    }`}
                  />
                  <span>{st}</span>
                  <span className="text-[10px] opacity-75">({count})</span>
                </button>
              );
            })}
          </div>

          {/* Quick Search Input */}
          <div className="relative min-w-[220px]">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-swiss-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filtrer (entreprise, poste)..."
              className="w-full pl-8 pr-3 py-1.5 text-xs font-sans bg-swiss-neutral/50 border border-swiss-border rounded-swiss focus:outline-none focus:border-swiss-blue"
            />
          </div>
        </div>
      </div>

      {/* Table Card */}
      <div className="swiss-card overflow-hidden">
        {filteredHistory.length === 0 ? (
          <div className="p-8 text-center text-xs text-swiss-muted font-sans">
            Aucune candidature ne correspond à votre filtre actuel.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-swiss-border bg-swiss-neutral/60 text-[11px] font-mono text-swiss-muted uppercase">
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Entreprise & Intitulé</th>
                  <th className="py-3 px-4">Localisation</th>
                  <th className="py-3 px-4">Version</th>
                  <th className="py-3 px-4">Statut d'Avancement</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-swiss-neutral text-xs font-sans">
                {filteredHistory.map((item, idx) => {
                  const statusConf = STATUS_CONFIG[item.status] || STATUS_CONFIG["Enregistré"];
                  const isConfirmingDelete = confirmDeleteId === item.id;
                  const rowKey = `${item.id || "item"}-${idx}`;

                  return (
                    <tr
                      key={rowKey}
                      className="hover:bg-swiss-neutral/30 transition-colors"
                    >
                      {/* Date */}
                      <td className="py-3.5 px-4 font-mono text-swiss-muted whitespace-nowrap">
                        <span className="flex items-center space-x-1">
                          <Calendar className="w-3 h-3 text-swiss-muted" />
                          <span>{item.applied_at || "Récemment"}</span>
                        </span>
                      </td>

                      {/* Company & Job */}
                      <td className="py-3.5 px-4 font-medium text-swiss-black min-w-[200px]">
                        <div className="font-bold flex items-center space-x-1.5">
                          <Building2 className="w-3.5 h-3.5 text-swiss-blue flex-shrink-0" />
                          <span className="truncate">{item.company || "Entreprise"}</span>
                        </div>
                        <div className="text-xs text-swiss-muted mt-0.5 font-normal truncate max-w-sm">
                          {item.job_title || "Stage Ingénieur"}
                        </div>
                      </td>

                      {/* Location */}
                      <td className="py-3.5 px-4 text-swiss-muted whitespace-nowrap">
                        {item.location || "France"}
                      </td>

                      {/* Selected Version */}
                      <td className="py-3.5 px-4 font-mono text-swiss-blue whitespace-nowrap">
                        <span className="px-1.5 py-0.5 rounded bg-blue-50 border border-blue-200 text-[11px]">
                          {item.selected_version || "Standard"}
                        </span>
                      </td>

                      {/* Interactive Status Selector */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="relative inline-block">
                          <select
                            value={item.status}
                            onChange={(e) => {
                              const newStatus = e.target.value as HistoryEntry["status"];
                              if (onUpdateStatus) {
                                onUpdateStatus(item.id, newStatus);
                              }
                            }}
                            className={`text-[11px] font-mono font-semibold py-1 px-2.5 rounded-swiss border cursor-pointer focus:outline-none appearance-none pr-6 ${statusConf.badge}`}
                            style={{
                              backgroundImage: `url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%230047AB%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E")`,
                              backgroundRepeat: "no-repeat",
                              backgroundPosition: "right 6px top 50%",
                              backgroundSize: "7px auto",
                            }}
                          >
                            {ALL_STATUSES.map((st) => (
                              <option key={st} value={st}>
                                {st}
                              </option>
                            ))}
                          </select>
                        </div>
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right whitespace-nowrap space-x-1.5">
                        <button
                          onClick={() => setSelectedEntry(item)}
                          className="px-2.5 py-1 text-xs font-mono bg-white border border-swiss-border rounded-swiss hover:bg-swiss-neutral text-swiss-black transition-colors inline-flex items-center space-x-1"
                          title="Consulter la lettre enregistrée"
                        >
                          <Eye className="w-3 h-3 text-swiss-muted" />
                          <span>Voir</span>
                        </button>

                        <button
                          onClick={() => handleCopy(item.id, item.letter_content)}
                          className="px-2 py-1 text-xs font-mono bg-white border border-swiss-border rounded-swiss hover:bg-swiss-neutral text-swiss-black transition-colors inline-flex items-center space-x-1"
                          title="Copier la lettre dans le presse-papier"
                        >
                          {copiedId === item.id ? (
                            <Check className="w-3 h-3 text-emerald-600" />
                          ) : (
                            <Copy className="w-3 h-3 text-swiss-muted" />
                          )}
                        </button>

                        <a
                          href={getSafeUrl(item.url, `${item.job_title} ${item.company}`)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-2 py-1 text-xs font-mono bg-white border border-swiss-border rounded-swiss hover:bg-swiss-neutral text-swiss-muted hover:text-swiss-blue transition-colors inline-flex items-center space-x-1"
                          title="Accéder à l'offre ou fiche source"
                        >
                          <ExternalLink className="w-3 h-3" />
                        </a>

                        {/* Delete with confirmation */}
                        {isConfirmingDelete ? (
                          <span className="inline-flex items-center space-x-1">
                            <button
                              onClick={() => {
                                if (onDeleteEntry) onDeleteEntry(item.id);
                                setConfirmDeleteId(null);
                              }}
                              className="px-2 py-1 text-[11px] font-mono bg-rose-600 text-white rounded-swiss hover:bg-rose-700 transition-colors"
                            >
                              Confirmer
                            </button>
                            <button
                              onClick={() => setConfirmDeleteId(null)}
                              className="px-1.5 py-1 text-[11px] font-mono text-swiss-muted hover:text-swiss-black"
                            >
                              ✕
                            </button>
                          </span>
                        ) : (
                          <button
                            onClick={() => setConfirmDeleteId(item.id)}
                            className="px-2 py-1 text-xs font-mono bg-white border border-swiss-border rounded-swiss hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 text-swiss-muted transition-colors inline-flex items-center"
                            title="Supprimer cette candidature"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal / Preview drawer for saved letter */}
      {selectedEntry && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-swiss max-w-3xl w-full p-6 shadow-2xl space-y-4 max-h-[92vh] flex flex-col border border-swiss-border">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-swiss-neutral pb-4">
              <div>
                <div className="flex items-center space-x-2">
                  <Building2 className="w-4 h-4 text-swiss-blue" />
                  <h3 className="text-base font-bold font-sans text-swiss-black">
                    {selectedEntry.company}
                  </h3>
                  <span
                    className={`text-[10px] font-mono font-semibold py-0.5 px-2 rounded-swiss border ${
                      STATUS_CONFIG[selectedEntry.status]?.badge || ""
                    }`}
                  >
                    {selectedEntry.status}
                  </span>
                </div>
                <p className="text-xs text-swiss-muted font-sans mt-1">
                  {selectedEntry.job_title} &bull; <span className="font-mono text-swiss-blue">Version {selectedEntry.selected_version}</span> &bull; Enregistré le {selectedEntry.applied_at}
                </p>
              </div>

              <button
                onClick={() => setSelectedEntry(null)}
                className="text-swiss-muted hover:text-swiss-black text-sm font-mono px-2 py-1 rounded hover:bg-swiss-neutral"
              >
                ✕ Fermer
              </button>
            </div>

            {/* Letter Content */}
            <div className="flex-1 overflow-y-auto p-5 bg-swiss-neutral/30 rounded border border-swiss-border text-xs font-sans whitespace-pre-wrap leading-relaxed text-swiss-black font-normal selection:bg-blue-100">
              {selectedEntry.letter_content || "Aucun contenu enregistré pour cette lettre."}
            </div>

            {/* Modal Footer Controls */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-3 border-t border-swiss-neutral">
              <div className="flex items-center space-x-2 text-xs font-mono">
                <span className="text-swiss-muted">Changer statut :</span>
                <select
                  value={selectedEntry.status}
                  onChange={(e) => {
                    const newStatus = e.target.value as HistoryEntry["status"];
                    if (onUpdateStatus) {
                      onUpdateStatus(selectedEntry.id, newStatus);
                    }
                    setSelectedEntry((prev) => prev ? { ...prev, status: newStatus } : null);
                  }}
                  className="text-xs font-mono py-1 px-2 border border-swiss-border rounded-swiss bg-white focus:outline-none"
                >
                  {ALL_STATUSES.map((st) => (
                    <option key={st} value={st}>
                      {st}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={handlePrintModal}
                  className="px-3 py-1.5 bg-white border border-swiss-border hover:bg-swiss-neutral text-swiss-black text-xs font-mono rounded-swiss transition-colors inline-flex items-center space-x-1.5"
                  title="Imprimer ou exporter en PDF"
                >
                  <Printer className="w-3.5 h-3.5 text-swiss-muted" />
                  <span>IMPRIMER / PDF</span>
                </button>

                <button
                  onClick={() => handleCopy(selectedEntry.id, selectedEntry.letter_content)}
                  className="px-4 py-1.5 bg-swiss-blue hover:bg-swiss-blue-hover text-white text-xs font-mono font-semibold rounded-swiss transition-colors flex items-center space-x-1.5"
                >
                  {copiedId === selectedEntry.id ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-300" />
                      <span>COPIÉ DANS LE PRESSE-PAPIER</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>COPIER LE TEXTE</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
