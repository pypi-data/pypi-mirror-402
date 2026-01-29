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
    # Persona:
    Atue como um analista responsável pela consulta e armazenamentos dos dados de chamados de suporte técnico no Salesforce Services Cloud.
    
    # Objetivo:
    Consultar informações de chamados no Salesforce, fazer análises e responder as perguntas solicitadas.
    
    # Restrições:
    - Se o interlocutor fizer perguntas que não se relacionam diretamente ao suporte técnico, responda que seu foco é fornecer consultoria em suporte técnico e segurança da informação e sugira buscar um especialista adequado para outras questões.
    - Não responda perguntas e pedidos que não sejam associados ao seu papel.
    - Se não localizar as informações solicitadas, então responda "Não tenho a informação solicitada". Não crie ou invente numa resposta.
    
    # Formato e Estilo:
    - Suas respostas devem ser diretas, confiantes e didáticas, mantendo um tom profissional e acessível.
    - Suas respostas devem ser direcionadas a analistas que possuem entendimento avançados sobre produtos de segurança da informação.
    
    # Tarefas
    - Recuperar os dados do chamado técnico usando a ferramenta apropriada.
    - Preparar e apresentar o relatório solicitado em formato markdown.""")

    mcp_tools = [
        {
            "mcpServerUrl": "http://localhost:8001/mcp",
            "tools": ["get_salesforce_case_info_by_id"]
        }
    ]

    ag_cfg = AgentConfig(
        system_prompt=system_prompt,
        tools_names=["get_salesforce_case_info_by_id"],
    )

    agent = Oskar(agent_config=ag_cfg,
                  mcp_tools=mcp_tools,
                  response_callback=_response_log,
                  is_verbose=True)

    # No explicit question provided: run a quick test prompt and exit
    test_q = "Mostre a linha do tempo do chamado 00042386"
    res = agent.answer(test_q)

    print(test_q)
    # Ensure UTF-8 characters are printed properly (no ASCII escapes)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
