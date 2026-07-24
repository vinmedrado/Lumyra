from __future__ import annotations

import re


def only_digits(value: object) -> str:
    """Retorna somente números, sem espaços, parênteses, hífens ou símbolos."""
    return re.sub(r"\D+", "", str(value or ""))


def normalize_phone(phone: str) -> str:
    """Normaliza telefone brasileiro para dígitos com DDI 55.

    Aceita formatos como:
    - 11999999999
    - 5511999999999
    - (11) 99999-9999
    - +55 11 99999-9999

    Retorna string vazia quando o telefone não atende às regras mínimas.
    """
    digits = only_digits(phone)
    if not digits:
        return ""

    # Alguns exports de agenda salvam prefixo internacional como 0055.
    if digits.startswith("0055"):
        digits = digits[2:]

    if digits.startswith("55"):
        national = digits[2:]
        if len(national) not in {10, 11}:
            return ""
        return f"55{national}"

    if len(digits) in {10, 11}:
        return f"55{digits}"

    return ""


def is_valid_phone(phone: str) -> bool:
    """Valida telefone brasileiro já normalizado ou em formato livre."""
    normalized = normalize_phone(phone)
    if not normalized or not normalized.startswith("55"):
        return False
    national = normalized[2:]
    if len(national) not in {10, 11}:
        return False
    ddd = national[:2]
    if ddd.startswith("0") or ddd == "00":
        return False
    return True
