---
name: new-topic
description: Create a new topic folder with the standard layout (README, notes/, papers/) and register it in the root README. Use when asked to start, add, or create a new topic or subject area.
argument-hint: <topic name>
---

# New Topic

1. **Pick a name.** Use a general kebab-case name for the area rather than one technology (e.g. `hardware-accelerators`, not `tpu`). Check the existing top-level folders first. If the new topic overlaps one of them, suggest making it a sub-area of that topic instead.

2. **Create the folders:**
   ```
   <topic>/
     README.md
     notes/.gitkeep
     papers/.gitkeep
   ```

3. **Write the topic README** using this template:
   ```markdown
   # <Topic Title>

   <One-paragraph description of the area.>

   ## Scope

   - <sub-area 1>
   - <sub-area 2>

   ## Key Ideas

   _To be filled in as I read._

   ## Reading List

   | Paper / Resource | Year | Notes |
   | --- | --- | --- |
   | | | |
   ```

4. **Register the topic.** Add a line under `## Topics` in the root `README.md`, keeping the list in alphabetical order: `- [<Topic Title>](<topic>/) — <short description>`.

5. **Offer next steps:** `/kb:find-canonical-papers` to seed the reading list.
