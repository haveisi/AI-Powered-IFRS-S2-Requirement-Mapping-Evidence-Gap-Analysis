import json
import os
import re
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CANDIDATE_FILE = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "TJX_CDP_gap_evidence_candidates.json"
)

SOURCE_FILE = (
    PROJECT_ROOT
    / "03_Extracted_Text"
    / "TJX_2025_CDP_Climate_Response.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "TJX_CDP_gap_evidence_quote_repaired.json"
)


# =========================================================
# SETTINGS
# =========================================================

MODEL = "claude-sonnet-4-6"

MAX_TOKENS = 1800


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv(
    PROJECT_ROOT / ".env"
)

api_key = os.getenv(
    "ANTHROPIC_API_KEY"
)

if not api_key:
    raise ValueError(
        "ANTHROPIC_API_KEY not found."
    )

client = Anthropic(
    api_key=api_key
)


# =========================================================
# JSON HELPERS
# =========================================================

def load_json(path):

    if not path.exists():
        raise FileNotFoundError(
            f"File not found:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def save_json(data, path):

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_text(text):

    if not text:
        return ""

    # Non-breaking spaces
    text = text.replace(
        "\u00a0",
        " ",
    )

    # Soft hyphen
    text = text.replace(
        "\u00ad",
        "",
    )

    # Normalize curly quotes
    text = text.replace(
        "\u2018",
        "'",
    )

    text = text.replace(
        "\u2019",
        "'",
    )

    text = text.replace(
        "\u201c",
        '"',
    )

    text = text.replace(
        "\u201d",
        '"',
    )

    # Normalize long dashes
    text = text.replace(
        "\u2013",
        "-",
    )

    text = text.replace(
        "\u2014",
        "-",
    )

    # Collapse whitespace
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# =========================================================
# PAGE LOOKUP
# =========================================================

def build_page_lookup(
    source_pages,
):

    return {
        page["page_number"]:
            page["text"]

        for page in source_pages
    }


# =========================================================
# STRICT QUOTE CHECK
# =========================================================

def quote_exists(
    quote,
    page_text,
):

    quote_normalized = normalize_text(
        quote
    )

    page_normalized = normalize_text(
        page_text
    )

    if not quote_normalized:
        return False

    return (
        quote_normalized
        in page_normalized
    )


# =========================================================
# CLAUDE QUOTE REPAIR
# =========================================================

def repair_quote(
    requirement_id,
    evidence,
    page_text,
):

    page_number = evidence[
        "page_number"
    ]

    failed_quote = evidence.get(
        "exact_quote",
        "",
    )

    claim = evidence.get(
        "evidence_claim",
        "",
    )

    prompt = f"""
You are repairing an evidence quotation in a controlled
sustainability disclosure review.

REQUIREMENT:
{requirement_id}

PDF PAGE:
{page_number}

EVIDENCE CLAIM:
{claim}

PREVIOUS QUOTE THAT FAILED EXACT VALIDATION:
{failed_quote}


TASK

Look ONLY at the source page below.

Determine whether the source page directly supports the
evidence claim.

If it does:

1. Copy the smallest useful supporting passage VERBATIM.
2. Do not paraphrase.
3. Do not correct grammar.
4. Do not combine separate passages.
5. Do not add words.
6. Do not remove words from inside the selected passage.
7. Preserve numbers exactly.
8. Return JSON only.

If the page does NOT directly support the claim,
do not invent a quotation.

Return:

{{
  "status": "NO_EXACT_SUPPORT",
  "exact_quote": null
}}

Otherwise return:

{{
  "status": "QUOTE_FOUND",
  "exact_quote": "exact verbatim passage from the source page"
}}


SOURCE PAGE

===== PDF PAGE {page_number} =====

{page_text}
"""

    response = client.messages.create(

        model=MODEL,

        max_tokens=MAX_TOKENS,

        temperature=0,

        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    raw = response.content[
        0
    ].text.strip()

    raw = re.sub(
        r"^```json\s*",
        "",
        raw,
        flags=re.IGNORECASE,
    )

    raw = re.sub(
        r"\s*```$",
        "",
        raw,
    )

    try:

        result = json.loads(
            raw
        )

        return result

    except json.JSONDecodeError:

        return {
            "status":
                "REPAIR_RESPONSE_ERROR",

            "exact_quote":
                None,

            "raw_response":
                raw,
        }


# =========================================================
# PROCESS
# =========================================================

def main():

    print()
    print("=" * 80)
    print("TJX CDP FAILED QUOTE REPAIR")
    print("=" * 80)

    candidates = load_json(
        CANDIDATE_FILE
    )

    source_pages = load_json(
        SOURCE_FILE
    )

    page_lookup = build_page_lookup(
        source_pages
    )

    original_pass = 0

    attempted_repairs = 0

    repaired_pass = 0

    unresolved = 0

    output_results = []

    for requirement_result in candidates:

        requirement_id = (
            requirement_result[
                "requirement_id"
            ]
        )

        print()
        print(
            f"Requirement: "
            f"{requirement_id}"
        )

        for evidence in (
            requirement_result.get(
                "evidence_items",
                [],
            )
        ):

            current_status = (
                evidence.get(
                    "quote_validation"
                )
            )

            # -----------------------------------------
            # Preserve existing PASS items
            # -----------------------------------------

            if current_status == "PASS":

                original_pass += 1

                evidence[
                    "quote_repair_status"
                ] = "NOT_REQUIRED"

                continue

            # -----------------------------------------
            # Failed item
            # -----------------------------------------

            attempted_repairs += 1

            page_number = evidence[
                "page_number"
            ]

            page_text = page_lookup.get(
                page_number,
                "",
            )

            print(
                f"  Repairing page "
                f"{page_number}..."
            )

            repair = repair_quote(
                requirement_id,
                evidence,
                page_text,
            )

            repair_status = repair.get(
                "status"
            )

            repaired_quote = repair.get(
                "exact_quote"
            )

            # -----------------------------------------
            # Claude found candidate quote
            # -----------------------------------------

            if (
                repair_status
                == "QUOTE_FOUND"
                and repaired_quote
            ):

                valid = quote_exists(
                    repaired_quote,
                    page_text,
                )

                if valid:

                    evidence[
                        "original_failed_quote"
                    ] = evidence.get(
                        "exact_quote"
                    )

                    evidence[
                        "exact_quote"
                    ] = repaired_quote

                    evidence[
                        "quote_validation"
                    ] = "PASS"

                    evidence[
                        "quote_repair_status"
                    ] = "REPAIRED_PASS"

                    evidence[
                        "review_status"
                    ] = (
                        "Ready for Human Review"
                    )

                    repaired_pass += 1

                    print(
                        "    REPAIRED PASS"
                    )

                else:

                    evidence[
                        "quote_repair_status"
                    ] = (
                        "REPAIR_FAILED_VALIDATION"
                    )

                    evidence[
                        "review_status"
                    ] = (
                        "Technical Review Required"
                    )

                    unresolved += 1

                    print(
                        "    STILL FAIL"
                    )

            # -----------------------------------------
            # No exact support
            # -----------------------------------------

            elif (
                repair_status
                == "NO_EXACT_SUPPORT"
            ):

                evidence[
                    "quote_repair_status"
                ] = "NO_EXACT_SUPPORT"

                evidence[
                    "review_status"
                ] = (
                    "Technical Review Required"
                )

                unresolved += 1

                print(
                    "    NO EXACT SUPPORT"
                )

            # -----------------------------------------
            # Other failure
            # -----------------------------------------

            else:

                evidence[
                    "quote_repair_status"
                ] = (
                    "REPAIR_PROCESSING_ERROR"
                )

                evidence[
                    "review_status"
                ] = (
                    "Technical Review Required"
                )

                evidence[
                    "quote_repair_response"
                ] = repair

                unresolved += 1

                print(
                    "    REPAIR ERROR"
                )

        output_results.append(
            requirement_result
        )

    save_json(
        output_results,
        OUTPUT_FILE,
    )

    print()
    print("=" * 80)
    print("QUOTE REPAIR SUMMARY")
    print("=" * 80)

    print(
        f"Original quote PASS: "
        f"{original_pass}"
    )

    print(
        f"Failed quotes sent for repair: "
        f"{attempted_repairs}"
    )

    print(
        f"Successfully repaired: "
        f"{repaired_pass}"
    )

    print(
        f"Still unresolved: "
        f"{unresolved}"
    )

    final_pass = (
        original_pass
        + repaired_pass
    )

    print(
        f"Final quotes ready for human review: "
        f"{final_pass}"
    )

    print()
    print(
        "Saved to:"
    )

    print(
        OUTPUT_FILE
    )

    print("=" * 80)


if __name__ == "__main__":
    main()