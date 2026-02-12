from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Sentinelle - Plateforme de Décision Risque & Fraude"
    environment: str = "dev"

    # Database
    database_url: str = "sqlite:///./app.db"

    # Policy thresholds (tweak later)
    fraud_alert_threshold: float = 0.85
    risk_reject_threshold: float = 0.70
    risk_review_lower: float = 0.45
    risk_review_upper: float = 0.70

    # Pseudonymization
    client_id_salt: str = "CHANGE_ME_SALT"

    # Agent (optional, can remain disabled initially)
    agent_enabled: bool = False
    agent_base_url: str = "http://agent:9000"

settings = Settings()
