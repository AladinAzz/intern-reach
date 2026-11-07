"use client";

import React, { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { SearchSection } from "@/components/SearchSection";
import { CvSection } from "@/components/CvSection";
import { LetterStudio } from "@/components/LetterStudio";
import { HistorySection } from "@/components/HistorySection";
import { SettingsModal } from "@/components/SettingsModal";
import {
  searchInternships,
  getProfile,
  updateProfile,
  uploadCvFile,
  generateLetters,
  refineLetter,
  getHistory,
  saveHistoryEntry,
  updateHistoryStatus,
  deleteHistoryEntry,
  getSettings,
  saveSettings,
} from "@/lib/api";
import { JobOffer, UserProfile, LetterVersion, HistoryEntry, AppSettings } from "@/types";

export default function Home() {
  const [activeTab, setActiveTab] = useState("search");
  const [offers, setOffers] = useState<JobOffer[]>([]);
  const [loadingOffers, setLoadingOffers] = useState(false);

  const [profile, setProfile] = useState<UserProfile>({
    full_name: "Ingénieur Stagiaire",
    email: "etudiant@institution.edu",
    phone: "+33 6 00 00 00 00",
    education: "Master 2 / École d'Ingénieurs — Systèmes Embarqués & IA",
    target_domains: ["Systèmes Embarqués", "Edge AI", "Traitement du Signal"],
    technical_skills: ["C++", "PyTorch", "OpenCV", "Linux Embarqué", "FreeRTOS", "FPGA"],
    key_projects: [],
  });
  const [uploadingCv, setUploadingCv] = useState(false);

  const [selectedJob, setSelectedJob] = useState<JobOffer | null>(null);
  const [letterVersions, setLetterVersions] = useState<LetterVersion[]>([]);
  const [generatingLetters, setGeneratingLetters] = useState(false);

  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [settings, setSettings] = useState<AppSettings>({
    active_provider: "gemini",
    ollama_base_url: "http://localhost:11434",
    ollama_model: "llama3:latest",
  });
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Initial load
  useEffect(() => {
    async function init() {
      setLoadingOffers(true);
      try {
        const [fetchedOffers, fetchedProfile, fetchedHistory, fetchedSettings] =
          await Promise.allSettled([
            searchInternships("Systèmes embarqués, Edge AI, Traitement du signal", ""),
            getProfile(),
            getHistory(),
            getSettings(),
          ]);

        if (fetchedOffers.status === "fulfilled") setOffers(fetchedOffers.value);
        if (fetchedProfile.status === "fulfilled") setProfile(fetchedProfile.value);
        if (fetchedHistory.status === "fulfilled") setHistory(fetchedHistory.value);
        if (fetchedSettings.status === "fulfilled") setSettings(fetchedSettings.value);
      } finally {
        setLoadingOffers(false);
      }
    }
    init();
  }, []);

  const handleSearch = async (query: string, location: string) => {
    setLoadingOffers(true);
    try {
      const results = await searchInternships(query, location);
      setOffers(results);
    } finally {
      setLoadingOffers(false);
    }
  };

  const handleSelectForLetter = async (job: JobOffer) => {
    setSelectedJob(job);
    setActiveTab("studio");
    setGeneratingLetters(true);
    try {
      const versions = await generateLetters(job, profile);
      setLetterVersions(versions);
    } finally {
      setGeneratingLetters(false);
    }
  };

  const handleUpdateProfile = async (updated: UserProfile) => {
    setProfile(updated);
    await updateProfile(updated);
  };

  const handleUploadCv = async (file: File) => {
    setUploadingCv(true);
    try {
      const updated = await uploadCvFile(file);
      setProfile(updated);
    } finally {
      setUploadingCv(false);
    }
  };

  const handleRefineLetter = async (currentLetter: string, feedback: string): Promise<string> => {
    if (!selectedJob) return currentLetter;
    return await refineLetter(currentLetter, feedback, selectedJob);
  };

  const handleSaveToHistory = async (entry: HistoryEntry) => {
    const updated = await saveHistoryEntry(entry);
    setHistory(updated);
  };

  const handleUpdateStatus = async (id: string, newStatus: HistoryEntry["status"]) => {
    setHistory((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status: newStatus } : item))
    );
    const updated = await updateHistoryStatus(id, newStatus);
    if (updated && updated.length > 0) {
      setHistory(updated);
    }
  };

  const handleDeleteHistory = async (id: string) => {
    setHistory((prev) => prev.filter((item) => item.id !== id));
    const updated = await deleteHistoryEntry(id);
    setHistory(updated);
  };

  const handleSaveSettings = async (updated: AppSettings) => {
    const res = await saveSettings(updated);
    setSettings(res);
  };

  return (
    <div className="min-h-[100dvh] flex flex-col bg-[#F8F9FA]">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        openSettings={() => setIsSettingsOpen(true)}
        historyCount={history.length}
      />

      <main className="flex-1 swiss-container py-8">
        {activeTab === "search" && (
          <SearchSection
            offers={offers}
            loading={loadingOffers}
            onSearch={handleSearch}
            onSelectForLetter={handleSelectForLetter}
            onAddCustomOffer={(newOffer) => setOffers((prev) => [newOffer, ...prev])}
          />
        )}

        {activeTab === "cv" && (
          <CvSection
            profile={profile}
            onUpdateProfile={handleUpdateProfile}
            onUploadFile={handleUploadCv}
            uploading={uploadingCv}
          />
        )}

        {activeTab === "studio" && (
          <LetterStudio
            job={selectedJob}
            versions={letterVersions}
            loading={generatingLetters}
            profile={profile}
            onRefine={handleRefineLetter}
            onSaveToHistory={handleSaveToHistory}
            onBackToSearch={() => setActiveTab("search")}
          />
        )}

        {activeTab === "history" && (
          <HistorySection
            history={history}
            onUpdateStatus={handleUpdateStatus}
            onDeleteEntry={handleDeleteHistory}
          />
        )}
      </main>

      <footer className="border-t border-swiss-border bg-white py-4 text-center text-xs font-mono text-swiss-muted no-print">
        <div className="swiss-container flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>INTERN.REACH // ESTILO SUÍÇO CIENTÍFICO (DESIGN SYSTEM 2026)</span>
          <span>SYSTÈMES EMBARQUÉS & IA // FRANCE // MULTI-SOURCES JOBSPY</span>
        </div>
      </footer>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={settings}
        onSave={handleSaveSettings}
        onSyncCompleted={() => handleSearch("Systèmes embarqués, Edge AI, Traitement du signal", "")}
      />
    </div>
  );
}

