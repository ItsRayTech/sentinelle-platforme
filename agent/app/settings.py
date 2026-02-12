from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    agent_provider: str = "mock"  # mock | ollama | openai
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "llama3.1"

    # If you later use OpenAI / Mistral
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""

settings = Settings()
