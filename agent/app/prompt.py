def build_prompt(payload: dict) -> str:
    """
    Anti-hallucination prompt:
    - Use only provided data
    - No invented facts
    - Provide short, structured output
    """
    decision = payload["decision"]
    risk = payload["risk_score"]
    fraud = payload["fraud_score"]
    rule = payload["policy_rule"]
    versions = payload.get("model_versions", {})
    exp = payload.get("explanations_preview", {})

    credit_feats = exp.get("credit_top_features", [])
    fraud_feats = exp.get("fraud_top_features", [])

    FEATURE_MAP = {
        "credit_history_length_months": "Ancienneté crédit",
        "employment_status": "Statut emploi",
        "income_annual": "Revenu annuel",
        "late_payments_12m": "Retards paiement (12m)",
        "debt_to_income": "Ratio Endettement",
        "is_new_device": "Nouvel appareil",
        "hour": "Heure transaction",
        "distance_from_home_km": "Distance domicile",
        "num_open_accounts": "Comptes ouverts",
        "age": "Âge",
        "amount": "Montant",
        "merchant_category": "Catégorie marchand",
        "country": "Pays"
    }

    def fmt_feats(feats):
        return ", ".join([f'{FEATURE_MAP.get(x.get("feature"), x.get("feature"))} ({x.get("impact")})' for x in feats[:3]]) or "n/a"

    return f"""
Tu es un assistant IA pour un système d'aide à la décision bancaire.
IMPORTANT:
- N'utilise QUE les informations fournies.
- N'invente PAS de raisons, de chiffres, ni de données client.
- Si une information manque, dis "information non disponible".
- Reste concis (6-10 lignes max), ton professionnel.

Données:
- decision: {decision}
- risk_score: {risk:.3f}
- fraud_score: {fraud:.3f}
- policy_rule: {rule}
- model_versions: {versions}
- credit_top_features: {fmt_feats(credit_feats)}
- fraud_top_features: {fmt_feats(fraud_feats)}

Sortie attendue (FR):
1) Résumé de décision (1 phrase)
2) Principaux facteurs (2-3 bullets)
3) Action recommandée (1 phrase)
""".strip()
