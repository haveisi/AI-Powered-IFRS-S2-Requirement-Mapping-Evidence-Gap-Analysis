import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PDF_FILE = (
    PROJECT_ROOT
    / "02_Source_Documents"
    / "TJX_2025_CDP_Climate_Response.pdf"
)

JSON_FILE = (
    PROJECT_ROOT
    / "03_Extracted_Text"
    / "TJX_2025_CDP_Climate_Response.json"
)


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"JSON file not found:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "Expected JSON root to be a list."
        )

    return data


def validate_schema(records: list[dict]) -> list[str]:
    required_fields = {
        "document_name",
        "document_type",
        "page_number",
        "page_index",
        "text",
        "character_count",
    }

    errors = []

    for row_number, record in enumerate(
        records,
        start=1,
    ):
        missing = required_fields - set(record.keys())

        if missing:
            errors.append(
                f"Record {row_number}: "
                f"missing fields {sorted(missing)}"
            )

    return errors


def validate_page_numbers(
    records: list[dict],
) -> dict:
    page_numbers = [
        row["page_number"]
        for row in records
    ]

    expected_pages = list(
        range(
            1,
            len(records) + 1,
        )
    )

    duplicates = sorted(
        {
            page
            for page in page_numbers
            if page_numbers.count(page) > 1
        }
    )

    missing = sorted(
        set(expected_pages)
        - set(page_numbers)
    )

    out_of_sequence = (
        page_numbers != expected_pages
    )

    return {
        "duplicates": duplicates,
        "missing": missing,
        "out_of_sequence": out_of_sequence,
    }


def validate_text(records: list[dict]) -> dict:
    empty_pages = []

    short_pages = []

    mismatched_character_counts = []

    for record in records:
        page_number = record["page_number"]

        text = record["text"]

        character_count = record[
            "character_count"
        ]

        if text is None:
            empty_pages.append(
                page_number
            )

            continue

        actual_count = len(text)

        if actual_count == 0:
            empty_pages.append(
                page_number
            )

        if 0 < actual_count < 100:
            short_pages.append(
                {
                    "page_number": page_number,
                    "character_count": actual_count,
                    "text_preview": text[:300],
                }
            )

        if actual_count != character_count:
            mismatched_character_counts.append(
                {
                    "page_number": page_number,
                    "stored": character_count,
                    "actual": actual_count,
                }
            )

    return {
        "empty_pages": empty_pages,
        "short_pages": short_pages,
        "character_count_mismatches":
            mismatched_character_counts,
    }


def validate_metadata(
    records: list[dict],
) -> list[str]:
    issues = []

    expected_document_name = (
        "TJX_2025_CDP_Climate_Response.pdf"
    )

    expected_document_type = (
        "CDP Climate Response"
    )

    for record in records:
        page = record["page_number"]

        if (
            record["document_name"]
            != expected_document_name
        ):
            issues.append(
                f"Page {page}: unexpected "
                f"document_name "
                f"{record['document_name']}"
            )

        if (
            record["document_type"]
            != expected_document_type
        ):
            issues.append(
                f"Page {page}: unexpected "
                f"document_type "
                f"{record['document_type']}"
            )

        if (
            record["page_index"]
            != page - 1
        ):
            issues.append(
                f"Page {page}: page_index "
                f"{record['page_index']} "
                f"does not equal page_number - 1."
            )

    return issues


def print_short_page_review(
    short_pages: list[dict],
) -> None:
    print()
    print("=" * 72)
    print("SHORT PAGE REVIEW")
    print("=" * 72)

    if not short_pages:
        print(
            "No pages under 100 characters."
        )

        return

    for item in short_pages:
        print()
        print(
            f"Page: "
            f"{item['page_number']}"
        )

        print(
            f"Character count: "
            f"{item['character_count']}"
        )

        print("Text preview:")

        print(
            repr(
                item["text_preview"]
            )
        )


def main() -> None:
    print()
    print(
        "Validating TJX CDP extraction..."
    )

    records = load_json(
        JSON_FILE
    )

    schema_errors = validate_schema(
        records
    )

    page_checks = validate_page_numbers(
        records
    )

    text_checks = validate_text(
        records
    )

    metadata_issues = validate_metadata(
        records
    )

    print()
    print("=" * 72)
    print("CDP EXTRACTION VALIDATION")
    print("=" * 72)

    print(
        f"JSON records: "
        f"{len(records)}"
    )

    print(
        f"Schema errors: "
        f"{len(schema_errors)}"
    )

    print(
        f"Duplicate pages: "
        f"{len(page_checks['duplicates'])}"
    )

    print(
        f"Missing pages: "
        f"{len(page_checks['missing'])}"
    )

    print(
        f"Out of sequence: "
        f"{page_checks['out_of_sequence']}"
    )

    print(
        f"Empty pages: "
        f"{len(text_checks['empty_pages'])}"
    )

    print(
        f"Short pages: "
        f"{len(text_checks['short_pages'])}"
    )

    print(
        f"Character-count mismatches: "
        f"{len(text_checks['character_count_mismatches'])}"
    )

    print(
        f"Metadata issues: "
        f"{len(metadata_issues)}"
    )

    if schema_errors:
        print()
        print("SCHEMA ERRORS:")

        for error in schema_errors:
            print(
                f"- {error}"
            )

    if page_checks["duplicates"]:
        print()
        print(
            "DUPLICATE PAGE NUMBERS:"
        )

        print(
            page_checks["duplicates"]
        )

    if page_checks["missing"]:
        print()
        print(
            "MISSING PAGE NUMBERS:"
        )

        print(
            page_checks["missing"]
        )

    if text_checks[
        "character_count_mismatches"
    ]:
        print()
        print(
            "CHARACTER COUNT MISMATCHES:"
        )

        for issue in text_checks[
            "character_count_mismatches"
        ]:
            print(
                issue
            )

    if metadata_issues:
        print()
        print("METADATA ISSUES:")

        for issue in metadata_issues:
            print(
                f"- {issue}"
            )

    print_short_page_review(
        text_checks["short_pages"]
    )

    critical_errors = (
        len(schema_errors)
        + len(page_checks["duplicates"])
        + len(page_checks["missing"])
        + len(text_checks["empty_pages"])
        + len(
            text_checks[
                "character_count_mismatches"
            ]
        )
        + len(metadata_issues)
    )

    print()
    print("=" * 72)

    if critical_errors == 0:
        print(
            "VALIDATION RESULT: PASS"
        )

        print(
            "The CDP extraction is structurally "
            "ready for retrieval."
        )

    else:
        print(
            "VALIDATION RESULT: REVIEW REQUIRED"
        )

        print(
            f"Critical issues found: "
            f"{critical_errors}"
        )

    print("=" * 72)


if __name__ == "__main__":
    main()