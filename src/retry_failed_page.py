import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SELECTED_PAGES_FILE = (
    PROJECT_ROOT
    / "03_Extracted_Text"
    / "TJX_selected_relevant_pages_refined.json"
)

OUTPUT_FOLDER = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "batch_pages"
)

DEBUG_FOLDER = (
    PROJECT_ROOT
    / "logs"
    / "failed_responses"
)

PAGE_NUMBER_TO_RETRY = 35
MODEL_NAME = "claude-sonnet-4-6"
MAX_TOKENS = 1800


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_target_page() -> dict[str, Any]:
    if not SELECTED_PAGES_FILE.exists():
        raise FileNotFoundError(
            f"Selected-pages file not found:\n{SELECTED_PAGES_FILE}"
        )

    with SELECTED_PAGES_FILE.open("r", encoding="utf-8") as file:
        pages = json.load(file)

    for page in pages:
        if page.get("pdf_page_number") == PAGE_NUMBER_TO_RETRY:
            return page

    raise ValueError(
        f"PDF page {PAGE_NUMBER_TO_RETRY} was not found "
        f"in the selected-pages file."
    )


def build_prompt(page: dict[str, Any]) -> str:
    page_number = page["pdf_page_number"]
    source_document = page["source_document"]
    source_text = page["text"]

    return f"""
You are extracting auditable ESG evidence from one page of a TJX report.

SOURCE DOCUMENT:
{source_document}

PDF PAGE:
{page_number}

SOURCE TEXT:
---BEGIN SOURCE TEXT---
{source_text}
---END SOURCE TEXT---

Return one valid JSON object with this exact structure:

{{
  "source_document": "{source_document}",
  "pdf_page_number": {page_number},
  "page_primary_topic": "{page.get('primary_topic')}",
  "evidence_items": [
    {{
      "evidence_id": "P{page_number:03d}-EV-001",
      "topic": "specific ESG topic",
      "claim": "faithful summary of what the source explicitly states",
      "exact_quote": "one short verbatim sentence or phrase from the source",
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

Strict rules:

1. Use only the source text above.
2. Return no more than five evidence items.
3. Every exact_quote must be copied directly from the source text.
4. Use only one sentence or one short phrase for each exact_quote.
5. Do not combine text from separate paragraphs, bullets, or table cells.
6. Do not use ellipses.
7. Do not add or remove words inside exact_quote.
8. You may replace line breaks with spaces.
9. Do not paraphrase inside exact_quote.
10. Use null when information is unavailable.
11. Do not invent metrics, dates, targets, outcomes, entities, or geographic scopes.
12. A target is not an achieved result.
13. An activity is not automatically an outcome.
14. Return valid JSON only.
15. Do not use markdown code fences.
16. Do not include commentary before or after the JSON.
""".strip()


def clean_json_response(response_text: str) -> str:
    cleaned = response_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


def normalize_text(value: str) -> str:
    if not isinstance(value, str):
        return ""

    value = unicodedata.normalize("NFKC", value)

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


def validate_structure(
    result: dict[str, Any],
    page: dict[str, Any],
) -> None:
    if not isinstance(result, dict):
        raise ValueError("Claude response must be a JSON object.")

    if result.get("source_document") != page["source_document"]:
        raise ValueError("Source-document validation failed.")

    if result.get("pdf_page_number") != page["pdf_page_number"]:
        raise ValueError("PDF-page validation failed.")

    evidence_items = result.get("evidence_items")

    if not isinstance(evidence_items, list):
        raise ValueError("evidence_items must be a list.")

    if len(evidence_items) > 5:
        raise ValueError("Claude returned more than five evidence items.")

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

    allowed_types = {
        "policy",
        "target",
        "metric",
        "action",
        "governance",
        "risk",
        "other",
    }

    for index, item in enumerate(evidence_items, start=1):
        if not isinstance(item, dict):
            raise ValueError(
                f"Evidence item {index} must be a JSON object."
            )

        missing_fields = required_fields - set(item.keys())

        if missing_fields:
            raise ValueError(
                f"Evidence item {index} is missing fields: "
                f"{sorted(missing_fields)}"
            )

        if item.get("evidence_type") not in allowed_types:
            raise ValueError(
                f"Evidence item {index} has an invalid evidence type."
            )


def validate_quotes(
    result: dict[str, Any],
    source_text: str,
) -> None:
    normalized_source = normalize_text(source_text)

    validation_errors: list[str] = []

    for item in result.get("evidence_items", []):
        evidence_id = item.get("evidence_id", "UNKNOWN")
        quote = item.get("exact_quote", "")
        normalized_quote = normalize_text(quote)

        if not normalized_quote:
            validation_errors.append(
                f"{evidence_id}: quotation is empty."
            )
            continue

        if normalized_quote not in normalized_source:
            validation_errors.append(
                f"{evidence_id}: quote not found.\n"
                f"Quote: {quote}"
            )

    if validation_errors:
        raise ValueError(
            "\n\n".join(validation_errors)
        )


def add_control_metadata(
    result: dict[str, Any],
    response: Any,
) -> dict[str, Any]:
    for item in result.get("evidence_items", []):
        item["quote_validation_status"] = "passed"
        item["human_review_status"] = "pending"

    result["model_name"] = MODEL_NAME
    result["retry_run"] = True
    result["extracted_at_utc"] = utc_timestamp()
    result["extraction_status"] = "validated_by_python"
    result["human_review_required"] = True

    result["api_usage"] = {
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
    }

    return result


def save_raw_response(
    response_text: str,
) -> Path:
    DEBUG_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    debug_path = (
        DEBUG_FOLDER
        / f"page_{PAGE_NUMBER_TO_RETRY:03d}_raw_response.txt"
    )

    with debug_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        file.write(response_text)

    return debug_path


def save_validated_result(
    result: dict[str, Any],
) -> Path:
    OUTPUT_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        OUTPUT_FOLDER
        / f"page_{PAGE_NUMBER_TO_RETRY:03d}_evidence.json"
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


def main() -> None:
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise RuntimeError(
            "Missing ANTHROPIC_API_KEY in the .env file."
        )

    page = load_target_page()

    print(
        f"Retrying PDF page "
        f"{page['pdf_page_number']}..."
    )

    client = Anthropic(
        api_key=api_key
    )

    response = client.messages.create(
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

    if not response.content:
        raise RuntimeError(
            "Claude returned no response content."
        )

    response_text = response.content[0].text

    debug_path = save_raw_response(
        response_text
    )

    cleaned_text = clean_json_response(
        response_text
    )

    try:
        result = json.loads(cleaned_text)
    except json.JSONDecodeError as error:
        print(
            f"Raw response saved to:\n{debug_path}"
        )

        raise RuntimeError(
            "Claude returned invalid JSON."
        ) from error

    validate_structure(
        result=result,
        page=page,
    )

    try:
        validate_quotes(
            result=result,
            source_text=page["text"],
        )
    except ValueError:
        print(
            f"Raw response saved to:\n{debug_path}"
        )
        raise

    result = add_control_metadata(
        result=result,
        response=response,
    )

    output_path = save_validated_result(
        result
    )

    print(
        f"Evidence items extracted: "
        f"{len(result.get('evidence_items', []))}"
    )

    print(
        "Structure validation passed."
    )

    print(
        "Exact-quote validation passed."
    )

    print(
        f"Validated evidence saved to:\n{output_path}"
    )

    print(
        f"Raw Claude response saved to:\n{debug_path}"
    )


if __name__ == "__main__":
    main()