from __future__ import annotations

from pathlib import Path
from typing import Any

from oskaragent.agent import Oskar
from oskaragent.agent_config import AgentConfig
from tests.helpers import set_key


def main() -> None:
    # Set OpenAI API key
    set_key()

    # Caminho do arquivo de imagem a ser descrito
    img_path = (Path(__file__).parent / "sources" / "img_pent.png").resolve()
    if not img_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {img_path}")

    # Instancia o agente oskaragent (configuração simples)
    agent_cfg = AgentConfig(
        model_settings={
            "history_window_size": 5,  # parametrizável
        },
    )
    agent = Oskar(agent_config=agent_cfg, is_verbose=False)

    # Pergunta ao agente para descrever a imagem
    question = "Descreva a imagem anexada em detalhes em português."
    result: dict[str, Any] = agent.answer(
        question=question,
        attached_files=str(img_path)
    )

    # Extrai e imprime o conteúdo da resposta (descrição)
    content = (result or {}).get("content") or ""
    print("Descrição gerada:\n")
    print(content)


if __name__ == "__main__":
    main()

