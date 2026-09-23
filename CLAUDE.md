# Claude project instructions

Before changing this repository, read `PROJECT_HANDOFF.md` and `README.md` completely.

## Non-negotiable product requirements

- The service must keep working without a paid API, trial credit, or an always-on personal computer.
- GitHub Actions is the scheduled runtime. The repository is public so standard hosted runners remain within the free architecture.
- Gemini is an optional quality layer only. Every Gemini failure, missing key, or exhausted quota must fall back to the local analyzer.
- Telegram news and tutorials must be written in clear, conversational Persian.
- Published posts must not display a source name or source URL. Keep URLs internally only for duplicate detection.
- Automated Telegram posts must be silent (`disable_notification=true`).
- Never print, commit, request in chat, or expose secret values. Only refer to their GitHub Secret names.
- Preserve the existing Telegram Forum Topic behavior and the committed publication history.

## Working rules

- Make the smallest safe change and preserve the zero-cost fallback.
- Run relevant tests or a dry run before proposing deployment.
- Do not enable billing or add a dependency that requires a credit card.
- Do not manually edit generated publication history unless repairing corrupted state.
- Update `PROJECT_HANDOFF.md` when architecture, operations, secrets, scheduling, or product decisions change.
