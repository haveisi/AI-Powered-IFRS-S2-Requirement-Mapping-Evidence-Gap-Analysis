import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "03_Extracted_Text"
    / "TJX_2025_Global_Corporate_Responsibility_Report.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "03_Extracted_Text"
    / "TJX_selected_relevant_pages_refined.json"
)


# ---------------------------------------------------------
# Weighted topic vocabulary
# ---------------------------------------------------------

TOPIC_KEYWORDS: dict[str, dict[str, int]] = {
    "climate_and_energy": {
        "scope 1": 5,
        "scope 2": 5,
        "scope 3": 5,
        "greenhouse gas emissions": 5,
        "ghg emissions": 5,
        "carbon emissions": 4,
        "renewable electricity": 4,
        "renewable energy": 4,
        "energy efficiency": 4,
        "science-based target": 5,
        "climate risk": 4,
        "climate change": 3,
        "decarbonization": 4,
        "net zero": 5,
        "electricity": 2,
        "energy": 1,
        "emissions": 2,
        "carbon": 1,
    },

    "waste_and_circularity": {
        "waste diversion": 5,
        "waste reduction": 4,
        "recycled content": 5,
        "circular economy": 5,
        "textile waste": 5,
        "packaging waste": 4,
        "reusable packaging": 4,
        "landfill diversion": 5,
        "recycling": 3,
        "reuse": 3,
        "packaging": 2,
        "waste": 2,
        "plastic": 2,
        "circular": 3,
        "landfill": 3,
    },

    "supply_chain": {
        "responsible sourcing": 5,
        "supplier code of conduct": 5,
        "factory audit": 5,
        "social compliance audit": 5,
        "forced labor": 5,
        "child labor": 5,
        "human rights due diligence": 5,
        "supply chain traceability": 5,
        "vendor standards": 4,
        "supplier engagement": 4,
        "sourcing practices": 4,
        "supply chain": 4,
        "manufacturing facility": 3,
        "factory": 2,
        "supplier": 2,
        "vendor": 2,
        "sourcing": 2,
        "procurement": 2,
        "audit": 1,
    },

    "workforce_and_diversity": {
        "employee engagement": 4,
        "associate engagement": 4,
        "leadership development": 4,
        "talent development": 4,
        "health and safety": 5,
        "occupational safety": 5,
        "diversity and inclusion": 5,
        "diversity, equity and inclusion": 5,
        "racial and ethnic": 4,
        "gender representation": 4,
        "workforce diversity": 5,
        "employee retention": 4,
        "associate retention": 4,
        "training hours": 4,
        "career development": 4,
        "employee": 1,
        "associate": 1,
        "workforce": 2,
        "diversity": 3,
        "inclusion": 3,
        "training": 2,
        "leadership": 2,
        "safety": 2,
    },

    "governance_and_ethics": {
        "board oversight": 5,
        "board of directors": 4,
        "corporate governance": 5,
        "ethics and compliance": 5,
        "code of conduct": 5,
        "enterprise risk management": 5,
        "risk oversight": 5,
        "audit committee": 5,
        "executive compensation": 4,
        "whistleblower": 4,
        "anti-corruption": 5,
        "anti-bribery": 5,
        "governance structure": 4,
        "compliance program": 4,
        "board": 2,
        "committee": 2,
        "ethics": 3,
        "compliance": 2,
        "governance": 3,
        "risk": 1,
    },

    "community_and_social_impact": {
        "community investment": 5,
        "charitable giving": 5,
        "employee volunteering": 4,
        "associate volunteering": 4,
        "philanthropic support": 4,
        "social impact": 4,
        "nonprofit organizations": 4,
        "community partnership": 4,
        "foundation": 3,
        "philanthropy": 3,
        "donation": 3,
        "volunteer": 3,
        "community": 2,
        "charitable": 3,
    },

    "water_and_nature": {
        "water stewardship": 5,
        "water consumption": 4,
        "water withdrawal": 5,
        "water stress": 5,
        "biodiversity impact": 5,
        "deforestation-free": 5,
        "forest conservation": 4,
        "nature-related risk": 5,
        "ecosystem protection": 4,
        "land use": 3,
        "biodiversity": 4,
        "deforestation": 4,
        "water": 2,
        "forest": 2,
        "nature": 2,
        "ecosystem": 3,
    },

    "targets_and_metrics": {
        "baseline year": 4,
        "target year": 4,
        "performance target": 4,
        "annual target": 3,
        "progress against target": 5,
        "percentage reduction": 4,
        "metric tons": 4,
        "metric tonnes": 4,
        "tco2e": 5,
        "mwh": 4,
        "kwh": 4,
        "fiscal year 2025": 3,
        "fiscal year 2024": 3,
        "baseline": 2,
        "target": 2,
        "goal": 2,
        "progress": 2,
        "metric": 2,
        "performance": 1,
        "percentage": 1,
    },
}


# ---------------------------------------------------------
# Load input pages
# ---------------------------------------------------------

def load_pages() -> list[dict[str, Any]]:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        pages = json.load(file)

    if not isinstance(pages, list):
        raise ValueError(
            "The extracted-text file must contain a list of page records."
        )

    return pages


# ---------------------------------------------------------
# Text normalization
# ---------------------------------------------------------

def normalize_for_search(text: str) -> str:
    text = text.lower()
    text = text.replace("\u2013", "-")
    text = text.replace("\u2014", "-")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------------------------------------------------
# Detect pages that should not control extraction
# ---------------------------------------------------------

def is_navigation_or_reference_page(text: str) -> bool:
    """
    Detect likely contents, index, reference, or navigation-heavy pages.
    """

    normalized = normalize_for_search(text)

    navigation_markers = [
        "table of contents",
        "contents",
        "about this report",
        "index",
        "sasb index",
        "gri index",
        "sdg index",
        "forward-looking statements",
    ]

    marker_hits = sum(
        marker in normalized
        for marker in navigation_markers
    )

    # Many short lines often indicate a contents or index page.
    original_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    short_lines = sum(
        len(line) <= 45
        for line in original_lines
    )

    short_line_ratio = (
        short_lines / len(original_lines)
        if original_lines
        else 0
    )

    return (
        marker_hits >= 1
        or short_line_ratio > 0.80
    )


# ---------------------------------------------------------
# Keyword matching
# ---------------------------------------------------------

def contains_keyword(
    normalized_text: str,
    keyword: str,
) -> bool:
    normalized_keyword = normalize_for_search(keyword)

    if " " in normalized_keyword:
        return normalized_keyword in normalized_text

    pattern = rf"\b{re.escape(normalized_keyword)}\b"

    return bool(
        re.search(
            pattern,
            normalized_text,
        )
    )


# ---------------------------------------------------------
# Page scoring
# ---------------------------------------------------------

def score_page(
    page: dict[str, Any],
) -> dict[str, Any]:
    source_text = page.get("text", "")
    normalized_text = normalize_for_search(source_text)

    navigation_page = is_navigation_or_reference_page(
        source_text
    )

    topic_scores: dict[str, int] = {}
    matched_keywords: dict[str, list[str]] = {}

    for topic, weighted_keywords in TOPIC_KEYWORDS.items():
        score = 0
        matches: list[str] = []

        for keyword, weight in weighted_keywords.items():
            if contains_keyword(
                normalized_text,
                keyword,
            ):
                score += weight
                matches.append(keyword)

        # Require multiple signals for a meaningful topic.
        if len(matches) < 2:
            score = 0
            matches = []

        topic_scores[topic] = score
        matched_keywords[topic] = matches

    ranked_topics = sorted(
        topic_scores,
        key=lambda topic: topic_scores[topic],
        reverse=True,
    )

    primary_topic = None
    secondary_topics: list[str] = []

    if ranked_topics and topic_scores[ranked_topics[0]] > 0:
        primary_topic = ranked_topics[0]
        primary_score = topic_scores[primary_topic]

        secondary_topics = [
            topic
            for topic in ranked_topics[1:]
            if topic_scores[topic] >= 5
            and topic_scores[topic] >= primary_score * 0.50
        ]

    total_score = sum(
        score
        for score in topic_scores.values()
        if score >= 5
    )

    if navigation_page:
        total_score = 0

    return {
        "source_document": page.get("source_document"),
        "pdf_page_number": page.get("pdf_page_number"),
        "character_count": page.get("character_count"),
        "requires_review": page.get("requires_review"),
        "navigation_or_reference_page": navigation_page,
        "relevance_score": total_score,
        "primary_topic": primary_topic,
        "secondary_topics": secondary_topics,
        "topic_scores": topic_scores,
        "matched_keywords": matched_keywords,
        "text": source_text,
    }


# ---------------------------------------------------------
# Balanced page selection
# ---------------------------------------------------------

def select_balanced_pages(
    scored_pages: list[dict[str, Any]],
    maximum_pages: int = 20,
    maximum_per_primary_topic: int = 4,
    minimum_relevance_score: int = 6,
) -> list[dict[str, Any]]:
    """
    Select pages while preventing one topic from dominating.
    """

    eligible_pages = [
        page
        for page in scored_pages
        if page["relevance_score"] >= minimum_relevance_score
        and not page.get("requires_review", False)
        and not page.get("navigation_or_reference_page", False)
        and page.get("primary_topic") is not None
    ]

    eligible_pages.sort(
        key=lambda page: (
            page["relevance_score"],
            page["character_count"] or 0,
        ),
        reverse=True,
    )

    selected_pages: list[dict[str, Any]] = []
    topic_counts: Counter[str] = Counter()

    for page in eligible_pages:
        primary_topic = page["primary_topic"]

        if topic_counts[primary_topic] >= maximum_per_primary_topic:
            continue

        selected_pages.append(page)
        topic_counts[primary_topic] += 1

        if len(selected_pages) >= maximum_pages:
            break

    return selected_pages


# ---------------------------------------------------------
# Save results
# ---------------------------------------------------------

def save_selected_pages(
    selected_pages: list[dict[str, Any]],
) -> None:
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            selected_pages,
            file,
            ensure_ascii=False,
            indent=2,
        )


# ---------------------------------------------------------
# Print summary
# ---------------------------------------------------------

def print_summary(
    scored_pages: list[dict[str, Any]],
    selected_pages: list[dict[str, Any]],
) -> None:
    print("=" * 78)
    print("TJX ESG REFINED PAGE-SELECTION SUMMARY")
    print("=" * 78)

    navigation_pages = sum(
        page["navigation_or_reference_page"]
        for page in scored_pages
    )

    print(
        f"Total pages reviewed: {len(scored_pages)}"
    )

    print(
        f"Navigation/reference pages excluded: {navigation_pages}"
    )

    print(
        f"Pages selected: {len(selected_pages)}"
    )

    primary_topic_counts = Counter(
        page["primary_topic"]
        for page in selected_pages
    )

    print("\nPrimary-topic coverage:")

    for topic, count in primary_topic_counts.most_common():
        print(
            f"- {topic}: {count} page(s)"
        )

    print("\nSelected pages:")

    for page in selected_pages:
        secondary = (
            ", ".join(page["secondary_topics"])
            if page["secondary_topics"]
            else "None"
        )

        primary_matches = page["matched_keywords"].get(
            page["primary_topic"],
            [],
        )

        print(
            f"- PDF page {page['pdf_page_number']}: "
            f"score={page['relevance_score']}, "
            f"primary={page['primary_topic']}, "
            f"secondary={secondary}, "
            f"characters={page['character_count']:,}"
        )

        print(
            f"  Primary matches: "
            f"{', '.join(primary_matches)}"
        )

    print("\nOutput saved to:")
    print(OUTPUT_FILE)

    print("=" * 78)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main() -> None:
    pages = load_pages()

    scored_pages = [
        score_page(page)
        for page in pages
    ]

    selected_pages = select_balanced_pages(
        scored_pages=scored_pages,
        maximum_pages=20,
        maximum_per_primary_topic=4,
        minimum_relevance_score=6,
    )

    if not selected_pages:
        raise RuntimeError(
            "No pages met the refined selection rules."
        )

    save_selected_pages(
        selected_pages
    )

    print_summary(
        scored_pages=scored_pages,
        selected_pages=selected_pages,
    )


if __name__ == "__main__":
    main()