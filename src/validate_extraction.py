import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXTRACTED_FOLDER = PROJECT_ROOT / "03_Extracted_Text"


def main() -> None:
    json_files = sorted(EXTRACTED_FOLDER.glob("*.json"))

    if not json_files:
        raise FileNotFoundError(
            f"No JSON files found in: {EXTRACTED_FOLDER}"
        )

    for json_path in json_files:
        with json_path.open("r", encoding="utf-8") as file:
            pages = json.load(file)

        total_pages = len(pages)
        empty_pages = [
            page for page in pages
            if not page.get("text", "").strip()
        ]
        review_pages = [
            page for page in pages
            if page.get("requires_review") is True
        ]

        total_characters = sum(
            page.get("character_count", 0)
            for page in pages
        )

        print("=" * 70)
        print(f"File: {json_path.name}")
        print(f"Total pages: {total_pages}")
        print(f"Total characters: {total_characters:,}")
        print(f"Empty pages: {len(empty_pages)}")
        print(f"Pages requiring review: {len(review_pages)}")

        if review_pages:
            print("\nReview pages:")
            for page in review_pages:
                print(
                    f"- PDF page {page['pdf_page_number']}: "
                    f"{page['character_count']} characters"
                )

                preview = page.get("text", "")[:300]
                print(f"  Preview: {preview!r}")

        required_fields = {
            "source_document",
            "pdf_page_number",
            "text",
            "character_count",
            "requires_review",
        }

        schema_errors = []

        for index, page in enumerate(pages, start=1):
            missing_fields = required_fields - set(page.keys())

            if missing_fields:
                schema_errors.append(
                    {
                        "record": index,
                        "missing_fields": sorted(missing_fields),
                    }
                )

        print(f"\nSchema errors: {len(schema_errors)}")

        if schema_errors:
            for error in schema_errors[:10]:
                print(error)
        else:
            print("Schema validation passed.")


if __name__ == "__main__":
    main()