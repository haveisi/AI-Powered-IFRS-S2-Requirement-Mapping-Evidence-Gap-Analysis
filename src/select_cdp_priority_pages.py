import json
import re
from collections import defaultdict
from pathlib import Path


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "03_Extracted_Text"
    / "TJX_2025_CDP_Climate_Response.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "03_Extracted_Text"
    / "TJX_CDP_priority_pages.json"
)


# =========================================================
# REQUIREMENT SEARCH PROFILES
# =========================================================

SEARCH_PROFILES = {
    "S2-GOV-02": {
        "topic": "Board climate oversight",
        "high_weight": [
            "board of directors",
            "board committee",
            "climate oversight",
            "climate-related oversight",
            "governing body",
            "board oversight",
        ],
        "medium_weight": [
            "board",
            "committee",
            "governance",
            "oversight",
            "responsibility",
            "climate-related risks",
        ],
        "low_weight": [
            "management",
            "executive",
            "reporting line",
            "frequency",
        ],
    },

    "S2-STR-06": {
        "topic": "Climate resilience and scenario analysis",
        "high_weight": [
            "scenario analysis",
            "climate scenario",
            "climate-related scenario analysis",
            "1.5°c",
            "1.5 c",
            "2°c",
            "2 c",
            "resilience assessment",
        ],
        "medium_weight": [
            "physical risk",
            "transition risk",
            "climate resilience",
            "warming scenario",
            "time horizon",
            "temperature pathway",
            "scenario",
        ],
        "low_weight": [
            "iea",
            "ngfs",
            "rcp",
            "ssp",
            "acute physical risk",
            "chronic physical risk",
        ],
    },

    "S2-MT-01": {
        "topic": "Scope 1 emissions",
        "high_weight": [
            "scope 1 emissions",
            "scope 1",
            "gross scope 1",
            "direct emissions",
        ],
        "medium_weight": [
            "metric tons co2e",
            "metric tonnes co2e",
            "tco2e",
            "ghg protocol",
            "greenhouse gas emissions",
        ],
        "low_weight": [
            "emission factors",
            "organizational boundary",
            "consolidation approach",
            "activity data",
        ],
    },

    "S2-MT-02": {
        "topic": "Scope 2 emissions",
        "high_weight": [
            "scope 2 emissions",
            "scope 2",
            "gross scope 2",
            "market-based",
            "location-based",
        ],
        "medium_weight": [
            "purchased electricity",
            "electricity consumption",
            "renewable electricity",
            "metric tons co2e",
            "metric tonnes co2e",
        ],
        "low_weight": [
            "contractual instruments",
            "renewable energy certificates",
            "energy attribute certificates",
            "emission factors",
        ],
    },

    "S2-MT-04": {
        "topic": "Climate-related targets",
        "high_weight": [
            "net zero",
            "55% absolute reduction",
            "100% renewable",
            "2030",
            "2040",
            "target year",
            "baseline year",
        ],
        "medium_weight": [
            "climate target",
            "emissions target",
            "renewable energy target",
            "target progress",
            "progress against target",
            "baseline",
        ],
        "low_weight": [
            "sbti",
            "validation",
            "interim target",
            "offset",
            "removal",
            "target methodology",
        ],
    },
}


# =========================================================
# SETTINGS
# =========================================================

HIGH_WEIGHT_SCORE = 5
MEDIUM_WEIGHT_SCORE = 3
LOW_WEIGHT_SCORE = 1

MIN_PAGE_SCORE = 4

MAX_PAGES_PER_REQUIREMENT = 8

MAX_TOTAL_PAGES = 30


# =========================================================
# LOAD DATA
# =========================================================

def load_pages(path: Path) -> list[dict]:

    if not path.exists():
        raise FileNotFoundError(
            f"Input JSON not found:\n{path}"
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
# TEXT NORMALIZATION
# =========================================================

def normalize_for_search(text: str) -> str:

    text = text.lower()

    text = text.replace("–", "-")
    text = text.replace("—", "-")

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# =========================================================
# SCORING
# =========================================================

def phrase_count(
    text: str,
    phrase: str,
) -> int:

    return text.count(
        phrase.lower()
    )


def score_page(
    text: str,
    profile: dict,
) -> tuple[int, list[dict]]:

    score = 0

    matches = []

    for phrase in profile["high_weight"]:

        count = phrase_count(
            text,
            phrase,
        )

        if count > 0:

            contribution = (
                HIGH_WEIGHT_SCORE
                * count
            )

            score += contribution

            matches.append(
                {
                    "phrase": phrase,
                    "weight": "high",
                    "count": count,
                    "score": contribution,
                }
            )

    for phrase in profile["medium_weight"]:

        count = phrase_count(
            text,
            phrase,
        )

        if count > 0:

            contribution = (
                MEDIUM_WEIGHT_SCORE
                * count
            )

            score += contribution

            matches.append(
                {
                    "phrase": phrase,
                    "weight": "medium",
                    "count": count,
                    "score": contribution,
                }
            )

    for phrase in profile["low_weight"]:

        count = phrase_count(
            text,
            phrase,
        )

        if count > 0:

            contribution = (
                LOW_WEIGHT_SCORE
                * count
            )

            score += contribution

            matches.append(
                {
                    "phrase": phrase,
                    "weight": "low",
                    "count": count,
                    "score": contribution,
                }
            )

    return score, matches


# =========================================================
# REQUIREMENT SEARCH
# =========================================================

def search_requirement(
    pages: list[dict],
    requirement_id: str,
    profile: dict,
) -> list[dict]:

    results = []

    for page in pages:

        text = normalize_for_search(
            page.get(
                "text",
                "",
            )
        )

        score, matches = score_page(
            text,
            profile,
        )

        if score < MIN_PAGE_SCORE:
            continue

        results.append(
            {
                "requirement_id":
                    requirement_id,

                "requirement_topic":
                    profile["topic"],

                "document_name":
                    page["document_name"],

                "page_number":
                    page["page_number"],

                "score":
                    score,

                "matches":
                    matches,

                "text_preview":
                    page["text"][:700],
            }
        )

    results.sort(
        key=lambda x: (
            -x["score"],
            x["page_number"],
        )
    )

    return results[
        :MAX_PAGES_PER_REQUIREMENT
    ]


# =========================================================
# COMBINE RESULTS
# =========================================================

def build_priority_set(
    requirement_results: dict,
) -> list[dict]:

    page_index = {}

    for requirement_id, results in (
        requirement_results.items()
    ):

        for result in results:

            page_number = (
                result["page_number"]
            )

            if page_number not in page_index:

                page_index[
                    page_number
                ] = {
                    "page_number":
                        page_number,

                    "document_name":
                        result[
                            "document_name"
                        ],

                    "total_score": 0,

                    "requirements": [],

                    "requirement_scores":
                        {},

                    "matched_phrases":
                        [],
                }

            page_record = page_index[
                page_number
            ]

            page_record[
                "total_score"
            ] += result["score"]

            page_record[
                "requirements"
            ].append(
                requirement_id
            )

            page_record[
                "requirement_scores"
            ][
                requirement_id
            ] = result["score"]

            for match in result[
                "matches"
            ]:

                phrase = match[
                    "phrase"
                ]

                if phrase not in (
                    page_record[
                        "matched_phrases"
                    ]
                ):

                    page_record[
                        "matched_phrases"
                    ].append(
                        phrase
                    )

    combined = list(
        page_index.values()
    )

    combined.sort(
        key=lambda x: (
            -len(
                x["requirements"]
            ),
            -x["total_score"],
            x["page_number"],
        )
    )

    return combined[
        :MAX_TOTAL_PAGES
    ]


# =========================================================
# PAGE TEXT LOOKUP
# =========================================================

def add_page_text(
    priority_pages: list[dict],
    pages: list[dict],
) -> list[dict]:

    lookup = {
        page["page_number"]: page
        for page in pages
    }

    final = []

    for record in priority_pages:

        page_number = record[
            "page_number"
        ]

        source_page = lookup[
            page_number
        ]

        final_record = {
            **record,

            "character_count":
                source_page[
                    "character_count"
                ],

            "text":
                source_page[
                    "text"
                ],
        }

        final.append(
            final_record
        )

    return final


# =========================================================
# SAVE
# =========================================================

def save_json(
    data: list[dict],
    path: Path,
) -> None:

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


# =========================================================
# REPORT
# =========================================================

def print_requirement_results(
    requirement_results: dict,
) -> None:

    print()
    print("=" * 78)
    print(
        "CDP REQUIREMENT SEARCH RESULTS"
    )
    print("=" * 78)

    for requirement_id, results in (
        requirement_results.items()
    ):

        print()
        print(
            f"{requirement_id} — "
            f"{SEARCH_PROFILES[requirement_id]['topic']}"
        )

        print("-" * 78)

        if not results:

            print(
                "No pages met the minimum score."
            )

            continue

        for result in results:

            phrases = [
                item["phrase"]
                for item in result[
                    "matches"
                ][:6]
            ]

            print(
                f"Page "
                f"{result['page_number']:>3} "
                f"| Score "
                f"{result['score']:>3} "
                f"| "
                f"{', '.join(phrases)}"
            )


def print_priority_pages(
    priority_pages: list[dict],
) -> None:

    print()
    print("=" * 78)
    print(
        "FINAL PRIORITY PAGE SET"
    )
    print("=" * 78)

    print(
        f"Unique priority pages: "
        f"{len(priority_pages)}"
    )

    print()

    for record in priority_pages:

        requirements = ", ".join(
            record["requirements"]
        )

        print(
            f"Page "
            f"{record['page_number']:>3}"
            f" | Total score "
            f"{record['total_score']:>3}"
            f" | {requirements}"
        )


# =========================================================
# MAIN
# =========================================================

def main() -> None:

    print()
    print(
        "Loading TJX CDP page corpus..."
    )

    pages = load_pages(
        INPUT_FILE
    )

    print(
        f"Pages loaded: "
        f"{len(pages)}"
    )

    requirement_results = {}

    for requirement_id, profile in (
        SEARCH_PROFILES.items()
    ):

        requirement_results[
            requirement_id
        ] = search_requirement(
            pages=pages,
            requirement_id=
                requirement_id,
            profile=profile,
        )

    print_requirement_results(
        requirement_results
    )

    priority_pages = (
        build_priority_set(
            requirement_results
        )
    )

    priority_pages = add_page_text(
        priority_pages,
        pages,
    )

    save_json(
        priority_pages,
        OUTPUT_FILE,
    )

    print_priority_pages(
        priority_pages
    )

    print()
    print(
        "Saved priority pages to:"
    )

    print(
        OUTPUT_FILE
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "These pages are retrieval "
        "candidates, not approved evidence."
    )

    print()


if __name__ == "__main__":
    main()