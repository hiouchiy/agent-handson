"""Managed Agent Memory（長期記憶, Unity Catalog の MEMORY_STORE）の読み書き。

Memory のエントリは scope（誰／何についての記憶か）と path（名前）で管理する。このエージェントでは:
  - scope = "shared"           : 全社で共通の採点ルール
  - scope = "rubric_<観点>"    : その観点だけを補足する採点ルール
  - scope = "<会社ID>"         : 会社ごとの申し送りと、過去の採点の履歴（エージェントが書き込む）
1 つの scope の記憶は数件なので、検索ではなく一覧で全部読む。

認証:
  - ノートブック / ジョブ: 実行しているユーザーの資格情報。
  - Model Serving: 呼び出したユーザー本人の資格情報（OBO: On-Behalf-Of）。エンドポイント自身の資格情報では
    Memory を読み書きできないため。エンドポイントは UserAuthPolicy の `unity-catalog` スコープ付きでデプロイする。
    OBO のトークンはリクエストごとに取得し、そのリクエスト専用のクライアントに固定する
    （並行するリクエストで別のユーザーのトークンを使わないようにするため）。
"""
from __future__ import annotations

import os

from databricks.sdk import WorkspaceClient
from databricks.sdk.credentials_provider import CredentialsStrategy

_API = "/api/2.1/unity-catalog/memory-stores"


class MemoryAuthError(RuntimeError):
    """呼び出しユーザーの資格情報（OBO）を取得できないことを表す。"""


def is_model_serving() -> bool:
    return os.environ.get("IS_IN_DB_MODEL_SERVING_ENV", "false") == "true"


def _fetch_obo_token() -> str:
    try:
        from mlflowserving.scoring_server.agent_utils import fetch_obo_token
    except ImportError as exc:
        raise MemoryAuthError("OBO のトークンを取得する関数が見つかりません") from exc
    token = fetch_obo_token()
    if not token:
        raise MemoryAuthError("OBO のトークンが空です")
    return token


class _RequestUserCredentials(CredentialsStrategy):
    """取得済みのトークンを、このリクエスト専用の資格情報として固定する。"""

    def __init__(self, token: str):
        self._headers = {"Authorization": f"Bearer {token}"}

    def auth_type(self) -> str:
        return "model_serving_request_user"

    def __call__(self, cfg):
        if cfg.host is None:
            cfg.host = os.environ.get("DATABRICKS_MODEL_SERVING_HOST_URL") or os.environ.get(
                "DB_MODEL_SERVING_HOST_URL")
        headers = dict(self._headers)
        return lambda: dict(headers)


def client_for_request() -> WorkspaceClient:
    """現在のリクエスト用のクライアント（Model Serving では呼び出しユーザー本人の資格情報）。predict の中で呼ぶ。"""
    if is_model_serving():
        return WorkspaceClient(credentials_strategy=_RequestUserCredentials(_fetch_obo_token()))
    return WorkspaceClient()


def read(ws: WorkspaceClient, store: str, scope: str) -> str:
    """scope の記憶を全部読み、本文をつなげて返す（なければ空文字）。"""
    entries = ws.api_client.do("GET", f"{_API}/{store}/entries", query={"scope": scope}).get("entries", [])
    texts = []
    for e in entries:
        got = ws.api_client.do("GET", f"{_API}/{store}/entries:get", query={"scope": scope, "path": e["path"]})
        if got.get("contents"):
            texts.append(got["contents"])
    return "\n\n".join(texts)


def write(ws: WorkspaceClient, store: str, scope: str, path: str, contents: str, description: str = "") -> None:
    """scope に記憶を 1 件書き込む。"""
    ws.api_client.do("POST", f"{_API}/{store}/entries", query={"scope": scope},
                     body={"path": path, "contents": contents, "description": description})
