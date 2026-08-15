from pathlib import Path

from llama_index.core import (
    Settings,
    StorageContext,
    load_index_from_storage,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INDEX_DIR = (
    PROJECT_ROOT
    / "04_Vector_Indexes"
    / "TJX_CDP_Index"
)

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

TOP_K = 8


QUERIES = {
    "S2-GOV-02": (
        "Find evidence that identifies the board, board committee, "
        "or equivalent governing body responsible for oversight of "
        "climate-related risks, opportunities, targets, and performance."
    ),

    "S2-STR-06": (
        "Find evidence of TJX climate-related scenario analysis, "
        "including scenarios used, assumptions, time horizons, "
        "physical risks, transition risks, vulnerabilities, "
        "resilience conclusions, and planned responses."
    ),

    "S2-MT-01": (
        "Find TJX gross Scope 1 greenhouse gas emissions for the "
        "reporting period, including the emissions value, unit, "
        "organizational boundary, measurement methodology, "
        "emission factors, and reporting period."
    ),

    "S2-MT-02": (
        "Find TJX gross Scope 2 greenhouse gas emissions for the "
        "reporting period, including market-based and location-based "
        "values, unit, organizational boundary, methodology, "
        "emission factors, and reporting period."
    ),

    "S2-MT-04": (
        "Find TJX climate-related targets, including target value, "
        "baseline year, target year, emissions scope, organizational "
        "boundary, methodology, validation status, and progress "
        "against the target."
    ),
}


def load_index():
    if not INDEX_DIR.exists():
        raise FileNotFoundError(
            f"Vector index not found:\n{INDEX_DIR}"
        )

    embed_model = HuggingFaceEmbedding(
        model_name=EMBEDDING_MODEL
    )

    Settings.embed_model = embed_model

    storage_context = StorageContext.from_defaults(
        persist_dir=str(INDEX_DIR)
    )

    index = load_index_from_storage(
        storage_context
    )

    return index


def print_result(
    requirement_id,
    rank,
    node_with_score,
):
    node = node_with_score.node
    score = node_with_score.score

    metadata = node.metadata

    page_number = metadata.get(
        "page_number",
        "UNKNOWN"
    )

    document_name = metadata.get(
        "document_name",
        "UNKNOWN"
    )

    text = node.get_content()

    preview = text[:900].replace(
        "\n",
        " "
    )

    print()
    print(
        f"Rank {rank}"
    )

    print(
        f"Page: {page_number}"
    )

    print(
        f"Score: {score:.4f}"
        if score is not None
        else "Score: None"
    )

    print(
        f"Document: {document_name}"
    )

    print(
        f"Preview: {preview}"
    )

    print("-" * 80)


def main():
    print()
    print("=" * 80)
    print("TJX CDP SEMANTIC RETRIEVAL TEST")
    print("=" * 80)

    index = load_index()

    retriever = index.as_retriever(
        similarity_top_k=TOP_K
    )

    for requirement_id, query in QUERIES.items():

        print()
        print()
        print("=" * 80)

        print(
            f"{requirement_id}"
        )

        print("=" * 80)

        print(
            f"Query:\n{query}"
        )

        results = retriever.retrieve(
            query
        )

        print(
            f"\nRetrieved nodes: "
            f"{len(results)}"
        )

        for rank, result in enumerate(
            results,
            start=1,
        ):
            print_result(
                requirement_id,
                rank,
                result,
            )

    print()
    print("=" * 80)
    print("SEMANTIC RETRIEVAL TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()