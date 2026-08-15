import csv
import json
from collections import defaultdict
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

OUTPUT_JSON = (
    EVIDENCE_DIR
    / "TJX_ISSB_requirement_reassessment_draft.json"
)

OUTPUT_CSV = (
    EVIDENCE_DIR
    / "TJX_ISSB_requirement_reassessment_review.csv"
)


# =========================================================
# PILOT REQUIREMENTS
# =========================================================

REQUIREMENTS = {

    "S2-GOV-02": {
        "name":
            "Board oversight of climate-related risks and opportunities",

        "baseline_rating":
            "Partially Covered",

        "baseline_score":
            2,

        "assessment_elements": [
            "Board or board-level committee responsibility",
            "Climate-related oversight responsibility",
            "Frequency or process of oversight",
            "Monitoring of climate targets or performance",
            "Governance linkage to strategy or risk oversight",
        ],
    },

    "S2-STR-06": {
        "name":
            "Climate resilience and scenario analysis",

        "baseline_rating":
            "Weakly Covered",

        "baseline_score":
            1,

        "assessment_elements": [
            "Use of climate scenario analysis",
            "Transition scenario",
            "Physical-risk scenario",
            "Time horizons",
            "Resilience conclusion",
            "Key assumptions or scenario parameters",
            "Quantitative financial or operational effects",
            "Enterprise-wide applicability",
        ],
    },

    "S2-MT-01": {
        "name":
            "Scope 1 greenhouse gas emissions",

        "baseline_rating":
            "Weakly Covered",

        "baseline_score":
            1,

        "assessment_elements": [
            "Gross Scope 1 emissions disclosed",
            "Reporting period identified",
            "Organizational boundary or scope explained",
            "Measurement approach or emission factors",
            "Disaggregation or supporting breakdown",
        ],
    },

    "S2-MT-02": {
        "name":
            "Scope 2 greenhouse gas emissions",

        "baseline_rating":
            "Weakly Covered",

        "baseline_score":
            1,

        "assessment_elements": [
            "Location-based Scope 2 disclosed",
            "Market-based Scope 2 disclosed",
            "Reporting period identified",
            "Measurement methodology explained",
            "Organizational boundary explained",
            "Disaggregation or supporting breakdown",
        ],
    },

    "S2-MT-04": {
        "name":
            "Climate targets",

        "baseline_rating":
            "Partially Covered",

        "baseline_score":
            2,

        "assessment_elements": [
            "Target clearly stated",
            "Target metric or objective identified",
            "Target year identified",
            "Baseline year identified where relevant",
            "Scope or boundary of target identified",
            "Progress toward target disclosed",
            "Target development methodology described",
            "Governance or monitoring of target",
            "Interim milestones or roadmap disclosed",
        ],
    },
}


# =========================================================
# ALLOWED RATINGS
# =========================================================

RATING_SCALE = {
    "Not Covered": 0,
    "Weakly Covered": 1,
    "Partially Covered": 2,
    "Mostly Covered": 3,
    "Fully Covered": 4,
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
            f"Input evidence file not found:\n"
            f"{path}"
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
# GROUP EVIDENCE BY REQUIREMENT
# =========================================================

def group_evidence_by_requirement(
    records,
):

    grouped = defaultdict(
        list
    )

    for record in records:

        requirement_id = clean(
            record.get(
                "requirement_id"
            )
        )

        if requirement_id in REQUIREMENTS:

            grouped[
                requirement_id
            ].append(
                record
            )

    return grouped


# =========================================================
# EVIDENCE SUMMARY
# =========================================================

def summarize_evidence(
    records,
):

    source_counts = defaultdict(
        int
    )

    strength_counts = defaultdict(
        int
    )

    evidence_ids = []

    claims = []

    for record in records:

        source = clean(
            record.get(
                "evidence_source"
            )
        )

        if source:
            source_counts[
                source
            ] += 1

        strength = clean(
            record.get(
                "coverage_strength"
            )
        )

        if strength:
            strength_counts[
                strength
            ] += 1

        evidence_id = clean(
            record.get(
                "evidence_id"
            )
        )

        if evidence_id:
            evidence_ids.append(
                evidence_id
            )

        claim = clean(
            record.get(
                "final_evidence_claim"
            )
        )

        if claim:
            claims.append(
                {
                    "evidence_id":
                        evidence_id,

                    "source":
                        source,

                    "claim":
                        claim,
                }
            )

    return {

        "evidence_count":
            len(records),

        "source_counts":
            dict(
                source_counts
            ),

        "strength_counts":
            dict(
                strength_counts
            ),

        "evidence_ids":
            evidence_ids,

        "claims":
            claims,
    }


# =========================================================
# KEYWORD-ASSISTED ELEMENT CHECK
#
# IMPORTANT:
# This does not produce final compliance conclusions.
# It only identifies possible evidence support for
# human reassessment.
# =========================================================

ELEMENT_KEYWORDS = {

    "Board or board-level committee responsibility":
        [
            "board",
            "board-level",
            "committee",
        ],

    "Climate-related oversight responsibility":
        [
            "climate",
            "environmental",
            "oversight",
            "responsibility",
        ],

    "Frequency or process of oversight":
        [
            "annually",
            "periodic",
            "periodically",
            "scheduled",
            "updates",
        ],

    "Monitoring of climate targets or performance":
        [
            "target",
            "progress",
            "monitor",
            "performance",
        ],

    "Governance linkage to strategy or risk oversight":
        [
            "strategy",
            "risk",
            "governance",
            "oversight",
        ],

    "Use of climate scenario analysis":
        [
            "scenario",
            "scenario analysis",
        ],

    "Transition scenario":
        [
            "1.5",
            "transition",
            "decarbonization",
        ],

    "Physical-risk scenario":
        [
            "physical",
            "3.0",
            "rcp6.0",
            "ssp3",
        ],

    "Time horizons":
        [
            "short",
            "medium",
            "long",
            "2030",
            "2050",
        ],

    "Resilience conclusion":
        [
            "resilience",
            "resilient",
            "business model",
        ],

    "Key assumptions or scenario parameters":
        [
            "rcp",
            "ssp",
            "1.5",
            "3.0",
            "scenario",
        ],

    "Quantitative financial or operational effects":
        [
            "financial",
            "cost",
            "revenue",
            "value",
            "quantitative",
        ],

    "Enterprise-wide applicability":
        [
            "global",
            "company-wide",
            "enterprise",
        ],

    "Gross Scope 1 emissions disclosed":
        [
            "gross global scope 1",
            "scope 1 emissions",
            "143258",
            "143,258",
        ],

    "Reporting period identified":
        [
            "fiscal 2025",
            "fy2025",
            "reporting year",
        ],

    "Organizational boundary or scope explained":
        [
            "global",
            "consolidated",
            "operations",
            "organizational boundary",
        ],

    "Measurement approach or emission factors":
        [
            "emission factor",
            "epa",
            "desnz",
            "ghg protocol",
        ],

    "Disaggregation or supporting breakdown":
        [
            "u.s.",
            "canada",
            "europe",
            "australia",
            "stores",
            "offices",
            "distribution centers",
        ],

    "Location-based Scope 2 disclosed":
        [
            "location-based",
            "scope 2",
            "559158",
            "559,158",
        ],

    "Market-based Scope 2 disclosed":
        [
            "market-based",
            "scope 2",
            "363202",
            "363,202",
        ],

    "Measurement methodology explained":
        [
            "ghg protocol",
            "scope 2 guidance",
            "residual",
            "location-based",
            "market-based",
        ],

    "Target clearly stated":
        [
            "target",
            "goal",
            "net zero",
            "renewable",
        ],

    "Target metric or objective identified":
        [
            "55%",
            "100%",
            "net zero",
            "emissions reduction",
        ],

    "Target year identified":
        [
            "2030",
            "2040",
        ],

    "Baseline year identified where relevant":
        [
            "2017",
            "baseline",
        ],

    "Scope or boundary of target identified":
        [
            "scope 1",
            "scope 2",
            "operations",
            "global operations",
        ],

    "Progress toward target disclosed":
        [
            "37%",
            "progress",
            "underway",
            "fiscal 2025",
        ],

    "Target development methodology described":
        [
            "sbti",
            "guidance",
            "1.5",
            "paris agreement",
        ],

    "Governance or monitoring of target":
        [
            "committee",
            "monitor",
            "progress",
            "oversight",
        ],

    "Interim milestones or roadmap disclosed":
        [
            "milestone",
            "roadmap",
            "3-5",
            "3–5",
        ],
}


# =========================================================
# FIND POSSIBLE SUPPORT FOR EACH ELEMENT
# =========================================================

def evaluate_elements(
    requirement_id,
    evidence_records,
):

    elements = REQUIREMENTS[
        requirement_id
    ][
        "assessment_elements"
    ]

    results = []

    for element in elements:

        keywords = (
            ELEMENT_KEYWORDS.get(
                element,
                [],
            )
        )

        supporting_ids = []

        for record in evidence_records:

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
                            "metric_name"
                        )
                    ),
                ]
            ).lower()

            if any(
                keyword.lower()
                in searchable_text
                for keyword in keywords
            ):

                supporting_ids.append(
                    clean(
                        record.get(
                            "evidence_id"
                        )
                    )
                )

        # ---------------------------------------------
        # This is intentionally not a final judgement.
        # ---------------------------------------------

        if supporting_ids:

            preliminary_status = (
                "Potentially Supported"
            )

        else:

            preliminary_status = (
                "No Evidence Identified"
            )

        results.append(
            {
                "element":
                    element,

                "preliminary_status":
                    preliminary_status,

                "supporting_evidence_ids":
                    supporting_ids,
            }
        )

    return results


# =========================================================
# BUILD DRAFT REASSESSMENT
# =========================================================

def build_reassessment(
    grouped_evidence,
):

    output = []

    for requirement_id, definition in (
        REQUIREMENTS.items()
    ):

        evidence_records = (
            grouped_evidence.get(
                requirement_id,
                [],
            )
        )

        evidence_summary = (
            summarize_evidence(
                evidence_records
            )
        )

        element_review = (
            evaluate_elements(
                requirement_id,
                evidence_records,
            )
        )

        output.append(
            {
                "requirement_id":
                    requirement_id,

                "requirement_name":
                    definition[
                        "name"
                    ],

                "baseline_rating":
                    definition[
                        "baseline_rating"
                    ],

                "baseline_score":
                    definition[
                        "baseline_score"
                    ],

                "evidence_summary":
                    evidence_summary,

                "element_review":
                    element_review,

                # Human-controlled fields
                "human_final_rating":
                    "",

                "human_final_score":
                    "",

                "remaining_gaps":
                    "",

                "reviewer_rationale":
                    "",

                "recommended_action":
                    "",
            }
        )

    return output


# =========================================================
# EXPORT HUMAN REVIEW CSV
# =========================================================

def export_review_csv(
    reassessment,
    path,
):

    fieldnames = [
        "Requirement ID",
        "Requirement Name",
        "Baseline Rating",
        "Baseline Score",
        "Evidence Count",
        "GCR Evidence Count",
        "CDP Evidence Count",
        "Strong Evidence Count",
        "Moderate Evidence Count",
        "Weak Evidence Count",
        "Assessment Elements",
        "Potentially Supported Elements",
        "No Evidence Identified Elements",
        "Evidence IDs",
        "Human Final Rating",
        "Human Final Score",
        "Remaining Gaps",
        "Reviewer Rationale",
        "Recommended Action",
    ]

    rows = []

    for item in reassessment:

        evidence_summary = (
            item[
                "evidence_summary"
            ]
        )

        element_review = (
            item[
                "element_review"
            ]
        )

        potentially_supported = [
            element[
                "element"
            ]
            for element in element_review
            if (
                element[
                    "preliminary_status"
                ]
                == "Potentially Supported"
            )
        ]

        no_evidence = [
            element[
                "element"
            ]
            for element in element_review
            if (
                element[
                    "preliminary_status"
                ]
                == "No Evidence Identified"
            )
        ]

        all_elements = [
            element[
                "element"
            ]
            for element in element_review
        ]

        source_counts = (
            evidence_summary[
                "source_counts"
            ]
        )

        strength_counts = (
            evidence_summary[
                "strength_counts"
            ]
        )

        rows.append(
            {
                "Requirement ID":
                    item[
                        "requirement_id"
                    ],

                "Requirement Name":
                    item[
                        "requirement_name"
                    ],

                "Baseline Rating":
                    item[
                        "baseline_rating"
                    ],

                "Baseline Score":
                    item[
                        "baseline_score"
                    ],

                "Evidence Count":
                    evidence_summary[
                        "evidence_count"
                    ],

                "GCR Evidence Count":
                    source_counts.get(
                        "GCR",
                        0,
                    ),

                "CDP Evidence Count":
                    source_counts.get(
                        "CDP",
                        0,
                    ),

                "Strong Evidence Count":
                    strength_counts.get(
                        "Strong",
                        0,
                    ),

                "Moderate Evidence Count":
                    strength_counts.get(
                        "Moderate",
                        0,
                    ),

                "Weak Evidence Count":
                    strength_counts.get(
                        "Weak",
                        0,
                    ),

                "Assessment Elements":
                    " | ".join(
                        all_elements
                    ),

                "Potentially Supported Elements":
                    " | ".join(
                        potentially_supported
                    ),

                "No Evidence Identified Elements":
                    " | ".join(
                        no_evidence
                    ),

                "Evidence IDs":
                    " | ".join(
                        evidence_summary[
                            "evidence_ids"
                        ]
                    ),

                "Human Final Rating":
                    "",

                "Human Final Score":
                    "",

                "Remaining Gaps":
                    "",

                "Reviewer Rationale":
                    "",

                "Recommended Action":
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
        "TJX ISSB REQUIREMENT-LEVEL REASSESSMENT"
    )
    print("=" * 80)

    print()
    print(
        "Loading human-approved mapped evidence..."
    )

    records = load_json(
        INPUT_FILE
    )

    print(
        f"Evidence records loaded: "
        f"{len(records)}"
    )

    # -----------------------------------------------------
    # GROUP
    # -----------------------------------------------------

    grouped = (
        group_evidence_by_requirement(
            records
        )
    )

    print()
    print(
        "Mapped evidence by requirement:"
    )

    for requirement_id in REQUIREMENTS:

        count = len(
            grouped.get(
                requirement_id,
                [],
            )
        )

        print(
            f"  {requirement_id}: "
            f"{count}"
        )

    # -----------------------------------------------------
    # BUILD DRAFT
    # -----------------------------------------------------

    reassessment = (
        build_reassessment(
            grouped
        )
    )

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    save_json(
        reassessment,
        OUTPUT_JSON,
    )

    export_review_csv(
        reassessment,
        OUTPUT_CSV,
    )

    # -----------------------------------------------------
    # REPORT
    # -----------------------------------------------------

    print()
    print("=" * 80)
    print(
        "REASSESSMENT DRAFT CREATED"
    )
    print("=" * 80)

    for item in reassessment:

        supported = sum(
            1
            for element
            in item[
                "element_review"
            ]
            if (
                element[
                    "preliminary_status"
                ]
                == "Potentially Supported"
            )
        )

        total_elements = len(
            item[
                "element_review"
            ]
        )

        print(
            f"{item['requirement_id']}: "
            f"{supported}/"
            f"{total_elements} "
            f"elements potentially supported"
        )

    print()
    print(
        "Draft JSON:"
    )

    print(
        OUTPUT_JSON
    )

    print()
    print(
        "Human reassessment review CSV:"
    )

    print(
        OUTPUT_CSV
    )

    print()
    print("=" * 80)
    print(
        "HUMAN REVIEW REQUIRED"
    )
    print("=" * 80)

    print(
        "For each requirement, review the "
        "underlying evidence and complete:"
    )

    print()
    print(
        "  Human Final Rating"
    )

    print(
        "  Human Final Score"
    )

    print(
        "  Remaining Gaps"
    )

    print(
        "  Reviewer Rationale"
    )

    print(
        "  Recommended Action"
    )

    print()
    print(
        "Allowed ratings:"
    )

    for rating, score in (
        RATING_SCALE.items()
    ):

        print(
            f"  {rating} = {score}"
        )

    print()
    print(
        "Do not convert evidence counts "
        "directly into coverage ratings."
    )

    print(
        "Coverage depends on whether the "
        "required disclosure elements are "
        "actually addressed."
    )

    print("=" * 80)


if __name__ == "__main__":
    main()