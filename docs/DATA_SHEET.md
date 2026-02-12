# Fiche de Données (Datasheet) pour Datasets Risque & Fraude

## Motivation
*   **But** : Entraîner des modèles pour l'évaluation du risque de crédit (classification) et la détection de fraude (détection d'anomalies/classification).
*   **Créateur** : Équipe Data Science Interne pour la Plateforme de Décision Risque.

## Base Légale (Simulation)
- Intérêt légitime (analyse de risque financier).
- Respect du principe de minimisation.

## Composition
*   **Instances** : ~50k transactions historiques/demandes de crédit (anonymisées/synthétiques).
*   **Champs** :
    *   `client_id` (hashé)
    *   `age`, `income_annual`, `employment_status`, `debt_to_income`, `credit_history_length`
    *   `transaction_amount`, `merchant_category`, `country`, `is_new_device`
    *   Cibles : `default_flag` (0/1), `is_fraud` (0/1)
*   **Sensibilité** : Contient des modèles comportementaux financiers. Aucune PII directe (noms, adresses exactes) incluse dans les sets d'entraînement.

## Processus de Collecte
*   **Source** : Logs bancaires agrégés de 2023-2025 (simulés pour le MVP).
*   **Pré-traitement** : Normalisation des valeurs numériques, encodage catégoriel, suppression des valeurs aberrantes.

## Politique de Conservation
- Données d'entraînement conservées 24 mois maximum (simulation).
- Logs décisionnels conservés 90 jours en environnement démo.

## Contrôles Qualité
- Vérification des valeurs extrêmes.
- Analyse des valeurs manquantes.
- Détection des distributions anormales avant entraînement.

## Usages
*   **Primaire** : Entraînement et validation des modèles de risque.
*   **Hors Périmètre** : Ciblage marketing, revente de données.

## Distribution
*   **Accès** : Restreint aux équipes Data Science et Conformité.
*   **Licence** : Propriétaire / usage interne uniquement.
