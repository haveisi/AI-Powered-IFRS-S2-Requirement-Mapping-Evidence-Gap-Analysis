import json
import re
from pathlib import Path

import fitz  # PyMuPDF


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SOURCE_FILE = (
    PROJECT_ROOT
    / "02_Source_Documents"
    / "TJX_2025_CDP_Climate_Response.pdf"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "03_Extracted_Text"
    / "TJX_2025_CDP_Climate_Response.json"
)


# ---------------------------------------------------------
# Text cleanup
# ---------------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Clean extracted PDF text conservatively.

    Important:
    We do NOT aggressively rewrite the text because later
    we need to validate exact quotations against the source.
    """

    text = text.replace("\u00a0", " ")

    # Collapse multiple spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Reduce excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ---------------------------------------------------------
# Extract PDF
# ---------------------------------------------------------

def extract_pdf_pages(pdf_path: Path) -> list[dict]:
    """
    Extract one JSON object per PDF page.
    """

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"CDP PDF not found:\n{pdf_path}"
        )

    document = fitz.open(pdf_path)

    records = []

    for page_index in range(len(document)):

        page = document.load_page(page_index)

        raw_text = page.get_text("text")

        clean_text = normalize_text(raw_text)

        record = {
            "document_name": pdf_path.name,
            "document_type": "CDP Climate Response",
            "page_number": page_index + 1,
            "page_index": page_index,
            "text": clean_text,
            "character_count": len(clean_text),
        }

        records.append(record)

    document.close()

    return records


# ---------------------------------------------------------
# Validation summary
# ---------------------------------------------------------

def summarize_extraction(records: list[dict]) -> None:

    total_pages = len(records)

    total_characters = sum(
        row["character_count"]
        for row in records
    )

    empty_pages = [
        row["page_number"]
        for row in records
        if row["character_count"] == 0
    ]

    short_pages = [
        row["page_number"]
        for row in records
        if 0 < row["character_count"] < 100
    ]

    print()
    print("=" * 72)
    print("TJX CDP EXTRACTION SUMMARY")
    print("=" * 72)

    print(
        f"Pages extracted: {total_pages}"
    )

    print(
        f"Total characters: {total_characters:,}"
    )

    print(
        f"Empty pages: {len(empty_pages)}"
    )

    if empty_pages:
        print(
            f"Empty page numbers: {empty_pages}"
        )

    print(
        f"Very short pages (<100 chars): "
        f"{len(short_pages)}"
    )

    if short_pages:
        print(
            f"Short page numbers: {short_pages}"
        )

    print("=" * 72)


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

def save_json(
    records: list[dict],
    output_path: Path,
) -> None:

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            records,
            file,
            indent=2,
            ensure_ascii=False,
        )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main() -> None:

    print()
    print("Starting TJX CDP extraction...")
    print()

    print(
        f"Source:\n{SOURCE_FILE}"
    )

    records = extract_pdf_pages(
        SOURCE_FILE
    )

    save_json(
        records=records,
        output_path=OUTPUT_FILE,
    )

    summarize_extraction(
        records
    )

    print()
    print("Saved extracted CDP text to:")
    print(
        OUTPUT_FILE
    )

    print()
    print("Extraction complete.")


if __name__ == "__main__":
    main()