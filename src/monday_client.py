from __future__ import annotations

from datetime import datetime
import json
from typing import Any

import requests


class MondayAPIError(RuntimeError):
    pass


class MondayClient:
    def __init__(self, api_token: str, api_url: str = "https://api.monday.com/v2") -> None:
        self.api_token = api_token
        self.api_url = api_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": self.api_token,
                "Content-Type": "application/json",
            }
        )

    def _post(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        response = self.session.post(
            self.api_url,
            data=json.dumps({"query": query, "variables": variables}),
            timeout=30,
        )
        if response.status_code >= 400:
            raise MondayAPIError(f"HTTP {response.status_code}: {response.text}")

        payload = response.json()
        if payload.get("errors"):
            raise MondayAPIError(str(payload["errors"]))
        return payload["data"]

    def fetch_board_items(self, board_id: str, page_size: int = 500) -> list[dict[str, Any]]:
        # Cursor-based pagination keeps memory predictable and works for large boards.
        query = """
        query ($boardId: ID!, $limit: Int!, $cursor: String) {
          boards(ids: [$boardId]) {
            id
            name
            items_page(limit: $limit, cursor: $cursor) {
              cursor
              items {
                id
                name
                created_at
                updated_at
                group {
                  title
                }
                column_values {
                  id
                  text
                  type
                  value
                  column {
                    title
                  }
                }
              }
            }
          }
        }
        """
        cursor = None
        rows: list[dict[str, Any]] = []

        while True:
            data = self._post(query, {"boardId": str(board_id), "limit": page_size, "cursor": cursor})
            boards = data.get("boards", [])
            if not boards:
                break

            board = boards[0]
            items_page = board.get("items_page") or {}
            items = items_page.get("items", [])
            for item in items:
                row: dict[str, Any] = {
                    "item_id": item.get("id"),
                    "item_name": item.get("name"),
                    "item_created_at": item.get("created_at"),
                    "item_updated_at": item.get("updated_at"),
                    "group_title": (item.get("group") or {}).get("title"),
                    "board_id": board.get("id"),
                    "board_name": board.get("name"),
                    "loaded_at_utc": datetime.utcnow().isoformat(),
                }
                for col in item.get("column_values", []):
                    title = (col.get("column") or {}).get("title") or col.get("id")
                    row[title] = col.get("text")
                    row[f"__raw__{title}"] = col.get("value")
                rows.append(row)

            cursor = items_page.get("cursor")
            if not cursor:
                break

        return rows
