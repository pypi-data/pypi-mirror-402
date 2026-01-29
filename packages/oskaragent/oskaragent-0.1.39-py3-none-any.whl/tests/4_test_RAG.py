from __future__ import annotations

from typing import Any

from tests.helpers import set_key
from oskaragent.agent import Oskar
from oskaragent.agent_config import AgentConfig


def main() -> None:
    """Execute smoke test forcing local RAG retriever against the psicologia base."""
    # Set OpenAI API key
    set_key()

    # cria a base de dados RAG
    # create_knowledge_base_from_file(knowledge_base_name="psicologia",
    #                                 knowledge_base_folder="./sources/vectorstore",
    #                                 file_path="./sources/artigo psicologia.md")

    # Configura o agente para usar o índice local de RAG
    ag_cfg = AgentConfig(
        knowledge_base=[
            {
                "name": "psicologia",
                "folder": "./sources/vectorstore"
            }
        ]
        # Observação: para habilitar o retriever local, também é possível
        # informar `working_dbs=["./sources/vectorstore"]`. Aqui seguimos exatamente o pedido.
    )

    # Ativar logs detalhados para ver chamadas de ferramenta (inclui logs azuis)
    agent = Oskar(agent_config=ag_cfg, is_verbose=True)

    question = "Quantas sessões foram realizadas?"
    # Força o uso do RAG local chamando explicitamente a ferramenta de recuperação
    # Caso prefira deixar o modelo decidir, use action="chat".
    result: dict[str, Any] = agent.answer(
        question=question,
        action="tool:retriever_tool",
        message_format="raw",
        is_consult_prompt=False,
    )

    # Imprime apenas o conteúdo textual da resposta
    content = (result or {}).get("content")
    if content:
        print(content)
    else:
        # Fallback: imprime o objeto completo para facilitar o debug
        import json as _json
        print(_json.dumps(result or {}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
