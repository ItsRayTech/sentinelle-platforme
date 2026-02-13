# Documentation de Conformité IA

## AI Act (Haut Risque - Approche Portefeuille)

*   **Logging / Traçabilité** : ✅ (Logs de décision + Versioning de modèle)
*   **Documentation Technique** : ✅ (Carte du Modèle + Fiche de Données)
*   **Explicabilité** : ✅ (Importance globale des features + SHAP Local)
*   **Gouvernance** : ✅ (Couche de politique + Flux de revue humaine)
*   **Robustesse** : ✅ (Validation Pydantic + Tests unitaires)
*   **Supervision Humaine** : ✅ (Point de terminaison REVIEW + Capacité de surcharge)

## Gestion des Risques IA

- Identification des risques liés aux décisions automatisées.
- Évaluation de l'impact potentiel sur les clients.
- Mise en place de seuils conservateurs (Zone REVIEW).
- Possibilité d'intervention humaine avant décision finale.

## Surveillance Continue

- Monitoring des performances (AUC, recall).
- Détection de drift des features.
- Analyse périodique des décisions REVIEW.
- Audit trimestriel des overrides humains.

## RGPD / CNIL

*   **Minimisation** : ✅ (Seuls les champs de données nécessaires sont collectés)
*   **Pseudonymisation** : ✅ (IDs clients hashés avec sel avant stockage)
*   **Transparence** : ✅ (Génération de rapport + Endpoint d'explication)
*   **Contestabilité** : ✅ (Mécanisme de revue humaine disponible)
*   **Rétention** : ✅ (Logs conservés uniquement pour la période d'audit - configurable)
*   **Prise de Décision Automatisée** : ✅ (Garde-fous : "Pas uniquement automatisé" pour les décisions critiques)
