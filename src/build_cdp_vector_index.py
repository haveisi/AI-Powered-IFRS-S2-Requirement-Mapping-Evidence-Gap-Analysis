import json
from pathlib import Path

from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "03_Extracted_Text"
    / "TJX_2025_CDP_Climate_Response.json"
)

PERSIST_DIR = (
    PROJECT_ROOT
    / "04_Vector_Indexes"
    / "TJX_CDP_Index"
)


# =========================================================
# SETTINGS
# =========================================================

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

CHUNK_SIZE = 700
CHUNK_OVERLAP = 100


# =========================================================
# LOAD PAGE JSON
# =========================================================

def load_pages(path: Path) -> list[dict]:

    if not path.exists():
        raise FileNotFoundError(
            f"CDP JSON not found:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "Expected page-level JSON list."
        )

    return data


# =========================================================
# CONVERT TO LLAMAINDEX DOCUMENTS
# =========================================================

def create_documents(
    pages: list[dict],
) -> list[Document]:

    documents = []

    for page in pages:

        text = page.get(
            "text",
            "",
        ).strip()

        if not text:
            continue

        metadata = {
            "document_name":
                page["document_name"],

            "document_type":
                page["document_type"],

            "page_number":
                page["page_number"],

            "page_index":
                page["page_index"],

            "source_type":
                "CDP",

            "company":
                "TJX Companies",

            "reporting_source":
                "2025 CDP Climate Response",
        }

        document = Document(
            text=text,
            metadata=metadata,
        )

        documents.append(
            document
        )

    return documents


# =========================================================
# BUILD INDEX
# =========================================================

def build_index(
    documents: list[Document],
) -> VectorStoreIndex:

    print()
    print(
        "Loading local embedding model..."
    )

    embed_model = HuggingFaceEmbedding(
        model_name=EMBEDDING_MODEL
    )

    Settings.embed_model = embed_model

    Settings.node_parser = SentenceSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    print(
        f"Embedding model: "
        f"{EMBEDDING_MODEL}"
    )

    print(
        f"Documents: "
        f"{len(documents)}"
    )

    print(
        f"Chunk size: "
        f"{CHUNK_SIZE}"
    )

    print(
        f"Chunk overlap: "
        f"{CHUNK_OVERLAP}"
    )

    print()
    print(
        "Building vector index..."
    )

    index = VectorStoreIndex.from_documents(
        documents,
        show_progress=True,
    )

    return index


# =========================================================
# SAVE INDEX
# =========================================================

def save_index(
    index: VectorStoreIndex,
) -> None:

    PERSIST_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    index.storage_context.persist(
        persist_dir=str(PERSIST_DIR)
    )


# =========================================================
# MAIN
# =========================================================

def main() -> None:

    print()
    print("=" * 72)
    print("TJX CDP VECTOR INDEX")
    print("=" * 72)

    pages = load_pages(
        INPUT_FILE
    )

    print(
        f"CDP pages loaded: "
        f"{len(pages)}"
    )

    documents = create_documents(
        pages
    )

    print(
        f"Documents created: "
        f"{len(documents)}"
    )

    index = build_index(
        documents
    )

    save_index(
        index
    )

    print()
    print("=" * 72)
    print("VECTOR INDEX COMPLETE")
    print("=" * 72)

    print(
        "Index saved to:"
    )

    print(
        PERSIST_DIR
    )

    print()
    print(
        "No LLM was used."
    )

    print(
        "No Claude API call was made."
    )

    print(
        "This index contains semantic "
        "embeddings for retrieval only."
    )

    print("=" * 72)


if __name__ == "__main__":
    main()