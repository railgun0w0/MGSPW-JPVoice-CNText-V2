# BRIEFING_NBE translation mappings

This directory contains validated, per-file translation mappings for the frozen JPN-only `BRIEFING_NBE` corpus.

Create one validated mapping per `BRIEFING_NBE` template as translation work is completed. Mapping rows must bind the template's `file_id` and `unique_index`, and must contain translated `cn_text`; `eng_reference` and `mlg_cn_reference` are auxiliary evidence and must never be copied here as if they were completed translations.

## Resume translation work

For browser/ChatGPT translation sessions, do **not** scan the complete template directory or all existing mappings just to discover the next file.

1. Read `CURSOR.json` first.
2. Start directly from `CURSOR.next_file_id`.
3. Check only that target mapping before translating it.
4. If that mapping already exists, treat the mapping as authoritative and advance through the canonical order defined by `QUEUE.json` until the first missing mapping; repair `CURSOR.json` before continuing.
5. After a mapping has been committed and read back successfully, advance `CURSOR.json` to the next template in canonical order.

`CURSOR.json` is an operational resume pointer, not the source of truth for completed translations. Existing mapping files are always authoritative, so a stale cursor is safe to recover.

`QUEUE.json` defines the canonical queue from the frozen template directory: `BRIEFING_FILES_BLOCK_*.csv` in lexicographic ascending filename order. Do not rebuild queue positions from only the missing mappings, because that would make queue positions change as translation progresses.

The corpus contains 469 templates. Live progress counts are intentionally not embedded in this README because they become stale during long-running translation. Use mappings/state rebuild tooling when a full progress report is needed.

Continue one complete `file_id` at a time. Write the result as `BRIEFING_NBE/<file_id>.json` using the existing schema and do not create packet-level or `partNNN.json` translation artifacts.

For the browser translation workflow, do not manually edit generated global state/progress/checkpoint files merely to record each translated file. The mapping plus updated `CURSOR.json` is sufficient for resuming work; run the repository state rebuild/check tooling separately when a synchronized global checkpoint is required.
