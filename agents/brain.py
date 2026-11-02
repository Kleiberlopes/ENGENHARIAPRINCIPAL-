from __future__ import annotations

import uuid
from typing import Any, Callable, Optional

from models.schemas import (
    AgentName,
    BrainDecision,
    CEOGoal,
    ExecutionLog,
    ResearchOutput,
    CopyOutput,
    TrafficOutput,
    AnalystReport,
    TaskDispatch,
)


class BrainAgent:
    """
    Agente Cerebro — orquestrador central.

    Recebe a meta do CEO, define a rota (roteamento), delega tarefas aos
    executores (Pesquisa -> Copy -> Trafego) e, ao receber o relatorio do
    Analista, toma uma NOVA decisao (loop de feedback).
    """

    NAME = AgentName.CEREBRO

    def __init__(self, executor: Optional[Callable[[TaskDispatch], Any]] = None) -> None:
        """`executor` recebe um TaskDispatch e executa o agente alvo
        (chamada de funcao interna ou HTTP local)."""
        self._executor = executor
        self.run_id: str = ""
        self.logs: list[ExecutionLog] = []
        self._step: int = 0
        self.goal: Optional[CEOGoal] = None
        self.last_decision: Optional[BrainDecision] = None
        self.last_report: Optional[AnalystReport] = None

    # ------------------------------------------------------------------ #
    # Log de execucao (impresso no terminal)
    # ------------------------------------------------------------------ #
    def _log(self, agent: AgentName, action: str, detail: str = "") -> None:
        self._step += 1
        entry = ExecutionLog(
            step=self._step, agent=agent, action=action, detail=detail, status="OK"
        )
        self.logs.append(entry)
        print(
            f"[CEREBRO][{self.run_id}] passo={entry.step:02d} "
            f"agente={agent.value} acao={action} | {detail}"
        )

    def reset(self, goal: CEOGoal) -> None:
        self.run_id = uuid.uuid4().hex[:8]
        self.logs = []
        self._step = 0
        self.goal = goal
        self.last_decision = None
        self.last_report = None

    # ------------------------------------------------------------------ #
    # ROTEAMENTO — logica central do Cerebro
    # ------------------------------------------------------------------ #
    def route(self, goal: CEOGoal) -> BrainDecision:
        """Define a rota de execucao a partir da meta do CEO."""
        meta = goal.meta.lower()

        if any(k in meta for k in ("venda", "vendas", "faturar", "converter", "receita")):
            rota = [AgentName.PESQUISA, AgentName.COPY, AgentName.TRAFEGO]
            motivo = "Meta de VENDAS: pesquisa -> copy -> trafego (funil completo)."
        elif any(k in meta for k in ("trafego", "lead", "leads", "captar", "captacao")):
            rota = [AgentName.PESQUISA, AgentName.TRAFEGO, AgentName.COPY]
            motivo = "Meta de TRAFEGO/LEADS: pesquisa -> trafego -> copy."
        elif any(k in meta for k in ("copy", "texto", "conteudo", "pagina")):
            rota = [AgentName.PESQUISA, AgentName.COPY]
            motivo = "Meta de COPY: pesquisa -> copy."
        elif any(k in meta for k in ("marca", "awareness", "visibilidade")):
            rota = [AgentName.PESQUISA, AgentName.COPY, AgentName.TRAFEGO]
            motivo = "Meta de MARCA: pesquisa -> copy -> trafego."
        else:
            rota = [AgentName.PESQUISA, AgentName.COPY, AgentName.TRAFEGO]
            motivo = "Meta generica: usando pipeline padrao pesquisa -> copy -> trafego."

        decision = BrainDecision(rota=rota, motivo=motivo)
        self.last_decision = decision
        self._log(self.NAME, "Roteamento", f"rota={[a.value for a in rota]} | {motivo}")
        return decision

    # ------------------------------------------------------------------ #
    # DELEGACAO aos executores
    # ------------------------------------------------------------------ #
    def dispatch(self, task: TaskDispatch) -> Any:
        """Delega uma tarefa ao executor (interno ou HTTP)."""
        self._log(task.agent, task.action, f"payload_keys={list(task.payload.keys())}")
        if self._executor is None:
            raise RuntimeError("Cerebro sem executor configurado.")
        return self._executor(task)

    def run_pipeline(self, goal: CEOGoal) -> dict[str, Any]:
        """Executa a rota completa: executores em sequencia."""
        decision = self.route(goal)
        context: dict[str, Any] = {"goal": goal}

        for agent in decision.rota:
            action = {
                AgentName.PESQUISA: "analise_mercado",
                AgentName.COPY: "gerar_copy",
                AgentName.TRAFEGO: "definir_trafego",
            }.get(agent, "executar")

            payload = {
                "goal": goal.model_dump(),
                "context": {
                    k: (v.model_dump() if hasattr(v, "model_dump") else v)
                    for k, v in context.items()
                },
                "ajustes": decision.ajustes,
            }
            result = self.dispatch(TaskDispatch(agent=agent, action=action, payload=payload))

            key = {
                AgentName.PESQUISA: "pesquisa",
                AgentName.COPY: "copy",
                AgentName.TRAFEGO: "trafego",
            }.get(agent, agent.value)
            context[key] = result
            self._log(agent, "Concluido", f"output={key}")

        return context

    # ------------------------------------------------------------------ #
    # FEEDBACK DO ANALISTA -> NOVA DECISAO (segunda metade do loop)
    # ------------------------------------------------------------------ #
    def process_feedback(self, report: AnalystReport) -> BrainDecision:
        """O Analista devolve ROI/CAC/Conversao e o Cerebro decide o proximo passo."""
        self.last_report = report
        ajustes: dict[str, Any] = {}
        nova_meta: Optional[str] = None
        rota: list[AgentName] = []

        if report.roi < 1.0:
            ajustes["acao"] = "otimizar_conversao"
            ajustes["copy"] = "reforcar_urgencia_e_prova_social"
            ajustes["trafego"] = "cortar_canais_com_cac_alto"
            nova_meta = "Otimizar Vendas: reduzir CAC e aumentar conversao"
            rota = [AgentName.COPY, AgentName.TRAFEGO, AgentName.ANALISTA]
            motivo = (
                f"ROI={report.roi:.2f} < 1.0 -> refazer copy e cortar canais caros."
            )
        elif report.conversao < 0.05:
            ajustes["acao"] = "melhorar_funil"
            ajustes["funil"] = "reforcar_etapa_de_educacao"
            nova_meta = "Aumentar Conversao do funil"
            rota = [AgentName.PESQUISA, AgentName.COPY, AgentName.ANALISTA]
            motivo = f"Conversao={report.conversao:.2%} baixa -> reforcar educacao."
        elif report.cac > goal_safe(self.goal).ticket_medio * 0.5:
            ajustes["acao"] = "reduzir_cac"
            ajustes["trafego"] = "redirecionar_orcamento_para_melhor_canal"
            nova_meta = "Reduzir CAC mantendo volume"
            rota = [AgentName.TRAFEGO, AgentName.ANALISTA]
            motivo = f"CAC={report.cac:.2f} alto vs ticket -> realocar verba."
        else:
            ajustes["acao"] = "escalar"
            ajustes["trafego"] = "aumentar_orcamento_em_15_por_cento"
            nova_meta = "Escalar Vendas com resultado atual"
            rota = [AgentName.TRAFEGO, AgentName.COPY, AgentName.ANALISTA]
            motivo = (
                f"ROI={report.roi:.2f} saudavel -> escalar o que funciona."
            )

        decision = BrainDecision(rota=rota, motivo=motivo, ajustes=ajustes, nova_meta=nova_meta)
        self.last_decision = decision
        self._log(
            self.NAME,
            "Novapos_feedback_analista",
            f"roi={report.roi:.2f} cac={report.cac:.2f} conv={report.conversao:.2%} | {motivo}",
        )
        return decision


def goal_safe(goal: Optional[CEOGoal]) -> CEOGoal:
    return goal if goal is not None else CEOGoal(meta="default")
