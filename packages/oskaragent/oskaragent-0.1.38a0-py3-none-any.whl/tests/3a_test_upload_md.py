from __future__ import annotations

from pathlib import Path
from typing import Any

from oskaragent.agent import Oskar
from oskaragent.agent_config import AgentConfig
from tests.helpers import set_key


def main() -> None:
    # Set OpenAI API key
    set_key()

    # Caminho do arquivo Markdown a ser resumido
    md_path = Path("sources/cristianismo.md").resolve()
    if not md_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {md_path}")

    # Instancia o agente oskaragent (com configurações padrão)
    agent_cfg = AgentConfig(
        model_settings={
            "history_window_size": 5,  # parametrizável
        },
    )
    agent = Oskar(agent_config=agent_cfg, is_verbose=True)

    # Pergunta ao agente para fazer um resumo do arquivo
    question = (
        "Por favor, leia o arquivo anexo e produza um resumo objetivo em português, "
        "destacando as ideias principais em 5–7 linhas."
    )
    result: dict[str, Any] = agent.answer(
        question=question,
        attached_files=str(md_path)
    )

    # Extrai e imprime o conteúdo da resposta (resumo)
    content = (result or {}).get("content") or ""
    print("Resumo gerado:\n")
    print(content)


if __name__ == "__main__":
    main()

