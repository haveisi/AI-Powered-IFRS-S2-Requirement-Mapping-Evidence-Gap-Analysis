import json
from pathlib import Path

import fitz


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_FOLDER = PROJECT_ROOT / "01_Source_Documents"
OUTPUT_FOLDER = PROJECT_ROOT / "03_Extracted_Text"


def find_pdf_files() -> list[Path]:
    """Return all PDF files in the source folder."""
    return sorted(SOURCE_FOLDER.glob("*.pdf"))


def extract_pdf_pages(pdf_path: Path) -> list[dict]:
    """Extract text while preserving document name and PDF page number."""
    pages: list[dict] = []

    with fitz.open(pdf_path) as document:
        for page_index, page in enumerate(document):
            text = page.get_text("text").strip()

            pages.append(
                {
                    "source_document": pdf_path.name,
                    "pdf_page_number": page_index + 1,
                    "text": text,
                    "character_count": len(text),
                    "requires_review": len(text) < 50,
                }
            )

    return pages


def save_pages(pdf_path: Path, pages: list[dict]) -> Path:
    """Save extracted pages as UTF-8 JSON."""
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_FOLDER / f"{pdf_path.stem}.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            pages,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return output_path


def main() -> None:
    if not SOURCE_FOLDER.exists():
        raise FileNotFoundError(
            f"Source folder does not exist: {SOURCE_FOLDER}"
        )

    pdf_files = find_pdf_files()

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files were found in: {SOURCE_FOLDER}"
        )

    print(f"Found {len(pdf_files)} PDF file(s).")

    for pdf_path in pdf_files:
        pages = extract_pdf_pages(pdf_path)
        output_path = save_pages(pdf_path, pages)

        review_pages = sum(
            page["requires_review"] for page in pages
        )

        print()
        print(f"Document: {pdf_path.name}")
        print(f"Pages extracted: {len(pages)}")
        print(f"Pages requiring review: {review_pages}")
        print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
