"""Genera hashes de PIN individuales para Streamlit Secrets.

Uso: python scripts/generate_pin_hash.py
No almacena ni imprime el PIN, únicamente el hash resultante.
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.auth import hash_pin  # noqa: E402


def main() -> None:
    name = input("Nombre exacto del usuario: ").strip()
    pin1 = getpass.getpass("PIN (mínimo 6 caracteres): ")
    pin2 = getpass.getpass("Confirmar PIN: ")
    if pin1 != pin2:
        raise SystemExit("Los PIN no coinciden.")
    try:
        hashed = hash_pin(pin1)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    escaped = name.replace('"', '\\"')
    print("\nAgrega esta línea bajo [PIN_HASHES] en Secrets:")
    print(f'"{escaped}" = "{hashed}"')


if __name__ == "__main__":
    main()
