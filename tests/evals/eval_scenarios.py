"""
AEGIS Eval Harness — 15 dispute scenarios
Run with: python tests/evals/eval_scenarios.py
"""

import json
import sys
import time

import httpx

API_URL = "http://localhost:8000/dispute"

SCENARIOS = [
    {
        "chargeback_id": "EVAL-001",
        "merchant_id": "M1",
        "transaction_id": "T001",
        "amount": 250.0,
        "reason_code": "13.1",
        "reason_description": "Item not received",
        "expected_verdict": "FIGHT",
    },
    {
        "chargeback_id": "EVAL-002",
        "merchant_id": "M1",
        "transaction_id": "T002",
        "amount": 450.0,
        "reason_code": "13.1",
        "reason_description": "Item not received",
        "expected_verdict": "FIGHT",
    },
    {
        "chargeback_id": "EVAL-003",
        "merchant_id": "M1",
        "transaction_id": "T003",
        "amount": 99.0,
        "reason_code": "13.3",
        "reason_description": "Item not as described",
        "expected_verdict": None,
    },
    {
        "chargeback_id": "EVAL-004",
        "merchant_id": "M1",
        "transaction_id": "T004",
        "amount": 175.0,
        "reason_code": "10.4",
        "reason_description": "Fraudulent transaction",
        "expected_verdict": "FIGHT",
    },
    {
        "chargeback_id": "EVAL-005",
        "merchant_id": "M1",
        "transaction_id": "T005",
        "amount": 320.0,
        "reason_code": "13.1",
        "reason_description": "Package not delivered",
        "expected_verdict": "FIGHT",
    },
    {
        "chargeback_id": "EVAL-006",
        "merchant_id": "M1",
        "transaction_id": "T006",
        "amount": 540.0,
        "reason_code": "10.4",
        "reason_description": "Fraud claim",
        "expected_verdict": "FIGHT",
    },
    {
        "chargeback_id": "EVAL-007",
        "merchant_id": "M1",
        "transaction_id": "T007",
        "amount": 89.0,
        "reason_code": "12.6",
        "reason_description": "Duplicate processing",
        "expected_verdict": "FIGHT",
    },
    {
        "chargeback_id": "EVAL-008",
        "merchant_id": "M1",
        "transaction_id": "T008",
        "amount": 1200.0,
        "reason_code": "13.7",
        "reason_description": "Cancelled merchandise",
        "expected_verdict": None,
    },
    {
        "chargeback_id": "EVAL-009",
        "merchant_id": "M1",
        "transaction_id": "T009",
        "amount": 850.0,
        "reason_code": "13.2",
        "reason_description": "Cancelled recurring transaction",
        "expected_verdict": None,
    },
    {
        "chargeback_id": "EVAL-010",
        "merchant_id": "M1",
        "transaction_id": "T010",
        "amount": 2200.0,
        "reason_code": "13.6",
        "reason_description": "Credit not processed",
        "expected_verdict": None,
    },
    {
        "chargeback_id": "EVAL-011",
        "merchant_id": "M1",
        "transaction_id": "T011",
        "amount": 5000.0,
        "reason_code": "10.5",
        "reason_description": "Visa fraud monitoring",
        "expected_verdict": "ESCALATE",
    },
    {
        "chargeback_id": "EVAL-012",
        "merchant_id": "M1",
        "transaction_id": "T012",
        "amount": 7500.0,
        "reason_code": "10.4",
        "reason_description": "High value fraud claim",
        "expected_verdict": None,
    },
    {
        "chargeback_id": "EVAL-013",
        "merchant_id": "M1",
        "transaction_id": "T013",
        "amount": 130.0,
        "reason_code": "13.3",
        "reason_description": "Wrong item shipped",
        "expected_verdict": None,
    },
    {
        "chargeback_id": "EVAL-014",
        "merchant_id": "M1",
        "transaction_id": "T014",
        "amount": 420.0,
        "reason_code": "13.1",
        "reason_description": "Delayed delivery claim",
        "expected_verdict": "FIGHT",
    },
    {
        "chargeback_id": "EVAL-015",
        "merchant_id": "M1",
        "transaction_id": "T015",
        "amount": 670.0,
        "reason_code": "10.4",
        "reason_description": "Customer claims no authorization",
        "expected_verdict": "FIGHT",
    },
]

VALID_VERDICTS = {"FIGHT", "ACCEPT", "ESCALATE"}


def run_evals():
    passed = 0
    failed = 0
    errors = 0
    results = []

    print(f"\n{'=' * 60}")
    print("AEGIS EVAL HARNESS — 15 Scenarios")
    print(f"{'=' * 60}\n")

    for s in SCENARIOS:
        payload = {k: v for k, v in s.items() if k != "expected_verdict"}
        expected = s["expected_verdict"]

        try:
            resp = httpx.post(API_URL, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            time.sleep(2)

            verdict = data.get("verdict", "").upper()
            winability = data.get("winability_score", 0)
            review = data.get("review_passed", False)

            if verdict not in VALID_VERDICTS:
                status = "ERROR"
                errors += 1
            elif expected is None:
                status = "PASS"
                passed += 1
            elif verdict == expected:
                status = "PASS"
                passed += 1
            else:
                status = "FAIL"
                failed += 1

            results.append(
                {
                    "id": s["chargeback_id"],
                    "status": status,
                    "expected": expected or "ANY",
                    "got": verdict,
                    "winability": winability,
                    "review_passed": review,
                }
            )

            icon = "✅" if status == "PASS" else ("⚠️" if status == "ERROR" else "❌")
            print(
                f"{icon}  {s['chargeback_id']} | expected={expected or 'ANY':<8} got={verdict:<8} win={winability:.2f} review={review}"
            )

        except Exception as e:
            errors += 1
            results.append({"id": s["chargeback_id"], "status": "ERROR", "error": str(e)})
            print(f"💥  {s['chargeback_id']} | ERROR: {e}")

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {passed} passed | {failed} failed | {errors} errors | {len(SCENARIOS)} total")
    print(f"{'=' * 60}\n")

    with open("tests/evals/eval_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to tests/evals/eval_results.json")

    if failed > 0 or errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_evals()
