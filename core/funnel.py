from __future__ import annotations

from typing import Optional

from models.schemas import (
    CommercialReply,
    FunnelStage,
    LeadJourney,
)
from database.db import Database, get_db


class SalesFunnel:
    """
    Funil de Vendas — fluxo de estados:
        Captacao -> Educacao -> Conversao -> Vendido
    """

    ORDEM = [
        FunnelStage.CAPTACAO,
        FunnelStage.EDUCACAO,
        FunnelStage.CONVERSAO,
    ]

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or get_db()

    def capture(self, nome: str, origem: str = "Meta Ads") -> LeadJourney:
        lead_id = self.db.create_lead(nome, origem)
        print(f"[FUNIL] Captação: lead={lead_id} nome='{nome}' origem={origem}")
        return LeadJourney(lead_id=lead_id, nome=nome, stage=FunnelStage.CAPTACAO, origem=origem)

    def advance(self, lead_id: int, reply: CommercialReply) -> LeadJourney:
        lead = self.db.get_lead(lead_id)
        if lead is None:
            raise ValueError(f"Lead {lead_id} nao encontrado")

        self.db.update_lead_stage(lead_id, reply.stage.value)
        print(
            f"[FUNIL] lead={lead_id} {lead['stage']} -> {reply.stage.value} "
            f"(proxima_acao={reply.proxima_acao})"
        )
        return LeadJourney(
            lead_id=lead_id,
            nome=lead["nome"],
            stage=reply.stage,
            origem=lead["origem"],
            interacoes=lead["interacoes"] + 1,
            comprou=bool(lead["comprou"]),
        )

    def close_won(self, lead_id: int) -> None:
        self.db.update_lead_stage(lead_id, FunnelStage.VENDIDO.value, comprou=True)
        print(f"[FUNIL] lead={lead_id} -> Vendido")

    def close_lost(self, lead_id: int) -> None:
        self.db.update_lead_stage(lead_id, FunnelStage.PERDIDO.value, comprou=False)
        print(f"[FUNIL] lead={lead_id} -> Perdido")

    def status(self, lead_id: int) -> Optional[LeadJourney]:
        lead = self.db.get_lead(lead_id)
        if not lead:
            return None
        return LeadJourney(
            lead_id=lead["lead_id"],
            nome=lead["nome"],
            stage=FunnelStage(lead["stage"]),
            origem=lead["origem"],
            interacoes=lead["interacoes"],
            comprou=bool(lead["comprou"]),
        )
