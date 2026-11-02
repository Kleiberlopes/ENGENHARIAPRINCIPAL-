from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class FunnelStage(str, Enum):
    CAPTACAO = "Captacao"
    EDUCACAO = "Educacao"
    CONVERSAO = "Conversao"
    VENDIDO = "Vendido"
    PERDIDO = "Perdido"


class AgentName(str, Enum):
    CEREBRO = "Cerebro"
    PESQUISA = "Pesquisa"
    COPY = "Copy"
    TRAFEGO = "Trafego"
    FUNIL = "Funil"
    COMERCIAL = "Comercial"
    CHECKOUT = "Checkout"
    ANALISTA = "Analista"


class CEOGoal(BaseModel):
    """Meta enviada pelo CEO ao Agente Cerebro."""

    meta: str = Field(..., description="Ex: 'Aumentar Vendas'")
    produto: str = Field(default="Produto X", description="Nome do produto/servico")
    orcamento: float = Field(default=1000.0, description="Orcamento total em BRL")
    ticket_medio: float = Field(default=100.0, description="Ticket medio em BRL")
    publico_alvo: str = Field(default="publico geral", description="Descric do publico")
    mes: int = Field(default=1, description="Mes de operacao para simulacao")


class TaskDispatch(BaseModel):
    """Tarefa delegada pelo Cerebro a um executor."""

    agent: AgentName
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)


class BrainDecision(BaseModel):
    """Decisao do Cerebro: roteamento + novas acoes apos feedback do Analista."""

    rota: list[AgentName] = Field(default_factory=list)
    motivo: str = ""
    ajustes: dict[str, Any] = Field(default_factory=dict)
    nova_meta: Optional[str] = None


class ExecutionLog(BaseModel):
    step: int
    agent: AgentName
    action: str
    detail: str = ""
    status: str = "OK"


class ResearchOutput(BaseModel):
    personas: list[str] = Field(default_factory=list)
    dores: list[str] = Field(default_factory=list)
    angulos_venda: list[str] = Field(default_factory=list)
    canais_sugeridos: list[str] = Field(default_factory=list)
    resumo: str = ""


class CopyOutput(BaseModel):
    anuncios: list[str] = Field(default_factory=list)
    pagina_vendas: str = ""
    headlines: list[str] = Field(default_factory=list)
    cta: str = ""
    resumo: str = ""


class TrafficOutput(BaseModel):
    publicos: list[str] = Field(default_factory=list)
    canais: list[str] = Field(default_factory=list)
    orcamento_por_canal: dict[str, float] = Field(default_factory=dict)
    lances: dict[str, float] = Field(default_factory=dict)
    resumo: str = ""


class LeadJourney(BaseModel):
    lead_id: int
    nome: str
    stage: FunnelStage = FunnelStage.CAPTACAO
    origem: str = ""
    interacoes: int = 0
    comprou: bool = False


class ChatMessage(BaseModel):
    lead_id: int
    mensagem: str


class CommercialReply(BaseModel):
    lead_id: int
    stage: FunnelStage
    resposta: str
    proxima_acao: str
    qualificado: bool = False


class SaleRecord(BaseModel):
    sale_id: int
    lead_id: int
    valor: float
    canal: str = ""
    status: str = "aprovada"


class AnalystReport(BaseModel):
    """Relatorio devolvido pelo Analista ao Cerebro."""

    roi: float
    cac: float
    conversao: float
    vendas: int
    receita: float
    investimento: float
    leads: int
    recomendacao: str
    ajustes_sugeridos: dict[str, Any] = Field(default_factory=dict)


class EngineRunResponse(BaseModel):
    """Resposta completa da execucao da engrenagem."""

    meta: str
    rota: list[AgentName]
    logs: list[ExecutionLog]
    pesquisa: Optional[ResearchOutput] = None
    copy_output: Optional[CopyOutput] = None
    trafego: Optional[TrafficOutput] = None
    vendas: list[SaleRecord] = Field(default_factory=list)
    relatorio: Optional[AnalystReport] = None
    decisao_final: Optional[BrainDecision] = None
