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

    # Build initial agent configuration
    ag_cfg = AgentConfig(
        model_settings={"history_window_size": 5},
        system_prompt=(
            "Você é um assistente prestativo chamado oskaragent. Mantenha e use o histórico para responder coerentemente."
        ),
    )

    # Create the agent and send the first prompt
    agent = Oskar(agent_config=ag_cfg, response_callback=_response_log, is_verbose=True)
    q1 = "Minha cor preferida é azul. Qual é sua cor preferida?"
    print(f"\n[teste] Enviando primeira pergunta: {q1}")
    r1 = agent.answer(q1)
    print("[teste] Resposta 1:")
    print(r1['content'])

    # Export agent to JSON
    j = agent.to_json()

    # Destroy the agent (drop the reference)
    del agent

    # Recreate a new agent importing the exported JSON
    print("[teste] Recriando agente a partir do JSON exportado…")
    agent2 = Oskar.from_json(j, working_folder="./output")

    # Send the second prompt which relies on remembered history
    q2 = "Qual é minha cor preferida?"
    print(f"\n[teste] Enviando segunda pergunta: {q2}")
    r2 = agent2.answer(q2)
    print("[teste] Resposta 2:")
    print(r2['content'])

    # Simple check: expect the model/agent to answer "azul"
    content = (r2 or {}).get("content", "")
    ok = isinstance(content, str) and ("azul" in content.lower())
    status = "OK" if ok else "ATENÇÃO"
    print(f"\n[verificação] Esperado conter 'azul' → {status}")

    print('-' * 40)
    print(json.dumps(j, indent=2, ensure_ascii=False))

    print('-' * 40)
    print(json.dumps(agent2.to_json(), indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
