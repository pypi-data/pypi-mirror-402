from __future__ import annotations

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

    # ------------- agente subordinado
    ag_cfg = AgentConfig(
            agent_id="AssistenteOskar",
            agent_name="Assistente do oskaragent",
            system_prompt="""
                Você conhece todos os colaboradores da empresa.
                Quando for perguntado, você informar o cargo de qualquer um deles.
                Segue a lista dos colaboradores:
                - José Carlos: Programador
                - Elisa: Gerente de Financeiro
                - Jacques: Diretor
                - Maria: Analista de BI
                """,
    )
    agent_assistente = Oskar(agent_config=ag_cfg, response_callback=_response_log, is_verbose=True)

    # ------------- agente orquestrador
    ag_cfg = AgentConfig(
            agent_name="Chefe",
            model_settings={"history_window_size": 5},
    )
    agent_chefe = Oskar(agent_config=ag_cfg, response_callback=_response_log, is_verbose=True)

    agent_chefe.add_subordinated_agent(agent_assistente,
                                       role="Conhece todos os colaboradores da empresa e pode informar o cargo de qualquer um deles.")
    test_q = "Qual é o cargo do colaborador Jacques?"
    res = agent_chefe.answer(test_q)

    print(test_q)
    # Ensure UTF-8 characters are printed properly (no ASCII escapes)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
