"use client";

import React, { useState } from "react";
import { UserProfile } from "@/types";
import { UploadCloud, CheckCircle2, AlertCircle, Plus, Trash2, Save, FileText, Code2, GraduationCap, Compass } from "lucide-react";

interface CvSectionProps {
  profile: UserProfile;
  onUpdateProfile: (updated: UserProfile) => void;
  onUploadFile: (file: File) => Promise<void>;
  uploading: boolean;
}

export const CvSection: React.FC<CvSectionProps> = ({
  profile,
  onUpdateProfile,
  onUploadFile,
  uploading,
}) => {
  const [formData, setFormData] = useState<UserProfile>(profile);
  const [newSkill, setNewSkill] = useState("");
  const [newDomain, setNewDomain] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  // Synchronize internal form state whenever profile prop updates (e.g. after CV upload)
  React.useEffect(() => {
    if (profile) {
      setFormData(profile);
    }
  }, [profile]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setFileName(file.name);
    setUploadError(null);
    setUploadSuccess(false);
    try {
      await onUploadFile(file);
      setUploadSuccess(true);
      setTimeout(() => setUploadSuccess(false), 6000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erreur lors de l'analyse du CV.";
      setUploadError(msg);
    }
  };

  const handleAddDomain = () => {
    const clean = newDomain.trim();
    if (clean && !formData.target_domains.includes(clean)) {
      setFormData({
        ...formData,
        target_domains: [...formData.target_domains, clean],
      });
      setNewDomain("");
    }
  };

  const handleRemoveDomain = (domainToRemove: string) => {
    setFormData({
      ...formData,
      target_domains: formData.target_domains.filter((d) => d !== domainToRemove),
    });
  };

  const handleAddSkill = () => {
    const clean = newSkill.trim();
    if (clean && !formData.technical_skills.includes(clean)) {
      setFormData({
        ...formData,
        technical_skills: [...formData.technical_skills, clean],
      });
      setNewSkill("");
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setFormData({
      ...formData,
      technical_skills: formData.technical_skills.filter((s) => s !== skillToRemove),
    });
  };

  const handleAddProject = () => {
    setFormData({
      ...formData,
      key_projects: [...formData.key_projects, { title: "", desc: "" }],
    });
  };

  const handleRemoveProject = (index: number) => {
    setFormData({
      ...formData,
      key_projects: formData.key_projects.filter((_, idx) => idx !== index),
    });
  };

  const handleSave = () => {
    onUpdateProfile(formData);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Upload Banner */}
      <div className="swiss-card p-6 border-dashed border-2 border-swiss-border bg-white text-center">
        <UploadCloud className="w-8 h-8 text-swiss-blue mx-auto mb-2" />
        <h3 className="text-sm font-bold font-sans text-swiss-black">
          Téléverser votre CV (PDF ou Texte)
        </h3>
        <p className="text-xs text-swiss-muted font-sans mt-1 max-w-lg mx-auto">
          L&apos;agent extrait automatiquement vos spécialités cibles, vos compétences techniques, votre formation et vos projets scientifiques.
        </p>
        <div className="mt-4 flex flex-col items-center gap-2">
          <label className={`inline-flex items-center space-x-2 px-4 py-2 ${uploading ? "bg-slate-400 cursor-not-allowed" : "bg-swiss-blue hover:bg-swiss-blue-hover cursor-pointer"} text-white text-xs font-mono font-semibold rounded-swiss transition-colors shadow-sm`}>
            {uploading && <div className="inline-block animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent mr-1" />}
            <span>{uploading ? "EXTRACTION DU CV PAR L'IA EN COURS..." : "SÉLECTIONNER UN FICHIER PDF OU TEXTE"}</span>
            <input
              type="file"
              accept=".pdf,.txt,.md"
              onChange={handleFileChange}
              disabled={uploading}
              className="hidden"
            />
          </label>

          {uploadSuccess && (
            <div className="inline-flex items-center space-x-1.5 px-3 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded font-mono text-xs mt-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>{fileName || "CV"} analysé avec succès ! Profil et compétences actualisés.</span>
            </div>
          )}

          {uploadError && (
            <div data-testid="cv-upload-error" role="alert" className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-rose-50 text-rose-800 border border-rose-200 rounded font-mono text-xs mt-1">
              <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}
        </div>
      </div>

      {/* Editable Structured Profile */}
      <div className="swiss-card p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-swiss-neutral pb-4">
          <div>
            <h2 className="text-base font-bold font-sans text-swiss-black flex items-center space-x-2">
              <GraduationCap className="w-4 h-4 text-swiss-blue" />
              <span>Profil Candidat & Compétences Scientifiques</span>
            </h2>
            <p className="text-xs text-swiss-muted font-sans mt-0.5">
              Ces données pilotent vos requêtes de recherche et servent de socle objectif pour chaque lettre de motivation.
            </p>
          </div>
          <button
            onClick={handleSave}
            className="flex items-center space-x-1.5 px-4 py-2 bg-swiss-blue hover:bg-swiss-blue-hover text-white text-xs font-mono font-semibold rounded-swiss transition-colors shadow-sm"
          >
            <Save className="w-3.5 h-3.5" />
            <span>ENREGISTRER LE PROFIL</span>
          </button>
        </div>

        {saveSuccess && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-mono flex items-center space-x-2 rounded">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>Profil sauvegardé avec succès dans le stockage local !</span>
          </div>
        )}

        {/* Identity & Education */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-mono text-swiss-muted uppercase">Nom & Prénom</label>
            <input
              type="text"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-swiss-border rounded-swiss outline-none focus:border-swiss-blue font-sans"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-mono text-swiss-muted uppercase">Email de Contact</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-swiss-border rounded-swiss outline-none focus:border-swiss-blue font-sans"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-mono text-swiss-muted uppercase">Téléphone</label>
            <input
              type="text"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-swiss-border rounded-swiss outline-none focus:border-swiss-blue font-sans"
            />
          </div>
          <div className="md:col-span-3 space-y-1">
            <label className="text-xs font-mono text-swiss-muted uppercase">Formation & Spécialité</label>
            <input
              type="text"
              value={formData.education}
              onChange={(e) => setFormData({ ...formData, education: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-swiss-border rounded-swiss outline-none focus:border-swiss-blue font-sans"
            />
          </div>
        </div>

        {/* Target Domains Tag Manager */}
        <div className="space-y-3 pt-4 border-t border-swiss-neutral">
          <div className="flex items-center justify-between">
            <label className="text-xs font-mono text-swiss-muted uppercase flex items-center space-x-1.5">
              <Compass className="w-3.5 h-3.5 text-swiss-blue" />
              <span>Spécialités & Domaines Cibles ({formData.target_domains.length})</span>
            </label>
          </div>

          <div className="flex flex-wrap gap-2">
            {formData.target_domains.map((domain) => (
              <span
                key={domain}
                className="inline-flex items-center space-x-1 text-xs font-mono bg-blue-50 px-2.5 py-1 rounded border border-blue-200 text-swiss-blue"
              >
                <span>{domain}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveDomain(domain)}
                  className="text-swiss-muted hover:text-red-700 ml-1"
                  aria-label={`Supprimer le domaine ${domain}`}
                >
                  ×
                </button>
              </span>
            ))}
          </div>

          <div className="flex items-center space-x-2 pt-1 max-w-md">
            <input
              type="text"
              value={newDomain}
              onChange={(e) => setNewDomain(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleAddDomain();
                }
              }}
              placeholder="Ajouter une spécialité cible (ex: Edge AI, Robotique)..."
              className="flex-1 px-3 py-1.5 text-xs border border-swiss-border rounded-swiss outline-none focus:border-swiss-blue font-sans"
            />
            <button
              type="button"
              onClick={handleAddDomain}
              className="px-3 py-1.5 bg-swiss-neutral hover:bg-swiss-blue hover:text-white text-xs font-mono font-medium rounded-swiss border border-swiss-border transition-colors flex items-center space-x-1"
            >
              <Plus className="w-3 h-3" />
              <span>Ajouter</span>
            </button>
          </div>
        </div>

        {/* Technical Skills Tag Manager */}
        <div className="space-y-3 pt-4 border-t border-swiss-neutral">
          <div className="flex items-center justify-between">
            <label className="text-xs font-mono text-swiss-muted uppercase flex items-center space-x-1.5">
              <Code2 className="w-3.5 h-3.5 text-swiss-blue" />
              <span>Compétences & Outils Techniques ({formData.technical_skills.length})</span>
            </label>
          </div>

          <div className="flex flex-wrap gap-2">
            {formData.technical_skills.map((skill) => (
              <span
                key={skill}
                className="inline-flex items-center space-x-1 text-xs font-mono bg-swiss-neutral px-2.5 py-1 rounded border border-swiss-border text-swiss-black"
              >
                <span>{skill}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveSkill(skill)}
                  className="text-swiss-muted hover:text-red-700 ml-1"
                  aria-label={`Supprimer la compétence ${skill}`}
                >
                  ×
                </button>
              </span>
            ))}
          </div>

          <div className="flex items-center space-x-2 pt-1 max-w-md">
            <input
              type="text"
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleAddSkill();
                }
              }}
              placeholder="Ajouter une compétence (ex: CUDA, FreeRTOS)..."
              className="flex-1 px-3 py-1.5 text-xs border border-swiss-border rounded-swiss outline-none focus:border-swiss-blue font-sans"
            />
            <button
              type="button"
              onClick={handleAddSkill}
              className="px-3 py-1.5 bg-swiss-neutral hover:bg-swiss-blue hover:text-white text-xs font-mono font-medium rounded-swiss border border-swiss-border transition-colors flex items-center space-x-1"
            >
              <Plus className="w-3 h-3" />
              <span>Ajouter</span>
            </button>
          </div>
        </div>

        {/* Key Projects */}
        <div className="space-y-3 pt-4 border-t border-swiss-neutral">
          <div className="flex items-center justify-between">
            <label className="text-xs font-mono text-swiss-muted uppercase flex items-center space-x-1.5">
              <FileText className="w-3.5 h-3.5 text-swiss-blue" />
              <span>Projets Clés Réalisés ({formData.key_projects.length})</span>
            </label>
            <button
              type="button"
              onClick={handleAddProject}
              className="px-2.5 py-1 bg-swiss-neutral hover:bg-swiss-blue hover:text-white text-xs font-mono font-medium rounded-swiss border border-swiss-border transition-colors flex items-center space-x-1"
            >
              <Plus className="w-3 h-3" />
              <span>Ajouter un projet</span>
            </button>
          </div>

          <div className="space-y-3">
            {formData.key_projects.map((proj, idx) => (
              <div key={idx} className="p-3 bg-swiss-neutral/30 border border-swiss-border rounded space-y-1.5">
                <div className="flex items-center justify-between gap-2">
                  <input
                    type="text"
                    value={proj.title}
                    onChange={(e) => {
                      const updated = formData.key_projects.map((item, i) =>
                        i === idx ? { ...item, title: e.target.value } : item
                      );
                      setFormData({ ...formData, key_projects: updated });
                    }}
                    className="flex-1 text-xs font-bold font-sans text-swiss-black bg-transparent border-b border-swiss-border/60 pb-1 outline-none focus:border-swiss-blue"
                    placeholder="Titre du projet..."
                  />
                  <button
                    type="button"
                    onClick={() => handleRemoveProject(idx)}
                    className="text-swiss-muted hover:text-rose-600 p-1"
                    title="Supprimer ce projet"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                <textarea
                  value={proj.desc}
                  rows={2}
                  onChange={(e) => {
                    const updated = formData.key_projects.map((item, i) =>
                      i === idx ? { ...item, desc: e.target.value } : item
                    );
                    setFormData({ ...formData, key_projects: updated });
                  }}
                  className="w-full text-xs font-sans text-swiss-black/80 bg-transparent outline-none focus:border-swiss-blue resize-none"
                  placeholder="Description technique du projet et résultats obtenus..."
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
