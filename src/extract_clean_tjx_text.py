from pathlib import Path
import fitz  # PyMuPDF


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PDF_PATH = PROJECT_ROOT / "01_Source_Documents" / "TJX_2025_Global_Corporate_Responsibility_Report.pdf"
OUTPUT_DIR = PROJECT_ROOT / "03_Extracted_Text"
OUTPUT_PATH = OUTPUT_DIR / "tjx_2025_clean_text.txt"

OUTPUT_DIR.mkdir(exist_ok=True)


def extract_text_from_pdf(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    all_pages = []

    for page_number, page in enumerate(doc, start=1):
        text = page.get_text("text")

        if text.strip():
            page_text = f"\n\n--- PAGE {page_number} ---\n\n{text}"
            all_pages.append(page_text)

    doc.close()
    return "\n".join(all_pages)


if __name__ == "__main__":
    clean_text = extract_text_from_pdf(PDF_PATH)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(clean_text)

    print(f"Clean text saved to: {OUTPUT_PATH}")
    print(f"Characters extracted: {len(clean_text)}")