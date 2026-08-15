import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "03_Extracted_Text"
    / "TJX_2025_Global_Corporate_Responsibility_Report.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "test_evidence.json"
)


# ---------------------------------------------------------
# Load extracted PDF pages
# ---------------------------------------------------------

def load_pages() -> list[dict[str, Any]]:
    """
    Load the page-level JSON created by pdf_extractor.py.
    """

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        pages = json.load(file)

    if not isinstance(pages, list):
        raise ValueError(
            "The extracted-text JSON must contain a list of page records."
        )

    if not pages:
        raise ValueError(
            "The extracted-text JSON contains no pages."
        )

    return pages


# ---------------------------------------------------------
# Select one controlled test page
# ---------------------------------------------------------

def select_test_page(
    pages: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Select one substantive page for the first Claude extraction test.

    The longest eligible page is selected, excluding pages that were
    previously marked as requiring review.
    """

    eligible_pages = [
        page
        for page in pages
        if not page.get("requires_review", False)
        and page.get("text", "").strip()
    ]

    if not eligible_pages:
        raise RuntimeError(
            "No eligible pages were found for extraction."
        )

    selected_page = max(
        eligible_pages,
        key=lambda page: page.get("character_count", 0),
    )

    return selected_page


# ---------------------------------------------------------
# Build the controlled Claude prompt
# ---------------------------------------------------------

def build_prompt(page: dict[str, Any]) -> str:
    """
    Build a constrained ESG evidence-extraction prompt.
    """

    return f"""
You are extracting ESG disclosure evidence from one page of a TJX report.

SOURCE DOCUMENT:
{page["source_document"]}

PDF PAGE:
{page["pdf_page_number"]}

SOURCE TEXT:
---BEGIN SOURCE TEXT---
{page["text"]}
---END SOURCE TEXT---

Extract only evidence explicitly supported by the source text.

Return one valid JSON object with this exact structure:

{{
  "source_document": "{page["source_document"]}",
  "pdf_page_number": {page["pdf_page_number"]},
  "evidence_items": [
    {{
      "evidence_id": "EV-001",
      "topic": "brief ESG topic",
      "claim": "faithful summary of what the source explicitly states",
      "exact_quote": "shortest verbatim source passage that supports the claim",
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
3. Do not infer missing facts.
4. Copy each exact_quote directly from the source text.
5. Preserve the wording, capitalization, punctuation, and sentence order.
6. You may replace PDF line breaks with spaces.
7. Do not paraphrase inside exact_quote.
8. Use null when information is unavailable.
9. Do not invent metrics, dates, scopes, targets, programs, entities, or outcomes.
10. Return no more than five evidence items.
11. Prefer short quotations of one or two sentences.
12. Each quotation must directly support the related claim.
13. Return valid JSON only.
14. Do not use markdown code fences.
15. Do not include commentary before or after the JSON.
""".strip()


# ---------------------------------------------------------
# Clean Claude response
# ---------------------------------------------------------

def clean_json_response(response_text: str) -> str:
    """
    Remove accidental markdown fences from Claude's response.
    """

    cleaned = response_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]

    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


# ---------------------------------------------------------
# Normalize PDF and Claude text
# ---------------------------------------------------------

def normalize_text(value: str) -> str:
    """
    Normalize common PDF extraction differences without changing
    the substantive wording.

    This handles:
    - Unicode normalization
    - line-break differences
    - repeated whitespace
    - nonbreaking spaces
    - curly quotation marks
    - long dashes
    - words split by PDF line wrapping
    """

    if not isinstance(value, str):
        return ""

    value = unicodedata.normalize("NFKC", value)

    # Join words split by a hyphen and a PDF line break.
    value = re.sub(
        r"-\s*\n\s*",
        "-",
        value,
    )

    # Normalize punctuation.
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

    # Collapse all whitespace into one space.
    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


# ---------------------------------------------------------
# Validate Claude JSON structure
# ---------------------------------------------------------

def validate_result_structure(
    result: dict[str, Any],
    source_page: dict[str, Any],
) -> None:
    """
    Validate the basic response structure and source lineage.
    """

    if not isinstance(result, dict):
        raise ValueError(
            "Claude response must be a JSON object."
        )

    expected_document = source_page["source_document"]
    expected_page = source_page["pdf_page_number"]

    returned_document = result.get("source_document")
    returned_page = result.get("pdf_page_number")

    if returned_document != expected_document:
        raise ValueError(
            "Source-document validation failed.\n"
            f"Expected: {expected_document}\n"
            f"Received: {returned_document}"
        )

    if returned_page != expected_page:
        raise ValueError(
            "PDF-page validation failed.\n"
            f"Expected: {expected_page}\n"
            f"Received: {returned_page}"
        )

    evidence_items = result.get("evidence_items")

    if not isinstance(evidence_items, list):
        raise ValueError(
            "evidence_items must be a JSON list."
        )

    if len(evidence_items) > 5:
        raise ValueError(
            "Claude returned more than five evidence items."
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

    valid_evidence_types = {
        "policy",
        "target",
        "metric",
        "action",
        "governance",
        "risk",
        "other",
    }

    valid_confidence_values = {
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
                f"Evidence item {index} must be a JSON object."
            )

        missing_fields = required_fields - set(item.keys())

        if missing_fields:
            raise ValueError(
                f"Evidence item {index} is missing fields: "
                f"{sorted(missing_fields)}"
            )

        if not item.get("evidence_id"):
            raise ValueError(
                f"Evidence item {index} has no evidence_id."
            )

        if not item.get("topic"):
            raise ValueError(
                f"Evidence item {index} has no topic."
            )

        if not item.get("claim"):
            raise ValueError(
                f"Evidence item {index} has no claim."
            )

        evidence_type = item.get("evidence_type")

        if evidence_type not in valid_evidence_types:
            raise ValueError(
                f"Invalid evidence_type in item {index}: "
                f"{evidence_type}"
            )

        confidence = item.get("confidence")

        if confidence not in valid_confidence_values:
            raise ValueError(
                f"Invalid confidence in item {index}: "
                f"{confidence}"
            )


# ---------------------------------------------------------
# Validate exact quotations
# ---------------------------------------------------------

def validate_quotes(
    result: dict[str, Any],
    source_text: str,
) -> None:
    """
    Confirm that every Claude quotation exists in the source page
    after controlled normalization.
    """

    evidence_items = result.get(
        "evidence_items",
        [],
    )

    normalized_source = normalize_text(source_text)

    for item in evidence_items:
        evidence_id = item.get(
            "evidence_id",
            "UNKNOWN",
        )

        quote = item.get("exact_quote")

        if not quote:
            raise ValueError(
                f"Missing exact quote for {evidence_id}."
            )

        normalized_quote = normalize_text(quote)

        if not normalized_quote:
            raise ValueError(
                f"Quote became empty after normalization "
                f"for {evidence_id}."
            )

        if normalized_quote not in normalized_source:
            raise ValueError(
                f"Quote validation failed for {evidence_id}.\n\n"
                f"Original quote:\n{quote}\n\n"
                f"Normalized quote:\n{normalized_quote}"
            )


# ---------------------------------------------------------
# Add validation metadata
# ---------------------------------------------------------

def add_validation_metadata(
    result: dict[str, Any],
) -> dict[str, Any]:
    """
    Add Python-generated validation fields to each evidence item.
    """

    for item in result.get(
        "evidence_items",
        [],
    ):
        item["quote_validation_status"] = "passed"
        item["human_review_status"] = "pending"

    result["extraction_status"] = "validated_by_python"
    result["human_review_required"] = True

    return result


# ---------------------------------------------------------
# Save evidence output
# ---------------------------------------------------------

def save_result(
    result: dict[str, Any],
) -> None:
    """
    Save the validated evidence register as formatted JSON.
    """

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2,
        )


# ---------------------------------------------------------
# Main workflow
# ---------------------------------------------------------

def main() -> None:
    """
    Run one controlled ESG evidence-extraction test.
    """

    load_dotenv()

    api_key = os.getenv(
        "ANTHROPIC_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "Missing ANTHROPIC_API_KEY in the .env file."
        )

    pages = load_pages()

    test_page = select_test_page(
        pages
    )

    print(
        f"Selected PDF page "
        f"{test_page['pdf_page_number']} "
        f"with "
        f"{test_page['character_count']:,} characters."
    )

    client = Anthropic(
        api_key=api_key
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1800,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": build_prompt(
                    test_page
                ),
            }
        ],
    )

    if not response.content:
        raise RuntimeError(
            "Claude returned no response content."
        )

    response_text = response.content[0].text

    cleaned_text = clean_json_response(
        response_text
    )

    try:
        result = json.loads(
            cleaned_text
        )

    except json.JSONDecodeError as error:
        print(
            "\nClaude returned invalid JSON:\n"
        )
        print(response_text)

        raise RuntimeError(
            "JSON parsing failed."
        ) from error

    validate_result_structure(
        result=result,
        source_page=test_page,
    )

    validate_quotes(
        result=result,
        source_text=test_page["text"],
    )

    result = add_validation_metadata(
        result
    )

    save_result(
        result
    )

    evidence_count = len(
        result.get(
            "evidence_items",
            [],
        )
    )

    print(
        f"Evidence items extracted: "
        f"{evidence_count}"
    )

    print(
        "JSON structure validation passed."
    )

    print(
        "Source-document validation passed."
    )

    print(
        "PDF-page validation passed."
    )

    print(
        "Exact-quote validation passed."
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()