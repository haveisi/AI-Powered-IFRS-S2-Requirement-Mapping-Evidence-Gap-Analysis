import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EVIDENCE_DIR = (
    PROJECT_ROOT
    / "05_Evidence_Register"
)

MAPPING_REVIEW_FILE = (
    EVIDENCE_DIR
    / "TJX_GCR_ISSB_mapping_review.csv"
)

COMBINED_INPUT_FILE = (
    EVIDENCE_DIR
    / "TJX_combined_approved_evidence.json"
)

OUTPUT_FILE = (
    EVIDENCE_DIR
    / "TJX_combined_evidence_with_gcr_mapping.json"
)

MAPPING_SUMMARY_FILE = (
    EVIDENCE_DIR
    / "TJX_GCR_ISSB_mapping_summary.json"
)


# =========================================================
# ALLOWED VALUES
# =========================================================

ALLOWED_DECISIONS = {
    "Approve",
    "Correct",
    "Not Relevant",
}

ALLOWED_REQUIREMENTS = {
    "S2-GOV-02",
    "S2-STR-06",
    "S2-MT-01",
    "S2-MT-02",
    "S2-MT-04",
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
            f"File not found:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


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
# LOAD HUMAN MAPPING REVIEW
# =========================================================

def load_mapping_review(
    path: Path,
) -> list[dict]:

    if not path.exists():

        raise FileNotFoundError(
            f"GCR mapping review file not found:\n"
            f"{path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        return list(
            reader
        )


# =========================================================
# VALIDATE HUMAN REVIEW
# =========================================================

def validate_mapping_review(
    rows: list[dict],
) -> list[str]:

    errors = []

    for row_number, row in enumerate(
        rows,
        start=2,
    ):

        evidence_id = clean(
            row.get(
                "Evidence ID"
            )
        )

        suggested_id = clean(
            row.get(
                "Suggested Requirement ID"
            )
        )

        decision = clean(
            row.get(
                "Human Mapping Decision"
            )
        )

        final_requirement_id = clean(
            row.get(
                "Final Requirement ID"
            )
        )

        # -------------------------------------------------
        # Decision required
        # -------------------------------------------------

        if not decision:

            errors.append(
                f"Row {row_number} "
                f"({evidence_id}): "
                f"Human Mapping Decision is blank."
            )

            continue

        # -------------------------------------------------
        # Allowed decision
        # -------------------------------------------------

        if decision not in (
            ALLOWED_DECISIONS
        ):

            errors.append(
                f"Row {row_number} "
                f"({evidence_id}): "
                f"Invalid decision "
                f"'{decision}'."
            )

            continue

        # -------------------------------------------------
        # Approve requires a valid suggested ID
        # -------------------------------------------------

        if decision == "Approve":

            if not suggested_id:

                errors.append(
                    f"Row {row_number} "
                    f"({evidence_id}): "
                    f"Decision is Approve but "
                    f"Suggested Requirement ID "
                    f"is blank."
                )

            elif suggested_id not in (
                ALLOWED_REQUIREMENTS
            ):

                errors.append(
                    f"Row {row_number} "
                    f"({evidence_id}): "
                    f"Suggested Requirement ID "
                    f"'{suggested_id}' is invalid."
                )

        # -------------------------------------------------
        # Correct requires Final Requirement ID
        # -------------------------------------------------

        if decision == "Correct":

            if not final_requirement_id:

                errors.append(
                    f"Row {row_number} "
                    f"({evidence_id}): "
                    f"Decision is Correct but "
                    f"Final Requirement ID is blank."
                )

            elif final_requirement_id not in (
                ALLOWED_REQUIREMENTS
            ):

                errors.append(
                    f"Row {row_number} "
                    f"({evidence_id}): "
                    f"Final Requirement ID "
                    f"'{final_requirement_id}' "
                    f"is invalid."
                )

        # -------------------------------------------------
        # Not Relevant should not carry requirement ID
        # -------------------------------------------------

        if decision == "Not Relevant":

            if final_requirement_id:

                errors.append(
                    f"Row {row_number} "
                    f"({evidence_id}): "
                    f"Decision is Not Relevant "
                    f"but Final Requirement ID "
                    f"is populated."
                )

    return errors


# =========================================================
# BUILD FINAL MAPPING LOOKUP
# =========================================================

def build_mapping_lookup(
    rows: list[dict],
):

    mapping_lookup = {}

    for row in rows:

        evidence_id = clean(
            row.get(
                "Evidence ID"
            )
        )

        suggested_id = clean(
            row.get(
                "Suggested Requirement ID"
            )
        )

        decision = clean(
            row.get(
                "Human Mapping Decision"
            )
        )

        final_requirement_id = clean(
            row.get(
                "Final Requirement ID"
            )
        )

        notes = clean(
            row.get(
                "Human Mapping Notes"
            )
        )

        if decision == "Approve":

            mapped_requirement_id = (
                suggested_id
            )

        elif decision == "Correct":

            mapped_requirement_id = (
                final_requirement_id
            )

        elif decision == "Not Relevant":

            mapped_requirement_id = ""

        else:

            mapped_requirement_id = ""

        mapping_lookup[
            evidence_id
        ] = {
            "decision":
                decision,

            "suggested_requirement_id":
                suggested_id,

            "final_requirement_id":
                mapped_requirement_id,

            "mapping_notes":
                notes,
        }

    return mapping_lookup


# =========================================================
# APPLY GCR MAPPINGS
# =========================================================

def apply_mappings(
    combined_records: list[dict],
    mapping_lookup: dict,
):

    updated_records = []

    gcr_updated = 0
    gcr_not_relevant = 0
    gcr_missing_review = 0

    for record in combined_records:

        updated = dict(
            record
        )

        source = clean(
            record.get(
                "evidence_source"
            )
        )

        evidence_id = clean(
            record.get(
                "evidence_id"
            )
        )

        # -------------------------------------------------
        # CDP records remain unchanged
        # -------------------------------------------------

        if source != "GCR":

            updated_records.append(
                updated
            )

            continue

        # -------------------------------------------------
        # GCR mapping lookup
        # -------------------------------------------------

        mapping = mapping_lookup.get(
            evidence_id
        )

        if mapping is None:

            gcr_missing_review += 1

            updated[
                "gcr_mapping_status"
            ] = "MISSING HUMAN REVIEW"

            updated_records.append(
                updated
            )

            continue

        decision = mapping[
            "decision"
        ]

        final_requirement_id = (
            mapping[
                "final_requirement_id"
            ]
        )

        # -------------------------------------------------
        # Preserve original pre-mapping requirement
        # -------------------------------------------------

        updated[
            "original_requirement_id"
        ] = clean(
            record.get(
                "requirement_id"
            )
        )

        # -------------------------------------------------
        # Store mapping audit fields
        # -------------------------------------------------

        updated[
            "gcr_mapping_decision"
        ] = decision

        updated[
            "gcr_suggested_requirement_id"
        ] = mapping[
            "suggested_requirement_id"
        ]

        updated[
            "gcr_human_mapping_notes"
        ] = mapping[
            "mapping_notes"
        ]

        # -------------------------------------------------
        # Apply final result
        # -------------------------------------------------

        if decision in {
            "Approve",
            "Correct",
        }:

            updated[
                "requirement_id"
            ] = final_requirement_id

            updated[
                "gcr_mapping_status"
            ] = "Mapped"

            gcr_updated += 1

        elif decision == "Not Relevant":

            updated[
                "requirement_id"
            ] = ""

            updated[
                "gcr_mapping_status"
            ] = "Not Relevant to Pilot Requirements"

            gcr_not_relevant += 1

        updated_records.append(
            updated
        )

    return (
        updated_records,
        gcr_updated,
        gcr_not_relevant,
        gcr_missing_review,
    )


# =========================================================
# REQUIREMENT SUMMARY
# =========================================================

def build_requirement_summary(
    records: list[dict],
):

    summary = defaultdict(
        lambda: {
            "total_evidence": 0,
            "gcr_evidence": 0,
            "cdp_evidence": 0,
            "strong": 0,
            "moderate": 0,
            "weak": 0,
        }
    )

    for record in records:

        requirement_id = clean(
            record.get(
                "requirement_id"
            )
        )

        if not requirement_id:
            continue

        summary[
            requirement_id
        ][
            "total_evidence"
        ] += 1

        source = clean(
            record.get(
                "evidence_source"
            )
        )

        if source == "GCR":

            summary[
                requirement_id
            ][
                "gcr_evidence"
            ] += 1

        elif source == "CDP":

            summary[
                requirement_id
            ][
                "cdp_evidence"
            ] += 1

        strength = clean(
            record.get(
                "coverage_strength"
            )
        ).lower()

        if strength in {
            "strong",
            "moderate",
            "weak",
        }:

            summary[
                requirement_id
            ][
                strength
            ] += 1

    return dict(
        summary
    )


# =========================================================
# BUILD MAPPING SUMMARY
# =========================================================

def build_mapping_summary(
    review_rows,
    updated_records,
    gcr_updated,
    gcr_not_relevant,
    gcr_missing_review,
):

    decision_counts = Counter(
        clean(
            row.get(
                "Human Mapping Decision"
            )
        )
        for row in review_rows
    )

    requirement_counts = Counter()

    for record in updated_records:

        if clean(
            record.get(
                "evidence_source"
            )
        ) != "GCR":
            continue

        requirement_id = clean(
            record.get(
                "requirement_id"
            )
        )

        if requirement_id:

            requirement_counts[
                requirement_id
            ] += 1

    return {

        "total_gcr_review_rows":
            len(review_rows),

        "approved_suggested_mappings":
            decision_counts.get(
                "Approve",
                0,
            ),

        "corrected_mappings":
            decision_counts.get(
                "Correct",
                0,
            ),

        "not_relevant":
            decision_counts.get(
                "Not Relevant",
                0,
            ),

        "gcr_records_mapped":
            gcr_updated,

        "gcr_records_not_relevant":
            gcr_not_relevant,

        "gcr_records_missing_review":
            gcr_missing_review,

        "gcr_mapping_by_requirement":
            dict(
                requirement_counts
            ),

        "combined_requirement_summary":
            build_requirement_summary(
                updated_records
            ),
    }


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 80)
    print(
        "TJX GCR → ISSB HUMAN MAPPING FINALIZATION"
    )
    print("=" * 80)

    # -----------------------------------------------------
    # LOAD HUMAN REVIEW
    # -----------------------------------------------------

    print()
    print(
        "Loading GCR mapping review..."
    )

    review_rows = (
        load_mapping_review(
            MAPPING_REVIEW_FILE
        )
    )

    print(
        f"Mapping review rows loaded: "
        f"{len(review_rows)}"
    )

    # -----------------------------------------------------
    # VALIDATE HUMAN REVIEW
    # -----------------------------------------------------

    validation_errors = (
        validate_mapping_review(
            review_rows
        )
    )

    if validation_errors:

        print()
        print("=" * 80)
        print(
            "FINALIZATION STOPPED"
        )
        print("=" * 80)

        print(
            "Fix the following mapping "
            "review errors:"
        )

        for error in (
            validation_errors
        ):

            print(
                f"- {error}"
            )

        print()
        print(
            "Save the CSV and run this "
            "script again."
        )

        return

    # -----------------------------------------------------
    # LOAD COMBINED EVIDENCE
    # -----------------------------------------------------

    print()
    print(
        "Loading combined approved evidence..."
    )

    combined_records = (
        load_json(
            COMBINED_INPUT_FILE
        )
    )

    print(
        f"Combined records loaded: "
        f"{len(combined_records)}"
    )

    # -----------------------------------------------------
    # BUILD LOOKUP
    # -----------------------------------------------------

    mapping_lookup = (
        build_mapping_lookup(
            review_rows
        )
    )

    print(
        f"Human-reviewed GCR mappings: "
        f"{len(mapping_lookup)}"
    )

    # -----------------------------------------------------
    # APPLY MAPPINGS
    # -----------------------------------------------------

    (
        updated_records,
        gcr_updated,
        gcr_not_relevant,
        gcr_missing_review,
    ) = apply_mappings(
        combined_records,
        mapping_lookup,
    )

    # -----------------------------------------------------
    # SAFETY CHECK
    # -----------------------------------------------------

    if gcr_missing_review > 0:

        print()
        print("=" * 80)
        print(
            "FINALIZATION STOPPED"
        )
        print("=" * 80)

        print(
            f"{gcr_missing_review} GCR "
            f"evidence records do not have "
            f"a matching human mapping row."
        )

        print(
            "No output was finalized."
        )

        return

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    summary = (
        build_mapping_summary(
            review_rows,
            updated_records,
            gcr_updated,
            gcr_not_relevant,
            gcr_missing_review,
        )
    )

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    save_json(
        updated_records,
        OUTPUT_FILE,
    )

    save_json(
        summary,
        MAPPING_SUMMARY_FILE,
    )

    # -----------------------------------------------------
    # REPORT
    # -----------------------------------------------------

    print()
    print("=" * 80)
    print(
        "GCR ISSB MAPPING FINALIZED"
    )
    print("=" * 80)

    print(
        f"Human review rows: "
        f"{summary['total_gcr_review_rows']}"
    )

    print(
        f"Approved suggested mappings: "
        f"{summary['approved_suggested_mappings']}"
    )

    print(
        f"Corrected mappings: "
        f"{summary['corrected_mappings']}"
    )

    print(
        f"Not relevant to five pilot "
        f"requirements: "
        f"{summary['not_relevant']}"
    )

    print()
    print(
        "Final GCR mapping by requirement:"
    )

    for requirement_id, count in (
        summary[
            "gcr_mapping_by_requirement"
        ].items()
    ):

        print(
            f"  {requirement_id}: "
            f"{count}"
        )

    print()
    print(
        "Combined evidence by requirement:"
    )

    for requirement_id, values in (
        summary[
            "combined_requirement_summary"
        ].items()
    ):

        print(
            f"  {requirement_id}: "
            f"{values['total_evidence']} total"
            f" | GCR {values['gcr_evidence']}"
            f" | CDP {values['cdp_evidence']}"
            f" | Strong {values['strong']}"
            f" | Moderate {values['moderate']}"
            f" | Weak {values['weak']}"
        )

    print()
    print(
        "Final combined mapped evidence:"
    )

    print(
        OUTPUT_FILE
    )

    print()
    print(
        "Mapping summary:"
    )

    print(
        MAPPING_SUMMARY_FILE
    )

    print()
    print("=" * 80)
    print(
        "NEXT STEP"
    )
    print("=" * 80)

    print(
        "Perform requirement-level ISSB "
        "coverage reassessment using the "
        "human-approved GCR mappings plus "
        "the finalized CDP evidence."
    )

    print("=" * 80)


if __name__ == "__main__":
    main()