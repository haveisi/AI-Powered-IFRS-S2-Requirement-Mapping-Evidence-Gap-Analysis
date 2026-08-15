import json
import os
import re
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "03_Extracted_Text"
    / "TJX_CDP_hybrid_retrieval_results.json"
)

SOURCE_PAGES_FILE = (
    PROJECT_ROOT
    / "03_Extracted_Text"
    / "TJX_2025_CDP_Climate_Response.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "TJX_CDP_gap_evidence_candidates.json"
)

FAILED_OUTPUT_FILE = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "TJX_CDP_gap_evidence_failures.json"
)


# =========================================================
# SETTINGS
# =========================================================

MODEL = "claude-sonnet-4-6"

# Start with strongest retrieved pages only.
TOP_PAGES_PER_REQUIREMENT = 4

MAX_TOKENS = 5000


# =========================================================
# REQUIREMENT DEFINITIONS
# =========================================================

REQUIREMENTS = {

    "S2-GOV-02": {
        "name": "Board climate oversight",

        "need": (
            "Evidence identifying board or board-committee oversight "
            "of climate-related risks, opportunities, targets, "
            "performance, responsibilities, reporting lines, "
            "decision authority, or oversight frequency."
        ),
    },

    "S2-STR-06": {
        "name": "Climate resilience and scenario analysis",

        "need": (
            "Evidence of climate scenario analysis including scenarios, "
            "temperature pathways, assumptions, time horizons, physical "
            "risks, transition risks, vulnerabilities, financial or "
            "operational implications, resilience conclusions, or "
            "planned responses."
        ),
    },

    "S2-MT-01": {
        "name": "Scope 1 emissions",

        "need": (
            "Evidence of gross Scope 1 greenhouse gas emissions, "
            "including emissions value, unit, reporting period, "
            "organizational boundary, measurement methodology, "
            "emission factors, consolidation approach, or activity data."
        ),
    },

    "S2-MT-02": {
        "name": "Scope 2 emissions",

        "need": (
            "Evidence of gross Scope 2 greenhouse gas emissions, "
            "especially market-based and location-based values, "
            "including unit, reporting period, organizational boundary, "
            "measurement methodology, emission factors, or contractual "
            "instrument treatment."
        ),
    },

    "S2-MT-04": {
        "name": "Climate-related targets",

        "need": (
            "Evidence of climate-related targets including target value, "
            "baseline year, target year, emissions scope, organizational "
            "boundary, methodology, validation status, interim milestones, "
            "offsets or removals, baseline recalculation, and progress."
        ),
    },
}


# =========================================================
# PYDANTIC SCHEMA
# =========================================================

class EvidenceItem(BaseModel):

    requirement_id: str

    page_number: int

    exact_quote: str

    evidence_claim: str

    evidence_type: str

    relevance: str

    coverage_strength: str

    metric_name: Optional[str] = None

    # IMPORTANT:
    # Claude may naturally return a numeric value.
    metric_value: Optional[str | int | float] = None

    metric_unit: Optional[str] = None

    reporting_period: Optional[str] = None

    baseline_year: Optional[str | int] = None

    target_year: Optional[str | int] = None

    missing_elements: list[str] = Field(
        default_factory=list
    )

    reviewer_attention: Optional[str] = None


class EvidenceResponse(BaseModel):

    requirement_id: str

    evidence_found: bool

    evidence_items: list[EvidenceItem]

    requirement_level_notes: str


# =========================================================
# ENVIRONMENT / CLAUDE CLIENT
# =========================================================

load_dotenv(
    PROJECT_ROOT / ".env"
)

api_key = os.getenv(
    "ANTHROPIC_API_KEY"
)

if not api_key:
    raise ValueError(
        "ANTHROPIC_API_KEY not found in .env"
    )

client = Anthropic(
    api_key=api_key
)


# =========================================================
# LOAD JSON
# =========================================================

def load_json(path: Path):

    if not path.exists():
        raise FileNotFoundError(
            f"File not found:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# =========================================================
# SAVE JSON
# =========================================================

def save_json(
    data,
    path: Path,
):

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
# BUILD RETRIEVED CONTEXT
# =========================================================

def build_context(
    requirement_id,
    hybrid_results,
    page_lookup,
):

    rows = hybrid_results[
        requirement_id
    ][:TOP_PAGES_PER_REQUIREMENT]

    blocks = []

    for row in rows:

        page_number = row[
            "page_number"
        ]

        page_text = page_lookup.get(
            page_number,
            ""
        )

        block = (
            f"\n"
            f"===== PDF PAGE {page_number} =====\n"
            f"{page_text}\n"
        )

        blocks.append(
            block
        )

    return "\n".join(
        blocks
    )


# =========================================================
# PROMPT
# =========================================================

def build_prompt(
    requirement_id,
    context,
):

    requirement = REQUIREMENTS[
        requirement_id
    ]

    return f"""
You are reviewing TJX's 2025 CDP Climate Response for
evidence relevant to an ISSB climate disclosure readiness
assessment.

REQUIREMENT ID:
{requirement_id}

REQUIREMENT NAME:
{requirement["name"]}

EVIDENCE NEEDED:
{requirement["need"]}


STRICT EVIDENCE RULES

1. Use ONLY the source text provided below.

2. Do not use outside knowledge.

3. Do not infer a value, governance structure, methodology,
   target feature, or disclosure that is not explicitly supported.

4. exact_quote must be copied from ONE source page.

5. Keep each evidence item atomic.
   One evidence item should support one principal claim.

6. Do not treat a target as actual emissions performance.

7. Do not treat management-level responsibility as board-level
   oversight unless the source explicitly establishes that link.

8. Do not treat combined Scope 1 and Scope 2 emissions as a
   separate gross Scope 1 or separate gross Scope 2 disclosure.

9. For metrics, populate metric fields only when the source
   actually gives a measurable value.

10. Missing information is important.
    List important disclosure elements that remain unsupported.

11. coverage_strength must be one of:
    Weak
    Moderate
    Strong

12. relevance must be one of:
    Direct
    Supporting

13. evidence_type should use a concise category such as:
    Governance
    Scenario Analysis
    GHG Metric
    Climate Target
    Target Progress
    Methodology

14. metric_value may be a number or text.

15. If one page contains multiple distinct claims, create separate
    evidence items only where useful.

16. Do not duplicate the same quote or claim.

Return JSON ONLY.

Do not use markdown code fences.

Use exactly this structure:

{{
  "requirement_id": "{requirement_id}",
  "evidence_found": true,
  "evidence_items": [
    {{
      "requirement_id": "{requirement_id}",
      "page_number": 1,
      "exact_quote": "verbatim source text",
      "evidence_claim": "what this quote supports",
      "evidence_type": "GHG Metric",
      "relevance": "Direct",
      "coverage_strength": "Strong",
      "metric_name": null,
      "metric_value": null,
      "metric_unit": null,
      "reporting_period": null,
      "baseline_year": null,
      "target_year": null,
      "missing_elements": [],
      "reviewer_attention": null
    }}
  ],
  "requirement_level_notes":
    "short assessment of what the retrieved evidence supports and what remains missing"
}}

If there is no valid evidence:

{{
  "requirement_id": "{requirement_id}",
  "evidence_found": false,
  "evidence_items": [],
  "requirement_level_notes":
    "No directly relevant evidence identified in the retrieved pages."
}}


SOURCE TEXT

{context}
"""


# =========================================================
# CLEAN JSON RESPONSE
# =========================================================

def clean_json_text(
    text: str,
) -> str:

    text = text.strip()

    # Remove accidental markdown fences.
    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"^```\s*",
        "",
        text,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    return text.strip()


# =========================================================
# CLAUDE CALL
# =========================================================

def call_claude(
    prompt: str,
):

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

    return response.content[
        0
    ].text


# =========================================================
# REPAIR MALFORMED JSON
# =========================================================

def repair_json_with_claude(
    raw_text: str,
    requirement_id: str,
):

    repair_prompt = f"""
The following response is intended to be valid JSON,
but its JSON syntax is malformed.

Fix ONLY the JSON syntax.

Do not change the meaning.
Do not add evidence.
Do not remove evidence.
Do not summarize.
Do not rewrite quotes.
Do not add markdown.

Return valid JSON only.

REQUIREMENT:
{requirement_id}

MALFORMED JSON:

{raw_text}
"""

    repaired_text = call_claude(
        repair_prompt
    )

    return clean_json_text(
        repaired_text
    )


# =========================================================
# PARSE + VALIDATE CLAUDE OUTPUT
# =========================================================

def parse_and_validate(
    text: str,
):

    parsed_json = json.loads(
        text
    )

    validated = (
        EvidenceResponse
        .model_validate(
            parsed_json
        )
    )

    return validated.model_dump()


# =========================================================
# EXTRACT ONE REQUIREMENT
# =========================================================

def extract_requirement(
    requirement_id,
    context,
):

    prompt = build_prompt(
        requirement_id,
        context,
    )

    print()
    print(
        f"Claude extraction: "
        f"{requirement_id}"
    )

    raw_text = call_claude(
        prompt
    )

    cleaned_text = clean_json_text(
        raw_text
    )

    # -----------------------------------------------------
    # FIRST ATTEMPT
    # -----------------------------------------------------

    try:

        return parse_and_validate(
            cleaned_text
        )

    # -----------------------------------------------------
    # JSON SYNTAX FAILURE
    # -----------------------------------------------------

    except json.JSONDecodeError as error:

        print()
        print(
            f"JSON ERROR for "
            f"{requirement_id}:"
        )

        print(
            error
        )

        print(
            "Attempting one JSON repair..."
        )

        try:

            repaired_text = (
                repair_json_with_claude(
                    raw_text,
                    requirement_id,
                )
            )

            repaired_result = (
                parse_and_validate(
                    repaired_text
                )
            )

            print(
                f"JSON repair PASS: "
                f"{requirement_id}"
            )

            repaired_result[
                "json_repair_used"
            ] = True

            return repaired_result

        except (
            json.JSONDecodeError,
            ValidationError,
        ) as repair_error:

            print()
            print(
                f"JSON repair FAILED: "
                f"{requirement_id}"
            )

            print(
                repair_error
            )

            return {
                "requirement_id":
                    requirement_id,

                "evidence_found":
                    False,

                "evidence_items":
                    [],

                "requirement_level_notes":
                    (
                        "Claude output failed "
                        "JSON syntax repair or "
                        "Pydantic validation."
                    ),

                "processing_error":
                    str(repair_error),

                "raw_response":
                    raw_text,

                "repaired_response":
                    repaired_text,
            }

    # -----------------------------------------------------
    # PYDANTIC SCHEMA FAILURE
    # -----------------------------------------------------

    except ValidationError as error:

        print()
        print(
            f"PYDANTIC VALIDATION ERROR "
            f"for {requirement_id}:"
        )

        print(
            error
        )

        return {
            "requirement_id":
                requirement_id,

            "evidence_found":
                False,

            "evidence_items":
                [],

            "requirement_level_notes":
                (
                    "Claude returned valid JSON, "
                    "but it did not match the "
                    "required evidence schema."
                ),

            "processing_error":
                str(error),

            "raw_response":
                raw_text,
        }


# =========================================================
# QUOTE NORMALIZATION
# =========================================================

def normalize_quote(
    text: str,
) -> str:

    if text is None:
        return ""

    text = text.replace(
        "\u00a0",
        " ",
    )

    return " ".join(
        text.split()
    )


# =========================================================
# EXACT QUOTE VALIDATION
# =========================================================

def validate_quotes(
    result,
    page_lookup,
):

    for evidence in result.get(
        "evidence_items",
        [],
    ):

        page_number = evidence.get(
            "page_number"
        )

        exact_quote = evidence.get(
            "exact_quote",
            "",
        )

        page_text = page_lookup.get(
            page_number,
            "",
        )

        normalized_page = (
            normalize_quote(
                page_text
            )
        )

        normalized_quote_text = (
            normalize_quote(
                exact_quote
            )
        )

        quote_valid = (
            normalized_quote_text
            in normalized_page
            and normalized_quote_text != ""
        )

        evidence[
            "quote_validation"
        ] = (
            "PASS"
            if quote_valid
            else "FAIL"
        )

    return result


# =========================================================
# REQUIREMENT ID VALIDATION
# =========================================================

def validate_requirement_ids(
    result,
):

    expected_id = result.get(
        "requirement_id"
    )

    for evidence in result.get(
        "evidence_items",
        [],
    ):

        evidence_id = evidence.get(
            "requirement_id"
        )

        if evidence_id == expected_id:

            evidence[
                "requirement_id_validation"
            ] = "PASS"

        else:

            evidence[
                "requirement_id_validation"
            ] = "FAIL"

    return result


# =========================================================
# PAGE VALIDATION
# =========================================================

def validate_pages(
    result,
    page_lookup,
):

    valid_pages = set(
        page_lookup.keys()
    )

    for evidence in result.get(
        "evidence_items",
        [],
    ):

        page_number = evidence.get(
            "page_number"
        )

        evidence[
            "page_validation"
        ] = (
            "PASS"
            if page_number in valid_pages
            else "FAIL"
        )

    return result


# =========================================================
# REVIEW FLAG
# =========================================================

def add_review_flag(
    result,
):

    for evidence in result.get(
        "evidence_items",
        [],
    ):

        quote_status = evidence.get(
            "quote_validation"
        )

        page_status = evidence.get(
            "page_validation"
        )

        requirement_status = evidence.get(
            "requirement_id_validation"
        )

        if (
            quote_status == "PASS"
            and page_status == "PASS"
            and requirement_status == "PASS"
        ):

            evidence[
                "review_status"
            ] = "Ready for Human Review"

        else:

            evidence[
                "review_status"
            ] = "Technical Review Required"

    return result


# =========================================================
# PROCESS ONE REQUIREMENT
# =========================================================

def process_requirement(
    requirement_id,
    hybrid_results,
    page_lookup,
):

    context = build_context(
        requirement_id,
        hybrid_results,
        page_lookup,
    )

    result = extract_requirement(
        requirement_id,
        context,
    )

    result = validate_quotes(
        result,
        page_lookup,
    )

    result = validate_requirement_ids(
        result
    )

    result = validate_pages(
        result,
        page_lookup,
    )

    result = add_review_flag(
        result
    )

    return result


# =========================================================
# SUMMARY
# =========================================================

def print_summary(
    results,
):

    print()
    print("=" * 80)
    print("CDP EVIDENCE EXTRACTION SUMMARY")
    print("=" * 80)

    total_evidence = 0
    passed_quotes = 0
    failed_quotes = 0
    ready_for_review = 0
    technical_review = 0
    processing_failures = 0

    for result in results:

        requirement_id = (
            result[
                "requirement_id"
            ]
        )

        items = result.get(
            "evidence_items",
            [],
        )

        if result.get(
            "processing_error"
        ):
            processing_failures += 1

        print()
        print(
            f"{requirement_id}: "
            f"{len(items)} evidence item(s)"
        )

        if result.get(
            "json_repair_used"
        ):
            print(
                "  JSON repair used: YES"
            )

        if result.get(
            "processing_error"
        ):
            print(
                "  Processing error: YES"
            )

        for item in items:

            total_evidence += 1

            quote_status = item.get(
                "quote_validation"
            )

            review_status = item.get(
                "review_status"
            )

            if quote_status == "PASS":
                passed_quotes += 1

            elif quote_status == "FAIL":
                failed_quotes += 1

            if (
                review_status
                == "Ready for Human Review"
            ):
                ready_for_review += 1

            else:
                technical_review += 1

            print(
                f"  Page "
                f"{item['page_number']}"
                f" | "
                f"{item['relevance']}"
                f" | "
                f"{item['coverage_strength']}"
                f" | Quote "
                f"{quote_status}"
                f" | "
                f"{review_status}"
            )

    print()
    print("-" * 80)

    print(
        f"Total evidence items: "
        f"{total_evidence}"
    )

    print(
        f"Quote validation PASS: "
        f"{passed_quotes}"
    )

    print(
        f"Quote validation FAIL: "
        f"{failed_quotes}"
    )

    print(
        f"Ready for Human Review: "
        f"{ready_for_review}"
    )

    print(
        f"Technical Review Required: "
        f"{technical_review}"
    )

    print(
        f"Requirement processing failures: "
        f"{processing_failures}"
    )

    print("=" * 80)


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 80)
    print("TJX CDP GAP EVIDENCE EXTRACTION")
    print("=" * 80)

    hybrid_results = load_json(
        INPUT_FILE
    )

    source_pages = load_json(
        SOURCE_PAGES_FILE
    )

    page_lookup = build_page_lookup(
        source_pages
    )

    all_results = []

    failure_results = []

    for requirement_id in REQUIREMENTS:

        result = process_requirement(
            requirement_id,
            hybrid_results,
            page_lookup,
        )

        all_results.append(
            result
        )

        if result.get(
            "processing_error"
        ):
            failure_results.append(
                result
            )

    save_json(
        all_results,
        OUTPUT_FILE,
    )

    save_json(
        failure_results,
        FAILED_OUTPUT_FILE,
    )

    print_summary(
        all_results
    )

    print()
    print(
        "Saved evidence candidates to:"
    )

    print(
        OUTPUT_FILE
    )

    print()
    print(
        "Saved processing failures to:"
    )

    print(
        FAILED_OUTPUT_FILE
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "These are AI-generated evidence candidates."
    )

    print(
        "Technical validation does not equal "
        "human approval."
    )

    print(
        "Only human-reviewed evidence should be "
        "moved into Approved Evidence."
    )


if __name__ == "__main__":
    main()