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
    full_name: "",
    email: "",
    phone: "",
    education: "",
    target_domains: [],
    technical_skills: [],
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
        const [fetchedProfile, fetchedHistory, fetchedSettings] =
          await Promise.allSettled([
            getProfile(),
            getHistory(),
            getSettings(),
          ]);

        let loadedProfile: UserProfile | null = null;
        if (fetchedProfile.status === "fulfilled") {
          loadedProfile = fetchedProfile.value;
          setProfile(fetchedProfile.value);
        }
        if (fetchedHistory.status === "fulfilled") setHistory(fetchedHistory.value);
        if (fetchedSettings.status === "fulfilled") setSettings(fetchedSettings.value);

        // Derive initial search query dynamically from the candidate's CV profile
        let initialQuery = "";
        if (loadedProfile?.target_domains && loadedProfile.target_domains.length > 0) {
          initialQuery = loadedProfile.target_domains.slice(0, 3).join(", ");
        } else if (loadedProfile?.technical_skills && loadedProfile.technical_skills.length > 0) {
          initialQuery = loadedProfile.technical_skills.slice(0, 4).join(", ");
        }

        const initialOffers = await searchInternships(initialQuery, "");
        setOffers(initialOffers);
      } catch (err) {
        console.error("Init error:", err);
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

      // Refresh search offers in background using the newly extracted CV specialties
      let cvQuery = "";
      if (updated.target_domains && updated.target_domains.length > 0) {
        cvQuery = updated.target_domains.slice(0, 3).join(", ");
      } else if (updated.technical_skills && updated.technical_skills.length > 0) {
        cvQuery = updated.technical_skills.slice(0, 4).join(", ");
      }
      if (cvQuery) {
        void handleSearch(cvQuery, "");
      }
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
    const previous = history;
    setHistory((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status: newStatus } : item))
    );
    const updated = await updateHistoryStatus(id, newStatus);
    if (updated) {
      setHistory(updated);
    } else {
      setHistory(previous);
    }
  };

  const handleDeleteHistory = async (id: string) => {
    const previous = history;
    setHistory((prev) => prev.filter((item) => item.id !== id));
    const updated = await deleteHistoryEntry(id);
    if (updated) {
      setHistory(updated);
    } else {
      setHistory(previous);
    }
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
            profile={profile}
            onSearch={handleSearch}
            onSelectForLetter={handleSelectForLetter}
            onAddCustomOffer={(newOffer) => setOffers((prev) => [newOffer, ...prev])}
            onGoToCvTab={() => setActiveTab("cv")}
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
        onSyncCompleted={() => {
          const cvQ = profile.target_domains?.length
            ? profile.target_domains.slice(0, 3).join(", ")
            : (profile.technical_skills?.slice(0, 4).join(", ") || "");
          handleSearch(cvQ, "");
        }}
      />
    </div>
  );
}

