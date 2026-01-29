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

    # Allow the calculator tool explicitly (defaults are included, but we state intent)
    ag_cfg = AgentConfig(
        tools_names=[
            "calculator_tool",
        ],
        system_prompt=(
            "Você é um assistente focado em cálculos. Sempre que houver uma expressão matemática, "
            "use a ferramenta 'calculator_tool' para avaliar e retorne apenas o número final."
        ),
    )

    agent = Oskar(agent_config=ag_cfg, response_callback=_response_log, is_verbose=True)

    # Expression chosen to exercise math functions available to the tool
    # expression = "2**10 + sqrt(144) + sin(pi/2)"  # 1024 + 12 + 1 = 1037.0
    expression = "1024 + 12 + 1"  # 1024 + 12 + 1 = 1037.0
    question = (
        "Calcule a expressão a seguir usando a ferramenta calculator_tool e retorne apenas o número final: "
        f"{expression}"
    )

    res = agent.answer(question, action='tool:calculator_tool')

    # Ensure UTF-8 characters are printed properly (no ASCII escapes)
    print(json.dumps(res, indent=2, ensure_ascii=False))


    return 0


if __name__ == "__main__":
    raise SystemExit(main())
