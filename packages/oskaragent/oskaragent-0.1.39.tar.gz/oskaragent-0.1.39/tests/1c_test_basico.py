from __future__ import annotations

from textwrap import dedent
from typing import Any

from oskaragent.agent import Oskar
from oskaragent.agent_config import AgentConfig
from tests.helpers import set_key


def _response_log(assistant_message_struct: dict[str, Any]):
    usage = assistant_message_struct.get("usage", {}) or {}
    print(
            f"[callback] message_id={assistant_message_struct.get('message_id')} "
            f"tokens={{'input_tokens': {usage.get('input_tokens')}, 'output_tokens': {usage.get('output_tokens')}, 'total_tokens': {usage.get('total_tokens')}}}"
    )


def main() -> int:
    # Set OpenAI API key
    set_key()

    ag_cfg = AgentConfig(
        model="gpt-5",
        model_settings={
            "history_window_size": 5,  # parametrizável
        }
    )

    agent = Oskar(agent_config=ag_cfg, response_callback=_response_log, is_verbose=True)

    # No explicit question provided: run a quick test prompt and exit
    test_q = dedent("""
        Estou desenvolvendo um programa CLI em Python para conversar com agentes de IA.
        
        Quero que você:
        
        1. Defina uma arquitetura de alto nível para o programa.
        2. Proponha a estrutura de diretórios e arquivos.
        3. Explique o fluxo de execução principal.
        4. Indique como persistir histórico de conversas por agente.
        5. Liste riscos técnicos e como mitigá-los.
        
        Restrições:
        - O programa deve funcionar no Windows.
        - Deve ser compatível com Python 3.12+.
        - O design deve permitir adicionar novos agentes sem alterar o núcleo.
        - A resposta deve ser estruturada em seções claras.
        
        Não escreva código agora. Foque apenas em arquitetura e decisões técnicas.
        """)
    res = agent.answer(test_q)

    print(test_q)
    # Ensure UTF-8 characters are printed properly (no ASCII escapes)
    print(res['content'])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
