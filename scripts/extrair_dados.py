import re
import json
import unicodedata
from pathlib import Path
from pypdf import PdfReader


# =========================================================
# CAMINHOS
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

PDF_LISTA = DATA_DIR / "lista.pdf"
ARQUIVO_JSON = DATA_DIR / "base_convidados.json"
ARQUIVO_TXT = DATA_DIR / "nomes_extraidos.txt"


# =========================================================
# UTILITÁRIOS
# =========================================================
def normalizar_texto(texto: str) -> str:
    texto = str(texto).strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def normalizar_nome(nome: str) -> str:
    return normalizar_texto(nome).upper()


def ler_pdf(caminho_pdf: Path) -> str:
    reader = PdfReader(str(caminho_pdf))
    partes = []

    for pagina in reader.pages:
        texto = pagina.extract_text()
        if texto:
            partes.append(texto)

    return "\n".join(partes)


def remover_duplicados_por_chave(lista: list[dict]) -> list[dict]:
    vistos = set()
    resultado = []

    for item in lista:
        chave = (
            item["nome"],
            item["categoria"],
            item["tipo"],
            item["grupo"],
            item["mesa_atual"],
        )
        if chave not in vistos:
            vistos.add(chave)
            resultado.append(item)

    return resultado


def normalizar_tipo(tipo: str | None) -> str | None:
    if not tipo:
        return None

    tipo = normalizar_texto(tipo)
    mapa = {
        "Adulto": "Adulto",
        "Adolescente": "Adolescente",
        "Crianca": "Criança",
        "Crianca de colo": "Criança de colo",
        "Idoso": "Idoso",
        "Free": "Free",
    }
    return mapa.get(tipo, tipo)


def normalizar_mesa(valor_mesa: str | None) -> str | None:
    if not valor_mesa:
        return None

    valor_mesa = normalizar_texto(valor_mesa)

    if valor_mesa in {"--", "-", ""}:
        return None

    match_familia = re.match(
        r"^(\d+)\s+mesa da familia$",
        valor_mesa,
        flags=re.IGNORECASE
    )
    if match_familia:
        return f"Mesa {int(match_familia.group(1))} mesa da familia"

    match_num = re.match(r"^0*(\d+)$", valor_mesa)
    if match_num:
        return f"Mesa {int(match_num.group(1))}"

    if valor_mesa.lower().startswith("mesa "):
        return valor_mesa[0].upper() + valor_mesa[1:]

    return valor_mesa


# =========================================================
# EXTRAÇÃO PRINCIPAL
# =========================================================
def extrair_convidados(texto: str) -> list[dict]:
    linhas = [linha.rstrip() for linha in texto.splitlines() if linha.strip()]
    convidados = []

    i = 0
    while i < len(linhas):
        linha = normalizar_texto(linhas[i])

        # cada convidado começa com " Nome"
        if not linha.startswith(""):
            i += 1
            continue

        nome_original = normalizar_texto(linha.replace("", "", 1))

        # tenta ler a linha seguinte com os metadados
        detalhe = ""
        if i + 1 < len(linhas):
            detalhe = normalizar_texto(linhas[i + 1])

        # se a próxima linha for cabeçalho/rodapé/outro bloco, ignora detalhe
        if (
            detalhe.startswith("")
            or detalhe.startswith("08/04/26")
            or detalhe.startswith("https://")
            or detalhe.startswith("LISTA DE CONVIDADOS")
            or detalhe.startswith("Caroline Aguinel Ferreira Pinto")
            or detalhe.startswith("Medrado")
            or detalhe.startswith("05/06/2026")
            or detalhe.startswith("94 Convite(s)")
            or detalhe.startswith("243 Convidados")
            or detalhe.startswith("186 Confirmados")
            or detalhe.startswith("54 Pendentes")
            or detalhe.startswith("3 Nao")
            or detalhe.startswith("comparecerao")
            or detalhe.startswith("0 Idoso")
            or detalhe.startswith("7 Crianca de colo")
            or detalhe.startswith("159 Inteira")
            or detalhe.startswith("88 97 0 1")
        ):
            detalhe = ""

        categoria = None
        tipo = None
        grupo = None
        mesa_atual = None
        status_mesa = "sem_mesa_pdf"

        if detalhe:
            # categoria = tudo antes do primeiro |
            partes = [normalizar_texto(p) for p in detalhe.split("|")]

            if len(partes) >= 1:
                categoria = partes[0]

            for parte in partes[1:]:
                if parte.startswith("Convite:"):
                    grupo = normalizar_texto(parte.replace("Convite:", "", 1))
                elif parte.startswith("Mesa:"):
                    mesa_raw = normalizar_texto(parte.replace("Mesa:", "", 1))
                    mesa_atual = normalizar_mesa(mesa_raw)
                    status_mesa = "mesa_confirmada" if mesa_atual else "sem_mesa_pdf"
                else:
                    tipo = normalizar_tipo(parte)

        convidados.append({
            "nome": normalizar_nome(nome_original),
            "nome_original": nome_original,
            "categoria": categoria,
            "tipo": tipo,
            "grupo": grupo,
            "mesa_atual": mesa_atual,
            "mesa_corrigida": None,
            "mesa_final": mesa_atual,
            "status_mesa": status_mesa
        })

        i += 2

    return remover_duplicados_por_chave(convidados)


# =========================================================
# APOIO
# =========================================================
def calcular_capacidades(convidados: list[dict]) -> dict:
    """
    Como este PDF não traz a capacidade de cada mesa diretamente em cada bloco,
    aqui calculamos só a ocupação atual.
    Depois, se você quiser, eu adapto para juntar com seu PDF de mapeamento
    e recuperar a capacidade máxima também.
    """
    ocupacao = {}

    for convidado in convidados:
        mesa = convidado["mesa_atual"]
        if mesa:
            ocupacao[mesa] = ocupacao.get(mesa, 0) + 1

    return dict(sorted(ocupacao.items(), key=lambda x: x[0]))


def salvar_txt_conferencia(convidados: list[dict], caminho_txt: Path) -> None:
    convidados_ordenados = sorted(
        convidados,
        key=lambda x: (
            x["mesa_atual"] is None,
            x["mesa_atual"] or "",
            x["nome"]
        )
    )

    with open(caminho_txt, "w", encoding="utf-8") as f:
        for c in convidados_ordenados:
            mesa = c["mesa_atual"] if c["mesa_atual"] else "SEM_MESA"
            categoria = c["categoria"] if c["categoria"] else "-"
            tipo = c["tipo"] if c["tipo"] else "-"
            grupo = c["grupo"] if c["grupo"] else "-"
            f.write(f"{mesa} | {c['nome_original']} | {tipo} | {grupo} | {categoria}\n")


def gerar_resumo(convidados: list[dict]) -> dict:
    ocupacao = calcular_capacidades(convidados)
    nomes = [c["nome"] for c in convidados]
    duplicados = sorted({n for n in nomes if nomes.count(n) > 1})

    total_extraido = len(convidados)
    total_oficial = total_extraido

    return {
        "total_oficial_pdf": total_oficial,
        "total_convidados_extraidos": total_extraido,
        "faltando_localizar": total_oficial - total_extraido,
        "total_mesa_confirmada": sum(1 for c in convidados if c["mesa_atual"] is not None),
        "total_sem_mesa_pdf": sum(1 for c in convidados if c["mesa_atual"] is None),
        "total_com_grupo": sum(1 for c in convidados if c["grupo"]),
        "total_com_categoria": sum(1 for c in convidados if c["categoria"]),
        "total_com_tipo": sum(1 for c in convidados if c["tipo"]),
        "total_duplicados_detectados": len(duplicados),
        "duplicados_detectados": duplicados,
        "ocupacao_por_mesa": ocupacao
    }


# =========================================================
# MAIN
# =========================================================
def main():
    if not PDF_LISTA.exists():
        print(f"[ERRO] Arquivo não encontrado: {PDF_LISTA}")
        return

    print("[1/4] Lendo PDF de convidados...")
    texto = ler_pdf(PDF_LISTA)

    print("[2/4] Extraindo convidados...")
    convidados = extrair_convidados(texto)

    print("[3/4] Gerando resumo...")
    resumo = gerar_resumo(convidados)

    saida = {
        "resumo": resumo,
        "convidados": convidados
    }

    print("[4/4] Salvando arquivos...")
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(saida, f, indent=2, ensure_ascii=False)

    salvar_txt_conferencia(convidados, ARQUIVO_TXT)

    print("\n[OK] Arquivos gerados com sucesso:")
    print(f" - JSON: {ARQUIVO_JSON}")
    print(f" - TXT : {ARQUIVO_TXT}")

    print("\n[RESUMO]")
    print(json.dumps(resumo, indent=2, ensure_ascii=False))

    print("\n[CONFERÊNCIA FINAL]")
    print(f"Total oficial do PDF : {resumo['total_oficial_pdf']}")
    print(f"Total extraído script: {resumo['total_convidados_extraidos']}")
    print(f"Faltando localizar   : {resumo['faltando_localizar']}")


if __name__ == "__main__":
    main()