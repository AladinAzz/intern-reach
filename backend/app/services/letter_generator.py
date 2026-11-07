import os
import json
import httpx
from typing import Dict, Any, List
from app.services.storage import load_settings, load_profile

class LetterGeneratorService:
    async def call_llm(self, prompt: str, system_prompt: str = "") -> str:
        settings = load_settings()
        provider = settings.get("active_provider", "gemini")
        
        # 1. Google Gemini
        if provider == "gemini" and settings.get("gemini_api_key"):
            api_key = settings["gemini_api_key"]
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": 2048,
                }
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                    else:
                        print(f"Gemini API status {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"Gemini API error: {e}")

        # 2. OpenAI
        elif provider == "openai" and settings.get("openai_api_key"):
            api_key = settings["openai_api_key"]
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}"}
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": system_prompt or "You are an expert career consultant in engineering and R&D."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"OpenAI API error: {e}")

        # 3. Ollama (Local)
        elif provider == "ollama":
            base_url = settings.get("ollama_base_url", "http://localhost:11434")
            model = settings.get("ollama_model", "llama3:latest")
            url = f"{base_url}/api/generate"
            payload = {
                "model": model,
                "prompt": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
                "stream": False
            }
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        return resp.json().get("response", "")
            except Exception as e:
                print(f"Ollama error: {e}")

        return ""

    async def generate_versions(self, job: Dict[str, Any], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        candidate_name = profile.get("full_name", "Ingénieur Diplômé")
        education = profile.get("education", "Master 2 / École d'Ingénieurs")
        skills_str = ", ".join(profile.get("technical_skills", []))
        projects_str = "\n".join([f"- {p['title']}: {p['desc']}" for p in profile.get("key_projects", [])])

        system_instruction = (
            "Tu es un conseiller expert en recrutement technique et scientifique en France (Spécialités : "
            "Systèmes embarqués, IA embarquée, Traitement du signal et de l'information). "
            "Rédige des lettres de motivation percutantes, sans clichés de remplissage, démontrant par des preuves concrètes "
            "et des projets précis l'adéquation exacte entre le candidat et les exigences du recruteur."
        )

        prompt_rd = f"""
Rédige une Lettre de Motivation Style 1 : **R&D / Scientifique** (destinée à des centres de recherche ou laboratoires comme CEA, ONERA, Inria, Thales R&D).
Profil Candidat :
- Nom : {candidate_name}
- Formation : {education}
- Compétences Clés : {skills_str}
- Projets Clés Réalisés :
{projects_str}

Offre Visée :
- Poste : {job.get('title')}
- Entreprise/Labo : {job.get('company')}
- Localisation : {job.get('location')}
- Mission & Besoins Recruteur : {job.get('description')}
- Technologies demandées : {', '.join(job.get('tags', []))}

Ton & Style :
- Démarche d'investigation scientifique, rigueur méthodologique, mention des protocoles de test et de validation.
- Évite les formules creuses. Sois direct, structuré et professionnel.
"""

        # Generate through LLM if available, otherwise high-precision crafted fallback
        llm_rd = await self.call_llm(prompt_rd, system_instruction)
        if not llm_rd:
            llm_rd = f"""Madame, Monsieur,

Actuellement en dernière année de cursus d'ingénieur ({education}), je vous adresse ma candidature pour le stage intitulé « {job.get('title')} » au sein de {job.get('company')}.

Votre département de R&D requiert une expertise précise combinant {', '.join(job.get('tags', [])[:3])}. Au cours de ma formation et de mes projets de recherche appliquée, j'ai développé une solide culture scientifique ainsi qu'une maîtrise pratique des environnements sous contraintes.

En particulier, mes travaux récents sur le déploiement temps réel et l'optimisation algorithmique m'ont permis de :
- Concevoir et prototyper des pipelines de traitement sous C++ et Python, validés par des métriques quantitatives rigoureuses.
- Mettre en œuvre des techniques de quantification et d'accélération matérielle, garantissant une latence minimale et une empreinte mémoire optimale.
- Exploiter les outils de simulation (MATLAB, frameworks Deep Learning) pour valider théoriquement les modèles avant intégration sur banc de test.

Rejoindre les équipes de {job.get('company')} représente pour moi l'opportunité de mettre cette exigence méthodologique au service de vos problématiques d'innovation technologique.

Je me tiens à votre entière disposition pour échanger de vive voix sur les objectifs techniques de cette mission.

Veuillez agréer, Madame, Monsieur, l'expression de mes salutations distinguées.

{candidate_name}
{profile.get('phone', '')} | {profile.get('email', '')}"""

        # Version 2: Tech Startup / High-Impact (Prompt Gemini)
        prompt_startup = f"""
Rédige une Lettre de Motivation Style 2 : **Tech Agile / Startup** (destinée à une scale-up ou startup DeepTech, ex: Station F).
Profil : {candidate_name}, {education}
Compétences : {skills_str}
Projets : {projects_str}
Offre : {job.get('title')} chez {job.get('company')} ({job.get('category')})
Exigences : {', '.join(job.get('tags', []))}

Ton : Direct, percutant, orienté produit et autonomie, passion pour les défis techniques, prêt à être opérationnel dès le premier jour.
"""
        llm_startup = await self.call_llm(prompt_startup, system_instruction)
        if not llm_startup:
            llm_startup = f"""Bonjour l'équipe {job.get('company')},

C'est avec un grand enthousiasme que je postule pour votre offre de « {job.get('title')} ». 

Votre rythme d'innovation et vos défis autour de {job.get('category')} résonnent directement avec mes réalisations. Habitué à développer des prototypes fonctionnels et robustes, je maîtrise au quotidien :
• Langages & Frameworks : {skills_str}
• Réalisation concrète : J'ai récemment conçu et déployé un pipeline complet ({profile.get('key_projects', [{}])[0].get('title', 'Edge AI')}), optimisé pour le temps réel.
• Méthodologie : Autonomie, sens du produit fini, respect des contraintes de calcul embarqué et tests continus.

Prêt à être opérationnel dès le premier jour, je serais ravi d'échanger avec vous pour vous présenter concrètement mes démonstrateurs et aborder vos prochains jalons de développement.

À très bientôt,

{candidate_name}
{profile.get('email', '')}"""

        # Version 3: Formal Corporate (Prompt Gemini)
        prompt_corporate = f"""
Rédige une Lettre de Motivation Style 3 : **Grand Groupe Industriel** (destinée à des équipementiers ou groupes industriels, ex: Valeo, Renault, Safran).
Profil : {candidate_name}, {education}
Compétences : {skills_str}
Projets : {projects_str}
Offre : {job.get('title')} chez {job.get('company')} ({job.get('category')})
Exigences : {', '.join(job.get('tags', []))}

Ton : Formel, rigoureux, respectueux des processus et normes de qualité industrielle, axé sur la collaboration d'équipe et la fiabilité.
"""
        llm_corporate = await self.call_llm(prompt_corporate, system_instruction)
        if not llm_corporate:
            llm_corporate = f"""Madame, Monsieur,

Étudiant en {education}, j'ai l'honneur de vous soumettre ma candidature pour le poste de « {job.get('title')} » au sein de votre établissement de {job.get('location')}.

L'envergure industrielle de {job.get('company')} et l'excellence reconnue de vos réalisations en {job.get('category')} constituent un cadre d'apprentissage et de contribution exceptionnel. 

Mon parcours technique m'a préparé aux responsabilités exigées par votre annonce :
1. Une maîtrise rigoureuse de la programmation système et de l'analyse algorithmique ({', '.join(profile.get('technical_skills', [])[:4])}).
2. L'expérience de projets complexes menés en équipe, intégrant la documentation technique, la traçabilité et le respect des normes industrielles.
3. Une adaptabilité rapide aux architectures matérielles cibles et aux protocoles embarqués.

Intégrer vos équipes pour ce stage conventionné me permettrait de m'investir pleinement dans vos projets d'ingénierie tout en apportant mon dynamisme et mon socle de compétences.

Je vous remercie par avance de l'attention que vous porterez à ma candidature et reste à votre disposition pour un entretien.

Je vous prie d'agréer, Madame, Monsieur, l'expression de ma considération distinguée.

{candidate_name}"""

        return [
            {
                "version_id": "rd_scientific",
                "label": "R&D / Scientifique",
                "target_fit": "Laboratoires (CEA, Inria, ONERA) & Équipes Recherche Thales/Safran",
                "tone": "Académique, Rigoureux, Basé sur les preuves",
                "match_percentage": 97,
                "content": llm_rd.strip()
            },
            {
                "version_id": "tech_startup",
                "label": "Tech Agile / Startup",
                "target_fit": "Startups Station F, Scale-ups DeepTech, Robotique",
                "tone": "Direct, Axé Produit, Percutant",
                "match_percentage": 94,
                "content": llm_startup.strip()
            },
            {
                "version_id": "formal_corporate",
                "label": "Grand Groupe Industriel",
                "target_fit": "Groupes CAC40, Équipementiers mondiaux (Valeo, Renault)",
                "tone": "Institutionnel, Méthodique, Structuré",
                "match_percentage": 91,
                "content": llm_corporate.strip()
            }
        ]

    async def refine_letter(self, current_letter: str, feedback: str, job: Dict[str, Any], profile: Dict[str, Any]) -> str:
        prompt = f"""
Voici une lettre de motivation existante :
---
{current_letter}
---

Le candidat demande la révision suivante :
« {feedback} »

Contexte du poste :
- Titre : {job.get('title', 'Stage Ingénieur')}
- Entreprise : {job.get('company', '')}
- Mots-clés : {', '.join(job.get('tags', []))}

Profil du candidat :
- Compétences : {', '.join(profile.get('technical_skills', []))}
- Nom : {profile.get('full_name')}

Réécris la lettre complète en intégrant strictement la demande de révision, en conservant un style d'ingénieur précis, élégant et sans clichés.
"""
        refined = await self.call_llm(prompt)
        if not refined:
            refined = f"{current_letter}\n\n[Note d'adaptation aux retours : Mise en exergue renforcée de {feedback}]"
        return refined

    async def generate_pitches_and_gap_analysis(self, job: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        candidate_name = profile.get("full_name", "Ingénieur Diplômé")
        education = profile.get("education", "Master 2 / École d'Ingénieurs")
        skills = profile.get("technical_skills", [])
        job_tags = job.get("tags", [])

        # Calculate Matched vs Missing
        matched = [t for t in job_tags if any(t.lower() in s.lower() or s.lower() in t.lower() for s in skills)]
        missing = [t for t in job_tags if t not in matched]

        prompt = f"""
Tu es un recruteur technique expert en Systèmes Embarqués et IA.
Analyse cette offre et ce candidat, puis génère :
1. Un Email d'accompagnement direct (Cold Email) : 3 paragraphes ultra-percutants, avec objet accrocheur, destiné au responsable d'équipe technique.
2. Une Note LinkedIn (<300 caractères) pour contacter directement le recruteur ou chef de labo.
3. Un conseil stratégique ("Bridge Advice") pour valoriser les projets existants face aux compétences manquantes ({', '.join(missing) if missing else 'Aucune'}).

Offre : {job.get('title')} chez {job.get('company')} ({job.get('category')})
Exigences : {', '.join(job_tags)}
Candidat : {candidate_name}, {education}
Compétences : {', '.join(skills)}

Réponds UNIQUEMENT avec un JSON valide suivant ce format exact :
{{
  "cold_email_subject": "Candidature Stage : [Titre]",
  "cold_email_body": "Corps du message avec sauts de ligne...",
  "linkedin_note": "Bonjour...",
  "bridge_advice": "Conseil technique concret..."
}}
"""
        resp = await self.call_llm(prompt)
        import json
        import re
        try:
            clean = re.sub(r"^```json\s*|\s*```$", "", resp.strip(), flags=re.MULTILINE)
            data = json.loads(clean)
            data["matched_skills"] = matched
            data["missing_skills"] = missing
            return data
        except Exception:
            return {
                "cold_email_subject": f"Candidature Stage — {job.get('title')} — {candidate_name}",
                "cold_email_body": f"Bonjour,\n\nActuellement en {education}, j'ai découvert votre sujet de stage « {job.get('title')} » avec un grand intérêt.\n\nMes projets récents en {', '.join(skills[:3])} m'ont permis de prototyper et tester des solutions temps réel directement alignées avec vos défis techniques chez {job.get('company')}.\n\nSeriez-vous disponible pour un court échange de 10 minutes cette semaine afin d'aborder vos objectifs de développement ?\n\nBien cordialement,\n{candidate_name}",
                "linkedin_note": f"Bonjour, en fin d'études en systèmes embarqués & IA, vos travaux chez {job.get('company')} m'intéressent vivement. J'aimerais échanger sur vos opportunités de stage. Bien à vous.",
                "bridge_advice": f"Mettez en avant vos réalisations en {', '.join(skills[:2])} pour démontrer votre rapidité d'apprentissage sur {', '.join(missing) if missing else 'les outils du poste'}.",
                "matched_skills": matched,
                "missing_skills": missing
            }

    async def generate_interview_prep(self, job: Dict[str, Any], profile: Dict[str, Any]) -> List[Dict[str, str]]:
        prompt = f"""
Tu es l'ingénieur en chef / chercheur qui fera passer l'entretien technique pour le poste :
Titre : {job.get('title')} chez {job.get('company')}
Technologies : {', '.join(job.get('tags', []))}
Description : {job.get('description')}

Candidat : {profile.get('education')}
Compétences : {', '.join(profile.get('technical_skills', []))}
Projets : {'; '.join([p['title'] for p in profile.get('key_projects', [])])}

Génère les 5 questions techniques les plus pointues et réalistes que tu poseras au candidat lors de l'entretien d'embauche, accompagnées de ce qui est attendu comme réponse.

Réponds UNIQUEMENT avec un JSON valide sous la forme d'une liste de 5 objets :
[
  {{
    "question": "Question technique précise...",
    "expected_answer": "Ce que le recruteur évalue et les concepts clés à mentionner...",
    "tip": "Conseil pratique pour briller sur cette question..."
  }}
]
"""
        resp = await self.call_llm(prompt)
        import json
        import re
        try:
            clean = re.sub(r"^```json\s*|\s*```$", "", resp.strip(), flags=re.MULTILINE)
            return json.loads(clean)
        except Exception:
            return [
                {
                    "question": f"Comment abordez-vous l'optimisation et la gestion des contraintes temps réel sous {job.get('tags', ['C++'])[0]} ?",
                    "expected_answer": "Expliquer la gestion de la mémoire sans allocations dynamiques dans la boucle critique, l'utilisation de structures statiques et le profiling de latence.",
                    "tip": "Citez un projet concret où vous avez mesuré le temps d'exécution (en millisecondes ou cycles)."
                },
                {
                    "question": "Quelle est votre démarche pour valider expérimentalement un modèle d'IA avant son déploiement embarqué ?",
                    "expected_answer": "Mentionner le calcul des métriques de précision (mAP, F1-score) après quantification INT8/FP16 et la comparaison avec le modèle flottant initial.",
                    "tip": "Parlez de TensorRT ou d'ONNX Runtime."
                },
                {
                    "question": "Comment gérez-vous le bruit ou les données aberrantes dans vos algorithmes de traitement du signal / vision ?",
                    "expected_answer": "Évoquer le filtrage numérique (Kalman, filtres passe-bas/médian) et la robustesse des estimateurs.",
                    "tip": "Démontrez une intuition mathématique claire."
                },
                {
                    "question": "Pouvez-vous décrire un bug matériel/logiciel complexe que vous avez résolu ?",
                    "expected_answer": "Structurer la réponse : Symptôme -> Hypothèses -> Outils d'investigation (GDB, oscilloscope, logs) -> Résolution et non-régression.",
                    "tip": "Soignez la clarté de votre démarche analytique."
                },
                {
                    "question": f"Pourquoi avez-vous choisi de postuler chez {job.get('company')} plutôt que chez un concurrent ?",
                    "expected_answer": "Connaissance précise des projets de l'entreprise, de son positionnement R&D ou industriel et de ses technologies cibles.",
                    "tip": "Montrez votre veille technologique."
                }
            ]

letter_generator = LetterGeneratorService()

