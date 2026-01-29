from __future__ import annotations

from typing import Any
import json

from tests.helpers import set_key
from oskaragent.agent import Oskar


def _response_log(assistant_message_struct: dict[str, Any]):
    usage = assistant_message_struct.get("usage", {}) or {}
    print(
            f"[callback] message_id={assistant_message_struct.get('message_id')} "
            f"tokens={{'input_tokens': {usage.get('input_tokens')}, 'output_tokens': {usage.get('output_tokens')}, 'total_tokens': {usage.get('total_tokens')}}}"
    )


def main() -> int:
    # Set OpenAI API key
    set_key()

    mcp_tools = [
        {
            "mcpServerUrl": "http://localhost:8001/mcp",
            "tools": ["get_salesforce_case_info_by_id"]
        }
    ]

    agent = Oskar(input_data={"ticket": 42555},
                  response_callback=_response_log,
                  mcp_tools=mcp_tools,
                  is_verbose=True)

    # No explicit question provided: run a quick test prompt and exit
    test_q = 'Faça uma síntese do ticket {ticket}.'
    res = agent.answer(test_q)

    print(test_q)
    # Ensure UTF-8 characters are printed properly (no ASCII escapes)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
