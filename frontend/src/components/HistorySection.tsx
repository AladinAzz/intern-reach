"use client";

import React, { useState } from "react";
import { HistoryEntry } from "@/types";
import { BookmarkCheck, ExternalLink, Copy, Check, Eye, Trash2, Building2 } from "lucide-react";

interface HistorySectionProps {
  history: HistoryEntry[];
  onUpdateStatus?: (id: string, newStatus: HistoryEntry["status"]) => void;
}

export const HistorySection: React.FC<HistorySectionProps> = ({ history }) => {
  const [selectedEntry, setSelectedEntry] = useState<HistoryEntry | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2500);
  };

  if (!history || history.length === 0) {
    return (
      <div className="swiss-card p-12 text-center space-y-3">
        <BookmarkCheck className="w-10 h-10 text-swiss-muted mx-auto" />
        <h3 className="text-base font-bold font-sans text-swiss-black">
          Aucune candidature enregistrée
        </h3>
        <p className="text-xs text-swiss-muted font-sans max-w-md mx-auto">
          Lorsque vous générez et ajustez une lettre de motivation dans le Studio, cliquez sur « Sauvegarder » pour l'archiver dans votre tableau de bord.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between text-xs font-mono text-swiss-muted px-1">
        <span>ARCHIVES DES CANDIDATURES // {history.length} ENTRÉES</span>
        <span>SUIVI CHRONOLOGIQUE</span>
      </div>

      <div className="swiss-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-swiss-border bg-swiss-neutral/50 text-[11px] font-mono text-swiss-muted uppercase">
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Entreprise & Poste</th>
                <th className="py-3 px-4">Localisation</th>
                <th className="py-3 px-4">Version Utilisée</th>
                <th className="py-3 px-4">Statut</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-swiss-neutral text-xs font-sans">
              {history.map((item) => (
                <tr key={item.id} className="hover:bg-swiss-neutral/20 transition-colors">
                  <td className="py-3 px-4 font-mono text-swiss-muted whitespace-nowrap">
                    {item.applied_at}
                  </td>
                  <td className="py-3 px-4 font-medium text-swiss-black">
                    <div className="font-bold flex items-center space-x-1.5">
                      <Building2 className="w-3.5 h-3.5 text-swiss-blue" />
                      <span>{item.company}</span>
                    </div>
                    <div className="text-xs text-swiss-muted mt-0.5">{item.job_title}</div>
                  </td>
                  <td className="py-3 px-4 text-swiss-muted whitespace-nowrap">
                    {item.location}
                  </td>
                  <td className="py-3 px-4 font-mono text-swiss-blue whitespace-nowrap">
                    {item.selected_version}
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className="swiss-badge bg-emerald-50 text-emerald-800 border border-emerald-200">
                      {item.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right whitespace-nowrap space-x-2">
                    <button
                      onClick={() => setSelectedEntry(item)}
                      className="px-2.5 py-1 text-xs font-mono bg-white border border-swiss-border rounded hover:bg-swiss-neutral text-swiss-black transition-colors inline-flex items-center space-x-1"
                    >
                      <Eye className="w-3 h-3 text-swiss-muted" />
                      <span>Voir la lettre</span>
                    </button>
                    <button
                      onClick={() => handleCopy(item.id, item.letter_content)}
                      className="px-2 py-1 text-xs font-mono bg-white border border-swiss-border rounded hover:bg-swiss-neutral text-swiss-black transition-colors inline-flex items-center space-x-1"
                      title="Copier le texte"
                    >
                      {copiedId === item.id ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3 text-swiss-muted" />}
                    </button>
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-2 py-1 text-xs font-mono bg-white border border-swiss-border rounded hover:bg-swiss-neutral text-swiss-muted hover:text-swiss-black transition-colors inline-flex items-center space-x-1"
                      title="Lien externe"
                    >
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal / Preview drawer for saved letter */}
      {selectedEntry && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-swiss max-w-2xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] flex flex-col">
            <div className="flex items-start justify-between border-b border-swiss-neutral pb-3">
              <div>
                <h3 className="text-sm font-bold font-sans text-swiss-black">
                  Lettre Enregistrée — {selectedEntry.company}
                </h3>
                <p className="text-xs text-swiss-muted font-mono mt-0.5">
                  {selectedEntry.job_title} | Version : {selectedEntry.selected_version}
                </p>
              </div>
              <button
                onClick={() => setSelectedEntry(null)}
                className="text-swiss-muted hover:text-swiss-black text-sm font-mono px-2 py-1"
              >
                ✕ Fermer
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 bg-swiss-neutral/30 rounded border border-swiss-border text-xs font-sans whitespace-pre-wrap leading-relaxed text-swiss-black">
              {selectedEntry.letter_content}
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t border-swiss-neutral">
              <button
                onClick={() => handleCopy(selectedEntry.id, selectedEntry.letter_content)}
                className="px-4 py-2 bg-swiss-blue hover:bg-swiss-blue-hover text-white text-xs font-mono font-semibold rounded-swiss transition-colors flex items-center space-x-1.5"
              >
                {copiedId === selectedEntry.id ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedId === selectedEntry.id ? "COPIÉ DANS LE PRESSE-PAPIER" : "COPIER LE TEXTE"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

