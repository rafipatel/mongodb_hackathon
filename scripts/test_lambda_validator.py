#!/usr/bin/env python3
"""Dry-run AWS Lambda skill validator (same payload shape as forge/validator.py).

Exit codes:
  0 — Lambda responded with JSON (check printed score / errors)
  0 — AWS not configured (skipped, nothing to test)
  1 — boto3 invoke failed or Lambda returned an error payload
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

# Import after load_dotenv so config sees env
sys.path.insert(0, str(_ROOT))

from config import AWS_LAMBDA_FUNCTION, AWS_REGION  # noqa: E402


def _aws_configured() -> bool:
    return bool(os.environ.get("AWS_ACCESS_KEY_ID")) and bool(
        os.environ.get("AWS_SECRET_ACCESS_KEY")
    )


def _minimal_skill_code() -> str:
    """Tiny stub that satisfies local AST checks; Lambda may score it differently."""
    return """
async def coordinate(context):
    return {"steps_initiated": [], "escalation_after_minutes": 20}
"""


def main() -> int:
    if not _aws_configured():
        print(
            "SKIP: AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY not set — "
            "cannot invoke Lambda (forge will use local AST fallback)."
        )
        return 0

    import boto3

    cases_path = _ROOT / "tests" / "synthetic_cases" / "transfer_cases.json"
    test_cases: list = []
    if cases_path.exists():
        test_cases = json.loads(cases_path.read_text())

    payload = {"code": _minimal_skill_code(), "test_cases": test_cases}

    print(f"Region:      {AWS_REGION}")
    print(f"Function:    {AWS_LAMBDA_FUNCTION}")
    print(f"Test cases:  {len(test_cases)} loaded")

    client = boto3.client("lambda", region_name=AWS_REGION)
    try:
        response = client.invoke(
            FunctionName=AWS_LAMBDA_FUNCTION,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload).encode(),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: invoke error: {exc}")
        return 1

    raw = response["Payload"].read().decode()
    status = response.get("StatusCode")
    fn_err = response.get("FunctionError")

    print(f"HTTP status: {status}")
    if fn_err:
        print(f"FunctionError: {fn_err}")

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        print(f"FAIL: non-JSON payload (first 500 chars): {raw[:500]!r}")
        return 1

    print(f"Response: {json.dumps(result, indent=2)[:4000]}")

    if fn_err or result.get("errorMessage"):
        print("FAIL: Lambda reported an execution error.")
        return 1

    # Same parsing as forge/validator._lambda_score_from_result
    score = result.get("score")
    if score is None and isinstance(result.get("body"), str):
        try:
            inner = json.loads(result["body"])
            if isinstance(inner, dict):
                score = inner.get("score")
        except json.JSONDecodeError:
            pass

    if score is not None:
        print(f"OK: Lambda returned score={score}")
        return 0

    print(
        "WARN: No numeric score in payload. Forge will use local AST fallback until "
        "the handler returns {\"score\": <float>} (or API Gateway body with that JSON)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
