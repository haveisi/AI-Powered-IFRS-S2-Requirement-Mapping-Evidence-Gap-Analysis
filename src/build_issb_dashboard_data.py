import csv
import json
from collections import Counter
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EVIDENCE_DIR = (
    PROJECT_ROOT
    / "05_Evidence_Register"
)

REASSESSMENT_FILE = (
    EVIDENCE_DIR
    / "TJX_ISSB_requirement_reassessment_final.json"
)

ACTION_PLAN_FILE = (
    EVIDENCE_DIR
    / "TJX_ISSB_gap_action_plan.json"
)

SUMMARY_FILE = (
    EVIDENCE_DIR
    / "TJX_ISSB_requirement_reassessment_summary.json"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "06_Dashboard_Data"
)

REQUIREMENT_SUMMARY_CSV = (
    OUTPUT_DIR
    / "TJX_ISSB_requirement_summary.csv"
)

DASHBOARD_KPI_CSV = (
    OUTPUT_DIR
    / "TJX_ISSB_dashboard_kpis.csv"
)

GAP_PRIORITY_CSV = (
    OUTPUT_DIR
    / "TJX_ISSB_gap_priority_summary.csv"
)

DASHBOARD_JSON = (
    OUTPUT_DIR
    / "TJX_ISSB_dashboard_data.json"
)


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


def save_csv(
    rows,
    fieldnames,
    path: Path,
):

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
# REQUIREMENT SUMMARY
# =========================================================

def build_requirement_summary(
    reassessment,
    action_plan,
):

    gap_lookup = {
        clean(
            gap.get(
                "requirement_id"
            )
        ): gap
        for gap in action_plan
    }

    rows = []

    for record in reassessment:

        requirement_id = clean(
            record.get(
                "requirement_id"
            )
        )

        gap = gap_lookup.get(
            requirement_id,
            {},
        )

        baseline_score = int(
            record.get(
                "baseline_score",
                0,
            )
        )

        final_score = int(
            record.get(
                "final_score",
                0,
            )
        )

        score_change = (
            final_score
            - baseline_score
        )

        rows.append(
            {
                "Requirement ID":
                    requirement_id,

                "Requirement Name":
                    clean(
                        record.get(
                            "requirement_name"
                        )
                    ),

                "Baseline Rating":
                    clean(
                        record.get(
                            "baseline_rating"
                        )
                    ),

                "Baseline Score":
                    baseline_score,

                "Final Rating":
                    clean(
                        record.get(
                            "final_rating"
                        )
                    ),

                "Final Score":
                    final_score,

                "Score Change":
                    score_change,

                "Readiness Percent":
                    round(
                        final_score / 4,
                        4,
                    ),

                "Evidence Count":
                    int(
                        record.get(
                            "evidence_count",
                            0,
                        )
                    ),

                "GCR Evidence Count":
                    int(
                        record.get(
                            "gcr_evidence_count",
                            0,
                        )
                    ),

                "CDP Evidence Count":
                    int(
                        record.get(
                            "cdp_evidence_count",
                            0,
                        )
                    ),

                "Strong Evidence Count":
                    int(
                        record.get(
                            "strong_evidence_count",
                            0,
                        )
                    ),

                "Moderate Evidence Count":
                    int(
                        record.get(
                            "moderate_evidence_count",
                            0,
                        )
                    ),

                "Weak Evidence Count":
                    int(
                        record.get(
                            "weak_evidence_count",
                            0,
                        )
                    ),

                "Priority":
                    clean(
                        gap.get(
                            "priority"
                        )
                    ),

                "Effort":
                    clean(
                        gap.get(
                            "effort"
                        )
                    ),

                "Owner":
                    clean(
                        gap.get(
                            "owner"
                        )
                    ),

                "Status":
                    clean(
                        gap.get(
                            "status"
                        )
                    ),

                "Remaining Gap":
                    clean(
                        record.get(
                            "remaining_gaps"
                        )
                    ),

                "Recommended Action":
                    clean(
                        record.get(
                            "recommended_action"
                        )
                    ),
            }
        )

    return rows


# =========================================================
# DASHBOARD KPI TABLE
# =========================================================

def build_dashboard_kpis(
    summary,
    reassessment,
    action_plan,
):

    requirements_assessed = int(
        summary.get(
            "requirements_assessed",
            len(reassessment),
        )
    )

    baseline_score = int(
        summary.get(
            "baseline_total_score",
            0,
        )
    )

    final_score = int(
        summary.get(
            "final_total_score",
            0,
        )
    )

    max_score = int(
        summary.get(
            "maximum_possible_score",
            requirements_assessed * 4,
        )
    )

    baseline_readiness = float(
        summary.get(
            "baseline_pilot_readiness",
            0,
        )
    )

    final_readiness = float(
        summary.get(
            "final_pilot_readiness",
            0,
        )
    )

    improvement = (
        final_readiness
        - baseline_readiness
    )

    high_priority_count = sum(
        1
        for gap in action_plan
        if clean(
            gap.get(
                "priority"
            )
        ) == "High"
    )

    medium_priority_count = sum(
        1
        for gap in action_plan
        if clean(
            gap.get(
                "priority"
            )
        ) == "Medium"
    )

    open_gap_count = sum(
        1
        for gap in action_plan
        if clean(
            gap.get(
                "status"
            )
        ) == "Open"
    )

    mostly_covered_count = sum(
        1
        for record in reassessment
        if clean(
            record.get(
                "final_rating"
            )
        ) == "Mostly Covered"
    )

    partially_covered_count = sum(
        1
        for record in reassessment
        if clean(
            record.get(
                "final_rating"
            )
        ) == "Partially Covered"
    )

    fully_covered_count = sum(
        1
        for record in reassessment
        if clean(
            record.get(
                "final_rating"
            )
        ) == "Fully Covered"
    )

    total_evidence = sum(
        int(
            record.get(
                "evidence_count",
                0,
            )
        )
        for record in reassessment
    )

    rows = [
        {
            "KPI":
                "Requirements Assessed",
            "Value":
                requirements_assessed,
            "Unit":
                "requirements",
        },
        {
            "KPI":
                "Baseline Pilot Readiness",
            "Value":
                baseline_readiness,
            "Unit":
                "percent",
        },
        {
            "KPI":
                "Final Pilot Readiness",
            "Value":
                final_readiness,
            "Unit":
                "percent",
        },
        {
            "KPI":
                "Readiness Improvement",
            "Value":
                improvement,
            "Unit":
                "percentage points",
        },
        {
            "KPI":
                "Baseline Score",
            "Value":
                baseline_score,
            "Unit":
                f"out of {max_score}",
        },
        {
            "KPI":
                "Final Score",
            "Value":
                final_score,
            "Unit":
                f"out of {max_score}",
        },
        {
            "KPI":
                "Total Supporting Evidence",
            "Value":
                total_evidence,
            "Unit":
                "evidence items",
        },
        {
            "KPI":
                "Open Gaps",
            "Value":
                open_gap_count,
            "Unit":
                "gaps",
        },
        {
            "KPI":
                "High Priority Gaps",
            "Value":
                high_priority_count,
            "Unit":
                "gaps",
        },
        {
            "KPI":
                "Medium Priority Gaps",
            "Value":
                medium_priority_count,
            "Unit":
                "gaps",
        },
        {
            "KPI":
                "Mostly Covered Requirements",
            "Value":
                mostly_covered_count,
            "Unit":
                "requirements",
        },
        {
            "KPI":
                "Partially Covered Requirements",
            "Value":
                partially_covered_count,
            "Unit":
                "requirements",
        },
        {
            "KPI":
                "Fully Covered Requirements",
            "Value":
                fully_covered_count,
            "Unit":
                "requirements",
        },
    ]

    return rows


# =========================================================
# GAP PRIORITY SUMMARY
# =========================================================

def build_gap_priority_summary(
    action_plan,
):

    priority_counter = Counter(
        clean(
            gap.get(
                "priority"
            )
        )
        or "Unassigned"
        for gap in action_plan
    )

    effort_counter = Counter(
        clean(
            gap.get(
                "effort"
            )
        )
        or "Unassigned"
        for gap in action_plan
    )

    rows = []

    for priority in [
        "Critical",
        "High",
        "Medium",
        "Low",
        "Unassigned",
    ]:

        count = priority_counter.get(
            priority,
            0,
        )

        if count > 0:

            rows.append(
                {
                    "Category":
                        "Priority",

                    "Level":
                        priority,

                    "Gap Count":
                        count,
                }
            )

    for effort in [
        "High",
        "Medium",
        "Low",
        "Unassigned",
    ]:

        count = effort_counter.get(
            effort,
            0,
        )

        if count > 0:

            rows.append(
                {
                    "Category":
                        "Effort",

                    "Level":
                        effort,

                    "Gap Count":
                        count,
                }
            )

    return rows


# =========================================================
# JSON DASHBOARD PACKAGE
# =========================================================

def build_dashboard_json(
    requirement_rows,
    kpi_rows,
    gap_priority_rows,
    action_plan,
):

    return {

        "dashboard_scope":
            (
                "Five selected IFRS S2 pilot "
                "requirements assessed using "
                "public TJX evidence."
            ),

        "scope_warning":
            (
                "This is a pilot disclosure "
                "readiness assessment and is "
                "not an ISSB compliance score."
            ),

        "kpis":
            kpi_rows,

        "requirement_summary":
            requirement_rows,

        "gap_priority_summary":
            gap_priority_rows,

        "gap_action_plan":
            action_plan,
    }


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 80)
    print(
        "TJX ISSB DASHBOARD DATA BUILD"
    )
    print("=" * 80)

    # -----------------------------------------------------
    # LOAD INPUTS
    # -----------------------------------------------------

    reassessment = load_json(
        REASSESSMENT_FILE
    )

    action_plan = load_json(
        ACTION_PLAN_FILE
    )

    summary = load_json(
        SUMMARY_FILE
    )

    print(
        f"Requirements loaded: "
        f"{len(reassessment)}"
    )

    print(
        f"Gaps loaded: "
        f"{len(action_plan)}"
    )

    # -----------------------------------------------------
    # BUILD TABLES
    # -----------------------------------------------------

    requirement_rows = (
        build_requirement_summary(
            reassessment,
            action_plan,
        )
    )

    kpi_rows = (
        build_dashboard_kpis(
            summary,
            reassessment,
            action_plan,
        )
    )

    gap_priority_rows = (
        build_gap_priority_summary(
            action_plan
        )
    )

    dashboard_package = (
        build_dashboard_json(
            requirement_rows,
            kpi_rows,
            gap_priority_rows,
            action_plan,
        )
    )

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    save_csv(
        requirement_rows,
        [
            "Requirement ID",
            "Requirement Name",
            "Baseline Rating",
            "Baseline Score",
            "Final Rating",
            "Final Score",
            "Score Change",
            "Readiness Percent",
            "Evidence Count",
            "GCR Evidence Count",
            "CDP Evidence Count",
            "Strong Evidence Count",
            "Moderate Evidence Count",
            "Weak Evidence Count",
            "Priority",
            "Effort",
            "Owner",
            "Status",
            "Remaining Gap",
            "Recommended Action",
        ],
        REQUIREMENT_SUMMARY_CSV,
    )

    save_csv(
        kpi_rows,
        [
            "KPI",
            "Value",
            "Unit",
        ],
        DASHBOARD_KPI_CSV,
    )

    save_csv(
        gap_priority_rows,
        [
            "Category",
            "Level",
            "Gap Count",
        ],
        GAP_PRIORITY_CSV,
    )

    save_json(
        dashboard_package,
        DASHBOARD_JSON,
    )

    # -----------------------------------------------------
    # REPORT
    # -----------------------------------------------------

    print()
    print("=" * 80)
    print(
        "DASHBOARD DATA CREATED"
    )
    print("=" * 80)

    print()
    print(
        "Requirement Summary:"
    )
    print(
        REQUIREMENT_SUMMARY_CSV
    )

    print()
    print(
        "Dashboard KPIs:"
    )
    print(
        DASHBOARD_KPI_CSV
    )

    print()
    print(
        "Gap Priority Summary:"
    )
    print(
        GAP_PRIORITY_CSV
    )

    print()
    print(
        "Dashboard JSON:"
    )
    print(
        DASHBOARD_JSON
    )

    print()
    print(
        "Key results:"
    )

    for row in kpi_rows:

        if row["KPI"] in {
            "Baseline Pilot Readiness",
            "Final Pilot Readiness",
            "Readiness Improvement",
            "Open Gaps",
            "High Priority Gaps",
        }:

            value = row["Value"]

            if row["Unit"] in {
                "percent",
                "percentage points",
            }:

                print(
                    f"  {row['KPI']}: "
                    f"{value:.1%}"
                )

            else:

                print(
                    f"  {row['KPI']}: "
                    f"{value}"
                )

    print()
    print("=" * 80)
    print(
        "NEXT STEP"
    )
    print("=" * 80)

    print(
        "Load the three CSV files into "
        "Excel or Power BI."
    )

    print()
    print(
        "Recommended dashboard visuals:"
    )

    print(
        "  1. Baseline vs final pilot readiness KPI"
    )

    print(
        "  2. Baseline vs final score by requirement"
    )

    print(
        "  3. Current rating by requirement"
    )

    print(
        "  4. Gap priority and effort"
    )

    print(
        "  5. Requirement / owner / recommended action table"
    )

    print()
    print(
        "Do not label the 70% result as "
        "ISSB compliance."
    )

    print("=" * 80)


if __name__ == "__main__":
    main()