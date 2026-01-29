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


def main() -> int:
    # Set OpenAI API key
    set_key()

    # Allow tools we might want the model to call; not strictly required for this test
    ag_cfg = AgentConfig(
        tools_names=[
            "execute_python_code_tool",
        ],
        system_prompt=(
            "Você é um assistente com capacidade para executar código python usando a ferramenta 'execute_python_code_tool'."
        ),
    )

    agent = Oskar(agent_config=ag_cfg, response_callback=_response_log, is_verbose=True)

    question = (
        "Crie um bloco de código Python para gerar um gráfico de barras simples usando matplotlib com três categorias (A, B, C) e valores, "
        "adicionar rótulos de eixos e título, e chamar plt.show() no final. "
        "Execute o código gerado usando a ferramenta execute_python_code_tool e retorne apenas o resultado final."
    )

    res = agent.answer(question)

    # Ensure UTF-8 characters are printed properly (no ASCII escapes)
    print(json.dumps(res, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
