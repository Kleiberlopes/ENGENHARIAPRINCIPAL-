"""
Teste do ciclo completo do Projeto Enriquecer.

Fluxo simulado:
    Meta do CEO -> Cerebro -> Executores (Pesquisa/Copy/Trafego)
    -> Funil (Captacao -> Educacao -> Conversao) -> Venda (Checkout)
    -> Analista (ROI/CAC/Conversao) -> NOVA DECISAO do Cerebro

Uso:
    python test_flow.py
"""
from __future__ import annotations

import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from models.schemas import CEOGoal, ChatMessage, FunnelStage
from core.engine import Engine


def banner(titulo: str) -> None:
    print("\n" + "=" * 70)
    print(f"  {titulo}")
    print("=" * 70)


def main() -> int:
    banner("PROJETO ENRIQUECER — CICLO COMPLETO (test_flow.py)")

    goal = CEOGoal(
        meta="Aumentar Vendas",
        produto="Enriquecer CRM",
        orcamento=5000.0,
        ticket_medio=197.0,
        publico_alvo="donos de pequenos negocios",
    )
    print(f"[CEO] Meta: {goal.meta} | Produto: {goal.produto} "
          f"| Orcamento: R$ {goal.orcamento} | Ticket: R$ {goal.ticket_medio}")

    engine = Engine()

    # ------------------------------------------------------------------ #
    # ETAPA 1 — Cerebro roteia e dispara executores (Pesquisa->Copy->Trafego)
    # ------------------------------------------------------------------ #
    banner("ETAPA 1 — CÉREBRO -> EXECUTORES")
    brain = engine.brain
    brain.reset(goal)
    context = brain.run_pipeline(goal)

    assert context.get("pesquisa") is not None, "Pesquisa nao executada"
    assert context.get("copy") is not None, "Copy nao executada"
    assert context.get("trafego") is not None, "Trafego nao executado"
    print("[OK] Rota executa: Pesquisa -> Copy -> Trafego")

    # ------------------------------------------------------------------ #
    # ETAPA 2 — FUNIL: captacao -> educacao -> conversao
    # ------------------------------------------------------------------ #
    banner("ETAPA 2 — FUNIL DE VENDAS + AGENTE COMERCIAL")
    lead = engine.funnel.capture(nome="Lead Teste", origem="Meta Ads")
    assert lead.stage == FunnelStage.CAPTACAO

    r1 = engine.commercial.reply(lead.lead_id, "Oi, tenho duvidas", lead.stage)
    j1 = engine.funnel.advance(lead.lead_id, r1)
    print(f"[OK] Apos msg 1: stage={j1.stage.value}")

    r2 = engine.commercial.reply(lead.lead_id, "quero testar, quanto custa?", j1.stage)
    j2 = engine.funnel.advance(lead.lead_id, r2)
    print(f"[OK] Apos msg 2: stage={j2.stage.value}")
    assert j2.stage in (FunnelStage.EDUCACAO, FunnelStage.CONVERSAO)

    # ------------------------------------------------------------------ #
    # ETAPA 3 — CHECKOUT: transacao e registro de venda
    # ------------------------------------------------------------------ #
    banner("ETAPA 3 — CHECKOUT (simulação de transação)")
    venda = engine.checkout.pay(j2.lead_id, valor=goal.ticket_medio, canal="Meta Ads")
    assert venda.status == "aprovada"
    print(f"[OK] Venda registrada #{venda.sale_id} R$ {venda.valor}")

    # ------------------------------------------------------------------ #
    # ETAPA 4 — ANALISTA: ROI, CAC, Conversao
    # ------------------------------------------------------------------ #
    banner("ETAPA 4 — ANALISTA (ROI / CAC / Conversão)")
    leads_total = engine.db.conn.execute("SELECT COUNT(*) c FROM leads").fetchone()["c"]
    relatorio = engine.analyst.analyze(
        goal, investimento=goal.orcamento, leads=leads_total, run_id=brain.run_id
    )
    print(f"[OK] ROI={relatorio.roi} | CAC={relatorio.cac} "
          f"| Conversao={relatorio.conversao} | Vendas={relatorio.vendas}")
    print(f"[OK] Recomendacao: {relatorio.recomendacao}")

    # ------------------------------------------------------------------ #
    # ETAPA 5 — VOLTA AO CÉREBRO: nova decisao (fecha o loop)
    # ------------------------------------------------------------------ #
    banner("ETAPA 5 — ANALISTA -> CÉREBRO (NOVA DECISÃO)")
    decisao = engine.analyst.send_to_brain(relatorio, brain)
    print(f"[OK] Nova meta: {decisao.nova_meta}")
    print(f"[OK] Nova rota: {[a.value for a in decisao.rota]}")
    print(f"[OK] Ajustes: {decisao.ajustes}")
    assert decisao.rota, "Cerebro nao gerou nova rota apos feedback"

    # ------------------------------------------------------------------ #
    # ETAPA 6 — ENGENHARIA COMPLETA via motor (ciclo unico integrado)
    # ------------------------------------------------------------------ #
    banner("ETAPA 6 — ENGENHARIA COMPLETA (/engine/run)")
    resultado = engine.run(goal, n_leads=20)
    print(f"[OK] Rodada run_id={engine.brain.run_id}")
    print(f"[OK] Vendas na rodada: {len(resultado.vendas)}")
    print(f"[OK] Relatorio final: ROI={resultado.relatorio.roi} "
          f"CAC={resultado.relatorio.cac} Conv={resultado.relatorio.conversao}")
    print(f"[OK] Decisao final do Cerebro: {resultado.decisao_final.motivo}")
    assert resultado.relatorio is not None
    assert resultado.decisao_final is not None

    banner("LOG DE EXECUCAO (terminal)")
    for entry in engine.brain.logs:
        print(f"  passo={entry.step:02d} {entry.agent.value:<10} {entry.action:<28} {entry.detail}")

    banner("RESULTADO FINAL — CICLO COMPLETO CONCLUIDO COM SUCESSO")
    print("  CEO -> Cerebro -> Executores -> Funil -> Venda -> Analista -> Nova Decisao")
    return 0


if __name__ == "__main__":
    sys.exit(main())
