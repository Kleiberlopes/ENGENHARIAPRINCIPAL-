from __future__ import annotations

from typing import Optional

from models.schemas import SaleRecord
from database.db import Database, get_db


class Checkout:
    """Simulacao de transacao e registro de venda."""

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or get_db()

    def pay(self, lead_id: int, valor: float, canal: str = "Meta Ads") -> SaleRecord:
        """Simula a aprovacao do pagamento (100% aprovado no MVP)."""
        sale_id = self.db.record_sale(lead_id, valor, canal)
        print(f"[CHECKOUT] Venda #{sale_id} lead={lead_id} valor=R$ {valor:.2f} canal={canal} status=aprovada")
        return SaleRecord(
            sale_id=sale_id,
            lead_id=lead_id,
            valor=valor,
            canal=canal,
            status="aprovada",
        )
