import csv
import json
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EVIDENCE_DIR = (
    PROJECT_ROOT
    / "05_Evidence_Register"
)

INPUT_FILE = (
    EVIDENCE_DIR
    / "TJX_combined_evidence_with_gcr_mapping.json"
)

OUTPUT_CSV = (
    EVIDENCE_DIR
    / "TJX_S2_GOV_04_candidate_review.csv"
)

OUTPUT_JSON = (
    EVIDENCE_DIR
    / "TJX_S2_GOV_04_candidate_evidence.json"
)


# =========================================================
# REQUIREMENT
# =========================================================

REQUIREMENT_ID = "S2-GOV-04"

REQUIREMENT_NAME = (
    "Management-level responsibility and oversight "
    "for climate-related risks, opportunities, targets, "
    "and related processes"
)


# =========================================================
# SEARCH TERMS
# =========================================================

# High-value concepts for management-level climate oversight.
# These are used only to FIND candidates.
# They do not determine the final mapping.

KEYWORDS = [
    "management",
    "executive",
    "senior executive",
    "cross-functional committee",
    "internal committee",
    "steering committee",
    "responsible for",
    "responsibility",
    "climate",
    "environmental sustainability",
    "greenhouse gas",
    "ghg",
    "renewable energy",
    "target",
    "targets",
    "net zero",
    "net-zero",
    "progress",
    "monitor",
    "monitoring",
    "implementation",
    "roadmap",
    "reporting",
    "metrics",
]


# =========================================================
# HELPERS
# =========================================================

def clean(value):

    if value is None:
        return ""

    return str(value).strip()


def load_json(path: Path):

    if not path.exists():

        raise FileNotFoundError(
            f"Evidence file not found:\n{path}"
        )

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
# SCORE CANDIDATE
# =========================================================

def score_candidate(record: dict):

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
                    "human_reviewer_notes"
                )
            ),
        ]
    ).lower()

    matched = []

    for keyword in KEYWORDS:

        if keyword.lower() in searchable_text:

            matched.append(
                keyword
            )

    # -----------------------------------------------------
    # Base keyword score
    # -----------------------------------------------------

    score = len(
        matched
    )

    # -----------------------------------------------------
    # Strong management-specific bonus
    # -----------------------------------------------------

    management_terms = [
        "management",
        "executive",
        "cross-functional committee",
        "internal committee",
        "steering committee",
    ]

    if any(
        term in searchable_text
        for term in management_terms
    ):
        score += 5

    # -----------------------------------------------------
    # Climate / target responsibility bonus
    # -----------------------------------------------------

    climate_terms = [
        "climate",
        "ghg",
        "greenhouse gas",
        "renewable energy",
        "net zero",
        "net-zero",
    ]

    responsibility_terms = [
        "responsible",
        "responsibility",
        "monitor",
        "progress",
        "implementation",
        "oversight",
    ]

    if (
        any(
            term in searchable_text
            for term in climate_terms
        )
        and
        any(
            term in searchable_text
            for term in responsibility_terms
        )
    ):
        score += 5

    return (
        score,
        matched,
    )


# =========================================================
# FIND CANDIDATES
# =========================================================

def find_candidates(records):

    candidates = []

    for record in records:

        score, matched = (
            score_candidate(
                record
            )
        )

        # ---------------------------------------------
        # Require at least some meaningful signal.
        # ---------------------------------------------

        if score < 3:
            continue

        candidate = {

            "evidence_id":
                clean(
                    record.get(
                        "evidence_id"
                    )
                ),

            "source":
                clean(
                    record.get(
                        "evidence_source"
                    )
                ),

            "existing_requirement_id":
                clean(
                    record.get(
                        "requirement_id"
                    )
                ),

            "pdf_page":
                record.get(
                    "pdf_page",
                    "",
                ),

            "evidence_claim":
                clean(
                    record.get(
                        "final_evidence_claim"
                    )
                ),

            "exact_quote":
                clean(
                    record.get(
                        "final_exact_quote"
                    )
                ),

            "coverage_strength":
                clean(
                    record.get(
                        "coverage_strength"
                    )
                ),

            "candidate_score":
                score,

            "matched_keywords":
                matched,
        }

        candidates.append(
            candidate
        )

    candidates.sort(
        key=lambda item: (
            -item[
                "candidate_score"
            ],
            item[
                "evidence_id"
            ],
        )
    )

    return candidates


# =========================================================
# EXPORT HUMAN REVIEW CSV
# =========================================================

def export_review_csv(
    candidates,
    path: Path,
):

    fieldnames = [
        "Evidence ID",
        "Source",
        "Existing Requirement ID",
        "PDF Page",
        "Evidence Claim",
        "Exact Quote",
        "Current Coverage Strength",
        "Candidate Score",
        "Matched Keywords",
        "Human Decision",
        "Human Coverage Assessment",
        "Reviewer Notes",
    ]

    rows = []

    for item in candidates:

        rows.append(
            {
                "Evidence ID":
                    item[
                        "evidence_id"
                    ],

                "Source":
                    item[
                        "source"
                    ],

                "Existing Requirement ID":
                    item[
                        "existing_requirement_id"
                    ],

                "PDF Page":
                    item[
                        "pdf_page"
                    ],

                "Evidence Claim":
                    item[
                        "evidence_claim"
                    ],

                "Exact Quote":
                    item[
                        "exact_quote"
                    ],

                "Current Coverage Strength":
                    item[
                        "coverage_strength"
                    ],

                "Candidate Score":
                    item[
                        "candidate_score"
                    ],

                "Matched Keywords":
                    ", ".join(
                        item[
                            "matched_keywords"
                        ]
                    ),

                "Human Decision":
                    "",

                "Human Coverage Assessment":
                    "",

                "Reviewer Notes":
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

        writer.writerows(
            rows
        )


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 80)
    print(
        "TJX S2-GOV-04 MANAGEMENT OVERSIGHT REVIEW"
    )
    print("=" * 80)

    records = load_json(
        INPUT_FILE
    )

    print(
        f"Combined evidence loaded: "
        f"{len(records)}"
    )

    candidates = (
        find_candidates(
            records
        )
    )

    print(
        f"S2-GOV-04 candidates found: "
        f"{len(candidates)}"
    )

    save_json(
        candidates,
        OUTPUT_JSON,
    )

    export_review_csv(
        candidates,
        OUTPUT_CSV,
    )

    print()
    print(
        "Top candidates:"
    )

    for item in candidates[:15]:

        print()
        print(
            f"{item['evidence_id']} "
            f"| {item['source']} "
            f"| score {item['candidate_score']}"
        )

        print(
            f"  Existing mapping: "
            f"{item['existing_requirement_id'] or 'None'}"
        )

        print(
            f"  Claim: "
            f"{item['evidence_claim']}"
        )

    print()
    print("=" * 80)

    print(
        "Human review file:"
    )

    print(
        OUTPUT_CSV
    )

    print()
    print(
        "Candidate JSON:"
    )

    print(
        OUTPUT_JSON
    )

    print()
    print("=" * 80)
    print(
        "HUMAN REVIEW RULE"
    )
    print("=" * 80)

    print(
        "Human Decision must be:"
    )

    print(
        "  Approve"
    )

    print(
        "  Reject"
    )

    print(
        "  Duplicate"
    )

    print()
    print(
        "Approve only when the evidence "
        "actually demonstrates management-level "
        "responsibility, oversight, monitoring, "
        "or implementation of climate matters."
    )

    print()
    print(
        "Do not approve a row merely because "
        "it mentions a climate target."
    )

    print("=" * 80)


if __name__ == "__main__":
    main()