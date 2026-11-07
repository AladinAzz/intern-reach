"use client";

import React from "react";
import { Search, FileText, Send, BookmarkCheck, Settings, Cpu } from "lucide-react";

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  openSettings: () => void;
  historyCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  openSettings,
  historyCount,
}) => {
  const tabs = [
    { id: "search", label: "01. RECHERCHE D'OFFRES", icon: Search },
    { id: "cv", label: "02. PROFIL & CV", icon: FileText },
    { id: "studio", label: "03. STUDIO DE LETTRES", icon: Send },
    { id: "history", label: `04. HISTORIQUE (${historyCount})`, icon: BookmarkCheck },
  ];

  return (
    <header className="bg-white border-b border-swiss-border sticky top-0 z-50 no-print">
      <div className="swiss-container">
        {/* Top Technical Metadata Bar */}
        <div className="flex items-center justify-between py-2 border-b border-swiss-neutral text-[11px] font-mono text-swiss-muted">
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1.5 text-swiss-black font-semibold">
              <Cpu className="w-3.5 h-3.5 text-swiss-blue" />
              <span>INTERN.REACH // SCIENTIFIC ENGINE</span>
            </span>
            <span className="hidden sm:inline-block">LOC: MULTI-SOURCES // FRANCE & INTERNATIONAL</span>
            <span className="hidden md:inline-block">DOMAINE: SYSTÈMES EMBARQUÉS & IA</span>
          </div>
          <div className="flex items-center space-x-3">
            <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
              ● AGENT-REACH ONLINE
            </span>
            <button
              onClick={openSettings}
              className="flex items-center space-x-1 hover:text-swiss-blue transition-colors px-2 py-0.5 rounded border border-swiss-border"
              title="Configurer les clés d'API (Gemini, Claude, OpenAI, Ollama)"
            >
              <Settings className="w-3 h-3" />
              <span>BYOK API</span>
            </button>
          </div>
        </div>

        {/* Main Navigation & Title */}
        <div className="flex flex-col md:flex-row md:items-center justify-between py-3 gap-3">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-swiss-black font-sans">
              Plateforme Scientifique de Recherche de Stage & Lettres Personnalisées
            </h1>
            <p className="text-xs text-swiss-muted font-sans mt-0.5">
              Traitement du signal, vision par ordinateur & IA embarquée — Alignement rigoureux aux exigences recruteurs
            </p>
          </div>

          {/* Swiss Navigation Tabs */}
          <nav className="flex items-center space-x-1 border border-swiss-border p-1 rounded-swiss bg-swiss-neutral/40 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-3 py-1.5 rounded-swiss text-xs font-mono transition-all whitespace-nowrap ${
                    isActive
                      ? "bg-swiss-blue text-white shadow-sm font-semibold"
                      : "text-swiss-black hover:bg-white hover:text-swiss-blue"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
};

