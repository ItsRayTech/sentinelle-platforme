from fastapi import FastAPI
from .schemas import AgentRequest, AgentResponse
from .providers import generate_report
from .settings import settings

app = FastAPI(title="Decision Agent")

@app.get("/health")
def health():
    return {"status": "ok", "provider": settings.agent_provider}

@app.post("/report", response_model=AgentResponse)
async def report(payload: AgentRequest):
    text = await generate_report(payload.model_dump())
    return AgentResponse(report_summary=text)
