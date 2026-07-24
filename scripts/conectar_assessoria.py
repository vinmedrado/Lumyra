import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from integrations.assessoria_embedded import abrir_login_assessoria

ARQUIVO_SAIDA = BASE_DIR / "data" / "assessoria_contexto.json"


def main():
    ctx = abrir_login_assessoria()

    if not ctx:
        print("Contexto não capturado.")
        return

    ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(ctx, f, indent=2, ensure_ascii=False)

    print("Contexto salvo com sucesso:")
    print(ARQUIVO_SAIDA.resolve())
    print(ctx)


if __name__ == "__main__":
    main()