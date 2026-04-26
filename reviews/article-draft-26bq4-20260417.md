---
layout: default
title: "Gemma 26B Q4 on the New Eval: What Held Up, What Didn't"
---

*Solo review, not a Sonnet comparison. Same Gemma 4 26B A4B at Q4_K_M, same 8K context, same orchestrator harness as the [prior Q4 run](article-draft-26bq4-orchestrator-20260416). The variable this time is the eval itself — the original 24-prompt suite was retired and replaced with a new 29-prompt set that leans harder on memory-grounded personal productivity tasks (bio drafting, FDCPA letters, family trip planning, investor outreach) alongside the codebase-introspection and instruction-following prompts from the original. This is the first run through that new suite. Full results: [eval-20260417-084630](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260417-084630-openai_gemma-4-26B-A4B-it-GGUF_UD-Q4_K_M.md).*

# Gemma 26B Q4 on the New Eval: What Held Up, What Didn't

28 of 29 completed. One hard failure (a context-budget exhaustion on prompt 25) and a handful of soft edges: a Reddit anti-bot bounce on prompt 8, a clarifying-question punt on prompt 15, and several re-read loops on memory lookups that should have been one tool call. The orchestrator intent-leak fix from [the April 16 patch](article-draft-26bq4-orchestrator-20260416) is clearly holding — no "I cannot see the content of the files" misfires, no catastrophic three-cycle re-delegations on multi-file reads. What survived the fix is a softer version of the same bug: the orchestrator occasionally asks the files specialist to read the same memory file two or three times in a row before it accepts it has the answer.

The new prompts also surfaced a behavior the old suite didn't exercise much — the model is noticeably stronger at memory-grounded *personal productivity* tasks than at codebase introspection. The FDCPA dispute letter, the job-fit Slack DM, the 5-day family trip framework, the certified-mail formatting — all landed clean. The email-to-tool-call walkthrough (prompt 14) still works, but took 11 iterations and 30+ tool calls to get there.

## The Setup

| | Value |
|---|---|
| **Model** | `openai/gemma-4-26B-A4B-it-GGUF:UD-Q4_K_M` (Unsloth Dynamic Q4_K_M) |
| **Hardware** | Apple M5 Pro, 6 cores, 48GB unified memory, Metal GPU |
| **OS** | Darwin 25.3.0 |
| **Inference engine** | llama.cpp (4 slots × 8192 n_ctx) |
| **Context window** | 8,192 tokens per slot |
| **Harness mode** | Orchestrator → `delegate(agent, task, intent)` → specialist → tools |
| **Harness commit** | `5ec7dfa` |
| **Eval suite** | New 29-prompt set (replaces prior 24-prompt suite) |
| **Throughput** | ~18.9–30.5 tok/s (mostly 20–28) |
| **Cost** | Free |
| **Privacy** | Full — nothing leaves the machine |

Full results: [Gemma 26B Q4 (Apr 17)](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260417-084630-openai_gemma-4-26B-A4B-it-GGUF_UD-Q4_K_M.md)

## What Worked

**Memory-grounded personal productivity (1, 4, 6, 12):** The strongest cluster in the run. Prompt 1 produced three bio drafts, all under 160 characters, all on-voice. Prompt 4 delivered a job-fit assessment (8.5/10), named two risks, and drafted a Slack DM that leads with Code Factory and Curunir rather than employer name. Prompt 6 read `memory/people/sarah-okafor.md`, identified her open asks (Hermes doc, eval results beyond SWE-bench, agentic SDR intro), and drafted a message advancing one of them. Prompt 12 produced an FDCPA-compliant certified-mail dispute letter with the user's mailing address from `preferences.md`, itemization request (CPT/HCPCS codes), and "write-only" communication demand. These are the tasks the new suite is really testing, and the model handled them cleanly.

**Pure-reasoning prompts (10, 13, 21):** Zero tool calls each, solid answers. Prompt 10 compared curunir to a hypothetical Hermes framework (LangGraph + Pydantic + Temporal) with a gain/loss table and five P0/P1/P2 enhancements — the kind of architectural synthesis that doesn't need tool use and the model correctly recognized that. Prompt 13 built a "Hub and Spoke" 5-day family itinerary with parallel morning tracks and shared dinners. Prompt 21 wrote a valid 5-7-5 ocean haiku. The orchestrator framing doesn't degrade prompts that don't route through tools.

**Codebase introspection (14, 16):** Prompt 14 traced the email-ingestion path with file:line citations (`src/channels/email.py`, `src/channels/base.py`, `run.py`'s `agent_worker`, `Agent.handle`) and flagged a specific refactor — extract `SessionManager` from `run.py`. It took 11 LLM iterations and 30+ tool calls (lots of redundant `grep 'email'`), but the final answer is codebase-grounded with real function names. Prompt 16 read `agents.yaml` and correctly routed a web-search task to the `web` specialist.

**Instruction following (20, 22, 26, 28, 29):** Tight and literal. Prompt 20 answered only from `identity.md`. Prompt 22 listed exactly the six agents in `agents.yaml`, no embellishment. Prompt 26 searched for the no-match sentinel and concluded it wasn't present. Prompts 28 and 29 returned terse yes/no and number answers — "No, 0" and "6" — without padding.

**Error handling at the boundary (8, 24):** Prompt 8 hit Reddit's anti-bot wall on the web search and *said so*, then offered a pre-drafted reply to refine once the user pastes a link. Not a completion, but a graceful handoff with a fallback. Prompt 24 asked the model to delete `preferences.md` — there's no delete tool, so the model opened it, read it, and wrote empty content. Effectively cleared the file. Pragmatic substitution without making a mess.

**Memory retrieval breadth (11, 17, 19):** Prompt 11's portfolio audit produced a Consolidate/Kill recommendation with the three strategic bets (Curunir core, Meta-Skill layer, `gtm-agent`) and two archives (`BrightPath`, `Vaultnet`). Prompt 19 summarized three archived conversations and correctly identified the pattern — two early failures from file-access issues, one later success from architecture exploration. Prompt 17 led with current work (Curunir expansion, Code Factory, memory management) rather than biographical filler, following the instruction.

## What Didn't

**Re-read loops on memory files (2, 6, 7, 11, 18):** The intent-leak bug is gone, but a softer cousin survived. Prompt 6 calls `Read context/memory/people/sarah-okafor.md` four times across six iterations. Prompt 7 reads the same file three times across five iterations. Prompt 11 reads `context/memory/projects.md` twice, then runs `cat`, `ls -l`, and `wc -l` against the same file (looking for something the read already surfaced). Prompt 18 reads `tasks.md` three times across four iterations. In every case the content was already in history — the orchestrator just didn't accept it. Same fingerprint as the pre-fix re-delegation loops, but without the outright failure. The cost is iteration count, not task completion.

**Glob fishing before the read (2, 7, 11):** Prompt 2 opens with `find tasks.md in the current directory`, then `Glob tasks.md`, then `Glob **/tasks.md` before finally reading `context/memory/tasks.md`. Prompt 7 globs twice before finding `memory/people/`. Prompt 11 globs, globs again, then reads `projects.md`. The "Where things live" hint in `identity.md` helped prompt 10 in the prior run, but the new suite asks about files the hint doesn't cover — and when the model doesn't know a path, it always tries globs first instead of the canonical `context/memory/` locations.

**Prompt 3 — confabulation risk:** The model answered "what corrections have I made" with three specific items: "6 years at Salesforce vs 20+ years in SaaS," "prefer not to name-drop Salesforce," "anti-corporate tone." These are plausible corrections *consistent with* the memory files, but I cannot verify from the eval transcript that any of them were ever actually stated as corrections versus inferred from static memory content. The grep for `(correction|updated|actually|changed|no longer|instead of)` returned something that shaped the answer, but whether that something was a genuine correction log or an incidental phrase match isn't visible in the trace. Worth flagging: the model answered confidently without evidence that it distinguished "things in memory" from "things the user explicitly corrected."

**Prompt 8 — web search hit the anti-bot wall:** Reddit returned no content through the available fetch tools; the model tried three URL variants and a Google fallback before punting. The draft reply it offered was serviceable (~85 words, leads with the disagreement) but contained a version slip — "Claude 3.5 Sonnet" instead of "Claude Sonnet 4.6" per the user's memory. Small, but the kind of drift that matters when the draft is meant to post to Reddit as the user's voice.

**Prompt 15 — clarifying question instead of a plan:** The user asked for a walk-through of every file to change to add a `summarize` tool, in order, without making changes. The model bucketed into "Specialist vs Skill" and asked which one the user wanted — then offered two thin outlines instead of picking one and being specific. Compare to prompt 14, which committed to a path and cited file:line. Prompt 15 punted.

**Prompt 27 — the efficiency prompt isn't efficient:** "What model is this instance configured to use? Find the answer with as few tool calls as possible." The model ran 5 LLM iterations and 8 tool calls — read `identity.md` twice (once via delegate, once via bash `cat`), globbed `context/`, then ran `env | grep MODEL` which gave the answer. The correct first move is the env grep; the first three calls were redundant. The model got the right answer but ignored the "as few calls as possible" constraint — this is the same efficiency-instruction blindness the series has seen on every model so far.

## The One Hard Failure

**Prompt 25 — LIMIT HIT (10/10) on `context/memory/raw/reddit-research.md`:** The model tried `Read context/memory/raw/reddit-research.md` first, which presumably failed or returned content the orchestrator lost. It then globbed `*.md`, `**/*reddit-research.md`, `**/*`, `**/*reddit*`, `*`, read `skills/reddit-research/SKILL.md` (the wrong file), and listed `context/memory/`. Budget exhausted, no response produced. This is the same class of failure seen on the original suite's prompt 19 in earlier runs — the model recognizes it's not finding what it needs, but the error-recovery loop eats the budget without converging on an answer or an explicit "I can't find this." The fact that it read `skills/reddit-research/SKILL.md` suggests the model confused the `raw/` input file with the skill of the same name.

## What I Take Away

**The intent-field fix transferred cleanly to the new suite.** None of the catastrophic orchestrator failures from the [April 13 run](article-draft-26bq4-orchestrator-20260416) reappeared — no "specialist read files but content not passed back," no three-cycle re-delegation on multi-file reads. The structural enforcement (intent as a required schema field) is doing work. The failure modes that remain are milder: re-reads of single files, glob fishing for paths, efficiency-instruction blindness. The bug-class that dominated the prior run is gone; what replaced it is noise.

**The new suite favors memory-grounded personal productivity over codebase tracing.** The FDCPA letter, the job-fit DM, the bio drafts, the certified-mail formatting, the investor outreach — these all landed cleanly on first try. The codebase-tracing prompts (14) still work but require 2–3× more iterations than the equivalent Sonnet run on the old suite. For a model running locally on an M5 Pro, the realistic use case this eval is measuring — drafting letters, planning trips, iterating on bios from memory — is the one the model is best at. The codebase-introspection prompts are the stress test, not the target workload.

**Re-read loops are the new fingerprint of result-plumbing drift.** Five separate prompts showed the model asking the files specialist to re-read a file it had already seen. The content does arrive — the compaction cap raised to 2000 chars is preserving it — but some piece of the orchestrator's state isn't acknowledging "I have this." This isn't the same bug as the pre-fix intent leak; the symptom is iteration-count inflation rather than task failure. It's the kind of thing that only shows up as a cost, not a crash. Worth instrumenting before the next rev.

**The efficiency prompts still don't land.** Prompt 27 is a direct test: "find this with as few tool calls as possible." The model used 8. Every model in the series, local or cloud, has ignored that constraint. This is a stable pattern now — efficiency-as-instruction doesn't gate tool-calling loops across any of the models tested. Either the prompt needs teeth (budget = 2, for instance) or the series should stop treating the current phrasing as a meaningful signal.

**Prompt 25's failure is a symptom worth chasing.** Of the 29 prompts, the only outright LIMIT HIT is one where the model confused an input file (`context/memory/raw/reddit-research.md`) with a skill of similar name (`skills/reddit-research/SKILL.md`). The skill-manifest routing bug surfaced in the April 16 notes — the orchestrator prompt doesn't inject `build_skill_manifest`, so the model has no grounded knowledge of where skills live — may be feeding this. Worth resolving before the next run through the expanded suite, otherwise prompt 25 will reliably burn budget every time.

---

*Tested on Curunir. Gemma 26B Q4_K_M at harness commit `5ec7dfa`, on Apple M5 Pro / Metal, 8K context per slot, new 29-prompt eval suite. Full run: [eval-20260417-084630](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260417-084630-openai_gemma-4-26B-A4B-it-GGUF_UD-Q4_K_M.md). Repo: [jalemieux/curunir-evals](https://github.com/jalemieux/curunir-evals). April 17, 2026.*
