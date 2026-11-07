# InternReach REST API Specification

> Complete REST API reference for the InternReach scientific internship search, AI application tailoring, and candidate CRM platform.

**Base URL:** `http://localhost:8008` (Default development environment)  
**Interactive Swagger UI:** `http://localhost:8008/docs`  
**Interactive ReDoc:** `http://localhost:8008/redoc`

---

## Table of Contents

- [Search & Ingestion Endpoints](#search--ingestion-endpoints)
  - [POST /api/search](#post-apisearch)
  - [POST /api/search/import-offer](#post-apisearchimport-offer)
  - [POST /api/search/suggest-keywords](#post-apisearchsuggest-keywords)
- [CV & Profile Endpoints](#cv--profile-endpoints)
  - [GET /api/cv/profile](#get-apicvprofile)
  - [POST /api/cv/profile](#post-apicvprofile)
  - [POST /api/cv/upload](#post-apicvupload)
- [Motivation Letter & AI Studio Endpoints](#motivation-letter--ai-studio-endpoints)
  - [POST /api/letters/generate](#post-apilettersgenerate)
  - [POST /api/letters/refine](#post-apilettersrefine)
  - [POST /api/letters/pitch-and-gap](#post-apiletterspitch-and-gap)
  - [POST /api/letters/interview-prep](#post-apilettersinterview-prep)
- [Application CRM & History Endpoints](#application-crm--history-endpoints)
  - [GET /api/history](#get-apihistory)
  - [POST /api/history](#post-apihistory)
  - [PATCH /api/history/{entry_id}/status](#patch-apihistoryentry_idstatus)
  - [DELETE /api/history/{entry_id}](#delete-apihistoryentry_id)
  - [DELETE /api/history](#delete-apihistory)
- [Autonomous Worker & Liveness Endpoints](#autonomous-worker--liveness-endpoints)
  - [GET /api/worker/status](#get-apiworkerstatus)
  - [POST /api/worker/trigger](#post-apiworkertrigger)
  - [GET /api/worker/settings](#get-apiworkersettings)
  - [POST /api/worker/settings](#post-apiworkersettings)
- [Settings & BYOK Endpoints](#settings--byok-endpoints)
  - [GET /api/settings](#get-apisettings)
  - [POST /api/settings](#post-apisettings)

---

## Search & Ingestion Endpoints

### POST /api/search

Performs real-time multi-source internship search across live aggregators (`JobSpy` covering Indeed, LinkedIn, Glassdoor) and direct web live search (`ddgs` targeting French/European R&D portals and specialized platforms like Welcome to the Jungle, Apec, HelloWork, CEA, Thales, Inria).

**Parameters (Request Body):**

| Name | Type | Required | Description |
|---|---|---|---|
| `query` | string | No | Search domain, technical keywords, or title (e.g. `"Systèmes Embarqués"`, `"Edge AI"`, `"FPGA"`). Defaults to all scientific domains. |
| `location` | string | No | Geographic target (e.g. `"Paris, Île-de-France"`, `"Saclay"`, `"France"`). Defaults to Paris/IDF. |

**Response Status Codes:**
- `200 OK`: Successful search query execution with aggregated listings.

**Request Example:**
```json
{
  "query": "Systèmes Embarqués",
  "location": "Paris, Île-de-France"
}
```

**Response Example:**
```json
{
  "status": "success",
  "total": 12,
  "location": "Paris, Île-de-France",
  "query": "Systèmes Embarqués",
  "results": [
    {
      "id": "jobspy-indeed-1827491",
      "title": "Stage Ingénieur Systèmes Embarqués C/C++ - Linux RT",
      "company": "Thales",
      "location": "Vélizy-Villacoublay, Île-de-France",
      "url": "https://fr.indeed.com/viewjob?jk=example123",
      "description": "Au sein du département R&D, vous participerez au développement de firmwares bas niveau sous FreeRTOS et Linux Temps Réel...",
      "tags": ["C++", "Linux RT", "FreeRTOS", "ARM Cortex"],
      "published_at": "2026-11-06T14:30:00Z",
      "is_active": true,
      "source": "JobSpy (Indeed)",
      "score": 92
    }
  ]
}
```

---

### POST /api/search/import-offer

Imports and structures an internship offer directly from an external URL or from raw job description text pasted by the user. Automatically deduplicates and indexes the listing into local storage.

**Parameters (Request Body):**

| Name | Type | Required | Description |
|---|---|---|---|
| `url` | string | No | Direct URL of the job advertisement (HTML scraped via Trafilatura/BeautifulSoup). |
| `raw_text` | string | No | Raw pasted job posting text if URL scraping is gated or unavailable. |

**Response Status Codes:**
- `200 OK`: Successfully parsed and indexed offer.
- `400 Bad Request`: Blocked SSRF attempt (private IP, loopback, internal hostname) or missing inputs.
- `422 Unprocessable Entity`: Invalid request payload or missing URL/raw_text.
- `502 Bad Gateway`: Target server unreachable or rejected request.

**Request Example:**
```json
{
  "url": "https://www.welcometothejungle.com/fr/companies/example/jobs/stage-ia-embarquee"
}
```

**Response Example:**
```json
{
  "status": "success",
  "offer": {
    "id": "imported-9f8a2c1b",
    "title": "Stage R&D Edge AI & Computer Vision",
    "company": "Prophesee",
    "location": "Paris 11e",
    "url": "https://www.welcometothejungle.com/fr/companies/example/jobs/stage-ia-embarquee",
    "description": "Conception d'algorithmes neuromorphiques et déploiement sur cibles FPGA/DSP...",
    "tags": ["Edge AI", "Computer Vision", "Python", "PyTorch", "C++"],
    "published_at": "2026-11-07T02:00:00Z",
    "is_active": true,
    "source": "Import Manuel"
  }
}
```

---

### POST /api/search/suggest-keywords

Analyzes the candidate's CV profile using AI to synthesize the optimal search query, key specialty facets, and strategic alternative search angles tailored to the job market.

**Parameters (Request Body):**

| Name | Type | Required | Description |
|---|---|---|---|
| `profile` | object | No | Candidate profile dictionary. If omitted, the saved profile is loaded from `profile.json`. |

**Response Status Codes:**
- `200 OK`: AI keyword suggestions successfully generated.

**Request Example:**
```json
{
  "profile": {
    "full_name": "Amine OTMANI",
    "education": "Master 2 E3A - Université Paris-Saclay",
    "target_domains": ["Systèmes Embarqués", "Linux RT", "Edge AI"],
    "technical_skills": ["C++", "FreeRTOS", "STM32", "ROS 2"]
  }
}
```

**Response Example:**
```json
{
  "status": "success",
  "suggested_query": "Stage Systèmes Embarqués C++ FreeRTOS STM32",
  "specialties": [
    "Systèmes Embarqués Temps Réel",
    "Développement C/C++ Bas Niveau",
    "FreeRTOS & STM32",
    "Robotique & ROS 2"
  ],
  "alternative_queries": [
    {
      "label": "Angle R&D / Scientifique",
      "query": "Stage R&D Systèmes Embarqués Linux RT C++"
    },
    {
      "label": "Angle Industriel / Aéro",
      "query": "Stage Ingénieur Logiciel Embarqué STM32 CAN"
    },
    {
      "label": "Angle Robotique & IA",
      "query": "Stage Edge AI Robotique ROS 2 Perception"
    }
  ],
  "rationale": "Cette combinaison valorise immédiatement vos réalisations en firmware bas niveau et en temps réel."
}
```

---

## CV & Profile Endpoints

### GET /api/cv/profile

Retrieves the candidate's persisted scientific profile, including contact details, educational background, technical skills, and structured engineering projects.

**Parameters:** None

**Response Status Codes:**
- `200 OK`: Candidate profile object.

**Response Example:**
```json
{
  "name": "Amine OTMANI",
  "email": "amineotmani06@gmail.com",
  "phone": "+33 746505582",
  "education": "Master 1 & 2 E3A - Électronique, Énergie Électrique, Automatique (Université Paris-Saclay)",
  "skills": ["C/C++", "Python", "FreeRTOS", "Linux Embarqué", "STM32", "FPGA", "ROS 2", "Git"],
  "projects": [
    "Conception d'un nanosatellite CubeSat (LATMOS / UVSQ) : Intégration du bus I2C/SPI et firmware de télémétrie",
    "Système de supervision IoT temps réel sous FreeRTOS avec microcontrôleur STM32F4"
  ],
  "experience": "Stage Technicien Télécom (Algérie Télécom) : Déploiement FTTH et analyse de réflectométrie OTDR"
}
```

---

### POST /api/cv/profile

Updates and persists the candidate's scientific profile JSON document.

**Parameters (Request Body):**

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Full candidate name |
| `email` | string | Yes | Email address |
| `phone` | string | No | Mobile phone number |
| `education` | string | Yes | Academic degrees and institutions |
| `skills` | array[string]| Yes | List of verified technical skills |
| `projects` | array[string]| No | List of key scientific/engineering projects |
| `experience` | string | No | Professional internships or positions |

**Response Status Codes:**
- `200 OK`: Confirmation of saved profile.

**Request Example:**
```json
{
  "name": "Amine OTMANI",
  "email": "amineotmani06@gmail.com",
  "phone": "+33 746505582",
  "education": "Master 2 E3A - Université Paris-Saclay",
  "skills": ["C++", "Python", "STM32", "ROS 2", "Linux RT"],
  "projects": ["Banc de test avionique STM32"],
  "experience": "Stage LATMOS Paris-Saclay"
}
```

**Response Example:**
```json
{
  "status": "saved",
  "profile": {
    "name": "Amine OTMANI",
    "email": "amineotmani06@gmail.com",
    "phone": "+33 746505582",
    "education": "Master 2 E3A - Université Paris-Saclay",
    "skills": ["C++", "Python", "STM32", "ROS 2", "Linux RT"],
    "projects": ["Banc de test avionique STM32"],
    "experience": "Stage LATMOS Paris-Saclay"
  }
}
```

---

### POST /api/cv/upload

Uploads a candidate CV (PDF, TXT, or Markdown) up to 10 MB. Extracts raw text via `pypdf`, then invokes the AI Structured Extraction Pipeline (Gemini LLM with regex fallback) to extract names, emails, phone numbers, degrees, skills, and projects.

**Parameters (Multipart Form Data):**

| Name | Type | Required | Description |
|---|---|---|---|
| `file` | file (binary) | Yes | Uploaded resume (`.pdf`, `.txt`, `.md`). Maximum 10 MB. |

**Response Status Codes:**
- `200 OK`: File successfully uploaded, parsed, and persisted into candidate profile.
- `400 Bad Request`: Unsupported file type.
- `413 Payload Too Large`: File exceeds 10 MB limit.

**Response Example:**
```json
{
  "status": "extracted",
  "filename": "Profile.pdf",
  "profile": {
    "name": "Amine OTMANI",
    "email": "amineotmani06@gmail.com",
    "phone": "+33 746505582",
    "education": "Master 1 E3A - Université Paris-Saclay",
    "skills": ["C", "C++", "Python", "FreeRTOS", "Linux Embarqué", "STM32", "FPGA Vivado", "MATLAB", "Simulink", "CAN", "I2C", "SPI", "Git"],
    "projects": [
      "LATMOS: Architecture logicielle d'un sous-système de contrôle d'attitude pour nanosatellite",
      "Robotique mobile autonome avec cartographie SLAM sous ROS 2"
    ],
    "experience": "Stage ingénieur junior chez Sonelgaz : Automatisation SCADA"
  }
}
```

---

## Motivation Letter & AI Studio Endpoints

### POST /api/letters/generate

Generates three tailored, publication-ready motivation letter variants targeting the specified job offer using the candidate's profile.

**Variants Produced:**
1. **R&D / Scientifique:** Tailored for research institutes and laboratories (CEA, Inria, CNRS, ONERA, Thales Research). Focuses on scientific methodology, state-of-the-art literature, and experimental rigor.
2. **Tech Agile / Startup:** Tailored for fast-paced scale-ups and robotics startups (Station F, Prophesee, Wandercraft). Emphasizes rapid iteration, pragmatism, and clean code.
3. **Grand Groupe Industriel:** Tailored for large defense, aerospace, or automotive corporations (Safran, Airbus, Renault, Valeo). Emphasizes safety-critical standards (ISO 26262, DO-178C), quality assurance, and scalability.

**Parameters (Request Body):**

| Name | Type | Required | Description |
|---|---|---|---|
| `job` | object | Yes | The target job offer dictionary (must contain `title`, `company`, `description`). |
| `profile` | object | No | Candidate profile. If omitted, the persisted candidate profile is loaded automatically. |

**Response Status Codes:**
- `200 OK`: Successfully generated 3 letter variants with rationale and ATS alignment scores.

**Request Example:**
```json
{
  "job": {
    "id": "thales-stage-1",
    "title": "Stage R&D Nanosatellite & Logiciel Embarqué",
    "company": "Thales Alenia Space",
    "description": "Développement de modules logiciels critiques en C/C++ pour constellation de satellites..."
  }
}
```

**Response Example:**
```json
{
  "status": "success",
  "job_id": "thales-stage-1",
  "versions": {
    "scientific": "Madame, Monsieur,\n\nActuellement étudiant en Master 2 E3A à l'Université Paris-Saclay...",
    "startup": "Bonjour l'équipe Thales Alenia Space,\n\nPassionné par le développement bas niveau...",
    "industrial": "Madame, Monsieur,\n\nC'est avec un vif intérêt que je postule à votre offre de stage..."
  }
}
```

---

### POST /api/letters/refine

Refines an existing motivation letter iteratively based on precise user directives (e.g. *"Insiste plus sur mes compétences en FreeRTOS et supprime la mention de Java"*).

**Parameters (Request Body):**

| Name | Type | Required | Description |
|---|---|---|---|
| `current_letter` | string | Yes | The current text of the letter being modified. |
| `feedback` | string | Yes | Natural language refinement instructions from the candidate. |
| `job` | object | Yes | The target job offer dictionary for context preservation. |

**Response Status Codes:**
- `200 OK`: Refined letter matching user feedback while preserving professional tone.

**Request Example:**
```json
{
  "current_letter": "Madame, Monsieur,\n\nActuellement en Master E3A...",
  "feedback": "Mets l'accent sur mon projet CubeSat au LATMOS et raccourcis le deuxième paragraphe.",
  "job": {
    "title": "Stage Nanosatellite",
    "company": "Thales Alenia Space"
  }
}
```

**Response Example:**
```json
{
  "status": "success",
  "refined_letter": "Madame, Monsieur,\n\nActuellement en Master E3A à l'Université Paris-Saclay, j'ai notamment conçu au LATMOS l'architecture logicielle..."
}
```

---

### POST /api/letters/pitch-and-gap

Performs in-depth ATS skill gap analysis and crafts 3 persuasive elevator pitches tailored to the offer.

**Parameters (Request Body):**

| Name | Type | Required | Description |
|---|---|---|---|
| `job` | object | Yes | The target job offer dictionary. |
| `profile` | object | No | Candidate profile. Loaded from storage if omitted. |

**Response Status Codes:**
- `200 OK`: Strategic matching analysis.

**Response Example:**
```json
{
  "status": "success",
  "analysis": {
    "pitches": [
      "Profil polyvalent alliant modélisation électronique et développement bas niveau en C++ sous Linux temps réel.",
      "Expérience concrète sur projet spatial universitaire (CubeSat) immédiatement transférable à vos bancs de test.",
      "Solide rigueur méthodologique issue d'un cursus sélectif à l'Université Paris-Saclay."
    ],
    "matching_skills": ["C++", "FreeRTOS", "Linux Embarqué", "STM32"],
    "missing_skills": ["DO-178C", "VxWorks"],
    "recommendations": "Mettre en avant l'analogie entre vos projets de laboratoire et les contraintes de robustesse aérospatiales."
  }
}
```

---

### POST /api/letters/interview-prep

Generates five targeted technical and behavioral interview questions tailored to the intersection of the job description and the candidate's CV, complete with suggested high-impact answer angles.

**Parameters (Request Body):**

| Name | Type | Required | Description |
|---|---|---|---|
| `job` | object | Yes | Target job offer dictionary. |
| `profile` | object | No | Candidate profile. |

**Response Status Codes:**
- `200 OK`: List of generated interview questions with strategic pointers.

**Response Example:**
```json
{
  "status": "success",
  "questions": [
    {
      "question": "Comment gérez-vous les sections critiques et l'inversion de priorité sous FreeRTOS ?",
      "category": "Technique Bas Niveau",
      "suggested_angle": "Évoquez l'utilisation de mutex avec héritage de priorité et les mécanismes de files de messages utilisés lors de votre projet STM32."
    }
  ]
}
```

---

## Application CRM & History Endpoints

### GET /api/history

Retrieves the candidate's application pipeline history, sorted chronologically from newest to oldest.

**Parameters:** None

**Response Status Codes:**
- `200 OK`: Array of application tracking records.

**Response Example:**
```json
[
  {
    "id": "app-hist-001",
    "job_id": "jobspy-indeed-1827491",
    "job_title": "Stage Ingénieur Systèmes Embarqués C/C++",
    "company": "Thales",
    "location": "Vélizy-Villacoublay",
    "applied_at": "2026-11-06T15:00:00Z",
    "status": "Entretien",
    "variant_used": "scientific",
    "letter_content": "Madame, Monsieur,...",
    "notes": "Entretien RH prévu le 14 novembre à 10h."
  }
]
```

---

### POST /api/history

Creates a new entry in the candidate's application pipeline.

**Parameters (Request Body):**

| Name | Type | Required | Description |
|---|---|---|---|
| `job_id` | string | Yes | Unique ID of the job offer |
| `job_title` | string | Yes | Title of the position |
| `company` | string | Yes | Company or laboratory name |
| `location` | string | No | Work location |
| `status` | string | No | Pipeline status (`"Prêt"`, `"Candidaté"`, `"Entretien"`, `"Offre"`, `"Refusé"`). Defaults to `"Candidaté"`. |
| `letter_content`| string | No | Full text of the generated letter used for this application |
| `variant_used` | string | No | Identifier of the variant (`"scientific"`, `"startup"`, `"industrial"`) |
| `notes` | string | No | Personal follow-up notes |

**Response Status Codes:**
- `200 OK`: Saved history array containing the newly added record.

---

### PATCH /api/history/{entry_id}/status

Updates the pipeline status of an existing application record in real-time.

**Parameters:**
- `entry_id` (Path, required): Unique identifier of the application record.

**Request Body:**

| Name | Type | Required | Description |
|---|---|---|---|
| `status` | string | Yes | New status (`"Enregistré"`, `"Candidaté"`, `"Entretien"`, `"Accepté"`, `"Refusé"`) |

**Response Status Codes:**
- `200 OK`: Status updated successfully.
- `404 Not Found`: Entry ID does not exist in history.
- `422 Unprocessable Entity`: Status value is not one of the allowed lifecycle states.

**Request Example:**
```json
{
  "status": "Entretien"
}
```

---

### DELETE /api/history/{entry_id}

Deletes an application record from the tracking CRM.

**Parameters:**
- `entry_id` (Path, required): Unique identifier of the record to delete.

**Response Status Codes:**
- `200 OK`: Record deleted. Returns updated history array.
- `404 Not Found`: Entry ID does not exist in history.

---

### DELETE /api/history

Clears all entries from the candidate application tracking history.

**Parameters:** None

**Response Status Codes:**
- `200 OK`: All records deleted. Returns empty array `[]`.

---

## Autonomous Worker & Liveness Endpoints

### GET /api/worker/status

Inspects the current health, execution status, and sync metrics of the background ingestion worker.

**Parameters:** None

**Response Status Codes:**
- `200 OK`: Worker state metadata.

**Response Example:**
```json
{
  "is_running": false,
  "last_sync": "2026-11-07T03:00:00Z",
  "last_status": "success",
  "total_jobs_stored": 48,
  "active_jobs": 44,
  "closed_jobs": 4,
  "last_checked_urls": 48
}
```

---

### POST /api/worker/trigger

Manually triggers an immediate background cycle of multi-source ingestion (`JobSpy` + `ddgs`) followed by an asynchronous HTTP HEAD liveness sweep of all stored job postings.

**Parameters:** None

**Response Status Codes:**
- `200 OK`: Cycle executed or currently running.

**Response Example:**
```json
{
  "status": "completed",
  "message": "Synchronisation multi-sources et vérification de liveness terminées.",
  "state": {
    "is_running": false,
    "last_sync": "2026-11-07T03:28:00Z",
    "last_status": "success",
    "total_jobs_stored": 52,
    "active_jobs": 47,
    "closed_jobs": 5
  }
}
```

---

### GET /api/worker/settings

Retrieves the autonomous worker's operational parameters (interval, automated sync enable flag, target domains).

**Parameters:** None

**Response Status Codes:**
- `200 OK`: Current worker settings.

**Response Example:**
```json
{
  "auto_sync_enabled": true,
  "sync_interval_hours": 6,
  "verify_liveness": true,
  "default_domains": ["Systèmes Embarqués", "Edge AI", "Traitement du Signal"]
}
```

---

### POST /api/worker/settings

Updates worker operational configuration.

**Parameters (Request Body):**

| Name | Type | Required | Description |
|---|---|---|---|
| `auto_sync_enabled` | boolean | Yes | Whether the worker automatically executes on schedule |
| `sync_interval_hours`| integer | Yes | Hours between automated scans (minimum 1) |
| `verify_liveness` | boolean | Yes | Whether to perform HTTP HEAD liveness probing |

**Response Status Codes:**
- `200 OK`: Worker configuration persisted.

---

## Settings & BYOK Endpoints

### GET /api/settings

Retrieves the active application settings with all sensitive API keys safely masked (`AIzaSy...4aB1`).

**Parameters:** None

**Response Status Codes:**
- `200 OK`: Application settings object.

**Response Example:**
```json
{
  "llm_provider": "gemini",
  "gemini_api_key": "AIzaSy...4xQ9",
  "openai_api_key": "",
  "claude_api_key": "",
  "ollama_base_url": "http://localhost:11434",
  "ollama_model": "mistral"
}
```

---

### POST /api/settings

Persists user settings and BYOK credentials. If a masked string (`...`) is passed for an API key, the existing key in secure storage is preserved.

**Parameters (Request Body):**

| Name | Type | Required | Description |
|---|---|---|---|
| `llm_provider` | string | Yes | Selected provider (`"gemini"`, `"openai"`, `"claude"`, `"ollama"`) |
| `gemini_api_key` | string | No | Google Gemini API key |
| `openai_api_key` | string | No | OpenAI API key |
| `claude_api_key` | string | No | Anthropic Claude API key |
| `ollama_base_url`| string | No | Custom Ollama host URL for local inference |
| `ollama_model` | string | No | Model name (e.g. `"mistral"`, `"llama3"`) |

**Response Status Codes:**
- `200 OK`: Settings successfully updated. Masked credentials returned.

