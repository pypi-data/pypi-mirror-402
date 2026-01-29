from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml


def load_keys() -> str | None:
    """
    Carrega o YAML de chaves de acesso.

    :return:
    """
    root = Path(__file__).resolve().parent.parent
    keys_path = root / "tests" / "keys.yaml"

    if keys_path.exists():
        with open(keys_path, 'r', encoding='UTF-8') as file:
            keys_str = file.read()
        return keys_str
    # endiif --

    return None


def get_key(key: str = None) -> Optional[str]:
    """Return the OPENAI_API_KEY value from the project root `keys.yaml`.

    Looks for `keys.yaml` in the same directory as this file (the project root)
    and extracts the value of the `OPENAI_API_KEY` entry without requiring a YAML
    parser dependency.
    """
    keys_yaml = yaml.load(load_keys(), Loader=yaml.FullLoader)

    if key is None:
        # retorna a chave da OpenAI
        return keys_yaml.get('OPENAI_API_KEY', None)

    if '.' not in key:
        return keys_yaml.get(key, None)
    # endfor --

    tks = key.split('.')
    value = keys_yaml

    for tk in tks:
        if not value:
            return None

        value = value.get(tk)
    # endfor --

    return value


def set_key():
    key = get_key()
    os.environ["OPENAI_API_KEY"] = key