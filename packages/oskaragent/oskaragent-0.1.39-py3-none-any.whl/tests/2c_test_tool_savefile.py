from __future__ import annotations

import json
from typing import Any

from tests.helpers import set_key
from oskaragent.agent import Oskar
from oskaragent.agent_config import AgentConfig


def _response_log(assistant_message_struct: dict[str, Any]):
    usage = assistant_message_struct.get("usage", {}) or {}
    print(
        f"[callback] message_id={assistant_message_struct.get('message_id')} "
        f"tokens={{'input_tokens': {usage.get('input_tokens')}, 'output_tokens': {usage.get('output_tokens')}, 'total_tokens': {usage.get('total_tokens')}}}"
    )


def main() -> None:
    # Set OpenAI API key
    set_key()

    # Habilita explicitamente a ferramenta de escrita em arquivo
    ag_cfg = AgentConfig(
        tools_names=[
            "write_file_tool",
        ],
        system_prompt=(
            "Você é um agente chamado oskaragent. Quando solicitado a salvar conteúdo, "
            "use a ferramenta 'write_file_tool'."
        ),
    )

    agent = Oskar(agent_config=ag_cfg, response_callback=_response_log, is_verbose=True)

    # 1) Expressão regular para telefone internacional
    q1 = "Gere um diagrama plantuml de uma expressão regular para telefone internacional."
    agent.answer(q1)
    print("[q1] enviado")

    # 3) Solicitar que o agente salve o diagrama em arquivo (sem ação explícita)
    q3 = "Salve o diagrama plantuml num arquivo."
    r3 = agent.answer(q3)

    # Imprime o JSON completo da última resposta
    print(json.dumps(r3, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
