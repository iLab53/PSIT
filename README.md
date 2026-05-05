# STRATEGIST — Market Intelligence Validation Agent

STRATEGIST is a multi-agent pipeline that validates, grades, and reviews
market intelligence signals before they reach strategic decision-makers.

## Architecture

Phase 1  →  Parallel collection + evidence grading (ThreadPoolExecutor)
Phase 2  →  Sequential HITL review (one region at a time)
Phase 3  →  Parallel adversarial review + CHALLENGE feedback loop
Output   →  JSON audit report + Haiku executive summary

## Setup

    python -m venv .venv && source .venv/bin/activate
    pip install anthropic pytest
    export ANTHROPIC_API_KEY=sk-ant-...

## Usage

    # Run the pipeline (AUTO_APPROVE=True for demo)
    python strategist_hello.py

    # Run the test suite
    pytest test_pipeline.py -v

## Key Files

    strategist_hello.py      — coordinator() entry point
    hitl_gate.py             — HITL review gate (AUTO_APPROVE flag)
    adversarial_reviewer.py  — adversarial review + CHALLENGE loop
    evidence_grader.py       — A/B/C/D rubric scoring
    source_validator.py      — TIER_1/2/3 source classification
    confidence_scorer.py     — confidence scoring with TIER_3 cap
    deduplicator.py          — cross-region signal deduplication
    output_formatter.py      — JSON report + exec summary writer
    test_pipeline.py         — 42-assertion pytest suite
    reports/                 — auto-created; JSON reports written here

## Environment Variables

    ANTHROPIC_API_KEY        — required; used by adversarial_reviewer.py
                               and output_formatter.py

## Extending the Pipeline

  Add a region: append to REGIONS list in strategist_hello.py
  Change models: edit MODEL_GENERATION / MODEL_EVALUATION constants
  Disable HITL: set AUTO_APPROVE = True in hitl_gate.py (tests only)
  Increase iteration cap: edit MAX_ITERATIONS in adversarial_reviewer.py
