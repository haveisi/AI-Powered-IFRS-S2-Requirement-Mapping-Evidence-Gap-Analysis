import csv
import json
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "TJX_CDP_gap_evidence_quote_repaired.json"
)

REVIEW_OUTPUT = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "TJX_CDP_human_review_ready.csv"
)

UNRESOLVED_OUTPUT = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "TJX_CDP_unresolved_evidence.csv"
)


# =========================================================
# REQUIREMENT NAMES
# =========================================================

REQUIREMENT_NAMES = {
    "S2-GOV-02":
        "Board climate oversight",

    "S2-STR-06":
        "Climate resilience and scenario analysis",

    "S2-MT-01":
        "Scope 1 emissions",

    "S2-MT-02":
        "Scope 2 emissions",

    "S2-MT-04":
        "Climate-related targets",
}


# =========================================================
# LOAD JSON
# =========================================================

def load_json(path):

    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# =========================================================
# FLATTEN EVIDENCE
# =========================================================

def flatten_evidence(data):

    review_rows = []
    unresolved_rows = []

    sequence = 1

    for requirement_result in data:

        requirement_id = (
            requirement_result[
                "requirement_id"
            ]
        )

        requirement_name = (
            REQUIREMENT_NAMES.get(
                requirement_id,
                ""
            )
        )

        requirement_notes = (
            requirement_result.get(
                "requirement_level_notes",
                "",
            )
        )

        for item in requirement_result.get(
            "evidence_items",
            [],
        ):

            evidence_id = (
                f"CDP-EV-{sequence:03d}"
            )

            sequence += 1

            missing_elements = item.get(
                "missing_elements",
                [],
            )

            if isinstance(
                missing_elements,
                list,
            ):
                missing_elements = (
                    "; ".join(
                        str(x)
                        for x
                        in missing_elements
                    )
                )

            row = {

                "Evidence ID":
                    evidence_id,

                "Requirement ID":
                    requirement_id,

                "Requirement Name":
                    requirement_name,

                "Source Document":
                    "TJX_2025_CDP_Climate_Response.pdf",

                "PDF Page":
                    item.get(
                        "page_number"
                    ),

                "Evidence Type":
                    item.get(
                        "evidence_type",
                        "",
                    ),

                "Relevance":
                    item.get(
                        "relevance",
                        "",
                    ),

                "AI Coverage Strength":
                    item.get(
                        "coverage_strength",
                        "",
                    ),

                "Evidence Claim":
                    item.get(
                        "evidence_claim",
                        "",
                    ),

                "Exact Quote":
                    item.get(
                        "exact_quote",
                        "",
                    ),

                "Metric Name":
                    item.get(
                        "metric_name",
                        "",
                    ),

                "Metric Value":
                    item.get(
                        "metric_value",
                        "",
                    ),

                "Metric Unit":
                    item.get(
                        "metric_unit",
                        "",
                    ),

                "Reporting Period":
                    item.get(
                        "reporting_period",
                        "",
                    ),

                "Baseline Year":
                    item.get(
                        "baseline_year",
                        "",
                    ),

                "Target Year":
                    item.get(
                        "target_year",
                        "",
                    ),

                "Missing Elements":
                    missing_elements,

                "AI Reviewer Attention":
                    item.get(
                        "reviewer_attention",
                        "",
                    ),

                "Quote Validation":
                    item.get(
                        "quote_validation",
                        "",
                    ),

                "Quote Repair Status":
                    item.get(
                        "quote_repair_status",
                        "",
                    ),

                "Page Validation":
                    item.get(
                        "page_validation",
                        "",
                    ),

                "Requirement ID Validation":
                    item.get(
                        "requirement_id_validation",
                        "",
                    ),

                "Technical Review Status":
                    item.get(
                        "review_status",
                        "",
                    ),

                # ---------------------------------------
                # HUMAN REVIEW FIELDS
                # ---------------------------------------

                "Human Decision":
                    "",

                "Corrected Claim":
                    "",

                "Corrected Quote":
                    "",

                "Corrected Metric Value":
                    "",

                "Human Coverage Assessment":
                    "",

                "Human Reviewer Notes":
                    "",

                "Requirement-Level Notes":
                    requirement_notes,
            }

            if (
                item.get(
                    "review_status"
                )
                == "Ready for Human Review"
                and
                item.get(
                    "quote_validation"
                )
                == "PASS"
            ):

                review_rows.append(
                    row
                )

            else:

                unresolved_rows.append(
                    row
                )

    return (
        review_rows,
        unresolved_rows,
    )


# =========================================================
# WRITE CSV
# =========================================================

def write_csv(
    rows,
    path,
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not rows:
        print(
            f"No rows to save for "
            f"{path.name}"
        )

        return

    fields = list(
        rows[0].keys()
    )

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


# =========================================================
# SUMMARY
# =========================================================

def summarize_by_requirement(
    rows,
):

    counts = {}

    for row in rows:

        requirement_id = row[
            "Requirement ID"
        ]

        counts[
            requirement_id
        ] = (
            counts.get(
                requirement_id,
                0,
            )
            + 1
        )

    return counts


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 80)
    print("TJX CDP HUMAN REVIEW EXPORT")
    print("=" * 80)

    data = load_json(
        INPUT_FILE
    )

    review_rows, unresolved_rows = (
        flatten_evidence(
            data
        )
    )

    write_csv(
        review_rows,
        REVIEW_OUTPUT,
    )

    write_csv(
        unresolved_rows,
        UNRESOLVED_OUTPUT,
    )

    counts = summarize_by_requirement(
        review_rows
    )

    print()
    print(
        f"Ready for human review: "
        f"{len(review_rows)}"
    )

    print(
        f"Unresolved / technical review: "
        f"{len(unresolved_rows)}"
    )

    print()
    print(
        "Ready evidence by requirement:"
    )

    for requirement_id in (
        REQUIREMENT_NAMES
    ):

        print(
            f"  {requirement_id}: "
            f"{counts.get(requirement_id, 0)}"
        )

    print()
    print(
        "Human review file:"
    )

    print(
        REVIEW_OUTPUT
    )

    print()
    print(
        "Unresolved evidence file:"
    )

    print(
        UNRESOLVED_OUTPUT
    )

    print()
    print("=" * 80)
    print(
        "NEXT CONTROL:"
    )

    print(
        "Human Decision must be "
        "Approve, Correct, Reject, or Duplicate."
    )

    print("=" * 80)


if __name__ == "__main__":
    main()