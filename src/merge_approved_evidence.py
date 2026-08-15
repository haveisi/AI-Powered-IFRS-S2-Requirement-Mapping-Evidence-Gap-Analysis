import json
from collections import Counter, defaultdict
from pathlib import Path


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EVIDENCE_DIR = (
    PROJECT_ROOT
    / "05_Evidence_Register"
)

CDP_FILE = (
    EVIDENCE_DIR
    / "TJX_CDP_approved_evidence.json"
)

GCR_FILE = (
    EVIDENCE_DIR
    / "reviewed_outputs"
    / "TJX_approved_evidence.json"
)

OUTPUT_FILE = (
    EVIDENCE_DIR
    / "TJX_combined_approved_evidence.json"
)

SUMMARY_FILE = (
    EVIDENCE_DIR
    / "TJX_combined_evidence_summary.json"
)


# =========================================================
# HELPERS
# =========================================================

def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def get_first(record, fields, default=""):
    for field in fields:
        if field in record:
            value = record.get(field)
            if value not in (None, ""):
                return value
    return default


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
# FLATTEN OLD GCR JSON
# =========================================================

def flatten_possible_evidence_json(data):

    if isinstance(data, list):
        return [
            item
            for item in data
            if isinstance(item, dict)
        ]

    if isinstance(data, dict):

        possible_keys = [
            "approved",
            "approved_evidence",
            "evidence",
            "evidence_items",
            "records",
            "data",
        ]

        for key in possible_keys:
            value = data.get(key)

            if isinstance(value, list):
                return [
                    item
                    for item in value
                    if isinstance(item, dict)
                ]

    return []


# =========================================================
# NORMALIZE CDP
# =========================================================

def normalize_cdp_record(
    record: dict,
    sequence: int,
):

    evidence_id = clean(
        get_first(
            record,
            [
                "evidence_id",
                "Evidence ID",
            ],
        )
    )

    if not evidence_id:
        evidence_id = (
            f"CDP-FINAL-{sequence:03d}"
        )

    return {

        "evidence_id":
            evidence_id,

        "evidence_source":
            "CDP",

        "requirement_id":
            clean(
                get_first(
                    record,
                    [
                        "requirement_id",
                        "Requirement ID",
                    ],
                )
            ),

        "requirement_name":
            clean(
                get_first(
                    record,
                    [
                        "requirement_name",
                        "Requirement Name",
                    ],
                )
            ),

        "source_document":
            clean(
                get_first(
                    record,
                    [
                        "source_document",
                        "Source Document",
                    ],
                    "TJX_2025_CDP_Climate_Response.pdf",
                )
            ),

        "pdf_page":
            get_first(
                record,
                [
                    "pdf_page",
                    "PDF Page",
                    "page_number",
                ],
            ),

        "evidence_type":
            clean(
                get_first(
                    record,
                    [
                        "evidence_type",
                        "Evidence Type",
                    ],
                )
            ),

        "coverage_strength":
            clean(
                get_first(
                    record,
                    [
                        "human_coverage_assessment",
                        "coverage_strength",
                        "AI Coverage Strength",
                    ],
                )
            ),

        "final_evidence_claim":
            clean(
                get_first(
                    record,
                    [
                        "final_evidence_claim",
                        "evidence_claim",
                        "Evidence Claim",
                    ],
                )
            ),

        "final_exact_quote":
            clean(
                get_first(
                    record,
                    [
                        "final_exact_quote",
                        "exact_quote",
                        "Exact Quote",
                    ],
                )
            ),

        "metric_name":
            clean(
                get_first(
                    record,
                    [
                        "metric_name",
                        "Metric Name",
                    ],
                )
            ),

        "metric_value":
            get_first(
                record,
                [
                    "final_metric_value",
                    "metric_value",
                    "Metric Value",
                ],
            ),

        "metric_unit":
            clean(
                get_first(
                    record,
                    [
                        "metric_unit",
                        "Metric Unit",
                    ],
                )
            ),

        "reporting_period":
            get_first(
                record,
                [
                    "reporting_period",
                    "Reporting Period",
                ],
            ),

        "baseline_year":
            get_first(
                record,
                [
                    "baseline_year",
                    "Baseline Year",
                ],
            ),

        "target_year":
            get_first(
                record,
                [
                    "target_year",
                    "Target Year",
                ],
            ),

        "human_decision":
            clean(
                get_first(
                    record,
                    [
                        "human_decision",
                        "Human Decision",
                    ],
                    "Approve",
                )
            ),

        "human_reviewer_notes":
            clean(
                get_first(
                    record,
                    [
                        "human_reviewer_notes",
                        "Human Reviewer Notes",
                    ],
                )
            ),

        "quote_validation":
            clean(
                get_first(
                    record,
                    [
                        "quote_validation",
                        "Quote Validation",
                    ],
                )
            ),

        "original_record":
            record,
    }


# =========================================================
# NORMALIZE GCR
# =========================================================

def normalize_gcr_record(
    record: dict,
    sequence: int,
):

    original_id = clean(
        get_first(
            record,
            [
                "Evidence ID",
                "evidence_id",
                "id",
            ],
        )
    )

    source_json = clean(
        record.get(
            "Source JSON File"
        )
    )

    if original_id:
        evidence_id = (
            original_id
            if original_id.startswith("GCR-")
            else f"GCR-{original_id}"
        )

    elif source_json:
        evidence_id = (
            f"GCR-"
            f"{source_json.replace('.json', '')}"
            f"-{sequence:03d}"
        )

    else:
        evidence_id = (
            f"GCR-FINAL-{sequence:03d}"
        )

    requirement_id = clean(
        get_first(
            record,
            [
                "Requirement ID",
                "requirement_id",
                "Potential Disclosure Requirement",
            ],
        )
    )

    if requirement_id.lower() in {
        "none",
        "null",
        "n/a",
        "na",
    }:
        requirement_id = ""

    quote_validation = clean(
        get_first(
            record,
            [
                "Quote Validation",
                "quote_validation",
            ],
        )
    )

    if quote_validation.lower() == "passed":
        quote_validation = "PASS"

    elif quote_validation.lower() == "failed":
        quote_validation = "FAIL"

    return {

        "evidence_id":
            evidence_id,

        "original_evidence_id":
            original_id,

        "evidence_source":
            "GCR",

        "requirement_id":
            requirement_id,

        "requirement_name":
            "",

        "source_document":
            "TJX_2025_Global_Corporate_Responsibility_Report.pdf",

        "source_json_file":
            source_json,

        "pdf_page":
            get_first(
                record,
                [
                    "PDF Page",
                    "Page",
                    "page",
                    "page_number",
                ],
            ),

        "evidence_type":
            clean(
                get_first(
                    record,
                    [
                        "Evidence Type",
                        "evidence_type",
                    ],
                )
            ),

        "coverage_strength":
            "",

        "final_evidence_claim":
            clean(
                get_first(
                    record,
                    [
                        "Final Claim",
                        "final_evidence_claim",
                        "Corrected Claim",
                        "Evidence Claim",
                        "claim",
                    ],
                )
            ),

        "final_exact_quote":
            clean(
                get_first(
                    record,
                    [
                        "Exact Quote",
                        "final_exact_quote",
                        "exact_quote",
                        "quote",
                    ],
                )
            ),

        "metric_name":
            clean(
                get_first(
                    record,
                    [
                        "Metric Name",
                        "metric_name",
                    ],
                )
            ),

        "metric_value":
            get_first(
                record,
                [
                    "Corrected Metric Value",
                    "Metric Value",
                    "metric_value",
                ],
            ),

        "metric_unit":
            clean(
                get_first(
                    record,
                    [
                        "Metric Unit",
                        "metric_unit",
                    ],
                )
            ),

        "reporting_period":
            get_first(
                record,
                [
                    "Reporting Period",
                    "reporting_period",
                ],
            ),

        "geographic_scope":
            clean(
                get_first(
                    record,
                    [
                        "Geographic Scope",
                        "geographic_scope",
                    ],
                )
            ),

        "human_decision":
            clean(
                get_first(
                    record,
                    [
                        "Human Review Status",
                        "Human Decision",
                        "human_decision",
                    ],
                    "Approved",
                )
            ),

        "human_reviewer_notes":
            clean(
                get_first(
                    record,
                    [
                        "Reviewer Comment",
                        "Human Reviewer Notes",
                    ],
                )
            ),

        "quote_validation":
            quote_validation,

        "framework_relevance":
            clean(
                record.get(
                    "Framework Relevance"
                )
            ),

        "potential_disclosure_requirement":
            clean(
                record.get(
                    "Potential Disclosure Requirement"
                )
            ),

        "duplicate_evidence":
            clean(
                record.get(
                    "Duplicate Evidence"
                )
            ),

        "ai_confidence":
            clean(
                record.get(
                    "AI Confidence"
                )
            ),

        "final_validation_status":
            clean(
                record.get(
                    "Final Validation Status"
                )
            ),

        "original_record":
            record,
    }


# =========================================================
# FILTER GCR ACCEPTED
# =========================================================

def gcr_record_is_accepted(
    record: dict,
):

    decision = clean(
        get_first(
            record,
            [
                "Human Review Status",
                "Human Decision",
                "human_decision",
                "status",
            ],
        )
    ).lower()

    if decision in {
        "reject",
        "rejected",
    }:
        return False

    duplicate = clean(
        record.get(
            "Duplicate Evidence"
        )
    ).lower()

    if duplicate == "yes":
        return False

    return True


# =========================================================
# QA
# =========================================================

def find_duplicate_ids(records):

    ids = [
        clean(
            record.get(
                "evidence_id"
            )
        )
        for record in records
    ]

    counts = Counter(ids)

    return [
        evidence_id
        for evidence_id, count
        in counts.items()
        if evidence_id
        and count > 1
    ]


def build_qa_summary(records):

    blank_claims = []
    blank_quotes = []
    unmapped = []

    for record in records:

        evidence_id = clean(
            record.get(
                "evidence_id"
            )
        )

        if not clean(
            record.get(
                "final_evidence_claim"
            )
        ):
            blank_claims.append(
                evidence_id
            )

        if not clean(
            record.get(
                "final_exact_quote"
            )
        ):
            blank_quotes.append(
                evidence_id
            )

        if not clean(
            record.get(
                "requirement_id"
            )
        ):
            unmapped.append(
                evidence_id
            )

    return {
        "blank_claim_count":
            len(blank_claims),

        "blank_claim_evidence_ids":
            blank_claims,

        "blank_quote_count":
            len(blank_quotes),

        "blank_quote_evidence_ids":
            blank_quotes,

        "unmapped_requirement_count":
            len(unmapped),

        "unmapped_requirement_evidence_ids":
            unmapped,
    }


# =========================================================
# REQUIREMENT SUMMARY
# =========================================================

def build_requirement_summary(records):

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
            ][strength] += 1

    return dict(summary)


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 80)
    print(
        "TJX COMBINED APPROVED EVIDENCE"
    )
    print("=" * 80)

    print()
    print("Checking source files...")

    print()
    print("CDP file:")
    print(CDP_FILE)
    print(
        f"Exists: {CDP_FILE.exists()}"
    )

    print()
    print("GCR file:")
    print(GCR_FILE)
    print(
        f"Exists: {GCR_FILE.exists()}"
    )

    if not CDP_FILE.exists():
        raise FileNotFoundError(
            f"CDP file not found:\n"
            f"{CDP_FILE}"
        )

    if not GCR_FILE.exists():
        raise FileNotFoundError(
            f"GCR file not found:\n"
            f"{GCR_FILE}"
        )

    # -----------------------------------------------------
    # LOAD CDP
    # -----------------------------------------------------

    print()
    print(
        "Loading finalized CDP evidence..."
    )

    cdp_raw = load_json(
        CDP_FILE
    )

    print(
        f"CDP approved records loaded: "
        f"{len(cdp_raw)}"
    )

    # -----------------------------------------------------
    # LOAD GCR
    # -----------------------------------------------------

    print()
    print(
        "Loading finalized GCR evidence..."
    )

    gcr_raw_data = load_json(
        GCR_FILE
    )

    gcr_raw = (
        flatten_possible_evidence_json(
            gcr_raw_data
        )
    )

    print(
        f"GCR records discovered: "
        f"{len(gcr_raw)}"
    )

    gcr_accepted = [
        record
        for record in gcr_raw
        if gcr_record_is_accepted(
            record
        )
    ]

    print(
        f"GCR accepted records retained: "
        f"{len(gcr_accepted)}"
    )

    # -----------------------------------------------------
    # NORMALIZE
    # -----------------------------------------------------

    normalized_cdp = [
        normalize_cdp_record(
            record,
            sequence,
        )
        for sequence, record
        in enumerate(
            cdp_raw,
            start=1,
        )
    ]

    normalized_gcr = [
        normalize_gcr_record(
            record,
            sequence,
        )
        for sequence, record
        in enumerate(
            gcr_accepted,
            start=1,
        )
    ]

    print()
    print(
        f"Normalized CDP records: "
        f"{len(normalized_cdp)}"
    )

    print(
        f"Normalized GCR records: "
        f"{len(normalized_gcr)}"
    )

    # -----------------------------------------------------
    # MERGE
    # -----------------------------------------------------

    combined = (
        normalized_gcr
        + normalized_cdp
    )

    print(
        f"Combined records before QA: "
        f"{len(combined)}"
    )

    duplicate_ids = (
        find_duplicate_ids(
            combined
        )
    )

    if duplicate_ids:

        print()
        print(
            "MERGE STOPPED: "
            "duplicate evidence IDs."
        )

        for evidence_id in duplicate_ids:
            print(
                f"- {evidence_id}"
            )

        return

    qa_summary = (
        build_qa_summary(
            combined
        )
    )

    requirement_summary = (
        build_requirement_summary(
            combined
        )
    )

    # -----------------------------------------------------
    # SORT
    # -----------------------------------------------------

    combined.sort(
        key=lambda record: (
            clean(
                record.get(
                    "requirement_id"
                )
            ),
            clean(
                record.get(
                    "evidence_source"
                )
            ),
            clean(
                record.get(
                    "evidence_id"
                )
            ),
        )
    )

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    summary = {

        "merge_status":
            "COMPLETE",

        "total_combined_evidence":
            len(combined),

        "gcr_evidence_count":
            len(normalized_gcr),

        "cdp_evidence_count":
            len(normalized_cdp),

        "qa_summary":
            qa_summary,

        "requirement_summary":
            requirement_summary,
    }

    save_json(
        combined,
        OUTPUT_FILE,
    )

    save_json(
        summary,
        SUMMARY_FILE,
    )

    # -----------------------------------------------------
    # REPORT
    # -----------------------------------------------------

    print()
    print("=" * 80)
    print("MERGE COMPLETE")
    print("=" * 80)

    print(
        f"GCR evidence: "
        f"{len(normalized_gcr)}"
    )

    print(
        f"CDP evidence: "
        f"{len(normalized_cdp)}"
    )

    print(
        f"Total combined evidence: "
        f"{len(combined)}"
    )

    print()
    print("QA:")

    print(
        f"  Blank claims: "
        f"{qa_summary['blank_claim_count']}"
    )

    print(
        f"  Blank quotes: "
        f"{qa_summary['blank_quote_count']}"
    )

    print(
        f"  Evidence without requirement ID: "
        f"{qa_summary['unmapped_requirement_count']}"
    )

    print()
    print(
        "Evidence mapped by requirement:"
    )

    for requirement_id, values in (
        requirement_summary.items()
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
        "Combined evidence saved to:"
    )
    print(
        OUTPUT_FILE
    )

    print()
    print(
        "Combined summary saved to:"
    )
    print(
        SUMMARY_FILE
    )

    print()
    print("=" * 80)
    print("NEXT CONTROL")
    print("=" * 80)

    print(
        "GCR evidence should now have "
        "claims and quotes populated."
    )

    print(
        "Unmapped GCR requirement IDs "
        "are expected until the next "
        "ISSB mapping step."
    )

    print("=" * 80)


if __name__ == "__main__":
    main()