---
name: paper-notes
description: Read a paper and write structured markdown notes in the topic's notes/ folder. Use when asked to summarize, take notes on, break down, or explain a paper in the repo.
argument-hint: <path to paper or title>
---

# Paper Notes

## 1. Read the paper

Use the Read tool on the PDF, a page range at a time for long papers (`pages: "1-10"`, then the next range). Read the abstract, introduction, method, results and conclusion. Skim the appendices.

## 2. Write the notes

Save to `<topic>/notes/<same-name-as-pdf>.md`, using this template:

```markdown
# <Title>

**Authors:** <authors> · **Year:** <year> · **Venue:** <venue>
**Paper:** [PDF](../papers/<name>.pdf) · [Source](<url>)

## TL;DR
<2–3 sentences: what they did and why it matters>

## Problem
<What gap or bottleneck does it address?>

## Key Ideas
- <core contribution 1>
- <core contribution 2>

## How It Works
<Method or architecture. Include key equations, numbers and design choices.>

## Results
<Headline numbers, plus what they were compared against>

## Limitations & Open Questions
- <what the authors admit, and what you notice>

## Connections
- <links to related notes in this repo, and prior or follow-up work>

## My Takeaways
<Leave for the user to fill in, or draft if they ask>
```

Keep it accurate: quote numbers from the paper exactly, and mark any interpretation of your own as such.

## 3. Link it up

In the topic's `README.md` reading list, put a link `[notes](notes/<name>.md)` in the Notes column for that paper. If the paper adds an important concept, offer to add a bullet to the topic's **Key Ideas** section.
