from __future__ import annotations

from typing import Any

from models.schemas import (
    AgentName,
    AnalystReport,
    BrainDecision,
    CEOGoal,
    EngineRunResponse,
    FunnelStage,
    TaskDispatch,
)
from agents import (
    BrainAgent,
    AnalystAgent,
    ResearchAgent,
    CopyAgent,
    TrafficAgent,
    CommercialAgent,
)
from core.funnel import SalesFunnel
from core.checkout import Checkout
from database.db import get_db


class Engine:
    """
    Motor da engrenagem: acopla Cerebro -> Executores -> Funil -> Venda
    -> Analista -> NOVA DECISAO do Cerebro (loop de feedback completo).

    Comunicacao entre agentes: chamadas de funcao internas.
    (para HTTP local, troque `_internal_executor` por `requests.post`)."""

    def __init__(self) -> None:
        self.db = get_db()
        self.brain = BrainAgent(executor=self._internal_executor)
        self.analyst = AnalystAgent(db=self.db)
        self.research = ResearchAgent()
        self.copy = CopyAgent()
        self.traffic = TrafficAgent()
        self.commercial = CommercialAgent()
        self.funnel = SalesFunnel(db=self.db)
        self.checkout = Checkout(db=self.db)

    # ------------------------------------------------------------------ #
    # Executor de agentes (chamada de funcao interna)
    # ------------------------------------------------------------------ #
    def _internal_executor(self, task: TaskDispatch) -> Any:
        mapping = {
            AgentName.PESQUISA: self.research.analyze,
            AgentName.COPY: self.copy.generate,
            AgentName.TRAFEGO: self.traffic.plan,
        }
        handler = mapping.get(task.agent)
        if handler is None:
            raise ValueError(f"Agente executor nao suportado: {task.agent}")
        return handler(task.payload)

    # ------------------------------------------------------------------ #
    # CICLO COMPLETO: Meta CEO -> ... -> Nova Decisao
    # ------------------------------------------------------------------ #
    def run(self, goal: CEOGoal, n_leads: int = 20) -> EngineRunResponse:
        # 1) Cerebro recebe a meta e roteia
        self.brain.reset(goal)
        context = self.brain.run_pipeline(goal)

        # 2) Funil: captacao + conversa comercial + checkout
        vendas = []
        for i in range(n_leads):
            lead = self.funnel.capture(nome=f"Lead {i + 1}", origem="Meta Ads")

            # Simulacao de conversa natural (2 mensagens do lead)
            r1 = self.commercial.reply(
                lead.lead_id, "Oi, tenho duvida sobre o produto", lead.stage
            )
            self.funnel.advance(lead.lead_id, r1)

            r2 = self.commercial.reply(
                lead.lead_id, "quero testar, quanto custa?", r1.stage
            )
            self.funnel.advance(lead.lead_id, r2)

            # ~60% dos leads qualificados compram (simulacao deterministica)
            if r2.qualificado and (i % 5 in (0, 1, 2, 3)):
                venda = self.checkout.pay(
                    lead.lead_id, valor=goal.ticket_medio, canal="Meta Ads"
                )
                vendas.append(venda)
                self.brain._log(AgentName.FUNIL, "Venda", f"lead={lead.lead_id} R${venda.valor}")
            else:
                if r2.stage == FunnelStage.CONVERSAO:
                    self.funnel.close_lost(lead.lead_id)
                    self.brain._log(AgentName.FUNIL, "Perdido", f"lead={lead.lead_id}")

        # 3) Analista calcula ROI/CAC/Conversao e devolve ao Cerebro
        investimento = goal.orcamento
        leads_total = self.db.conn.execute("SELECT COUNT(*) c FROM leads").fetchone()["c"]
        relatorio = self.analyst.analyze(
            goal, investimento=investimento, leads=leads_total, run_id=self.brain.run_id
        )
        self.brain._log(
            AgentName.ANALISTA,
            "Relatorio",
            f"roi={relatorio.roi} cac={relatorio.cac} conv={relatorio.conversao}",
        )

        # 4) Cerebro processa o feedback -> NOVA DECISAO (fecha o loop)
        decisao = self.analyst.send_to_brain(relatorio, self.brain)

        # Persistir log no SQLite
        for entry in self.brain.logs:
            self.db.log(
                self.brain.run_id, entry.step, entry.agent.value,
                entry.action, entry.detail, entry.status,
            )

        return EngineRunResponse(
            meta=goal.meta,
            rota=decisao.rota,
            logs=self.brain.logs,
            pesquisa=context.get("pesquisa"),
            copy_output=context.get("copy"),
            trafego=context.get("trafego"),
            vendas=vendas,
            relatorio=relatorio,
            decisao_final=decisao,
        )


_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = Engine()
    return _engine
