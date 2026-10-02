# Optional Evidence-Grounded Summary Extension

## Current status

This is a **future design note**, not an implemented version-one feature. The current project ends
at evaluated retrieval, topic monitoring, SQL analytics, and the local Power BI report.

The extension must not be called complete until it has a selected model/provider, privacy review,
grounding tests, citation checks, cost and latency measurements, and a safe refusal path.

## What RAG would add

Retrieval-Augmented Generation would convert an analyst question into a concise explanation based
on already calculated results and retrieved evidence.

```text
Analyst question
      |
      v
Intent and filter parsing
      |
      +---------------------+
      |                     |
      v                     v
Verified analytical data   Relevant complaint evidence
      |                     |
      +----------+----------+
                 v
        Evidence package with IDs
                 |
                 v
     Constrained summary + citations
```

It would explain evidence; it would not replace classification, retrieval, clustering, anomaly
detection, or SQL calculations.

## Example question

> Which complaint themes showed persistent unusual growth during the final month, and what evidence
> supports that conclusion?

A valid answer would need to cite the alert week, topic ID, observed share, historical median,
robust z-score, persistence count, and supporting complaint identifiers. It must also state that
the signal is retrospective and not proof of harm or causation.

## Required prerequisites

Before implementation:

1. create a human-labelled retrieval set rather than relying only on product agreement;
2. compare the sparse TF-IDF baseline with at least one dense embedding model;
3. define which metadata and excerpts may be supplied to an external model;
4. specify the allowed analytical claims and mandatory caveats;
5. create questions with known answers from verified SQL results;
6. define citation completeness, faithfulness, refusal, latency, and cost targets.

## Proposed evidence contract

Every retrieved item should include:

- source type: complaint metadata, alert record, topic metric, or model metric;
- complaint or analytical identifier;
- relevant date or monitoring week;
- exact calculated values used by the answer;
- source artifact version or hash;
- permission classification;
- a short permitted excerpt only when privacy review allows it.

The generator should receive a bounded evidence package, not unrestricted access to raw project
files.

## Response rules

The summary layer should:

- answer only from supplied evidence;
- cite every material quantitative statement;
- distinguish observed data, model output, and analyst interpretation;
- refuse when evidence is missing, contradictory, or outside scope;
- avoid legal, causal, institution-quality, prevalence, or customer-harm conclusions;
- never make lending, pricing, eligibility, enforcement, or escalation decisions.

## Evaluation plan

| Dimension | Example check |
|---|---|
| Retrieval relevance | Human-labelled relevance at k |
| Citation completeness | Share of factual claims linked to supporting evidence |
| Citation correctness | Whether the cited record actually supports the claim |
| Numerical fidelity | Exact match with SQL or exported analytical values |
| Faithfulness | Unsupported-claim rate |
| Refusal quality | Safe handling of unanswerable or prohibited questions |
| Stability | Similar evidence produces materially consistent answers |
| Privacy | No unapproved narrative or personal information leaves the boundary |
| Operations | Latency, token use, and cost per question |

An attractive demonstration is not sufficient evidence of quality.

## Why it remains future work

The current retrieval metric uses product-label agreement as a proxy rather than human semantic
judgement. Adding a language model now would create a fluent interface over evidence whose
retrieval quality is not yet evaluated strongly enough. Keeping RAG outside version one is a
deliberate quality and privacy decision.

## Interview defense

**Why did you not add an LLM just to make the project look modern?**

The core problem is reliable evidence generation. A language model cannot repair leakage, weak
retrieval, unstable topics, or invalid anomaly logic. I completed and evaluated those foundations
first and kept RAG as a gated extension.

**What would make you comfortable implementing it?**

A privacy-approved evidence contract, human relevance labels, a dense-versus-sparse retrieval
comparison, grounded question-answer tests, citation validation, and explicit refusal behavior.

