# AI Workflow Directives

**🚨 DO NOT write or modify code without explicit user approval.** Strictly follow the 3 phases below:

1. **Research**
   - Deeply analyze relevant files/architecture. Document all findings in `research.md`. (Do not just summarize in chat).

2. **Plan**
   - Create a `plan.md` before any implementation.
   - Must include: detailed approach, target file paths, core code snippets, and a granular Todo list.
   - **WAIT:** Stop immediately after creating `plan.md` and wait for user review/approval. Do not implement yet.

3. **Implement**
   - Start only when the user explicitly says to implement.
   - Sequentially complete and check off tasks in the `plan.md` Todo list. Do not stop until all tasks are finished.
   - Code rules: No `any` types, no unnecessary comments/JSDocs, run continuous typechecks.