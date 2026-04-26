---
layout: default
title: "Gemma 26B Q4, Third Run: What Orchestrator Mode Costs a Small Model"
---

*Companion to [Same Model, Half the Bits, No GPU](article-draft-26bq4-sonnet46-20260411). Same model weights, same Q4_K_M GGUF, same Ryzen box with no GPU. The variable this time is the harness: every tool call now routes through a `delegate` specialist instead of running directly. On a frontier cloud model that abstraction is free; on a 26B model running on CPU, it's expensive, and the failure modes are revealing.*

# Gemma 26B Q4, Third Run: What Orchestrator Mode Costs a Small Model

The [first Q4 run](article-draft-26bq4-sonnet46-20260411) went 21/24 against Sonnet 4.6. Same model, same hardware, same prompts — a later harness revision added an "orchestrator" layer where the top-level agent no longer calls tools directly. It calls a single tool — `Delegate [files | system | web | scheduler]` — and a specialist sub-agent runs the actual `Read`, `Grep`, `Bash`, etc. inside its own loop. The idea is clean: keep the orchestrator's context small, let specialists do noisy filesystem work.

That's free on Sonnet. On a 26B MoE running Q4_K_M on a CPU, the same model dropped from 21/24 to 19/24, and more importantly the *shape* of the failures changed. Every round trip now costs two LLM turns instead of one, re-delegation loops started appearing where the model would ask the same specialist to read the same file three times in a row, and on a multi-file read the orchestrator would get back "I read the files" and then have nothing to analyze.

This isn't a model comparison. It's a harness-change smoke test that surfaces something specific about how small models behave when you put a sub-agent between them and their tools.

## The Setup

| | Prior Q4 Run (April 9) | This Run (April 13) |
|---|---|---|
| **Model** | `unsloth/gemma-4-26B-A4B-it-UD-Q4_K_M` | Same weights |
| **Hardware** | AMD Ryzen 7 8745HS, 32GB RAM, no discrete GPU | Same |
| **Inference engine** | llama.cpp, CPU-only (`-ngl 0`) | Same |
| **Context window** | 8,192 tokens | Same |
| **Harness mode** | Direct tool calls | Orchestrator → delegate specialist → tools |
| **Harness commit** | `ff0315f` | `5ec7dfa` |

The intentional change is the orchestrator layer. Everything else — weights, quantization, box, context window — is held constant. The orchestrator's system prompt exposes a single `delegate(agent, task)` tool and a lookup table mapping four specialist agents (`files`, `system`, `web`, `scheduler`) to the underlying tools they're allowed to call.

Full results: [Q4 + orchestrator (Apr 13)](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260413-064002-openai_gemma-4-26B-A4B-it-UD-Q4_K_M.md) | [Q4 direct (Apr 9)](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260409-233506-openai_gemma-4-26B-A4B-it-UD-Q4_K_M.md) | [Claude Sonnet 4.6](https://github.com/jalemieux/curunir-evals/blob/main/results/eval-20260407-144738-anthropic_claude-sonnet-4-6.md)

## Results

### Q4 + orchestrator completed 19 of 24 prompts. Q4 direct completed 21. Sonnet completed 23.

Two new failures relative to the direct-mode run, plus one soft failure where the orchestrator gave up and asked the user to wait for the specialist. Where the model works, the answers still read like Gemma — the capability ceiling didn't move. What moved is tool-call discipline: every task that touches the filesystem now costs two LLM turns instead of one, and several failure patterns compound on top of that.

### Where Orchestrator Mode Held Up (13 prompts)

Pure-reasoning prompts are clean. **Haiku (12)**, **context overflow (19)**, and **delegate comparison (20)** — zero tool calls in all three, same quality as direct mode. The orchestrator framing doesn't degrade responses that don't need tools.

Single-lookup prompts land in two LLM turns. **Basic tool use (1, 3)**, **error recovery (16, 17, 18)**, **model config (22)**, **scheduled tasks (23)** — one `delegate` → one specialist tool call → answer. This is the happy path the design targets, and on those prompts it works.

**Deep-research deps (14)** and **Reddit skill (15)** also complete, though with extra glob exploration before the specialist finds `context/skills/` (more on that below).

### Where Orchestrator Mode Broke

Four distinct patterns, each one costing specific prompts.

**Re-delegation loops (prompts 2, 7):** On single-file reads, the orchestrator delegates, the specialist runs `Read`, the result comes back, and then the orchestrator delegates *again* with the same ask. **Prompt 2** ("read `context/identity.md` and summarize in one sentence") goes through three full delegate cycles before the orchestrator produces a summary — `Delegate → Read → Delegate → Read → Delegate → Read → answer`. **Prompt 7** ("what do you know about me?") does the same thing with `preferences.md`, reading it three times across 7 LLM iterations. Each re-delegation burns two LLM turns for no progress. The direct-mode run of prompt 2 took one `Read` call.

**The intent leak (prompt 21):** This is the most instructive failure. Prompt 21 asks the model to read three specific files and return the most important design decision in each. Gemma correctly delegates to `files`, the specialist reads all three files (`agent.py`, `dispatcher.py`, `skills.py`), and reports back. Then the orchestrator replies:

> I'm sorry, but I cannot see the content of the files. Although the `files` specialist stated they have read them, the actual content was not passed back to me in the response.

The orchestrator re-delegates twice more with the same wording. Same outcome. Budget exhausts, no analysis produced.

Docker logs made the root cause obvious. When crafting the delegate task the orchestrator dropped the user's analytical intent. On prompt 2, the user asked "summarize in one sentence"; the orchestrator delegated "read the file and provide its content." The summarization goal never reached the specialist. On prompt 21 the analytical question was dropped entirely — so the specialist, whose prompt told it to "report what you did in under 100 words", did exactly that: "I read the files." A status report, not an answer. Then a 200-character compaction step on the very next iteration truncated whatever the specialist *did* return, before the orchestrator could react to it. Three cooperating bugs, one symptom.

**Thrashing on multi-file synthesis (prompts 6, 11, 24):** Tasks that require holding a trace in working memory are expensive when every tool use is two round-trips. **Prompt 6** (WebSocket → tool-execution trace) hit the 50-call ceiling re-reading `run.py` and `agent.py` six times without making progress. **Prompt 11** (list skills from manifest) hit a 5-call budget chasing globs before the specialist found the right file. **Prompt 24** (test count) hit 20 calls cycling through `find`, `grep`, and `ls -R` variants. Budgets tuned for direct-mode runs don't survive the 2× multiplier that orchestrator mode introduces on every tool use.

**Glob fishing (prompt 10):** "What is your name and what are you? Answer only from your identity file." The specialist globs `*`, then `*identity*`, then `*profile*`, then `*me*`, then re-runs the same globs a second time before finally reading `context/identity.md`. Four LLM iterations to locate a file the specialist could have jumped to if the orchestrator's system prompt listed the canonical paths. In direct mode the same model found the file faster because the direct-tool schema surfaces the full working directory in the grep results; the delegate summary loses that signal.

**Non-answer (prompt 4):** The orchestrator delegates a `Glob *` for discovery, the specialist returns the listing, and the orchestrator responds with a generic four-step framework-agnostic plan plus: *"Please provide the output of the file listing (or I will proceed once the specialist finishes) so I can give you the exact file names and line-by-line instructions."* The orchestrator hadn't realized the specialist already finished — the delegate result summarization masked the signal. In direct mode the same model at least read enough files to give a partially grounded plan; here it gave up on grounding entirely.

### Where Both Runs Failed

**Test count (24):** Both orchestrator and direct modes exhaust their budget. The real answer is 202 via `pytest --collect-only`. Eight models into the series, zero have reached for the test runner. This one is the prompt, not the harness.

## The Post-Mortem

The failure modes above all point at the same architectural issue: the orchestrator's delegate message was status-oriented, not goal-oriented, and the compaction step amplified that.

- **Intent was optional in the delegate schema.** The orchestrator decided what to forward to the specialist, and on small models it reliably dropped the analytical goal. "Summarize in one sentence" became "read the file." "Most important design decision" became "read three files." The user's question didn't survive the hop.
- **The files specialist's prompt was status-oriented.** "Report what you did in under 100 words" biases a read operation toward "I read the file" — not toward the file's content, and not toward an answer. Even when intent made it through, the specialist's framing pushed it to describe actions rather than produce results.
- **The delegate-result compaction step truncated verbose answers.** The next iteration of the orchestrator's history capped the delegate output at 200 characters. When a specialist *did* return a useful summary, the orchestrator saw the first 200 characters of it and nothing else.

None of this shows up on Sonnet, because Sonnet pushes enough signal through delegate calls to keep the intent alive on its own. A 26B model at Q4 doesn't have that headroom.

## The Fix

Rather than redesign the sub-agent topology, we tightened the contract:

- **`intent` is now a required argument to `delegate`, alongside `agent` and `task`.** Schema enforcement beats prompt-hoping on small models — the orchestrator literally cannot emit a delegation without naming what it needs back.
- **The `files` specialist prompt now consumes `task` and `intent` explicitly:** *"Execute the task using your tools, then return exactly what the intent asks for. Do not return raw file contents unless the intent explicitly says so."* All six specialist prompts got the same rewrite.
- **The orchestrator's specialist block now spells out the two-field contract with a worked example.** One more forcing function — show the model the shape of a correct call, not just describe it.
- **The delegate-exchange compaction cap went from 200 to 2000 characters**, so distilled answers survive into the next turn. The old cap was sized for direct-tool outputs; orchestrator mode produces longer, more information-dense summaries that were getting truncated mid-thought.
- **`context/identity.md` got a "Where things live" block** listing canonical paths (`context/memory/`, `context/agents.yaml`, `skills/`). Kills the glob-fishing pattern from prompt 10.

The rebuilt image has not yet been re-evaluated against the full 24-prompt suite — that's in progress. The unit tests pass, and the failing docker log reproductions for prompts 2 and 21 resolve cleanly. A follow-up will cover the post-fix numbers.

## Comparison

| | Q4 direct (Apr 9) | Q4 + orchestrator (Apr 13) | Sonnet 4.6 |
|---|:-:|:-:|:-:|
| **Prompts completed** | 21/24 | 19/24 | 23/24 |
| **Basic tool use** | Mixed (prompt 1 empty) | Pass | Pass |
| **Memory retrieval** | Pass | Pass (with re-delegation loops) | Pass |
| **Skill loading** | Pass | Mixed (budget on prompt 11) | Pass |
| **Error recovery** | Pass | Pass | Pass |
| **Code tracing** | Fail (context limit) | Fail (budget, thrashing) | Strong |
| **Multi-step planning** | Weak (generic) | Soft fail (non-answer on 4) | Strong |
| **Design decisions (21)** | Fail (context limit) | Fail (intent leak) | Strong |
| **Instruction precision** | Pass | Pass | Strong |
| **Self-directed exploration** | Mixed | Weak (glob fishing) | Strong |
| **Efficiency** | Strong | Weak (2× multiplier per tool use) | Mixed |

## What I Take Off the Table

**Orchestrator mode is a 26B-era tax.** On Sonnet, wrapping the tool layer in a delegate specialist costs nothing visible. On a 26B MoE at Q4 running on CPU, the same wrapping reliably costs two prompts outright and measurably degrades the rest. The ceiling didn't move — Gemma still writes the same haiku, still answers prompt 19 from knowledge, still reaches the right files when it gets there. What broke is tool-use discipline: more round trips, less intent, less budget.

**Schema enforcement beats prompt-hoping on small models.** The single most load-bearing change in the fix is adding `intent` as a required field in the delegate JSON schema. Prompt rewrites alone would not have been reliable — a 26B model leans heavily on schema as a forcing function for what to include in a tool call. The description text can warn "if you omit the user's goal here, it is lost" all it wants; the structural requirement is what makes the model actually include it.

**Eval budgets were tuned for direct mode.** Prompt 11's 5-call budget survived direct mode because one `Glob` and one `Read` is plenty. Under orchestrator mode, that's `Delegate → Glob → Delegate → Read` — four calls minimum before synthesis, with zero headroom for a missed guess. Rerunning the same prompts against the fixed build will need budget adjustments independent of any model capability question: the orchestrator adds a fixed cost per tool use, and the evaluation envelope has to account for it.

**Re-delegation loops are the fingerprint of lossy result plumbing.** When you see the same model asking the same specialist to read the same file three times, the bug is not in the model — it's in what the orchestrator's history retains after a delegate completes. In this case the 200-character compaction was eating the delegate result before the orchestrator could decide it had the answer. Logging what actually lands in the orchestrator's next-turn context is the fastest way to find this kind of bug; inspecting prompts and schemas won't surface it.

**Abstractions that are free on large models are diagnostic on small ones.** The orchestrator layer didn't fail on Sonnet in any way we could see. It failed on Gemma 26B Q4 in five different ways, each one pointing at a specific place where the abstraction had a hidden cost. Small local models are a pretty good forcing function for this kind of bug: if the design only works when the model is smart enough to paper over the seams, the design has seams.

---

*Tested on Curunir. Q4 + orchestrator at harness commit `5ec7dfa`, prior Q4 direct at `ff0315f`, Sonnet 4.6 at `4e6d576`. Full results: [jalemieux/curunir-evals](https://github.com/jalemieux/curunir-evals). April 16, 2026.*
