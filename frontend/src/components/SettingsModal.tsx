"use client";

import React, { useState } from "react";
import { AppSettings } from "@/types";
import { Settings, Check, Key, Server, Cpu, ShieldCheck } from "lucide-react";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: AppSettings;
  onSave: (updated: AppSettings) => Promise<void>;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onSave,
}) => {
  const [formData, setFormData] = useState<AppSettings>(settings);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
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

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
      <div className="bg-white rounded-swiss max-w-lg w-full p-6 shadow-2xl space-y-5">
        <div className="flex items-center justify-between border-b border-swiss-neutral pb-3">
          <div className="flex items-center space-x-2">
            <Settings className="w-4 h-4 text-swiss-blue" />
            <h3 className="text-sm font-bold font-sans text-swiss-black">
              Paramètres BYOK (Bring Your Own Key) & Moteur IA
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-swiss-muted hover:text-swiss-black text-xs font-mono"
          >
            ✕ Fermer
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-mono text-swiss-muted uppercase">
              Fournisseur d'IA Actif
            </label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { id: "gemini", label: "Google Gemini", sub: "Flash (Recommandé)" },
                { id: "openai", label: "OpenAI", sub: "GPT-4o" },
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
      </div>
    </div>
  );
};

