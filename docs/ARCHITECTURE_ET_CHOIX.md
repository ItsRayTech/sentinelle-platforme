# 🧭 Architecture & Choix Techniques

Ce document détaille la philosophie, l'architecture et les décisions techniques du projet **Sentinelle**. Il sert de référence pour comprendre le fonctionnement interne de la plateforme et les motivations derrière chaque brique technologique.

---

## 1. Vision du Projet 🎯

**Sentinelle** est une plateforme de décision temps réel conçue pour l'évaluation du risque de crédit et la détection de fraude. Elle répond à un besoin critique des institutions financières : **automatiser les décisions à faible risque tout en gardant le contrôle humain sur les cas complexes**, le tout dans un cadre réglementaire strict (RGPD, AI Act).

**Piliers du projet :**
1.  **Temps réel** : API optimisée pour des réponses < 200ms.
2.  **Hybride** : Combinaison de règles métiers déterministes et de modèles Machine Learning probabilistes.
3.  **Human-in-the-loop** : L'IA propose une décision, l'humain valide les cas ambigus ("Zone Grise").
4.  **Explicabilité** : Chaque décision est justifiée par SHAP et traduite en langage naturel par une IA Générative.

---

## 2. Architecture Technique 🏗️

Le système repose sur une architecture micro-services isolés via Docker :

1.  **API Gateway (FastAPI)** : Point d'entrée unique. Elle orchestre la validation des données (Pydantic), l'interrogation des modèles ML et l'application des politiques de décision.
2.  **Moteur de Scoring (Scikit-Learn / XGBoost)** :
    *   **Crédit (Supervisé)** : Régression Logistique pour sa transparence et sa robustesse.
    *   **Fraude (Non-supervisé)** : Isolation Forest pour la détection d'anomalies (fraudes inconnues).
3.  **Agent Explicatif (LLM)** : Service dédié qui consomme les scores bruts et les valeurs SHAP pour générer un rapport narratif en français.
4.  **Observabilité (Grafana/Prometheus/MLflow)** : Stack de monitoring pour suivre la performance des modèles (Data Drift) et la santé des services en production.

---

## 3. Justification des Choix Techniques 💡

Chaque technologie a été choisie pour répondre à une contrainte spécifique :

### 🐍 Python & FastAPI
*   **Pourquoi ?** Python est le standard en Data Science. FastAPI offre la performance (asynchrone) nécessaire pour le temps réel et une sécurité accrue grâce à la validation stricte des types (Pydantic).

### 🤖 Modèles ML : Simplicité vs Complexité
*   **Risque Crédit (Régression Logistique)** : Choisi pour son **interprétabilité native**. Dans le domaine bancaire, pouvoir expliquer pourquoi un crédit est refusé est une obligation légale.
*   **Fraude (Isolation Forest)** : Choisi pour sa capacité à détecter les **anomalies** (outliers) sans avoir besoin d'un historique de fraudes étiqueté, souvent rare ou obsolète.

### ⚖️ SHAP (Shapley Additive Explanations)
*   **Pourquoi ?** Fournit une mesure mathématiquement rigoureuse de la contribution de chaque variable au score final. Indispensable pour l'explicabilité locale ("Pourquoi ce client spécifique a été rejeté ?").

### 🐳 Docker & Architecture Conteneurisée
*   **Pourquoi ?** Garantit la reproductibilité des environnements (Dev, Test, Prod) et facilite le déploiement. Élimine les problèmes de dépendances ("Works on my machine").

---

## 4. Défis Techniques & Solutions ✨

### Tendre vers l'Explicabilité Totale
*   **Problème** : Les scores de probabilité (ex: 0.76) sont abstraits pour les conseillers bancaires.
*   **Solution** : Intégration d'un **Agent LLM** avec un prompt d'ingénierie strict ("Anti-hallucination"). L'IA traduit les données techniques SHAP en phrases claires en français ("Le revenu est le facteur principal du refus").

### Gestion des Cas Limites (Edge Cases)
*   **Problème** : L'automatisation à 100% présente des risques éthiques et financiers.
*   **Solution** : Implémentation d'une logique de **"Zone Grise" (Review)**. Si le score de risque est intermédiaire, le système ne tranche pas mais envoie le dossier en révision humaine. C'est le principe du "Human-in-the-loop".

### Interface Utilisateur "Non-Tech"
*   **Problème** : Les parties prenantes métier ne peuvent pas tester une API via Swagger/Curl.
*   **Solution** : Développement d'un **Dashboard Web (Jinja2)** avec thème corporate (Clair/Sombre) pour permettre aux équipes métier de tester visuellement les décisions et l'audit trail.

---

## 5. Conformité & Éthique 🛡️

Le projet intègre le "Compliance by Design" :

*   **Pseudonymisation (RGPD)** : Aucun identifiant direct n'est stocké. Les IDs clients sont hashés cryptographiquement.
*   **Transparence (AI Act)** : Système documenté (Model Card, Data Sheet) avec traçabilité complète des décisions (version du modèle, règle appliquée, horodatage).

---

## 6. Pistes d'Amélioration (Roadmap) 🚀

*   **Automatisation du Ré-entraînement** : Coupler la détection de drift (Grafana) à un pipeline Airflow pour relancer l'entraînement automatiquement.
*   **Scalabilité** : Migration vers Kubernetes (K8s) pour gérer la montée en charge horizontale des conteneurs API.
*   **Base de Données** : Passage de SQLite (MVP) à PostgreSQL pour la persistance en production.

---
*Document généré pour la documentation technique du projet Sentinelle.*
