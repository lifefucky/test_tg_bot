from typing import Any, List, Optional

import requests

PROCEDURES_URL = "https://api.onlc.ru/purchases/v1/public/procedures"
POSITIONS_URL_TEMPLATE = "https://api.onlc.ru/purchases/v1/public/procedures/{}/positions"


class OnlineContract:
    procedures_kc = [
        "id",
        "type",
        "name",
        "date",
        "status",
        "useNDS",
        "nds",
        "reBiddingStart",
        "reBiddingEnd",
        "owner",
    ]

    def __init__(self) -> None:
        self.procedures_params: dict[str, Any] = {}

    def build_procedures_params(self, categories: List[str]) -> "OnlineContract":
        self.procedures_params = {
            "total": True,
            "limit": 100,
            "offset": 0,
            "include": "owner",
            "sort": "-startAt",
            "filters[status]": 1,
            "filters[searchType]": 2,
            "filters[categories]": categories,
        }
        return self

    def fetch_current_procedures(self) -> dict[str, Any]:
        response = requests.get(PROCEDURES_URL, params=self.procedures_params, timeout=60)
        if response.status_code != 200:
            return {}
        try:
            return response.json()
        except ValueError:
            return {}

    def get_procedures(self, categories: List[str]) -> Optional[List[dict[str, Any]]]:
        """
        Returns None if the API request failed or the response was invalid.
        Returns [] if the request succeeded but there are no procedures.
        """
        self.build_procedures_params(categories)
        raw = self.fetch_current_procedures()
        if not raw:
            return None
        rows = raw.get("data")
        if rows is None:
            return None
        if not rows:
            return []

        out: list[dict[str, Any]] = []
        for row in rows:
            owner = row.get("owner")
            owner_name = owner.get("name", "") if isinstance(owner, dict) else ""
            item = {k: row.get(k) for k in self.procedures_kc if k != "owner"}
            item["owner"] = owner_name
            pid = row.get("id")
            item["link"] = f"https://onlinecontract.ru/tenders/{pid}"
            out.append(item)
        return out

    @staticmethod
    def fetch_positions_for_procedure(procedure_id: str) -> dict[str, Any]:
        url = POSITIONS_URL_TEMPLATE.format(procedure_id)
        response = requests.get(url, timeout=60)
        if response.status_code != 200:
            return {}
        try:
            return response.json()
        except ValueError:
            return {}

    def get_positions(self, procedure_id: str) -> Optional[dict[str, Any]]:
        data = self.fetch_positions_for_procedure(procedure_id)
        if not data:
            return None
        rows = data.get("data")
        if rows is None:
            return None
        if not rows:
            common_message_unique: dict[str, Any] = {"Id": str(procedure_id)}
            return {"common_message": common_message_unique, "positions": []}

        position_keys = ["name", "totalCount", "unit", "price"]
        common_message_keys = ["ownerSrok", "ownerSklad", "deliveryPlace"]

        common_message = [{key: row.get(key) for key in common_message_keys} for row in rows]
        common_message_unique = list({frozenset(d.items()): d for d in common_message}.values())

        if len(common_message_unique) == 1:
            common_message_unique_dict: Any = common_message_unique[0]
        else:
            common_message_unique_dict = {}
            position_keys = position_keys + common_message_keys

        if isinstance(common_message_unique_dict, dict):
            common_message_unique_dict.setdefault("Id", str(procedure_id))

        positions = [{key: row.get(key) for key in position_keys} for row in rows]
        return {"common_message": common_message_unique_dict, "positions": positions}
