from pathlib import Path
from typing import List, TypedDict

from dotenv import load_dotenv

from llama_index.core import Settings, StorageContext, load_index_from_storage
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from langgraph.graph import StateGraph, END


# =======================================================
# 1. PROJECT PATHS
# =======================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENV_PATH = PROJECT_ROOT / ".env"

# IMPORTANT:
# Use the clean text index, not the original dirty PDF index.
INDEX_DIR = PROJECT_ROOT / "storage" / "tjx_clean_text_index"

OUTPUT_DIR = PROJECT_ROOT / "03_Extracted_Text"
OUTPUT_PATH = OUTPUT_DIR / "tjx_langgraph_esg_agent_result.txt"

OUTPUT_DIR.mkdir(exist_ok=True)


# =======================================================
# 2. LOAD ENVIRONMENT VARIABLES
# =======================================================

load_dotenv(dotenv_path=ENV_PATH)

ANTHROPIC_API_KEY = None

import os
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

print("PROJECT_ROOT:", PROJECT_ROOT)
print("ENV_PATH:", ENV_PATH)
print("ENV_EXISTS:", ENV_PATH.exists())
print("ANTHROPIC_KEY_LOADED:", bool(ANTHROPIC_API_KEY))
print("INDEX_DIR:", INDEX_DIR)
print("INDEX_EXISTS:", INDEX_DIR.exists())


if not ANTHROPIC_API_KEY:
    raise ValueError(
        f"""
ANTHROPIC_API_KEY is missing.

Expected .env file here:
{ENV_PATH}

Your .env should contain:
ANTHROPIC_API_KEY=your_key_here
"""
    )


if not INDEX_DIR.exists():
    raise FileNotFoundError(
        f"""
Clean TJX index was not found.

Expected index folder:
{INDEX_DIR}

Before running this LangGraph agent, run:

python src/extract_clean_tjx_text.py
python src/build_tjx_clean_text_index.py

Then run this file again:

python src/langgraph_tjx_esg_agent.py
"""
    )


# =======================================================
# 3. CONFIGURE MODELS
# =======================================================

# Claude model:
# Use Haiku for speed and cost while testing.
# You already confirmed this model is available for your key.
Settings.llm = Anthropic(
    model="claude-haiku-4-5-20251001",
    temperature=0
)

# Embeddings:
# Force local HuggingFace embeddings.
# This prevents LlamaIndex from trying OpenAI embeddings.
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)


# =======================================================
# 4. LOAD SAVED CLEAN INDEX
# =======================================================

print("\nLoading saved clean TJX index...")

storage_context = StorageContext.from_defaults(
    persist_dir=str(INDEX_DIR)
)

index = load_index_from_storage(
    storage_context=storage_context,
    embed_model=Settings.embed_model
)

print("Clean TJX index loaded successfully.")


# =======================================================
# 5. CREATE QUERY ENGINE
# =======================================================

# Keep similarity_top_k small for speed.
# Increase to 5 only when you need deeper evidence.
query_engine = index.as_query_engine(
    similarity_top_k=3,
    response_mode="compact"
)


# =======================================================
# 6. DEFINE LANGGRAPH STATE
# =======================================================

class ESGAgentState(TypedDict):
    question: str
    retrieved_answer: str
    source_evidence: List[str]
    risk_classification: str
    confidence_score: str
    human_review_required: bool
    exception_flags: List[str]
    final_answer: str


# =======================================================
# 7. NODE 1 — RETRIEVE EVIDENCE
# =======================================================

def retrieve_evidence(state: ESGAgentState) -> ESGAgentState:
    print("\nNODE 1: Retrieving clean evidence from TJX report...")

    question = state["question"]

    response = query_engine.query(question)

    retrieved_answer = str(response)

    source_evidence = []

    if hasattr(response, "source_nodes") and response.source_nodes:
        for i, source_node in enumerate(response.source_nodes, start=1):
            content = source_node.node.get_content()

            # Keep evidence readable and not too long.
            evidence_text = content[:2500]

            source_evidence.append(
                f"Evidence Chunk {i}:\n{evidence_text}"
            )

    else:
        source_evidence.append("No source nodes returned by retriever.")

    state["retrieved_answer"] = retrieved_answer
    state["source_evidence"] = source_evidence

    return state


# =======================================================
# 8. NODE 2 — CLASSIFY ESG RISK / REVIEW NEED
# =======================================================

def classify_esg_risk(state: ESGAgentState) -> ESGAgentState:
    print("\nNODE 2: Classifying ESG risk and review need...")

    text = (
        state["retrieved_answer"] + "\n" +
        "\n".join(state["source_evidence"])
    ).lower()

    exception_flags = []

    # -------------------------------
    # Topic / risk indicators
    # -------------------------------

    forward_looking_keywords = [
        "aim", "goal", "target", "commitment", "plan",
        "expect", "future", "intend", "seek", "strive",
        "net zero", "renewable energy", "divert"
    ]

    quantitative_keywords = [
        "%", "percent", "metric tons", "tonnes", "tco2e",
        "mwh", "kwh", "scope 1", "scope 2", "scope 3",
        "emissions", "waste", "water", "energy"
    ]

    assurance_keywords = [
        "assurance", "assured", "verified", "verification",
        "limited assurance", "reasonable assurance",
        "third-party", "independent"
    ]

    vague_keywords = [
        "support", "help", "contribute", "promote",
        "engage", "encourage", "where possible"
    ]

    # -------------------------------
    # Exception flags
    # -------------------------------

    if any(word in text for word in forward_looking_keywords):
        exception_flags.append("Forward-looking ESG claim or target")

    if any(word in text for word in quantitative_keywords):
        exception_flags.append("Quantitative ESG metric or performance claim")

    if not any(word in text for word in assurance_keywords):
        exception_flags.append("Assurance status not confirmed in retrieved evidence")

    if any(word in text for word in vague_keywords):
        exception_flags.append("Narrative or qualitative ESG claim")

    if "no source nodes returned" in text:
        exception_flags.append("Missing source evidence")

    # -------------------------------
    # Risk classification
    # -------------------------------

    if "missing source evidence" in [flag.lower() for flag in exception_flags]:
        risk_classification = "High review risk"
        confidence_score = "Low"
        human_review_required = True

    elif "Forward-looking ESG claim or target" in exception_flags:
        risk_classification = "Medium to high review risk"
        confidence_score = "Medium"
        human_review_required = True

    elif "Quantitative ESG metric or performance claim" in exception_flags:
        risk_classification = "Medium review risk"
        confidence_score = "Medium"
        human_review_required = True

    else:
        risk_classification = "Lower review risk"
        confidence_score = "Medium"
        human_review_required = False

    state["risk_classification"] = risk_classification
    state["confidence_score"] = confidence_score
    state["human_review_required"] = human_review_required
    state["exception_flags"] = exception_flags

    return state


# =======================================================
# 9. NODE 3 — WRITE FINAL CONSULTANT-STYLE ANSWER
# =======================================================

def write_final_answer(state: ESGAgentState) -> ESGAgentState:
    print("\nNODE 3: Writing final ESG consultant-style output...")

    review_status = (
        "Human review required"
        if state["human_review_required"]
        else "Human review not required for initial screening"
    )

    exception_flags_text = "\n".join(
        [f"- {flag}" for flag in state["exception_flags"]]
    )

    source_evidence_text = "\n\n".join(state["source_evidence"])

    final_answer = f"""
TJX ESG Evidence Review — LangGraph Agent Output

==================================================
USER QUESTION
==================================================

{state["question"]}


==================================================
RETRIEVED ANSWER
==================================================

{state["retrieved_answer"]}


==================================================
RISK CLASSIFICATION
==================================================

{state["risk_classification"]}


==================================================
CONFIDENCE SCORE
==================================================

{state["confidence_score"]}


==================================================
HUMAN-IN-THE-LOOP REVIEW STATUS
==================================================

{review_status}


==================================================
EXCEPTION FLAGS
==================================================

{exception_flags_text if exception_flags_text else "- No major exception flags identified"}


==================================================
SOURCE EVIDENCE
==================================================

{source_evidence_text}


==================================================
CONSULTANT INTERPRETATION
==================================================

This workflow retrieved ESG-related evidence from the cleaned TJX corporate responsibility report index,
classified the evidence for reporting and review risk, and identified whether human review is needed.

The output should not be treated as final disclosure language. It is an evidence-review and triage layer.
For audit-ready ESG reporting, the next step would be to connect each claim or metric to:

1. source evidence,
2. reporting boundary,
3. calculation methodology,
4. assurance status,
5. validation rules,
6. exception flags,
7. human approval,
8. audit trail.

This is consistent with a governed ESG Data and AI workflow where AI accelerates evidence retrieval
and classification, but humans remain responsible for final reporting decisions.
"""

    state["final_answer"] = final_answer

    return state


# =======================================================
# 10. BUILD LANGGRAPH WORKFLOW
# =======================================================

workflow = StateGraph(ESGAgentState)

workflow.add_node("retrieve_evidence", retrieve_evidence)
workflow.add_node("classify_esg_risk", classify_esg_risk)
workflow.add_node("write_final_answer", write_final_answer)

workflow.set_entry_point("retrieve_evidence")

workflow.add_edge("retrieve_evidence", "classify_esg_risk")
workflow.add_edge("classify_esg_risk", "write_final_answer")
workflow.add_edge("write_final_answer", END)

app = workflow.compile()


# =======================================================
# 11. RUN THE AGENT
# =======================================================

if __name__ == "__main__":

    input_state: ESGAgentState = {
        "question": """
Review TJX sustainability disclosures and identify evidence related to climate,
energy, emissions, renewable energy, waste, supply chain, governance, human capital,
community impact, and environmental initiatives.

Classify whether the retrieved evidence appears quantitative, qualitative,
forward-looking, assured, or requiring human review.
""",
        "retrieved_answer": "",
        "source_evidence": [],
        "risk_classification": "",
        "confidence_score": "",
        "human_review_required": False,
        "exception_flags": [],
        "final_answer": ""
    }

    print("\nRunning LangGraph ESG evidence agent...")

    result = app.invoke(input_state)

    print("\n==================================================")
    print("FINAL LANGGRAPH ESG AGENT RESULT")
    print("==================================================\n")

    print(result["final_answer"])

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(result["final_answer"])

    print("\nResult saved to:")
    print(OUTPUT_PATH)