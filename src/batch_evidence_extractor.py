import json
import os
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "03_Extracted_Text"
    / "TJX_selected_relevant_pages_refined.json"
)

OUTPUT_FOLDER = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "batch_pages"
)

LOG_FILE = (
    PROJECT_ROOT
    / "logs"
    / "batch_evidence_extraction_log.jsonl"
)

BATCH_SUMMARY_FILE = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "batch_summary.json"
)

MODEL_NAME = "claude-sonnet-4-6"

MAX_PAGES_PER_RUN = 5
MAX_EVIDENCE_ITEMS_PER_PAGE = 5
MAX_TOKENS = 1800


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_selected_pages() -> list[dict[str, Any]]:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Selected-page file not found:\n{INPUT_FILE}"
        )

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        pages = json.load(file)

    if not isinstance(pages, list):
        raise ValueError(
            "The selected-page file must contain a list."
        )

    if not pages:
        raise ValueError(
            "The selected-page file contains no pages."
        )

    return pages


def output_path_for_page(
    page: dict[str, Any],
) -> Path:
    page_number = page["pdf_page_number"]

    return (
        OUTPUT_FOLDER
        / f"page_{page_number:03d}_evidence.json"
    )


def page_already_processed(
    page: dict[str, Any],
) -> bool:
    return output_path_for_page(page).exists()


def select_batch_pages(
    pages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    unprocessed_pages = [
        page
        for page in pages
        if not page_already_processed(page)
    ]

    return unprocessed_pages[:MAX_PAGES_PER_RUN]


def build_prompt(
    page: dict[str, Any],
) -> str:
    source_document = page["source_document"]
    page_number = page["pdf_page_number"]
    primary_topic = page.get("primary_topic")
    secondary_topics = page.get("secondary_topics", [])
    source_text = page["text"]

    return f"""
You are extracting traceable ESG disclosure evidence from one page of a TJX report.

SOURCE DOCUMENT:
{source_document}

PDF PAGE:
{page_number}

PAGE-SELECTION CONTEXT:
Primary topic: {primary_topic}
Secondary topics: {secondary_topics}

The topic labels above are planning signals only. Do not assume they are correct.
Classify each evidence item from the actual source text.

SOURCE TEXT:
---BEGIN SOURCE TEXT---
{source_text}
---END SOURCE TEXT---

Return one valid JSON object with this exact structure:

{{
  "source_document": "{source_document}",
  "pdf_page_number": {page_number},
  "page_primary_topic": "{primary_topic}",
  "evidence_items": [
    {{
      "evidence_id": "P{page_number:03d}-EV-001",
      "topic": "specific ESG topic",
      "claim": "faithful summary of what the source explicitly states",
      "exact_quote": "shortest verbatim passage supporting the claim",
      "metric_name": null,
      "metric_value": null,
      "metric_unit": null,
      "reporting_period": null,
      "geographic_scope": null,
      "evidence_type": "policy, target, metric, action, governance, risk, or other",
      "confidence": "high"
    }}
  ]
}}

Rules:

1. Use only the source text provided above.
2. Do not use outside knowledge.
3. Do not infer missing information.
4. Copy exact_quote directly from the source text.
5. Preserve wording, capitalization, punctuation, and sentence order.
6. You may replace PDF line breaks with spaces.
7. Use the shortest quotation that fully supports the claim.
8. Do not paraphrase inside exact_quote.
9. Use null when information is unavailable.
10. Do not invent metrics, dates, scopes, targets, outcomes, or entities.
11. A goal is not a completed result.
12. An activity is not automatically an outcome.
13. A policy statement is not automatically proof of implementation.
14. Return no more than {MAX_EVIDENCE_ITEMS_PER_PAGE} evidence items.
15. Return valid JSON only.
16. Do not use markdown fences.
17. Do not include commentary before or after the JSON.
""".strip()


def clean_json_response(
    response_text: str,
) -> str:
    cleaned = response_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]

    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


def normalize_text(
    value: str,
) -> str:
    if not isinstance(value, str):
        return ""

    value = unicodedata.normalize(
        "NFKC",
        value,
    )

    value = re.sub(
        r"-\s*\n\s*",
        "-",
        value,
    )

    value = (
        value
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u00a0", " ")
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def validate_result_structure(
    result: dict[str, Any],
    page: dict[str, Any],
) -> None:
    if not isinstance(result, dict):
        raise ValueError(
            "Claude response must be a JSON object."
        )

    expected_document = page["source_document"]
    expected_page = page["pdf_page_number"]

    if result.get("source_document") != expected_document:
        raise ValueError(
            "Source-document validation failed."
        )

    if result.get("pdf_page_number") != expected_page:
        raise ValueError(
            "PDF-page validation failed."
        )

    evidence_items = result.get("evidence_items")

    if not isinstance(evidence_items, list):
        raise ValueError(
            "evidence_items must be a list."
        )

    if len(evidence_items) > MAX_EVIDENCE_ITEMS_PER_PAGE:
        raise ValueError(
            "Too many evidence items were returned."
        )

    required_fields = {
        "evidence_id",
        "topic",
        "claim",
        "exact_quote",
        "metric_name",
        "metric_value",
        "metric_unit",
        "reporting_period",
        "geographic_scope",
        "evidence_type",
        "confidence",
    }

    valid_types = {
        "policy",
        "target",
        "metric",
        "action",
        "governance",
        "risk",
        "other",
    }

    valid_confidence = {
        "high",
        "medium",
        "low",
    }

    for index, item in enumerate(
        evidence_items,
        start=1,
    ):
        if not isinstance(item, dict):
            raise ValueError(
                f"Evidence item {index} is not an object."
            )

        missing_fields = (
            required_fields
            - set(item.keys())
        )

        if missing_fields:
            raise ValueError(
                f"Evidence item {index} is missing: "
                f"{sorted(missing_fields)}"
            )

        if not item.get("claim"):
            raise ValueError(
                f"Evidence item {index} has no claim."
            )

        if not item.get("exact_quote"):
            raise ValueError(
                f"Evidence item {index} has no quote."
            )

        if item.get("evidence_type") not in valid_types:
            raise ValueError(
                f"Invalid evidence type in item {index}."
            )

        if item.get("confidence") not in valid_confidence:
            raise ValueError(
                f"Invalid confidence in item {index}."
            )


def validate_quotes(
    result: dict[str, Any],
    source_text: str,
) -> None:
    normalized_source = normalize_text(
        source_text
    )

    for item in result.get(
        "evidence_items",
        [],
    ):
        evidence_id = item.get(
            "evidence_id",
            "UNKNOWN",
        )

        normalized_quote = normalize_text(
            item.get("exact_quote", "")
        )

        if not normalized_quote:
            raise ValueError(
                f"Empty quotation for {evidence_id}."
            )

        if normalized_quote not in normalized_source:
            raise ValueError(
                f"Quote validation failed for {evidence_id}."
            )


def add_control_metadata(
    result: dict[str, Any],
    page: dict[str, Any],
    usage: Any,
) -> dict[str, Any]:
    for item in result.get(
        "evidence_items",
        [],
    ):
        item["quote_validation_status"] = "passed"
        item["human_review_status"] = "pending"

    result["selection_primary_topic"] = page.get(
        "primary_topic"
    )

    result["selection_secondary_topics"] = page.get(
        "secondary_topics",
        [],
    )

    result["selection_relevance_score"] = page.get(
        "relevance_score"
    )

    result["model_name"] = MODEL_NAME
    result["extracted_at_utc"] = utc_timestamp()
    result["extraction_status"] = "validated_by_python"
    result["human_review_required"] = True

    result["api_usage"] = {
        "input_tokens": getattr(
            usage,
            "input_tokens",
            None,
        ),
        "output_tokens": getattr(
            usage,
            "output_tokens",
            None,
        ),
    }

    return result


@retry(
    retry=retry_if_exception_type(
        (
            TimeoutError,
            ConnectionError,
        )
    ),
    wait=wait_exponential(
        multiplier=2,
        min=2,
        max=30,
    ),
    stop=stop_after_attempt(3),
    reraise=True,
)
def call_claude(
    client: Anthropic,
    page: dict[str, Any],
):
    return client.messages.create(
        model=MODEL_NAME,
        max_tokens=MAX_TOKENS,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": build_prompt(page),
            }
        ],
    )


def save_page_result(
    page: dict[str, Any],
    result: dict[str, Any],
) -> Path:
    OUTPUT_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = output_path_for_page(
        page
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return output_path


def write_log(
    record: dict[str, Any],
) -> None:
    LOG_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with LOG_FILE.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
            + "\n"
        )


def process_page(
    client: Anthropic,
    page: dict[str, Any],
) -> dict[str, Any]:
    page_number = page["pdf_page_number"]

    started_at = time.perf_counter()

    try:
        response = call_claude(
            client=client,
            page=page,
        )

        if not response.content:
            raise RuntimeError(
                "Claude returned no response content."
            )

        response_text = response.content[0].text

        cleaned_text = clean_json_response(
            response_text
        )

        result = json.loads(
            cleaned_text
        )

        validate_result_structure(
            result=result,
            page=page,
        )

        validate_quotes(
            result=result,
            source_text=page["text"],
        )

        result = add_control_metadata(
            result=result,
            page=page,
            usage=response.usage,
        )

        output_path = save_page_result(
            page=page,
            result=result,
        )

        elapsed_seconds = (
            time.perf_counter()
            - started_at
        )

        log_record = {
            "timestamp_utc": utc_timestamp(),
            "pdf_page_number": page_number,
            "status": "success",
            "output_file": str(output_path),
            "evidence_count": len(
                result.get(
                    "evidence_items",
                    [],
                )
            ),
            "input_tokens": getattr(
                response.usage,
                "input_tokens",
                None,
            ),
            "output_tokens": getattr(
                response.usage,
                "output_tokens",
                None,
            ),
            "elapsed_seconds": round(
                elapsed_seconds,
                2,
            ),
        }

        write_log(log_record)

        return log_record

    except Exception as error:
        elapsed_seconds = (
            time.perf_counter()
            - started_at
        )

        log_record = {
            "timestamp_utc": utc_timestamp(),
            "pdf_page_number": page_number,
            "status": "failed",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "elapsed_seconds": round(
                elapsed_seconds,
                2,
            ),
        }

        write_log(log_record)

        return log_record


def save_batch_summary(
    results: list[dict[str, Any]],
) -> None:
    successful = [
        result
        for result in results
        if result["status"] == "success"
    ]

    failed = [
        result
        for result in results
        if result["status"] == "failed"
    ]

    summary = {
        "run_timestamp_utc": utc_timestamp(),
        "model_name": MODEL_NAME,
        "pages_attempted": len(results),
        "pages_succeeded": len(successful),
        "pages_failed": len(failed),
        "total_evidence_items": sum(
            result.get("evidence_count", 0)
            for result in successful
        ),
        "total_input_tokens": sum(
            result.get("input_tokens") or 0
            for result in successful
        ),
        "total_output_tokens": sum(
            result.get("output_tokens") or 0
            for result in successful
        ),
        "results": results,
    }

    BATCH_SUMMARY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with BATCH_SUMMARY_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            summary,
            file,
            ensure_ascii=False,
            indent=2,
        )


def print_summary(
    results: list[dict[str, Any]],
) -> None:
    print("=" * 72)
    print("TJX CONTROLLED FIVE-PAGE EVIDENCE BATCH")
    print("=" * 72)

    for result in results:
        page_number = result["pdf_page_number"]
        status = result["status"]

        if status == "success":
            print(
                f"Page {page_number}: SUCCESS | "
                f"evidence={result['evidence_count']} | "
                f"input_tokens={result['input_tokens']} | "
                f"output_tokens={result['output_tokens']}"
            )
        else:
            print(
                f"Page {page_number}: FAILED | "
                f"{result['error_type']}: "
                f"{result['error_message']}"
            )

    successful_count = sum(
        result["status"] == "success"
        for result in results
    )

    failed_count = sum(
        result["status"] == "failed"
        for result in results
    )

    print("-" * 72)

    print(
        f"Pages attempted: {len(results)}"
    )

    print(
        f"Pages succeeded: {successful_count}"
    )

    print(
        f"Pages failed: {failed_count}"
    )

    print(
        f"Batch summary saved to:\n{BATCH_SUMMARY_FILE}"
    )

    print("=" * 72)


def main() -> None:
    load_dotenv()

    api_key = os.getenv(
        "ANTHROPIC_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "Missing ANTHROPIC_API_KEY."
        )

    selected_pages = load_selected_pages()

    batch_pages = select_batch_pages(
        selected_pages
    )

    if not batch_pages:
        print(
            "No unprocessed pages remain for this batch."
        )
        return

    print(
        f"Selected {len(batch_pages)} "
        f"unprocessed page(s) for this run."
    )

    print(
        "Pages: "
        + ", ".join(
            str(page["pdf_page_number"])
            for page in batch_pages
        )
    )

    client = Anthropic(
        api_key=api_key
    )

    results: list[dict[str, Any]] = []

    for page in batch_pages:
        page_number = page["pdf_page_number"]

        print(
            f"\nProcessing PDF page {page_number}..."
        )

        result = process_page(
            client=client,
            page=page,
        )

        results.append(result)

    save_batch_summary(
        results
    )

    print_summary(
        results
    )


if __name__ == "__main__":
    main()