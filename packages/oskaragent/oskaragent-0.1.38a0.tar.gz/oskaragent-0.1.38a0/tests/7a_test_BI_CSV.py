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
        working_files=[
            {
                "name": "basileia",
                "description": "Dados de temperatura da cidade de Basileia",
                "pathname": "./sources/Basileia.csv"
            }
        ]
    )

    # Ativar logs detalhados para ver chamadas de ferramenta (inclui logs azuis)
    agent = Oskar(agent_config=ag_cfg, is_verbose=True)

    test_q = 'Faça um gráfico de linhas que mostra a evolução da média da temperatura ao longo dos anos. Considere a maior valor de cada ano.'
    res = agent.answer(test_q)

    print(test_q)
    # Ensure UTF-8 characters are printed properly (no ASCII escapes)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
