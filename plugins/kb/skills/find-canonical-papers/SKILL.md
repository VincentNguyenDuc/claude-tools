---
name: find-canonical-papers
description: Find the foundational, most influential papers for a topic and build a ranked, verified reading list. Use when asked for "top papers", "canonical papers", "must-read papers", "seminal work", or a reading list on a subject.
argument-hint: <topic or sub-area>
---

# Find Canonical Papers

Build a short, trustworthy reading list for a topic: the papers someone who knows the field would call essential.

## 1. Pin down scope

- Figure out the topic folder it belongs to (e.g. `hardware-accelerators/`). If no folder fits, suggest running `/kb:new-topic` first.
- If the topic is broad, pick or ask for a sub-area (e.g. "TPU architecture" rather than "hardware").
- Read the topic's `README.md` first so you don't suggest papers it already lists.

## 2. Gather candidates from several kinds of sources

Use WebSearch and WebFetch, and cross-check across sources:

- **Surveys and review papers.** Their reference lists show what the field considers foundational.
- **University course syllabi** (Stanford, MIT, Berkeley, CMU), which often have curated reading lists.
- **Citation data** from the Semantic Scholar API (no key needed):
  `https://api.semanticscholar.org/graph/v1/paper/search?query=<q>&fields=title,year,authors,venue,citationCount,externalIds&limit=20`
- **Curated lists** such as well-maintained "awesome-*" repos, and the best-paper / test-of-time awards from top venues (ISCA, MICRO, HPCA, ASPLOS, NeurIPS, ICML, OSDI, and so on).

## 3. Rank into tiers

| Tier | Meaning |
| --- | --- |
| **Foundational** | Started the area or defined its core ideas |
| **Landmark** | Big step forward that later work builds on |
| **Recent / state of the art** | Last ~3 years, with clear impact |
| **Survey** | Good entry point or overview |

Aim for about 10–15 papers in total. Rank by influence, not raw citation count: older papers build up more citations over time.

## 4. Verify every entry. Never invent papers.

For each paper, confirm the exact title, first author, year, venue and a working link (arXiv, DOI or the publisher's page). If you can't verify a paper, leave it out or label it clearly as unverified.

## 5. Present and offer next steps

Show a table: Tier | Title | Authors (first author et al.) | Year | Venue | Link | Why it matters (one line).

Then offer to:
1. Add the papers to the topic's `README.md` reading list.
2. Download chosen papers with `/kb:add-paper`.
