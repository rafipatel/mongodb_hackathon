"""Skill validator.

Real path: invoke an AWS Lambda that runs the forged code against synthetic cases.
Local fallback: if AWS env not configured, do a syntax-and-shape check in-process so
the demo still runs without the Lambda deployed.
"""

import ast
import json
import os
from pathlib import Path

import boto3

from agent.state import MediMindState
from config import AWS_LAMBDA_FUNCTION, AWS_REGION, FORGE_PASS_SCORE

SYNTHETIC_CASES_PATH = (
    Path(__file__).resolve().parent.parent / "tests" / "synthetic_cases" / "transfer_cases.json"
)


def _load_synthetic_cases() -> list[dict]:
    if not SYNTHETIC_CASES_PATH.exists():
        return []
    with SYNTHETIC_CASES_PATH.open() as f:
        return json.load(f)


def _local_validate(code: str | None) -> float:
    """Cheap local fallback. Score in [0, 1]."""
    if not code:
        return 0.0
    score = 0.0
    try:
        tree = ast.parse(code)
        score += 0.4
    except SyntaxError:
        return 0.0

    has_coordinate = any(
        isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef))
        and node.name == "coordinate"
        for node in ast.walk(tree)
    )
    if has_coordinate:
        score += 0.3
    if "steps_initiated" in code and "escalation_after_minutes" in code:
        score += 0.2
    if "return" in code:
        score += 0.1
    return min(score, 1.0)


def _aws_configured() -> bool:
    return bool(os.environ.get("AWS_ACCESS_KEY_ID")) and bool(
        os.environ.get("AWS_SECRET_ACCESS_KEY")
    )


def _lambda_score_from_result(result: dict) -> float | None:
    """Accept direct invoke ``{\"score\": ...}`` or API-Gateway-style ``{\"body\": \"...\"}``."""
    if "score" in result:
        return float(result["score"])
    body = result.get("body")
    if isinstance(body, str):
        try:
            inner = json.loads(body)
        except json.JSONDecodeError:
            return None
        if isinstance(inner, dict) and "score" in inner:
            return float(inner["score"])
    return None


def _try_lambda_validate(code: str) -> float | None:
    """Try the AWS Lambda validator. Return None if it can't run so caller falls back."""
    if not _aws_configured():
        return None
    try:
        payload = {"code": code, "test_cases": _load_synthetic_cases()}
        lambda_client = boto3.client("lambda", region_name=AWS_REGION)
        response = lambda_client.invoke(
            FunctionName=AWS_LAMBDA_FUNCTION,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload).encode(),
        )
        result = json.loads(response["Payload"].read())
        score = _lambda_score_from_result(result)
        if score is None:
            print(
                "[validator] Lambda response had no score "
                "(handler should return JSON {\"score\": <float>}); using local fallback."
            )
            return None
        return score
    except Exception as exc:  # noqa: BLE001
        print(f"[validator] Lambda invoke failed, falling back to local: {exc}")
        return None


async def validate_skill(state: MediMindState) -> MediMindState:
    code = state.get("forged_code")
    if not code:
        return {**state, "forge_validation_score": 0.0}

    score = _try_lambda_validate(code)
    if score is None:
        score = _local_validate(code)

    return {
        **state,
        "forge_validation_score": score,
        "forged_code": code if score >= FORGE_PASS_SCORE else None,
    }
