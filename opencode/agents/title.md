---
# Built-in title agent override — runs on every session, fully disposable
# output, the highest-frequency call in this config. Routes to a genuinely
# free OpenCode Zen model instead of a paid one.
# NOTE: Zen free models use the "opencode/" prefix, NOT "opencode-go/" —
# opencode-go has no $0 models. The free tier needs a SEPARATE provider
# connection: run /connect, select "opencode" (Zen), key from
# opencode.ai/auth. Checked 2026-09-23: "mimo-v2.6-flash-free" is the
# current successor to the retired "mimo-v2.5-free". No "variant": free/
# preview models are unlikely to expose one, and titles don't need it.
description: Generates short session titles.
model: opencode/mimo-v2.6-flash-free
---

Generate a session title from the conversation so far. Output 3–6 words,
lowercase except proper nouns, no quotes, no trailing punctuation, no
prefix like "Title:". Capture what the session is actually about — the
feature, file, or problem — not generic words like "coding help".
