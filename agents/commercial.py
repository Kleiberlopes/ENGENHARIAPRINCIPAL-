from __future__ import annotations

from models.schemas import AgentName, CommercialReply, FunnelStage


class CommercialAgent:
    """
    Agente Comercial — simulacao de conversa natural com o lead.

    Recebe a mensagem do lead, interpreta a intencao e decide a proxima
    acao no funil (Captacao -> Educacao -> Conversao).
    """

    NAME = AgentName.COMERCIAL

    # Respostas simuladas por intencao (compra primeiro: prioridade de match)
    _INTENCOES = {
        "quero": ("oferta_direta", FunnelStage.CONVERSAO),
        "comprar": ("oferta_direta", FunnelStage.CONVERSAO),
        "testar": ("oferta_direta", FunnelStage.CONVERSAO),
        "preco": ("pergunta_preco", FunnelStage.EDUCACAO),
        "valor": ("pergunta_preco", FunnelStage.EDUCACAO),
        "quanto": ("pergunta_preco", FunnelStage.EDUCACAO),
        "como funciona": ("explicar_mecanismo", FunnelStage.EDUCACAO),
        "duvida": ("quebrar_objecao", FunnelStage.EDUCACAO),
        "garantia": ("quebrar_objecao", FunnelStage.EDUCACAO),
        "oi": ("aquecer", FunnelStage.CAPTACAO),
        "ola": ("aquecer", FunnelStage.CAPTACAO),
    }

    def reply(self, lead_id: int, mensagem: str, stage: FunnelStage) -> CommercialReply:
        texto = mensagem.lower()
        intencao, alvo_stage = "aquecer", FunnelStage.CAPTACAO
        for chave, (int_acao, int_stage) in self._INTENCOES.items():
            if chave in texto:
                intencao, alvo_stage = int_acao, int_stage
                break

        # Avanca o funil: nunca volta etapa
        ordem = [FunnelStage.CAPTACAO, FunnelStage.EDUCACAO, FunnelStage.CONVERSAO]
        if ordem.index(alvo_stage) > ordem.index(stage):
            novo_stage = alvo_stage
        else:
            novo_stage = stage

        qualificado = novo_stage == FunnelStage.CONVERSAO

        respostas = {
            "aquecer": (
                f"Ola! Aqui e a equipe do produto. Me conta: qual o maior "
                f"desafio que voce esta enfrentando hoje? Estou aqui para ajudar."
            ),
            "pergunta_preco": (
                "Nosso plano comeca com um investimento acessivel e voce "
                "tem 7 dias de garantia total. Quer que eu te envie a tabela "
                "combinando com o seu objetivo?"
            ),
            "explicar_mecanismo": (
                "Funciona assim: 1) voce faz o cadastro, 2) nosso time monta "
                "o plano, 3) voce acompanha os resultados em tempo real. "
                "Simples assim. Posso seguir com o cadastro?"
            ),
            "quebrar_objecao": (
                "Totalmente valido ter duvidas! Por isso damos 7 dias de "
                "garantia incondicional: se nao gostar, devolvemos 100%. "
                "Sem risco para voce."
            ),
            "oferta_direta": (
                "Perfeito! Voce esta no lugar certo. Vou te levar direto "
                "para a finalizacao — leva menos de 1 minuto. "
                "Confirme que deseja prosseguir?"
            ),
        }

        resposta = respostas.get(intencao, respostas["aquecer"])
        proxima = "Enviar checkout" if qualificado else "Enviar conteudo de educacao"

        print(f"[COMERCIAL] lead={lead_id} intencao={intencao} stage={stage.value}->{novo_stage.value}")
        return CommercialReply(
            lead_id=lead_id,
            stage=novo_stage,
            resposta=resposta,
            proxima_acao=proxima,
            qualificado=qualificado,
        )
