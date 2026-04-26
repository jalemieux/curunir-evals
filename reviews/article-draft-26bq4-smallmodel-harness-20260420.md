---
layout: default
title: "Gemma 26B Q4, Fourth Run: What a Small-Model Harness Branch Changes"
---

*Companion to [Gemma 26B Q4 on the New Eval: What Held Up, What Didn't](article-draft-26bq4-20260417). Same model weights, same Q4_K_M GGUF, same Apple M5 Pro box. The variable this time is the harness branch: a `small-model` branch of Curunir against `main`, both run back-to-back on the same afternoon. The branch is an attempt to lower the prompt-side overhead that Gemma at 8K context has to absorb before it can think. It works — in throughput. It also removes two tool primitives that `main` relies on, which shows up as lost prompts.*

# Gemma 26B Q4, Fourth Run: What a Small-Model Harness Branch Changes

The premise of the `small-model` branch is simple: a 26B model running Q4_K_M with an 8,192-token context window spends too much of that budget on the tool schema and the system prompt. If you shrink the surface — fewer meta-tools, leaner system prompt, a thinner stats schema — you buy back tokens for the conversation, and the model should be faster and better at the prompts where its capability isn't the bottleneck.

Two runs, same model, same hardware, 40 minutes apart. The `main` branch went 21/24. The `small-model` branch went 19/24. But the average `Completion tok/s` jumped from 11.4 to 18.75, and total wall time across the prompts with stats dropped from ~1,021 seconds to ~620 seconds — about 40% faster. The two prompts it lost are exactly the ones that required meta-tools the branch doesn't ship: `LoadSkill` for skill-loading prompts, and the overflow-prone search flow for prompt 13 that `LoadSkill` would have shortened.

This isn't a model comparison. It's a harness-change smoke test where the cost and benefit both land on the same model.

## The Setup

| | `main` (20:35 UTC) | `small-model` (19:55 UTC) |
|---|---|---|
| **Model** | `openai/gemma-4-26B-A4B-it-GGUF:UD-Q4_K_M` | Same weights |
| **Hardware** | Apple M5 Pro, 48 GB RAM, 6 cores | Same |
| **Context window** | 8,192 tokens | Same |
| **Reported Version** | `1adc308` | `1adc308` |
| **`LoadSkill` meta-tool** | Present | Not exposed |
| **`Schedule list` meta-tool** | Present | Not exposed (falls back to `Read context/schedules.json`) |
| **`Prompt tokens` / `Total tokens` in stats** | Recorded | Removed |
| **`context.default/` visible at cwd** | No | Yes |

Caveat worth flagging: both runs report the same harness commit hash in the result file. The branch delta isn't captured in the `Version` field — it shows up in the tool surface the model sees and the stats schema that gets written. Either the hash is the last common commit and the branch carries uncommitted or non-hashed changes, or the hash field is populated from `main` regardless of the checked-out branch. The transcripts make the branch difference unambiguous even if the field doesn't.

Full results: [`main` (Apr 20, 20:35)](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260420-133551-openai_gemma-4-26B-A4B-it-GGUF_UD-Q4_K_M.md) | [`small-model` (Apr 20, 19:55)](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260420-125505-openai_gemma-4-26B-A4B-it-GGUF_UD-Q4_K_M.md)

## Results

### Main completed 21 of 24 prompts. Small-model completed 19.

Two clean losses on `small-model` (prompts 13 and 14), one soft degrade (prompt 15) where it punts instead of loading, and one prompt (6) that produces a partial trace with garbled channel tokens instead of the clean budget failure `main` gets. On the other end, every prompt where speed or instruction precision is the story — haiku, skill listing, error recovery, efficiency — goes to `small-model` by a visible margin.

### Where Small-Model Wins on Throughput (every prompt it completed)

The average `Completion tok/s` difference is not subtle. On prompt 3 (`pwd && ls`), `main` runs at 5.9 tok/s and takes 15.23s; `small-model` runs at 19.4 tok/s and finishes in 5.06s. On prompt 17 (run a failing Python import and handle it), `main` takes 19.37s at 8.3 tok/s; `small-model` takes 3.21s at 16.9 tok/s. Prompts 12 (haiku, no tools), 18 (`Grep` for a missing pattern), 19 (context overflow explanation), and 20 (delegate vs function call) all land in the 25–27 tok/s range on `small-model` versus 9–21 on `main`.

This is the same model, same weights, same quant. The only thing that could move tok/s this much is what's arriving at the model's input — fewer tool schemas and a shorter system prompt both reduce prompt-processing work per turn and leave more of the 8K window for actual reasoning. It lines up with the other observable change: `small-model` dropped `Prompt tokens` from the stats table, which at minimum means someone touched the token accounting path.

### Where Small-Model Wins on Quality

**Prompt 4 (add a "summarize" tool)** — `main` interprets the request as Python surgery: `schemas.py` → `fs_tools.py` → `__init__.py` → `dispatcher.py`. `small-model` interprets it as a Skill: create `context/skills/summarize/SKILL.md`, optionally update `agents.yaml` and `schedules.json`. Both are plausible; the Skill answer is more idiomatic to how Curunir actually ships user-facing capabilities, and it's the route a user asking this question would more likely want.

**Prompt 11 (list skills, only what's in the manifest)** — `main` emits a two-column table with a "When to Use" description for each skill, exceeding the instruction. `small-model` returns a clean bulleted list, exactly what was asked for. Instruction precision wins.

**Prompt 22 (what model am I configured to use?)** — `main` reads `src/config.py` and answers `anthropic/claude-sonnet-4-20250514`, which is the committed default — not what's actually running. Four tool calls, 72.5 seconds. `small-model` runs `env | grep -i MODEL` and answers `openai/gemma-4-26B-A4B-it-GGUF:UD-Q4_K_M`, which is correct. Two tool calls, 16.7 seconds. Faster and right.

**Prompt 23 (scheduled tasks)** — both answer correctly. `main` calls `Schedule list` and takes 19.7s; `small-model` reads `context/schedules.json` directly and takes 5.6s. Same answer, ~4× faster. The meta-tool isn't earning its cost here.

### Where Main Wins

The pattern is consistent: every prompt where `main` wins outright is a prompt that wants a skill to be loaded, or wants search-style orchestration that a richer tool surface shortens.

**Prompt 5 (skills using "attach")** — `main` takes 123s and 8 tool calls to conclude no skill mentions "attach." `small-model` hits context overflow after 6 redundant greps.

**Prompt 13 (load web-search, summarize asyncio best practices)** — `main` runs `LoadSkill web-search` + one `curl` to the Brave API and produces a clean structured summary. `small-model` has no `LoadSkill`, so it loops through 11 calls trying to reconstruct the skill from filesystem shape and environment, and dies on context overflow.

**Prompt 14 (deep-research sub-skills)** — `main` calls `LoadSkill deep-research` and lists dependencies: mandatory `web-search`, optional `reddit-research`, `xai-search`, `gemini-search`, `linkedin-research`. `small-model` fails to find a local `SKILL.md` for `deep-research`, concludes it must be "built-in," and punts: *"Would you like me to run a task through the deep-research skill to ask it for its own dependency list?"* It isn't wrong that the skill is runtime-loaded rather than file-backed — but without `LoadSkill` in the tool surface, the model has no verb to reach it.

**Prompt 15 (Reddit research skill)** — same pattern: `main` loads it, `small-model` explains the skill from its description but can't actually load anything. Technically a partial pass, but the instruction was "load it."

**Prompt 1 (Python files with "async" in `src/tools/`)** — `main` lists both files by name (`dispatcher.py`, `delegate.py`). `small-model` runs `grep -rl "async" src/tools/ --include="*.py" | wc -l` and returns only the count. Correct but thinner; the prompt asked for both the files and how many there are.

### Where Both Failed, Differently

**Prompt 6 (WebSocket → tool execution trace)** — both fail. `main` runs out of context after four clean reads with nothing emitted. `small-model` produces a partial trace with real file citations — `src/channels/ws.py` lines 36-87, 59, 61, 66-72, 73 — and then the response is truncated and leaks raw Harmony channel tokens into the output:

> `<|channel> de<|channel>thought` ... `<|tool_call>call:grep{pattern:<|"|>WebSocketChannel<|"|>,path:<|"|>src<|"|>}<tool_call|>`

This is a decode/formatting bug surfacing at the model-output layer. The leaner prompt may be pushing the model closer to the token boundary where channel control tokens normally live, or the sampler/stop-string configuration differs between branches. Either way, `main`'s clean "conversation is too long" is a more useful failure than a garbled partial.

**Prompt 21 (design decisions across three files)** — both fail. `main` overflows after reading all three files once. `small-model` reads `agent.py` and `dispatcher.py`, then reads them again, then again — twelve-plus iterations of the same two reads, hitting the 25-call ceiling with no answer. This is the orchestrator-era loop pattern showing up in direct mode: when the model's working memory can't hold the three files at once, asking for the same files again becomes the only move it has. `main` at least fails fast.

**Prompt 24 (test count)** — both overflow mid-search. Neither branch reaches for `pytest --collect-only`, the only tool that gives the real answer (202). Nine Gemma runs into this series, still zero models have solved this prompt. It's the prompt, not the harness.

## The Post-Mortem

Three loose observations, the kind worth writing down before the next branch iteration.

- **`LoadSkill` is load-bearing in a way the tool budget hides.** On `main`, prompts 13–15 are cheap: one `LoadSkill` call establishes both the skill's identity and its file-backed contents in one shot. On `small-model`, the same prompts fan out into `ls` walks, `Glob` passes, and direct `Read`s of paths the model has to guess. For a 26B model at Q4, the prompt budget to infer "this skill is a built-in, not a file, so stop looking" is larger than the budget the eval gives it. Either `LoadSkill` comes back, or the skill catalog has to be surfaced to the system prompt in a way the model can resolve without probing the filesystem.
- **The throughput gain is real, and it's not free.** 18.75 tok/s average up from 11.4 is ~65% more throughput on the same hardware. That comes back directly on every prompt Gemma can answer from knowledge or with a single tool call — haiku, error recovery, simple reads. The cost lands concentrated on two prompts out of 24. For interactive use of Gemma 26B Q4 on this box, the `small-model` tradeoff is arguably correct: the median prompt improves visibly, and the lost prompts are ones the model struggles with in both modes.
- **`Schedule list` vs `Read context/schedules.json` is a miniature version of the same question.** Both branches answer prompt 23 correctly. The meta-tool version takes 19.7s; the direct-read version takes 5.6s. A meta-tool earns its place when it hides complexity the model can't handle — in this case it doesn't, and the Read is cheaper. Every meta-tool in the prompt has a similar check to pass.

A caveat on interpretation: single-run, qualitative smoke test, as always. The 65% throughput gain is suggestive — if prompt-side bytes really are the dominant cost on an 8K-context run, then the gain should reproduce; if it's partly noise from the sampler or from llama.cpp's slot state at 19:55 vs 20:35, it won't. A repeat pair of runs would clarify.

## Comparison

| | `main` (Apr 20) | `small-model` (Apr 20) |
|---|:-:|:-:|
| **Prompts completed** | 21/24 | 19/24 |
| **Total wall time (tracked prompts)** | ~1,021s | ~620s |
| **Average `Completion tok/s`** | 11.4 | 18.75 |
| **Basic tool use (1–3)** | Strong (includes filenames on #1) | Pass (count only on #1) |
| **Multi-step planning (4)** | Pass (Python-module interpretation) | Pass (Skill interpretation, more idiomatic) |
| **Memory retrieval** | Pass | Pass |
| **Skill loading (13–15)** | Pass (via `LoadSkill`) | Fail / punt (no `LoadSkill`) |
| **Instruction precision (11, 12)** | Weak (over-formatted #11) | Strong |
| **Error recovery (16–18)** | Pass | Pass (3–4× faster) |
| **Efficiency (22, 23)** | Weak (wrong answer on #22, slow on #23) | Strong |
| **Code tracing (6)** | Fail (context limit) | Fail (garbled partial) |
| **Design decisions (21)** | Fail (context limit) | Fail (read-loop budget exhaustion) |
| **Test count (24)** | Fail | Fail |

## What I Take Off the Table

**Prompt-surface budget is a first-class lever on small local models.** Shrinking the tool schema and system prompt moves the average `Completion tok/s` by 65% on the same weights. That's not a model-capability claim — the model's ceiling didn't change. It's a claim about how much of the 8K window was being burned on overhead before. Any future local-model harness on this box should treat the prompt surface as a design parameter, not a default.

**Meta-tools need to earn their spot, and most do.** `LoadSkill` does — the two prompts it costs `small-model` are strictly lost, and the third (prompt 15) only soft-lands. `Schedule list` does not — `Read context/schedules.json` gets the same answer in 5.6s instead of 19.7s. The filter is whether the meta-tool hides complexity the model can't handle. For Gemma 26B Q4, `LoadSkill` passes that filter; `Schedule list` does not. Other meta-tools on `main` deserve the same scrutiny.

**A leaner prompt surface is a different kind of failure, not no failure.** Prompt 6 on `small-model` produces a partial trace with real file citations and then leaks channel control tokens into the user-facing response. That's worse than `main`'s clean "conversation is too long" — not because it loses more information, but because a garbled response is a worse output than a failure signal. Whatever difference in sampler/stop-token handling shows up here is a regression to fix before this branch ships, separate from the tool-surface question.

**The harness itself is now a variable worth tracking.** The series started as "same harness, different models." Runs 3 (orchestrator mode) and 4 (small-model branch) have put enough of the harness itself on the variable list that the framing has to shift: same model, different harness, what moves. For local models in particular — where every byte of the prompt fights every other byte — harness-side decisions are starting to matter as much as model-side ones. The `Version` field in the result files should capture branch or config, not just commit hash, if this keeps going.

---

*Tested on Curunir. Both runs at harness commit `1adc308` per result files; branch delta is in tool surface and stats schema rather than committed code. Full results: [jalemieux/curunir-evals](https://github.com/jalemieux/curunir-evals). April 20, 2026.*
