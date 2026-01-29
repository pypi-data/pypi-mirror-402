from __future__ import annotations

from textwrap import dedent
from typing import Any
import json

from tests.helpers import set_key
from oskaragent.agent import Oskar
from oskaragent.agent_config import AgentConfig


def _response_log(assistant_message_struct: dict[str, Any]):
    usage = assistant_message_struct.get("usage", {}) or {}
    print(
            f"[callback] message_id={assistant_message_struct.get('message_id')} "
            f"tokens={{'input_tokens': {usage.get('input_tokens')}, 'output_tokens': {usage.get('output_tokens')}, 'total_tokens': {usage.get('total_tokens')}}}"
    )


def main() -> int:
    # Set OpenAI API key
    set_key()

    system_prompt = dedent("""
    ### Papel
    Atue como um assistente para os colaboradores da equipe de BDR, para responder perguntas sobre pessoas e empresas.

    ### Tarefas
    - Usar a ferramenta apropriada para buscar as informações sobre pessoas e empresas.
    - Responda ao pedido realizado.

    ### Modo, tom e estilo da resposta
    Suas respostas devem ser diretas, confiantes e didáticas, mantendo um tom profissional e acessível. Priorize a clareza e precisão nas informações técnicas, adaptando a complexidade das explicações ao nível de entendimento do interlocutor.

    ### Casos atípicos
    Se o interlocutor fizer perguntas que não se relacionam diretamente com pessoas e empresas, responda que seu foco é fornecer consultoria para as atividades de BDR.

    ### Limites da conversa
    Responda apenas perguntas sobre pessoas, empresas e atividades de BDR. Não responda perguntas e pedidos que não sejam associados à base de clientes.
    """)

    mcp_tools = [
        {
            "mcpServerUrl": "http://localhost:8001/mcp",
            "tools": ["get_salesforce_case_info_by_id"]
        }
    ]

    ag_cfg = AgentConfig(
            system_prompt=system_prompt
    )

    agent = Oskar(agent_config=ag_cfg,
                  response_callback=_response_log,
                  mcp_tools=mcp_tools,
                  is_verbose=True)

    # No explicit question provided: run a quick test prompt and exit
    test_q = 'Liste em formato de tabela as pessoas cujos nomes correspondam a "José Carlos".'
    res = agent.answer(test_q)

    print(test_q)
    # Ensure UTF-8 characters are printed properly (no ASCII escapes)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
