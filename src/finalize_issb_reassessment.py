import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

EVIDENCE_DIR = (
    PROJECT_ROOT
    / "05_Evidence_Register"
)

INPUT_CSV = (
    EVIDENCE_DIR
    / "TJX_ISSB_requirement_reassessment_review.csv"
)

OUTPUT_JSON = (
    EVIDENCE_DIR
    / "TJX_ISSB_requirement_reassessment_final.json"
)

SUMMARY_JSON = (
    EVIDENCE_DIR
    / "TJX_ISSB_requirement_reassessment_summary.json"
)


ALLOWED_RATINGS = {
    "Not Covered": 0,
    "Weakly Covered": 1,
    "Partially Covered": 2,
    "Mostly Covered": 3,
    "Fully Covered": 4,
}


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def load_csv(path: Path):

    if not path.exists():
        raise FileNotFoundError(
            f"Review CSV not found:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        return list(
            csv.DictReader(file)
        )


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


def validate_rows(rows):

    errors = []

    for row_number, row in enumerate(
        rows,
        start=2,
    ):

        requirement_id = clean(
            row.get(
                "Requirement ID"
            )
        )

        rating = clean(
            row.get(
                "Human Final Rating"
            )
        )

        score_text = clean(
            row.get(
                "Human Final Score"
            )
        )

        remaining_gaps = clean(
            row.get(
                "Remaining Gaps"
            )
        )

        rationale = clean(
            row.get(
                "Reviewer Rationale"
            )
        )

        action = clean(
            row.get(
                "Recommended Action"
            )
        )

        if rating not in ALLOWED_RATINGS:

            errors.append(
                f"Row {row_number} "
                f"({requirement_id}): "
                f"Invalid Human Final Rating "
                f"'{rating}'."
            )

            continue

        try:
            score = int(
                float(score_text)
            )
        except Exception:

            errors.append(
                f"Row {row_number} "
                f"({requirement_id}): "
                f"Human Final Score is invalid."
            )

            continue

        expected_score = (
            ALLOWED_RATINGS[
                rating
            ]
        )

        if score != expected_score:

            errors.append(
                f"Row {row_number} "
                f"({requirement_id}): "
                f"Rating '{rating}' requires "
                f"score {expected_score}, "
                f"not {score}."
            )

        if not remaining_gaps:

            errors.append(
                f"Row {row_number} "
                f"({requirement_id}): "
                f"Remaining Gaps is blank."
            )

        if not rationale:

            errors.append(
                f"Row {row_number} "
                f"({requirement_id}): "
                f"Reviewer Rationale is blank."
            )

        if not action:

            errors.append(
                f"Row {row_number} "
                f"({requirement_id}): "
                f"Recommended Action is blank."
            )

    return errors


def build_final_records(rows):

    final_records = []

    for row in rows:

        baseline_score = int(
            float(
                clean(
                    row.get(
                        "Baseline Score"
                    )
                )
            )
        )

        final_score = int(
            float(
                clean(
                    row.get(
                        "Human Final Score"
                    )
                )
            )
        )

        improvement = (
            final_score
            - baseline_score
        )

        final_records.append(
            {
                "requirement_id":
                    clean(
                        row.get(
                            "Requirement ID"
                        )
                    ),

                "requirement_name":
                    clean(
                        row.get(
                            "Requirement Name"
                        )
                    ),

                "baseline_rating":
                    clean(
                        row.get(
                            "Baseline Rating"
                        )
                    ),

                "baseline_score":
                    baseline_score,

                "final_rating":
                    clean(
                        row.get(
                            "Human Final Rating"
                        )
                    ),

                "final_score":
                    final_score,

                "score_improvement":
                    improvement,

                "evidence_count":
                    int(
                        float(
                            clean(
                                row.get(
                                    "Evidence Count"
                                )
                            )
                        )
                    ),

                "gcr_evidence_count":
                    int(
                        float(
                            clean(
                                row.get(
                                    "GCR Evidence Count"
                                )
                            )
                        )
                    ),

                "cdp_evidence_count":
                    int(
                        float(
                            clean(
                                row.get(
                                    "CDP Evidence Count"
                                )
                            )
                        )
                    ),

                "strong_evidence_count":
                    int(
                        float(
                            clean(
                                row.get(
                                    "Strong Evidence Count"
                                )
                            )
                        )
                    ),

                "moderate_evidence_count":
                    int(
                        float(
                            clean(
                                row.get(
                                    "Moderate Evidence Count"
                                )
                            )
                        )
                    ),

                "weak_evidence_count":
                    int(
                        float(
                            clean(
                                row.get(
                                    "Weak Evidence Count"
                                )
                            )
                        )
                    ),

                "assessment_elements":
                    clean(
                        row.get(
                            "Assessment Elements"
                        )
                    ),

                "potentially_supported_elements":
                    clean(
                        row.get(
                            "Potentially Supported Elements"
                        )
                    ),

                "no_evidence_identified_elements":
                    clean(
                        row.get(
                            "No Evidence Identified Elements"
                        )
                    ),

                "evidence_ids":
                    clean(
                        row.get(
                            "Evidence IDs"
                        )
                    ),

                "remaining_gaps":
                    clean(
                        row.get(
                            "Remaining Gaps"
                        )
                    ),

                "reviewer_rationale":
                    clean(
                        row.get(
                            "Reviewer Rationale"
                        )
                    ),

                "recommended_action":
                    clean(
                        row.get(
                            "Recommended Action"
                        )
                    ),
            }
        )

    return final_records


def build_summary(records):

    baseline_total = sum(
        record[
            "baseline_score"
        ]
        for record in records
    )

    final_total = sum(
        record[
            "final_score"
        ]
        for record in records
    )

    max_score = (
        len(records) * 4
    )

    baseline_readiness = (
        baseline_total
        / max_score
        if max_score
        else 0
    )

    final_readiness = (
        final_total
        / max_score
        if max_score
        else 0
    )

    return {
        "requirements_assessed":
            len(records),

        "maximum_possible_score":
            max_score,

        "baseline_total_score":
            baseline_total,

        "final_total_score":
            final_total,

        "baseline_pilot_readiness":
            round(
                baseline_readiness,
                4,
            ),

        "final_pilot_readiness":
            round(
                final_readiness,
                4,
            ),

        "readiness_improvement":
            round(
                final_readiness
                - baseline_readiness,
                4,
            ),

        "important_scope_note":
            (
                "This score reflects only the five "
                "selected IFRS S2 pilot requirements "
                "assessed using public TJX evidence. "
                "It is not an ISSB compliance score."
            ),

        "requirements":
            [
                {
                    "requirement_id":
                        record[
                            "requirement_id"
                        ],

                    "baseline_rating":
                        record[
                            "baseline_rating"
                        ],

                    "baseline_score":
                        record[
                            "baseline_score"
                        ],

                    "final_rating":
                        record[
                            "final_rating"
                        ],

                    "final_score":
                        record[
                            "final_score"
                        ],

                    "improvement":
                        record[
                            "score_improvement"
                        ],
                }
                for record in records
            ],
    }


def main():

    print()
    print("=" * 80)
    print(
        "TJX ISSB REQUIREMENT REASSESSMENT FINALIZATION"
    )
    print("=" * 80)

    rows = load_csv(
        INPUT_CSV
    )

    print(
        f"Requirement rows loaded: "
        f"{len(rows)}"
    )

    errors = validate_rows(
        rows
    )

    if errors:

        print()
        print("=" * 80)
        print(
            "FINALIZATION STOPPED"
        )
        print("=" * 80)

        for error in errors:
            print(
                f"- {error}"
            )

        print()
        print(
            "Fix the CSV and run again."
        )

        return

    final_records = (
        build_final_records(
            rows
        )
    )

    summary = (
        build_summary(
            final_records
        )
    )

    save_json(
        final_records,
        OUTPUT_JSON,
    )

    save_json(
        summary,
        SUMMARY_JSON,
    )

    print()
    print("=" * 80)
    print(
        "REASSESSMENT FINALIZED"
    )
    print("=" * 80)

    for record in final_records:

        print(
            f"{record['requirement_id']}: "
            f"{record['baseline_rating']} "
            f"({record['baseline_score']}) "
            f"→ "
            f"{record['final_rating']} "
            f"({record['final_score']})"
        )

    print()
    print(
        f"Baseline pilot score: "
        f"{summary['baseline_total_score']}"
        f"/"
        f"{summary['maximum_possible_score']}"
        f" = "
        f"{summary['baseline_pilot_readiness']:.1%}"
    )

    print(
        f"Final pilot score: "
        f"{summary['final_total_score']}"
        f"/"
        f"{summary['maximum_possible_score']}"
        f" = "
        f"{summary['final_pilot_readiness']:.1%}"
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "This is a five-requirement pilot "
        "readiness assessment, not an "
        "ISSB compliance percentage."
    )

    print()
    print(
        "Final reassessment:"
    )

    print(
        OUTPUT_JSON
    )

    print()
    print(
        "Summary:"
    )

    print(
        SUMMARY_JSON
    )

    print("=" * 80)


if __name__ == "__main__":
    main()