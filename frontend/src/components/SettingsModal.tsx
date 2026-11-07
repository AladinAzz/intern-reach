"use client";

import React, { useState, useEffect } from "react";
import { AppSettings, WorkerState, WorkerSettings, RegistrySource } from "@/types";
import {
  Settings,
  Check,
  Key,
  Server,
  Cpu,
  ShieldCheck,
  RefreshCw,
  Layers,
  Activity,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Clock,
  Database
} from "lucide-react";
import {
  getWorkerStatus,
  triggerWorkerSync,
  getWorkerSettings,
  saveWorkerSettings
} from "@/lib/api";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: AppSettings;
  onSave: (updated: AppSettings) => Promise<void>;
  onSyncCompleted?: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onSave,
  onSyncCompleted
}) => {
  const [activeTab, setActiveTab] = useState<"worker" | "ai">("worker");
  const [formData, setFormData] = useState<AppSettings>(settings);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  // Worker Supervision State
  const [workerState, setWorkerState] = useState<WorkerState | null>(null);
  const [workerSettings, setWorkerSettings] = useState<WorkerSettings | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setFormData(settings);
      loadWorkerInfo();
    }
  }, [isOpen, settings]);

  const loadWorkerInfo = async () => {
    try {
      const [st, cfg] = await Promise.all([
        getWorkerStatus(),
        getWorkerSettings()
      ]);
      setWorkerState(st);
      setWorkerSettings(cfg);
    } catch (err) {
      console.warn("Erreur chargement worker info:", err);
    }
  };

  const handleTriggerSync = async () => {
    setSyncing(true);
    setSyncMsg("Synchronisation multi-sources & vérification de liveness...");
    try {
      const res = await triggerWorkerSync();
      setWorkerState(res.state);
      setSyncMsg(res.message || "Synchronisation terminée avec succès.");
      if (onSyncCompleted) onSyncCompleted();
      setTimeout(() => setSyncMsg(null), 4000);
    } catch (err) {
      setSyncMsg("Erreur lors de la synchronisation.");
    } finally {
      setSyncing(false);
    }
  };

  const handleToggleSource = async (sourceId: string) => {
    if (!workerSettings) return;
    const updatedSources = workerSettings.sources.map((s) =>
      s.id === sourceId ? { ...s, enabled: !s.enabled } : s
    );
    const updated = { ...workerSettings, sources: updatedSources };
    setWorkerSettings(updated);
    await saveWorkerSettings(updated);
  };

  const handleSubmitAi = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave(formData);
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        onClose();
      }, 1000);
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-swiss max-w-2xl w-full p-6 shadow-2xl space-y-5 max-h-[92vh] flex flex-col border border-swiss-border">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-swiss-neutral pb-3">
          <div className="flex items-center space-x-2">
            <Settings className="w-4 h-4 text-swiss-blue" />
            <h3 className="text-base font-bold font-sans text-swiss-black">
              Panneau de Contrôle & Paramètres Système
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-swiss-muted hover:text-swiss-black text-xs font-mono px-2 py-1"
          >
            ✕ Fermer
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center space-x-1 border border-swiss-border p-1 rounded-swiss bg-swiss-neutral/40 text-xs font-mono">
          <button
            onClick={() => setActiveTab("worker")}
            className={`flex-1 py-1.5 px-3 rounded text-center transition-all flex items-center justify-center space-x-2 ${
              activeTab === "worker"
                ? "bg-white text-swiss-blue font-bold shadow-sm"
                : "text-swiss-muted hover:text-swiss-black"
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>MOTEUR D'INGESTION & WORKER AUTONOME</span>
          </button>
          <button
            onClick={() => setActiveTab("ai")}
            className={`flex-1 py-1.5 px-3 rounded text-center transition-all flex items-center justify-center space-x-2 ${
              activeTab === "ai"
                ? "bg-white text-swiss-blue font-bold shadow-sm"
                : "text-swiss-muted hover:text-swiss-black"
            }`}
          >
            <Key className="w-3.5 h-3.5" />
            <span>MODÈLES IA & CLÉS BYOK</span>
          </button>
        </div>

        {/* Tab 1: Worker & Ingestion Hub */}
        {activeTab === "worker" && (
          <div className="space-y-4 overflow-y-auto flex-1 pr-1 text-xs">
            {/* Live Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <div className="swiss-card p-3 bg-swiss-neutral/30">
                <span className="text-[10px] font-mono text-swiss-muted uppercase">Statut Worker</span>
                <div className="flex items-center space-x-1.5 mt-1 font-mono font-bold text-swiss-black">
                  <span className={`w-2 h-2 rounded-full ${syncing ? "bg-amber-500 animate-ping" : "bg-emerald-500"}`} />
                  <span>{syncing ? "SYNCHRO..." : "ACTIF // VEILLE"}</span>
                </div>
              </div>

              <div className="swiss-card p-3 bg-swiss-neutral/30">
                <span className="text-[10px] font-mono text-swiss-muted uppercase">Offres Indexées</span>
                <div className="text-base font-mono font-bold text-swiss-black mt-1">
                  {workerState ? workerState.total_jobs : "—"}
                </div>
              </div>

              <div className="swiss-card p-3 bg-emerald-50/50 border-emerald-200">
                <span className="text-[10px] font-mono text-emerald-700 uppercase">Actives (Liveness OK)</span>
                <div className="text-base font-mono font-bold text-emerald-800 mt-1">
                  {workerState ? workerState.active_jobs : "—"}
                </div>
              </div>

              <div className="swiss-card p-3 bg-slate-50 border-slate-200">
                <span className="text-[10px] font-mono text-slate-600 uppercase">Clôturées (404/Exp)</span>
                <div className="text-base font-mono font-bold text-slate-800 mt-1">
                  {workerState ? workerState.expired_jobs : "—"}
                </div>
              </div>
            </div>

            {/* Sync Now Action */}
            <div className="p-3.5 bg-blue-50/60 rounded border border-blue-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <div className="font-bold text-swiss-black flex items-center space-x-1.5 font-sans">
                  <RefreshCw className={`w-3.5 h-3.5 text-swiss-blue ${syncing ? "animate-spin" : ""}`} />
                  <span>Cycle de Synchronisation & Liveness Check</span>
                </div>
                <p className="text-[11px] text-swiss-muted font-sans mt-0.5">
                  Dernier scan : <span className="font-mono">{workerState?.last_sync || "Non exécuté"}</span>
                </p>
                {syncMsg && (
                  <p className="text-[11px] text-swiss-blue font-mono font-semibold mt-1">
                    ● {syncMsg}
                  </p>
                )}
              </div>

              <button
                type="button"
                onClick={handleTriggerSync}
                disabled={syncing}
                className="px-3 py-1.5 bg-swiss-blue hover:bg-swiss-blue-hover text-white text-xs font-mono font-semibold rounded-swiss transition-colors flex items-center space-x-1.5 whitespace-nowrap shadow-sm"
              >
                <RefreshCw className={`w-3 h-3 ${syncing ? "animate-spin" : ""}`} />
                <span>{syncing ? "ANALYSE EN COURS..." : "SYNCHRONISER MAINTENANT"}</span>
              </button>
            </div>

            {/* Configured Sources List */}
            <div className="space-y-2">
              <div className="flex items-center justify-between font-mono text-[11px] text-swiss-muted uppercase">
                <span>Outils de Recherche en Direct Disponibles</span>
                <span>État d'Activation</span>
              </div>

              <div className="space-y-2">
                {workerSettings?.sources?.map((src) => (
                  <div
                    key={src.id}
                    className="p-3 rounded border border-swiss-border bg-white flex items-center justify-between gap-3 hover:bg-swiss-neutral/20 transition-colors"
                  >
                    <div className="min-w-0">
                      <div className="font-bold font-mono text-xs text-swiss-black flex items-center space-x-1.5">
                        <Layers className="w-3.5 h-3.5 text-swiss-blue flex-shrink-0" />
                        <span className="truncate">{src.name}</span>
                      </div>
                      <p className="text-[11px] text-swiss-muted font-sans mt-0.5 line-clamp-1">
                        {src.description}
                      </p>
                      <a
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] text-swiss-blue font-mono hover:underline inline-flex items-center space-x-1 mt-1 truncate max-w-sm"
                      >
                        <span className="truncate">{src.url}</span>
                        <ExternalLink className="w-2.5 h-2.5 flex-shrink-0" />
                      </a>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleToggleSource(src.id)}
                      className={`px-3 py-1 text-xs font-mono font-semibold rounded transition-colors whitespace-nowrap ${
                        src.enabled
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                          : "bg-slate-100 text-slate-500 border border-slate-200"
                      }`}
                    >
                      {src.enabled ? "ACTIVÉ" : "DÉSACTIVÉ"}
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Frequency & Options */}
            <div className="p-3 bg-swiss-neutral/30 rounded border border-swiss-border space-y-2 text-xs font-sans">
              <div className="flex items-center justify-between">
                <span className="font-medium text-swiss-black">Périodicité du Worker en arrière-plan</span>
                <span className="font-mono text-swiss-blue font-semibold">Toutes les 6 heures</span>
              </div>
              <p className="text-[11px] text-swiss-muted leading-relaxed">
                Le worker interroge automatiquement les registres GitHub sans clé d'API, déduplique les offres contre le catalogue local et teste la liveness HTTP de chaque URL pour signaler les clôtures.
              </p>
            </div>
          </div>
        )}

        {/* Tab 2: AI BYOK Providers */}
        {activeTab === "ai" && (
          <form onSubmit={handleSubmitAi} className="space-y-4 overflow-y-auto flex-1 pr-1">
            <div className="space-y-1">
              <label className="text-xs font-mono text-swiss-muted uppercase">
                Fournisseur d'IA Actif
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: "gemini", label: "Google Gemini", sub: "Flash 3.5 Lite (Recommandé)" },
                  { id: "openai", label: "OpenAI", sub: "GPT-4o / Mini" },
                  { id: "claude", label: "Anthropic Claude", sub: "Claude 3.5 Sonnet" },
                  { id: "ollama", label: "Ollama Local", sub: "100% Hors-ligne / Privé" },
                ].map((p) => {
                  const isSelected = formData.active_provider === p.id;
                  return (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => setFormData({ ...formData, active_provider: p.id as any })}
                      className={`p-2.5 rounded border text-left transition-all ${
                        isSelected
                          ? "border-swiss-blue bg-blue-50/50 ring-1 ring-swiss-blue text-swiss-blue"
                          : "border-swiss-border bg-white text-swiss-black hover:bg-swiss-neutral/40"
                      }`}
                    >
                      <div className="text-xs font-mono font-bold">{p.label}</div>
                      <div className="text-[11px] font-sans text-swiss-muted">{p.sub}</div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Conditional API Key inputs */}
            {formData.active_provider === "gemini" && (
              <div className="space-y-1">
                <label className="text-xs font-mono text-swiss-muted uppercase flex items-center space-x-1">
                  <Key className="w-3 h-3 text-swiss-blue" />
                  <span>Clé d'API Google Gemini</span>
                </label>
                <input
                  type="password"
                  value={formData.gemini_api_key || ""}
                  onChange={(e) => setFormData({ ...formData, gemini_api_key: e.target.value })}
                  placeholder="AIzaSy..."
                  className="w-full px-3 py-2 text-xs font-mono border border-swiss-border rounded-swiss outline-none focus:border-swiss-blue"
                />
                <p className="text-[11px] text-swiss-muted font-sans">
                  Obtenez une clé gratuite sur aistudio.google.com pour des générations ultra-rapides.
                </p>
              </div>
            )}

            {formData.active_provider === "openai" && (
              <div className="space-y-1">
                <label className="text-xs font-mono text-swiss-muted uppercase flex items-center space-x-1">
                  <Key className="w-3 h-3 text-swiss-blue" />
                  <span>Clé d'API OpenAI</span>
                </label>
                <input
                  type="password"
                  value={formData.openai_api_key || ""}
                  onChange={(e) => setFormData({ ...formData, openai_api_key: e.target.value })}
                  placeholder="sk-..."
                  className="w-full px-3 py-2 text-xs font-mono border border-swiss-border rounded-swiss outline-none focus:border-swiss-blue"
                />
              </div>
            )}

            {formData.active_provider === "claude" && (
              <div className="space-y-1">
                <label className="text-xs font-mono text-swiss-muted uppercase flex items-center space-x-1">
                  <Key className="w-3 h-3 text-swiss-blue" />
                  <span>Clé d'API Anthropic Claude</span>
                </label>
                <input
                  type="password"
                  value={formData.claude_api_key || ""}
                  onChange={(e) => setFormData({ ...formData, claude_api_key: e.target.value })}
                  placeholder="sk-ant-..."
                  className="w-full px-3 py-2 text-xs font-mono border border-swiss-border rounded-swiss outline-none focus:border-swiss-blue"
                />
              </div>
            )}

            {formData.active_provider === "ollama" && (
              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-mono text-swiss-muted uppercase flex items-center space-x-1">
                    <Server className="w-3 h-3 text-swiss-blue" />
                    <span>URL Serveur Ollama</span>
                  </label>
                  <input
                    type="text"
                    value={formData.ollama_base_url}
                    onChange={(e) => setFormData({ ...formData, ollama_base_url: e.target.value })}
                    placeholder="http://localhost:11434"
                    className="w-full px-3 py-2 text-xs font-mono border border-swiss-border rounded-swiss outline-none focus:border-swiss-blue"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-mono text-swiss-muted uppercase flex items-center space-x-1">
                    <Cpu className="w-3 h-3 text-swiss-blue" />
                    <span>Modèle Ollama</span>
                  </label>
                  <input
                    type="text"
                    value={formData.ollama_model}
                    onChange={(e) => setFormData({ ...formData, ollama_model: e.target.value })}
                    placeholder="llama3:latest, mistral:latest..."
                    className="w-full px-3 py-2 text-xs font-mono border border-swiss-border rounded-swiss outline-none focus:border-swiss-blue"
                  />
                </div>
              </div>
            )}

            <div className="p-3 bg-swiss-neutral/40 rounded border border-swiss-border text-[11px] font-sans text-swiss-muted flex items-start space-x-2">
              <ShieldCheck className="w-4 h-4 text-swiss-blue shrink-0 mt-0.5" />
              <span>
                Vos clés d'API restent confidentielles et stockées uniquement sur votre machine locale dans <code>backend/app/data/settings.json</code>.
              </span>
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t border-swiss-neutral">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-1.5 text-xs font-mono border border-swiss-border rounded-swiss hover:bg-swiss-neutral"
              >
                Annuler
              </button>
              <button
                type="submit"
                disabled={saving}
                className="px-4 py-1.5 bg-swiss-blue hover:bg-swiss-blue-hover text-white text-xs font-mono font-semibold rounded-swiss transition-colors flex items-center space-x-1.5"
              >
                {success ? <Check className="w-3.5 h-3.5" /> : null}
                <span>{saving ? "ENREGISTREMENT..." : success ? "ENREGISTRÉ !" : "VALIDER"}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
