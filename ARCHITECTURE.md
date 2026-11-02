# Projeto Enriquecer — Documento de Arquitetura e Avaliação

> Guia de estudo do MVP de orquestração de agentes de marketing.
> Servidor: `http://127.0.0.1:8000` | Swagger: `http://127.0.0.1:8000/docs`

---

## 1. Visão Geral

O sistema segue o modelo **"Cérebro e Executores"**:

- **Agente Cérebro** = orquestrador central. Recebe a meta do CEO, decide a rota
  (roteamento), delega tarefas aos executores e, ao receber o relatório do Analista,
  toma uma **nova decisão** — fechando o **loop de feedback**.
- **Executores** = agentes especializados (Pesquisa, Copy, Tráfego) que só executam
  o que o Cérebro manda e devolvem um resultado estruturado.
- **Analista** = módulo de fechamento: calcula ROI, CAC e Conversão e devolve o
  relatório ao Cérebro para a próxima rodada de decisão.

```
                         ┌─────────────────────────────────────────────┐
   Meta do CEO ─────────►│            AGENTE CÉREBRO                   │
                         │  • route()    → define a rota               │
                         │  • dispatch() → delega aos executores       │
                         │  • process_feedback() → nova decisão       │
                         └──────┬──────────────┬───────────────▲───────┘
                                │              │               │
              1) roteia         │   2) delega   │               │  5) relatório
              por palavra-chave │              ▼               │     (ROI/CAC/Conv)
                                │      ┌───────────────┐       │
                                │      │  PESQUISA     │       │
                                │      │  personas,    │       │
                                │      │  dores, âng.  │       │
                                │      └──────┬────────┘       │
                                │             ▼                │
                                │      ┌───────────────┐       │
                                │      │    COPY       │       │
                                │      │ anúncios,     │       │
                                │      │ landing page  │       │
                                │      └──────┬────────┘       │
                                │             ▼                │
                                │      ┌───────────────┐       │
                                └─────►│   TRÁFEGO     │       │
                                       │ públicos,     │       │
                                       │ canais, verba │       │
                                       └──────┬────────┘       │
                                              ▼                │
   Lead ──► FUNIL (Captacao → Educacao → Conversao)            │
              │                                                │
              ▼                                                │
        COMERCIAL (conversa natural)                           │
              │                                                │
              ▼                                                │
        CHECKOUT (transação + registro) ──► vendas ──► ANALISTA ┘
                                                              │
                       6) NOVA DECISÃO (rota/ajustes) ◄───────┘
                       nova_meta, cortar canais, escalar...
```

**Ciclo completo em uma frase:**
`Meta do CEO → Cérebro → Executores → Funil → Venda → Analista → Nova Decisão do Cérebro`

---

## 2. Estrutura de Pastas

```
projeto-enriquecer/
├── main.py              # Servidor FastAPI + endpoints (porta 8000)
├── test_flow.py         # Script do ciclo completo (validação)
├── requirements.txt     # fastapi, uvicorn, pydantic
├── enriquecer.db        # SQLite (gerado em runtime)
│
├── agents/              # OS AGENTES (cérebro + executores + analista)
│   ├── brain.py         #   Agente Cérebro (roteamento + feedback)
│   ├── analyst.py       #   Agente Analista (ROI/CAC/conversão)
│   ├── research.py      #   Agente Pesquisa (mercado/personas/ângulos)
│   ├── copy.py          #   Agente Copy (anúncios + landing page)
│   ├── traffic.py       #   Agente Tráfego (públicos/canais/orçamento)
│   └── commercial.py    #   Agente Comercial (conversa com o lead)
│
├── core/                # NÚCLEO / ORQUESTRAÇÃO
│   ├── engine.py        #   Motor: acopla tudo no ciclo completo
│   ├── funnel.py        #   Funil de vendas (máquina de estados)
│   └── checkout.py      #   Simulação de transação/venda
│
├── database/
│   └── db.py            # Camada SQLite (leads, sales, reports, logs)
│
└── models/
    └── schemas.py       # Modelos Pydantic (contratos de dados)
```

**Regra de separação:**
- `agents/` = *quem* executa (lógica de negócio por agente)
- `core/` = *como* se conecta (orquestração e fluxo)
- `models/` = *o que* trafega (contratos/DTOs)
- `database/` = *onde* persiste

---

## 3. Componentes e Responsabilidades

| Componente | Arquivo | Responsabilidade | Método principal |
|---|---|---|---|
| **Cérebro** | `agents/brain.py` | Roteia, delega, decide | `route()`, `dispatch()`, `run_pipeline()`, `process_feedback()` |
| **Pesquisa** | `agents/research.py` | Mercado, personas, ângulos | `analyze(payload)` |
| **Copy** | `agents/copy.py` | Anúncios, headlines, landing | `generate(payload)` |
| **Tráfego** | `agents/traffic.py` | Públicos, canais, verba | `plan(payload)` |
| **Comercial** | `agents/commercial.py` | Conversa natural c/ lead | `reply(lead_id, msg, stage)` |
| **Funil** | `core/funnel.py` | Estados do lead | `capture()`, `advance()`, `close_won/lost()` |
| **Checkout** | `core/checkout.py` | Transação + registro | `pay(lead_id, valor, canal)` |
| **Analista** | `agents/analyst.py` | ROI/CAC/conversão + relatório | `analyze()`, `send_to_brain()` |
| **Motor** | `core/engine.py` | Liga tudo no ciclo | `run(goal, n_leads)` |

### Máquina de estados do Funil

```
Captacao ──► Educacao ──► Conversao ──► Vendido
                 │            │
                 └────► Perdido ◄─────┘
```

- Ordem fixa: `Captacao → Educacao → Conversao` (nunca volta etapa)
- `Conversao` habilita o checkout
- Persistido em `leads.stage` (SQLite)

---

## 4. Padrões de Design Utilizados

| Padrão | Onde | O que resolve |
|---|---|---|
| **Pipeline** | `brain.run_pipeline()` | Executa Pesquisa→Copy→Tráfego em sequência, passando contexto adiante |
| **Strategy (injeção)** | `BrainAgent(executor=...)` | O Cérebro não conhece *como* chama os agentes; recebe uma função `executor` (interna ou HTTP) |
| **Adapter de comunicação** | `engine._internal_executor()` | Troca fácil entre chamada de função interna e `requests.post` local sem mudar o Cérebro |
| **Singleton** | `get_db()`, `get_engine()` | Uma instância de DB e de Engine para a aplicação |
| **Repository** (leve) | `database/db.py` | Toda persistência isolada atrás de uma interface (`Database`) |
| **DTO / Contrato** | `models/schemas.py` | Pydantic valida e documenta o que trafega entre agentes |
| **Feedback loop** | `analyst.send_to_brain()` | Relatório → nova decisão → nova rota (ciclo fechado) |
| **Máquina de estados** | `core/funnel.py` | Transições controladas de estágio do lead |

### Comunicação entre agentes

**Hoje:** chamadas de função internas (rápido, sem rede).
O ponto de troca está isolado em `core/engine.py::_internal_executor` — para migrar
para HTTP local, basta trocar o corpo dessa função por `requests.post(...)` sem
alterar o Cérebro.

```python
# core/engine.py — ponto único de acoplamento
def _internal_executor(self, task: TaskDispatch) -> Any:
    mapping = {
        AgentName.PESQUISA: self.research.analyze,
        AgentName.COPY:     self.copy.generate,
        AgentName.TRAFEGO:  self.traffic.plan,
    }
    return mapping[task.agent](task.payload)
```

---

## 5. Fluxo Principal (`POST /engine/run`)

1. **CEO envia meta** (`CEGoal`: meta, produto, orçamento, ticket, público)
2. **Cérebro roteia** por palavra-chave da meta:
   - "venda/vendas/converter" → `Pesquisa → Copy → Tráfego`
   - "tráfego/lead/captar" → `Pesquisa → Tráfego → Copy`
   - "copy/texto" → `Pesquisa → Copy`
   - default → pipeline completo
3. **Executores rodam em sequência**, cada um lê `goal + context + ajustes`
4. **Funil simula leads**: capta → conversa comercial (2 mensagens) → qualifica
5. **Checkout** registra vendas (~80% dos leads qualificados, simulação)
6. **Analista** calcula sobre o snapshot do DB:
   - `ROI = (receita − investimento) / investimento`
   - `CAC = investimento / vendas`
   - `Conversão = vendas / leads`
7. **Cérebro processa o feedback** e gera nova decisão:
   - `ROI < 1` → refazer copy + cortar canais caros
   - `conversão < 5%` → reforçar educação do funil
   - `CAC > 50% do ticket` → realocar verba
   - senão → escalar 15%

---

## 6. Persistência (SQLite — `enriquecer.db`)

| Tabela | Guarda |
|---|---|
| `leads` | Jornada do lead (nome, stage, origem, interações, comprou) |
| `sales` | Vendas (valor, canal, status, data) |
| `reports` | Relatórios do Analista por rodada (roi, cac, conversao...) |
| `execution_log` | Log completo de cada passo da engrenagem |

Acesso sempre via `database/db.py` (`get_db()`), nunca SQL solto nos agentes.

---

## 7. Mapa da API

| Método | Rota | O que faz |
|---|---|---|
| POST | `/engine/run?n_leads=15` | Dispara a engrenagem completa com a meta do CEO |
| POST | `/funnel/lead` | Captura um lead |
| POST | `/funnel/chat` | Conversa natural (Agente Comercial) |
| POST | `/checkout` | Simula transação e registra venda |
| GET | `/analyst/report` | Último relatório do Analista |
| GET | `/logs` | Log de execução (filtro opcional `?run_id=`) |
| GET | `/leads` | Jornada de todos os leads |
| GET | `/sales` | Vendas registradas |
| GET | `/` | Índice dos endpoints |
| GET | `/docs` | Swagger UI |

---

## 8. Avaliação — Pontos Fortes

1. **Separação clara de responsabilidades** — adicionar um novo agente (ex: Analytics)
   não exige mexer no Cérebro, só mapear no `_internal_executor`.
2. **Loop de feedback real** — Analista → Cérebro fecha o ciclo; o sistema não é
   um pipeline linear, ele **decide a próxima rodada**.
3. **Contratos tipados** — Pydantic em toda a fronteira (`schemas.py`); erro de
   contrato estoura cedo e o Swagger se auto-documenta.
4. **Ponto único de troca de comunicação** — migrar de função interna para HTTP
   local é mudar uma função só.
5. **Persistência desacoplada** — nenhum agente conhece SQL; trocar SQLite por
   Postgres = mexer só em `database/db.py`.
6. **Roteamento explicável** — todo passo vira `ExecutionLog` (terminal + tabela),
   dá para auditar por que o sistema decidiu X.
7. **Testável de ponta a ponta** — `test_flow.py` roda o ciclo sem servidor e
   valida com asserts.

---

## 9. Avaliação — Pontos Fracos e Riscos

| # | Ponto | Por que importa | Gravidade |
|---|---|---|---|
| 1 | **Simulações determinísticas** — intenção do Comercial é busca por substring; venda é `i % 5` | Não é IA de verdade; qualquer frase fora do dicionário cai no fallback "aquecer" | Alta (para produção) |
| 2 | **Roteamento por keyword frágil** — `if "venda" in meta` | Sinônimos, typos e metas mistas quebram a rota | Média |
| 3 | **Sem autenticação/autorização** — qualquer um chama `/engine/run` | Inaceitável se expor fora de `localhost` | Alta (se expor) |
| 4 | **DB singleton com `check_same_thread=False`** — conexão compartilhada | Sob concorrência real (múltiplos workers uvicorn) pode dar race/locking | Média |
| 5 | **Sem testes automatizados formais** — só `test_flow.py` manual | Sem CI, sem regressão garantida ao mexer no código | Média |
| 6 | **Estado do Cérebro em memória** (`logs`, `last_decision`) | Reiniciou o servidor, perdeu contexto da rodada (o DB guarda, mas o objeto não) | Baixa |
| 7 | **Sem tratamento de erro padronizado** — exceptions vazam como 500 | Cliente não recebe corpo de erro consistente | Média |
| 8 | **Lógica de negócio nos `print`s** — log = `print` | Em produção precisa de `logging` estruturado (níveis, arquivo, JSON) | Baixa |
| 9 | **Orçamento/tráfego inventado** — distribuição por peso fixo, lances calculados | Não integra com Meta/Google Ads reais; é placeholder | Alta (para uso real) |
| 10 | **Sem versionamento de schema** — tabelas criadas só com `IF NOT EXISTS` | Mudou a tabela, DB antigo fica incompatível (falta migrations) | Média |
| 11 | **N+1 de leads no engine** — uma conversa por lead em loop sequencial | Com 10 mil leads fica lento; sem assincronismo/worker | Baixa no MVP |
| 12 | **ROI sem custo real de mídia por lead** — usa `orcamento` fixo da meta | Números do Analista são internamente consistentes mas não batem com o mundo real | Média |

---

## 10. O que falta para produção (roadmap sugerido)

**Curto prazo (endurecer o MVP):**
- [ ] `logging` estruturado no lugar dos `print`
- [ ] Handler global de erros (respostas JSON padronizadas)
- [ ] Testes com `pytest` + `TestClient` do FastAPI
- [ ] Chave simples de API (header) mesmo que só para localhost
- [ ] Migrations leves (ou Pydantic + SQL explicit versionado)

**Médio prazo (IA de verdade):**
- [ ] Trocar intenção substring → classificador (LLM ou regex com sinonimos)
- [ ] Roteamento do Cérebro via LLM com schema de saída validado
- [ ] Comunicação agentes via HTTP interno (cada agente = serviço)
- [ ] Fila/assíncrono (asyncio/worker) para o funil em massa

**Longo prazo (escala):**
- [ ] SQLite → PostgreSQL
- [ ] Integração real de tráfego (Meta Ads / Google Ads API)
- [ ] Dashboard de métricas consumindo `/analyst/report`
- [ ] Multi-tenant (vários CEOs/projetos)

---

## 11. Roteiro de Estudo (como ler o código)

Ordem sugerida para estudar e avaliar:

1. **`models/schemas.py`** — entenda os contratos (o que cada agente come/devolve)
2. **`agents/brain.py`** — o cérebro: `route()` e `process_feedback()` são o coração
3. **`agents/analyst.py`** — como ROI/CAC/conversão são calculados e devolvidos
4. **`core/engine.py`** — o glue: onde tudo se conecta (leia `_internal_executor`)
5. **`core/funnel.py` + `agents/commercial.py`** — estados do lead e conversa
6. **`database/db.py`** — o que persiste e como
7. **`main.py`** — superfície HTTP
8. **`test_flow.py`** — o ciclo completo em modo script

**Perguntas para avaliar (exercício):**
- O Cérebro conhece demais os detalhes dos executores? (acoplamento)
- Se eu adicionar um agente "Fidelidade", quantos arquivos mudo?
- O relatório do Analista influencia *de verdade* a próxima rota, ou é decorativo?
- O que quebra primeiro se 100 usuários chamarem `/engine/run` ao mesmo tempo?
- Os números de ROI fazem sentido para o negócio, ou só para o demo?
