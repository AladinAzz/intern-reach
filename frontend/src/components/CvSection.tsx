"use client";

import React, { useState } from "react";
import { UserProfile } from "@/types";
import { UploadCloud, CheckCircle2, Plus, Trash2, Save, FileText, Code2, GraduationCap } from "lucide-react";

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
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  // Synchronize internal form state whenever profile prop updates (e.g. after CV upload)
  React.useEffect(() => {
    if (profile) {
      setFormData(profile);
    }
  }, [profile]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setFileName(file.name);
      try {
        await onUploadFile(file);
        setUploadSuccess(true);
        setTimeout(() => setUploadSuccess(false), 6000);
      } catch (err) {
        console.error("Upload error:", err);
      }
    }
  };

  const handleAddSkill = () => {
    if (newSkill.trim() && !formData.technical_skills.includes(newSkill.trim())) {
      const updated = {
        ...formData,
        technical_skills: [...formData.technical_skills, newSkill.trim()],
      };
      setFormData(updated);
      setNewSkill("");
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    const updated = {
      ...formData,
      technical_skills: formData.technical_skills.filter((s) => s !== skillToRemove),
    };
    setFormData(updated);
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
          L'agent extrait automatiquement vos compétences clés, votre formation et vos projets en systèmes embarqués, traitement du signal et vision.
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
            <div className="inline-flex items-center space-x-1.5 px-3 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded font-mono text-xs mt-1 animate-fade-in">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>{fileName || "CV"} analysé avec succès ! Profil et compétences actualisés.</span>
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
              Ces données servent de socle objectif pour argumenter chaque paragraphe de la lettre de motivation.
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
          <label className="text-xs font-mono text-swiss-muted uppercase flex items-center space-x-1.5">
            <FileText className="w-3.5 h-3.5 text-swiss-blue" />
            <span>Projets Clés Réalisés (Utilisés comme preuves tangibles)</span>
          </label>

          <div className="space-y-3">
            {formData.key_projects.map((proj, idx) => (
              <div key={idx} className="p-3 bg-swiss-neutral/30 border border-swiss-border rounded space-y-1.5">
                <input
                  type="text"
                  value={proj.title}
                  onChange={(e) => {
                    const updated = [...formData.key_projects];
                    updated[idx].title = e.target.value;
                    setFormData({ ...formData, key_projects: updated });
                  }}
                  className="w-full text-xs font-bold font-sans text-swiss-black bg-transparent border-b border-swiss-border/60 pb-1 outline-none focus:border-swiss-blue"
                  placeholder="Titre du projet..."
                />
                <textarea
                  value={proj.desc}
                  rows={2}
                  onChange={(e) => {
                    const updated = [...formData.key_projects];
                    updated[idx].desc = e.target.value;
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

