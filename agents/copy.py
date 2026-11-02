from __future__ import annotations

from typing import Any

from models.schemas import AgentName, CEOGoal, CopyOutput, ResearchOutput


class CopyAgent:
    """Agente Copy — gera textos de anuncios e pagina de vendas baseado na pesquisa."""

    NAME = AgentName.COPY

    def generate(self, payload: dict[str, Any]) -> CopyOutput:
        goal = CEOGoal(**payload.get("goal", {}))
        ctx = payload.get("context", {})
        pesquisa = ResearchOutput(**ctx["pesquisa"]) if "pesquisa" in ctx else ResearchOutput()
        ajustes = payload.get("ajustes", {})

        angulo = pesquisa.angulos_venda[0] if pesquisa.angulos_venda else f"{goal.produto}"
        dor = pesquisa.dores[0] if pesquisa.dores else "resultados inconsistentes"

        urgencia = ""
        if ajustes.get("copy") == "reforcar_urgencia_e_prova_social" or ajustes.get("acao") == "otimizar_conversao":
            urgencia = " Vagas limitadas — garanta a sua agora."

        headlines = [
            f"Pare de perder dinheiro com {dor}",
            f"{goal.produto}: {angulo}",
            f"Como {goal.publico_alvo} esta faturando com {goal.produto}",
        ]

        anuncios = [
            (
                f"{angulo}.{urgencia} "
                f"Descubra como {goal.publico_alvo} resolve '{dor}' com {goal.produto}. "
                f"Clique e comece hoje."
            ),
            (
                f"Voce ainda luta com '{dor}'? "
                f"{goal.produto} foi feito para {goal.publico_alvo}. "
                f"Resultados em poucas semanas. {urgencia}".strip()
            ),
            (
                f"Ultima chance: {angulo}. "
                f"+ de {goal.publico_alvo} ja usam {goal.produto}. "
                f"Garanta sua vaga antes do encerramento.{urgencia}"
            ),
        ]

        pagina = (
            f"# {goal.produto} — {goal.meta}\n\n"
            f"## O problema\nVoce esta cansado de '{dor}'?\n\n"
            f"## A solucao\n{goal.produto} foi criado para {goal.publico_alvo} "
            f"que quer {goal.meta.lower()} sem complicacao.\n\n"
            f"## Por que agora?\n{angulo}.{urgencia}\n\n"
            f"## Garantia\nRisco zero por 7 dias. Se nao gostar, devolvemos 100%.\n\n"
            f"## Proximo passo\nClique no botao abaixo e garanta sua vaga.\n"
        )

        cta = "QUERO COMEÇAR AGORA" if not urgencia else "GARANTIR MINHA VAGA"

        resumo = f"Copy gerada: {len(anuncios)} anuncios, {len(headlines)} headlines, pagina de vendas + CTA '{cta}'."
        print(f"[COPY] {resumo}")
        return CopyOutput(
            anuncios=anuncios,
            pagina_vendas=pagina,
            headlines=headlines,
            cta=cta,
            resumo=resumo,
        )
