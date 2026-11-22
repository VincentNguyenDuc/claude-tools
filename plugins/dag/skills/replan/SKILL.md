---
name: replan
description: Revise the project's planning DAG (.claude-dag/) after a failure, a blocker, new information or a change of scope. Split, add, re-link or drop nodes and record why. Use when a node failed or is blocked, the plan no longer matches reality, or on "/dag:replan [reason]".
---

Use the `dag_*` MCP tools from the dag plugin. If they aren't available, use the `claude-dag` CLI.

1. **Assess.** Call `dag_summary` and `dag_list`. Call `dag_show` on the failed, blocked or affected nodes (read their Notes and Result), and check the recent lines of `.claude-dag/log.md`. Take the user's stated reason into account.
2. **Diagnose** in a sentence or two: what about the plan is wrong. For example: a missing prerequisite, a node that is too big, a wrong dependency, an approach that was invalidated, or a goal that changed.
3. **Propose specific changes.** Typical ones:
   - **Add a prerequisite** (fix, research or decision node) and make the stuck node depend on it.
   - **Split** a large node into smaller ones, and drop or repurpose the original.
   - **Re-link:** add or remove deps that turned out to be wrong.
   - **Drop** work that's no longer needed (`status="dropped"`). This keeps history and still counts as satisfied for anything that depends on it. Use `dag_remove` only for nodes created by mistake.
   - **Reset** a failed node to `todo` once whatever blocked it is planned.
   - **Move** nodes between milestones, or reorder milestones.

   List the changes as a short diff (`+ add`, `~ change`, `- drop`) and ask for a go-ahead. Skip the confirmation only when the user asked you to just do it and the changes are small.
4. **Apply** with `dag_add_many`, `dag_update`, `dag_link`/`dag_unlink` and `dag_append`. Put the reasoning in the affected nodes' Notes.
5. **Log and check.** Write one `dag_log` line covering what changed and why. Run `dag_validate`, then `dag_summary`, and say what is ready now.

Rules:
- Don't loosen acceptance criteria or verify commands just to make failing work pass. If the requirement itself should change, say so explicitly and get agreement.
- Keep completed nodes and their Results as they are. Replanning changes the future, not history.
