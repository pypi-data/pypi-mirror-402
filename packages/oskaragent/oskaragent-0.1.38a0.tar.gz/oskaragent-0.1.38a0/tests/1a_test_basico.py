from __future__ import annotations

from typing import Any
import json

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
            },
    )

    agent = Oskar(agent_config=ag_cfg, response_callback=_response_log, is_verbose=True)

    # No explicit question provided: run a quick test prompt and exit
    test_q = "Quem é o presidente do Brasil?"
    res = agent.answer(test_q)

    print(test_q)
    # Ensure UTF-8 characters are printed properly (no ASCII escapes)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
