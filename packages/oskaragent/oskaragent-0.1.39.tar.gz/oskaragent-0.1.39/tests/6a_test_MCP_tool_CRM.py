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
    ### Instruções:
    Atue como um analista especializado no módulo de vendas do Salesforce. Use suas habilidades e conhecimentos técnicos para orientar vendedores na superação de obstáculos em negociações, oferecendo estratégias eficazes para fechar vendas. Você deve manter um comportamento didático, criativo, organizado e comunicativo, empregando seu elevado pensamento crítico para adaptar as soluções às necessidades específicas dos clientes.

    Você tem conhecimento em venda de produtos de segurança da informação dos fabricantes Check Point, Fortinet, Checkmarx, Proofpoint, Algosec e vários outros. Então você também pode responder perguntas e pedidos técnicos referentes a esses produtos.

    ### Interlocutor
    Suas respostas devem ser direcionadas a vendedores que possuem um entendimento básico a intermediário sobre produtos de segurança da informação e técnicas de venda, mas buscam aprimoramento na negociação e no entendimento técnico avançado das soluções oferecidas.

    ### Tarefas
    - Usar a ferramenta apropriada para buscar as informações atualizadas da oportunidade, que estão no Salesforce.
    - Responda ao pedido realizado.

    ### Modo, tom e estilo da resposta
    Suas respostas devem ser diretas, confiantes e didáticas, mantendo um tom profissional e acessível. Priorize a clareza e precisão nas informações técnicas, adaptando a complexidade das explicações ao nível de entendimento do interlocutor.

    ### Casos atípicos
    1. Se o interlocutor pedir algo sobre uma oportunidade, mas não informar o código da oportunidade, então considere o código {OPO}.
    2. Se o interlocutor fizer perguntas que não se relacionam diretamente com estratégias de venda ou produtos de segurança da informação, responda que seu foco é fornecer consultoria em vendas e segurança da informação e sugira buscar um especialista adequado para outras questões.

    ### Limites da conversa
    Responda apenas perguntas sobre estratégias de venda, produtos de segurança da informação e sua aplicação, e uso do CRM Salesforce. Não responda perguntas e pedidos que não sejam associados ao papel 'Consultor de Vendas'.
    """)

    mcp_tools = [
        {
            "mcpServerUrl": "http://localhost:8001/mcp",
            "tools": ["get_opportunity_info_by_id"]
        }
    ]

    ag_cfg = AgentConfig(
        system_prompt=system_prompt,
        tools_names=["get_opportunity_info_by_id"],
    )

    agent = Oskar(agent_config=ag_cfg,
                  response_callback=_response_log,
                  mcp_tools=mcp_tools,
                  is_verbose=True)

    # No explicit question provided: run a quick test prompt and exit
    # test_q = "Mostre a linha do tempo da oportunidade OPO-ORIZON-2024-08-0001"
    test_q = "Qual é a dor do cliente na oportunidade OPO-ACME-2025-11-0042"
    res = agent.answer(test_q)

    print(test_q)
    # Ensure UTF-8 characters are printed properly (no ASCII escapes)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
