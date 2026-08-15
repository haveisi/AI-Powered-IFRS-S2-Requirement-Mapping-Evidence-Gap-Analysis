import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "TJX_CDP_human_review_ready.csv"
)

APPROVED_JSON = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "TJX_CDP_approved_evidence.json"
)

REJECTED_JSON = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "TJX_CDP_rejected_evidence.json"
)

DUPLICATE_JSON = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "TJX_CDP_duplicate_evidence.json"
)

SUMMARY_JSON = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "TJX_CDP_human_review_summary.json"
)

APPROVED_CSV = (
    PROJECT_ROOT
    / "05_Evidence_Register"
    / "TJX_CDP_approved_evidence.csv"
)


# =========================================================
# ALLOWED HUMAN DECISIONS
# =========================================================

ALLOWED_DECISIONS = {
    "Approve",
    "Correct",
    "Reject",
    "Duplicate",
}


# =========================================================
# LOAD REVIEW CSV
# =========================================================

def load_review_csv(path: Path) -> list[dict]:

    if not path.exists():
        raise FileNotFoundError(
            f"Human review file not found:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        rows = list(reader)

    return rows


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_value(value):

    if value is None:
        return ""

    return str(value).strip()


# =========================================================
# VALIDATE HUMAN DECISIONS
# =========================================================

def validate_human_decisions(
    rows: list[dict],
) -> list[str]:

    errors = []

    for row_number, row in enumerate(
        rows,
        start=2,
    ):

        evidence_id = clean_value(
            row.get("Evidence ID")
        )

        decision = clean_value(
            row.get("Human Decision")
        )

        if not decision:

            errors.append(
                f"Row {row_number} "
                f"({evidence_id}): "
                f"Human Decision is blank."
            )

            continue

        if decision not in ALLOWED_DECISIONS:

            errors.append(
                f"Row {row_number} "
                f"({evidence_id}): "
                f"Invalid Human Decision "
                f"'{decision}'."
            )

    return errors


# =========================================================
# VALIDATE CORRECTED ROWS
# =========================================================

def validate_corrected_rows(
    rows: list[dict],
) -> list[str]:

    warnings = []

    correction_fields = [
        "Corrected Claim",
        "Corrected Quote",
        "Corrected Metric Value",
    ]

    for row_number, row in enumerate(
        rows,
        start=2,
    ):

        decision = clean_value(
            row.get("Human Decision")
        )

        if decision != "Correct":
            continue

        has_correction = any(
            clean_value(
                row.get(field)
            )
            for field in correction_fields
        )

        if not has_correction:

            warnings.append(
                f"Row {row_number} "
                f"({row.get('Evidence ID')}): "
                f"Decision is Correct but no "
                f"corrected field is populated."
            )

    return warnings


# =========================================================
# APPLY HUMAN CORRECTIONS
# =========================================================

def build_final_evidence(
    row: dict,
) -> dict:

    decision = clean_value(
        row.get("Human Decision")
    )

    original_claim = clean_value(
        row.get("Evidence Claim")
    )

    original_quote = clean_value(
        row.get("Exact Quote")
    )

    original_metric_value = clean_value(
        row.get("Metric Value")
    )

    corrected_claim = clean_value(
        row.get("Corrected Claim")
    )

    corrected_quote = clean_value(
        row.get("Corrected Quote")
    )

    corrected_metric_value = clean_value(
        row.get("Corrected Metric Value")
    )

    # -----------------------------------------------------
    # If human chose Correct, use corrected fields where
    # populated; otherwise retain original values.
    # -----------------------------------------------------

    if decision == "Correct":

        final_claim = (
            corrected_claim
            if corrected_claim
            else original_claim
        )

        final_quote = (
            corrected_quote
            if corrected_quote
            else original_quote
        )

        final_metric_value = (
            corrected_metric_value
            if corrected_metric_value
            else original_metric_value
        )

    else:

        final_claim = original_claim
        final_quote = original_quote
        final_metric_value = original_metric_value

    final_record = {

        "evidence_id":
            clean_value(
                row.get("Evidence ID")
            ),

        "requirement_id":
            clean_value(
                row.get("Requirement ID")
            ),

        "requirement_name":
            clean_value(
                row.get("Requirement Name")
            ),

        "source_document":
            clean_value(
                row.get("Source Document")
            ),

        "pdf_page":
            clean_value(
                row.get("PDF Page")
            ),

        "evidence_type":
            clean_value(
                row.get("Evidence Type")
            ),

        "relevance":
            clean_value(
                row.get("Relevance")
            ),

        # ---------------------------------------------
        # ORIGINAL AI FIELDS
        # ---------------------------------------------

        "ai_coverage_strength":
            clean_value(
                row.get(
                    "AI Coverage Strength"
                )
            ),

        "original_evidence_claim":
            original_claim,

        "original_exact_quote":
            original_quote,

        "original_metric_value":
            original_metric_value,

        # ---------------------------------------------
        # FINAL HUMAN-CONTROLLED FIELDS
        # ---------------------------------------------

        "final_evidence_claim":
            final_claim,

        "final_exact_quote":
            final_quote,

        "metric_name":
            clean_value(
                row.get("Metric Name")
            ),

        "final_metric_value":
            final_metric_value,

        "metric_unit":
            clean_value(
                row.get("Metric Unit")
            ),

        "reporting_period":
            clean_value(
                row.get("Reporting Period")
            ),

        "baseline_year":
            clean_value(
                row.get("Baseline Year")
            ),

        "target_year":
            clean_value(
                row.get("Target Year")
            ),

        "missing_elements":
            clean_value(
                row.get("Missing Elements")
            ),

        # ---------------------------------------------
        # TECHNICAL CONTROLS
        # ---------------------------------------------

        "quote_validation":
            clean_value(
                row.get("Quote Validation")
            ),

        "quote_repair_status":
            clean_value(
                row.get(
                    "Quote Repair Status"
                )
            ),

        "page_validation":
            clean_value(
                row.get("Page Validation")
            ),

        "requirement_id_validation":
            clean_value(
                row.get(
                    "Requirement ID Validation"
                )
            ),

        "technical_review_status":
            clean_value(
                row.get(
                    "Technical Review Status"
                )
            ),

        # ---------------------------------------------
        # HUMAN REVIEW
        # ---------------------------------------------

        "human_decision":
            decision,

        "human_coverage_assessment":
            clean_value(
                row.get(
                    "Human Coverage Assessment"
                )
            ),

        "human_reviewer_notes":
            clean_value(
                row.get(
                    "Human Reviewer Notes"
                )
            ),

        "requirement_level_notes":
            clean_value(
                row.get(
                    "Requirement-Level Notes"
                )
            ),

        # ---------------------------------------------
        # AUDIT FLAG
        # ---------------------------------------------

        "human_correction_applied":
            decision == "Correct",
    }

    return final_record


# =========================================================
# SPLIT BY HUMAN DECISION
# =========================================================

def classify_rows(
    rows: list[dict],
):

    approved = []
    rejected = []
    duplicates = []

    for row in rows:

        decision = clean_value(
            row.get("Human Decision")
        )

        final_record = build_final_evidence(
            row
        )

        if decision in {
            "Approve",
            "Correct",
        }:

            approved.append(
                final_record
            )

        elif decision == "Reject":

            rejected.append(
                final_record
            )

        elif decision == "Duplicate":

            duplicates.append(
                final_record
            )

    return (
        approved,
        rejected,
        duplicates,
    )


# =========================================================
# FINAL QA ON APPROVED EVIDENCE
# =========================================================

def validate_final_approved(
    approved: list[dict],
) -> list[str]:

    warnings = []

    for record in approved:

        evidence_id = record[
            "evidence_id"
        ]

        if (
            record["quote_validation"]
            != "PASS"
        ):

            warnings.append(
                f"{evidence_id}: "
                f"approved evidence does not "
                f"have Quote Validation PASS."
            )

        if (
            record["page_validation"]
            != "PASS"
        ):

            warnings.append(
                f"{evidence_id}: "
                f"approved evidence does not "
                f"have Page Validation PASS."
            )

        if (
            record[
                "requirement_id_validation"
            ]
            != "PASS"
        ):

            warnings.append(
                f"{evidence_id}: "
                f"approved evidence does not "
                f"have Requirement ID "
                f"Validation PASS."
            )

        if not record[
            "final_exact_quote"
        ]:

            warnings.append(
                f"{evidence_id}: "
                f"final exact quote is blank."
            )

        if not record[
            "final_evidence_claim"
        ]:

            warnings.append(
                f"{evidence_id}: "
                f"final evidence claim is blank."
            )

    return warnings


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
# SAVE APPROVED CSV
# =========================================================

def save_approved_csv(
    rows: list[dict],
    path: Path,
):

    if not rows:
        return

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = list(
        rows[0].keys()
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
# REQUIREMENT SUMMARY
# =========================================================

def build_requirement_summary(
    approved,
    rejected,
    duplicates,
):

    summary = defaultdict(
        lambda: {
            "approved": 0,
            "corrected": 0,
            "rejected": 0,
            "duplicate": 0,
            "strong": 0,
            "moderate": 0,
            "weak": 0,
        }
    )

    for record in approved:

        requirement_id = record[
            "requirement_id"
        ]

        decision = record[
            "human_decision"
        ]

        if decision == "Approve":
            summary[
                requirement_id
            ]["approved"] += 1

        elif decision == "Correct":
            summary[
                requirement_id
            ]["corrected"] += 1

        strength = (
            record[
                "human_coverage_assessment"
            ]
            .strip()
            .lower()
        )

        if strength in {
            "strong",
            "moderate",
            "weak",
        }:

            summary[
                requirement_id
            ][strength] += 1

    for record in rejected:

        summary[
            record["requirement_id"]
        ]["rejected"] += 1

    for record in duplicates:

        summary[
            record["requirement_id"]
        ]["duplicate"] += 1

    return dict(summary)


# =========================================================
# BUILD REVIEW SUMMARY
# =========================================================

def build_review_summary(
    original_rows,
    approved,
    rejected,
    duplicates,
):

    decisions = Counter(
        clean_value(
            row.get("Human Decision")
        )
        for row in original_rows
    )

    corrected_count = decisions.get(
        "Correct",
        0,
    )

    approved_without_correction = (
        decisions.get(
            "Approve",
            0,
        )
    )

    rejected_count = decisions.get(
        "Reject",
        0,
    )

    duplicate_count = decisions.get(
        "Duplicate",
        0,
    )

    total_reviewed = len(
        original_rows
    )

    accepted_total = (
        approved_without_correction
        + corrected_count
    )

    acceptance_rate = (
        accepted_total / total_reviewed
        if total_reviewed
        else 0
    )

    clean_approval_rate = (
        approved_without_correction
        / total_reviewed
        if total_reviewed
        else 0
    )

    correction_rate = (
        corrected_count
        / total_reviewed
        if total_reviewed
        else 0
    )

    rejection_rate = (
        rejected_count
        / total_reviewed
        if total_reviewed
        else 0
    )

    duplicate_rate = (
        duplicate_count
        / total_reviewed
        if total_reviewed
        else 0
    )

    return {

        "total_reviewed":
            total_reviewed,

        "approved_without_correction":
            approved_without_correction,

        "corrected":
            corrected_count,

        "rejected":
            rejected_count,

        "duplicate":
            duplicate_count,

        "accepted_final_evidence":
            len(approved),

        "acceptance_rate":
            round(
                acceptance_rate,
                4,
            ),

        "clean_approval_rate":
            round(
                clean_approval_rate,
                4,
            ),

        "correction_rate":
            round(
                correction_rate,
                4,
            ),

        "rejection_rate":
            round(
                rejection_rate,
                4,
            ),

        "duplicate_rate":
            round(
                duplicate_rate,
                4,
            ),

        "requirement_summary":
            build_requirement_summary(
                approved,
                rejected,
                duplicates,
            ),
    }


# =========================================================
# PRINT SUMMARY
# =========================================================

def print_summary(
    summary,
):

    print()
    print("=" * 80)
    print("TJX CDP HUMAN REVIEW FINALIZATION")
    print("=" * 80)

    print(
        f"Total reviewed: "
        f"{summary['total_reviewed']}"
    )

    print(
        f"Approved without correction: "
        f"{summary['approved_without_correction']}"
    )

    print(
        f"Corrected and accepted: "
        f"{summary['corrected']}"
    )

    print(
        f"Rejected: "
        f"{summary['rejected']}"
    )

    print(
        f"Duplicate: "
        f"{summary['duplicate']}"
    )

    print(
        f"Final accepted evidence: "
        f"{summary['accepted_final_evidence']}"
    )

    print()
    print(
        f"Human acceptance rate: "
        f"{summary['acceptance_rate']:.1%}"
    )

    print(
        f"Clean approval rate: "
        f"{summary['clean_approval_rate']:.1%}"
    )

    print(
        f"Correction rate: "
        f"{summary['correction_rate']:.1%}"
    )

    print(
        f"Rejection rate: "
        f"{summary['rejection_rate']:.1%}"
    )

    print(
        f"Duplicate rate: "
        f"{summary['duplicate_rate']:.1%}"
    )

    print()

    print(
        "Accepted evidence by requirement:"
    )

    for requirement_id, values in (
        summary[
            "requirement_summary"
        ].items()
    ):

        accepted = (
            values["approved"]
            + values["corrected"]
        )

        print(
            f"  {requirement_id}: "
            f"{accepted} accepted"
            f" | "
            f"{values['corrected']} corrected"
            f" | "
            f"{values['rejected']} rejected"
            f" | "
            f"{values['duplicate']} duplicate"
        )

    print("=" * 80)


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print(
        "Loading completed CDP human review..."
    )

    rows = load_review_csv(
        INPUT_FILE
    )

    print(
        f"Rows loaded: "
        f"{len(rows)}"
    )

    # -----------------------------------------------------
    # CHECK 1 — decisions complete
    # -----------------------------------------------------

    decision_errors = (
        validate_human_decisions(
            rows
        )
    )

    if decision_errors:

        print()
        print("=" * 80)
        print(
            "FINALIZATION STOPPED"
        )
        print("=" * 80)

        print(
            "The following human-review "
            "decisions must be fixed:"
        )

        for error in decision_errors:

            print(
                f"- {error}"
            )

        print()
        print(
            "Complete the review file and "
            "run this script again."
        )

        return

    # -----------------------------------------------------
    # CHECK 2 — corrected rows
    # -----------------------------------------------------

    correction_warnings = (
        validate_corrected_rows(
            rows
        )
    )

    if correction_warnings:

        print()
        print(
            "CORRECTION WARNINGS:"
        )

        for warning in (
            correction_warnings
        ):

            print(
                f"- {warning}"
            )

        print()

        print(
            "These warnings do not stop "
            "processing, but should be reviewed."
        )

    # -----------------------------------------------------
    # SPLIT HUMAN DECISIONS
    # -----------------------------------------------------

    approved, rejected, duplicates = (
        classify_rows(
            rows
        )
    )

    # -----------------------------------------------------
    # FINAL QA
    # -----------------------------------------------------

    qa_warnings = (
        validate_final_approved(
            approved
        )
    )

    if qa_warnings:

        print()
        print(
            "FINAL APPROVED-EVIDENCE "
            "QA WARNINGS:"
        )

        for warning in qa_warnings:

            print(
                f"- {warning}"
            )

    # -----------------------------------------------------
    # BUILD SUMMARY
    # -----------------------------------------------------

    summary = build_review_summary(
        rows,
        approved,
        rejected,
        duplicates,
    )

    # -----------------------------------------------------
    # SAVE OUTPUTS
    # -----------------------------------------------------

    save_json(
        approved,
        APPROVED_JSON,
    )

    save_json(
        rejected,
        REJECTED_JSON,
    )

    save_json(
        duplicates,
        DUPLICATE_JSON,
    )

    save_json(
        summary,
        SUMMARY_JSON,
    )

    save_approved_csv(
        approved,
        APPROVED_CSV,
    )

    # -----------------------------------------------------
    # REPORT
    # -----------------------------------------------------

    print_summary(
        summary
    )

    print()
    print(
        "Approved evidence JSON:"
    )

    print(
        APPROVED_JSON
    )

    print()
    print(
        "Approved evidence CSV:"
    )

    print(
        APPROVED_CSV
    )

    print()
    print(
        "Rejected evidence:"
    )

    print(
        REJECTED_JSON
    )

    print()
    print(
        "Duplicate evidence:"
    )

    print(
        DUPLICATE_JSON
    )

    print()
    print(
        "Human review summary:"
    )

    print(
        SUMMARY_JSON
    )

    print()
    print("=" * 80)

    print(
        "FINALIZATION COMPLETE"
    )

    print()

    print(
        "Only Approved and Corrected "
        "evidence has been included in "
        "the final approved evidence set."
    )

    print("=" * 80)


if __name__ == "__main__":
    main()