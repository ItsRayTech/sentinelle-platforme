# Carte du Modèle : Risque & Fraude

## Version
- **Version du Modèle** : credit_risk:v1 / fraud:v1
- **Date** : 2026-02
- **Statut** : MVP (Scoring déterministe baseline)

## Objectif
Évaluer le risque de crédit (probabilité de défaut) et le risque de fraude (détection d'anomalies) pour les transactions financières en temps réel.

## Jeux de Données
*   **Données d'entraînement** : [Nom du Dataset Interne, ex: Historique Crédit Pseudonymisé 2023-2025] ou [Dataset de Référence Synthétique]
*   **Licence** : Propriétaire / Évaluation uniquement.

## Variables Utilisées
*   **Client** : `age`, `income_annual` (revenu annuel), `employment_status` (statut emploi), `debt_to_income` (taux endettement), `credit_history_length` (historique crédit), `num_open_accounts` (comptes ouverts), `late_payments_12m` (retards paiement 12m)
*   **Transaction** : `amount` (montant), `merchant_category` (catégorie marchand), `country` (pays), `hour` (heure), `is_new_device` (nouvel appareil), `distance_from_home_km` (distance domicile)
*   **Justification** : Minimisation des données appliquée (pas de noms, adresses ou identifiants directs) pour respecter le RGPD.

## Hypothèses
- Les données d'entraînement sont représentatives des comportements clients 2023-2025.
- Les labels de défaut/fraude sont considérés comme fiables.
- Les variables utilisées sont suffisantes pour estimer le risque sans information identifiante directe.

## Architecture du Modèle
*   **Risque Crédit** : Régression Logistique (baseline) + XGBoost (cible).
*   **Détection Fraude** : Isolation Forest / Détection d'Anomalies Non Supervisée (ou XGBoost si labels existants).

## Métriques (Cible)
*   **AUC** : > 0.85
*   **Recall (Défaut)** : > 0.70
*   **Calibration** : Score de Brier surveillé.

## Équité & Biais
- Surveillance des métriques par segment d'âge.
- Analyse comparative TPR/FPR par groupe socio-démographique (proxy).
- Rapport d'équité généré à chaque réentraînement.

## Limites
*   Biais potentiel dans les proxys socio-économiques (surveillé via rapports d'équité).
*   Performance dégradée sur les nouveaux types d'appareils (démarrage à froid).

## Scénarios de Défaillance
- Données manquantes ou corrompues.
- Drift important sur nouvelles catégories marchandes.
- Fraude organisée non représentée dans le dataset.

## Conditions d'Utilisation
*   **Système d'Aide à la Décision** : destiné aux flux de travail "Human-in-the-Loop" (Homme dans la boucle).
*   **Pas Uniquement Automatisé** : Les décisions à haut risque doivent pouvoir être révisées par un opérateur humain.

## Monitoring
*   Analyse mensuelle de la dérive des features (data drift).
*   Calendrier de réentraînement trimestriel.
