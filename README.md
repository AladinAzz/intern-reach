# InternReach (Systèmes Embarqués, IA & Traitement de l'Information)

> **Design System:** Estilo Suíço Científico (International Typographic Style / Müller-Brockmann Grid)  
> **Target:** Stages en Île-de-France (Paris, Saclay, Gennevilliers, Limours...)  
> **Core Value:** Recherche multi-sources avec Agent Reach + Analyse de la demande recruteur + Studio de lettres de motivation multi-versions avec boucle de feedback.

---

## 1. Architecture

```
intern-reach/
├── backend/                  # FastAPI (Python 3.12)
│   ├── app/
│   │   ├── core/             # Configuration & BYOK Keys
│   │   ├── services/
│   │   │   ├── agent_reach.py      # Moteur de recherche & indexation des offres
│   │   │   ├── cv_parser.py        # Extraction PDF/Texte des compétences & projets
│   │   │   ├── letter_generator.py # Générateur 3 versions & boucle d'ajustement
│   │   │   └── storage.py          # Stockage persistant JSON (profil & historique)
│   │   ├── routers/          # /api/search, /api/cv, /api/letters, /api/history, /api/settings
│   │   └── data/             # Stockage local sécurisé
│   ├── requirements.txt
│   └── main.py
│
├── frontend/                 # Next.js 14 (App Router) + Tailwind CSS
│   ├── src/
│   │   ├── app/              # page.tsx, layout.tsx, globals.css (Grille suisse)
│   │   ├── components/       # SearchSection, CvSection, LetterStudio, HistorySection, SettingsModal
│   │   ├── lib/api.ts        # Client REST
│   │   └── types/            # Contrats TypeScript
│   └── package.json
│
├── design.md                 # Spécification Estilo Suíço Científico
└── start.bat                 # Lanceur double-clic (Backend + Frontend)
```

---

## 2. Lancement Rapide

Double-cliquez simplement sur **`start.bat`** à la racine, ou exécutez dans un terminal :

### Backend (Terminal 1)
```powershell
cd backend
.\venv\Scripts\python.exe main.py
# Accès API & Documentation Swagger : http://localhost:8008/docs
```

### Frontend (Terminal 2)
```powershell
cd frontend
npx.cmd pnpm dev
# Accès Application Web : http://localhost:3005
```

---

## 3. Fonctionnalités Clés

1. **Recherche Ciblée Paris / IDF :** Filtres spécialisés sur *Systèmes Embarqués*, *Edge AI / TinyML*, *Traitement du Signal*, *Computer Vision*, *FPGA & DSP*.
2. **Extraction CV Automatique :** Glissez-déposez votre CV PDF pour extraire compétences et projets techniques.
3. **Génération de Lettres Multi-Versions :**
   * **Version R&D / Scientifique** (adaptée pour CEA, Inria, ONERA, Thales R&D).
   * **Version Tech Agile / Startup** (adaptée pour Station F, robotique, scale-ups).
   * **Version Grand Groupe Industriel** (adaptée pour Valeo, Safran, Renault).
4. **Boucle d'Assistance Interactive :** Tapez vos remarques (*"insiste plus sur ROS 2 et C++"*) pour régénérer la lettre en direct.
5. **BYOK (Bring Your Own Key) :** Support de Google Gemini (gratuit/rapide), OpenAI GPT-4o, Anthropic Claude ou Ollama 100% hors-ligne.
6. **Historique des Candidatures :** Suivi chronologique de vos candidatures avec sauvegarde de chaque lettre personnalisée.

