---
name: add-paper
description: Download a paper into a topic's papers/ folder with the repo's naming convention and add it to the topic reading list. Use when asked to add, save, or download a paper (arXiv link, DOI, title, or a local PDF).
argument-hint: <arXiv id | URL | title | local path> [topic]
---

# Add Paper

## 1. Identify the paper

- Work out the exact title, first author's last name, year and venue. For a bare title, look it up on arXiv or Semantic Scholar.
- Work out which topic folder it goes in. If that's unclear, ask. If the folder doesn't exist, offer `/kb:new-topic`.

## 2. Name the file

Pattern: `YYYY-firstauthorlastname-short-title.pdf`, all lowercase kebab-case, with the short title at most about 6 words.
Example: `2017-jouppi-in-datacenter-performance-analysis-tpu.pdf`

## 3. Get the PDF

- arXiv: `curl -L -o <topic>/papers/<name>.pdf https://arxiv.org/pdf/<id>`
- Other sources: download only from the official publisher, the author's page or arXiv. Don't use mirror or piracy sites. If the paper is paywalled, add only the reading-list entry with a link, and tell the user.
- Local file: copy it in (don't move it unless the user asks).
- Check that the result really is a PDF: `file <path>` should report `PDF document`. If it doesn't (for example an HTML error page), delete it and report what happened.

If the repo uses Git LFS (`filter=lfs` patterns in `.gitattributes`), PDFs are tracked automatically and `/git:commit` checks it. Otherwise, warn the user before adding large PDFs to plain Git.

## 4. Update the reading list

Add a row to the Reading List table in `<topic>/README.md`, in a sensible order (by year or by tier):

```
| [Title](papers/<name>.pdf) ([source](<url>)) | YYYY | |
```

Remove the empty placeholder row (`| | | |`) if it's still there.

## 5. Offer next steps

Offer to write notes with `/kb:paper-notes`, or to commit with `/git:commit`.
