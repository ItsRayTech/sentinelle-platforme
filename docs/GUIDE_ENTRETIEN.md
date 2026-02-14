# 🎓 Guide d'Entretien : Projet Sentinelle-Plateforme

Ce document est conçu pour t'aider à présenter **Sentinelle** lors d'un entretien technique ou fonctionnel. Il décortique chaque aspect du projet avec un angle pédagogique ("Pourquoi on a fait ça ?") et technique ("Comment ça marche ?").

---

## 1. Le Pitch (L'accroche) 🎤

**"C'est quoi Sentinelle ?"**

> "Sentinelle-Plateforme est une plateforme de décision temps réel pour l'évaluation du risque de crédit et la détection de fraude. C'est une solution 'Enterprise-Ready' qui combine l'analyse quantitative classique (Scoring) avec l'analyse comportementale (Fraude) et l'IA Générative pour l'explicabilité."

**Mots-clés à placer :**
*   **Temps réel** (API < 200ms)
*   **Hybride** (Règles métiers + Machine Learning)
*   **Human-in-the-loop** (L'IA propose, l'humain valide les cas complexes)
*   **Explicabilité** (SHAP + LLM)
*   **Conformité** (RGPD / AI Act)

---

## 2. Architecture Technique (La vue d'ensemble) 🏗️

Si on te demande de dessiner l'architecture, visualise ces 4 blocs :

1.  **L'API Gateway (FastAPI)** : C'est le chef d'orchestre. Elle reçoit la demande, interroge les modèles, vérifie les règles, et stocke le résultat.
2.  **Le Moteur ML (Scikit-Learn / XGBoost)** :
    *   Un modèle supervisé pour le **Crédit** (est-ce qu'il va payer ?).
    *   Un modèle non-supervisé pour la **Fraude** (est-ce une anomalie ?).
3.  **L'Agent Explicatif (LLM)** : Il prend les scores bruts et les valeurs SHAP pour rédiger un rapport en français ("Le client est rejeté car son ratio dette/revenu est trop élevé...").
4.  **L'Observabilité (Grafana/Prometheus)** :
    *   **Monitoring "Senior++" (IaC)** : On ne configure rien à la main. Tout est code.
    *   **Producer** : L'API expose des métriques métier (`decision_total_count`, `model_latency`) via Prometheus Client.
    *   **Scraper** : Prometheus collecte ces données toutes les 5s.
    *   **Viewer** : Grafana est pré-configuré (provisioning) pour afficher un dashboard JSON versionné. Cela garantit que si on redéploie l'infra, on ne perd pas nos graphiques.

---

## 3. Choix Techniques & Justifications 💡

En entretien, on te demandera "Pourquoi X et pas Y ?". Voici les réponses :

### 🐍 Pourquoi Python & FastAPI ?
*   **Performance** : FastAPI est asynchrone, parfait pour gérer beaucoup de requêtes simultanées.
*   **Typage fort (Pydantic)** : On valide les données à l'entrée. Si l'âge est une chaîne de caractères ("trente"), ça plante proprement avant même d'arriver au modèle. Sécurité et robustesse.

### 🤖 Pourquoi ces modèles ML ?
*   **Pour le Crédit (Logistic Regression / XGBoost)** : On a besoin d'**interprétabilité**. Une banque doit pouvoir dire pourquoi un crédit est refusé. La régression logistique est transparente.
*   **Pour la Fraude (Isolation Forest)** : La fraude change tout le temps. Un modèle supervisé apprendrait "les fraudes d'hier". L'*Isolation Forest* détecte les **anomalies** (ce qui sort de l'ordinaire), ce qui est plus robuste pour détecter les *nouveaux* types de fraudes.

### ⚖️ Pourquoi SHAP (Shapley Additive Explanations) ?
*   C'est le standard de l'industrie pour l'explicabilité. Ça nous dit *exactement* combien chaque variable (revenu, âge, dette) a contribué au score final, positivement ou négativement.

### 🐳 Pourquoi Docker ?
*   Pour la **reproductibilité**. "Ça marche sur ma machine" n'est pas une réponse acceptable. Avec Docker, l'environnement est iso-prod du début à la fin.

---

## 4. Les Challenges Résolus (Pour briller) ✨

Raconte une histoire sur les difficultés rencontrées :

*   **Le Challenge de l'Explicabilité** : "Les scores bruts (0.76) ne parlent pas aux conseillers bancaires. J'ai intégré un **Agent LLM** qui traduit ces maths en phrases claires en français. J'ai dû travailler le *Prompt Engineering* pour que l'IA n'hallucine pas (ne pas inventer de chiffres)."
*   **La Gestion des Cas Limites** : "L'automatisation à 100% est dangereuse. J'ai implémenté une logique de 'Zone Grise' (Review). Si le score est moyen, on ne rejette pas automatiquement, on envoie à un humain. C'est crucial pour l'éthique et la conformité."
*   **L'Interface Utilisateur** : "Je ne voulais pas d'un Swagger gris. J'ai développé un Dashboard complet (Thème Light Corporate / Dark Mode) pour que les parties prenantes non-techniques puissent tester et visualiser les décisions."

---

## 5. Conformité & Éthique (Le bonus Senior) 🛡️

Montre que tu ne fais pas que du code, mais que tu comprends le métier :

*   **RGPD** : "J'ai appliqué la **pseudonymisation**. On ne stocke pas le nom du client, mais un hash de son ID."
*   **AI Act** : "Le système est documenté (Model Card, Data Sheet). Il y a toujours un humain dans la boucle pour les décisions critiques."

---

## 6. Questions Types auxquelles s'attendre ❓

**Q: Comment gères-tu le ré-entraînement du modèle ?**
*   **R:** "Actuellement c'est un script manuel, mais grâce à MLflow, on tracke toutes les métriques. L'étape suivante serait d'automatiser le ré-entraînement via Airflow si on détecte une dérive (Data Drift) dans Grafana."

**Q: Si l'API est lente, que fais-tu ?**
*   **R:** "Je regarde d'abord les métriques Prometheus pour voir si c'est le modèle ML ou la base de données qui bloque. Si c'est le modèle, je peux optimiser l'inférence (ONNX) ou scaler horizontalement les conteneurs API avec Kubernetes."

**Q: Comment gères-tu le monitoring en production ?**
*   **R:** "Le monitoring est entièrement **provisionné as code**. Les métriques métier sont exposées par l'API, scrappées par Prometheus, et le dashboard Grafana est versionné en JSON. C'est reproductible, audit-able et iso-prod immédiat."

**Q: Comment sécurises-tu l'application ?**
*   **R:** "Validation stricte des entrées (Pydantic), pas de données sensibles en clair (Hash), et isolation des services via Docker Network."
