from __future__ import annotations

from textwrap import dedent
from typing import Any
import json

from oskaragent.helpers import ToolContext, vlog
from tests.helpers import set_key
from oskaragent.agent import Oskar
from oskaragent.agent_config import AgentConfig


OpportunityData = dict[str, Any]

_OPPORTUNITY_FIXTURES: list[OpportunityData] = [
    {
        "Id": "OPO-ADVICEHEALTH-2025-12-0001",
        "StageName": "Detalhando",
        "Probability": 25.0,
        "CreatedDate": "2025-12-01T14:27:23.000+0000",
        "OwnerId": "005SG000009Yux4YAC",
        "ShortDescription": "Renovação FortiNac",
        "ProductFamily": "Fortinet",
        "ProductLine": "SSD",
        "PainDescription": "Cliente precisa de proteção de NAC / ZTNA / Token para sua infra. Por isso, precisa renovar.",
        "PainImpact": "Cliente não pode ficar desprotegido.",
        "Renewal": True,
    },
    {
        "Id": "OPO-ACME-2025-11-0042",
        "StageName": "Qualificando",
        "Probability": 10.0,
        "CreatedDate": "2025-11-18T09:02:11.000+0000",
        "OwnerId": "005SG000009Yux4YAC",
        "ShortDescription": "Ampliação de licenças EDR",
        "ProductFamily": "Endpoint",
        "ProductLine": "EDR",
        "PainDescription": "Necessidade de melhorar cobertura de detecção e resposta.",
        "PainImpact": "Maior risco de incidentes e indisponibilidade.",
        "Renewal": False,
    },
    {
        "Id": "OPO-FOO-2026-01-0007",
        "StageName": "Negociando",
        "Probability": 60.0,
        "CreatedDate": "2025-12-15T16:40:00.000+0000",
        "OwnerId": "005SG000009Yux4YAC",
        "ShortDescription": "Projeto de migração de firewall",
        "ProductFamily": "Network Security",
        "ProductLine": "Firewall",
        "PainDescription": "Infra atual sem suporte e com limitações de throughput.",
        "PainImpact": "Risco de falhas e gargalos em períodos críticos.",
        "Renewal": False,
    },
]




def get_opportunity_info_by_id(
    opportunity_id: str
) -> OpportunityData:
    """Search opportunity fixtures by name.

    Returns:
      - On success: opportunity data with `Status="OK"`.
      - On failure: a small error payload with `Status` describing the issue.
    """
    normalized_query = opportunity_id.strip().upper()
    if not normalized_query or normalized_query == "*":
        return {
            "Status": "ERROR",
            "ErrorCode": "INVALID_ARGUMENT",
            "Message": "opportunity_id is required",
        }

    for oportunidade_info in _OPPORTUNITY_FIXTURES:
        if normalized_query == oportunidade_info["Id"].upper():
            return oportunidade_info

    return {
        "Status": "ERROR",
        "ErrorCode": "NOT_FOUND",
        "Message": "opportunity not found",
    }


def external_tools_function_handler(tool_name: str, args_obj: dict | None, ctx: ToolContext | None) -> dict[str, Any]:
    """
    Handles the execution of an external tool function and processes the result.

    This function takes a dictionary of parameters, processes them using an
    external tool functionality, and returns the resulting data in a specified
    format.

    Args:
        tool_name (str): The name of the external tool function to execute.
        args_obj (dict | None): A dictionary containing the parameters to
            process. If None, default behavior or configurations are applied.
        ctx (ToolContext | None, optional): Contexto opcional usado para logs verbosos. Defaults to None.

    Returns:
        dict[str, Any]: A dictionary containing the result of the processing,
            formatted as a key-value pair.
    """
    if ctx and getattr(ctx, "is_verbose", False):
        vlog(ctx, f"session={getattr(ctx, 'session_id', '-')}", func=tool_name)

    match tool_name:
        case "get_opportunity_info_by_id":
            opportunity_id = args_obj.get("opportunity_id")
            if opportunity_id is None:
                raise ValueError("opportunity_id is required")
            return get_opportunity_info_by_id(opportunity_id)

    raise ValueError(f"Unsupported tool name: {tool_name}")


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

    external_tools = [
        {
            "type": "function",
            "name": "get_opportunity_info_by_id",
            "description": "Use essa ferramenta para obter os dados de uma oportunidade que está no CRM, cujo código é fornecido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "opportunity_id": {"type": "string", "description": "Código da oportunidade no CRM"},
                },
                "required": ["opportunity_id"],
                "additionalProperties": False,
            },
        }
    ]

    ag_cfg = AgentConfig(
        system_prompt=system_prompt,
        tools_names=["get_opportunity_info_by_id"],
    )

    agent = Oskar(agent_config=ag_cfg,
                  response_callback=_response_log,
                  external_tools_schema=external_tools,
                  external_tools_function_handler=external_tools_function_handler,
                  is_verbose=True)

    # No explicit question provided: run a quick test prompt and exit
    # test_q = "Qual é a dor do cliente na oportunidade OPO-ORIZON-2024-08-0001?"
    test_q = "Qual é a dor do cliente na oportunidade OPO-FOO-2026-01-0007?"
    res = agent.answer(test_q)

    print(test_q)
    # Ensure UTF-8 characters are printed properly (no ASCII escapes)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
