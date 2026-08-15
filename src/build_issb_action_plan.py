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
    / "TJX_ISSB_requirement_reassessment_final.json"
)

OUTPUT_JSON = (
    EVIDENCE_DIR
    / "TJX_ISSB_gap_action_plan.json"
)

OUTPUT_CSV = (
    EVIDENCE_DIR
    / "TJX_ISSB_gap_action_plan.csv"
)


# =========================================================
# DEFAULT MANAGEMENT FIELDS
# =========================================================

DEFAULTS = {

    "S2-GOV-02": {
        "gap_category": "Governance",
        "likely_source": (
            "Board committee charters, governance materials, "
            "climate governance documentation"
        ),
        "owner": "Sustainability / Corporate Governance",
        "priority": "High",
        "effort": "Medium",
    },

    "S2-STR-06": {
        "gap_category": "Strategy / Scenario Analysis",
        "likely_source": (
            "Climate risk analysis, ERM, scenario modelling, "
            "FP&A and strategy documentation"
        ),
        "owner": "Sustainability / ERM / FP&A",
        "priority": "High",
        "effort": "High",
    },

    "S2-MT-01": {
        "gap_category": "Metrics / Scope 1",
        "likely_source": (
            "GHG inventory, emissions methodology, "
            "organizational boundary documentation"
        ),
        "owner": "Sustainability / Environmental Data",
        "priority": "Medium",
        "effort": "Low",
    },

    "S2-MT-02": {
        "gap_category": "Metrics / Scope 2",
        "likely_source": (
            "GHG inventory, utility data, renewable energy records, "
            "Scope 2 methodology"
        ),
        "owner": "Sustainability / Energy Management",
        "priority": "Medium",
        "effort": "Low",
    },

    "S2-MT-04": {
        "gap_category": "Targets",
        "likely_source": (
            "Climate target roadmap, transition planning, "
            "target governance documentation"
        ),
        "owner": "Sustainability / Strategy",
        "priority": "High",
        "effort": "Medium",
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

    if not path.exists():

        raise FileNotFoundError(
            f"Input file not found:\n{path}"
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
# BUILD GAP RECORD
# =========================================================

def build_gap_record(
    record: dict,
    sequence: int,
):

    requirement_id = clean(
        record.get(
            "requirement_id"
        )
    )

    defaults = DEFAULTS.get(
        requirement_id,
        {}
    )

    final_score = record.get(
        "final_score",
        0,
    )

    expected_improvement = (
        4 - int(final_score)
    )

    return {

        "gap_id":
            f"GAP-{sequence:03d}",

        "requirement_id":
            requirement_id,

        "requirement_name":
            clean(
                record.get(
                    "requirement_name"
                )
            ),

        "current_rating":
            clean(
                record.get(
                    "final_rating"
                )
            ),

        "current_score":
            final_score,

        "gap_category":
            defaults.get(
                "gap_category",
                "",
            ),

        "gap_description":
            clean(
                record.get(
                    "remaining_gaps"
                )
            ),

        "information_needed":
            clean(
                record.get(
                    "recommended_action"
                )
            ),

        "likely_source":
            defaults.get(
                "likely_source",
                "",
            ),

        "recommended_action":
            clean(
                record.get(
                    "recommended_action"
                )
            ),

        "owner":
            defaults.get(
                "owner",
                "",
            ),

        "priority":
            defaults.get(
                "priority",
                "Medium",
            ),

        "effort":
            defaults.get(
                "effort",
                "Medium",
            ),

        "status":
            "Open",

        "closure_check":
            "",

        "expected_readiness_improvement":
            expected_improvement,

        "reviewer_notes":
            "",
    }


# =========================================================
# BUILD ACTION PLAN
# =========================================================

def build_action_plan(
    reassessment_records,
):

    action_plan = []

    sequence = 1

    for record in reassessment_records:

        final_score = int(
            record.get(
                "final_score",
                0,
            )
        )

        # -------------------------------------------------
        # Only create a gap where requirement
        # is not fully covered.
        # -------------------------------------------------

        if final_score >= 4:
            continue

        gap_record = (
            build_gap_record(
                record,
                sequence,
            )
        )

        action_plan.append(
            gap_record
        )

        sequence += 1

    return action_plan


# =========================================================
# SAVE CSV
# =========================================================

def save_csv(
    records,
    path: Path,
):

    if not records:
        return

    fieldnames = [
        "Gap ID",
        "Requirement ID",
        "Requirement Name",
        "Current Rating",
        "Current Score",
        "Gap Category",
        "Gap Description",
        "Information Needed",
        "Likely Source",
        "Recommended Action",
        "Owner",
        "Priority",
        "Effort",
        "Status",
        "Closure Check",
        "Expected Readiness Improvement",
        "Reviewer Notes",
    ]

    rows = []

    for record in records:

        rows.append(
            {
                "Gap ID":
                    record[
                        "gap_id"
                    ],

                "Requirement ID":
                    record[
                        "requirement_id"
                    ],

                "Requirement Name":
                    record[
                        "requirement_name"
                    ],

                "Current Rating":
                    record[
                        "current_rating"
                    ],

                "Current Score":
                    record[
                        "current_score"
                    ],

                "Gap Category":
                    record[
                        "gap_category"
                    ],

                "Gap Description":
                    record[
                        "gap_description"
                    ],

                "Information Needed":
                    record[
                        "information_needed"
                    ],

                "Likely Source":
                    record[
                        "likely_source"
                    ],

                "Recommended Action":
                    record[
                        "recommended_action"
                    ],

                "Owner":
                    record[
                        "owner"
                    ],

                "Priority":
                    record[
                        "priority"
                    ],

                "Effort":
                    record[
                        "effort"
                    ],

                "Status":
                    record[
                        "status"
                    ],

                "Closure Check":
                    record[
                        "closure_check"
                    ],

                "Expected Readiness Improvement":
                    record[
                        "expected_readiness_improvement"
                    ],

                "Reviewer Notes":
                    record[
                        "reviewer_notes"
                    ],
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


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 80)
    print(
        "TJX ISSB GAP ACTION PLAN"
    )
    print("=" * 80)

    reassessment = (
        load_json(
            INPUT_FILE
        )
    )

    print(
        f"Requirements loaded: "
        f"{len(reassessment)}"
    )

    action_plan = (
        build_action_plan(
            reassessment
        )
    )

    save_json(
        action_plan,
        OUTPUT_JSON,
    )

    save_csv(
        action_plan,
        OUTPUT_CSV,
    )

    print()
    print(
        f"Open gaps created: "
        f"{len(action_plan)}"
    )

    print()
    print(
        "Gap Action Plan:"
    )

    for record in action_plan:

        print()
        print(
            f"{record['gap_id']} | "
            f"{record['requirement_id']}"
        )

        print(
            f"  Rating: "
            f"{record['current_rating']}"
        )

        print(
            f"  Priority: "
            f"{record['priority']}"
        )

        print(
            f"  Effort: "
            f"{record['effort']}"
        )

        print(
            f"  Owner: "
            f"{record['owner']}"
        )

        print(
            f"  Gap: "
            f"{record['gap_description']}"
        )

    print()
    print("=" * 80)

    print(
        "JSON saved to:"
    )

    print(
        OUTPUT_JSON
    )

    print()
    print(
        "CSV saved to:"
    )

    print(
        OUTPUT_CSV
    )

    print()
    print("=" * 80)
    print(
        "NEXT STEP"
    )
    print("=" * 80)

    print(
        "Review owner, priority and effort "
        "fields before loading this action "
        "plan into the reporting workbook."
    )

    print(
        "After review, update Requirement "
        "Summary and Readiness Dashboard."
    )

    print("=" * 80)


if __name__ == "__main__":
    main()