from __future__ import annotations

from typing import Any

from models.schemas import AgentName, CEOGoal, ResearchOutput, TrafficOutput


class TrafficAgent:
    """Agente Trafego — define publicos, canais e orcamentos."""

    NAME = AgentName.TRAFEGO

    def plan(self, payload: dict[str, Any]) -> TrafficOutput:
        goal = CEOGoal(**payload.get("goal", {}))
        ctx = payload.get("context", {})
        pesquisa = ResearchOutput(**ctx["pesquisa"]) if "pesquisa" in ctx else ResearchOutput()
        ajustes = payload.get("ajustes", {})

        canais = pesquisa.canais_sugeridos or [
            "Meta Ads (Facebook/Instagram)",
            "Google Ads (Search)",
        ]

        if ajustes.get("acao") == "reduzir_cac" or ajustes.get("trafego") == "cortar_canais_com_cac_alto":
            canais = canais[:2]

        orcamento = goal.orcamento
        # Distribuicao proporcional simples entre canais
        peso = {c: (1.0 if i == 0 else 0.7) for i, c in enumerate(canais)}
        total_peso = sum(peso.values()) or 1.0
        orcamento_por_canal = {
            c: round(orcamento * peso[c] / total_peso, 2) for c in canais
        }

        if ajustes.get("trafego") == "aumentar_orcamento_em_15_por_cento":
            orcamento = orcamento * 1.15
            orcamento_por_canal = {
                c: round(v * 1.15, 2) for c, v in orcamento_por_canal.items()
            }

        if ajustes.get("trafego") == "redirecionar_orcamento_para_melhor_canal" and canais:
            melhor = canais[0]
            orcamento_por_canal = {melhor: round(orcamento, 2)}

        publicos = [
            f"{p} — lookalike 1% de compradores" for p in pesquisa.personas
        ] or [goal.publico_alvo]

        lances = {c: round(max(1.5, goal.ticket_medio * 0.05), 2) for c in canais}

        resumo = (
            f"Plano de trafego: {len(publicos)} publicos, {len(canais)} canais, "
            f"orcamento total R$ {sum(orcamento_por_canal.values()):.2f} "
            f"(meta R$ {orcamento:.2f})."
        )
        print(f"[TRAFEGO] {resumo}")
        return TrafficOutput(
            publicos=publicos,
            canais=canais,
            orcamento_por_canal=orcamento_por_canal,
            lances=lances,
            resumo=resumo,
        )
