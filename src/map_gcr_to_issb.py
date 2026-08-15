import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "TJX_combined_approved_evidence.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "TJX_combined_evidence_with_gcr_mapping.json"
)

REVIEW_FILE = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "TJX_GCR_ISSB_mapping_review.csv"
)


# =========================================================
# REQUIREMENT DEFINITIONS
# =========================================================

REQUIREMENTS = {

    "S2-GOV-02": {
        "name": "Board oversight of climate-related risks and opportunities",
        "keywords": [
            "board",
            "board of directors",
            "committee",
            "oversight",
            "governance",
            "corporate governance",
            "board-level",
            "periodic updates",
        ],
    },

    "S2-STR-06": {
        "name": "Climate resilience and scenario analysis",
        "keywords": [
            "scenario",
            "resilience",
            "1.5",
            "3.0",
            "climate risk",
            "physical risk",
            "transition risk",
            "time horizon",
            "2050",
            "2030",
        ],
    },

    "S2-MT-01": {
        "name": "Scope 1 greenhouse gas emissions",
        "keywords": [
            "scope 1",
            "direct emissions",
            "greenhouse gas emissions",
            "ghg emissions",
            "tco2e",
            "metric tons co2e",
        ],
    },

    "S2-MT-02": {
        "name": "Scope 2 greenhouse gas emissions",
        "keywords": [
            "scope 2",
            "location-based",
            "market-based",
            "electricity",
            "renewable electricity",
            "purchased electricity",
        ],
    },

    "S2-MT-04": {
        "name": "Climate targets",
        "keywords": [
            "target",
            "goal",
            "2030",
            "2040",
            "net zero",
            "net-zero",
            "55%",
            "renewable",
            "emissions reduction",
        ],
    },
}


# =========================================================
# HELPERS
# =========================================================

def clean(value):

    if value is None:
        return ""

    return str(value).strip()


def load_json(path: Path):

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def save_json(data, path: Path):

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
# SCORE GCR RECORD AGAINST REQUIREMENT
# =========================================================

def score_requirement(
    record: dict,
    requirement_id: str,
):

    requirement = (
        REQUIREMENTS[
            requirement_id
        ]
    )

    searchable_text = " ".join(
        [
            clean(
                record.get(
                    "final_evidence_claim"
                )
            ),
            clean(
                record.get(
                    "final_exact_quote"
                )
            ),
            clean(
                record.get(
                    "evidence_type"
                )
            ),
            clean(
                record.get(
                    "metric_name"
                )
            ),
        ]
    ).lower()

    matched_keywords = []

    for keyword in (
        requirement[
            "keywords"
        ]
    ):

        if keyword.lower() in searchable_text:

            matched_keywords.append(
                keyword
            )

    score = len(
        matched_keywords
    )

    return (
        score,
        matched_keywords,
    )


# =========================================================
# GENERATE MAPPING CANDIDATES
# =========================================================

def generate_mapping_candidates(
    record: dict,
):

    candidates = []

    for requirement_id in REQUIREMENTS:

        score, keywords = (
            score_requirement(
                record,
                requirement_id,
            )
        )

        if score > 0:

            candidates.append(
                {
                    "requirement_id":
                        requirement_id,

                    "requirement_name":
                        REQUIREMENTS[
                            requirement_id
                        ]["name"],

                    "score":
                        score,

                    "matched_keywords":
                        keywords,
                }
            )

    candidates.sort(
        key=lambda item:
            item["score"],
        reverse=True,
    )

    return candidates


# =========================================================
# EXPORT HUMAN REVIEW CSV
# =========================================================

def export_review_csv(
    records,
    path: Path,
):

    import csv

    fieldnames = [
        "Evidence ID",
        "Source",
        "PDF Page",
        "Evidence Claim",
        "Exact Quote",
        "Suggested Requirement ID",
        "Suggested Requirement Name",
        "Mapping Score",
        "Matched Keywords",
        "Human Mapping Decision",
        "Final Requirement ID",
        "Human Mapping Notes",
    ]

    rows = []

    for record in records:

        if (
            record.get(
                "evidence_source"
            )
            != "GCR"
        ):
            continue

        candidates = (
            generate_mapping_candidates(
                record
            )
        )

        if candidates:

            best = candidates[0]

            suggested_id = (
                best[
                    "requirement_id"
                ]
            )

            suggested_name = (
                best[
                    "requirement_name"
                ]
            )

            score = (
                best[
                    "score"
                ]
            )

            keywords = ", ".join(
                best[
                    "matched_keywords"
                ]
            )

        else:

            suggested_id = ""
            suggested_name = ""
            score = 0
            keywords = ""

        rows.append(
            {
                "Evidence ID":
                    record.get(
                        "evidence_id",
                        "",
                    ),

                "Source":
                    record.get(
                        "evidence_source",
                        "",
                    ),

                "PDF Page":
                    record.get(
                        "pdf_page",
                        "",
                    ),

                "Evidence Claim":
                    record.get(
                        "final_evidence_claim",
                        "",
                    ),

                "Exact Quote":
                    record.get(
                        "final_exact_quote",
                        "",
                    ),

                "Suggested Requirement ID":
                    suggested_id,

                "Suggested Requirement Name":
                    suggested_name,

                "Mapping Score":
                    score,

                "Matched Keywords":
                    keywords,

                "Human Mapping Decision":
                    "",

                "Final Requirement ID":
                    "",

                "Human Mapping Notes":
                    "",
            }
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    return rows


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 80)
    print(
        "TJX GCR → ISSB MAPPING PREPARATION"
    )
    print("=" * 80)

    records = load_json(
        INPUT_FILE
    )

    print(
        f"Combined evidence loaded: "
        f"{len(records)}"
    )

    gcr_records = [
        record
        for record in records
        if (
            record.get(
                "evidence_source"
            )
            == "GCR"
        )
    ]

    print(
        f"GCR records to map: "
        f"{len(gcr_records)}"
    )

    review_rows = (
        export_review_csv(
            records,
            REVIEW_FILE,
        )
    )

    print()
    print(
        "Suggested mapping distribution:"
    )

    distribution = {}

    for row in review_rows:

        requirement_id = (
            row[
                "Suggested Requirement ID"
            ]
            or "UNMAPPED"
        )

        distribution[
            requirement_id
        ] = (
            distribution.get(
                requirement_id,
                0,
            )
            + 1
        )

    for requirement_id, count in (
        distribution.items()
    ):

        print(
            f"  {requirement_id}: "
            f"{count}"
        )

    print()
    print(
        "Human mapping review file:"
    )

    print(
        REVIEW_FILE
    )

    print()
    print("=" * 80)
    print(
        "HUMAN REVIEW REQUIRED"
    )
    print("=" * 80)

    print(
        "For each GCR evidence item, "
        "review the suggested requirement."
    )

    print()
    print(
        "Human Mapping Decision should be:"
    )

    print(
        "  Approve"
    )

    print(
        "  Correct"
    )

    print(
        "  Not Relevant"
    )

    print()
    print(
        "If Correct, enter the correct "
        "requirement in Final Requirement ID."
    )

    print()
    print(
        "Do not map evidence only because "
        "a keyword appears. Confirm the "
        "actual disclosure meaning."
    )

    print("=" * 80)


if __name__ == "__main__":
    main()