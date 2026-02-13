import httpx
from .settings import settings
from .prompt import build_prompt

def _mock_report(payload: dict) -> str:
    # Sortie déterministe pour la CI
    decision = payload["decision"]
    risk = payload["risk_score"]
    fraud = payload["fraud_score"]
    rule = payload["policy_rule"]

    exp = payload.get("explanations_preview", {})
    credit_feats = exp.get("credit_top_features", [])[:3]
    fraud_feats = exp.get("fraud_top_features", [])[:3]

    def bullets(items):
        return "\n".join([f"- {x.get('feature')}: impact {x.get('impact')}" for x in items]) or "- information non disponible"

    action = {
        "ACCEPT": "Poursuivre le processus standard.",
        "REVIEW": "Déclencher une revue humaine et demander pièces justificatives si nécessaire.",
        "REJECT": "Refuser ou demander un dossier renforcé selon la politique interne.",
        "ALERT": "Bloquer/mettre en attente et déclencher une vérification anti-fraude.",
    }[decision]

    return (
        f"Décision: {decision} (risk={risk:.3f}, fraud={fraud:.3f}).\n"
        f"Règle appliquée: {rule}\n"
        f"Facteurs crédit principaux:\n{bullets(credit_feats)}\n"
        f"Facteurs fraude principaux:\n{bullets(fraud_feats)}\n"
        f"Action recommandée: {action}"
    )

async def _ollama_report(payload: dict) -> str:
    prompt = build_prompt(payload)
    url = f"{settings.ollama_base_url}/api/generate"
    body = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, json=body)
        r.raise_for_status()
        data = r.json()
        return data.get("response", "").strip() or "information non disponible"

async def generate_report(payload: dict) -> str:
    prov = settings.agent_provider.lower()
    if prov == "mock":
        return _mock_report(payload)
    if prov == "ollama":
        return await _ollama_report(payload)

    # Placeholder for future providers
    return _mock_report(payload)
