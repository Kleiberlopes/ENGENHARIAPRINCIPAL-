"""
Projeto Enriquecer — MVP de orquestracao de agentes de marketing.

Servidor FastAPI em http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from models.schemas import (
    CEOGoal,
    ChatMessage,
    EngineRunResponse,
    FunnelStage,
)
from core.engine import get_engine
from database.db import get_db

DASHBOARD = Path(__file__).resolve().parent / "dashboard" / "index.html"

app = FastAPI(
    title="Projeto Enriquecer — Orquestrador de Agentes de Marketing",
    description=(
        "Cérebro (orquestrador) -> Executores (Pesquisa/Copy/Trafego) -> "
        "Funil -> Venda -> Analista -> Nova Decisão do Cérebro."
    ),
    version="0.1.0",
)


@app.get("/", include_in_schema=False)
def dashboard():
    """Painel profissional de arquitetura, estudo e avaliação."""
    return FileResponse(DASHBOARD, media_type="text/html; charset=utf-8")


@app.get("/api", tags=["sistema"])
def api_index():
    return {
        "status": "ok",
        "servidor": "Projeto Enriquecer",
        "url": "http://127.0.0.1:8000",
        "painel": "http://127.0.0.1:8000/",
        "docs": "http://127.0.0.1:8000/docs",
        "endpoints": {
            "GET /": "Painel de arquitetura e avaliação (HTML)",
            "GET /api/overview": "KPIs + logs agregados para o painel",
            "POST /engine/run": "Dispara a engrenagem completa (meta do CEO)",
            "POST /funnel/lead": "Captura um lead no funil",
            "POST /funnel/chat": "Conversa natural via Agente Comercial",
            "POST /checkout": "Simula transacao e registra venda",
            "GET /analyst/report": "Ultimo relatorio do Analista (ROI/CAC/Conversao)",
            "GET /logs": "Log de execucao da ultima rodada",
            "GET /leads": "Jornada dos leads",
            "GET /sales": "Vendas registradas",
        },
    }


@app.get("/api/overview", tags=["sistema"])
def api_overview():
    """Dados agregados para o painel: relatorio, logs recentes e contadores."""
    db = get_db()
    reports = db.list_reports()
    leads = db.list_leads()
    sales = db.list_sales()
    logs = db.list_logs()[-40:]
    return {
        "relatorio": reports[-1] if reports else None,
        "logs": logs,
        "counts": {
            "leads": len(leads),
            "sales": len(sales),
            "logs": len(db.list_logs()),
            "reports": len(reports),
        },
    }


# ------------------------------------------------------------------ #
# ENGENHARIA PRINCIPAL — disparar a "Engrenagem" via JSON
# ------------------------------------------------------------------ #
@app.post("/engine/run", response_model=EngineRunResponse, tags=["engrenagem"])
def engine_run(goal: CEOGoal, n_leads: int = 20):
    """
    Ciclo completo:
    Meta do CEO -> Cérebro -> Executores -> Funil -> Venda -> Analista
    -> Nova Decisão do Cérebro.
    """
    engine = get_engine()
    resultado = engine.run(goal, n_leads=n_leads)
    return resultado


@app.get("/logs", tags=["engrenagem"])
def get_logs(run_id: str | None = None):
    db = get_db()
    return {"logs": db.list_logs(run_id)}


# ------------------------------------------------------------------ #
# FUNIL / COMERCIAL / CHECKOUT
# ------------------------------------------------------------------ #
@app.post("/funnel/lead", tags=["funil"])
def create_lead(nome: str = "Lead Manual", origem: str = "Direto"):
    engine = get_engine()
    lead = engine.funnel.capture(nome, origem)
    return lead.model_dump()


@app.post("/funnel/chat", tags=["funil"])
def funnel_chat(msg: ChatMessage):
    engine = get_engine()
    lead = engine.db.get_lead(msg.lead_id)
    if lead is None:
        return JSONResponse(status_code=404, content={"erro": "lead nao encontrado"})
    stage = FunnelStage(lead["stage"])
    reply = engine.commercial.reply(msg.lead_id, msg.mensagem, stage)
    engine.funnel.advance(msg.lead_id, reply)
    return reply.model_dump()


@app.post("/checkout", tags=["checkout"])
def checkout(lead_id: int, valor: float = 100.0, canal: str = "Meta Ads"):
    engine = get_engine()
    venda = engine.checkout.pay(lead_id, valor, canal)
    return venda.model_dump()


# ------------------------------------------------------------------ #
# ANALISTA
# ------------------------------------------------------------------ #
@app.get("/analyst/report", tags=["analista"])
def last_report():
    db = get_db()
    reports = db.list_reports()
    return {"relatorio": reports[-1] if reports else None}


@app.get("/leads", tags=["funil"])
def list_leads():
    db = get_db()
    return {"leads": db.list_leads()}


@app.get("/sales", tags=["checkout"])
def list_sales():
    db = get_db()
    return {"vendas": db.list_sales()}


if __name__ == "__main__":
    import uvicorn

    print("Projeto Enriquecer rodando em http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
