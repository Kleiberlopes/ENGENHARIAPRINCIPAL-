from __future__ import annotations

from typing import Any

from models.schemas import AgentName, CEOGoal, ResearchOutput


class ResearchAgent:
    """Agente Pesquisa — processa mercado, personas e angulos de venda."""

    NAME = AgentName.PESQUISA

    def analyze(self, payload: dict[str, Any]) -> ResearchOutput:
        goal = CEOGoal(**payload.get("goal", {}))
        ajustes = payload.get("ajustes", {})

        publico = goal.publico_alvo
        personas = [
            f"Dono(a) de negocio focado em {publico} que quer resultado rapido",
            f"Gestor(a) de marketing de {goal.produto} buscando escalar aquisicao",
            f"Empreendedor(a) iniciante que precisa de {goal.produto} com orcamento apertado",
        ]
        dores = [
            "Baixa conversao nas campanhas atuais",
            "CAC alto demais para o ticket medio",
            "Falta de tempo para produzir copy e criativos",
            "Dependencia de um unico canal de trafego",
        ]
        angulos = [
            f"Prova social: resultados com {goal.produto} em 30 dias",
            f"Economia de tempo: {goal.produto} automatiza o que consome horas",
            f"Garantia de risco zero: teste {goal.produto} e so pague se funcionar",
        ]
        canais = ["Meta Ads (Facebook/Instagram)", "Google Ads (Search)", "E-mail marketing"]

        if ajustes.get("acao") == "reduzir_cac":
            canais = ["Meta Ads (Facebook/Instagram)", "E-mail marketing"]
            angulos.insert(0, "Oferta de entrada com ticket baixo para aquecer o publico")

        resumo = (
            f"Analise para '{goal.meta}' ({goal.produto}): "
            f"{len(personas)} personas, {len(dores)} dores, {len(angulos)} angulos. "
            f"Canais sugeridos: {', '.join(canais)}."
        )
        print(f"[PESQUISA] {resumo}")
        return ResearchOutput(
            personas=personas,
            dores=dores,
            angulos_venda=angulos,
            canais_sugeridos=canais,
            resumo=resumo,
        )
