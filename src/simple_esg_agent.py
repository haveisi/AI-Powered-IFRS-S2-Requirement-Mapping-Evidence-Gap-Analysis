from typing import Dict, Any

def validate_metric(metric: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks whether a ESG matric has the basic fields needed for reporting.
    """

    required_fields =["matric_name", "value", "unite", "year", "source"]
    missing_fields = []

    for field in required_fields:
        if field not in metric or metric[field] in [None, "", "not stated"]:
            missing_fields.append(field)

    if missing_fields:
        metric["validation_status"]= "Needs review"
        metric["validation_notes"] = f"Missing fields: {', '.join(missing_fields)}"
    else:
        metric["validation_status"] = "Passed"
        metric["validation_notes"] ="All required fields are present."

    return metric

def classify_assurance(metric: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify whether the metric appears to have assurance support
    This is simple rule-based logic, not a final assurance conclusion.
 """

    source_text = metric.get("source", "").lower()

    if "assurance" in source_text or "verified" in source_text or "bureau veritas" in source_text:
        metric["assurance_status"] = "Potentially assured"
        metric["assurance_notes"] = "Source mentions assurance or verification. Confirm against assurance statement."
    else:
        metric["assurance_status"] = "Not confirmed"
        metric["assurance_notes"] = "No assurance reference found in source field."

    return metric


def assign_human_review(metric: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decide whether the metric should be reviewed by a human before reporting.
    """

    needs_review = False
    reasons = []

    if metric["validation_status"] != "Passed":
        needs_review = True
        reasons.append("Metric failed basic validation.")

    if metric["assurance_status"] == "Not confirmed":
        needs_review = True
        reasons.append("Assurance status is not confirmed.")

    if metric.get("claim_type") in ["forward-looking", "narrative claim"]:
        needs_review = True
        reasons.append("Claim type requires interpretation.")

    metric["human_review_required"] = "Yes" if needs_review else "No"
    metric["human_review_reason"] = " ".join(reasons) if reasons else "No major review trigger identified."

    return metric


def run_esg_agent(metric: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple ESG agent workflow:
    validate -> classify assurance -> assign human review
    """

    metric = validate_metric(metric)
    metric = classify_assurance(metric)
    metric = assign_human_review(metric)

    return metric


if __name__ == "__main__":

    sample_metric = {
        "metric_name": "Scope 1 emissions",
        "value": 412646,
        "unit": "tCO2e",
        "year": 2024,
        "source": "TJX 2025 Global Corporate Responsibility Report",
        "claim_type": "quantitative metric"
    }

    result = run_esg_agent(sample_metric)

    print("\n--- Simple ESG Agent Result ---")
    for key, value in result.items():
        print(f"{key}: {value}")

