import json
import re
import unicodedata
from pathlib import Path

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ARQUIVO_CONTEXTO = DATA_DIR / "assessoria_contexto.json"

URL = "https://api.assessoriavip.com.br/graphql"

QUERY_EVENT_TABLES = """
query eventTables($eventId: Int!, $filter: EventTableInputFilter, $filterOccupiedSeats: EventTableOccupiedSeatsInputFilter) {
  event(eventId: $eventId) {
    id
    tables(filter: $filter) {
      id
      name
      observation
      totalSeats
      occupiedSeats(filter: $filterOccupiedSeats)
      guests {
        id
        name
        type
        cost
        situation
        eventTable {
          id
          name
          __typename
        }
        group {
          id
          name
          color
          isDefault
          __typename
        }
        invitation {
          id
          name
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
}
"""
QUERY_EVENT_GUESTS = """
query eventGuests($eventId: Int!) {
  event(eventId: $eventId) {
    id
    invitations {
      id
      name
      guests {
        id
        name
        type
        situation
      }
    }
  }
}
"""

QUERY_INVITATION_BY_ID = """
query invitationById($id: Int!) {
  invitation(id: $id) {
    id
    name
    guests {
      id
      name
      type
      situation
    }
  }
}
"""

QUERY_MOVER = """
mutation ($tableId: Int!, $guestIds: [Int]!) {
  moveGuestsToTableReturningModifiedTables(
    tableId: $tableId,
    guestIds: $guestIds
  ) {
    id
    name
    occupiedSeats
  }
}
"""

def buscar_invitation_por_id(token: str, invitation_id: int) -> dict:
    data = graphql_request(
        QUERY_INVITATION_BY_ID,
        {"id": invitation_id},
        token=token,
        operation_name="invitationById",
    )

    return data.get("data", {}).get("invitation", {})

def buscar_invitation_por_id(token: str, invitation_id: int) -> dict:
    data = graphql_request(
        QUERY_INVITATION_BY_ID,
        {"id": invitation_id},
        token=token,
        operation_name="invitationById",
    )

    return data.get("data", {}).get("invitation", {})

def buscar_todos_guests_evento(token: str, event_id: int) -> list[dict]:
    data = graphql_request(
        """
        query eventInvitations($eventId: Int!) {
          event(eventId: $eventId) {
            id
            invitations(limit: 200) {
              id
              name
            }
          }
        }
        """,
        {"eventId": event_id},
        token=token,
        operation_name="eventInvitations",
    )

    event = data.get("data", {}).get("event", {})
    invitations = event.get("invitations", [])

    guests = []
    vistos = set()

    for invitation in invitations:
        invitation_id = invitation.get("id")
        if not invitation_id:
            continue

        convite_completo = buscar_invitation_por_id(token, int(invitation_id))

        for guest in convite_completo.get("guests", []):
            guest_id = guest.get("id")
            if guest_id and guest_id not in vistos:
                vistos.add(guest_id)
                guests.append(guest)

    return guests


def montar_mapa_guest_ids_completo(token: str, event_id: int) -> dict[str, int]:
    guests = buscar_todos_guests_evento(token, event_id)

    mapa = {}
    for guest in guests:
        nome = normalizar_nome(guest.get("name"))
        guest_id = guest.get("id")

        if nome and guest_id and nome not in mapa:
            mapa[nome] = int(guest_id)

    return mapa

def normalizar_nome(texto: str) -> str:
    if not texto:
        return ""
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"\s+", " ", texto)
    return texto


def extrair_token_do_user_storage(user_storage_raw: str) -> str:
    data = json.loads(user_storage_raw)
    token = data.get("token")
    if not token:
        raise ValueError("Token não encontrado no JSON do localStorage user.")
    return token


def extrair_event_id_do_referrer_path(referrer_path: str) -> int:
    match = re.search(r"/invitationManagement/(\d+)/mapping", str(referrer_path))
    if not match:
        raise ValueError("eventId não encontrado no referrer path.")
    return int(match.group(1))


def carregar_contexto_salvo() -> dict:
    if not ARQUIVO_CONTEXTO.exists():
        raise FileNotFoundError(
            f"Arquivo de contexto não encontrado: {ARQUIVO_CONTEXTO}"
        )

    with open(ARQUIVO_CONTEXTO, "r", encoding="utf-8") as f:
        contexto = json.load(f)

    return contexto


def obter_token_do_contexto(contexto: dict) -> str:
    token = contexto.get("token")
    if token:
        return token

    user_raw = contexto.get("user_raw")
    if user_raw:
        return extrair_token_do_user_storage(user_raw)

    raise ValueError("Token não encontrado no contexto salvo.")


def obter_event_id_do_contexto(contexto: dict) -> int:
    event_id = contexto.get("event_id")
    if event_id:
        return int(event_id)

    referrer_path = contexto.get("referrer_path")
    if referrer_path:
        return extrair_event_id_do_referrer_path(referrer_path)

    raise ValueError("event_id não encontrado no contexto salvo.")


def obter_token_e_event_id_do_contexto() -> tuple[str, int]:
    contexto = carregar_contexto_salvo()
    token = obter_token_do_contexto(contexto)
    event_id = obter_event_id_do_contexto(contexto)
    return token, event_id


def montar_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Origin": "https://assessoriavip.com.br",
        "Referer": "https://assessoriavip.com.br/",
    }


def graphql_request(
    query: str,
    variables: dict,
    token: str,
    operation_name: str | None = None,
):
    payload = {
        "query": query,
        "variables": variables,
    }

    if operation_name:
        payload["operationName"] = operation_name

    resp = requests.post(
        URL,
        json=payload,
        headers=montar_headers(token),
        timeout=30,
    )

    if not resp.ok:
        try:
            detalhe = resp.json()
        except Exception:
            detalhe = resp.text
        raise RuntimeError(f"Erro HTTP {resp.status_code}: {detalhe}")

    data = resp.json()

    if data.get("errors"):
        raise RuntimeError(f"Erro GraphQL: {data['errors']}")

    return data


def buscar_evento_com_mesas(token: str, event_id: int):
    variables = {
        "eventId": event_id,
        "filter": {
            "_OR": ["name", "invitationName", "guestName"],
            "name": "",
            "guestName": "",
            "invitationName": "",
            "guestSituations": [],
            "guestTypes": [],
            "hasGuestType": None,
            "invitationGroupIds": [],
            "occupationStatus": [],
        },
        "filterOccupiedSeats": None,
    }

    data = graphql_request(
        QUERY_EVENT_TABLES,
        variables,
        token=token,
        operation_name="eventTables",
    )

    return data["data"]["event"]


def montar_mapa_mesas(token: str, event_id: int) -> dict[str, int]:
    event = buscar_evento_com_mesas(token, event_id)

    mapa = {}
    for mesa in event.get("tables", []):
        nome_mesa = str(mesa.get("name", "")).strip()
        mesa_id = mesa.get("id")

        if nome_mesa and mesa_id:
            mapa[f"Mesa {nome_mesa}"] = int(mesa_id)

    return mapa


def montar_mapa_mesas_auto() -> dict[str, int]:
    token, event_id = obter_token_e_event_id_do_contexto()
    return montar_mapa_mesas(token, event_id)


def montar_mapa_guest_ids(token: str, event_id: int) -> dict[str, int]:
     return montar_mapa_guest_ids_completo(token, event_id)


def preencher_guest_ids_no_df(df: pd.DataFrame, token: str, event_id: int) -> pd.DataFrame:
    guests = buscar_todos_guests_evento(token, event_id)
    df2 = df.copy()

    if "guest_id" not in df2.columns:
        df2["guest_id"] = None

    if "guest_type" not in df2.columns:
        df2["guest_type"] = None

    mapa_guests = {}
    for guest in guests:
        nome = normalizar_nome(guest.get("name"))
        guest_id = guest.get("id")
        guest_type = guest.get("type")

        if nome and guest_id and nome not in mapa_guests:
            mapa_guests[nome] = {
                "guest_id": int(guest_id),
                "guest_type": guest_type,
            }

    coluna_nome = "nome_original" if "nome_original" in df2.columns else "nome"

    def buscar_dados_guest(nome):
        nome_norm = normalizar_nome(nome)
        info = mapa_guests.get(nome_norm)

        if not info:
            return pd.Series([None, None])

        return pd.Series([info["guest_id"], info["guest_type"]])

    df2[["guest_id", "guest_type"]] = df2[coluna_nome].apply(buscar_dados_guest)

    return df2

def preencher_guest_ids_no_df_auto(df: pd.DataFrame) -> pd.DataFrame:
    token, event_id = obter_token_e_event_id_do_contexto()
    return preencher_guest_ids_no_df(df, token, event_id)


def mover_convidados(table_id: int, guest_ids: list[int], token: str):
    return graphql_request(
        QUERY_MOVER,
        {"tableId": table_id, "guestIds": guest_ids},
        token=token,
    )


def sincronizar_assessoria(df: pd.DataFrame):
    token, event_id = obter_token_e_event_id_do_contexto()
    mapa_mesas = montar_mapa_mesas(token, event_id)

    if "mesa_final" not in df.columns:
        raise ValueError("DataFrame sem coluna 'mesa_final'.")

    if "guest_id" not in df.columns or df["guest_id"].isna().all():
        df = preencher_guest_ids_no_df(df, token, event_id)

    if "guest_type" not in df.columns:
        df["guest_type"] = None

    total_movidos = 0
    total_mesas = 0

    for mesa in df["mesa_final"].dropna().unique():
        convidados = df[df["mesa_final"] == mesa].copy()

        guest_ids = convidados[
            (convidados["guest_id"].notna()) &
            (convidados["guest_type"].fillna("") != "FREE")
        ]["guest_id"].astype(int).tolist()

        if not guest_ids:
            continue

        table_id = mapa_mesas.get(mesa)
        if not table_id:
            continue

        mover_convidados(table_id, guest_ids, token)
        total_movidos += len(guest_ids)
        total_mesas += 1

    return {
        "status": "ok",
        "event_id": event_id,
        "mesas_atualizadas": total_mesas,
        "convidados_movidos": total_movidos,
        "df": df,
    }
