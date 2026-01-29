from __future__ import annotations

from pathlib import Path
from typing import Any

from oskaragent.agent import Oskar
from oskaragent.agent_config import AgentConfig

from tests.helpers import set_key


def main() -> None:
    # Set OpenAI API key
    set_key()

    # Caminho dos arquivos pdf para comparação
    pdf1_path = Path("sources/GlobalThreatReport2024.pdf").resolve()
    if not pdf1_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {pdf1_path}")

    pdf2_path = Path("sources/comptia-state-of-cybersecurity-2025.pdf").resolve()
    if not pdf2_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {pdf2_path}")

    # Instancia o agente oskaragent (com configurações padrão)
    agent = Oskar(agent_config=AgentConfig(), is_verbose=True)

    # Pergunta ao agente para fazer um resumo do arquivo
    question = "Faça uma análise comparativa desses dois documentos PDF e apresente o resultado em português."

    result: dict[str, Any] = agent.answer(
        question=question,
        attached_files=[str(pdf1_path), str(pdf2_path)]
    )

    # Extrai e imprime o conteúdo da resposta (resumo)
    content = (result or {}).get("content") or ""
    print("Resumo gerado:\n")
    print(content)


if __name__ == "__main__":
    main()

