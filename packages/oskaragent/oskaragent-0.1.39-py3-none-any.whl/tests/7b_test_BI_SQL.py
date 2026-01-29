from __future__ import annotations

import json

from oskaragent.agent import Oskar
from oskaragent.agent_config import AgentConfig
from tests.helpers import set_key


def main() -> None:
    # Set OpenAI API key
    set_key()

    # Configura o agente para usar o índice local de RAG
    ag_cfg = AgentConfig(
            working_databases=[
                {
                    "name": "Chamados",
                    "description": "Informações sobre chamados de suporte técnico",
                    "connection_string": "Driver={SQL Server};Server=CGSQL07;Database=DB_KPI;Uid=relkpi;Pwd=tele13",
                    "query": """
                             select top 100
                                    CH.NumeroChamado as 'Número do Chamado', CJE.MnemonicoCliente as 'Nome do Cliente', CH.TipoChamado as 'Tipo do Chamado', CH.Classificacao as 'Classificação', CH.[Status] as 'Situação', CH.[Fila] as 'Grupo de Atendimento', CH.[Contrato] as 'Contrato', CH.DataAbertura as 'Data da Abertura', CH.DataEncerramento as 'Data do Encerramento', CH.Titulo as 'Título', CH.Descricao as 'Descrição', CH.Fabricante,
                                    CH.CausaIncidente as 'Causa do Incidente', CH.DetalheCausas as 'Detalhe da Causa', CH.Indisponibilidade,
                                    CH.Resolucao as 'Solucão'
                             from gestaocorp.vwChamado as CH
                                      join gestaocorp.vwCotacao as CO on CO.IdCotacao = CH.IdCotacao
                                      join gestaocorp.vwOportunidade as OPO on OPO.IdOportunidade = CO.IdOportunidade
                                      join gestaocorp.vwConjEmpresas as CJE on CJE.IdConjEmpresas = OPO.IdConjEmpresas
                             """,
                }
            ]
    )

    # Ativar logs detalhados para ver chamadas de ferramenta (inclui logs azuis)
    agent = Oskar(agent_config=ag_cfg, is_verbose=True)

    test_q = 'Faça um gráfico de barras por Fabricante.'
    res = agent.answer(test_q)

    print(test_q)
    # Ensure UTF-8 characters are printed properly (no ASCII escapes)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
