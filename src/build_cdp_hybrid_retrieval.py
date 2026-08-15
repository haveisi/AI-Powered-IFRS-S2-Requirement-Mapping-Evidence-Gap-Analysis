import json
from pathlib import Path
from collections import defaultdict

from llama_index.core import (
    Settings,
    StorageContext,
    load_index_from_storage,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

KEYWORD_FILE = (
    PROJECT_ROOT
    / "03_Extracted_Text"
    / "TJX_CDP_priority_pages.json"
)

INDEX_DIR = (
    PROJECT_ROOT
    / "04_Vector_Indexes"
    / "TJX_CDP_Index"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "03_Extracted_Text"
    / "TJX_CDP_hybrid_retrieval_results.json"
)


# =========================================================
# SETTINGS
# =========================================================

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

SEMANTIC_TOP_K = 8

FINAL_TOP_K = 8


# =========================================================
# REQUIREMENT QUERIES
# =========================================================

QUERIES = {

    "S2-GOV-02": (
        "Find evidence that identifies the board, board committee, "
        "or equivalent governing body responsible for oversight of "
        "climate-related risks, opportunities, climate targets, "
        "and climate performance."
    ),

    "S2-STR-06": (
        "Find evidence of climate-related scenario analysis, "
        "including scenarios used, assumptions, time horizons, "
        "physical risks, transition risks, vulnerabilities, "
        "resilience conclusions, and planned responses."
    ),

    "S2-MT-01": (
        "Find TJX gross Scope 1 greenhouse gas emissions for the "
        "reporting period, including emissions value, unit, "
        "organizational boundary, measurement methodology, "
        "emission factors, and reporting period."
    ),

    "S2-MT-02": (
        "Find TJX gross Scope 2 greenhouse gas emissions for the "
        "reporting period, including market-based and location-based "
        "emissions, unit, organizational boundary, measurement "
        "methodology, emission factors, and reporting period."
    ),

    "S2-MT-04": (
        "Find TJX climate-related targets, including target value, "
        "baseline year, target year, emissions scope, organizational "
        "boundary, methodology, validation status, interim milestones, "
        "and progress against the target."
    ),
}


# =========================================================
# LOAD KEYWORD RESULTS
# =========================================================

def load_keyword_results():

    if not KEYWORD_FILE.exists():
        raise FileNotFoundError(
            f"Keyword results not found:\n{KEYWORD_FILE}"
        )

    with KEYWORD_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# =========================================================
# LOAD VECTOR INDEX
# =========================================================

def load_vector_index():

    print("Loading embedding model...")

    Settings.embed_model = HuggingFaceEmbedding(
        model_name=EMBEDDING_MODEL
    )

    storage_context = StorageContext.from_defaults(
        persist_dir=str(INDEX_DIR)
    )

    index = load_index_from_storage(
        storage_context
    )

    return index


# =========================================================
# ORGANIZE KEYWORD RESULTS BY REQUIREMENT
# =========================================================

def organize_keyword_results(
    keyword_pages,
):

    results = defaultdict(dict)

    for page in keyword_pages:

        page_number = page["page_number"]

        requirement_scores = page.get(
            "requirement_scores",
            {},
        )

        for requirement_id, score in (
            requirement_scores.items()
        ):

            results[
                requirement_id
            ][
                page_number
            ] = {
                "keyword_score": score,
                "keyword_found": True,
            }

    return results


# =========================================================
# SEMANTIC RETRIEVAL
# =========================================================

def semantic_retrieval(
    index,
):

    retriever = index.as_retriever(
        similarity_top_k=SEMANTIC_TOP_K
    )

    semantic_results = defaultdict(dict)

    for requirement_id, query in (
        QUERIES.items()
    ):

        print()
        print(
            f"Semantic retrieval: "
            f"{requirement_id}"
        )

        nodes = retriever.retrieve(
            query
        )

        for rank, result in enumerate(
            nodes,
            start=1,
        ):

            node = result.node

            page_number = node.metadata.get(
                "page_number"
            )

            if page_number is None:
                continue

            semantic_results[
                requirement_id
            ][
                page_number
            ] = {

                "semantic_score":
                    result.score,

                "semantic_rank":
                    rank,

                "semantic_found":
                    True,

                "text":
                    node.get_content(),

                "metadata":
                    node.metadata,
            }

    return semantic_results


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_keyword_scores(
    keyword_results,
):

    normalized = {}

    for requirement_id, pages in (
        keyword_results.items()
    ):

        if not pages:
            normalized[
                requirement_id
            ] = {}

            continue

        max_score = max(
            item["keyword_score"]
            for item in pages.values()
        )

        normalized[
            requirement_id
        ] = {}

        for page_number, item in (
            pages.items()
        ):

            score = (
                item["keyword_score"]
                / max_score
                if max_score > 0
                else 0
            )

            normalized[
                requirement_id
            ][
                page_number
            ] = score

    return normalized


def normalize_semantic_scores(
    semantic_results,
):

    normalized = {}

    for requirement_id, pages in (
        semantic_results.items()
    ):

        if not pages:
            normalized[
                requirement_id
            ] = {}

            continue

        scores = [
            item["semantic_score"]
            for item in pages.values()
            if item["semantic_score"]
            is not None
        ]

        if not scores:
            normalized[
                requirement_id
            ] = {}

            continue

        min_score = min(scores)
        max_score = max(scores)

        normalized[
            requirement_id
        ] = {}

        for page_number, item in (
            pages.items()
        ):

            raw_score = item[
                "semantic_score"
            ]

            if raw_score is None:

                normalized_score = 0

            elif max_score == min_score:

                normalized_score = 1

            else:

                normalized_score = (
                    raw_score - min_score
                ) / (
                    max_score - min_score
                )

            normalized[
                requirement_id
            ][
                page_number
            ] = normalized_score

    return normalized


# =========================================================
# HYBRID COMBINATION
# =========================================================

def build_hybrid_results(
    keyword_results,
    semantic_results,
):

    normalized_keyword = (
        normalize_keyword_scores(
            keyword_results
        )
    )

    normalized_semantic = (
        normalize_semantic_scores(
            semantic_results
        )
    )

    final_results = {}

    for requirement_id in QUERIES:

        all_pages = set()

        all_pages.update(
            keyword_results.get(
                requirement_id,
                {},
            ).keys()
        )

        all_pages.update(
            semantic_results.get(
                requirement_id,
                {},
            ).keys()
        )

        requirement_rows = []

        for page_number in all_pages:

            keyword_normalized = (
                normalized_keyword
                .get(
                    requirement_id,
                    {},
                )
                .get(
                    page_number,
                    0,
                )
            )

            semantic_normalized = (
                normalized_semantic
                .get(
                    requirement_id,
                    {},
                )
                .get(
                    page_number,
                    0,
                )
            )

            keyword_found = (
                page_number
                in keyword_results.get(
                    requirement_id,
                    {},
                )
            )

            semantic_found = (
                page_number
                in semantic_results.get(
                    requirement_id,
                    {},
                )
            )

            # ---------------------------------------------
            # HYBRID SCORE
            #
            # 50% keyword
            # 50% semantic
            #
            # Small bonus if both systems found page
            # ---------------------------------------------

            hybrid_score = (
                0.50
                * keyword_normalized
                +
                0.50
                * semantic_normalized
            )

            if (
                keyword_found
                and semantic_found
            ):
                hybrid_score += 0.10

            semantic_item = (
                semantic_results
                .get(
                    requirement_id,
                    {},
                )
                .get(
                    page_number,
                    {},
                )
            )

            keyword_item = (
                keyword_results
                .get(
                    requirement_id,
                    {},
                )
                .get(
                    page_number,
                    {},
                )
            )

            row = {

                "requirement_id":
                    requirement_id,

                "page_number":
                    page_number,

                "hybrid_score":
                    round(
                        hybrid_score,
                        4,
                    ),

                "keyword_found":
                    keyword_found,

                "semantic_found":
                    semantic_found,

                "keyword_score":
                    keyword_item.get(
                        "keyword_score"
                    ),

                "keyword_normalized":
                    round(
                        keyword_normalized,
                        4,
                    ),

                "semantic_score":
                    semantic_item.get(
                        "semantic_score"
                    ),

                "semantic_normalized":
                    round(
                        semantic_normalized,
                        4,
                    ),

                "semantic_rank":
                    semantic_item.get(
                        "semantic_rank"
                    ),

                "text":
                    semantic_item.get(
                        "text",
                        "",
                    ),

                "metadata":
                    semantic_item.get(
                        "metadata",
                        {},
                    ),
            }

            requirement_rows.append(
                row
            )

        requirement_rows.sort(
            key=lambda x: (
                -x["hybrid_score"],
                x["page_number"],
            )
        )

        final_results[
            requirement_id
        ] = requirement_rows[
            :FINAL_TOP_K
        ]

    return final_results


# =========================================================
# SAVE
# =========================================================

def save_results(
    results,
):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False,
        )


# =========================================================
# PRINT RESULTS
# =========================================================

def print_results(
    results,
):

    print()
    print("=" * 80)
    print("TJX CDP HYBRID RETRIEVAL RESULTS")
    print("=" * 80)

    for requirement_id, rows in (
        results.items()
    ):

        print()
        print()
        print(
            f"{requirement_id}"
        )

        print("-" * 80)

        for rank, row in enumerate(
            rows,
            start=1,
        ):

            print(
                f"Rank {rank}"
                f" | Page "
                f"{row['page_number']}"
                f" | Hybrid "
                f"{row['hybrid_score']:.4f}"
                f" | Keyword "
                f"{row['keyword_found']}"
                f" | Semantic "
                f"{row['semantic_found']}"
            )


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 80)
    print("BUILDING TJX CDP HYBRID RETRIEVAL")
    print("=" * 80)

    keyword_pages = (
        load_keyword_results()
    )

    keyword_results = (
        organize_keyword_results(
            keyword_pages
        )
    )

    index = load_vector_index()

    semantic_results = (
        semantic_retrieval(
            index
        )
    )

    hybrid_results = (
        build_hybrid_results(
            keyword_results,
            semantic_results,
        )
    )

    save_results(
        hybrid_results
    )

    print_results(
        hybrid_results
    )

    print()
    print("=" * 80)

    print(
        "Hybrid results saved to:"
    )

    print(
        OUTPUT_FILE
    )

    print()
    print(
        "No LLM was used."
    )

    print(
        "These are retrieval candidates only."
    )

    print("=" * 80)


if __name__ == "__main__":
    main()