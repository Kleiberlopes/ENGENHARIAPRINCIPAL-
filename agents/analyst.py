from __future__ import annotations

from typing import Any, Optional

from models.schemas import AnalystReport, CEOGoal, AgentName
from database.db import Database, get_db


class AnalystAgent:
    """
    Agente Analista — modulo de fechamento do loop.

    Calcula ROI, CAC e Taxa de Conversao a partir das vendas e do
    investimento, gera o relatorio e o devolve ao Agente Cerebro
    para que ele tome a nova decisao.
    """

    NAME = AgentName.ANALISTA

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or get_db()

    # ------------------------------------------------------------------ #
    # Metricas brutas
    # ------------------------------------------------------------------ #
    def _snapshot(self, investimento: float, leads: int) -> dict[str, Any]:
        sales = self.db.list_sales()
        receita = sum(s["valor"] for s in sales)
        vendas = len(sales)
        conversao = (vendas / leads) if leads > 0 else 0.0
        cac = (investimento / vendas) if vendas > 0 else float(investimento) if leads else 0.0
        roi = ((receita - investimento) / investimento) if investimento > 0 else 0.0
        return {
            "roi": round(roi, 4),
            "cac": round(cac, 2),
            "conversao": round(conversao, 4),
            "vendas": vendas,
            "receita": round(receita, 2),
            "investimento": round(investimento, 2),
            "leads": leads,
        }

    # ------------------------------------------------------------------ #
    # Geracao do relatorio + devolucao ao Cerebro
    # ------------------------------------------------------------------ #
    def analyze(
        self,
        goal: CEOGoal,
        investimento: float,
        leads: int,
        run_id: str = "local",
    ) -> AnalystReport:
        metrics = self._snapshot(investimento, leads)

        if metrics["roi"] >= 1.0 and metrics["conversao"] >= 0.05:
            recomendacao = (
                "Resultado positivo: manter rota atual e escalar orcamento "
                "nos canais de melhor desempenho."
            )
        elif metrics["vendas"] == 0:
            recomendacao = (
                "Zero vendas: revisar copy e qualificacao dos leads antes "
                "de aumentar investimento."
            )
        elif metrics["cac"] > goal.ticket_medio * 0.5:
            recomendacao = (
                f"CAC ({metrics['cac']:.2f}) acima de 50% do ticket "
                f"({goal.ticket_medio:.2f}): cortar canais caros e testar novos angulos."
            )
        else:
            recomendacao = (
                "Conversao abaixo do alvo (5%): reforcar a etapa de Educacao "
                "do funil e a prova social na copy."
            )

        report = AnalystReport(
            roi=metrics["roi"],
            cac=metrics["cac"],
            conversao=metrics["conversao"],
            vendas=metrics["vendas"],
            receita=metrics["receita"],
            investimento=metrics["investimento"],
            leads=metrics["leads"],
            recomendacao=recomendacao,
            ajustes_sugeridos={
                "ticket_medio": goal.ticket_medio,
                "meta": goal.meta,
            },
        )

        self.db.save_report(run_id, metrics | {"recomendacao": recomendacao})

        print(
            f"[ANALISTA] run={run_id} ROI={report.roi:.2f} "
            f"CAC={report.cac:.2f} Conv={report.conversao:.2%} "
            f"Vendas={report.vendas} Receita={report.receita:.2f}"
        )
        print(f"[ANALISTA] Recomendacao: {report.recomendacao}")

        return report

    def send_to_brain(self, report: AnalystReport, brain: Any) -> Any:
        """Devolve o relatorio ao Cerebro -> gera NOVA decisao (fecha o loop)."""
        print("[ANALISTA] Enviando relatorio para o Agente Cerebro...")
        decision = brain.process_feedback(report)
        return decision
