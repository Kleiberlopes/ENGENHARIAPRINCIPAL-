from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "enriquecer.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    lead_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    stage TEXT NOT NULL DEFAULT 'Captacao',
    origem TEXT DEFAULT '',
    interacoes INTEGER DEFAULT 0,
    comprou INTEGER DEFAULT 0,
    criado_em TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    valor REAL NOT NULL,
    canal TEXT DEFAULT '',
    status TEXT DEFAULT 'aprovada',
    criado_em TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
);

CREATE TABLE IF NOT EXISTS reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    roi REAL,
    cac REAL,
    conversao REAL,
    vendas INTEGER,
    receita REAL,
    investimento REAL,
    leads INTEGER,
    recomendacao TEXT,
    criado_em TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS execution_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    step INTEGER,
    agent TEXT,
    action TEXT,
    detail TEXT,
    status TEXT DEFAULT 'OK',
    criado_em TEXT DEFAULT (datetime('now'))
);
"""


class Database:
    """Camada de persistencia SQLite: jornada do lead + metricas."""

    def __init__(self, path: Path | str = DB_PATH) -> None:
        self.path = str(path)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # --- Leads / Jornada ---
    def create_lead(self, nome: str, origem: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO leads (nome, stage, origem) VALUES (?, 'Captacao', ?)",
            (nome, origem),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_lead_stage(self, lead_id: int, stage: str, comprou: Optional[bool] = None) -> None:
        if comprou is None:
            self.conn.execute(
                "UPDATE leads SET stage = ?, interacoes = interacoes + 1 WHERE lead_id = ?",
                (stage, lead_id),
            )
        else:
            self.conn.execute(
                "UPDATE leads SET stage = ?, interacoes = interacoes + 1, comprou = ? WHERE lead_id = ?",
                (stage, int(comprou), lead_id),
            )
        self.conn.commit()

    def get_lead(self, lead_id: int) -> Optional[dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM leads WHERE lead_id = ?", (lead_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_leads(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM leads ORDER BY lead_id").fetchall()
        return [dict(r) for r in rows]

    # --- Vendas ---
    def record_sale(self, lead_id: int, valor: float, canal: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO sales (lead_id, valor, canal) VALUES (?, ?, ?)",
            (lead_id, valor, canal),
        )
        self.conn.execute(
            "UPDATE leads SET comprou = 1, stage = 'Vendido' WHERE lead_id = ?",
            (lead_id,),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_sales(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM sales ORDER BY sale_id").fetchall()
        return [dict(r) for r in rows]

    # --- Relatorios do Analista ---
    def save_report(self, run_id: str, report: dict[str, Any]) -> int:
        cur = self.conn.execute(
            """INSERT INTO reports
               (run_id, roi, cac, conversao, vendas, receita, investimento, leads, recomendacao)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                report.get("roi", 0.0),
                report.get("cac", 0.0),
                report.get("conversao", 0.0),
                report.get("vendas", 0),
                report.get("receita", 0.0),
                report.get("investimento", 0.0),
                report.get("leads", 0),
                report.get("recomendacao", ""),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_reports(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM reports ORDER BY report_id").fetchall()
        return [dict(r) for r in rows]

    # --- Log de execucao ---
    def log(self, run_id: str, step: int, agent: str, action: str,
            detail: str = "", status: str = "OK") -> None:
        self.conn.execute(
            "INSERT INTO execution_log (run_id, step, agent, action, detail, status) VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, step, agent, action, detail, status),
        )
        self.conn.commit()

    def list_logs(self, run_id: Optional[str] = None) -> list[dict[str, Any]]:
        if run_id:
            rows = self.conn.execute(
                "SELECT * FROM execution_log WHERE run_id = ? ORDER BY log_id", (run_id,)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM execution_log ORDER BY log_id"
            ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.conn.close()


_db: Optional[Database] = None


def get_db() -> Database:
    """Singleton da base de dados para a aplicacao."""
    global _db
    if _db is None:
        _db = Database()
    return _db


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")
