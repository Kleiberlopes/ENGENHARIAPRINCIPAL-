# ENGENHARIAPRINCIPAL-

**Escritório de Vendas — Projeto Enriquecer**
MVP de orquestração de agentes de marketing (modelo *Cérebro e Executores*).

> Painel de arquitetura: `http://127.0.0.1:8000/` · Swagger: `http://127.0.0.1:8000/docs`

---

## O que é

Sistema local que recebe a **meta do CEO**, delega a executores especializados,
simula o funil de vendas até o checkout e devolve um **relatório de ROI/CAC/Conversão**
ao **Agente Cérebro**, que toma a **nova decisão** — fechando o loop de feedback.

```
Meta do CEO → Cérebro → Pesquisa → Copy → Tráfego
            → Funil (Captação → Educação → Conversão) → Checkout
            → Analista (ROI · CAC · Conversão) → Nova decisão do Cérebro
```

## Stack

| Camada | Tecnologia |
|---|---|
| API | FastAPI + Uvicorn (porta 8000) |
| Lógica | Python 3.10+ (testado em 3.12) |
| Modelos | Pydantic v2 |
| Persistência | SQLite (`enriquecer.db`) |
| Painel | HTML/CSS/JS estático (`dashboard/`) |

## Estrutura

```
├── main.py              # Servidor FastAPI + painel + endpoints
├── dashboard/index.html # Painel de arquitetura, estudo e avaliação
├── test_flow.py         # Ciclo completo com asserts
├── ARCHITECTURE.md      # Arquitetura detalhada + avaliação
├── agents/              # Cérebro, Analista, Pesquisa, Copy, Tráfego, Comercial
├── core/                # engine (orquestração), funnel, checkout
├── database/db.py       # Camada SQLite
└── models/schemas.py    # Contratos Pydantic
```

## Como rodar

```bash
# dependências
pip install -r requirements.txt

# teste do ciclo completo (sem servidor)
python test_flow.py

# servidor + painel
python main.py
# → http://127.0.0.1:8000/
```

## Disparar a engrenagem

```powershell
$body = @{
  meta = "Aumentar Vendas"
  produto = "Enriquecer CRM"
  orcamento = 5000
  ticket_medio = 197
  publico_alvo = "donos de pequenos negocios"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:8000/engine/run?n_leads=15" `
  -Method Post -Body $body -ContentType "application/json"
```

## Endpoints principais

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Painel de arquitetura e avaliação |
| GET | `/docs` | Swagger UI |
| GET | `/api/overview` | KPIs + logs agregados |
| POST | `/engine/run` | Ciclo completo (meta do CEO) |
| POST | `/funnel/lead` · `/funnel/chat` | Captação e conversa comercial |
| POST | `/checkout` | Transação simulada |
| GET | `/analyst/report` · `/logs` · `/leads` · `/sales` | Métricas e jornada |

## Documentação de estudo

- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — arquitetura, padrões, pontos fortes/fracos e roadmap
- Painel web em `/` — abas para fluxo, funções de cada agente, avaliação e roteiro de estudo

## Licença

Projeto privado — uso interno do Escritório de Vendas.
