from __future__ import annotations

import json
import random
import time
from typing import Any

import requests

from logsentry_agent.signer import compute_body_hash, sign_request


def build_headers(*, agent_id: str, secret: str, body: bytes, nonce: str, timestamp: str) -> dict:
    body_hash = compute_body_hash(body)
    signature = sign_request(secret, agent_id, timestamp, nonce, body_hash)
    return {
        "X-Agent-Id": agent_id,
        "X-Agent-Timestamp": timestamp,
        "X-Agent-Nonce": nonce,
        "X-Agent-Signature": signature,
        "X-Agent-Content-SHA256": body_hash,
        "Content-Type": "application/json",
    }


def send_payload(
    *,
    endpoint: str,
    agent_id: str,
    secret: str,
    payload: dict[str, Any],
    retry_max_seconds: int,
) -> requests.Response:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    attempt = 0
    while True:
        timestamp = str(int(time.time()))
        nonce = f"{random.getrandbits(96):024x}"
        headers = build_headers(
            agent_id=agent_id,
            secret=secret,
            body=body,
            nonce=nonce,
            timestamp=timestamp,
        )
        response = requests.post(endpoint, data=body, headers=headers, timeout=10)
        if response.status_code < 500:
            return response
        sleep_for = min((2**attempt) + random.random(), retry_max_seconds)
        time.sleep(sleep_for)
        attempt += 1
