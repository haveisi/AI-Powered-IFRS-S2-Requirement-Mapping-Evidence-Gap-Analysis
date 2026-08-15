# AI-Powered IFRS S2 Requirement Mapping & Evidence Gap Analysis

This project explores how AI can support sustainability disclosure review by helping analysts find relevant evidence, map it to IFRS S2 requirements, identify disclosure gaps, and turn the results into an actionable readiness assessment.

I developed the workflow using publicly available TJX sustainability and climate disclosures as a practical case study. The goal was not to automate compliance decisions, but to test how AI, deterministic validation, and human review can work together to make disclosure analysis more structured, traceable, and efficient.

## Why I Built This

Sustainability reports often contain a large amount of useful information, but the evidence needed for a specific disclosure requirement may be spread across different reports, pages, metrics, governance discussions, and methodologies.

A traditional review can require significant manual searching and interpretation.

This project asks a practical question:

**Can AI help retrieve and organize the right evidence while keeping the final disclosure judgment with a human reviewer?**

The workflow was designed around that principle.

## How the Workflow Works

```text
Public sustainability and climate disclosures
                    ↓
             PDF extraction
                    ↓
       Keyword + semantic retrieval
                    ↓
        LlamaIndex vector retrieval
                    ↓
      Claude-assisted evidence extraction
                    ↓
      Pydantic / schema validation
                    ↓
         Exact-quote validation
                    ↓
       Repair of failed evidence
                    ↓
          Human-in-the-loop review
                    ↓
       IFRS S2 requirement mapping
                    ↓
      Requirement-level reassessment
                    ↓
         Disclosure gap analysis
                    ↓
          Management action plan
                    ↓
       Dashboard-ready reporting data
````

The AI is used to assist with retrieval, interpretation, and evidence structuring. Deterministic checks and human review are used to control quality before evidence is accepted.

## Pilot Scope

The current pilot focuses on five selected IFRS S2 disclosure areas:

* Board-level climate oversight
* Climate resilience and scenario analysis
* Scope 1 greenhouse gas emissions
* Scope 2 greenhouse gas emissions
* Climate-related targets

The project also began a separate review of management-level climate oversight evidence.

## What the Project Produced

The workflow brought together evidence from TJX's public corporate responsibility and CDP climate disclosures.

Key results from the pilot include:

* **64** combined evidence records
* **40** CDP evidence items sent through human review
* **39** CDP evidence items accepted after review
* **5** IFRS S2 pilot requirements reassessed
* Pilot readiness increased from **35% to 70%**
* **5** remaining disclosure gaps converted into an action plan
* **3** gaps identified as high priority

The 35% to 70% change reflects improved evidence discovery and reassessment against the five selected requirements. It should not be interpreted as an ISSB compliance score.

## Example of the Analysis

One of the strongest improvements occurred in Scope 1 and Scope 2 emissions.

The retrieval and review process identified evidence covering reported emissions, methodology, emission factors, activity breakdowns, and reporting approaches. That allowed the assessment to move beyond simply asking whether a number appeared in a sustainability report and instead evaluate whether the supporting disclosure evidence was sufficiently complete.

Scenario analysis remained one of the weaker areas.

TJX disclosed useful qualitative scenario-analysis information, but the review still identified gaps around enterprise-wide applicability, quantitative financial impacts, operational sensitivities, assumptions, uncertainty, and management response.

This distinction is important: **more evidence does not automatically mean complete disclosure coverage.**

## Human-in-the-Loop Design

A central part of this project is that the AI does not make the final disclosure determination.

Evidence moves through several controls:

1. Retrieval identifies potentially relevant pages.
2. The LLM extracts structured evidence and exact supporting quotations.
3. Deterministic validation checks the output structure and quotation match.
4. Failed quotations are routed for repair.
5. A human reviewer approves, corrects, rejects, or marks evidence as duplicate.
6. Requirement-level readiness is reassessed using the reviewed evidence.
7. Remaining gaps are translated into recommended actions.

This design helps reduce two common risks in AI-assisted disclosure work: unsupported claims and false-positive requirement matching.

## Technology

**Python**
Workflow automation, validation, evidence processing, and reporting outputs.

**LlamaIndex**
Document indexing and semantic retrieval.

**Embeddings**
Local semantic representation using `BAAI/bge-small-en-v1.5`.

**Hybrid Retrieval**
Combination of keyword and semantic search to improve evidence discovery.

**Claude**
Structured evidence extraction and interpretation.

**Pydantic**
Schema and output validation.

**LangGraph**
Explored as an orchestration layer for routing workflow steps and human-review checkpoints.

**Excel / CSV / Power BI-ready outputs**
Requirement summaries, gap action plans, KPI tables, and dashboard datasets.

## Repository Structure

```text
src/
    PDF extraction
    retrieval and indexing
    evidence extraction
    validation and repair
    human-review processing
    IFRS S2 mapping
    reassessment
    gap analysis
    dashboard-data preparation

06_Dashboard_Data/
    requirement summary
    readiness KPIs
    gap-priority summary

06_Framework_Libraries/
    IFRS S2 requirement library

07_Framework_Mapping/
    requirement-mapping workbooks
```

Source PDFs, local vector indexes, API credentials, extracted full text, and working evidence-review files are intentionally excluded from the public repository.

## What I Learned

The most important lesson from this project was that AI is more useful as an **evidence-navigation and analysis layer** than as an autonomous disclosure writer.

Semantic retrieval can reduce the effort required to search long sustainability reports. LLMs can help interpret and structure evidence. But reliable disclosure analysis still requires clear requirement definitions, traceability to source material, deterministic controls, and human judgment.

The project also reinforced the difference between three questions:

**Is relevant information present?**

**Does the information actually address the disclosure requirement?**

**What is still missing for a decision-useful disclosure?**

Those are different questions, and treating them separately makes the analysis much more useful.

## Next Development

The next stage is to expand the requirement library beyond the initial five-requirement pilot, strengthen management-level governance mapping, evaluate retrieval quality systematically, and connect the outputs to a Power BI disclosure-readiness dashboard.

The longer-term goal is a reusable architecture that can support sustainability teams in moving from manual report review toward structured, evidence-based disclosure intelligence.

## Important Note

This project is an independent applied research and portfolio exercise using publicly available information.

The readiness assessment covers a limited set of selected IFRS S2 requirements and is intended to demonstrate an analytical workflow. It is **not an audit, assurance engagement, legal opinion, or determination of TJX's compliance with IFRS Sustainability Disclosure Standards**.

```
```
