```
██╗     ███████╗ █████╗ ██████╗ ███╗   ██╗██╗      ██████╗  ██████╗██╗  ██╗
██║     ██╔════╝██╔══██╗██╔══██╗████╗  ██║██║     ██╔═══██╗██╔════╝██║ ██╔╝
██║     █████╗  ███████║██████╔╝██╔██╗ ██║██║     ██║   ██║██║     █████╔╝
██║     ██╔══╝  ██╔══██║██╔══██╗██║╚██╗██║██║     ██║   ██║██║     ██╔═██╗
███████╗███████╗██║  ██║██║  ██║██║ ╚████║███████╗╚██████╔╝╚██████╗██║  ██╗
╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝
```

> **The app that argues with you.**

LearnLock is a CLI learning tool that uses adversarial Socratic dialogue to expose gaps in your understanding. It doesn't quiz you — it _interrogates_ you.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [The Duel Engine](#the-duel-engine)
- [Claim Pipeline](#claim-pipeline)
- [Module Reference](#module-reference)
- [Database Schema](#database-schema)
- [Configuration](#configuration)
- [CLI Commands](#cli-commands)
- [Known Limitations](#known-limitations)
- [Development](#development)
- [License](#license)

---

## Installation

### From PyPI

Install using pip. Requires Python 3.11 or higher.

### From Source

Clone the repository and install in editable mode.

### Optional Dependencies

- `learnlock[ocr]` — EasyOCR for handwritten answer support
- `learnlock[whisper]` — Whisper fallback for YouTube videos without transcripts

---

## Quick Start

1. Set your API keys as environment variables:
   - `GROQ_API_KEY` (required) — Get free at console.groq.com
   - `GEMINI_API_KEY` (recommended) — Get free at aistudio.google.com

2. Launch the CLI by running `learnlock`

3. Add content by pasting a YouTube URL, article link, PDF path, or GitHub repo

4. Start studying with `/study`

5. Double Enter to send your answer

---

## How It Works

1. You explain a concept in your own words
2. The engine infers what you believe
3. It compares your belief against ground truth claims
4. It finds contradictions and attacks the weakest point
5. After 3 turns (or success), it reveals your belief trajectory
6. Your score feeds into SM-2 spaced repetition scheduling

---

## Architecture

```
Tools (youtube, article, pdf, github)
    │
    ▼
LLM ──▶ extract concepts & claims
    │
    ▼
Duel Engine ──▶ belief modeling, contradiction detection, interrogation
    │
    ├──▶ Scheduler (SM-2) ──▶ Storage (SQLite)
    │
    └──▶ HUD ──▶ CLI (claims, belief, attack, reveal)
```

### Data Flow

```
Source (YouTube/PDF/Article/GitHub)
    │
    ▼
Content Extraction (tools/)
    │
    ▼
Concept Extraction (llm.py) ──▶ 8-12 concepts with claims
    │
    ▼
Storage (storage.py) ──▶ SQLite: sources, concepts, progress, duel_memory
    │
    ▼
Scheduler (scheduler.py) ──▶ SM-2 spaced repetition
    │
    ▼
Duel Engine (duel.py) ──▶ Adversarial Socratic interrogation
    │
    ▼
HUD (hud.py) ──▶ Live visualization of engine state
```

---

## The Duel Engine

The cognitive core of LearnLock. Located in `duel.py`.

### Philosophy

Traditional learning apps ask: "Do you know X?"

LearnLock asks: "What do you _believe_ about X, and where is it wrong?"

### Pipeline

1. **Belief Modeling** — Infers what the user thinks from their response
2. **Contradiction Detection** — Compares belief against claims, finds violations
3. **Interrogation** — Generates attack question targeting highest-severity error
4. **Snapshot** — Records belief state for trajectory tracking

### Behaviors

- Vague answers trigger mechanism probes
- Wrong answers trigger claim-specific attacks
- "I don't know" triggers guiding questions (not punishment)
- Correct answers pass after verification
- 3 turns exhausted triggers reveal with full trajectory

### Graded Harshness

- Turn 1: Forgiving — only clear violations flagged
- Turn 2: Moderate — violations plus omissions
- Turn 3: Strict — all violations surfaced

### Error Types

- `wrong_mechanism` — Incorrect explanation of how something works
- `missing_mechanism` — Omitted critical mechanism
- `boundary_error` — Wrong about limitations or scope
- `conflation` — Confused two distinct concepts
- `superficial` — Surface-level understanding without depth

---

## Claim Pipeline

Claims are the epistemic foundation. The duel is only as fair as the claims.

### Three-Pass Verification

**Pass 1: Generation** — LLM generates claims with explicit instructions to produce conceptual truths, not transcript parroting. Demands falsifiable statements about WHY and HOW, not just WHAT.

**Pass 2: Garbage Filter** — Pattern matching rejects stateful claims ("is running", "must remain active"), tautologies ("processes requests", "serves requests"), and vague claims ("is useful", "is important").

**Pass 3: Sharpness Filter** — Rejects blurry truths that are technically correct but unfalsifiable ("handles security", "manages data", "deals with").

### Claim Types

- `definition` — What the concept is
- `mechanism` — How it works internally
- `requirement` — What it needs to function
- `boundary` — What it cannot do or where it fails

### Good vs Bad Claims

Bad claims get rejected:

- "The server processes requests" (tautology)
- "It handles security" (blurry)
- "Must be running to work" (stateful)

Good claims survive:

- "Validates request payloads against a JSON schema"
- "Enforces authentication via JWT token verification"
- "Uses Python type hints for automatic request validation"

---

## Module Reference

### duel.py — The Engine

Core dataclasses: `Claim`, `BeliefError`, `BeliefSnapshot`, `BeliefState`

Main class `DuelEngine` provides:

- `process(user_input)` — Process response, return attack or reveal
- `get_reveal()` — Get final state with claims, errors, trajectory
- `get_claims()` — Get parsed claims
- `finished` — Boolean indicating duel completion

Helper functions:

- `create_duel()` — Factory for DuelEngine
- `belief_to_score()` — Convert final state to 1-5 score
- `export_duel_data()` — Export for research/training
- `save_duel_data()` — Persist to disk

### hud.py — Visualization

- `set_gentle_mode()` — Toggle between brutal and gentle UI
- `render_duel_state()` — Render claims panel, belief panel, attack target
- `render_attack()` — Render interrogation panel with question
- `render_reveal()` — Render final verdict with trajectory and claim satisfaction

### cli.py — Interface

Entry point `main()` launches the REPL.

Key commands routed through `handle_input()`:

- `cmd_study()` — Main duel session loop
- `cmd_add()` — Add content from URL
- `cmd_stats()` — Display progress statistics
- `cmd_list()` — List all concepts
- `cmd_due()` — Show due concepts

### storage.py — Persistence

SQLite database with tables for sources, concepts, explanations, progress, and duel_memory.

Key functions:

- `add_source()` / `get_source()` — Source CRUD
- `add_concept()` / `get_concept()` — Concept CRUD
- `get_due_concepts()` — Query due items
- `save_duel_memory()` / `get_duel_memory()` — Persist last duel state per concept
- `update_progress()` — Update SM-2 scheduling data

### scheduler.py — SM-2 Spaced Repetition

Implements SM-2 algorithm for scheduling reviews.

- `update_after_review()` — Update ease factor and interval after scoring
- `get_next_due()` — Get single next due concept
- `get_all_due()` — Get all due concepts
- `get_study_summary()` — Aggregate statistics

### llm.py — LLM Interface

Dual-provider setup: Groq for extraction, Gemini for evaluation.

- `extract_concepts()` — Extract concepts with claims from content
- `evaluate_explanation()` — Score user explanation (legacy, replaced by duel)
- `generate_title()` — Generate topic-based title from content

### tools/ — Content Extraction

**youtube.py**

- `extract_youtube()` — Get transcript with timestamps
- `find_timestamp_for_text()` — Find timestamp for concept
- `extract_frame_at_timestamp()` — Extract and describe frame with Gemini Vision
- Whisper fallback for videos without transcripts

**article.py**

- `extract_article()` — Extract text from web articles using trafilatura

**pdf.py**

- `extract_pdf()` — Extract text from local or remote PDFs using pymupdf

**github.py**

- `extract_github()` — Extract README from GitHub repositories

### ocr.py — Image Input

- `extract_text_from_image()` — OCR using EasyOCR or Tesseract
- `check_relevance()` — Verify extracted text relates to concept

---

## Database Schema

### sources

Stores raw content from URLs. Fields: id, url, title, source_type, raw_content, segments (JSON for YouTube timestamps), created_at

### concepts

Stores extracted concepts. Fields: id, source_id, name, source_quote (ground truth), question, skipped, created_at

### explanations

Stores user responses and scores. Fields: id, concept_id, text, score, covered, missed, feedback, created_at

### progress

SM-2 scheduling data. Fields: id, concept_id, ease_factor, interval_days, due_date, review_count, last_score

### duel_memory

Persists last duel state for returning users. Fields: id, concept_id, last_belief, last_errors, last_attack, updated_at

---

## Configuration

All settings configurable via environment variables.

### Paths

- `LEARNLOCK_DATA_DIR` — Data directory (default: ~/.learnlock)

### Models

- `LEARNLOCK_GROQ_MODEL` — Groq model for extraction
- `LEARNLOCK_GEMINI_MODEL` — Gemini model for evaluation and vision

### SM-2 Parameters

- `LEARNLOCK_SM2_INITIAL_EASE` — Starting ease factor (default: 2.5)
- `LEARNLOCK_SM2_INITIAL_INTERVAL` — Starting interval in days (default: 1.0)
- `LEARNLOCK_SM2_MIN_EASE` — Minimum ease factor (default: 1.3)
- `LEARNLOCK_SM2_MAX_INTERVAL` — Maximum interval in days (default: 180)

### Extraction

- `LEARNLOCK_MIN_CONCEPTS` — Minimum concepts per source (default: 8)
- `LEARNLOCK_MAX_CONCEPTS` — Maximum concepts per source (default: 12)
- `LEARNLOCK_CONTENT_MAX_CHARS` — Max content length for processing (default: 8000)

---

## CLI Commands

| Command          | Description                          |
| ---------------- | ------------------------------------ |
| `/add <url>`     | Add YouTube, article, PDF, or GitHub |
| `/study`         | Start duel session                   |
| `/stats`         | View progress statistics             |
| `/list`          | List all concepts                    |
| `/due`           | Show concepts due for review         |
| `/skip <name>`   | Skip a concept                       |
| `/unskip <name>` | Restore skipped concept              |
| `/config`        | Show current configuration           |
| `/help`          | Show help                            |
| `/quit`          | Exit                                 |

### Flags

- `--gentle` or `-g` — Gentle UI mode (minimal, supportive feedback)
- `--version` or `-v` — Show version

---

## Known Limitations

### 1. Claim Quality (Epistemic Risk)

Claims are LLM-generated. Despite three-pass filtering, semantic drift can occur. A source saying "enforces authentication" might become "handles security" — technically related but unfalsifiable.

Mitigation: Pattern filters and sharpness checks reduce but don't eliminate this risk.

### 2. Hallucinated Errors (Moral Risk)

The contradiction detector can invent violations. A correct answer might be flagged as "missing_mechanism" due to LLM drift, causing unfair attacks.

Mitigation: Graded harshness (forgiving on turn 1), claim-index validation (errors must reference real claims). Still possible.

### 3. UI Density

The HUD displays claims, belief, attack target, and interrogation panel simultaneously. Powerful for power users, overwhelming for beginners.

Mitigation: `--gentle` flag provides minimal UI with supportive framing.

### 4. No Confidence Signals

Errors are binary. The engine cannot express "I might be wrong here."

Future: Multi-pass agreement, confidence scores, human-in-the-loop for high-stakes content.

---

## Development

### Setup

Clone the repo and install with dev dependencies using pip editable mode with the `[dev]` extra.

### Testing

Run pytest from the project root.

### Linting

Run ruff check on the src directory.

### Building

Use python -m build to create distribution packages.

### File Structure

```
src/learnlock/
├── __init__.py
├── cli.py          # CLI interface and command routing
├── config.py       # Environment-based configuration
├── duel.py         # Duel Engine (core logic)
├── hud.py          # Rich-based visualization
├── llm.py          # LLM interface (Groq/Gemini)
├── ocr.py          # Image text extraction
├── scheduler.py    # SM-2 spaced repetition
├── storage.py      # SQLite persistence
└── tools/
    ├── __init__.py
    ├── youtube.py  # YouTube extraction with timestamps
    ├── article.py  # Web article extraction
    ├── pdf.py      # PDF extraction
    └── github.py   # GitHub README extraction
```

---

## License

MIT

---

<p align="center">
<b>Stop consuming. Start retaining.</b>
<br><br>
LearnLock doesn't teach you.<br>
It finds out what you don't know.
</p>
